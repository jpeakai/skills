#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest>=8.0", "ruamel.yaml>=0.18"]
# ///
"""What a marketplace enforces when this repo is published, asserted locally.

Every rule here was learned from a real failed or warned sync of
``jpeakai/skills`` into the claude.ai plugin admin, and each one names the
incident it came from. That provenance matters, because none of these rules
are checked by anything else available locally:

* ``claude plugin validate --strict`` passes on a tree that fails the sync.
  Verified against the duplicate-name commit in a throwaway worktree.
* ``make harness-ci`` installs both packs into real Claude and Codex
  sandboxes, discovers every skill, and fires the hook, all while the tree
  was in breach.
* The published ``claude-code-marketplace.json`` schema declares no
  ``maxLength`` on any description field.

So the caps below are **observed**, not documented, and the sync's own
wording is quoted next to each one. If a sync ever reports a limit different
from these, the number here is what is wrong.

``scripts/validate_plugins.py`` is the sibling gate and owns a different
contract: the internal layout that holds the generated mirror together
(symlinks, composition, hook wiring, manifest agreement). A rule belongs
there if this repo invented it, and here if a marketplace will judge it.

Run standalone, or through ``make ci``:

    uv run --no-project tests/test_publication_contract.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest
from ruamel.yaml import YAML

REPO = Path(__file__).resolve().parent.parent

# --- The observed caps -----------------------------------------------------
# "Skill 'skills/gooddocs': field 'description' in SKILL.md must be at most
# 1024 characters" — sync of a9d86dc, 2026-09-09. gooddocs was 1041 and
# librarian 1562; both were dropped from the synced pack.
SKILL_DESCRIPTION_CAP = 1024

# "Plugin description must be at most 500 characters." — same sync.
# jpai-essentials was 595, jpai-delivery 510.
PLUGIN_DESCRIPTION_CAP = 500

# Frontmatter keys this publication path accepts. Deliberately wider than the
# Agent Skills spec, which allows only allowed-tools/compatibility/description/
# license/metadata/name and hard-errors on anything else when a skill is
# zip-uploaded to claude.ai. The plugin-marketplace sync is not that surface:
# it accepted `argument-hint` and `user-invocable` on all eight skills without
# comment. This set is the union of what the sync accepts and what Claude Code
# documents, so the assertion catches the failure that actually bites — a
# misspelled or wrongly-punctuated key (`desciption`, `allowed_tools`), which
# no validator reports because an unknown key is simply ignored.
KNOWN_FRONTMATTER_KEYS = frozenset(
    {
        "agent",
        "allowed-tools",
        "argument-hint",
        "arguments",
        "background",
        "compatibility",
        "context",
        "description",
        "disable-model-invocation",
        "disallowed-tools",
        "disallowed_tools",
        "effort",
        "hooks",
        "license",
        "metadata",
        "model",
        "name",
        "paths",
        "shell",
        "user-invocable",
        "when_to_use",
    }
)

# Every skill name in this repo is a lowercase slug, which is also what a
# harness turns into a `/command` and what the directory is called. A name with
# an uppercase letter, a space, or an underscore installs but cannot be invoked
# as typed.
SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


# --- Discovery -------------------------------------------------------------
def canonical_skills() -> list[Path]:
    """Every canonical skill directory. Parametrising over this is the point:
    a skill added tomorrow is covered without touching this file."""
    return sorted(p for p in (REPO / "skills").iterdir() if (p / "SKILL.md").is_file())


def plugin_manifests() -> list[Path]:
    return sorted((REPO / "plugins").glob("*/.*-plugin/plugin.json"))


def vendored_copies() -> list[Path]:
    """Wholesale copies of other skills, at ``skills/<skill>/vendor/<name>/``."""
    return sorted(p for p in (REPO / "skills").glob("*/vendor/*") if p.is_dir())


SKILLS = canonical_skills()
SKILL_IDS = [p.name for p in SKILLS]
MANIFESTS = plugin_manifests()
MANIFEST_IDS = [str(p.relative_to(REPO / "plugins")) for p in MANIFESTS]
VENDORED = vendored_copies()
VENDORED_IDS = [f"{p.parent.parent.name}/{p.name}" for p in VENDORED]


def frontmatter(skill_md: Path) -> dict:
    """Parse a SKILL.md frontmatter block as YAML.

    Parsed rather than scanned line by line: these descriptions are quoted
    strings hundreds of characters long containing colons, em dashes and
    parenthesised lists, and a naive split on ``:`` mis-reads them.
    """
    text = skill_md.read_text(encoding="utf-8")
    assert text.startswith("---"), f"{skill_md} has no frontmatter block"
    _, _, rest = text.partition("---")
    block, sep, _ = rest.partition("\n---")
    assert sep, f"{skill_md} frontmatter block is unterminated"
    loaded = YAML(typ="safe").load(block)
    assert isinstance(loaded, dict), f"{skill_md} frontmatter is not a mapping"
    return loaded


def test_repo_has_skills() -> None:
    """Guard the parametrisation itself: an empty discovery would make every
    test below pass by vacuum."""
    assert SKILLS, "no skills discovered under skills/ — the suite would be inert"
    assert MANIFESTS, "no plugin manifests discovered under plugins/"


# --- The sync's caps -------------------------------------------------------
@pytest.mark.parametrize("skill", SKILLS, ids=SKILL_IDS)
def test_skill_description_within_cap(skill: Path) -> None:
    """Regression: gooddocs (1041) and librarian (1562) were dropped from the
    synced pack for this.

    A description is the model's trigger surface — it is the only part of a
    skill loaded before invocation. So the fix for a breach is always to cut
    implementation detail the SKILL.md body already carries, never a "use when"
    or "skip when" clause, which would silently narrow what the skill answers
    to with no test able to notice.
    """
    n = len(frontmatter(skill / "SKILL.md")["description"])
    assert n <= SKILL_DESCRIPTION_CAP, (
        f"{skill.name} description is {n} chars, over the cap by {n - SKILL_DESCRIPTION_CAP}. "
        "Cut implementation detail, not a trigger clause."
    )


@pytest.mark.parametrize("manifest", MANIFESTS, ids=MANIFEST_IDS)
def test_plugin_description_within_cap(manifest: Path) -> None:
    """Regression: both packs breached this, and both manifests of each pack
    carry the same description, so all four had to be fixed."""
    n = len(json.loads(manifest.read_text(encoding="utf-8")).get("description", ""))
    assert n <= PLUGIN_DESCRIPTION_CAP, (
        f"{manifest.relative_to(REPO)} description is {n} chars, over the cap by {n - PLUGIN_DESCRIPTION_CAP}"
    )


# --- Duplicate skill names -------------------------------------------------
@pytest.mark.parametrize("skill", SKILLS, ids=SKILL_IDS)
def test_one_skill_md_per_skill(skill: Path) -> None:
    """Regression, and the failure that blocked the sync outright.

    "Duplicate skill name 'mermaidjs-diagrams' found in
    'skills/mermaidjs-diagrams' and 'skills/richdocs/vendor/mermaidjs-diagrams'"

    A harness registers every SKILL.md beneath a plugin as a skill, so a
    wholesale vendored copy that kept upstream's filename declared that skill
    a second time and the whole plugin was rejected.
    """
    nested = sorted(
        p.relative_to(REPO) for p in skill.rglob("SKILL.md") if p.parent != skill and "node_modules" not in p.parts
    )
    assert not nested, "SKILL.md below a skill's root: " + "; ".join(
        f"{p} — rename to {p.parent.name}.md" for p in nested
    )


def test_skill_names_are_unique_across_the_repo() -> None:
    """The rule the sync actually applies, stated directly rather than via its
    symptom. Two skills may not declare the same name, wherever they sit."""
    seen: dict[str, list[str]] = {}
    for skill_md in sorted((REPO / "skills").rglob("SKILL.md")):
        if "node_modules" in skill_md.parts:
            continue
        name = frontmatter(skill_md).get("name") or skill_md.parent.name
        seen.setdefault(name, []).append(str(skill_md.relative_to(REPO)))
    duplicates = {name: paths for name, paths in seen.items() if len(paths) > 1}
    assert not duplicates, f"duplicate skill names: {duplicates}"


# --- Vendored copies ------------------------------------------------------
@pytest.mark.parametrize("copy", VENDORED, ids=VENDORED_IDS)
def test_vendored_copy_has_a_demoted_entrypoint(copy: Path) -> None:
    """The convention that replaced the duplicate SKILL.md, asserted positively.

    Absence of SKILL.md is necessary but not sufficient: a refresh that
    rsynced over the copy and deleted nothing would leave no entrypoint at all,
    and the skill that operates the copy would cite a file that is not there.
    """
    entrypoint = copy / f"{copy.name}.md"
    assert entrypoint.is_file(), (
        f"{copy.relative_to(REPO)} has no {copy.name}.md — a vendored copy's entrypoint is "
        "upstream's SKILL.md renamed, per its vendor/README.md refresh procedure"
    )


@pytest.mark.parametrize("copy", VENDORED, ids=VENDORED_IDS)
def test_vendored_runtime_surfaces_cite_the_renamed_entrypoint(copy: Path) -> None:
    """A run must never be told to open a file the rename removed.

    Only the copy's runtime surfaces are checked — its entrypoint and
    ``resources/**``. Its README, CLAUDE.md and docs/adrs keep upstream's
    wording on purpose: they are addressed to whoever edits the upstream skill,
    where the file really is SKILL.md.
    """
    surfaces = [copy / f"{copy.name}.md", *sorted((copy / "resources").rglob("*.md"))]
    offenders = [
        str(p.relative_to(REPO)) for p in surfaces if p.is_file() and "SKILL.md" in p.read_text(encoding="utf-8")
    ]
    assert not offenders, (
        "vendored runtime surface still cites SKILL.md, which does not exist in the copy: "
        f"{offenders} — repoint to {copy.name}.md"
    )


# --- Frontmatter well-formedness -----------------------------------------
@pytest.mark.parametrize("skill", SKILLS, ids=SKILL_IDS)
def test_frontmatter_name_matches_directory(skill: Path) -> None:
    """The directory name is what a harness installs and what
    plugins/composition.yaml declares, so a mismatch is a skill nobody can
    invoke by the name they were given."""
    name = frontmatter(skill / "SKILL.md").get("name")
    assert name == skill.name, f"frontmatter name {name!r} does not match directory {skill.name!r}"


@pytest.mark.parametrize("skill", SKILLS, ids=SKILL_IDS)
def test_skill_name_is_a_lowercase_slug(skill: Path) -> None:
    assert SKILL_NAME.match(skill.name), (
        f"{skill.name!r} is not a lowercase hyphenated slug; it would install but not be invocable as typed"
    )


@pytest.mark.parametrize("skill", SKILLS, ids=SKILL_IDS)
def test_description_is_present_and_substantial(skill: Path) -> None:
    """An absent or throwaway description is the quietest way to break a skill:
    it installs, it lists, and the model never chooses it."""
    description = frontmatter(skill / "SKILL.md").get("description", "")
    assert description.strip(), f"{skill.name} has no description — the model would never auto-invoke it"
    assert len(description) >= 40, f"{skill.name} description is {len(description)} chars, too thin to route on"


@pytest.mark.parametrize("skill", SKILLS, ids=SKILL_IDS)
def test_frontmatter_keys_are_known(skill: Path) -> None:
    """Catch the typo no validator reports. An unrecognised key is ignored
    rather than rejected on this path, so `desciption:` or `allowed_tools:`
    silently does nothing at all."""
    unknown = sorted(set(frontmatter(skill / "SKILL.md")) - KNOWN_FRONTMATTER_KEYS)
    assert not unknown, (
        f"{skill.name} has unrecognised frontmatter key(s) {unknown}. "
        "Fix the spelling, or add the key to KNOWN_FRONTMATTER_KEYS with the source that documents it."
    )


if __name__ == "__main__":  # pragma: no cover
    sys.exit(pytest.main([__file__, "-v", "--rootdir", str(REPO), "-o", "addopts="] + sys.argv[1:]))
