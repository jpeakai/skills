"""Generated plugin commits use real Git repositories and a bare remote."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from ruamel.yaml import YAML

from plugin_ci.app import main

REPO = Path(__file__).resolve().parents[3]


def run(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], check=True, text=True, capture_output=True
    )
    return result.stdout.strip()


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "gitconfig"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    remote = tmp_path / "origin.git"
    run(tmp_path, "init", "--bare", str(remote))
    work = tmp_path / "work"
    run(tmp_path, "init", "-b", "main", str(work))
    run(work, "config", "user.name", "Tester")
    run(work, "config", "user.email", "tester@example.com")
    run(work, "config", "commit.gpgsign", "false")
    generated = work / "plugins/example/skills/example/SKILL.md"
    generated.parent.mkdir(parents=True)
    generated.write_text("old\n")
    (work / "README.md").write_text("canonical\n")
    run(work, "add", ".")
    run(work, "commit", "-m", "initial")
    run(work, "remote", "add", "origin", str(remote))
    run(work, "push", "-u", "origin", "main")
    return work


def invoke(repo: Path, *args: str) -> int:
    return main(["--project-dir", str(repo), *args])


def test_commits_and_pushes_only_generated_updates(repo: Path) -> None:
    (repo / "plugins/example/skills/example/SKILL.md").write_text("new\n")
    added = repo / "plugins/example/hooks/new.py"
    added.parent.mkdir()
    added.write_text("print(1)\n")
    assert invoke(repo, "commit", "--push") == 0
    assert run(repo, "status", "--porcelain") == ""
    assert run(repo, "rev-parse", "HEAD") == run(repo, "rev-parse", "origin/main")
    assert set(
        run(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines()
    ) == {"plugins/example/skills/example/SKILL.md", "plugins/example/hooks/new.py"}


def test_deletions_are_committed_and_reruns_do_nothing(repo: Path) -> None:
    (repo / "plugins/example/skills/example/SKILL.md").unlink()
    assert invoke(repo, "commit") == 0
    head = run(repo, "rev-parse", "HEAD")
    assert invoke(repo, "commit") == 0
    assert run(repo, "rev-parse", "HEAD") == head


@pytest.mark.parametrize(
    "path", ["README.md", "plugins/example/plugin.json", "plugins/example/README.md"]
)
def test_authored_changes_are_rejected(repo: Path, path: str) -> None:
    (repo / path).write_text("authored\n")
    assert invoke(repo, "check-worktree") == 1
    before = run(repo, "rev-parse", "HEAD")
    assert invoke(repo, "commit") == 1
    assert run(repo, "rev-parse", "HEAD") == before
    assert run(repo, "diff", "--cached", "--name-only") == ""


def test_check_allows_uncommitted_generated_output(repo: Path) -> None:
    (repo / "plugins/example/skills/example/SKILL.md").write_text("new\n")
    assert invoke(repo, "check-worktree") == 0


def test_existing_staged_changes_are_never_committed(repo: Path) -> None:
    (repo / "plugins/example/skills/example/SKILL.md").write_text("new\n")
    run(repo, "add", ".")
    before = run(repo, "rev-parse", "HEAD")
    assert invoke(repo, "commit") == 1
    assert run(repo, "rev-parse", "HEAD") == before
    assert run(repo, "diff", "--cached", "--name-only") == "plugins/example/skills/example/SKILL.md"


def test_publishing_from_feature_branch_is_rejected(repo: Path) -> None:
    run(repo, "switch", "-c", "feature")
    (repo / "plugins/example/skills/example/SKILL.md").write_text("new\n")
    assert invoke(repo, "commit", "--push") == 1
    assert run(repo, "log", "-1", "--format=%s") == "initial"


def test_non_fast_forward_push_fails_without_overwriting_remote(repo: Path, tmp_path: Path) -> None:
    other = tmp_path / "other"
    run(tmp_path, "clone", str(repo / ".git"), str(other))
    run(other, "config", "user.name", "Tester")
    run(other, "config", "user.email", "tester@example.com")
    run(other, "config", "commit.gpgsign", "false")
    (other / "README.md").write_text("concurrent update\n")
    run(other, "add", ".")
    run(other, "commit", "-m", "concurrent")
    remote = run(repo, "remote", "get-url", "origin")
    run(other, "push", remote, "HEAD:main")
    before = run(other, "rev-parse", "HEAD")
    (repo / "plugins/example/skills/example/SKILL.md").write_text("new\n")
    result = invoke(repo, "commit", "--push")
    assert result == 1
    assert run(repo, "ls-remote", "origin", "refs/heads/main").split()[0] == before


def test_workflow_validates_before_publishing_and_tags_the_sync_commit() -> None:

    workflow = YAML(typ="safe").load(
        (REPO / ".github/workflows/tag-plugin-versions.yml").read_text()
    )
    assert "pull_request" in workflow["on"]
    assert workflow["permissions"] == {"contents": "read"}
    release = workflow["jobs"]["tag"]
    assert release["permissions"] == {"contents": "write"}
    assert release["if"] == "github.event_name != 'pull_request' && github.ref == 'refs/heads/main'"
    for job in workflow["jobs"].values():
        setup = [
            step for step in job["steps"] if step.get("uses", "").startswith("astral-sh/setup-uv@")
        ]
        assert len(setup) == 1
        assert setup[0]["with"]["python-version"] == "3.12"
        assert setup[0]["with"]["enable-cache"] is True
        assert setup[0]["with"]["cache-dependency-glob"] == "uv.lock\ntools/plugin-ci/uv.lock\n"
    steps = release["steps"]
    assert steps[0]["with"]["ref"] == "main"
    commands = [step["run"] for step in steps if "run" in step]
    order = [
        "uv run --locked --project tools/plugin-ci plugin-ci sync",
        "uv run --locked --project tools/plugin-ci plugin-ci validate",
        "uv run --locked --directory tools/plugin-ci pytest\nuv run --locked pytest\n",
        "uv run --locked --project tools/plugin-ci plugin-ci commit --push",
        "uv run --locked --project tools/plugin-ci plugin-ci tag --push",
    ]
    assert [commands.index(command) for command in order] == sorted(
        commands.index(command) for command in order
    )
    assert not any(step.get("continue-on-error") for step in steps)
    pull_request = workflow["jobs"]["validate"]
    assert pull_request["if"] == "github.event_name == 'pull_request'"
    assert not any("push" in step.get("run", "") for step in pull_request["steps"])


def test_source_only_change_is_published_before_the_release_tag(repo: Path) -> None:

    (repo / "plugins/composition.yaml").write_text(
        "plugins:\n  example:\n    skills: [example]\n    hooks: false\n"
    )
    source = repo / "skills/example/SKILL.md"
    source.parent.mkdir(parents=True)
    source.write_text("canonical change\n")
    manifest = repo / "plugins/example/.claude-plugin/plugin.json"
    manifest.parent.mkdir()
    manifest.write_text(json.dumps({"name": "example", "version": "1.0.0"}))
    run(repo, "add", ".")
    run(repo, "commit", "-m", "canonical sources only")
    source_commit = run(repo, "rev-parse", "HEAD")
    subprocess.run(
        [sys.executable, "-m", "plugin_ci", "--project-dir", str(repo), "sync"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    assert invoke(repo, "check-worktree") == 0
    assert invoke(repo, "commit", "--push") == 0
    subprocess.run(
        [sys.executable, "-m", "plugin_ci", "--project-dir", str(repo), "tag", "--push"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    release = run(repo, "rev-parse", "example/v1.0.0^{commit}")
    assert release == run(repo, "rev-parse", "origin/main")
    assert release != source_commit
    assert (
        run(repo, "show", "example/v1.0.0:plugins/example/skills/example/SKILL.md")
        == "canonical change"
    )


def test_check_rejects_staged_authored_change_even_when_worktree_matches_head(
    repo: Path,
) -> None:
    path = repo / "README.md"
    path.write_text("staged authored change\n")
    run(repo, "add", "README.md")
    path.write_text("canonical\n")
    assert invoke(repo, "check-worktree") == 1
