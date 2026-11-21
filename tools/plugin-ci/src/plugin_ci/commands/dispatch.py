"""Execute resolved plugin operations."""

import argparse
from pathlib import Path

from . import plugin_mirrors, sync_plugins, tag_plugins, validate_plugins


def dispatch(args: argparse.Namespace, root: Path) -> int:
    if args.command == "sync":
        return sync_plugins.sync(args.check, root)
    if args.command == "validate":
        return validate_plugins.validate(root)
    if args.command == "tag":
        return tag_plugins.tag(root, args.push, args.dry_run, args.remote)
    if args.command == "commit":
        plugin_mirrors.commit_mirrors(root, args.push)
    else:
        plugin_mirrors.check_worktree(root)
    return 0
