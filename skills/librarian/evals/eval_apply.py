"""Apply-mode scenario: the drift fixture's plan, executed loss-free.

The fixture has a full CLAUDE.md and no AGENTS.md, and coding rules inside CONTRIBUTING.
After apply, the instructions live in AGENTS.md, CLAUDE.md is the import stub, and the
coding rules sit in CODING_STANDARDS.md with CONTRIBUTING linking to it.
"""

from __future__ import annotations

from _librarian import MODELS, SKILL, check_claude_stub, check_links
from pytest_xharness_eval import CaseOutput, evalcase
from pytest_xharness_eval.verify import check_rollout

#: Lines the fixture holds that must survive the move verbatim (extracts never reword cargo).
AGENT_RULE = "Never commit a file under `data/raw/`"
CODING_RULE = "Name functions with a verb first"


@evalcase(task="apply all", skill=SKILL, fixture="drift", models=MODELS)
def eval_apply_drift(output: CaseOutput) -> None:
    """Instructions moved into AGENTS.md, the stub left, coding rules extracted and linked."""
    check_rollout(output)
    check_claude_stub(output)
    assert AGENT_RULE in output.read("AGENTS.md"), "the agent rule did not move into AGENTS.md verbatim"
    assert CODING_RULE in output.read("CODING_STANDARDS.md"), "the coding rule did not move verbatim"
    assert CODING_RULE not in output.read("CONTRIBUTING.md"), "the coding rule is still in CONTRIBUTING.md"
    check_links(output, "CONTRIBUTING.md", "CODING_STANDARDS.md")
    check_links(output, "AGENTS.md", "CODING_STANDARDS.md")
    stray = [p for p in output.added if not p.startswith(".git/")]
    assert all(p.endswith(".md") for p in stray), f"apply added non-document files: {stray}"
