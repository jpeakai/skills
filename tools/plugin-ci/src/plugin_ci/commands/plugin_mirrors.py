from __future__ import annotations

import subprocess
from pathlib import Path


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], text=True, capture_output=True, check=False
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip())
    return result.stdout


def changed_paths(repo: Path) -> list[str]:
    staged = git(repo, "diff", "--cached", "--no-renames", "--name-only", "-z")
    unstaged = git(repo, "diff", "--no-renames", "--name-only", "-z")
    untracked = git(repo, "ls-files", "--others", "--exclude-standard", "-z")
    return sorted(set((staged + unstaged + untracked).split("\0")) - {""})


GENERATED_PATH_PARTS = 4


def is_generated(path: str) -> bool:
    parts = Path(path).parts
    return (
        len(parts) >= GENERATED_PATH_PARTS
        and parts[0] == "plugins"
        and parts[2] in {"skills", "hooks"}
    )


def check_worktree(repo: Path) -> list[str]:
    paths = changed_paths(repo)
    authored = [path for path in paths if not is_generated(path)]
    if authored:
        raise RuntimeError("Authored files have uncommitted changes:\n" + "\n".join(authored))
    return paths


def commit_mirrors(repo: Path, push: bool) -> None:
    if git(repo, "branch", "--show-current").strip() != "main":
        raise RuntimeError("Generated plugin commits must be made on main.")
    if git(repo, "diff", "--cached", "--name-only"):
        raise RuntimeError("The index must be empty before committing generated plugins.")
    paths = check_worktree(repo)
    if paths:
        git(repo, "add", "-A", "--", *paths)
        git(
            repo,
            "commit",
            "--no-gpg-sign",
            "-m",
            "chore: sync generated plugin mirrors",
        )
        print("Committed generated plugin mirrors.")
    else:
        print("Generated plugins have no changes to commit.")
    if push:
        git(repo, "push", "origin", "HEAD:refs/heads/main")
