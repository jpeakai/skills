"""Index-mode scenarios: the trigger is absent, or present with the named okf-yaml convention.

The refusal is as much a behaviour as the build: with no consumer reading the records,
plain markdown is the correct answer and the run must write nothing.
"""

from __future__ import annotations

from _librarian import MODELS, SKILL, check_read_only, check_reported
from pytest_xharness_eval import CaseOutput, evalcase
from pytest_xharness_eval.verify import check_rollout, check_skill_scripts_ran, check_skill_was_loaded


@evalcase(task="index docs/", skill=SKILL, fixture="docs_no_consumer", models=MODELS)
def eval_index_no_consumer(output: CaseOutput) -> None:
    """No script, gate or view reads the docs, so nothing is generated."""
    check_rollout(output)
    check_read_only(output)
    check_skill_was_loaded(output, "resources/structured_siblings.md")
    check_reported(output, "consumer")


@evalcase(task="index okf-yaml adrs/", skill=SKILL, fixture="adr_log_consumer", models=MODELS)
def eval_index_okf_yaml(output: CaseOutput) -> None:
    """`make check-adrs` is the consumer; the bundle gets records, a schema and a viewer."""
    check_rollout(output)
    records = [p for p in output.filenames if p.startswith("adrs/") and p.endswith(".yml")]
    assert len(records) >= 2, f"expected a .yml record per decision, found {records}"
    assert any(p.endswith("record.schema.json") for p in output.filenames), "no record schema copied in"
    assert output.exists("adrs/graph.html"), "the bundle ships no graph.html viewer"
    # Artifact first, provenance second: a correct bundle built without reading the
    # convention or running the skill's generator is a different outcome, and is reported as one.
    check_skill_was_loaded(output, "resources/adr_okf_yaml.md")
    check_skill_scripts_ran(output, "scripts/okf_render.py")
