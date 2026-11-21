#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest>=8.0", "pytest-cov>=4.0"]
# ///
"""Tests for ccw_check.py: real git, real config files and real remotes in tmp_path, no mocks.

Network-facing checks take their fetchers as arguments. The default fetchers are
exercised against a local git repository and file:// URLs.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

import ccw_check
from ccw_check import DRIFT, FIXED, OK, SKIP


@pytest.fixture
def env(tmp_path: Path) -> dict[str, str]:
    home = tmp_path / "home"
    home.mkdir()
    return {
        "HOME": str(home),
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "GIT_CONFIG_GLOBAL": str(home / ".gitconfig"),
        "GIT_CONFIG_NOSYSTEM": "1",
        "AWS_CONFIG_FILE": str(home / ".aws" / "config"),
        "CCW_RELEASE_FILE": str(tmp_path / "release"),
    }


def statuses(results: list[ccw_check.Result]) -> dict[str, str]:
    return {r.check: r.status for r in results}


# --- git identity -----------------------------------------------------------
def test_git_identity_skips_without_values(env: dict[str, str]) -> None:
    got = ccw_check.check_git_identity(env, fix=True)
    assert [(r.status, r.detail) for r in got] == [(SKIP, "CCW_GIT_AUTHOR_NAME is not set")]


def test_git_identity_never_applies_half_an_identity(env: dict[str, str]) -> None:
    env |= {"CCW_GIT_AUTHOR_NAME": "Ada Example"}
    got = ccw_check.check_git_identity(env, fix=True)
    assert [(r.status, r.detail) for r in got] == [(SKIP, "CCW_GIT_AUTHOR_EMAIL is not set")]
    assert ccw_check._git_get("author.name", env) == ""


def test_git_identity_reports_then_fixes_then_is_clean(env: dict[str, str]) -> None:
    env |= {"CCW_GIT_AUTHOR_NAME": "Ada Example", "CLAUDE_CODE_USER_EMAIL": "ada@example.com"}
    assert set(statuses(ccw_check.check_git_identity(env, fix=False)).values()) == {DRIFT}
    assert set(statuses(ccw_check.check_git_identity(env, fix=True)).values()) == {FIXED}
    assert set(statuses(ccw_check.check_git_identity(env, fix=True)).values()) == {OK}
    config = Path(env["GIT_CONFIG_GLOBAL"]).read_text()
    assert "Ada Example" in config and "ada@example.com" in config


def test_git_identity_leaves_the_committer_alone(env: dict[str, str]) -> None:
    subprocess.run(["git", "config", "--global", "user.name", "Signer"], check=True, env=env)
    env |= {"CCW_GIT_AUTHOR_NAME": "Ada Example", "CCW_GIT_AUTHOR_EMAIL": "ada@example.com"}
    ccw_check.check_git_identity(env, fix=True)
    assert ccw_check._git_get("user.name", env) == "Signer"
    assert ccw_check._git_get("author.name", env) == "Ada Example"


def test_explicit_author_email_wins_over_session_email(env: dict[str, str]) -> None:
    env |= {
        "CCW_GIT_AUTHOR_NAME": "Ada Example",
        "CCW_GIT_AUTHOR_EMAIL": "work@example.com",
        "CLAUDE_CODE_USER_EMAIL": "home@example.com",
    }
    ccw_check.check_git_identity(env, fix=True)
    assert ccw_check._git_get("author.email", env) == "work@example.com"


# --- AWS profiles -------------------------------------------------------------
ARN = "arn:aws:iam::111122223333:role/Worker"
ADMIN_ARN = "arn:aws:iam::111122223333:role/WorkerAdmin"


def test_aws_profiles_skip_when_nothing_is_configured(env: dict[str, str]) -> None:
    got = statuses(ccw_check.check_aws_profiles(env, fix=True))
    assert got == {"aws-profiles ccw": SKIP, "aws-profiles ccw-admin": SKIP}
    assert not Path(env["AWS_CONFIG_FILE"]).exists()


def test_aws_profiles_create_from_environment(env: dict[str, str]) -> None:
    env |= {"CCW_ROLE_ARN": ARN, "CCW_AWS_REGION": "eu-west-1"}
    assert statuses(ccw_check.check_aws_profiles(env, fix=False))["aws-profiles ccw"] == DRIFT
    assert statuses(ccw_check.check_aws_profiles(env, fix=True))["aws-profiles ccw"] == FIXED
    assert statuses(ccw_check.check_aws_profiles(env, fix=True))["aws-profiles ccw"] == OK
    config = Path(env["AWS_CONFIG_FILE"]).read_text()
    assert "[profile ccw]" in config and ARN in config and "credential_source = Environment" in config
    assert "region = eu-west-1" in config


def test_admin_external_id_added_to_a_profile_the_setup_script_wrote(env: dict[str, str]) -> None:
    path = Path(env["AWS_CONFIG_FILE"])
    path.parent.mkdir(parents=True)
    path.write_text(f"[profile ccw-admin]\nrole_arn = {ADMIN_ARN}\ncredential_source = Environment\n")
    env |= {"CCW_ADMIN_EXTERNAL_ID": "s3cret-value"}
    results = ccw_check.check_aws_profiles(env, fix=True)
    assert statuses(results)["aws-profiles ccw-admin"] == FIXED
    assert "s3cret-value" not in json.dumps([r.detail for r in results])
    assert "external_id = s3cret-value" in path.read_text()
    assert ADMIN_ARN in path.read_text()


def test_admin_profile_defaults_region_from_session(env: dict[str, str]) -> None:
    env |= {"CCW_ADMIN_ROLE_ARN": ADMIN_ARN, "AWS_DEFAULT_REGION": "ap-southeast-2"}
    ccw_check.check_aws_profiles(env, fix=True)
    assert "region = ap-southeast-2" in Path(env["AWS_CONFIG_FILE"]).read_text()


def test_aws_config_defaults_under_home(env: dict[str, str]) -> None:
    del env["AWS_CONFIG_FILE"]
    assert ccw_check.aws_config_path(env) == Path(env["HOME"]) / ".aws" / "config"


# --- versions ------------------------------------------------------------------
def write_installed(env: dict[str, str], versions: dict[str, str]) -> None:
    path = Path(env["HOME"]) / ".claude" / "plugins" / "installed_plugins.json"
    path.parent.mkdir(parents=True)
    plugins = {f"{p}@jpeakai": [{"version": v}] for p, v in versions.items()}
    path.write_text(json.dumps({"version": 2, "plugins": plugins}))


def published(versions: dict[str, str]) -> ccw_check.Fetch:
    def fetch(url: str) -> str | None:
        for plugin, version in versions.items():
            if f"/plugins/{plugin}/" in url:
                return json.dumps({"version": version})
        return None

    return fetch


def test_versions_all_current(env: dict[str, str]) -> None:
    write_installed(env, {"jpai-essentials": "1.2.0", "jpai-ccw": "0.1.0"})
    Path(env["CCW_RELEASE_FILE"]).write_text("CCW_RELEASE=ccw/v0.1.0\nCCW_CACHE_BUST=2026-01-01\n")
    fetch = published({"jpai-essentials": "1.2.0", "jpai-ccw": "0.1.0"})
    got = statuses(ccw_check.check_versions(env, fetch, lambda: ["ccw/v0.1.0"]))
    assert set(got.values()) == {OK}


def test_versions_report_lag_and_name_the_change(env: dict[str, str]) -> None:
    write_installed(env, {"jpai-essentials": "1.2.0"})
    Path(env["CCW_RELEASE_FILE"]).write_text("CCW_RELEASE=ccw/v0.1.0\n")
    fetch = published({"jpai-essentials": "1.10.0", "jpai-ccw": "0.2.0"})
    results = ccw_check.check_versions(env, fetch, lambda: ["ccw/v0.1.0", "ccw/v0.10.0", "ccw/v0.2.0"])
    by_check = {r.check: r for r in results}
    assert by_check["versions jpai-essentials"].status == DRIFT
    assert "CCW_CACHE_BUST" in by_check["versions jpai-essentials"].detail
    assert by_check["versions jpai-ccw"].status == DRIFT
    assert by_check["versions setup-script"].status == DRIFT
    assert "ccw/v0.10.0" in by_check["versions setup-script"].detail


def test_versions_skip_when_nothing_can_be_read(env: dict[str, str]) -> None:
    got = statuses(ccw_check.check_versions(env, lambda url: None, lambda: None))
    assert set(got.values()) == {SKIP}


def test_versions_skip_when_tags_unreadable(env: dict[str, str]) -> None:
    Path(env["CCW_RELEASE_FILE"]).write_text("CCW_RELEASE=ccw/v0.1.0\n")
    got = statuses(ccw_check.check_versions(env, lambda url: None, lambda: None))
    assert got["versions setup-script"] == SKIP


def test_default_fetchers_against_real_sources(tmp_path: Path) -> None:
    repo = tmp_path / "remote"
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    git = ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.com"]
    subprocess.run([*git, "commit", "-q", "--allow-empty", "--no-gpg-sign", "-m", "x"], check=True)
    for tag in ("ccw/v0.1.0", "ccw/v0.2.0", "other"):
        subprocess.run([*git, "tag", tag], check=True)
    assert sorted(ccw_check.git_tags(str(repo))() or []) == ["ccw/v0.1.0", "ccw/v0.2.0"]
    assert ccw_check.git_tags(str(tmp_path / "missing"))() is None

    page = tmp_path / "plugin.json"
    page.write_text('{"version": "9.9.9"}')
    assert ccw_check.curl_fetch(page.as_uri()) == '{"version": "9.9.9"}'
    assert ccw_check.curl_fetch((tmp_path / "absent").as_uri()) is None


def test_installed_versions_honours_claude_config_dir(env: dict[str, str], tmp_path: Path) -> None:
    env["CLAUDE_CONFIG_DIR"] = str(tmp_path / "cfg")
    assert ccw_check.installed_versions(env) == {}


# --- CLI ------------------------------------------------------------------------------
def test_aws_profile_written_elsewhere_with_nothing_to_compare(env: dict[str, str]) -> None:
    path = Path(env["AWS_CONFIG_FILE"])
    path.parent.mkdir(parents=True)
    path.write_text(f"[profile ccw]\nrole_arn = {ARN}\n")
    results = {r.check: r for r in ccw_check.check_aws_profiles(env, fix=False)}
    assert results["aws-profiles ccw"].detail == "no saved variables to compare"


def test_main_exit_codes_and_json(env: dict[str, str], capsys: pytest.CaptureFixture[str]) -> None:
    env |= {"CCW_GIT_AUTHOR_NAME": "Ada Example", "CLAUDE_CODE_USER_EMAIL": "ada@example.com"}
    assert ccw_check.main(["git-identity"], env) == 1
    assert ccw_check.main(["git-identity", "--fix"], env) == 0
    capsys.readouterr()
    assert ccw_check.main(["git-identity", "aws-profiles", "--json"], env) == 0
    rows = json.loads(capsys.readouterr().out)
    assert {"check", "status", "detail"} <= rows[0].keys()


def test_main_rejects_unknown_check(env: dict[str, str]) -> None:
    with pytest.raises(SystemExit) as exc:
        ccw_check.main(["nonsense"], env)
    assert exc.value.code == 2


def test_run_checks_runs_versions_with_injected_sources(env: dict[str, str]) -> None:
    results = ccw_check.run_checks(["versions"], env, fix=False, fetch=lambda u: None, list_tags=lambda: None)
    assert {r.status for r in results} == {SKIP}


def test_run_checks_defaults_to_every_check(env: dict[str, str], tmp_path: Path) -> None:
    env["CCW_REPO"] = str(tmp_path / "missing")
    env["CCW_RAW_BASE"] = (tmp_path / "missing").as_uri()
    checks = {r.check.split()[0] for r in ccw_check.run_checks([], env, fix=False)}
    assert checks == {"git-identity", "aws-profiles", "versions"}


if __name__ == "__main__":  # pragma: no cover
    script_dir = str(Path(__file__).parent.resolve())
    base_args = [__file__, "-v", "--rootdir", script_dir, "-o", "addopts="]
    sys.exit(pytest.main(base_args + sys.argv[1:]))
