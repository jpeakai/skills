#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["markdown-it-py>=3.0,<5"]
# ///
"""Check that Plotly fenced JSON explicitly places legends on the right."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from markdown_it import MarkdownIt

LEGEND = re.compile(r"legend(?:[2-9]|[1-9][0-9]+)?$")
POSITION = {"orientation": "v", "xref": "paper", "xanchor": "left", "yanchor": "top"}


def _number_between(value: object, lower: float, upper: float) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and lower <= value <= upper
    )


def _right_side(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    return (
        value.get("visible", True) is True
        and all(value.get(key) == expected for key, expected in POSITION.items())
        and _number_between(value.get("x"), 1.02, 3)
        and _number_between(value.get("y"), 0, 1)
    )


def _payload_errors(payload: object) -> list[str]:
    if not isinstance(payload, dict) or not isinstance(payload.get("layout"), dict):
        return ["Plotly needs an explicit layout.legend on the right"]
    layout = payload["layout"]
    if layout.get("showlegend") is not True:
        return ["layout.showlegend must be true so the chart legend is visible"]
    names = {"legend"} | {key for key in layout if LEGEND.fullmatch(key)}
    for trace in (
        payload.get("data", []) if isinstance(payload.get("data", []), list) else []
    ):
        if isinstance(trace, dict) and isinstance(trace.get("legend"), str):
            names.add(trace["legend"])
    return [
        f"layout.{name}: keep visible=true and set orientation=v, xref=paper, x between 1.02 and 3, xanchor=left, y between 0 and 1, yanchor=top"
        for name in sorted(names)
        if not _right_side(layout.get(name))
    ]


def check(source: str) -> list[str]:
    """Return line diagnostics for each noncompliant Plotly chart definition."""
    errors = []
    for token in MarkdownIt("commonmark").parse(source):
        if token.type != "fence" or token.info.split()[:1] != ["plotly"]:
            continue
        line = token.map[0] + 1 if token.map else 1
        try:
            payload = json.loads(token.content)
        except ValueError as failure:
            errors.append(f"line {line}: invalid Plotly JSON: {failure}")
            continue
        errors.extend(f"line {line}: {error}" for error in _payload_errors(payload))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", type=Path)
    args = parser.parse_args(argv)
    try:
        errors = check(args.document.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as failure:
        print(f"{args.document}: {failure}", file=sys.stderr)
        return 2
    for error in errors:
        print(f"{args.document}:{error}", file=sys.stderr)
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
