"""Setup-mode scenarios: one per markdown layout, on a repo with an agent file and no surface.

Setup ends by running audit, so each case also asserts the audit script ran.
The okf-yaml layout is covered by the migrate case, which builds the same bundle.
"""

from __future__ import annotations

from _adr import MODELS, SKILL, check_lens_headings, check_wired
from pytest_xharness_eval import CaseOutput, evalcase
from pytest_xharness_eval.verify import check_rollout, check_skill_scripts_ran, check_skill_was_loaded


@evalcase(task="setup files", skill=SKILL, fixture="greenfield", models=MODELS)
def eval_setup_files(output: CaseOutput) -> None:
    """File-per-decision: adrs/ with TEMPLATE.md and an index, wired from AGENTS.md."""
    check_rollout(output)
    check_skill_was_loaded(output, "resources/adr_template.md")
    check_lens_headings(output.read("adrs/TEMPLATE.md"), "adrs/TEMPLATE.md")
    assert output.exists("adrs/README.md"), f"no adrs/ index; workspace holds {output.filenames}"
    check_wired(output, "adrs/")
    check_skill_scripts_ran(output, "scripts/adr_audit.py")


@evalcase(task="setup log", skill=SKILL, fixture="greenfield", models=MODELS)
def eval_setup_log(output: CaseOutput) -> None:
    """Single-file log: ADRs.md closing with a Template section, wired from AGENTS.md."""
    check_rollout(output)
    log = output.read("ADRs.md")
    assert "## Template" in log, "ADRs.md has no closing Template section"
    check_lens_headings(log.split("## Template", 1)[1], "ADRs.md Template")
    check_wired(output, "ADRs.md")
    check_skill_scripts_ran(output, "scripts/adr_audit.py")
