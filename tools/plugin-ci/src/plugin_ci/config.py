"""Locate the repository independently of the installed Tool."""

import os
from pathlib import Path


def resolve_root(override: str | None = None) -> Path:
    """Resolve an explicit root, environment override, or enclosing repository."""
    candidate = override or os.environ.get("PLUGIN_CI_PROJECT_DIR")
    here = Path(candidate).expanduser().resolve() if candidate else Path.cwd().resolve()
    candidates = (here,) if candidate else (here, *here.parents)
    for root in candidates:
        if (root / "plugins").is_dir():
            return root
    raise RuntimeError(f"No plugins/ directory in project root or ancestors of {here}")
