"""Render a case's artifact with the skill's own renderer, as part of grading.

The gates prove a diagram is sound on paper. Only a render proves Mermaid accepts it and
Chromium draws it, so every case renders the agent's final file in both standard variants
(``dark_transparent_png`` and ``default_white_png``) and asserts each is a verified PNG.

The render runs in a grader-owned cache directory *beside* the workspace, never inside it:
the workspace is the agent's, and ``check_no_files_added`` judges what the agent left
there. The npm runtime ``mmdc`` needs is shared across cells so it downloads once.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from pytest_xharness_eval import CaseOutput

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
RENDERER = SCRIPTS / "render_mermaid.sh"
VARIANTS = ("dark_transparent_png", "default_white_png")

#: What the skill's renderer writes into the directory it runs in. An agent that follows
#: the skill and renders its work leaves these behind, and that is the mandated behaviour,
#: not an unwanted addition. Anything else the agent adds is still flagged.
RENDER_SCRATCH = (".mmdc_cache/*", "tmp/.mmdc_cache/*")


def render_both_variants(output: CaseOutput, target: str) -> list[Path]:
    """Render ``target`` in both variants into a cache dir beside the workspace; return the PNGs.

    Raises:
        AssertionError: Mermaid rejected the diagram. That is the agent's output being
            wrong, so the cell grades ``fail``.
        RuntimeError: the renderer could not run (no browser, no network, a sandbox
            denial). That is the host, not the skill, so the cell grades ``error``.
    """
    workspace = output.path(target).parent
    render_dir = workspace.parent / f"{workspace.name}.render"
    shutil.rmtree(render_dir, ignore_errors=True)
    render_dir.mkdir(parents=True)
    name = Path(target).name
    shutil.copyfile(output.path(target), render_dir / name)

    result = subprocess.run(
        ["bash", str(RENDERER), name],
        cwd=render_dir,
        env={**os.environ, "MERMAID_RUNTIME_DIR": str(workspace.parent / ".mmdc_runtime")},
        capture_output=True,
        text=True,
        check=False,
    )
    log = f"{result.stdout}{result.stderr}"
    if result.returncode != 0:
        if "DIAGRAM_SYNTAX" in log:
            raise AssertionError(f"Mermaid rejected {target} when rendering it:\n{log}")
        raise RuntimeError(f"render_mermaid.sh could not render {target} on this host:\n{log}")

    stem = Path(name).stem
    pngs = [png for variant in VARIANTS for png in sorted((render_dir / ".mmdc_cache" / variant).glob(f"{stem}-*.png"))]
    missing = [v for v in VARIANTS if not any(v in str(p) for p in pngs)]
    assert not missing, f"render_mermaid.sh exited 0 but wrote no PNG for {missing}:\n{log}"
    return pngs
