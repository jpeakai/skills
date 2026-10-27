"""Eval: can the skill restructure an over-budget diagram into its dual-density pattern?

The fixture holds one realistic 46-node platform diagram, well past the skill's 35-node
detailed budget and its 12-node overview budget. The skill's organisation doctrine
(``resources/diagram_organization.md``) says such a diagram becomes *two* fences: a
simplified overview that stays visible, and a detailed reference wrapped in
``<details>`` -- split further if the detail still exceeds 35 nodes -- both colour-themed
and both passing the complexity and contrast gates.

## Why this case has no golden

Its sibling ``eval_palette_mandate`` compares against a committed correct answer, because
styling a fixed four-node diagram is very nearly determined. This is the opposite case.
*Which* twelve of forty-six concepts belong in an overview, and where the detail splits,
are genuine design judgements with many defensible answers -- there is no artifact we
could commit that a correct run should resemble facet by facet (ADR 0046). So the verdict
comes from the lint the skill mandates, run the way a CI pipeline would run it, plus
the structural properties the doctrine actually names.

The last check is the interesting one: getting the structure right *by luck* without ever
running the mandatory gates is a different outcome from getting it right and checking, and
only the second is the behaviour the skill mandates.
"""

from __future__ import annotations

import re
from pathlib import Path

from _lint import check_lint_ran, lint
from _render import RENDER_SCRATCH, render_both_variants
from pytest_xharness_eval import CaseOutput, evalcase
from pytest_xharness_eval.verify import (
    check_files_written,
    check_no_files_added,
    check_rollout,
    facets,
)

SKILL_DIR = Path(__file__).resolve().parent.parent
SKILL = re.search(r"^name:\s*(\S+)", (SKILL_DIR / "mermaidjs-diagrams.md").read_text(encoding="utf-8"), re.MULTILINE)[1]
FIXTURE = "complex_diagram"  # evals/fixtures/complex_diagram/
TARGET = "ARCHITECTURE.md"

# What a user types after naming the skill.
TASK = (
    "ARCHITECTURE.md -- its flowchart is over the complexity budget. Restructure it into "
    "the dual-density pattern, editing the file in place."
)


# -- The skill's mandated lint, used as the verifier ----------------------------------
#
# ``_lint.lint`` is a local verifier, which is exactly what ADR 0013 keeps room for: it is
# specific to this skill's toolchain and belongs beside the case, not in the plugin.


def check_dual_density_structure(output: CaseOutput) -> None:
    """Two fences at least, one always visible and one collapsed, every one of them themed."""
    doc = output.read(TARGET)
    visible, collapsed = facets.visible_fences(doc), facets.collapsed_fences(doc)
    total = len(visible) + len(collapsed)
    assert total >= 2, f"expected an overview fence and at least one detailed fence, found {total}"
    assert visible, "every fence is inside <details>: there is no always-visible overview"
    assert collapsed, "no fence inside a <details> block: the detail was not collapsed"
    bare = facets.unstyled_nodes(doc)
    assert not bare, f"{len(bare)} node(s) left on Mermaid's default palette: {sorted(bare)[:12]}"


def check_the_skills_gates_pass(output: CaseOutput) -> None:
    """The overview fences fit the low preset, and the whole file passes the lint.

    The overview budget is asserted per fence because the lint's default preset only sees
    the file: a document whose overview is 30 nodes passes the default and still fails the
    doctrine that says an overview is at most 12.
    """
    doc = output.read(TARGET)
    scratch = output.path(".gate-scratch")
    scratch.mkdir(exist_ok=True)
    for i, fence in enumerate(facets.visible_fences(doc)):
        single = scratch / f"overview_{i}.mmd"
        single.write_text(fence, encoding="utf-8")
        low = lint(str(single), "--preset", "low", "--profile", "github")
        assert low.returncode == 0, (
            f"visible fence {i} is over the overview budget (<=12 nodes, VCS <=25):\n{low.stdout}"
        )

    # One run: parse, the detailed budget (the default high preset), and contrast.
    whole = lint(str(output.path(TARGET)), "--profile", "github")
    assert whole.returncode == 0, (
        f"the file fails the lint (a fence unparseable, over the detailed budget of <=35 nodes and "
        f"VCS <=60, or below contrast):\n{whole.stdout}{whole.stderr}"
    )


# -- The case -------------------------------------------------------------------------


@evalcase(task=TASK, skill=SKILL, fixture=FIXTURE)
def eval_dual_density(output: CaseOutput) -> None:
    """Evidence, then the structure, then the mandated lint, then whether the run invoked it."""
    check_rollout(output)
    check_files_written(output, TARGET)
    # The scratch directory this grader writes is its own, and is created after the run.
    check_no_files_added(output, allow=RENDER_SCRATCH)
    check_dual_density_structure(output)
    check_the_skills_gates_pass(output)
    render_both_variants(output, TARGET)
    check_lint_ran(output)
