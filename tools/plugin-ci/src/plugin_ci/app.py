"""Argument wiring for the plugin publication Tool."""

import argparse
import sys
from contextlib import redirect_stdout

from .commands.dispatch import dispatch
from .config import resolve_root


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--project-dir", default=argparse.SUPPRESS)
    parser = argparse.ArgumentParser(prog="plugin-ci", parents=[common])
    commands = parser.add_subparsers(dest="command")
    sync = commands.add_parser("sync", parents=[common], help="regenerate plugin mirrors")
    sync.add_argument("--check", action="store_true")
    commands.add_parser("validate", parents=[common], help="validate plugin contracts")
    commands.add_parser("check-worktree", parents=[common], help="require clean authored files")
    commit = commands.add_parser(
        "commit", parents=[common], help="commit generated mirrors on main"
    )
    commit.add_argument("--push", action="store_true")
    tag = commands.add_parser("tag", parents=[common], help="create missing immutable version tags")
    tag.add_argument("--push", action="store_true")
    tag.add_argument("--dry-run", action="store_true")
    tag.add_argument("--remote", default="origin")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    try:
        root = resolve_root(getattr(args, "project_dir", None))
        with redirect_stdout(sys.stderr):
            return dispatch(args, root)
    except (RuntimeError, OSError, ValueError, KeyError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
