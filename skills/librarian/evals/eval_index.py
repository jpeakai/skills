"""Index-mode scenarios: the trigger is absent, or the okf-yaml convention is asked for by name.

Both are refusals, and a refusal is as much a behaviour as a build: with no consumer reading
the records, plain markdown is the correct answer, and okf-yaml belongs to the adr skill.
Either way the run must write nothing.
"""

from __future__ import annotations

from _librarian import MODELS, SKILL, check_read_only, check_reported
from pytest_xharness_eval import CaseOutput, evalcase
from pytest_xharness_eval.verify import check_rollout, check_skill_was_loaded


@evalcase(task="index docs/", skill=SKILL, fixture="docs_no_consumer", models=MODELS)
def eval_index_no_consumer(output: CaseOutput) -> None:
    """No script, gate or view reads the docs, so nothing is generated."""
    check_rollout(output)
    check_read_only(output)
    check_skill_was_loaded(output, "resources/structured_siblings.md")
    check_reported(output, "consumer")


@evalcase(task="index okf-yaml docs/", skill=SKILL, fixture="docs_no_consumer", models=MODELS)
def eval_index_okf_yaml_redirects(output: CaseOutput) -> None:
    """The named ADR convention is the adr skill's, so index points there and stops."""
    check_rollout(output)
    check_read_only(output)
    check_reported(output, "/adr migrate okf-yaml")
