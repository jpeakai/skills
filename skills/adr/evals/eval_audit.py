"""Audit-mode scenarios: read-only, so the findings table in the final message is the artifact.

The compliant fixture must come back clean; the violations fixture carries one defect per
markdown check, and the report must name each check. `scripts/test_adr_audit.py` pins the
same two fixtures deterministically, so a failure here is the agent, not the script.
"""

from __future__ import annotations

from _adr import MODELS, SKILL, check_read_only, check_reported
from pytest_xharness_eval import CaseOutput, evalcase
from pytest_xharness_eval.verify import check_rollout, check_skill_scripts_ran

AUDIT_SCRIPT = "scripts/adr_audit.py"


@evalcase(task="audit", skill=SKILL, fixture="adr_compliant", models=MODELS)
def eval_audit_compliant(output: CaseOutput) -> None:
    """Three records, one superseded both ways, wired and indexed: no 🔴 finding."""
    check_rollout(output)
    check_read_only(output)
    check_skill_scripts_ran(output, AUDIT_SCRIPT)
    check_reported(output, "0 🔴")


@evalcase(task="audit", skill=SKILL, fixture="adr_violations", models=MODELS)
def eval_audit_violations(output: CaseOutput) -> None:
    """A missing Status, a gap, a dangling mention, an unmarked supersession, no ask line, two index gaps."""
    check_rollout(output)
    check_read_only(output)
    check_skill_scripts_ran(output, AUDIT_SCRIPT)
    check_reported(output, "schema", "ids", "relations", "superseded", "wiring", "index")
