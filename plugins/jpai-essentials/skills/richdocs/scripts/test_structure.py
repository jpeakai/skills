#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest>=8.0", "pytest-cov>=4.0", "markdown-it-py>=3.0,<5"]
# ///
"""Document structure checks against real Markdown and filesystem output."""

import sys
from pathlib import Path

import pytest

import structure


def test_numbers_hierarchy_and_restarts_children() -> None:
    source = "# Guide\n## Setup\n### Local\n### Remote\n## Usage\n# Reference\n## API\n"
    expected = "# 1. Guide\n## 1.1 Setup\n### 1.1.1 Local\n### 1.1.2 Remote\n## 1.2 Usage\n# 2. Reference\n## 2.1 API\n"
    assert structure.prepare(source)[0] == expected
    assert structure.prepare(expected) == (expected, [])


def test_preserves_examples_frontmatter_and_heading_format() -> None:
    source = "---\ntitle: Example\n---\nGuide\n=====\n\n~~~markdown\n# Example\n```plotly\n{}\n```\n~~~\n\n## 7.2 Setup ##\n## 2026 outlook\n"
    expected = (
        source.replace("Guide\n", "1\\. Guide\n")
        .replace("7.2 Setup", "1.1 Setup")
        .replace("2026 outlook", "1.2 2026 outlook")
    )
    assert structure.prepare(source) == (expected, [])
    assert structure.prepare(expected) == (expected, [])


def test_skipped_heading_levels_follow_actual_parents() -> None:
    source = "## Intro\n#### Detail\n## Next\n"
    assert structure.prepare(source)[0] == "## 1. Intro\n#### 1.1 Detail\n## 2. Next\n"


@pytest.mark.parametrize("kind", ["mermaid", "plotly", "cytoscape", "deckgl"])
def test_rejects_unheaded_and_shared_fenced_visuals(kind: str) -> None:
    visual = f"```{kind}\n{{}}\n```\n"
    assert "heading" in structure.prepare(visual)[1][0]
    errors = structure.prepare("# Guide\n" + visual + visual)[1]
    assert len(errors) == 1
    assert "line 5" in errors[0]
    assert "own heading" in errors[0]


def test_child_sections_have_their_own_visual_budget() -> None:
    source = (
        "# Guide\n## Flow\n```mermaid\nflowchart LR\n```\n## Cost\n```plotly\n{}\n```\n"
    )
    assert structure.prepare(source)[1] == []


@pytest.mark.parametrize(
    "visual",
    [
        "![Flow](flow.svg)",
        "![Flow][ref]\n\n[ref]: flow.svg",
        '<svg><path d=""/></svg>',
        '<img src="chart.png">',
        "<canvas></canvas>",
    ],
)
def test_images_and_html_visuals_need_separate_headings(visual: str) -> None:
    assert structure.prepare(visual)[1]
    assert structure.prepare("## Chart\n" + visual)[1] == []


def test_nested_svg_is_one_visual_but_sibling_roots_are_separate() -> None:
    nested = '<svg><svg viewBox="0 0 10 10"><path d="M0 0"/></svg><svg/></svg>'
    assert structure.prepare("# Diagram\n" + nested)[1] == []
    assert len(structure.prepare("# Diagrams\n" + nested + "<svg/>")[1]) == 1


def test_two_images_on_one_line_fail() -> None:
    assert len(structure.prepare("# Charts\n![a](a.svg) ![b](b.svg)\n")[1]) == 1


def test_quoted_and_list_headings_preserve_container_markers() -> None:
    source = "> # Quoted\n> ![A](a.svg)\n\n- ## Listed\n\n  ![B](b.svg)\n"
    assert structure.prepare(source) == (
        source.replace("# Quoted", "# 1. Quoted").replace("## Listed", "## 1.1 Listed"),
        [],
    )


def test_cli_checks_without_writing_and_fixes_idempotently(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    doc = tmp_path / "guide.md"
    doc.write_text("# Guide\n## Chart\n![Chart](chart.svg)\n", encoding="utf-8")
    assert structure.main([str(doc)]) == 1
    assert doc.read_text().startswith("# Guide")
    assert "number" in capsys.readouterr().err
    assert structure.main([str(doc), "--fix-headings"]) == 0
    expected = "# 1. Guide\n## 1.1 Chart\n![Chart](chart.svg)\n"
    assert doc.read_text() == expected
    assert structure.main([str(doc), "--fix-headings"]) == 0
    assert doc.read_text() == expected


def test_cli_retains_invalid_visuals_for_agent_to_fix(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    doc = tmp_path / "guide.md"
    doc.write_text("# Guide\n![a](a.svg) ![b](b.svg)\n", encoding="utf-8")
    assert structure.main([str(doc), "--fix-headings"]) == 1
    assert "own heading" in capsys.readouterr().err
    assert "![a](a.svg) ![b](b.svg)" in doc.read_text()


def test_skipped_depths_do_not_duplicate_sibling_numbers() -> None:
    source = "# Guide\n### First\n## Second\n### Child\n"
    assert (
        structure.prepare(source)[0]
        == "# 1. Guide\n### 1.1 First\n## 1.2 Second\n### 1.2.1 Child\n"
    )


def test_empty_heading_stays_a_heading() -> None:
    numbered, _ = structure.prepare("#\n## Child\n")
    assert numbered == "# 1. \n## 1.1 Child\n"
    assert structure.prepare(numbered)[0] == numbered


def test_cli_missing_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert structure.main([str(tmp_path / "missing.md")]) == 2
    assert "missing.md" in capsys.readouterr().err


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, *sys.argv[1:]]))
