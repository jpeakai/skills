"""Eval: does the palette mandate survive an ``erDiagram``, where its usual recipe fails?

The regression behind jpeakai/skills#6. Mermaid paints a ``classDef`` ``fill:`` on an
entity's *even* attribute rows only; the odd rows keep the theme's own surface, which
flips with the reader's theme, while ``color:`` lands on every row. So the recipe that is
right for a flowchart -- opaque ``fill:`` paired with ``color:`` (``color_theming.md`` §3)
-- leaves half of every entity unreadable in one theme. The right answer here is the
translucent recipe: no ``color:``, a translucent fill, the hue in an opaque stroke.

The fixture is one unstyled five-entity data model and the task is the same sentence the
flowchart case uses. Nothing in it mentions rows, themes or the exception: an agent that
applies §3 by rote produces the shipped defect, and only reaching the ``erDiagram``
exception -- or being stopped by the contrast gate that now models it -- gets it right.

## What the golden decides, and what the gate decides

``goldens/unstyled_erd/DATA_MODEL.md`` fixes the *structure*: the entities, relationships
and attributes are the fixture's, and a styling task must not change them. It deliberately
does not fix the colours. Whether a palette reads on both row surfaces in both themes is a
contrast question with many right answers, and the skill ships the verifier for exactly
that question, so the colour verdict comes from ``mermaid_contrast.ts`` rather than a
hex-level facet.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from _render import RENDER_SCRATCH, render_both_variants
from pytest_xharness_eval import CaseOutput, evalcase
from pytest_xharness_eval.verify import (
    Count,
    Exact,
    Facet,
    GoldenCase,
    Ratio,
    Superset,
    check_files_written,
    check_no_files_added,
    check_rollout,
    check_skill_scripts_ran,
    facets,
)

EVALS = Path(__file__).resolve().parent
SKILL_DIR = EVALS.parent
SKILL = re.search(r"^name:\s*(\S+)", (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8"), re.MULTILINE)[1]
FIXTURE = "unstyled_erd"  # evals/fixtures/unstyled_erd/
TARGET = "DATA_MODEL.md"
SCRIPTS = SKILL_DIR / "scripts"

# The same sentence eval_palette_mandate uses, pointed at a different diagram type.
TASK = "DATA_MODEL.md -- apply the mandatory colour theming to its diagram, editing the file in place."


# -- erDiagram extractors ---------------------------------------------------------------
#
# The plugin's facets read flowchart syntax, so an erDiagram's node_ids and edges come back
# empty and would compare equal to anything. These read the erDiagram grammar instead.

_ENTITY_BLOCK = re.compile(r"^\s*([A-Za-z][\w-]*)\s*\{(.*?)\}", re.MULTILINE | re.DOTALL)
_RELATIONSHIP = re.compile(
    r"^\s*([A-Za-z][\w-]*)\s+([|}o][|o]--[|o][|{o]|[|}o][|o]\.\.[|o][|{o])\s+([A-Za-z][\w-]*)", re.MULTILINE
)
_CLASS_STMT = re.compile(r"^\s*class\s+([\w,\s-]+?)\s+([A-Za-z][\w-]*)\s*;?\s*$", re.MULTILINE)
_INLINE_CLASS = re.compile(r"([A-Za-z][\w-]*):::[A-Za-z][\w-]*")
_STYLE_STMT = re.compile(r"^\s*style\s+([A-Za-z][\w-]*)\s+\S", re.MULTILINE)


def entities(doc: str) -> set[str]:
    """Every entity an erDiagram declares, by attribute block or by relationship."""
    out: set[str] = set()
    for body in facets.fences(doc):
        out.update(name for name, _ in _ENTITY_BLOCK.findall(body))
        for left, _, right in _RELATIONSHIP.findall(body):
            out.update((left, right))
    return out - {"erDiagram"}


def relationships(doc: str) -> set[str]:
    """Every relationship as ``LEFT <cardinality> RIGHT``: the model's shape."""
    return {
        f"{left} {card} {right}" for body in facets.fences(doc) for left, card, right in _RELATIONSHIP.findall(body)
    }


def attributes(doc: str) -> set[str]:
    """Every attribute as ``ENTITY.name``: the rows the theming has to keep readable."""
    out: set[str] = set()
    for body in facets.fences(doc):
        for entity, block in _ENTITY_BLOCK.findall(body):
            for line in block.splitlines():
                parts = line.split()
                if len(parts) >= 2:
                    out.add(f"{entity}.{parts[1]}")
    return out


def unstyled_entities(doc: str) -> set[str]:
    """Entities that no ``class``, ``:::`` or ``style`` statement reaches."""
    styled: set[str] = set()
    for body in facets.fences(doc):
        for names, _ in _CLASS_STMT.findall(body):
            styled.update(n.strip() for n in names.split(","))
        styled.update(_INLINE_CLASS.findall(body))
        styled.update(_STYLE_STMT.findall(body))
    return entities(doc) - styled


GOLDEN = GoldenCase.at(
    EVALS,
    FIXTURE,
    TARGET,
    [
        Facet(
            name="mermaid fences",
            extract=facets.fence_count,
            tolerance=Exact(),
            why="the one fence is styled in place -- not replaced, and not duplicated into a styled copy",
        ),
        Facet(
            name="entities",
            extract=entities,
            tolerance=Exact(),
            why="this is a styling task: the fixture fixes which entities exist",
        ),
        Facet(
            name="relationships",
            extract=relationships,
            tolerance=Exact(),
            why="colouring a data model must not change its cardinalities",
        ),
        Facet(
            name="attributes",
            extract=attributes,
            tolerance=Exact(),
            why="the attribute rows are what the theming has to keep readable; dropping rows dodges the problem",
        ),
        Facet(
            name="unstyled entities",
            extract=unstyled_entities,
            tolerance=Count(lo=0, hi=0),
            why="the mandate is that NO entity is left on Mermaid's default, not that one classDef exists",
        ),
        Facet(
            name="classDef groups",
            extract=facets.classdef_count,
            tolerance=Count(lo=2, hi=6),
            why="people, transactions and catalogue are distinct roles; one class for all encodes nothing",
        ),
        Facet(
            name="headings",
            extract=facets.headings,
            tolerance=Superset(),
            why="the document around the diagram survives",
        ),
        Facet(
            name="prose",
            extract=facets.body_text,
            tolerance=Ratio(at_least=0.9),
            why="same reason, at the level of the words",
        ),
    ],
)


# -- The skill's own gate, as the colour verifier ---------------------------------------


def check_contrast_gate_passes(output: CaseOutput) -> None:
    """The row-aware contrast gate passes: text reads on both row surfaces in both themes.

    This is the assertion the case exists for. An opaque ``fill:`` + ``color:`` pairing
    fails it on one theme's odd rows, however well it reads on the fill itself.
    """
    result = subprocess.run(
        ["bun", "run", str(SCRIPTS / "mermaid_contrast.ts"), str(output.path(TARGET)), "--profile", "github"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        "the erDiagram fails the contrast gate -- text is unreadable on an attribute row in one theme "
        f"(see color_theming.md §3, the erDiagram exception):\n{result.stdout}{result.stderr}"
    )


# -- The case -------------------------------------------------------------------------


@evalcase(task=TASK, skill=SKILL, fixture=FIXTURE)
def eval_erd_theming(output: CaseOutput) -> None:
    """Evidence, scope, structure against the golden, colour via the gate, a real render, then that it checked."""
    check_rollout(output)
    check_files_written(output, TARGET)
    check_no_files_added(output, allow=RENDER_SCRATCH)
    GOLDEN.assert_matches(output)
    check_contrast_gate_passes(output)
    render_both_variants(output, TARGET)
    # Right by luck is a different outcome from right and checked; the skill mandates the check.
    check_skill_scripts_ran(output, "scripts/mermaid_contrast.ts")
