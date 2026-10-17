#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest>=8.0", "pytest-cov>=4.0"]
# ///
"""Tests for profile_resolver.py: the five-tier cascade, .default-profile and the DTCG reader."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

import profile_resolver as pr


def make_profile(folder: Path, doc: dict[str, Any] | None = None) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / pr.TOKENS_FILE
    path.write_text(json.dumps(doc or {}), encoding="utf-8")
    return path


@pytest.fixture
def roots(tmp_path: Path) -> tuple[Path, Path]:
    return tmp_path / "project", tmp_path / "home"


def test_candidate_dirs_follow_the_five_tier_order(roots: tuple[Path, Path]) -> None:
    project, home = roots
    dirs = pr.candidate_dirs("brand", "richdocs", project, home)
    tail = Path("skills/richdocs/resources/profile/brand")
    assert dirs == [
        project / ".design-profiles/brand",
        home / ".design-profiles/brand",
        project / ".codex" / tail,
        project / ".claude" / tail,
        home / ".codex" / tail,
        home / ".claude" / tail,
    ]


def test_first_tier_holding_a_profile_wins(roots: tuple[Path, Path]) -> None:
    project, home = roots
    user = make_profile(home / ".design-profiles/brand")
    assert pr.resolve_profile("brand", "richdocs", project, home) == user
    local = make_profile(project / ".design-profiles/brand")
    assert pr.resolve_profile("brand", "richdocs", project, home) == local


def test_skill_tiers_are_searched_after_the_shared_store(
    roots: tuple[Path, Path],
) -> None:
    project, home = roots
    skill = make_profile(home / ".claude/skills/richdocs/resources/profile/brand")
    assert pr.resolve_profile("brand", "richdocs", project, home) == skill
    with pytest.raises(pr.ProfileError, match="resolves nowhere"):
        pr.resolve_profile("brand", "other-skill", project, home)


def test_no_name_and_no_default_falls_through_to_the_built_in(
    roots: tuple[Path, Path],
) -> None:
    project, home = roots
    assert pr.resolve_profile(None, "richdocs", project, home) is None


def test_default_profile_resolves_through_the_same_cascade(
    roots: tuple[Path, Path],
) -> None:
    project, home = roots
    target = make_profile(home / ".design-profiles/brand")
    (project / ".design-profiles").mkdir(parents=True)
    (project / ".design-profiles/.default-profile").write_text(
        "brand\n", encoding="utf-8"
    )
    assert pr.resolve_profile(None, "richdocs", project, home) == target


def test_project_default_wins_over_user_default(roots: tuple[Path, Path]) -> None:
    project, home = roots
    for store, name in ((project, "a"), (home, "b")):
        (store / ".design-profiles").mkdir(parents=True)
        (store / ".design-profiles/.default-profile").write_text(name, encoding="utf-8")
    assert pr.default_profile_name(project, home) == "a"


def test_default_naming_a_missing_profile_fails_loudly(
    roots: tuple[Path, Path],
) -> None:
    project, home = roots
    (home / ".design-profiles").mkdir(parents=True)
    (home / ".design-profiles/.default-profile").write_text("ghost", encoding="utf-8")
    with pytest.raises(pr.ProfileError, match=r"'ghost' \(from .default-profile\)"):
        pr.resolve_profile(None, "richdocs", project, home)


def test_empty_default_file_fails_loudly(roots: tuple[Path, Path]) -> None:
    project, home = roots
    (project / ".design-profiles").mkdir(parents=True)
    (project / ".design-profiles/.default-profile").write_text("\n", encoding="utf-8")
    with pytest.raises(pr.ProfileError, match="is empty"):
        pr.default_profile_name(project, home)


def test_defaults_to_cwd_and_home(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    target = make_profile(tmp_path / ".design-profiles/brand")
    assert (
        pr.resolve_profile("brand", "richdocs")
        == Path(".design-profiles/brand/design-tokens.json").absolute()
    )
    assert target.is_file()


# ── Reader ──────────────────────────────────────────────────────────────────
def colour(hexs: str, alpha: float = 1.0) -> dict[str, Any]:
    value: dict[str, Any] = {"colorSpace": "srgb", "components": [0, 0, 0], "hex": hexs}
    if alpha != 1.0:
        value["alpha"] = alpha
    return value


def doc_with(
    light: dict[str, Any], dark: dict[str, Any] | None = None, default: str = "light"
) -> dict[str, Any]:
    return {
        "version": "2025.10",
        "modifiers": {
            "mode": {
                "contexts": {"light": [light], "dark": [dark or light]},
                "default": default,
                "$extensions": {
                    pr.EXT: {"profile": "t", "fontStylesheet": "https://x"}
                },
            }
        },
        "resolutionOrder": [{"$ref": "#/modifiers/mode"}],
    }


TREE = {
    "color": {
        "$type": "color",
        "text": {
            "default": {"$value": colour("#111111")},
            "subtle": {"$value": colour("#222222")},
        },
        "border": {
            "default": {"$value": colour("#111111", 0.14)},
            "focused": {"$value": "{color.link}"},
        },
        "link": {"$value": "{color.text.default}"},
    },
    "font": {
        "$type": "fontFamily",
        "family": {"body": {"$value": ["Fira Sans", "sans-serif"]}},
    },
    "surface": {
        "$type": "color",
        "plotly": {
            "colorway": {
                "2": {"$value": "{color.text.subtle}"},
                "1": {"$value": colour("#333333")},
            }
        },
    },
    "size": {"gap": {"$type": "number", "$value": 4}},
}


def test_read_tokens_flattens_restores_bare_names_and_resolves_alias_chains() -> None:
    flat = pr.read_tokens(doc_with(TREE))
    assert flat["color.text"] == "#111111"
    assert flat["color.border"] == "#11111124"
    assert flat["color.border.focused"] == "#111111"  # focused -> link -> text.default
    assert flat["font.family.body"] == "'Fira Sans', sans-serif"
    assert flat["size.gap"] == 4
    assert pr.series(flat, "surface.plotly.colorway") == ["#333333", "#222222"]
    assert pr.group(flat, "color.text") == {"subtle": "#222222"}


def test_read_tokens_picks_the_mode_and_merges_its_sets() -> None:
    dark = {"color": {"$type": "color", "text": {"$value": colour("#eeeeee")}}}
    doc = doc_with(TREE, dark, default="dark")
    doc["modifiers"]["mode"]["contexts"]["dark"].append(
        {"color": {"link": {"$value": "{color.text}"}}}
    )
    assert pr.default_mode(doc) == "dark"
    assert pr.modes(doc) == ["light", "dark"]
    assert pr.read_tokens(doc) == {"color.text": "#eeeeee", "color.link": "#eeeeee"}
    assert pr.extension(doc)["fontStylesheet"] == "https://x"


def test_read_tokens_rejects_an_unknown_mode() -> None:
    with pytest.raises(pr.ProfileError, match="no mode 'sepia'"):
        pr.read_tokens(doc_with(TREE), "sepia")


@pytest.mark.parametrize(
    ("tree", "message"),
    [
        ({"a": {"$value": "{b}"}, "b": {"$value": "{a}"}}, "alias cycle"),
        ({"a": {"$value": "{nowhere}"}}, "does not define"),
    ],
)
def test_read_tokens_rejects_broken_aliases(tree: dict[str, Any], message: str) -> None:
    with pytest.raises(pr.ProfileError, match=message):
        pr.read_tokens(doc_with(tree))


def test_extension_is_empty_without_one() -> None:
    doc = doc_with(TREE)
    del doc["modifiers"]["mode"]["$extensions"]
    assert pr.extension(doc) == {}


if __name__ == "__main__":  # pragma: no cover
    script_dir = str(Path(__file__).parent.resolve())
    sys.exit(
        pytest.main(
            [__file__, "-v", "--rootdir", script_dir, "-o", "addopts=", *sys.argv[1:]]
        )
    )
