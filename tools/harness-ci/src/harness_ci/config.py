"""Resolve repository paths without depending on the executable location."""

import os
from pathlib import Path


def project_root(explicit: Path | None, cwd: Path) -> Path:
    """Resolve an explicit repository or search the working directory's ancestors."""
    selected = explicit or os.environ.get("HARNESS_CI_PROJECT_DIR")
    if selected is not None:
        root = Path(selected).expanduser().resolve()
        if not (root / "plugins/composition.yaml").is_file():
            raise ValueError(f"No plugins/composition.yaml in project directory: {root}")
        return root
    for candidate in (cwd, *cwd.parents):
        if (candidate / "plugins/composition.yaml").is_file():
            return candidate.resolve()
    raise ValueError("Cannot find project root; supply --project-dir")
