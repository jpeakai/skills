"""Checks shared by the adr eval cases.

Every check here is structural, matching the skill's own rule that it judges the shape of a
decision surface, never a decision's reasoning. Read-only modes are graded on the final
message, where the findings table is the only artifact; mutating modes on the workspace.
"""

from __future__ import annotations

import re
from pathlib import Path

from pytest_xharness_eval import CaseOutput

SKILL_DIR = Path(__file__).resolve().parent.parent
SKILL = re.search(r"^name:\s*(\S+)", (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8"), re.MULTILINE)[1]

#: Quick, cheap runs: the point is to see what the skill materialises, not to sweep.
MODELS = ["claude/claude-sonnet-5-5"]

LENS = ("Given", "We prefer", "Because", "Unless")


def check_read_only(output: CaseOutput) -> None:
    """Audit writes nothing at all."""
    assert not output.written, f"a read-only mode wrote {output.written}"


def check_reported(output: CaseOutput, *terms: str) -> None:
    """Each term appears in the final message, case-insensitively."""
    text = output.run.final_text.lower()
    missing = [t for t in terms if t.lower() not in text]
    assert not missing, f"the report never mentions {missing}:\n{output.run.final_text}"


def check_lens_headings(text: str, where: str) -> None:
    """A template carries the four lens headings."""
    missing = [h for h in LENS if f"# {h}" not in text]
    assert not missing, f"{where} lacks lens headings {missing}"


def check_wired(output: CaseOutput, surface: str) -> None:
    """AGENTS.md links the surface beside a check-before-you-ask line."""
    agents = output.read("AGENTS.md")
    assert surface in agents, f"AGENTS.md does not link {surface}"
    assert re.search(r"(?i)\bbefore\b[^.\n]*\b(ask|asking|question)", agents), "AGENTS.md has no check-before-you-ask line"
