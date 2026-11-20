"""Argument parsing and command dispatch."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from harness_ci.commands.run import run
from harness_ci.config import project_root


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch the explicitly requested installation check."""
    parser = argparse.ArgumentParser(description=__doc__)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--project-dir", type=Path, default=argparse.SUPPRESS)
    parser.add_argument("--project-dir", type=Path, default=None)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("run", parents=[common], help="Run live isolated harness installs")
    check.add_argument("sandbox", nargs="?", type=Path, help="Retained sandbox directory")
    arguments = parser.parse_args(argv)
    try:
        root = project_root(arguments.project_dir, Path.cwd())
    except ValueError as error:
        parser.error(str(error))
    return run(root, arguments.sandbox)
