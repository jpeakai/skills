"""Exercise CLI contracts with real files and safe subprocesses."""

import subprocess
import sys
from importlib.resources import files
from pathlib import Path

import pytest

from harness_ci.app import main
from harness_ci.commands.run import execute, run
from harness_ci.config import project_root


def repository(path: Path) -> Path:
    """Create the repository sentinel."""
    (path / "plugins").mkdir(parents=True)
    (path / "plugins/composition.yaml").write_text("plugins: []\n")
    return path


def test_root_resolution(tmp_path: Path) -> None:
    root = repository(tmp_path / "repo")
    child = root / "nested"
    child.mkdir()
    assert project_root(None, child) == root
    assert project_root(root, tmp_path) == root
    with pytest.raises(ValueError, match=r"No plugins/composition\.yaml"):
        project_root(tmp_path, child)
    with pytest.raises(ValueError, match="supply --project-dir"):
        project_root(None, tmp_path)


def test_cli_help_and_missing_root(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as help_exit:
        main(["--help"])
    assert help_exit.value.code == 0
    with pytest.raises(SystemExit) as error_exit:
        main(["run", "--project-dir", str(tmp_path)])
    assert error_exit.value.code == 2  # noqa: PLR2004


def test_real_subprocess_contract(tmp_path: Path) -> None:
    output_path = tmp_path / "output"
    with output_path.open("w") as output:
        result = execute(
            [
                sys.executable,
                "-c",
                "import os; print(os.environ['HARNESS_CI_PROJECT_DIR']); exit(7)",
            ],
            tmp_path,
            output,
        )
    assert result == 7  # noqa: PLR2004
    assert output_path.read_text().strip() == str(tmp_path)


def test_sandbox_paths_with_safe_shell_asset(tmp_path: Path) -> None:
    script = tmp_path / "safe.sh"
    script.write_text('test "$HARNESS_CI_PROJECT_DIR" = "$1"\n')
    assert run(tmp_path, tmp_path, asset_path=script) == 0
    script.write_text(
        'case "$1" in "$HARNESS_CI_PROJECT_DIR"/tmp/harness-ci/*) exit 0;; *) exit 1;; esac\n'
    )
    assert run(tmp_path, None, asset_path=script) == 0


def test_packaged_shell_is_valid() -> None:
    asset = files("harness_ci").joinpath("assets/install.sh")
    result = subprocess.run(["bash", "-n", str(asset)], check=False, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert "cli librarian" in asset.read_text()


def test_environment_root_and_explicit_precedence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    selected = repository(tmp_path / "selected")
    explicit = repository(tmp_path / "explicit")
    monkeypatch.setenv("HARNESS_CI_PROJECT_DIR", str(selected))
    assert project_root(None, tmp_path) == selected
    assert project_root(explicit, tmp_path) == explicit
