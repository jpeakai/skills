#!/usr/bin/env python3
"""Structural gate for the multi-plugin layout.

The repo keeps one canonical copy of every skill (``skills/``) and of the hook
implementation (``hooks/``), and composes them into plugins under ``plugins/``
by symlink. That buys single-sourcing but moves a whole class of breakage off
the type system and into the filesystem: a dangling link, a plugin whose
manifests disagree about its own name, a marketplace pointing at a directory
that was renamed, a per-plugin ``hooks.json`` that drifted from the canonical
wiring.

This script asserts the invariants that hold the layout together. It is
deliberately dependency-free (stdlib only) so it runs in any environment that
has ``python3``, with no virtualenv to resolve.

Run it with no arguments from anywhere:

    uv run scripts/validate_plugins.py

Exit codes: 0 all invariants hold, 1 at least one failed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

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


def frontmatter_name(skill_md: Path) -> str | None:
    """Return the ``name:`` field from a SKILL.md YAML frontmatter block.

    Parsed by hand rather than with PyYAML to keep this script stdlib-only;
    the frontmatter shape here is fixed and simple enough to justify it.
    """
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    _, _, rest = text.partition("---")
    block, _, _ = rest.partition("\n---")
    for line in block.splitlines():
        key, sep, value = line.partition(":")
        if sep and key.strip() == "name":
            return value.strip().strip("\"'")
    return None


def check_symlinks(rep: Report) -> None:
    print("\nSymlinks resolve")
    links = sorted(p for p in (REPO / "plugins").rglob("*") if p.is_symlink())
    rep.check(bool(links), "plugins/ contains symlinks", "found none — is the layout built?")
    for link in links:
        rel = link.relative_to(REPO)
        target = os.readlink(link)
        rep.check(link.exists(), f"{rel} -> {target}", "dangling")
        # A link that escapes the repo would break any consumer that clones it.
        resolved = link.resolve()
        rep.check(
            REPO in resolved.parents or resolved == REPO,
            f"{rel} stays inside the repo",
            f"resolves to {resolved}",
        )


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
    check_symlinks(rep)
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
