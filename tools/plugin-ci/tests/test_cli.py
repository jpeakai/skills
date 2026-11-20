"""CLI discovery, help and installed module behavior."""

import subprocess
import sys
from pathlib import Path

import pytest

from plugin_ci.app import main
from plugin_ci.config import resolve_root


def test_help_and_bad_root(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    assert "plugin-ci" in capsys.readouterr().out
    assert main(["validate", "--project-dir", str(tmp_path)]) == 1
    assert "No plugins/ directory" in capsys.readouterr().err


def test_root_discovery_and_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "plugins").mkdir()
    nested = tmp_path / "nested"
    nested.mkdir()
    monkeypatch.chdir(nested)
    assert resolve_root() == tmp_path
    monkeypatch.setenv("PLUGIN_CI_PROJECT_DIR", str(tmp_path))
    assert resolve_root() == tmp_path
    with pytest.raises(RuntimeError, match="No plugins/"):
        resolve_root(str(nested))


def test_module_entrypoint() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "plugin_ci", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "check-worktree" in result.stdout
    assert not result.stderr


def test_sync_cli_and_missing_canonical_inputs(tmp_path: Path) -> None:
    (tmp_path / "plugins/example").mkdir(parents=True)
    composition = tmp_path / "plugins/composition.yaml"
    composition.write_text("plugins:\n  example:\n    skills: [missing]\n    hooks: true\n")
    assert main(["sync", "--project-dir", str(tmp_path)]) == 1
    assert main(["sync", "--check", "--project-dir", str(tmp_path)]) == 1
    composition.write_text("plugins:\n  missing:\n    skills: []\n    hooks: false\n")
    assert main(["sync", "--project-dir", str(tmp_path)]) == 1
