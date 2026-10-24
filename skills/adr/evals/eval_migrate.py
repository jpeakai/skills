"""Migrate-mode scenario: an OKF markdown surface with a consumer moves to okf-yaml.

`make check-adrs` reads the records, so the trigger has fired. The bundle gets a .yml record
per decision, a schema and a viewer, and the run reads the convention and runs its generator.
"""

from __future__ import annotations

from _adr import MODELS, SKILL
from pytest_xharness_eval import CaseOutput, evalcase
from pytest_xharness_eval.verify import check_rollout, check_skill_scripts_ran, check_skill_was_loaded


@evalcase(task="migrate okf-yaml adrs/", skill=SKILL, fixture="adr_log_consumer", models=MODELS)
def eval_migrate_okf_yaml(output: CaseOutput) -> None:
    check_rollout(output)
    records = [p for p in output.filenames if p.startswith("adrs/") and p.endswith(".yml")]
    assert len(records) >= 2, f"expected a .yml record per decision, found {records}"
    assert any(p.endswith("record.schema.json") for p in output.filenames), "no record schema copied in"
    assert output.exists("adrs/graph.html"), "the bundle ships no graph.html viewer"
    # Artifact first, provenance second: a correct bundle built without reading the
    # convention or running the skill's generator is a different outcome, and is reported as one.
    check_skill_was_loaded(output, "resources/adr_okf_yaml.md")
    check_skill_scripts_ran(output, "scripts/okf_render.py")
