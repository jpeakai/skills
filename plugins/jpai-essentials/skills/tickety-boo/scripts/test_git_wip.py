#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "pytest",
#   "pytest-cov",
# ]
# ///
"""Tests for git_wip.py, against real repositories: a bare origin and a clone of it."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

import git_wip

ME = "me@example.com"
OTHER = "other@example.com"
KEY = re.compile(r"SKILLS-\d+")


def sh(repo: Path, *args: str, email: str = ME) -> str:
    env_args = ["-c", f"user.email={email}", "-c", "user.name=Test"]
    run = subprocess.run(["git", *env_args, "-C", str(repo), *args], capture_output=True, text=True, check=True)
    return run.stdout.strip()


def commit(repo: Path, name: str, email: str = ME) -> str:
    (repo / name).write_text(name, encoding="utf-8")
    sh(repo, "add", name, email=email)
    sh(repo, "commit", "-q", "-m", name, email=email)
    return sh(repo, "rev-parse", "HEAD")


@pytest.fixture(autouse=True)
def isolated_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """No global or system git config reaches the tests."""
    empty = tmp_path / "gitconfig"
    empty.write_text("", encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    origin = tmp_path / "origin.git"
    seed = tmp_path / "seed"
    sh(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    sh(tmp_path, "init", "-q", "-b", "main", str(seed))
    commit(seed, "readme")
    sh(seed, "push", "-q", str(origin), "main")
    work = tmp_path / "work"
    sh(tmp_path, "clone", "-q", str(origin), str(work))
    sh(work, "config", "user.email", ME)
    sh(work, "config", "user.name", "Me")
    return work


def branch(repo: Path, name: str, email: str = ME, *, push: bool = False) -> str:
    sh(repo, "switch", "-q", "-c", name, "origin/main")
    sha = commit(repo, name.replace("/", "_"), email)
    if push:
        sh(repo, "push", "-q", "-u", "origin", name)
    sh(repo, "switch", "-q", "main")
    return sha


def merge_on_origin(repo: Path, name: str) -> None:
    sh(repo, "merge", "-q", "--no-ff", "-m", f"merge {name}", name)
    sh(repo, "push", "-q", "origin", "main")
    sh(repo, "fetch", "-q", "origin")


def squash_on_origin(repo: Path, name: str) -> None:
    sh(repo, "merge", "-q", "--squash", name)
    sh(repo, "commit", "-q", "-m", f"squash {name}")
    sh(repo, "push", "-q", "origin", "main")
    sh(repo, "fetch", "-q", "origin")


def by_name(report: dict, name: str) -> dict:
    return next(b for b in report["branches"] if b["name"] == name)


# ── status ──────────────────────────────────────────────────────────────────
def test_status_reports_branches_worktrees_keys_and_ownership(repo: Path) -> None:
    branch(repo, "feat/SKILLS-1-merged-work", push=True)
    merge_on_origin(repo, "feat/SKILLS-1-merged-work")
    branch(repo, "feat/SKILLS-2-open-work")
    branch(repo, "fix/someone-else", OTHER)
    wt = repo.parent / "SKILLS-2-open-work"
    sh(repo, "worktree", "add", "-q", str(wt), "feat/SKILLS-2-open-work")
    (wt / "scratch").write_text("x", encoding="utf-8")

    report = git_wip.status(wt, KEY, None)  # from inside a linked worktree

    assert report["repo"] == str(repo.resolve())
    assert report["user"] == {"name": "Me", "email": ME}
    assert report["default_branch"] == "origin/main"
    merged = by_name(report, "feat/SKILLS-1-merged-work")
    assert (merged["merged_into_default"], merged["mine"], merged["key"]) == (True, True, "SKILLS-1")
    assert merged["upstream"] == "origin/feat/SKILLS-1-merged-work"
    open_ = by_name(report, "feat/SKILLS-2-open-work")
    assert (open_["merged_into_default"], open_["unique_commits"], open_["upstream"]) == (False, 1, None)
    assert open_["worktree"] == str(wt.resolve())
    assert by_name(report, "fix/someone-else")["mine"] is False
    assert by_name(report, "fix/someone-else")["key"] is None
    main_wt, linked = report["worktrees"]
    assert main_wt["main"] and not linked["main"]
    assert (linked["key"], linked["dirty"], linked["branch"]) == ("SKILLS-2", True, "feat/SKILLS-2-open-work")


def test_upstream_gone_and_ahead_behind(repo: Path) -> None:
    branch(repo, "feat/gone", push=True)
    sh(repo, "push", "-q", "origin", "--delete", "feat/gone")
    sh(repo, "fetch", "-q", "--prune", "origin")
    branch(repo, "feat/ahead", push=True)
    sh(repo, "switch", "-q", "feat/ahead")
    commit(repo, "more")
    sh(repo, "switch", "-q", "main")

    report = git_wip.status(repo, None, None)

    assert by_name(report, "feat/gone")["upstream_gone"] is True
    assert by_name(report, "feat/gone")["key"] is None
    assert by_name(report, "feat/ahead")["ahead"] == 1


def test_default_branch_must_be_known_or_overridden(repo: Path) -> None:
    sh(repo, "remote", "set-head", "origin", "--delete")
    with pytest.raises(git_wip.WipError, match="origin/HEAD is not set"):
        git_wip.status(repo, None, None)
    assert git_wip.status(repo, None, "main")["default_branch"] == "origin/main"
    assert git_wip.status(repo, None, "origin/main")["default_branch"] == "origin/main"


def test_no_user_email_fails_loudly(repo: Path) -> None:
    sh(repo, "config", "--unset", "user.email")
    with pytest.raises(git_wip.WipError, match="user.email is not set"):
        git_wip.status(repo, None, None)


def test_a_failing_git_command_names_itself(tmp_path: Path) -> None:
    with pytest.raises(git_wip.WipError, match="git rev-parse"):
        git_wip.status(tmp_path, None, None)


# ── remove ──────────────────────────────────────────────────────────────────
def removal(repo: Path, **kw: object) -> dict:
    args = {"branch": None, "worktree": None, "expect_sha": None, "remote": False, "dry_run": False, "override": None}
    args.update(kw)
    return git_wip.remove(repo, **args)  # type: ignore[arg-type]


def test_merged_branch_goes_with_its_worktree_and_remote(repo: Path) -> None:
    name = "feat/SKILLS-3-done"
    branch(repo, name, push=True)
    merge_on_origin(repo, name)
    wt = repo.parent / "SKILLS-3-done"
    sh(repo, "worktree", "add", "-q", str(wt), name)

    planned = removal(repo, branch=name, remote=True, dry_run=True)
    assert planned["steps"] == [
        ["git", "worktree", "remove", str(wt.resolve())],
        ["git", "branch", "-D", name],
        ["git", "push", "origin", "--delete", name],
    ]
    assert wt.exists() and sh(repo, "branch", "--list", name)  # a dry run touches nothing

    removal(repo, branch=name, remote=True)
    assert not wt.exists()
    assert sh(repo, "branch", "--list", name) == ""
    assert sh(repo, "ls-remote", "--heads", "origin", name) == ""


def test_squash_merge_needs_the_merged_head(repo: Path) -> None:
    name = "feat/SKILLS-4-squashed"
    sha = branch(repo, name, push=True)
    squash_on_origin(repo, name)

    with pytest.raises(git_wip.WipError, match="pass --expect-sha"):
        removal(repo, branch=name)
    with pytest.raises(git_wip.WipError, match="does not contain"):
        removal(repo, branch=name, expect_sha=sh(repo, "rev-parse", "origin/main~1"))
    done = removal(repo, branch=name, expect_sha=sha)
    assert done["steps"] == [["git", "branch", "-D", name]]
    assert sh(repo, "branch", "--list", name) == ""


def test_a_branch_behind_the_merged_head_may_go(repo: Path) -> None:
    name = "feat/behind"
    old = branch(repo, name, push=True)
    sh(repo, "switch", "-q", name)
    head = commit(repo, "pushed-later")
    sh(repo, "push", "-q", "origin", name)
    sh(repo, "reset", "-q", "--hard", old)
    sh(repo, "switch", "-q", "main")
    squash_on_origin(repo, head)
    assert removal(repo, branch=name, expect_sha=head, dry_run=True)["steps"] == [["git", "branch", "-D", name]]


def test_unsafe_removals_are_refused(repo: Path) -> None:
    name = "feat/SKILLS-5-dirty"
    branch(repo, name, push=True)
    merge_on_origin(repo, name)
    wt = repo.parent / "dirty"
    sh(repo, "worktree", "add", "-q", str(wt), name)
    (wt / "unsaved").write_text("x", encoding="utf-8")

    with pytest.raises(git_wip.WipError, match="uncommitted changes"):
        removal(repo, branch=name)
    with pytest.raises(git_wip.WipError, match="main worktree; it is never removed"):
        removal(repo, worktree=repo)
    with pytest.raises(git_wip.WipError, match="is not a worktree"):
        removal(repo, worktree=repo.parent / "nowhere")
    with pytest.raises(git_wip.WipError, match="no local branch"):
        removal(repo, branch="feat/ghost")
    with pytest.raises(git_wip.WipError, match="main worktree; it is never removed"):
        removal(repo, branch="main")
    sh(repo, "switch", "-q", "--detach")
    with pytest.raises(git_wip.WipError, match="is the default branch"):
        removal(repo, branch="main")

    sh(repo, "worktree", "lock", str(wt))
    with pytest.raises(git_wip.WipError, match="is locked"):
        removal(repo, worktree=wt)


def test_a_worktree_alone_keeps_its_branch_and_a_vanished_one_is_pruned(repo: Path) -> None:
    branch(repo, "feat/keep")
    wt = repo.parent / "keep"
    sh(repo, "worktree", "add", "-q", str(wt), "feat/keep")
    removal(repo, worktree=wt)
    assert not wt.exists() and sh(repo, "branch", "--list", "feat/keep")

    gone = repo.parent / "gone"
    sh(repo, "worktree", "add", "-q", str(gone), "feat/keep")
    gone.rename(repo.parent / "moved-away")
    assert removal(repo, worktree=gone)["steps"] == [["git", "worktree", "prune"]]
    assert len(git_wip.worktrees(repo)) == 1


def test_a_fresh_branch_is_not_merged_and_needs_proof(repo: Path) -> None:
    sh(repo, "branch", "--no-track", "feat/SKILLS-7-just-started", "origin/main")
    report = git_wip.status(repo, KEY, None)
    fresh = by_name(report, "feat/SKILLS-7-just-started")
    assert (fresh["fresh"], fresh["merged_into_default"], fresh["default"]) == (True, False, False)
    assert by_name(report, "main")["default"] is True

    with pytest.raises(git_wip.WipError, match="no commits of its own yet"):
        removal(repo, branch="feat/SKILLS-7-just-started")
    tip = sh(repo, "rev-parse", "origin/main")
    assert removal(repo, branch="feat/SKILLS-7-just-started", expect_sha=tip, dry_run=True)["steps"] == [
        ["git", "branch", "-D", "feat/SKILLS-7-just-started"]
    ]


# ── CLI ─────────────────────────────────────────────────────────────────────
def test_cli_status_text_and_json(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    branch(repo, "feat/SKILLS-6-cli", push=True)
    branch(repo, "feat/local")
    branch(repo, "feat/gone", push=True)
    sh(repo, "push", "-q", "origin", "--delete", "feat/gone")
    sh(repo, "fetch", "-q", "--prune", "origin")
    wt = repo.parent / "SKILLS-6-cli"
    sh(repo, "worktree", "add", "-q", str(wt), "feat/SKILLS-6-cli")
    sh(repo, "worktree", "add", "-q", "--detach", str(repo.parent / "detached"))

    git_wip.main(["--repo", str(repo), "status", "--key-pattern", r"SKILLS-\d+"])
    text = capsys.readouterr().out
    assert "user: Me <me@example.com>" in text
    assert "feat/SKILLS-6-cli  [SKILLS-6]  mine, 1 unique, upstream origin/feat/SKILLS-6-cli, worktree" in text
    assert "feat/local  [-]  mine, 1 unique, local only" in text
    assert "upstream gone" in text
    assert "detached  clean" in text
    assert "main  [-]  mine, default branch" in text
    sh(repo, "branch", "--no-track", "feat/fresh", "origin/main")
    git_wip.main(["--repo", str(repo), "status"])
    assert "feat/fresh  [-]  mine, no commits yet" in capsys.readouterr().out

    git_wip.main(["--repo", str(repo), "status", "--json"])
    assert json.loads(capsys.readouterr().out)["default_branch"] == "origin/main"


def test_cli_remove_and_help(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(git_wip.WipError, match="needs --branch or --worktree"):
        git_wip.main(["--repo", str(repo), "remove"])
    branch(repo, "feat/x", push=True)
    merge_on_origin(repo, "feat/x")
    git_wip.main(["--repo", str(repo), "remove", "--branch", "feat/x", "--dry-run"])
    assert json.loads(capsys.readouterr().out)["dry_run"] is True
    git_wip.main([])
    assert "status" in capsys.readouterr().out


def test_script_exits_1_with_the_message(tmp_path: Path) -> None:
    run = subprocess.run(
        ["python3", str(Path(git_wip.__file__)), "--repo", str(tmp_path), "status"],
        capture_output=True,
        check=False,
        text=True,
    )
    assert run.returncode == 1
    assert run.stderr.startswith("error: git rev-parse")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, *sys.argv[1:]]))
