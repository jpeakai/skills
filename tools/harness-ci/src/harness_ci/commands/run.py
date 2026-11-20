"""Run the isolated installation contract in its packaged shell asset."""

import os
import subprocess
import sys
from datetime import UTC, datetime
from importlib.resources import as_file, files
from pathlib import Path
from typing import TextIO


def execute(command: list[str], root: Path, output: TextIO) -> int:
    """Run a real subprocess with the selected root and diagnostic output stream."""
    environment = dict(os.environ, HARNESS_CI_PROJECT_DIR=str(root))
    return subprocess.run(
        command, env=environment, stdout=output, stderr=output, check=False
    ).returncode


def run(root: Path, sandbox: Path | None, *, asset_path: Path | None = None) -> int:
    """Install both plugins into isolated harness homes and retain their sandbox."""
    destination = sandbox or root / "tmp/harness-ci" / datetime.now(UTC).strftime(
        "%Y%m%d-%H%M%S-%f"
    )
    asset = asset_path or files("harness_ci").joinpath("assets/install.sh")
    with as_file(asset) as script:
        return execute(["bash", str(script), str(destination.resolve())], root, sys.stderr)
