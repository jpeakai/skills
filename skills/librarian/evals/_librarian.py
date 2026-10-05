"""Checks shared by the librarian eval cases.

Every check here is structural, matching the skill's own rule that it judges location and
shape, never content (ADR-1). They read the workspace the agent left, or the final message
for read-only modes, where the shelving plan is the only artifact.
"""

from __future__ import annotations

import re
from pathlib import Path

from pytest_xharness_eval import CaseOutput

SKILL_DIR = Path(__file__).resolve().parent.parent
SKILL = re.search(r"^name:\s*(\S+)", (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8"), re.MULTILINE)[1]

#: Quick, cheap runs: the point is to see what the skill materialises, not to sweep.
MODELS = ["claude/claude-sonnet-5-5"]

STUB = "@AGENTS.md"


def check_read_only(output: CaseOutput) -> None:
    """Audit and a refused index write nothing at all."""
    assert not output.written, f"a read-only mode wrote {output.written}"


def check_reported(output: CaseOutput, *terms: str) -> None:
    """Each term appears in the final message, case-insensitively."""
    text = output.run.final_text.lower()
    missing = [t for t in terms if t.lower() not in text]
    assert not missing, f"the report never mentions {missing}:\n{output.run.final_text}"


def check_not_reported(output: CaseOutput, *terms: str) -> None:
    """No term appears in the final message."""
    text = output.run.final_text.lower()
    present = [t for t in terms if t.lower() in text]
    assert not present, f"the report mentions out-of-scope {present}:\n{output.run.final_text}"


def check_no_finding_rows(output: CaseOutput, *terms: str) -> None:
    """No shelving-plan table row names a term; prose may still mention it as out of scope."""
    rows = [line for line in output.run.final_text.splitlines() if line.lstrip().startswith("|")]
    hits = [row for row in rows for t in terms if t.lower() in row.lower()]
    assert not hits, f"the plan files findings against out-of-scope {terms}:\n" + "\n".join(hits)


def check_claude_stub(output: CaseOutput, rel_dir: str = "") -> None:
    """CLAUDE.md beside AGENTS.md holds exactly the import line."""
    base = f"{rel_dir}/" if rel_dir else ""
    assert output.exists(f"{base}AGENTS.md"), f"no {base}AGENTS.md"
    stub = output.read(f"{base}CLAUDE.md").strip()
    assert stub == STUB, f"{base}CLAUDE.md must be exactly {STUB!r}, got:\n{stub}"


def check_links(output: CaseOutput, source: str, *targets: str) -> None:
    """``source`` links to every target by filename."""
    text = output.read(source)
    missing = [t for t in targets if t not in text]
    assert not missing, f"{source} does not link {missing}"


def check_glossary_shape(output: CaseOutput, rel: str = "GLOSSARY.md") -> None:
    """The template's structural rules: currency line, one diagram, alphabetical H2s, H2-to-node parity."""
    doc = output.read(rel)
    assert "same change" in doc, f"{rel} intro lacks the same-change currency rule"
    assert doc.count("```mermaid") == 1, f"{rel} needs exactly one relationship diagram"
    terms = re.findall(r"^## (.+)$", doc, re.MULTILINE)
    assert terms, f"{rel} defines no terms as H2s"
    assert terms == sorted(terms, key=str.lower), f"{rel} terms are not alphabetical: {terms}"
    diagram = doc.split("```mermaid", 1)[1].split("```", 1)[0]
    unplaced = [t for t in terms if f'"{t}"' not in diagram]
    assert not unplaced, f"{rel} terms with no diagram node: {unplaced}"


def check_flavour(output: CaseOutput, flavour: str) -> None:
    """docs/CONVENTIONS.md records the flavour on its Flavour line."""
    conv = output.read("docs/CONVENTIONS.md")
    line = re.search(r"^.*Flavour.*$", conv, re.MULTILINE)
    assert line, "docs/CONVENTIONS.md has no Flavour line"
    assert flavour in line[0].lower(), f"Flavour line should name {flavour}: {line[0]}"


def check_core_documents(output: CaseOutput) -> None:
    """Init leaves every core document present and wired from AGENTS.md."""
    for rel in ("docs/CONVENTIONS.md", "AGENTS.md", "GLOSSARY.md", "CODING_STANDARDS.md"):
        assert output.exists(rel), f"init did not leave {rel}; workspace holds {output.filenames}"
    check_claude_stub(output)
    check_links(output, "AGENTS.md", "CONVENTIONS.md", "GLOSSARY.md", "CODING_STANDARDS.md")
    check_glossary_shape(output)
    check_adr_surface_template(output)
    check_coding_standards_tenets(output)


def check_coding_standards_tenets(output: CaseOutput) -> None:
    """CODING_STANDARDS.md carries the seven baseline tenets, located by their load-bearing words."""
    doc = output.read("CODING_STANDARDS.md").lower()
    markers = {
        "autoformatting": "format",
        "strict lint, warnings as errors": "warning",
        "strict type checking": "type",
        "coverage above 90%": "90",
        "no mocks": "mock",
        "no tautological tests": "tautolog",
        "complexity capped": "complexity",
    }
    missing = [tenet for tenet, word in markers.items() if word not in doc]
    assert not missing, f"CODING_STANDARDS.md lacks baseline tenets {missing}"


def check_adr_surface_template(output: CaseOutput) -> None:
    """Init leaves an ADR surface carrying its layout's template, with the four lens headings."""
    if output.exists("ADRs.md"):
        surface = output.read("ADRs.md")
    else:
        assert output.exists("adrs/TEMPLATE.md"), f"no ADR surface template; workspace holds {output.filenames}"
        surface = output.read("adrs/TEMPLATE.md")
    missing = [h for h in ("Given", "We prefer", "Because", "Unless") if f"# {h}" not in surface]
    assert not missing, f"the ADR template lacks lens headings {missing}"
