#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest>=8.0", "pytest-cov>=4.0", "markdown-it-py>=3.0,<5"]
# ///
"""Check actual Markdown chart definitions and CLI diagnostics."""

import json
import sys
from pathlib import Path

import pytest

import legends

RIGHT = {
    "orientation": "v",
    "xref": "paper",
    "x": 1.02,
    "xanchor": "left",
    "y": 1,
    "yanchor": "top",
}


def chart(payload: object) -> str:
    return "# Cost\n\n```plotly\n" + json.dumps(payload) + "\n```\n"


def test_accepts_right_side_and_preserves_source() -> None:
    source = chart(
        {
            "data": [{"name": "Cost", "y": [2]}],
            "layout": {"showlegend": True, "legend": RIGHT},
        }
    )
    assert legends.check(source) == []


@pytest.mark.parametrize(
    "changes",
    [
        {"x": 0},
        {"x": -0.1},
        {"orientation": "h"},
        {"xanchor": "right"},
        {"xref": "container"},
        {"y": -0.2},
        {"yanchor": "bottom"},
        {"x": True},
        {"x": "1.02"},
    ],
)
def test_rejects_displaced_legends(changes: dict[str, object]) -> None:
    assert legends.check(
        chart({"layout": {"showlegend": True, "legend": RIGHT | changes}})
    )


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"layout": {}},
        {"layout": {"showlegend": True, "legend": {}}},
        {"layout": {"showlegend": True, "legend": None}},
        {"layout": []},
        [],
        None,
    ],
)
def test_rejects_missing_or_malformed_settings(payload: object) -> None:
    assert legends.check(chart(payload))


@pytest.mark.parametrize("visibility", [None, False, "true", 1])
def test_legend_visibility_is_explicit(visibility: object) -> None:
    assert (
        "showlegend"
        in legends.check(
            chart({"layout": {"showlegend": visibility, "legend": RIGHT}})
        )[0]
    )


@pytest.mark.parametrize("name", ["legend", "legend2"])
def test_rejects_hidden_legends(name: str) -> None:
    layout = {"showlegend": True, "legend": RIGHT, name: RIGHT | {"visible": False}}
    assert legends.check(chart({"layout": layout}))


def test_named_legends_are_checked() -> None:
    payload = {
        "data": [{"legend": "legend2"}],
        "layout": {"showlegend": True, "legend": RIGHT, "legend2": RIGHT | {"x": 1.2}},
    }
    assert legends.check(chart(payload)) == []
    payload["layout"].pop("legend2")
    assert "legend2" in legends.check(chart(payload))[0]


def test_ignores_non_chart_examples_and_parses_quoted_fences() -> None:
    assert legends.check("```markdown\n```plotly\n{}\n```\n```\n") == []
    assert legends.check("~~~text\n```plotly\n{}\n```\n~~~\n") == []
    assert "line 2" in legends.check("> # Chart\n> ```plotly\n> {}\n> ```\n")[0]


def test_bad_json_and_multiple_fences_report_locations() -> None:
    errors = legends.check("```plotly\n{broken\n```\n\n```plotly\n{}\n```\n")
    assert len(errors) == 2
    assert "JSON" in errors[0]
    assert "line 5" in errors[1]


def test_cli_is_read_only_and_reports_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "chart.md"
    path.write_text(chart({}))
    before = path.read_bytes()
    assert legends.main([str(path)]) == 1
    assert str(path) in capsys.readouterr().err
    assert path.read_bytes() == before
    path.write_text(chart({"layout": {"showlegend": True, "legend": RIGHT}}))
    assert legends.main([str(path)]) == 0
    assert legends.main([str(tmp_path / "missing.md")]) == 2


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, *sys.argv[1:]]))
