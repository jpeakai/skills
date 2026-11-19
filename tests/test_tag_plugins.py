"""Plugin release tags: real repositories and a real bare remote in tmp_path, no mocks."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "tag_plugins.py"
spec = importlib.util.spec_from_file_location("tag_plugins", SCRIPT)
assert spec and spec.loader
tag_plugins = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tag_plugins)

GIT_ID = ["-c", "user.name=Tester", "-c", "user.email=tester@example.com", "-c", "tag.gpgsign=false"]


def git(repo: Path, *args: str) -> str:
    out = subprocess.run(["git", "-C", str(repo), *GIT_ID, *args], capture_output=True, text=True, check=True)
    return out.stdout.strip()


def write_manifest(repo: Path, plugin: str, version: str) -> None:
    manifest = repo / "plugins" / plugin / ".claude-plugin" / "plugin.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({"name": plugin, "version": version}))


def commit(repo: Path, message: str) -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "--no-gpg-sign", "-m", message)


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A repository with two plugins, pushed to a bare remote named origin."""
    for key, value in {
        "GIT_AUTHOR_NAME": "Tester",
        "GIT_AUTHOR_EMAIL": "tester@example.com",
        "GIT_COMMITTER_NAME": "Tester",
        "GIT_COMMITTER_EMAIL": "tester@example.com",
        "GIT_CONFIG_GLOBAL": str(tmp_path / "gitconfig"),
        "GIT_CONFIG_NOSYSTEM": "1",
    }.items():
        monkeypatch.setenv(key, value)
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
    work = tmp_path / "work"
    subprocess.run(["git", "init", "-q", "-b", "main", str(work)], check=True)
    write_manifest(work, "jpai-ccw", "0.1.0")
    write_manifest(work, "jpai-essentials", "1.2.0")
    commit(work, "initial")
    git(work, "remote", "add", "origin", str(remote))
    git(work, "push", "-q", "origin", "main")
    return work


def remote_tags(repo: Path) -> set[str]:
    out = git(repo, "ls-remote", "--tags", "--refs", "origin")
    return {line.split("refs/tags/", 1)[1] for line in out.splitlines()}


def test_tag_name_drops_the_jpai_prefix() -> None:
    assert tag_plugins.tag_name("jpai-ccw", "0.1.0") == "ccw/v0.1.0"
    assert tag_plugins.tag_name("other", "2.0.0") == "other/v2.0.0"


def test_tags_every_untagged_version_and_pushes(repo: Path) -> None:
    assert tag_plugins.main(["--push"], repo) == 0
    assert remote_tags(repo) == {"ccw/v0.1.0", "essentials/v1.2.0"}
    assert git(repo, "cat-file", "-t", "ccw/v0.1.0") == "tag"


def test_rerun_creates_nothing(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    tag_plugins.main(["--push"], repo)
    capsys.readouterr()
    assert tag_plugins.main(["--push"], repo) == 0
    assert "already tagged" in capsys.readouterr().out


def test_bump_tags_only_the_new_version_and_keeps_old_tags(repo: Path) -> None:
    tag_plugins.main(["--push"], repo)
    first = git(repo, "rev-parse", "ccw/v0.1.0^{commit}")
    write_manifest(repo, "jpai-ccw", "0.2.0")
    commit(repo, "bump ccw")
    assert tag_plugins.missing_tags(repo) == ["ccw/v0.2.0"]
    tag_plugins.main(["--push"], repo)
    assert git(repo, "rev-parse", "ccw/v0.1.0^{commit}") == first
    assert git(repo, "rev-parse", "ccw/v0.2.0^{commit}") == git(repo, "rev-parse", "HEAD")


def test_dry_run_creates_nothing(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert tag_plugins.main(["--dry-run"], repo) == 0
    assert "would tag ccw/v0.1.0" in capsys.readouterr().out
    assert tag_plugins.missing_tags(repo) == ["ccw/v0.1.0", "essentials/v1.2.0"]


def test_without_push_tags_stay_local(repo: Path) -> None:
    assert tag_plugins.main([], repo) == 0
    assert tag_plugins.missing_tags(repo) == []
    assert remote_tags(repo) == set()


def test_push_failure_exits_one(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert tag_plugins.main(["--push", "--remote", "nowhere"], repo) == 1
    assert "git push failed" in capsys.readouterr().err


def test_tag_failure_exits_one(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write_manifest(repo, "jpai-ccw", "bad..version")
    assert tag_plugins.main([], repo) == 1
    assert "git tag ccw/vbad..version failed" in capsys.readouterr().err


def test_real_manifests_produce_valid_tag_names() -> None:
    repo = SCRIPT.parent.parent
    for plugin, version in tag_plugins.plugin_versions(repo).items():
        name = tag_plugins.tag_name(plugin, version)
        assert not name.startswith("jpai-")
        check = subprocess.run(["git", "check-ref-format", f"refs/tags/{name}"], check=False)
        assert check.returncode == 0, name
