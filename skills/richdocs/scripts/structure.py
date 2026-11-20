#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["markdown-it-py>=3.0,<5"]
# ///
"""Number Markdown headings and check each visual has its own heading section."""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

from markdown_it import MarkdownIt
from markdown_it.token import Token

RICH_BLOCKS = {"mermaid", "plotly", "cytoscape", "deckgl"}
NUMBER = re.compile(r"^(?:\d+(?:\.\d+)+\.?|\d+\\?\.)[ \t]+")


class VisualCounter(HTMLParser):
    """Count visual roots without counting SVG's internal drawing elements."""

    def __init__(self) -> None:
        super().__init__()
        self.count = 0
        self.svg_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"svg", "img", "canvas"} and self.svg_depth == 0:
            self.count += 1
        if tag == "svg":
            self.svg_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "svg" and self.svg_depth:
            self.svg_depth -= 1


def _without_frontmatter(lines: list[str]) -> str:
    parse_lines = lines.copy()
    if not lines or lines[0].strip() != "---":
        return "".join(parse_lines)
    for end in range(1, len(lines)):
        if lines[end].strip() in {"---", "..."}:
            parse_lines[: end + 1] = ["\n"] * (end + 1)
            break
    return "".join(parse_lines)


def _next_heading_number(depth: int, stack: list[tuple[int, int]]) -> str:
    sibling = 1
    while stack and stack[-1][0] >= depth:
        _, previous_number = stack.pop()
        sibling = previous_number + 1
    stack.append((depth, sibling))
    return ".".join(str(entry[1]) for entry in stack)


def _number_heading(
    line: str, token: Token, content: str, stack: list[tuple[int, int]]
) -> str:
    depth = int(token.tag[1:])
    number = _next_heading_number(depth, stack)
    separator = " "
    if len(stack) == 1:
        separator = ". " if token.markup.startswith("#") else "\\. "
    if token.markup.startswith("#"):
        marker = re.search(r"#{" + str(depth) + r"}(?:[ \t]+|$)", line)
        assert marker is not None
        start = marker.end()
    else:
        start = line.index(content.splitlines()[0])
    spacing = " " if start and line[start - 1] == "#" else ""
    return (
        line[:start]
        + spacing
        + number
        + separator
        + NUMBER.sub("", line[start:], count=1)
    )


def _count_visuals(token: Token) -> int:
    if token.type == "fence":
        info = token.info.split()
        return int(bool(info) and info[0].lower() in RICH_BLOCKS)
    if token.type not in {"inline", "html_block"}:
        return 0
    html = VisualCounter()
    if token.type == "html_block":
        html.feed(token.content)
        return html.count
    count = 0
    for child in token.children or []:
        if child.type == "image":
            count += 1
        elif child.type == "html_inline":
            html.feed(child.content)
    return count + html.count


def prepare(source: str) -> tuple[str, list[str]]:
    """Return numbered source and actionable visual-section diagnostics.

    Heading levels form a stack of actual parents, including skipped levels.
    Each visual belongs to the nearest preceding heading, irrespective of depth.
    """
    lines = source.splitlines(keepends=True)
    tokens = MarkdownIt("commonmark", {"html": True}).parse(_without_frontmatter(lines))
    stack: list[tuple[int, int]] = []
    errors: list[str] = []
    heading_line: int | None = None
    visual_count = 0
    for index, token in enumerate(tokens):
        if token.type == "heading_open" and token.map is not None:
            heading_line = token.map[0]
            visual_count = 0
            lines[heading_line] = _number_heading(
                lines[heading_line], token, tokens[index + 1].content, stack
            )
            continue
        for _ in range(_count_visuals(token)):
            line_number = token.map[0] + 1 if token.map else 1
            if heading_line is None:
                errors.append(
                    f"line {line_number}: visual needs its own descriptive heading before it"
                )
            elif visual_count:
                errors.append(
                    f"line {line_number}: visual needs its own heading; section at line {heading_line + 1} already has a visual"
                )
            visual_count += 1
    return "".join(lines), errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", type=Path)
    parser.add_argument(
        "--fix-headings",
        action="store_true",
        help="write hierarchical numbers; report visual errors for the agent to fix",
    )
    args = parser.parse_args(argv)
    try:
        source = args.document.read_text(encoding="utf-8")
        numbered, errors = prepare(source)
        if numbered != source:
            if args.fix_headings:
                args.document.write_text(numbered, encoding="utf-8")
            else:
                errors.insert(
                    0, "heading numbers need updating; run with --fix-headings"
                )
    except (OSError, UnicodeError) as failure:
        print(f"{args.document}: {failure}", file=sys.stderr)
        return 2
    for error in errors:
        print(f"{args.document}:{error}", file=sys.stderr)
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
