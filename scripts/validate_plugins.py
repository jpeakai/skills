#!/usr/bin/env -S uv run
"""Structural gate for the multi-plugin layout.

The repo keeps one canonical copy of every skill (``skills/``) and of the hook
implementation (``hooks/``), and composes them into plugins under ``plugins/``
by symlink. That buys single-sourcing but moves a whole class of breakage off
the type system and into the filesystem: a dangling link, a plugin whose
manifests disagree about its own name, a marketplace pointing at a directory
that was renamed, a per-plugin ``hooks.json`` that drifted from the canonical
wiring.

This script asserts the invariants that hold the layout together.

Run it with no arguments from anywhere:

    uv run scripts/validate_plugins.py

Dependencies are the project's ``dev`` group in ``pyproject.toml``, so ``uv
run`` syncs them and there is no environment to prepare.

Exit codes: 0 all invariants hold, 1 at least one failed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from ruamel.yaml import YAML

REPO = Path(__file__).resolve().parent.parent

# What a *marketplace* enforces on publication — description caps, unique skill
# names, no second SKILL.md inside a vendored copy — is asserted in
# tests/test_publication_contract.py, not here, and the caps are declared there
# once. This script owns the other half: the internal layout that holds the
# generated mirror together. A rule belongs there if a marketplace judges it,
# and here if this repo invented it.

# hooks.json must be a REGULAR FILE inside each plugin, not a symlink:
# `claude plugin validate --strict` reads hook config without following
# symlinks and fails the plugin if it cannot read it. The scripts it points at
# are symlinked, so only this one small wiring file is duplicated.
WIRING_FILE = "hooks.json"


class Report:
    """Collects pass/fail lines so one run reports every problem, not just the first."""

    def __init__(self) -> None:
        self.failures: list[str] = []
        self.checks = 0

    def check(self, ok: bool, label: str, detail: str = "") -> bool:
        self.checks += 1
        if ok:
            print(f"  ok   {label}")
        else:
            suffix = f" — {detail}" if detail else ""
            print(f"  FAIL {label}{suffix}")
            self.failures.append(f"{label}{suffix}")
        return ok


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict:
    return YAML(typ="safe").load(path.read_text(encoding="utf-8"))


def frontmatter(skill_md: Path) -> dict:
    """Return a SKILL.md's YAML frontmatter block as a dict.

    The block is real YAML, so it is parsed as YAML rather than scanned line by
    line. Several descriptions here are quoted strings running to many hundreds
    of characters and containing colons, which a naive split on ``:`` mis-reads.
    """
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    _, _, rest = text.partition("---")
    block, _, _ = rest.partition("\n---")
    front = YAML(typ="safe").load(block)
    return front if isinstance(front, dict) else {}


def frontmatter_name(skill_md: Path) -> str | None:
    return frontmatter(skill_md).get("name")


def check_no_symlinks(rep: Report) -> None:
    """No entry under plugins/ may be a symlink.

    Codex copies a plugin into its cache and skips symlink entries, so a
    symlinked skill installs as an empty directory with no error anywhere. The
    plugin reports "installed, enabled" and carries nothing. Claude Code does
    follow links, which is exactly why this has to be asserted rather than
    noticed: the layout looks healthy in one harness while being inert in the
    other.
    """
    print("\nNo symlinks under plugins/ (Codex silently drops them)")
    links = sorted(p for p in (REPO / "plugins").rglob("*") if p.is_symlink())
    rep.check(
        not links,
        "plugins/ is free of symlinks",
        ", ".join(str(p.relative_to(REPO)) for p in links[:5]),
    )


def check_mirror_in_sync(rep: Report) -> None:
    """Delegate the content comparison to the sync script's own --check mode."""
    print("\nMirror matches the canonical skills/ and hooks/ trees")
    # Invoked through `uv run` rather than this interpreter, so the sibling
    # script gets the project environment whatever this one was started with.
    result = subprocess.run(
        ["uv", "run", str(REPO / "scripts" / "sync_plugins.py"), "--check"],
        capture_output=True,
        text=True,
    )
    rep.check(
        result.returncode == 0,
        "plugins/ mirror is in sync",
        "run: uv run scripts/sync_plugins.py",
    )
    if result.returncode != 0:
        for line in result.stdout.splitlines()[1:6]:
            print(f"       {line.strip()}")


def check_composition(rep: Report) -> None:
    """plugins/composition.yaml is the declaration; the tree must match it."""
    print("\nEach plugin tree matches plugins/composition.yaml")
    composition = load_yaml(REPO / "plugins" / "composition.yaml")["plugins"]
    dirs = {p.name for p in (REPO / "plugins").iterdir() if p.is_dir()}
    rep.check(set(composition) == dirs, "composition.yaml covers every plugin dir", f"{set(composition)} vs {dirs}")
    for plugin, spec in sorted(composition.items()):
        declared = set(spec["skills"])
        present = {p.name for p in (REPO / "plugins" / plugin / "skills").iterdir() if not p.name.startswith(".")}
        rep.check(declared == present, f"{plugin}: composed skills match declaration", f"{declared} vs {present}")
        for name in sorted(declared):
            rep.check((REPO / "skills" / name).is_dir(), f"{plugin}: canonical skills/{name} exists")


def check_hook_wiring(rep: Report) -> None:
    print("\nHook wiring is a regular file and matches the canonical copy")
    canonical = (REPO / "hooks" / WIRING_FILE).read_bytes()
    for plugin in sorted((REPO / "plugins").iterdir()):
        if not plugin.is_dir():
            continue
        wiring = plugin / "hooks" / WIRING_FILE
        rel = wiring.relative_to(REPO)
        if not rep.check(wiring.exists(), f"{rel} exists"):
            continue
        rep.check(
            not wiring.is_symlink(),
            f"{rel} is a regular file",
            "it is a symlink; --strict cannot read it",
        )
        rep.check(
            wiring.read_bytes() == canonical,
            f"{rel} is byte-identical to hooks/{WIRING_FILE}",
            "drifted from the canonical wiring",
        )


def check_manifests(rep: Report) -> None:
    print("\nEach plugin's two manifests agree with its directory name")
    for plugin in sorted((REPO / "plugins").iterdir()):
        if not plugin.is_dir():
            continue
        claude = plugin / ".claude-plugin" / "plugin.json"
        codex = plugin / ".codex-plugin" / "plugin.json"
        if not rep.check(claude.exists(), f"{claude.relative_to(REPO)} exists"):
            continue
        if not rep.check(codex.exists(), f"{codex.relative_to(REPO)} exists"):
            continue
        cj, xj = load_json(claude), load_json(codex)
        rep.check(cj.get("name") == plugin.name, f"{plugin.name}: Claude manifest name matches dir", cj.get("name"))
        rep.check(xj.get("name") == plugin.name, f"{plugin.name}: Codex manifest name matches dir", xj.get("name"))
        rep.check(
            cj.get("version") == xj.get("version"),
            f"{plugin.name}: versions agree",
            f"claude={cj.get('version')} codex={xj.get('version')}",
        )
        # A manifest describing itself as symlink-composed is published metadata
        # contradicting the layout. It survived the switch to copies unnoticed
        # because nothing read it, so it is asserted here rather than reviewed.
        for label, path in (("Claude", claude), ("Codex", codex)):
            rep.check(
                "symlink" not in path.read_text(encoding="utf-8").lower(),
                f"{plugin.name}: {label} manifest makes no symlink claim",
                "the packs hold mirrored copies, not symlinks",
            )

        # Codex needs explicit paths; Claude auto-discovers, so only Codex is asserted here.
        rep.check(xj.get("skills") == "./skills", f"{plugin.name}: Codex skills path", xj.get("skills"))
        rep.check(
            xj.get("hooks") == f"./hooks/{WIRING_FILE}",
            f"{plugin.name}: Codex hooks path",
            xj.get("hooks"),
        )


def check_skills(rep: Report) -> None:
    print("\nEvery composed skill resolves to a real SKILL.md whose name matches")
    for plugin in sorted((REPO / "plugins").iterdir()):
        if not plugin.is_dir():
            continue
        skills = plugin / "skills"
        entries = sorted(p for p in skills.iterdir() if not p.name.startswith("."))
        rep.check(bool(entries), f"{plugin.name} composes at least one skill")
        for entry in entries:
            skill_md = entry / "SKILL.md"
            rel = f"{plugin.name}/{entry.name}"
            if not rep.check(skill_md.exists(), f"{rel}/SKILL.md exists"):
                continue
            name = frontmatter_name(skill_md)
            rep.check(name == entry.name, f"{rel}: frontmatter name matches directory", f"got {name!r}")


def check_marketplaces(rep: Report) -> None:
    print("\nBoth marketplaces list the same plugins, and each source path exists")
    on_disk = {p.name for p in (REPO / "plugins").iterdir() if p.is_dir()}

    claude_mp = load_json(REPO / ".claude-plugin" / "marketplace.json")
    claude_names = set()
    for entry in claude_mp.get("plugins", []):
        claude_names.add(entry["name"])
        src = (REPO / entry["source"]).resolve()
        rep.check(src.is_dir(), f"Claude marketplace source for {entry['name']}", entry["source"])

    codex_mp = load_json(REPO / ".agents" / "plugins" / "marketplace.json")
    codex_names = set()
    for entry in codex_mp.get("plugins", []):
        codex_names.add(entry["name"])
        src = (REPO / entry["source"]["path"]).resolve()
        rep.check(src.is_dir(), f"Codex marketplace source for {entry['name']}", entry["source"]["path"])
        # Codex 0.153.x rejects the whole marketplace file on an unknown
        # `authentication` variant, so assert only the accepted keys are used.
        policy = entry.get("policy", {})
        rep.check(
            set(policy) <= {"installation"},
            f"Codex marketplace policy keys for {entry['name']}",
            f"unexpected {sorted(set(policy) - {'installation'})}",
        )

    rep.check(claude_names == on_disk, "Claude marketplace covers every plugin dir", f"{claude_names} vs {on_disk}")
    rep.check(codex_names == on_disk, "Codex marketplace covers every plugin dir", f"{codex_names} vs {on_disk}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.parse_args()

    print(f"Validating plugin layout in {REPO}")
    rep = Report()
    check_no_symlinks(rep)
    check_mirror_in_sync(rep)
    check_composition(rep)
    check_hook_wiring(rep)
    check_manifests(rep)
    check_skills(rep)
    check_marketplaces(rep)

    print(f"\n{rep.checks} checks run.")
    if rep.failures:
        print(f"{len(rep.failures)} FAILED:")
        for f in rep.failures:
            print(f"  - {f}")
        sys.exit(1)
    print("All invariants hold.")


if __name__ == "__main__":
    main()
