#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "pytest>=8.0", "pytest-cov>=4.0",
#   "PyYAML>=6.0", "Jinja2>=3.1", "jsonschema>=4.0",
# ]
# ///
"""Tests for adr_audit.py — real repos with real git history in tmp_path, no mocks.

Each check gets a compliant case and one case per violation it reports.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

import adr_audit
import okf_render

SCRIPT_DIR = Path(__file__).parent.resolve()
EXAMPLE_DIR = SCRIPT_DIR.parent / "resources" / "okf_yaml" / "example"

AGENTS = "# Agents\n\nDecisions live in [adrs/](adrs/). Check them before raising a question.\n"


def record(number: int, title: str, *, status: str = "Accepted, 2026-01-01", relates: str = "-") -> str:
    return (
        f"# ADR-{number:04d}: {title}\n\n"
        "| Field | Value |\n|---|---|\n"
        f"| **Status** | {status} |\n"
        f"| **Relates to** | {relates} |\n\n"
        "## Decision\n\n#### Given\n\nsome context\n\n#### We prefer\n\nX, over Y\n\n"
        "#### Because\n\nit follows\n\n#### Unless\n\nnever\n\n"
        "## Consequences\n\n- a cost\n"
    )


def section(number: int, title: str) -> str:
    """The same record as one section of a single-file log: every heading one level deeper."""
    return "\n".join(
        "#" + line if line.startswith("#") else line for line in record(number, title).splitlines()
    )


def write(repo: Path, rel: str, text: str) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def commit(repo: Path, message: str = "change") -> None:
    git(repo, "add", "-A")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@example.org", "commit", "-q", "-m", message)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A compliant file-per-decision repo, committed."""
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q")
    write(root, "AGENTS.md", AGENTS)
    write(root, "adrs/0001-first.md", record(1, "first decision"))
    write(root, "adrs/0002-second.md", record(2, "second decision"))
    write(root, "adrs/README.md", "# Decisions\n\n- 0001-first.md\n- 0002-second.md\n")
    commit(root, "initial")
    return root


@pytest.fixture
def bundle_repo(tmp_path: Path) -> Path:
    """A compliant okf-yaml repo: the shipped example, built, committed."""
    root = tmp_path / "okf"
    shutil.copytree(EXAMPLE_DIR, root / "adrs")
    okf_render.render(root / "adrs")  # graph.html names its bundle directory
    git(root, "init", "-q")
    write(root, "AGENTS.md", AGENTS)
    commit(root, "initial")
    return root


def findings(root: Path, given: list[str] | None = None) -> list[dict[str, str]]:
    return list(adr_audit.audit(root, given)["findings"])


def checks(root: Path) -> set[str]:
    return {f["check"] for f in findings(root)}


def load_yml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def dump_yml(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False))


# ── compliant surfaces ──────────────────────────────────────────────────


def test_a_compliant_file_per_decision_repo_has_no_findings(repo: Path) -> None:
    assert findings(repo) == []


def test_a_compliant_okf_yaml_bundle_has_no_findings(bundle_repo: Path) -> None:
    assert findings(bundle_repo) == []


def test_a_compliant_single_file_log_has_no_findings(tmp_path: Path) -> None:
    git(tmp_path, "init", "-q")
    write(tmp_path, "AGENTS.md", AGENTS.replace("adrs/", "ADRs.md"))
    log_text = "# Decisions\n\n" + section(1, "one")
    log_text += "\n" + section(2, "two")
    write(tmp_path, "ADRs.md", log_text + "\n## Template\n\n## ADR-NNNN: shape\n")
    commit(tmp_path)
    assert findings(tmp_path) == []


# ── presence and discovery ──────────────────────────────────────────────


def test_a_repo_with_no_surface_is_a_presence_finding(tmp_path: Path) -> None:
    assert [f["check"] for f in findings(tmp_path)] == ["presence"]


def test_discovery_skips_nested_repos_and_fixtures(repo: Path) -> None:
    write(repo, "nested/.git", "gitdir: elsewhere\n")
    write(repo, "nested/adrs/0001-x.md", record(1, "nested"))
    write(repo, "evals/fixtures/case/adrs/0001-x.md", record(1, "fixture"))
    assert [s.path.as_posix() for s in adr_audit.discover(repo)] == ["adrs"]


def test_a_named_surface_overrides_discovery(repo: Path) -> None:
    result = adr_audit.audit(repo, ["adrs"])
    assert result["surfaces"] == [{"path": "adrs", "layout": "files"}]


def test_a_named_surface_with_no_records_is_a_usage_error(repo: Path) -> None:
    with pytest.raises(ValueError, match="holds no decision records"):
        adr_audit.audit(repo, ["src"])


# ── schema / structure ──────────────────────────────────────────────────


def test_a_markdown_record_missing_its_parts_is_reported(repo: Path) -> None:
    write(repo, "adrs/0003-bare.md", "# ADR-0003: bare\n\nJust a sentence.\n")
    write(repo, "adrs/README.md", "- 0001-first.md\n- 0002-second.md\n- 0003-bare.md\n")
    hits = [f for f in findings(repo) if f["check"] == "schema"]
    assert len(hits) == 1
    assert "no Status, no a decision statement, no reasoning" in hits[0]["finding"]


def test_an_okf_record_failing_the_schema_is_reported(bundle_repo: Path) -> None:
    path = bundle_repo / "adrs" / "0001-validate-at-the-boundary.yml"
    data = load_yml(path)
    data["lens"] = "a removed key"
    dump_yml(path, data)
    hits = [f for f in findings(bundle_repo) if f["check"] == "schema"]
    assert hits and "lens" in hits[0]["finding"]


def test_a_bundle_schema_wins_over_the_skills_own(bundle_repo: Path) -> None:
    schema = json.loads(okf_render.DEFAULT_SCHEMA.read_text())
    schema["properties"]["lens"] = {"type": "string"}
    (bundle_repo / "adrs" / "record.schema.json").write_text(json.dumps(schema))
    path = bundle_repo / "adrs" / "0001-validate-at-the-boundary.yml"
    data = load_yml(path)
    data["lens"] = "allowed here"
    dump_yml(path, data)
    assert "schema" not in checks(bundle_repo)


# ── fresh ────────────────────────────────────────────────────────────────


def test_a_hand_edited_generated_file_is_stale(bundle_repo: Path) -> None:
    path = bundle_repo / "adrs" / "index.md"
    path.write_text(path.read_text() + "\nedited by hand\n")
    hits = [f for f in findings(bundle_repo) if f["check"] == "fresh"]
    assert [h["where"] for h in hits] == ["adrs/index.md"]


def test_a_missing_viewer_is_reported(bundle_repo: Path) -> None:
    shutil.move(bundle_repo / "adrs" / "graph.html", bundle_repo / "graph.html.aside")
    hits = [f for f in findings(bundle_repo) if f["check"] == "fresh"]
    assert hits and "graph.html is missing" in hits[0]["finding"]


def test_markdown_with_no_yml_source_is_a_warning(bundle_repo: Path) -> None:
    write(bundle_repo, "adrs/notes.md", "loose notes\n")
    hits = [f for f in findings(bundle_repo) if f["check"] == "fresh"]
    assert [(h["where"], h["severity"]) for h in hits] == [("adrs/notes.md", adr_audit.YELLOW)]


def test_housekeeping_markdown_in_a_bundle_is_not_a_finding(bundle_repo: Path) -> None:
    for name in ("README.md", "CLAUDE.md", "AGENTS.md", "log.md"):
        write(bundle_repo, f"adrs/{name}", "housekeeping\n")
    assert "fresh" not in checks(bundle_repo)


def test_a_bundle_that_cannot_build_is_left_to_the_schema_check(bundle_repo: Path) -> None:
    path = bundle_repo / "adrs" / "0001-validate-at-the-boundary.yml"
    data = load_yml(path)
    data["status"] = "pending"
    dump_yml(path, data)
    assert "fresh" not in checks(bundle_repo)


def test_a_bundle_with_its_own_templates_is_built_with_them(bundle_repo: Path) -> None:
    shutil.copytree(okf_render.TEMPLATE_DIR, bundle_repo / "adrs" / "templates")
    index = bundle_repo / "adrs" / "templates" / "index.md.j2"
    index.write_text(index.read_text() + "a local footer\n")
    hits = [f for f in findings(bundle_repo) if f["check"] == "fresh"]
    assert [h["where"] for h in hits] == ["adrs/index.md"]


# ── ids ──────────────────────────────────────────────────────────────────


def test_a_duplicate_number_is_reported(repo: Path) -> None:
    write(repo, "adrs/0002-again.md", record(2, "a second second"))
    write(repo, "adrs/README.md", "- 0001-first.md\n- 0002-second.md\n- 0002-again.md\n")
    hits = [f for f in findings(repo) if f["check"] == "ids"]
    assert len(hits) == 1 and "number 2 is used by 2 records" in hits[0]["finding"]


def test_a_gap_in_the_sequence_is_reported(repo: Path) -> None:
    write(repo, "adrs/0005-later.md", record(5, "a later one"))
    write(repo, "adrs/README.md", "- 0001-first.md\n- 0002-second.md\n- 0005-later.md\n")
    hits = [f for f in findings(repo) if f["check"] == "ids"]
    assert len(hits) == 1 and "3, 4" in hits[0]["finding"]


def test_an_okf_record_in_a_misnumbered_file_is_reported(bundle_repo: Path) -> None:
    shutil.move(
        bundle_repo / "adrs" / "0002-one-error-taxonomy.yml",
        bundle_repo / "adrs" / "0003-one-error-taxonomy.yml",
    )
    hits = [f for f in findings(bundle_repo) if f["check"] == "ids"]
    assert hits and "sits in a file numbered 0003" in hits[0]["finding"]


# ── immutable ────────────────────────────────────────────────────────────


def test_rewording_an_accepted_record_is_reported(repo: Path) -> None:
    path = repo / "adrs" / "0001-first.md"
    path.write_text(path.read_text().replace("X, over Y", "Z, over Y"))
    commit(repo, "reword")
    hits = [f for f in findings(repo) if f["check"] == "immutable"]
    assert len(hits) == 1 and "ADR-0001 changed its argument" in hits[0]["finding"]


def test_an_uncommitted_edit_is_caught_too(repo: Path) -> None:
    path = repo / "adrs" / "0001-first.md"
    path.write_text(path.read_text().replace("it follows", "it no longer follows"))
    assert "immutable" in checks(repo)


def test_marking_a_record_superseded_is_not_an_edit(repo: Path) -> None:
    path = repo / "adrs" / "0001-first.md"
    text = path.read_text().replace("Accepted, 2026-01-01", "Superseded by ADR-0003, 2026-02-01")
    path.write_text(text.replace("- a cost", "- a cost (partly superseded by ADR-0003)"))
    write(repo, "adrs/0003-third.md", record(3, "third", relates="supersedes ADR-0001"))
    write(repo, "adrs/README.md", "- 0001-first.md\n- 0002-second.md\n- 0003-third.md\n")
    commit(repo, "supersede")
    assert findings(repo) == []


def test_a_proposed_record_may_change_freely(repo: Path) -> None:
    write(repo, "adrs/0003-draft.md", record(3, "draft", status="Proposed"))
    write(repo, "adrs/README.md", "- 0001-first.md\n- 0002-second.md\n- 0003-draft.md\n")
    commit(repo, "propose")
    path = repo / "adrs" / "0003-draft.md"
    path.write_text(path.read_text().replace("X, over Y", "W, over Y"))
    assert findings(repo) == []


def test_removing_an_accepted_record_is_reported(repo: Path) -> None:
    shutil.move(repo / "adrs" / "0002-second.md", repo / "second.aside")
    write(repo, "adrs/README.md", "- 0001-first.md\n")
    hits = [f for f in findings(repo) if f["check"] == "immutable"]
    assert len(hits) == 1 and "has since been removed" in hits[0]["finding"]


def test_editing_an_accepted_okf_lens_is_reported(bundle_repo: Path) -> None:
    path = bundle_repo / "adrs" / "0002-one-error-taxonomy.yml"
    data = load_yml(path)
    data["decision"]["because"] = "a different reason, written later"
    dump_yml(path, data)
    hits = [f for f in findings(bundle_repo) if f["check"] == "immutable"]
    assert [h["finding"].split()[0] for h in hits] == ["REC-0002"]


def test_an_accepted_log_section_is_tracked_by_id(tmp_path: Path) -> None:
    git(tmp_path, "init", "-q")
    write(tmp_path, "AGENTS.md", AGENTS.replace("adrs/", "ADRs.md"))
    write(tmp_path, "ADRs.md", "# Decisions\n\n" + section(1, "one"))
    commit(tmp_path)
    path = tmp_path / "ADRs.md"
    path.write_text(path.read_text().replace("some context", "other context"))
    hits = [f for f in findings(tmp_path) if f["check"] == "immutable"]
    assert [h["where"] for h in hits] == ["ADRs.md#ADR-0001"]


def test_no_git_history_is_a_warning_not_a_pass(tmp_path: Path) -> None:
    write(tmp_path, "AGENTS.md", AGENTS)
    write(tmp_path, "adrs/0001-first.md", record(1, "first decision"))
    hits = [f for f in findings(tmp_path) if f["check"] == "immutable"]
    assert [h["severity"] for h in hits] == [adr_audit.YELLOW]


# ── relations ────────────────────────────────────────────────────────────


def test_a_mention_of_a_missing_record_is_reported(repo: Path) -> None:
    path = repo / "adrs" / "0002-second.md"
    path.write_text(path.read_text() + "\nSee ADR-0009 for the rest.\n")
    hits = [f for f in findings(repo) if f["check"] == "relations"]
    assert hits and "mentions ADR-9" in hits[0]["finding"]


def test_a_broken_record_link_is_reported(repo: Path) -> None:
    path = repo / "adrs" / "0002-second.md"
    path.write_text(path.read_text() + "\nSee [the first](0001-wrong-name.md).\n")
    hits = [f for f in findings(repo) if f["check"] == "relations"]
    assert hits and "links 0001-wrong-name.md" in hits[0]["finding"]


def test_an_okf_relation_to_a_missing_record_is_reported(bundle_repo: Path) -> None:
    path = bundle_repo / "adrs" / "0002-one-error-taxonomy.yml"
    data = load_yml(path)
    data["relates_to"].append({"relation": "see_also", "target": "REC-0042"})
    dump_yml(path, data)
    hits = [f for f in findings(bundle_repo) if f["check"] == "relations" and f["severity"] == adr_audit.RED]
    assert hits and "REC-0042, which does not exist" in hits[0]["finding"]


def test_a_one_way_okf_relation_is_a_warning(bundle_repo: Path) -> None:
    path = bundle_repo / "adrs" / "0002-one-error-taxonomy.yml"
    data = load_yml(path)
    data["relates_to"] = []
    dump_yml(path, data)
    okf_render.render(bundle_repo / "adrs")
    hits = [f for f in findings(bundle_repo) if f["check"] == "relations"]
    assert [h["severity"] for h in hits] == [adr_audit.YELLOW]


# ── superseded ───────────────────────────────────────────────────────────


def test_a_supersession_left_unmarked_on_the_old_record_is_reported(repo: Path) -> None:
    write(repo, "adrs/0003-third.md", record(3, "third", relates="supersedes ADR-0001"))
    write(repo, "adrs/README.md", "- 0001-first.md\n- 0002-second.md\n- 0003-third.md\n")
    hits = [f for f in findings(repo) if f["check"] == "superseded"]
    assert len(hits) == 1 and "ADR-0001 is not marked superseded" in hits[0]["finding"]


def test_a_superseded_record_naming_no_successor_is_reported(repo: Path) -> None:
    path = repo / "adrs" / "0002-second.md"
    path.write_text(path.read_text().replace("Accepted, 2026-01-01", "Superseded, 2026-02-01"))
    hits = [f for f in findings(repo) if f["check"] == "superseded"]
    assert len(hits) == 1 and "names no successor" in hits[0]["finding"]


def okf_supersede(bundle: Path, *, mark_old: bool) -> None:
    new = bundle / "0002-one-error-taxonomy.yml"
    data = load_yml(new)
    data["relates_to"].append({"relation": "supersedes", "target": "REC-0001"})
    dump_yml(new, data)
    old = bundle / "0001-validate-at-the-boundary.yml"
    data = load_yml(old)
    if mark_old:
        data["status"] = "superseded"
        data["relates_to"].append({"relation": "superseded_by", "target": "REC-0002"})
    dump_yml(old, data)


def test_an_okf_supersession_marked_both_ways_passes(bundle_repo: Path) -> None:
    okf_supersede(bundle_repo / "adrs", mark_old=True)
    okf_render.render(bundle_repo / "adrs")
    assert findings(bundle_repo) == []


def test_an_okf_supersession_left_unmarked_is_reported(bundle_repo: Path) -> None:
    okf_supersede(bundle_repo / "adrs", mark_old=False)
    hits = [f for f in findings(bundle_repo) if f["check"] == "superseded"]
    assert len(hits) == 1 and "REC-0001 is not marked superseded" in hits[0]["finding"]


def test_an_okf_superseded_record_with_no_successor_is_reported(bundle_repo: Path) -> None:
    path = bundle_repo / "adrs" / "0002-one-error-taxonomy.yml"
    data = load_yml(path)
    data["status"] = "superseded"
    dump_yml(path, data)
    hits = [f for f in findings(bundle_repo) if f["check"] == "superseded"]
    assert len(hits) == 1 and "REC-0002 is superseded but names no successor" in hits[0]["finding"]


# ── wiring ───────────────────────────────────────────────────────────────


def test_no_agent_file_is_reported(repo: Path) -> None:
    shutil.move(repo / "AGENTS.md", repo / "agents.aside")
    hits = [f for f in findings(repo) if f["check"] == "wiring"]
    assert len(hits) == 1 and "no agent file" in hits[0]["finding"]


def test_an_agent_file_that_never_links_the_surface_is_reported(repo: Path) -> None:
    write(repo, "AGENTS.md", "# Agents\n\nCheck the docs before you ask.\n")
    hits = [f for f in findings(repo) if f["check"] == "wiring"]
    assert len(hits) == 1 and "never links adrs" in hits[0]["finding"]


def test_a_link_with_no_check_before_you_ask_line_is_reported(repo: Path) -> None:
    write(repo, "AGENTS.md", "# Agents\n\nDecisions live in [adrs/](adrs/).\n")
    hits = [f for f in findings(repo) if f["check"] == "wiring"]
    assert len(hits) == 1 and "before asking" in hits[0]["finding"]


def test_wiring_split_across_claude_and_agents_files_counts(repo: Path) -> None:
    write(repo, "AGENTS.md", "# Agents\n\nRead the decisions before asking a question.\n")
    write(repo, "CLAUDE.md", "@AGENTS.md\n\nDecisions: adrs/\n")
    assert "wiring" not in checks(repo)


# ── index ────────────────────────────────────────────────────────────────


def test_an_index_missing_a_record_is_reported(repo: Path) -> None:
    write(repo, "adrs/README.md", "# Decisions\n\n- 0001-first.md\n")
    hits = [f for f in findings(repo) if f["check"] == "index"]
    assert len(hits) == 1 and "does not list 0002-second.md" in hits[0]["finding"]


def test_a_scoped_log_missing_from_the_root_index_is_reported(repo: Path) -> None:
    write(repo, "packages/billing/ADRs.md", "# Decisions\n\n" + section(1, "billing"))
    hits = [f for f in findings(repo) if f["check"] == "index"]
    assert len(hits) == 1 and "scoped log packages/billing/ADRs.md" in hits[0]["finding"]


def test_a_scoped_log_linked_from_the_root_index_passes(repo: Path) -> None:
    write(repo, "packages/billing/ADRs.md", "# Decisions\n\n" + section(1, "billing"))
    index = "# Decisions\n\n- 0001-first.md\n- 0002-second.md\n- [billing](../packages/billing/ADRs.md)\n"
    write(repo, "adrs/README.md", index)
    commit(repo)
    assert "index" not in checks(repo)


def test_a_root_surface_with_no_index_misses_every_scoped_log(bundle_repo: Path) -> None:
    shutil.move(bundle_repo / "adrs" / "index.md", bundle_repo / "index.aside")
    write(bundle_repo, "lib/adrs/0001-x.md", record(1, "lib"))
    hits = [f for f in findings(bundle_repo) if f["check"] == "index"]
    assert [h["where"] for h in hits] == ["adrs"]


# ── report and CLI ───────────────────────────────────────────────────────


def test_the_report_says_compliant_when_clean(repo: Path) -> None:
    assert "Compliant: no findings." in adr_audit.report(adr_audit.audit(repo))


def test_the_report_tabulates_red_before_yellow(tmp_path: Path) -> None:
    write(tmp_path, "adrs/0001-first.md", record(1, "first decision"))
    text = adr_audit.report(adr_audit.audit(tmp_path))
    rows = [line for line in text.splitlines() if line.startswith("| ") and line[2].isdigit()]
    assert rows[0].endswith(f"{adr_audit.RED} |") and rows[-1].endswith(f"{adr_audit.YELLOW} |")


def run(argv: list[str]) -> int:
    return adr_audit.main(adr_audit.build_parser().parse_args(argv))


def test_cli_exits_zero_when_compliant(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert run([str(repo)]) == 0
    assert "ADR audit: 2 records in 1 surfaces" in capsys.readouterr().out


def test_cli_exits_one_on_a_red_finding_and_emits_json(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    shutil.move(repo / "AGENTS.md", repo / "agents.aside")
    assert run([str(repo), "--json"]) == 1
    assert json.loads(capsys.readouterr().out)["findings"][0]["check"] == "wiring"


def test_cli_exits_zero_on_warnings_only(tmp_path: Path) -> None:
    write(tmp_path, "AGENTS.md", AGENTS)
    write(tmp_path, "adrs/0001-first.md", record(1, "first decision"))
    assert run([str(tmp_path), "-v"]) == 0


def test_cli_exits_two_on_a_bad_surface(repo: Path) -> None:
    assert run([str(repo), "--surface", "missing"]) == 2


if __name__ == "__main__":  # pragma: no cover
    script_dir = str(Path(__file__).parent.resolve())
    base_args = [__file__, "-v", "--rootdir", script_dir, "-o", "addopts="]
    sys.exit(pytest.main(base_args + sys.argv[1:]))
