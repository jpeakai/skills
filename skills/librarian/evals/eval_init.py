"""Init-mode scenarios: every flavour argument, plus migrating an existing full CLAUDE.md.

All five leave the same core set (CONVENTIONS, AGENTS.md + stub, GLOSSARY, CODING_STANDARDS),
so the cases differ only in what the Flavour line says and what the migration preserves.
"""

from __future__ import annotations

from _librarian import MODELS, SKILL, check_core_documents, check_flavour, check_reported
from pytest_xharness_eval import CaseOutput, evalcase
from pytest_xharness_eval.verify import check_rollout, check_skill_was_loaded

INIT_RESOURCES = (
    "resources/conventions_template.md",
    "resources/flavours.md",
    "resources/glossary_template.md",
)
FLAVOURS = ("minimal", "standard", "rigorous")


@evalcase(task="init", skill=SKILL, fixture="greenfield", models=MODELS)
def eval_init_infer(output: CaseOutput) -> None:
    """No flavour given: the agent picks one, says which, and records it."""
    check_rollout(output)
    check_skill_was_loaded(output, *INIT_RESOURCES)
    check_core_documents(output)
    conv = output.read("docs/CONVENTIONS.md").lower()
    assert any(f in conv for f in FLAVOURS), "docs/CONVENTIONS.md names no flavour"
    check_reported(output, "flavour")


@evalcase(task="init minimal", skill=SKILL, fixture="greenfield", models=MODELS)
def eval_init_minimal(output: CaseOutput) -> None:
    check_rollout(output)
    check_core_documents(output)
    check_flavour(output, "minimal")


@evalcase(task="init standard", skill=SKILL, fixture="greenfield", models=MODELS)
def eval_init_standard(output: CaseOutput) -> None:
    check_rollout(output)
    check_core_documents(output)
    check_flavour(output, "standard")


@evalcase(task="init rigorous", skill=SKILL, fixture="greenfield", models=MODELS)
def eval_init_rigorous(output: CaseOutput) -> None:
    check_rollout(output)
    check_core_documents(output)
    check_flavour(output, "rigorous")


@evalcase(task="init", skill=SKILL, fixture="full_claude", models=MODELS)
def eval_init_migrate_claude(output: CaseOutput) -> None:
    """An existing full CLAUDE.md becomes AGENTS.md, and the stub takes its place."""
    check_rollout(output)
    check_core_documents(output)
    agents = output.read("AGENTS.md")
    assert "tally-compat contract" in agents, "the original CLAUDE.md rule did not reach AGENTS.md"
