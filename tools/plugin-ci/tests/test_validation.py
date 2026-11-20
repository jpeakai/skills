"""Validate real package trees and their failure cases."""

import json
from pathlib import Path

import pytest

from plugin_ci.app import main
from plugin_ci.commands.sync_plugins import HOOK_FILES, sync
from plugin_ci.commands.validate_plugins import (
    AGENT_PLUGINS_SCHEMA,
    Report,
    check_composition,
    check_hook_wiring,
    check_manifests,
    check_marketplaces,
    check_no_symlinks,
    check_skills,
    frontmatter,
)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.fixture
def package(tmp_path: Path) -> Path:
    plugin = tmp_path / "plugins/example"
    plugin.mkdir(parents=True)
    (tmp_path / "plugins/composition.yaml").write_text(
        "plugins:\n  example:\n    skills: [example]\n    hooks: true\n"
    )
    source = tmp_path / "skills/example"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text("---\nname: example\n---\nRuntime instructions\n")
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    for name in HOOK_FILES:
        (hooks / name).write_text("{}\n")
    manifest = {"name": "example", "version": "1.0.0"}
    write_json(plugin / ".claude-plugin/plugin.json", manifest)
    write_json(
        plugin / ".codex-plugin/plugin.json",
        {
            **manifest,
            "skills": "./skills",
            "hooks": "./hooks/hooks.json",
        },
    )
    write_json(
        plugin / "plugin.json",
        {
            **manifest,
            "$schema": AGENT_PLUGINS_SCHEMA,
            "keywords": ["example"],
        },
    )
    write_json(
        tmp_path / ".claude-plugin/marketplace.json",
        {
            "plugins": [{"name": "example", "source": "./plugins/example"}],
        },
    )
    write_json(
        tmp_path / ".agents/plugins/marketplace.json",
        {
            "plugins": [{"name": "example", "source": {"path": "./plugins/example"}}],
        },
    )
    assert sync(False, tmp_path) == 0
    return tmp_path


def test_valid_package_and_drift(package: Path) -> None:
    assert main(["validate", "--project-dir", str(package)]) == 0
    (package / "plugins/example/skills/example/SKILL.md").write_text("wrong\n")
    assert main(["--project-dir", str(package), "validate"]) == 1


def test_missing_manifest_paths(package: Path) -> None:
    plugin = package / "plugins/example"
    for relative in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json", "plugin.json"):
        target = plugin / relative
        saved = target.read_bytes()
        target.unlink()
        report = Report()
        check_manifests(report, package)
        assert report.failures
        target.write_bytes(saved)


def test_disabled_and_missing_hook_wiring(package: Path) -> None:
    wiring = package / "plugins/example/hooks/hooks.json"
    wiring.unlink()
    report = Report()
    check_hook_wiring(report, package)
    assert report.failures
    (package / "plugins/composition.yaml").write_text(
        "plugins:\n  example:\n    skills: [example]\n    hooks: false\n"
    )
    report = Report()
    check_hook_wiring(report, package)
    check_manifests(report, package)
    assert any("no hooks" in failure for failure in report.failures)
    assert sync(False, package) == 0
    report = Report()
    check_hook_wiring(report, package)
    assert not report.failures


def test_symlink_and_missing_skill(package: Path) -> None:
    entry = package / "plugins/example/skills/example"
    (entry / "SKILL.md").unlink()
    report = Report()
    check_skills(report, package)
    assert report.failures
    link = package / "plugins/example/link"
    link.symlink_to(package / "skills/example", target_is_directory=True)
    report = Report()
    check_no_symlinks(report, package)
    assert report.failures


def test_composition_and_marketplace_failures(package: Path) -> None:
    (package / "plugins/extra").mkdir()
    report = Report()
    check_composition(report, package)
    assert report.failures
    write_json(
        package / ".agents/plugins/marketplace.json",
        {
            "plugins": [
                {"name": "missing", "source": {"path": "missing"}, "policy": {"unsupported": True}}
            ],
        },
    )
    report = Report()
    check_marketplaces(report, package)
    assert report.failures


def test_frontmatter_absent_or_not_mapping(tmp_path: Path) -> None:
    source = tmp_path / "SKILL.md"
    for text in ("No header", "---\n- list\n---\n"):
        source.write_text(text)
        assert frontmatter(source) == {}
