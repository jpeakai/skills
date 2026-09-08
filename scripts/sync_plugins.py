#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "ruamel.yaml>=0.18",
# ]
# ///
"""Mirror the canonical skills and hooks into each plugin tree.

``skills/`` and ``hooks/`` at the repo root are the source of truth. Each pack
under ``plugins/`` gets a *copy* of what ``plugins/composition.yaml`` says it
composes.

Why a copy and not a symlink
----------------------------
A symlink was the obvious way to compose these packs, and it is what Claude
Code wants: it follows links at load time and reports every skill correctly.
Codex does not. ``codex plugin add`` copies the plugin directory into
``$CODEX_HOME/plugins/cache/<marketplace>/<plugin>/<version>`` and skips
symlink entries — its path handling refuses components that contain a symlink.
The observable result is the worst kind: the plugin installs, reports
"installed, enabled", and carries an **empty** ``skills/`` directory, so the
model never sees a single skill and nothing errors.

So the mirror is real files. Git stores content addressed by hash, so the
duplicated files collapse to the same objects and the repository barely grows;
the cost is working-tree disk, not history.

Nothing under ``plugins/*/skills/`` or ``plugins/*/hooks/`` is hand-editable.
Edit the canonical copy under ``skills/`` or ``hooks/`` and re-run this script;
``scripts/validate_plugins.py`` fails the build if the two ever disagree.

    uv run scripts/sync_plugins.py           # write the mirror
    uv run scripts/sync_plugins.py --check   # report drift, change nothing

Dependencies are declared in the PEP-723 header above, so ``uv run`` resolves
them per invocation and there is no environment to prepare. ``ruamel.yaml``
reads the composition file: the grouping is documented in comments that sit
next to the entries they explain, which the previous JSON could not carry.

Exit codes: 0 in sync (or written), 1 drift found under ``--check``.
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

from ruamel.yaml import YAML

REPO = Path(__file__).resolve().parent.parent
COMPOSITION = REPO / "plugins" / "composition.yaml"

# Copied per plugin so Codex sees a self-contained tree. hooks.json must also
# be a regular file for `claude plugin validate --strict`, which reads hook
# config without following symlinks.
HOOK_FILES = ["hooks.json", "tool_coach.py", "tool_coach_rules.json", "README.md"]

# Build artefacts that appear inside a canonical skill tree but must never be
# mirrored into a pack. Several skills ship their own script directories with a
# package.json or a PEP-723 environment, so running their gates materialises
# node_modules and friends next to the source. Copying those would bloat the
# published plugin and make the mirror non-idempotent: the tree would differ
# again the moment anyone ran a gate.
IGNORED = {"node_modules", "__pycache__", ".venv", ".mmdc_cache", ".pytest_cache", ".ruff_cache"}


def is_ignored(rel: Path) -> bool:
    """True when any path component is a build artefact rather than source."""
    return any(part in IGNORED for part in rel.parts)


def load_composition() -> dict[str, dict]:
    """Read plugins/composition.yaml.

    Uses the round-trip loader so a future writer keeps the comments, which are
    the reason the file is YAML rather than JSON.
    """
    yaml = YAML(typ="rt")
    return yaml.load(COMPOSITION.read_text(encoding="utf-8"))["plugins"]


def tree_differs(src: Path, dst: Path) -> list[str]:
    """Return a list of human-readable differences between two directories."""
    if dst.is_symlink():
        # Comparing through a link would report a perfect match while leaving
        # the very thing Codex refuses to copy, so the link itself is drift.
        return [f"{dst.relative_to(REPO)} is a symlink; Codex will not copy it"]
    if not dst.exists():
        return [f"{dst.relative_to(REPO)} missing"]
    diffs: list[str] = []
    src_files = {r for p in src.rglob("*") if p.is_file() and not is_ignored(r := p.relative_to(src))}
    dst_files = {r for p in dst.rglob("*") if p.is_file() and not is_ignored(r := p.relative_to(dst))}
    for missing in sorted(src_files - dst_files):
        diffs.append(f"{(dst / missing).relative_to(REPO)} missing")
    for stale in sorted(dst_files - src_files):
        diffs.append(f"{(dst / stale).relative_to(REPO)} is stale")
    for common in sorted(src_files & dst_files):
        if not filecmp.cmp(src / common, dst / common, shallow=False):
            diffs.append(f"{(dst / common).relative_to(REPO)} differs from canonical")
    return diffs


def mirror_dir(src: Path, dst: Path) -> None:
    """Replace dst with an exact copy of src.

    The destination is generated output, so it is rebuilt wholesale rather than
    patched — that is the only way a rename or removal upstream cannot leave a
    stale file behind in a published plugin.
    """
    if dst.is_symlink():
        dst.unlink()
    elif dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, symlinks=False, ignore=shutil.ignore_patterns(*IGNORED))


def sync(check_only: bool) -> int:
    composition = load_composition()
    drift: list[str] = []
    actions: list[str] = []

    for plugin, spec in sorted(composition.items()):
        plugin_dir = REPO / "plugins" / plugin
        if not plugin_dir.is_dir():
            drift.append(f"plugins/{plugin} does not exist")
            continue

        # --- skills -------------------------------------------------------
        skills_dir = plugin_dir / "skills"
        wanted = set(spec["skills"])
        for name in sorted(wanted):
            src, dst = REPO / "skills" / name, skills_dir / name
            if not src.is_dir():
                drift.append(f"skills/{name} named in composition.yaml but missing")
                continue
            diffs = tree_differs(src, dst)
            if diffs:
                drift.extend(diffs)
                if not check_only:
                    mirror_dir(src, dst)
                    actions.append(f"mirrored skills/{name} -> plugins/{plugin}/skills/{name}")

        # Anything in the plugin's skills/ that composition.yaml does not name
        # is stale output from an earlier grouping.
        if skills_dir.is_dir():
            for present in sorted(p for p in skills_dir.iterdir() if not p.name.startswith(".")):
                if present.name not in wanted:
                    drift.append(f"plugins/{plugin}/skills/{present.name} is not in composition.yaml")
                    if not check_only:
                        if present.is_symlink():
                            present.unlink()
                        else:
                            shutil.rmtree(present)
                        actions.append(f"removed stale plugins/{plugin}/skills/{present.name}")

        # --- hooks --------------------------------------------------------
        if spec.get("hooks"):
            hooks_dir = plugin_dir / "hooks"
            if not check_only:
                hooks_dir.mkdir(parents=True, exist_ok=True)
            for name in HOOK_FILES:
                src, dst = REPO / "hooks" / name, hooks_dir / name
                if not src.is_file():
                    drift.append(f"hooks/{name} missing from the canonical tree")
                    continue
                same = dst.is_file() and not dst.is_symlink() and filecmp.cmp(src, dst, shallow=False)
                if not same:
                    drift.append(f"plugins/{plugin}/hooks/{name} differs from canonical")
                    if not check_only:
                        if dst.is_symlink():
                            dst.unlink()
                        shutil.copy2(src, dst)
                        actions.append(f"mirrored hooks/{name} -> plugins/{plugin}/hooks/{name}")
            # Test files stay out of the published packs: they are part of the
            # canonical hooks/ suite, not of what a consumer installs.
            for present in sorted(p for p in hooks_dir.iterdir() if p.name not in HOOK_FILES):
                drift.append(f"plugins/{plugin}/hooks/{present.name} is not a published hook file")
                if not check_only:
                    if present.is_symlink():
                        present.unlink()
                    elif present.is_dir():
                        shutil.rmtree(present)
                    else:
                        present.unlink()
                    actions.append(f"removed plugins/{plugin}/hooks/{present.name}")

    if check_only:
        if drift:
            print(f"Plugin mirror is out of date ({len(drift)} differences):")
            for d in drift:
                print(f"  - {d}")
            print("\nRun: uv run scripts/sync_plugins.py")
            return 1
        print("Plugin mirror is in sync with the canonical trees.")
        return 0

    if actions:
        for a in actions:
            print(f"  {a}")
        print(f"\n{len(actions)} changes written.")
    else:
        print("Already in sync — nothing to do.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report drift and exit non-zero without writing anything (for CI)",
    )
    args = parser.parse_args()
    sys.exit(sync(args.check))


if __name__ == "__main__":
    main()
