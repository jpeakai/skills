from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

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
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
    )


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


def tag(repo: Path, push: bool = False, dry_run: bool = False, remote: str = "origin") -> int:
    tags = missing_tags(repo)
    if not tags:
        print("Every plugin version is already tagged.")
        return 0
    for tag in tags:
        print(f"{'would tag' if dry_run else 'tag'} {tag}")
    if dry_run:
        return 0
    try:
        create_tags(repo, tags, push, remote)
    except RuntimeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if push:
        print(f"pushed {len(tags)} tag(s) to {remote}")
    return 0
