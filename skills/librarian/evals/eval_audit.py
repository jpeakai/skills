"""Audit-mode scenarios: read-only, so the shelving plan in the final message is the artifact.

Each case covers one value of an axis in ARCHITECTURE.md section 7: repo state, the dialect
rung that answers, and the path-scope argument. Every case first asserts nothing was
written, because a write from audit is a defect whatever the plan says.
"""

from __future__ import annotations

from _librarian import (
    MODELS,
    SKILL,
    check_no_finding_rows,
    check_not_reported,
    check_read_only,
    check_reported,
)
from pytest_xharness_eval import CaseOutput, evalcase
from pytest_xharness_eval.verify import check_rollout, check_skill_was_loaded

AUDIT_RESOURCES = ("resources/baseline.md", "resources/misplacement_smells.md")


@evalcase(task="audit", skill=SKILL, fixture="greenfield", models=MODELS)
def eval_audit_greenfield(output: CaseOutput) -> None:
    """Baseline rung: a README-only repo is missing every other core document."""
    check_rollout(output)
    check_read_only(output)
    check_skill_was_loaded(output, *AUDIT_RESOURCES)
    check_reported(output, "AGENTS.md", "CONTRIBUTING", "CODING_STANDARDS", "GLOSSARY", "baseline")


@evalcase(task="audit", skill=SKILL, fixture="drift", models=MODELS)
def eval_audit_drift(output: CaseOutput) -> None:
    """A full CLAUDE.md with no AGENTS.md (M3), coding rules in CONTRIBUTING (P8), a term in README (P7)."""
    check_rollout(output)
    check_read_only(output)
    check_skill_was_loaded(output, *AUDIT_RESOURCES)
    check_reported(output, "M3", "P8", "P7", "CODING_STANDARDS")


@evalcase(task="audit", skill=SKILL, fixture="declared_dialect", models=MODELS)
def eval_audit_declared_dialect(output: CaseOutput) -> None:
    """Declared rung: the single-file ADRs.md log is the repo's choice, so it is never a finding."""
    check_rollout(output)
    check_read_only(output)
    check_skill_was_loaded(output, *AUDIT_RESOURCES)
    check_reported(output, "declared")
    check_not_reported(output, "file-per-decision")


@evalcase(task="audit", skill=SKILL, fixture="graduation", models=MODELS)
def eval_audit_graduation(output: CaseOutput) -> None:
    """A minimal-flavour repo whose README passed the docs/ trigger gets a Graduation section."""
    check_rollout(output)
    check_read_only(output)
    check_skill_was_loaded(output, *AUDIT_RESOURCES, "resources/flavours.md")
    check_reported(output, "graduation", "minimal")


@evalcase(task="audit packages/billing", skill=SKILL, fixture="monorepo", models=MODELS)
def eval_audit_scoped(output: CaseOutput) -> None:
    """Path scope: findings land only on billing; the sibling may be mentioned, never filed against."""
    check_rollout(output)
    check_read_only(output)
    check_reported(output, "billing", "P1", "P8")
    check_no_finding_rows(output, "packages/search")
