#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Check, and optionally apply, the per-session state of a Claude Cloud Worker session.

The environment's setup script runs once per cached snapshot and cannot read the
environment's saved variables. This script covers what only the session can do.

    ccw_check.py [git-identity] [aws-profiles] [versions] [--fix] [--json]

With no check named, every check runs. ``--fix`` applies what a check can apply;
``versions`` never fixes, because the fix is an environment change the user approves.

Exit codes: 0 when nothing is in drift, 1 when any check reports drift, 2 on a usage error.
"""

from __future__ import annotations

import argparse
import configparser
import json
import os
import re
import subprocess
import sys
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path

OK, FIXED, DRIFT, SKIP = "ok", "fixed", "drift", "skip"

MARKETPLACE = "jpeakai"
PLUGINS = ("jpai-essentials", "jpai-ccw")
DEFAULT_REPO = "https://github.com/jpeakai/skills"
DEFAULT_RAW_BASE = "https://raw.githubusercontent.com/jpeakai/skills/main"
DEFAULT_RELEASE_FILE = "/etc/ccw/release"
TAG_PREFIX = "ccw/v"

# Profile name -> {config key: environment variable}. A profile is configured only
# when its role ARN is known, either from the environment or from the setup script.
PROFILE_VARS: dict[str, dict[str, str]] = {
    "ccw": {"role_arn": "CCW_ROLE_ARN"},
    "ccw-admin": {"role_arn": "CCW_ADMIN_ROLE_ARN", "external_id": "CCW_ADMIN_EXTERNAL_ID"},
}
Fetch = Callable[[str], str | None]
ListTags = Callable[[], list[str] | None]


@dataclass(frozen=True)
class Result:
    check: str
    status: str
    detail: str


# --- git identity -----------------------------------------------------------
def _git_get(key: str, env: Mapping[str, str]) -> str:
    out = subprocess.run(
        ["git", "config", "--global", "--get", key],
        capture_output=True,
        text=True,
        env=dict(env),
        check=False,
    )
    return out.stdout.strip()


def check_git_identity(env: Mapping[str, str], fix: bool) -> list[Result]:
    """Set the commit author only. The committer stays as the session's signing identity.

    Name and email apply together: half an identity would pair the agent's name with a person's email.
    """
    wanted = {
        "author.name": env.get("CCW_GIT_AUTHOR_NAME", ""),
        "author.email": env.get("CCW_GIT_AUTHOR_EMAIL") or env.get("CLAUDE_CODE_USER_EMAIL", ""),
    }
    if not all(wanted.values()):
        missing = "CCW_GIT_AUTHOR_NAME" if not wanted["author.name"] else "CCW_GIT_AUTHOR_EMAIL"
        return [Result("git-identity author", SKIP, f"{missing} is not set")]
    results = []
    for key, value in wanted.items():
        name = f"git-identity {key}"
        if _git_get(key, env) == value:
            results.append(Result(name, OK, "matches the environment"))
        elif fix:
            subprocess.run(["git", "config", "--global", key, value], check=True, env=dict(env))
            results.append(Result(name, FIXED, "set from the environment"))
        else:
            results.append(Result(name, DRIFT, "differs from the environment"))
    return results


# --- AWS profiles ------------------------------------------------------------
def aws_config_path(env: Mapping[str, str]) -> Path:
    if env.get("AWS_CONFIG_FILE"):
        return Path(env["AWS_CONFIG_FILE"])
    return Path(env.get("HOME", str(Path.home()))) / ".aws" / "config"


def _read_config(path: Path) -> configparser.ConfigParser:
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str  # type: ignore[assignment,method-assign]
    if path.is_file():
        parser.read(path, encoding="utf-8")
    return parser


def wanted_profile(profile: str, env: Mapping[str, str], present: bool) -> dict[str, str]:
    """The keys this session can vouch for. Empty means the profile is not in use here."""
    wanted = {key: env[var] for key, var in PROFILE_VARS[profile].items() if env.get(var)}
    if not present and "role_arn" not in wanted:
        return {}
    if "role_arn" in wanted:
        wanted["credential_source"] = "Environment"
        region = env.get("CCW_AWS_REGION") or env.get("AWS_DEFAULT_REGION")
        if region:
            wanted["region"] = region
    return wanted


def check_aws_profiles(env: Mapping[str, str], fix: bool) -> list[Result]:
    path = aws_config_path(env)
    config = _read_config(path)
    results = []
    changed = False
    for profile in PROFILE_VARS:
        section = f"profile {profile}"
        name = f"aws-profiles {profile}"
        present = config.has_section(section)
        wanted = wanted_profile(profile, env, present)
        if not wanted:
            reason = "no saved variables to compare" if present else "not configured in this environment"
            results.append(Result(name, SKIP, reason))
            continue
        current = dict(config[section]) if config.has_section(section) else {}
        stale = sorted(k for k, v in wanted.items() if current.get(k) != v)
        if not stale:
            results.append(Result(name, OK, "matches the environment"))
        elif fix:
            if not config.has_section(section):
                config.add_section(section)
            for key in stale:
                config[section][key] = wanted[key]
            changed = True
            results.append(Result(name, FIXED, "set " + ", ".join(stale)))
        else:
            results.append(Result(name, DRIFT, "differs on " + ", ".join(stale)))
    if changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            config.write(handle)
    return results


# --- versions ------------------------------------------------------------------
def version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in re.findall(r"\d+", version))


def installed_versions(env: Mapping[str, str]) -> dict[str, str]:
    root = Path(env.get("CLAUDE_CONFIG_DIR") or Path(env.get("HOME", str(Path.home()))) / ".claude")
    path = root / "plugins" / "installed_plugins.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    versions = {}
    for plugin in PLUGINS:
        entries = data.get("plugins", {}).get(f"{plugin}@{MARKETPLACE}", [])
        if entries:
            versions[plugin] = entries[0].get("version", "")
    return versions


def read_release(env: Mapping[str, str]) -> dict[str, str]:
    path = Path(env.get("CCW_RELEASE_FILE", DEFAULT_RELEASE_FILE))
    if not path.is_file():
        return {}
    pairs = (line.split("=", 1) for line in path.read_text(encoding="utf-8").splitlines() if "=" in line)
    return {key.strip(): value.strip() for key, value in pairs}


def curl_fetch(url: str) -> str | None:
    out = subprocess.run(
        ["curl", "-fsSL", "--max-time", "20", url], capture_output=True, text=True, check=False
    )
    return out.stdout if out.returncode == 0 else None


def git_tags(repo: str) -> ListTags:
    def list_tags() -> list[str] | None:
        out = subprocess.run(
            ["git", "ls-remote", "--tags", "--refs", repo, f"refs/tags/{TAG_PREFIX}*"],
            capture_output=True,
            check=False,
            text=True,
            timeout=30,
        )
        if out.returncode != 0:
            return None
        return [line.split("refs/tags/", 1)[1] for line in out.stdout.splitlines() if "refs/tags/" in line]

    return list_tags


def check_versions(env: Mapping[str, str], fetch: Fetch, list_tags: ListTags) -> list[Result]:
    raw_base = env.get("CCW_RAW_BASE", DEFAULT_RAW_BASE)
    installed = installed_versions(env)
    results = []
    for plugin in PLUGINS:
        name = f"versions {plugin}"
        body = fetch(f"{raw_base}/plugins/{plugin}/.claude-plugin/plugin.json")
        latest = json.loads(body).get("version", "") if body else ""
        have = installed.get(plugin)
        if not latest:
            results.append(Result(name, SKIP, "latest release could not be read"))
        elif not have:
            results.append(Result(name, DRIFT, f"not installed, {latest} released: rebuild the setup script"))
        elif version_key(have) < version_key(latest):
            results.append(Result(name, DRIFT, f"{have} installed, {latest} released: change CCW_CACHE_BUST"))
        else:
            results.append(Result(name, OK, f"{have} is the latest"))

    name = "versions setup-script"
    pinned = read_release(env).get("CCW_RELEASE", "")
    tags = list_tags()
    if not pinned:
        results.append(Result(name, SKIP, "no release recorded by the setup script"))
    elif not tags:
        results.append(Result(name, SKIP, "released tags could not be read"))
    else:
        latest_tag = max(tags, key=version_key)
        if version_key(pinned) < version_key(latest_tag):
            results.append(Result(name, DRIFT, f"{pinned} pinned, {latest_tag} released: change CCW_RELEASE"))
        else:
            results.append(Result(name, OK, f"{pinned} is the latest"))
    return results


# --- CLI ---------------------------------------------------------------------------
CHECKS = ("git-identity", "aws-profiles", "versions")


def run_checks(
    names: list[str],
    env: Mapping[str, str],
    fix: bool,
    fetch: Fetch = curl_fetch,
    list_tags: ListTags | None = None,
) -> list[Result]:
    results: list[Result] = []
    for name in names or list(CHECKS):
        if name == "git-identity":
            results += check_git_identity(env, fix)
        elif name == "aws-profiles":
            results += check_aws_profiles(env, fix)
        else:
            tags = list_tags or git_tags(env.get("CCW_REPO", DEFAULT_REPO))
            results += check_versions(env, fetch, tags)
    return results


def main(argv: list[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("checks", nargs="*", metavar="check", help=f"any of: {', '.join(CHECKS)}")
    parser.add_argument("--fix", action="store_true", help="apply what a check can apply")
    parser.add_argument("--json", action="store_true", help="print results as JSON")
    args = parser.parse_args(argv)
    unknown = sorted(set(args.checks) - set(CHECKS))
    if unknown:
        parser.error(f"unknown check: {', '.join(unknown)}")
    results = run_checks(args.checks, os.environ if env is None else env, args.fix)
    if args.json:
        print(json.dumps([asdict(r) for r in results], indent=2))
    else:
        for r in results:
            print(f"{r.status.upper():<6} {r.check}: {r.detail}")
    return 1 if any(r.status == DRIFT for r in results) else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
