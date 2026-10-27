"""Grade a case's artifact with the lint the skill mandates, and check the run used it.

The skill's gates are the published ``@jpeakai/mermaidjs-lint`` package, not scripts
inside the skill, so two things change for a grader:

- the verifier runs the package (``bunx``, the same command ``mermaidjs-diagrams.md`` gives), and
- "the run executed the gate" can no longer be read off skill-file coverage, because the
  package is not a skill file. It is read off the shell commands the run issued instead.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Iterator

from pytest_xharness_eval import CaseOutput

PACKAGE = "@jpeakai/mermaidjs-lint"
LINT = ("bunx", PACKAGE)


def lint(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the lint on ``args``; the caller judges the exit code (0 clean, 1 findings, 2 usage)."""
    return subprocess.run([*LINT, *args], capture_output=True, text=True, check=False)


def _tool_inputs(output: CaseOutput) -> Iterator[str]:
    """Every tool call's input, serialised, from the primary thread and every subagent."""
    threads = [output.run.calls, *(sub.calls for sub in output.run.subagents)]
    for calls in threads:
        for call in calls:
            for tool in call.tools:
                yield json.dumps(tool.input, default=str)


def check_lint_ran(output: CaseOutput) -> None:
    """The run invoked ``@jpeakai/mermaidjs-lint`` at least once, through any shell tool.

    Right by luck is a different outcome from right and checked; the skill mandates the
    check, so a run that never invoked the lint fails here however good its file is.
    """
    ran = any(PACKAGE in payload for payload in _tool_inputs(output))
    assert ran, f"the run never invoked {PACKAGE}, which the skill declares mandatory"
