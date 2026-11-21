"""Mirror canonical skills and hooks into plugin packages."""

from __future__ import annotations

import filecmp
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from ruamel.yaml import YAML

HOOK_FILES = ["hooks.json", "tool_coach.py", "tool_coach_rules.json", "README.md"]
IGNORED = {
    "node_modules",
    "__pycache__",
    ".venv",
    ".mmdc_cache",
    ".pytest_cache",
    ".ruff_cache",
    "evals",
    ".coverage",
    ".mypy_cache",
}


def is_ignored(rel: Path) -> bool:
    return any(part in IGNORED for part in rel.parts)


def load_composition(repo: Path) -> dict[str, dict[str, Any]]:
    data = YAML(typ="safe").load((repo / "plugins/composition.yaml").read_text())
    return cast(dict[str, dict[str, Any]], data["plugins"])


def source_files(directory: Path) -> set[Path]:
    return {
        relative
        for path in directory.rglob("*")
        if path.is_file() and not is_ignored(relative := path.relative_to(directory))
    }


def tree_differs(src: Path, dst: Path, repo: Path) -> list[str]:
    if dst.is_symlink():
        return [f"{dst.relative_to(repo)} is a symlink; Codex will not copy it"]
    if not dst.exists():
        return [f"{dst.relative_to(repo)} missing"]
    diffs = [
        f"{path.relative_to(repo)} must not be published"
        for path in sorted(dst.rglob("evals"))
        if path.is_dir()
    ]
    src_files, dst_files = source_files(src), source_files(dst)
    for missing in sorted(src_files - dst_files):
        diffs.append(f"{(dst / missing).relative_to(repo)} missing")
    for stale in sorted(dst_files - src_files):
        diffs.append(f"{(dst / stale).relative_to(repo)} is stale")
    for common in sorted(src_files & dst_files):
        if not filecmp.cmp(src / common, dst / common, shallow=False):
            diffs.append(f"{(dst / common).relative_to(repo)} differs from canonical")
    return diffs


def remove(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def mirror_dir(src: Path, dst: Path) -> None:
    remove(dst)
    shutil.copytree(src, dst, symlinks=False, ignore=shutil.ignore_patterns(*IGNORED))


@dataclass
class Mirror:
    """Collect drift while applying only explicitly requested mirror writes."""

    repo: Path
    check_only: bool
    drift: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def missing_source(self, message: str) -> None:
        self.drift.append(message)
        self.errors.append(message)

    def remove_stale(self, path: Path, message: str) -> None:
        self.drift.append(message)
        if not self.check_only:
            remove(path)
            self.actions.append(f"removed {path.relative_to(self.repo)}")

    def skills(self, plugin: str, wanted: set[str]) -> None:
        destination = self.repo / "plugins" / plugin / "skills"
        for name in sorted(wanted):
            src, dst = self.repo / "skills" / name, destination / name
            if not src.is_dir():
                self.missing_source(f"skills/{name} named in composition.yaml but missing")
                continue
            differences = tree_differs(src, dst, self.repo)
            self.drift.extend(differences)
            if differences and not self.check_only:
                mirror_dir(src, dst)
                self.actions.append(f"mirrored skills/{name} -> plugins/{plugin}/skills/{name}")
        if destination.is_dir():
            self.stale_skills(destination, wanted)

    def stale_skills(self, directory: Path, wanted: set[str]) -> None:
        for present in sorted(directory.iterdir()):
            if not present.name.startswith(".") and present.name not in wanted:
                self.remove_stale(
                    present, f"{present.relative_to(self.repo)} is not in composition.yaml"
                )

    def hook_file(self, directory: Path, name: str) -> None:
        src, dst = self.repo / "hooks" / name, directory / name
        if not src.is_file():
            self.missing_source(f"hooks/{name} missing from the canonical tree")
            return
        if dst.is_file() and not dst.is_symlink() and filecmp.cmp(src, dst, shallow=False):
            return
        self.drift.append(f"{dst.relative_to(self.repo)} differs from canonical")
        if not self.check_only:
            remove(dst)
            shutil.copy2(src, dst)
            self.actions.append(f"mirrored hooks/{name} -> {dst.relative_to(self.repo)}")

    def hooks(self, plugin: str, enabled: bool) -> None:
        directory = self.repo / "plugins" / plugin / "hooks"
        if not enabled:
            if directory.exists() or directory.is_symlink():
                self.remove_stale(directory, f"{directory.relative_to(self.repo)} declares no hook")
            return
        if not self.check_only:
            directory.mkdir(parents=True, exist_ok=True)
        for name in HOOK_FILES:
            self.hook_file(directory, name)
        if directory.is_dir():
            for present in sorted(directory.iterdir()):
                if present.name not in HOOK_FILES:
                    self.remove_stale(
                        present, f"{present.relative_to(self.repo)} is not a published hook file"
                    )

    def report(self) -> int:
        if self.check_only and self.drift:
            print(f"Plugin mirror is out of date ({len(self.drift)} differences):")
            for difference in self.drift:
                print(f"  - {difference}")
            print("Run: uv run --project tools/plugin-ci plugin-ci sync")
            return 1
        for action in self.actions:
            print(f"  {action}")
        for error in self.errors:
            print(f"ERROR: {error}")
        print(
            f"{len(self.actions)} changes written." if self.actions else "Plugin mirror is in sync."
        )
        return int(bool(self.errors))


def sync(check_only: bool, repo: Path) -> int:
    mirror = Mirror(repo, check_only)
    for plugin, spec in sorted(load_composition(repo).items()):
        if not (repo / "plugins" / plugin).is_dir():
            mirror.missing_source(f"plugins/{plugin} does not exist")
            continue
        mirror.skills(plugin, set(spec["skills"]))
        mirror.hooks(plugin, bool(spec.get("hooks")))
    return mirror.report()
