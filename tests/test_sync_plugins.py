"""Plugin generation excludes development evals, including stale copies."""

import shutil
import subprocess
import sys
from pathlib import Path


def test_sync_removes_evals_and_preserves_canonical_sources(tmp_path: Path) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    script = scripts / "sync_plugins.py"
    shutil.copyfile(Path(__file__).resolve().parents[1] / "scripts/sync_plugins.py", script)
    plugins = tmp_path / "plugins"
    plugins.mkdir()
    (plugins / "composition.yaml").write_text("plugins:\n  example:\n    skills: [example]\n    hooks: false\n")
    source = tmp_path / "skills/example"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text("Runtime guidance\n")
    for relative in ("evals", "vendor/example/evals"):
        directory = source / relative
        directory.mkdir(parents=True)
        (directory / "case.py").write_text("assert True\n")
    destination = plugins / "example/skills/example"
    shutil.copytree(source, destination)

    def run(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True)

    assert run("--check").returncode == 1
    assert run().returncode == 0
    assert (destination / "SKILL.md").read_text() == "Runtime guidance\n"
    assert not list(destination.rglob("evals"))
    assert len(list(source.rglob("case.py"))) == 2
    assert run("--check").returncode == 0
