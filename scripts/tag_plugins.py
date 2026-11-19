#!/usr/bin/env -S uv run --no-project
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Tag each plugin's current version, once.

For every ``plugins/<name>/.claude-plugin/plugin.json``, the release tag is the
plugin name without its ``jpai-`` prefix, then ``/v`` and the version:
``jpai-ccw`` at ``0.1.0`` is ``ccw/v0.1.0``. The ``ccw-setup`` stub downloads
its setup script from that tag (ADR-0005), so the name is a contract.

A tag that already exists is never moved or recreated: tags are immutable, and
the commit that first carried a version keeps it. Rerunning changes nothing.

    uv run scripts/tag_plugins.py                  # tag HEAD locally, report
    uv run scripts/tag_plugins.py --push           # also push new tags to origin
    uv run scripts/tag_plugins.py --dry-run        # report only

Exit codes: 0 on success (including nothing to tag), 1 when a git command fails.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PREFIX = "jpai-"


def tag_name(plugin: str, version: str) -> str:
    return f"{plugin.removeprefix(PREFIX)}/v{version}"


def plugin_versions(repo: Path) -> dict[str, str]:
    """Plugin name to version, read from each Claude manifest."""
    versions = {}
    for manifest in sorted(repo.glob("plugins/*/.claude-plugin/plugin.json")):
        data = json.loads(manifest.read_text(encoding="utf-8"))
        versions[data["name"]] = data["version"]
    return versions


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)


def tag_exists(repo: Path, tag: str) -> bool:
    return git(repo, "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}").returncode == 0


def missing_tags(repo: Path) -> list[str]:
    tags = [tag_name(plugin, version) for plugin, version in plugin_versions(repo).items()]
    return [tag for tag in tags if not tag_exists(repo, tag)]


def create_tags(repo: Path, tags: list[str], push: bool, remote: str = "origin") -> None:
    for tag in tags:
        result = git(repo, "tag", "-a", tag, "-m", f"Release {tag}")
        if result.returncode != 0:
            raise RuntimeError(f"git tag {tag} failed: {result.stderr.strip()}")
    if push and tags:
        result = git(repo, "push", remote, *(f"refs/tags/{tag}" for tag in tags))
        if result.returncode != 0:
            raise RuntimeError(f"git push failed: {result.stderr.strip()}")


def main(argv: list[str] | None = None, repo: Path = REPO) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--push", action="store_true", help="push new tags to the remote")
    parser.add_argument("--dry-run", action="store_true", help="report the tags without creating them")
    parser.add_argument("--remote", default="origin", help="remote to push to (default: origin)")
    args = parser.parse_args(argv)

    tags = missing_tags(repo)
    if not tags:
        print("Every plugin version is already tagged.")
        return 0
    for tag in tags:
        print(f"{'would tag' if args.dry_run else 'tag'} {tag}")
    if args.dry_run:
        return 0
    try:
        create_tags(repo, tags, args.push, args.remote)
    except RuntimeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if args.push:
        print(f"pushed {len(tags)} tag(s) to {args.remote}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
