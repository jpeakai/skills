#!/usr/bin/env python3
"""Report the local git side of work in progress, and remove finished branches and worktrees safely.

The ticketing system and the forge (issues, PRs) are read by the agent through the commands
a repo's TICKETING.md documents. This script owns only what every repo shares: local branches
and git worktrees. Stdlib only (Tier B).

    uv run --no-project skills/tickety-boo/scripts/git_wip.py status --key-pattern 'SKILLS-(\\d+)'
    uv run --no-project skills/tickety-boo/scripts/git_wip.py remove --branch feat/SKILLS-7-x --expect-sha abc123
    uv run --no-project skills/tickety-boo/scripts/git_wip.py remove --worktree .claude/worktrees/SKILLS-7-x
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

# ── Configuration ───────────────────────────────────────────────────────────
REMOTE = "origin"
FIELD_SEP = "\x1f"
REF_FORMAT = FIELD_SEP.join(
    [
        "%(refname:short)",
        "%(objectname)",
        "%(upstream:short)",
        "%(upstream:track)",
        "%(committerdate:iso-strict)",
        "%(authoremail:trim)",
    ]
)


class WipError(SystemExit):
    """A loud, user-facing failure: the message is printed and the exit code is 1."""

    def __init__(self, message: str) -> None:
        super().__init__(f"error: {message}")


# ── Git ─────────────────────────────────────────────────────────────────────
def git(repo: Path, *args: str, check: bool = True) -> str:
    run = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)
    if check and run.returncode != 0:
        raise WipError(f"git {' '.join(args)} failed: {run.stderr.strip()}")
    return run.stdout.strip()


def succeeds(repo: Path, *args: str) -> bool:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=False).returncode == 0


def toplevel(repo: Path) -> Path:
    """The main worktree's root, so every report is the same from any worktree."""
    common = Path(git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    return common.parent if common.name == ".git" else Path(git(repo, "rev-parse", "--show-toplevel"))


def default_branch(repo: Path, override: str | None) -> str:
    """The remote's default branch as `origin/<name>`. Never guessed."""
    if override:
        return override if "/" in override else f"{REMOTE}/{override}"
    ref = git(repo, "symbolic-ref", "--quiet", f"refs/remotes/{REMOTE}/HEAD", check=False)
    if not ref:
        raise WipError(
            f"{REMOTE}/HEAD is not set, so the default branch is unknown. "
            f"Run `git remote set-head {REMOTE} --auto`, or pass --default-branch."
        )
    return ref.removeprefix("refs/remotes/")


def user(repo: Path) -> dict[str, str]:
    name = git(repo, "config", "user.name", check=False)
    email = git(repo, "config", "user.email", check=False)
    if not email:
        raise WipError("git config user.email is not set, so no branch can be attributed to anyone")
    return {"name": name, "email": email}


def key_of(pattern: re.Pattern[str] | None, *texts: str) -> str | None:
    """The ticket key a branch or worktree name carries, per TICKETING.md's naming rule."""
    if pattern is None:
        return None
    for text in texts:
        match = pattern.search(text)
        if match:
            return match.group(0)
    return None


# ── Worktrees ───────────────────────────────────────────────────────────────
def worktrees(repo: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    entry: dict[str, Any] = {}
    for line in git(repo, "worktree", "list", "--porcelain").splitlines() + [""]:
        if not line:
            if entry:
                out.append(entry)
            entry = {}
            continue
        key, _, value = line.partition(" ")
        if key == "worktree":
            entry = {"path": value, "branch": None, "detached": False, "locked": False, "prunable": False}
        elif key == "HEAD":
            entry["head"] = value
        elif key == "branch":
            entry["branch"] = value.removeprefix("refs/heads/")
        elif key in ("detached", "locked", "prunable"):
            entry[key] = True
    for i, wt in enumerate(out):
        wt["main"] = i == 0
        wt["dirty"] = False if wt["prunable"] else bool(git(Path(wt["path"]), "status", "--porcelain"))
    return out


# ── Branches ────────────────────────────────────────────────────────────────
def merged(repo: Path, sha: str, default: str) -> bool:
    """Merged into the remote default by ancestry. A tip AT the default tip is a branch with no
    commits yet, not finished work, so it never counts: deleting it needs the forge's proof."""
    return sha != git(repo, "rev-parse", default) and succeeds(repo, "merge-base", "--is-ancestor", sha, default)


def branches(repo: Path, default: str, email: str, trees: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checked_out = {wt["branch"]: wt["path"] for wt in trees if wt["branch"]}
    tip = git(repo, "rev-parse", default)
    out = []
    for line in git(repo, "for-each-ref", f"--format={REF_FORMAT}", "refs/heads").splitlines():
        name, sha, upstream, track, date, tip_author = line.split(FIELD_SEP)
        own = git(repo, "log", "--format=%ae", f"{default}..{sha}").splitlines()
        authors = own or [tip_author]
        # A branch cut from the default branch tracks it until first pushed; that is not its own.
        own_upstream = bool(upstream) and upstream != default
        ahead = re.search(r"ahead (\d+)", track) if own_upstream else None
        behind = re.search(r"behind (\d+)", track) if own_upstream else None
        out.append(
            {
                "name": name,
                "sha": sha,
                "upstream": upstream if own_upstream else None,
                "upstream_gone": track == "[gone]",
                "ahead": int(ahead.group(1)) if ahead else 0,
                "behind": int(behind.group(1)) if behind else 0,
                "default": name == default.split("/", 1)[1],
                "unique_commits": len(own),
                "fresh": sha == tip,
                "merged_into_default": merged(repo, sha, default),
                "mine": email.lower() in (a.lower() for a in authors),
                "last_commit": date,
                "worktree": checked_out.get(name),
            }
        )
    return out


def status(repo: Path, pattern: re.Pattern[str] | None, override: str | None) -> dict[str, Any]:
    root = toplevel(repo)
    default = default_branch(root, override)
    me = user(root)
    trees = worktrees(root)
    heads = branches(root, default, me["email"], trees)
    for b in heads:
        b["key"] = key_of(pattern, b["name"])
    for wt in trees:
        wt["key"] = key_of(pattern, wt["branch"] or "", Path(wt["path"]).name)
    return {"repo": str(root), "user": me, "default_branch": default, "branches": heads, "worktrees": trees}


# ── Removal ─────────────────────────────────────────────────────────────────
def find_worktree(
    trees: list[dict[str, Any]], *, path: Path | None = None, branch: str | None = None
) -> dict[str, Any] | None:
    for wt in trees:
        if path is not None and Path(wt["path"]).resolve() == path.resolve():
            return wt
        if branch is not None and wt["branch"] == branch:
            return wt
    return None


def worktree_steps(wt: dict[str, Any]) -> list[list[str]]:
    if wt["main"]:
        raise WipError(f"{wt['path']} is the main worktree; it is never removed")
    if wt["locked"]:
        raise WipError(f"worktree {wt['path']} is locked; unlock it first if it is really finished")
    if wt["prunable"]:
        return [["worktree", "prune"]]
    if wt["dirty"]:
        raise WipError(f"worktree {wt['path']} has uncommitted changes; commit or discard them first")
    return [["worktree", "remove", wt["path"]]]


def branch_steps(root: Path, name: str, expect_sha: str | None, default: str) -> list[list[str]]:
    sha = git(root, "rev-parse", "--verify", "--quiet", f"refs/heads/{name}", check=False)
    if not sha:
        raise WipError(f"no local branch {name!r}")
    if name == default.split("/", 1)[1]:
        raise WipError(f"{name} is the default branch; it is never removed")
    # Merged is decided here, against the remote default, so `-D` is safe; `-d` would judge
    # against a stale local HEAD or the branch's own upstream instead.
    if merged(root, sha, default):
        return [["branch", "-D", name]]
    # A squash or rebase merge leaves the branch unmerged by ancestry. The forge's record of
    # the merged head is then the proof: the local tip must be that head, or behind it.
    if expect_sha is None and sha == git(root, "rev-parse", default):
        raise WipError(f"{name} has no commits of its own yet; pass --expect-sha if its PR really merged")
    if expect_sha is None:
        raise WipError(
            f"{name} is not merged into {default} by ancestry. If its PR was squash or rebase merged, "
            "pass --expect-sha with the PR's head commit"
        )
    if sha != expect_sha and not succeeds(root, "merge-base", "--is-ancestor", sha, expect_sha):
        raise WipError(f"{name} is at {sha[:12]}, which the merged head {expect_sha[:12]} does not contain")
    return [["branch", "-D", name]]


def remove(
    repo: Path,
    *,
    branch: str | None,
    worktree: Path | None,
    expect_sha: str | None,
    remote: bool,
    dry_run: bool,
    override: str | None,
) -> dict[str, Any]:
    root = toplevel(repo)
    trees = worktrees(root)
    steps: list[list[str]] = []
    if worktree is not None:
        wt = find_worktree(trees, path=worktree)
        if wt is None:
            raise WipError(f"{worktree} is not a worktree of {root}")
        steps += worktree_steps(wt)
    if branch is not None:
        default = default_branch(root, override)
        wt = find_worktree(trees, branch=branch)
        if wt is not None:
            steps += worktree_steps(wt)
        steps += branch_steps(root, branch, expect_sha, default)
        if remote and git(root, "ls-remote", "--heads", REMOTE, branch):
            steps.append(["push", REMOTE, "--delete", branch])
    if not dry_run:
        for step in steps:
            git(root, *step)
    return {"repo": str(root), "dry_run": dry_run, "steps": [["git", *s] for s in steps]}


# ── CLI ─────────────────────────────────────────────────────────────────────
def cmd_status(args: argparse.Namespace) -> None:
    pattern = re.compile(args.key_pattern) if args.key_pattern else None
    report = status(Path(args.repo), pattern, args.default_branch)
    if args.json:
        print(json.dumps(report, indent=2))
        return
    print(f"user: {report['user']['name']} <{report['user']['email']}>")
    print(f"default branch: {report['default_branch']}")
    print("branches:")
    for b in report["branches"]:
        if b["default"]:
            state = "default branch"
        elif b["fresh"]:
            state = "no commits yet"
        else:
            state = "merged" if b["merged_into_default"] else f"{b['unique_commits']} unique"
        flags = [
            "mine" if b["mine"] else "other",
            state,
            "upstream gone" if b["upstream_gone"] else (f"upstream {b['upstream']}" if b["upstream"] else "local only"),
        ]
        if b["worktree"]:
            flags.append(f"worktree {b['worktree']}")
        print(f"  {b['name']}  [{b['key'] or '-'}]  {', '.join(flags)}")
    print("worktrees:")
    for wt in report["worktrees"]:
        state = "main" if wt["main"] else ("prunable" if wt["prunable"] else ("dirty" if wt["dirty"] else "clean"))
        print(f"  {wt['path']}  [{wt['key'] or '-'}]  {wt['branch'] or 'detached'}  {state}")


def cmd_remove(args: argparse.Namespace) -> None:
    if args.branch is None and args.worktree is None:
        raise WipError("remove needs --branch or --worktree")
    report = remove(
        Path(args.repo),
        branch=args.branch,
        worktree=Path(args.worktree) if args.worktree else None,
        expect_sha=args.expect_sha,
        remote=args.remote,
        dry_run=args.dry_run,
        override=args.default_branch,
    )
    print(json.dumps(report, indent=2))


def build_parser() -> argparse.ArgumentParser:
    def _help(p: argparse.ArgumentParser) -> Callable[[argparse.Namespace], None]:
        def _print_help(_: argparse.Namespace) -> None:
            p.print_help()

        return _print_help

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--repo", default=".", help="Any directory inside the repository (default: cwd)")
    parser.add_argument("--default-branch", help="Override origin/HEAD, e.g. main or origin/main")
    parser.set_defaults(func=_help(parser))
    sub = parser.add_subparsers(dest="command", required=False)

    st = sub.add_parser("status", help="Local branches and worktrees, with ticket keys and merge state")
    st.add_argument("--key-pattern", help="Regex for the ticket key in branch names, from TICKETING.md")
    st.add_argument("--json", action="store_true", help="Emit the report as JSON on stdout")
    st.set_defaults(func=cmd_status)

    rm = sub.add_parser("remove", help="Remove a finished branch (and its worktree) or a worktree")
    rm.add_argument("--branch", help="Local branch to delete; its worktree goes first")
    rm.add_argument("--worktree", help="Worktree path to remove; its branch is kept")
    rm.add_argument("--expect-sha", help="The merged PR's head commit, for a squash or rebase merge")
    rm.add_argument("--remote", action="store_true", help=f"Also delete the branch on {REMOTE} if it is there")
    rm.add_argument("--dry-run", action="store_true", help="Print the git steps, run none")
    rm.set_defaults(func=cmd_remove)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    try:
        main()
    except WipError as err:
        print(err.code, file=sys.stderr)
        raise SystemExit(1) from None
