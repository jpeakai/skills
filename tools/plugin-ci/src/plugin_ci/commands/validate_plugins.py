from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any, cast

from ruamel.yaml import YAML

from .sync_plugins import sync

# What a *marketplace* enforces on publication — description caps, unique skill
# names, no second SKILL.md inside a vendored copy — is asserted in
# tools/plugin-ci/tests/test_publication_contract.py, not here, and the caps are declared there
# once. This script owns the other half: the internal layout that holds the
# generated mirror together. A rule belongs there if a marketplace judges it,
# and here if this repo invented it.

# hooks.json must be a REGULAR FILE inside each plugin, not a symlink:
# `claude plugin validate --strict` reads hook config without following
# symlinks and fails the plugin if it cannot read it.
# Hook implementation files are mirrored alongside the regular wiring file.
WIRING_FILE = "hooks.json"


class Report:
    """Collects pass/fail lines so one run reports every problem, not just the first."""

    def __init__(self) -> None:
        self.failures: list[str] = []
        self.checks = 0

    def check(self, ok: bool, label: str, detail: Any = "") -> bool:
        self.checks += 1
        if ok:
            print(f"  ok   {label}")
        else:
            suffix = f" — {detail}" if detail else ""
            print(f"  FAIL {label}{suffix}")
            self.failures.append(f"{label}{suffix}")
        return ok


def load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def load_yaml(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], YAML(typ="safe").load(path.read_text(encoding="utf-8")))


def frontmatter(skill_md: Path) -> dict[str, Any]:
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
    return cast(str | None, frontmatter(skill_md).get("name"))


def check_no_symlinks(rep: Report, repo: Path) -> None:
    """No entry under plugins/ may be a symlink.

    Codex copies a plugin into its cache and skips symlink entries, so a
    symlinked skill installs as an empty directory with no error anywhere. The
    plugin reports "installed, enabled" and carries nothing. Claude Code does
    follow links, which is exactly why this has to be asserted rather than
    noticed: the layout looks healthy in one harness while being inert in the
    other.
    """
    print("\nNo symlinks under plugins/ (Codex silently drops them)")
    links = sorted(p for p in (repo / "plugins").rglob("*") if p.is_symlink())
    rep.check(
        not links,
        "plugins/ is free of symlinks",
        ", ".join(str(p.relative_to(repo)) for p in links[:5]),
    )


def check_mirror_in_sync(rep: Report, repo: Path) -> None:
    """Delegate the content comparison to the sync script's own --check mode."""
    print("\nMirror matches the canonical skills/ and hooks/ trees")
    output = io.StringIO()
    with redirect_stdout(output):
        result = sync(True, repo)
    rep.check(result == 0, "plugins/ mirror is in sync", "run: plugin-ci sync")
    if result:
        for line in output.getvalue().splitlines()[1:6]:
            print(f"       {line.strip()}")


def check_composition(rep: Report, repo: Path) -> None:
    """plugins/composition.yaml is the declaration; the tree must match it."""
    print("\nEach plugin tree matches plugins/composition.yaml")
    composition = load_yaml(repo / "plugins" / "composition.yaml")["plugins"]
    dirs = {p.name for p in (repo / "plugins").iterdir() if p.is_dir()}
    rep.check(
        set(composition) == dirs,
        "composition.yaml covers every plugin dir",
        f"{set(composition)} vs {dirs}",
    )
    for plugin, spec in sorted(composition.items()):
        declared = set(spec["skills"])
        present = {
            p.name
            for p in (repo / "plugins" / plugin / "skills").iterdir()
            if not p.name.startswith(".")
        }
        rep.check(
            declared == present,
            f"{plugin}: composed skills match declaration",
            f"{declared} vs {present}",
        )
        for name in sorted(declared):
            rep.check(
                (repo / "skills" / name).is_dir(), f"{plugin}: canonical skills/{name} exists"
            )


def check_hook_wiring(rep: Report, repo: Path) -> None:
    print("\nHook wiring is a regular file and matches the canonical copy")
    canonical = (repo / "hooks" / WIRING_FILE).read_bytes()
    composition = load_yaml(repo / "plugins" / "composition.yaml")["plugins"]
    for plugin in sorted((repo / "plugins").iterdir()):
        if not plugin.is_dir():
            continue
        wiring = plugin / "hooks" / WIRING_FILE
        rel = wiring.relative_to(repo)
        if not composition.get(plugin.name, {}).get("hooks"):
            rep.check(
                not (plugin / "hooks").exists(),
                f"{plugin.name}: no hooks/ (composition.yaml declares none)",
                "the tree still carries a hook the declaration dropped",
            )
            continue
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


AGENT_PLUGINS_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"


def check_manifests(rep: Report, repo: Path) -> None:
    print("\nEach plugin's three manifests agree with its directory name")
    composition = load_yaml(repo / "plugins" / "composition.yaml")["plugins"]
    for plugin in sorted((repo / "plugins").iterdir()):
        if not plugin.is_dir():
            continue
        claude = plugin / ".claude-plugin" / "plugin.json"
        codex = plugin / ".codex-plugin" / "plugin.json"
        if not rep.check(claude.exists(), f"{claude.relative_to(repo)} exists"):
            continue
        if not rep.check(codex.exists(), f"{codex.relative_to(repo)} exists"):
            continue
        cj, xj = load_json(claude), load_json(codex)
        rep.check(
            cj.get("name") == plugin.name,
            f"{plugin.name}: Claude manifest name matches dir",
            cj.get("name"),
        )
        rep.check(
            xj.get("name") == plugin.name,
            f"{plugin.name}: Codex manifest name matches dir",
            xj.get("name"),
        )
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

        # Kiro installs a pack as a power only when an Agent Plugins manifest
        # sits at the pack root; without it `kiro-cli powers install` refuses
        # the directory. Kiro also requires keywords, which the spec leaves optional.
        kiro = plugin / "plugin.json"
        if rep.check(kiro.exists(), f"{kiro.relative_to(repo)} exists"):
            kj = load_json(kiro)
            rep.check(
                kj.get("$schema") == AGENT_PLUGINS_SCHEMA,
                f"{plugin.name}: Kiro manifest $schema",
                kj.get("$schema"),
            )
            rep.check(
                kj.get("name") == plugin.name,
                f"{plugin.name}: Kiro manifest name matches dir",
                kj.get("name"),
            )
            rep.check(
                kj.get("version") == cj.get("version"),
                f"{plugin.name}: Kiro version agrees",
                f"claude={cj.get('version')} kiro={kj.get('version')}",
            )
            rep.check(
                bool(kj.get("keywords")),
                f"{plugin.name}: Kiro manifest has keywords",
                kj.get("keywords"),
            )

        # Codex needs explicit paths; Claude auto-discovers, so only Codex is asserted here.
        rep.check(
            xj.get("skills") == "./skills", f"{plugin.name}: Codex skills path", xj.get("skills")
        )
        if composition.get(plugin.name, {}).get("hooks"):
            rep.check(
                xj.get("hooks") == f"./hooks/{WIRING_FILE}",
                f"{plugin.name}: Codex hooks path",
                xj.get("hooks"),
            )
        else:
            # Codex resolves the declared path at install time; a path with no
            # file behind it is a load error, not a silently ignored key.
            rep.check(
                "hooks" not in xj,
                f"{plugin.name}: Codex manifest declares no hooks path",
                xj.get("hooks"),
            )


def check_skills(rep: Report, repo: Path) -> None:
    print("\nEvery composed skill resolves to a real SKILL.md whose name matches")
    for plugin in sorted((repo / "plugins").iterdir()):
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
            rep.check(
                name == entry.name, f"{rel}: frontmatter name matches directory", f"got {name!r}"
            )


def check_marketplaces(rep: Report, repo: Path) -> None:
    print("\nBoth marketplaces list the same plugins, and each source path exists")
    on_disk = {p.name for p in (repo / "plugins").iterdir() if p.is_dir()}

    claude_mp = load_json(repo / ".claude-plugin" / "marketplace.json")
    claude_names = set()
    for entry in claude_mp.get("plugins", []):
        claude_names.add(entry["name"])
        src = (repo / entry["source"]).resolve()
        rep.check(src.is_dir(), f"Claude marketplace source for {entry['name']}", entry["source"])

    codex_mp = load_json(repo / ".agents" / "plugins" / "marketplace.json")
    codex_names = set()
    for entry in codex_mp.get("plugins", []):
        codex_names.add(entry["name"])
        src = (repo / entry["source"]["path"]).resolve()
        rep.check(
            src.is_dir(), f"Codex marketplace source for {entry['name']}", entry["source"]["path"]
        )
        # Codex 0.153.x rejects the whole marketplace file on an unknown
        # `authentication` variant, so assert only the accepted keys are used.
        policy = entry.get("policy", {})
        rep.check(
            set(policy) <= {"installation"},
            f"Codex marketplace policy keys for {entry['name']}",
            f"unexpected {sorted(set(policy) - {'installation'})}",
        )

    rep.check(
        claude_names == on_disk,
        "Claude marketplace covers every plugin dir",
        f"{claude_names} vs {on_disk}",
    )
    rep.check(
        codex_names == on_disk,
        "Codex marketplace covers every plugin dir",
        f"{codex_names} vs {on_disk}",
    )


def validate(repo: Path) -> int:

    print(f"Validating plugin layout in {repo}")
    rep = Report()
    check_no_symlinks(rep, repo)
    check_mirror_in_sync(rep, repo)
    check_composition(rep, repo)
    check_hook_wiring(rep, repo)
    check_manifests(rep, repo)
    check_skills(rep, repo)
    check_marketplaces(rep, repo)

    print(f"\n{rep.checks} checks run.")
    if rep.failures:
        print(f"{len(rep.failures)} FAILED:")
        for f in rep.failures:
            print(f"  - {f}")
        return 1
    print("All invariants hold.")
    return 0
