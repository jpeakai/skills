#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest>=8.0", "pytest-cov>=4.0", "jsonschema>=4.23"]
# ///
"""Tests for profiles.py: curation, provenance, contrast scoring, the DTCG build and the CLI."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import jsonschema
import pytest

import profile_resolver
import profiles

SCHEMA = json.loads(
    (Path(__file__).parent / "schemas/2025.10/resolver.json").read_text(
        encoding="utf-8"
    )
)
ROLES = [
    "color.surface.sunken",
    "color.surface",
    "color.surface.raised",
    "color.text",
    "color.text.subtle",
    "color.text.subtlest",
    "color.text.inverse",
    "color.border",
    "color.border.bold",
    "color.border.brand",
    "color.background.brand.bold",
    "color.background.brand.subtlest",
    "color.link",
    "color.border.selected",
    "color.border.focused",
    "color.background.selected",
    "color.text.selected",
    "color.text.danger",
    "color.text.warning",
    "color.text.success",
]
SURFACES = ("css", "cytoscape", "plotly", "mermaid", "deckgl", "drawio")


@pytest.fixture
def store(tmp_path: Path) -> Path:
    return tmp_path / ".design-profiles"


def seeded(store: Path, name: str, seed: dict[str, Any]) -> Path:
    folder = store / name
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "seed.json").write_text(json.dumps(seed), encoding="utf-8")
    return folder


def ir_of(folder: Path) -> dict[str, Any]:
    ir: dict[str, Any] = json.loads((folder / "ir.json").read_text(encoding="utf-8"))
    return ir


# ── Colour maths ────────────────────────────────────────────────────────────
def test_contrast_matches_known_wcag_values() -> None:
    assert round(profiles.contrast("#000000", "#ffffff"), 2) == 21.0
    assert round(profiles.contrast("#ffc000", "#ffffff"), 2) == 1.64


def test_oklch_round_trips_and_exact_oklch_uses_few_decimals() -> None:
    assert profiles.exact_oklch("#5c4295") == (0.45, 0.131, 295.044)
    assert profiles.hex_of(profiles.oklch_of("#5c4295")) == "#5c4295"


def test_composite_and_helpers() -> None:
    assert profiles.composite("#00000080", "#ffffff") == "#7f7f7f"
    assert profiles.best_text("#ffffff") == "#000000"
    assert profiles.best_text("#000000") == "#ffffff"
    assert profiles.rgba("#0102037f") == [1, 2, 3, 127]
    assert profiles.max_chroma(0.0, 120) == 0.0
    assert profiles.font_families("'Fira Sans', \"A B\", serif") == [
        "Fira Sans",
        "A B",
        "serif",
    ]


# ── Seeds ───────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    ("seed", "message"),
    [
        ({}, "must state brand.hue"),
        ({"brand.hue": 1, "nope": 2}, "unknown seed parameter"),
        ({"brand.hue": 1, "mode.default": "sepia"}, "mode.default"),
    ],
)
def test_resolve_params_rejects_bad_seeds(seed: dict[str, Any], message: str) -> None:
    with pytest.raises(SystemExit, match=message):
        profiles.resolve_params(seed)


def test_resolve_params_tags_stated_and_defaults() -> None:
    params = profiles.resolve_params({"brand.hue": 10})
    assert params["brand.hue"] == (10, "stated")
    assert params["L-dark-bg"][1].startswith("default (DT-REF-1")


# ── Curation ────────────────────────────────────────────────────────────────
def test_hue_only_seed_imputes_every_role_and_surface_with_no_defect(
    store: Path,
) -> None:
    folder = seeded(store, "p", {"brand.hue": 295})
    report = profiles.curate_profile(folder)
    ir = ir_of(folder)
    assert not [r for r in report if r.startswith(("defect", "choice"))]
    for role in [*ROLES, *(f"color.chart.categorical.{i}" for i in range(1, 13))]:
        assert set(ir[role]) >= {"light", "dark", "$extensions"}, role
    for surface in SURFACES:
        assert any(k.startswith(f"surface.{surface}.") for k in ir), surface
    assert (
        ir["surface.mermaid.primaryColor"]["$extensions"][profiles.EXT]["alias"]
        == "color.background.brand.subtlest"
    )
    assert ir["surface.deckgl.background"]["light"] == profiles.rgba(
        ir["color.surface"]["light"]
    )


def test_mermaid_values_are_opaque(store: Path) -> None:
    folder = seeded(store, "p", {"brand.hue": 30})
    profiles.curate_profile(folder)
    ir = ir_of(folder)
    values = [
        ir[k][m] for k in ir if k.startswith("surface.mermaid.") for m in profiles.MODES
    ]
    assert values and all(len(v) == 7 for v in values)


@pytest.mark.parametrize("hue", range(0, 360, 15))
def test_hue_only_seeds_round_the_wheel_score_zero_defects(hue: int) -> None:
    ir = profiles.Curator({"brand.hue": hue}).run()
    assert not [s for s in profiles.score_contrast(ir) if s["verdict"] == "defect"]


def test_curation_is_idempotent(store: Path) -> None:
    folder = seeded(store, "p", {"brand.hue": 140})
    profiles.curate_profile(folder)
    first = (folder / "ir.json").read_text(encoding="utf-8")
    report = profiles.curate_profile(folder)
    assert (folder / "ir.json").read_text(encoding="utf-8") == first
    assert not [r for r in report if r.startswith(("new", "updated", "held"))]


def test_a_hand_edit_is_held_and_feeds_everything_derived_after_it(store: Path) -> None:
    folder = seeded(store, "p", {"brand.hue": 200})
    profiles.curate_profile(folder)
    ir = ir_of(folder)
    ir["color.surface"]["light"] = "#ffffff"
    (folder / "ir.json").write_text(json.dumps(ir), encoding="utf-8")
    report = profiles.curate_profile(folder)
    after = ir_of(folder)
    assert after["color.surface"]["light"] == "#ffffff"
    assert (
        after["color.surface"]["$extensions"][profiles.EXT]["origin"]["light"]
        == "stated"
    )
    assert any(
        r.startswith("held    color.surface light #ffffff stated (rule would give")
        for r in report
    )
    assert (
        after["surface.css.page"]["light"] == "#ffffff"
    )  # a later surface reads the stated value
    # Releasing it (deleting the value) lets the rule impute it again.
    del after["color.surface"]["light"]
    (folder / "ir.json").write_text(json.dumps(after), encoding="utf-8")
    profiles.curate_profile(folder)
    assert ir_of(folder)["color.surface"]["light"] != "#ffffff"


def test_a_role_curation_does_not_know_is_kept(store: Path) -> None:
    folder = seeded(store, "p", {"brand.hue": 200})
    profiles.curate_profile(folder)
    ir = ir_of(folder)
    ir["color.text.brand"] = {"light": "#123456", "dark": "#abcdef"}
    (folder / "ir.json").write_text(json.dumps(ir), encoding="utf-8")
    report = profiles.curate_profile(folder)
    assert ir_of(folder)["color.text.brand"] == {"light": "#123456", "dark": "#abcdef"}
    assert "held    color.text.brand (not a curated role; kept as stated)" in report


def test_a_stated_parameter_that_causes_a_miss_is_a_choice(store: Path) -> None:
    folder = seeded(store, "p", {"brand.hue": 200, "offset.text.subtle": 0.05})
    report = profiles.curate_profile(folder)
    assert any(r.startswith("choice  color.text.subtle") for r in report)
    assert not [r for r in report if r.startswith("defect")]


def test_a_default_that_causes_a_miss_is_a_defect(store: Path) -> None:
    defaults = dict(
        profiles.DEFAULTS, **{"offset.text.subtle": (0.05, "a bad default")}
    )
    folder = seeded(store, "p", {"brand.hue": 200})
    report = profiles.curate_profile(folder, defaults)
    assert any(r.startswith("defect  color.text.subtle") for r in report)


def test_stated_dark_accent_and_keywords(store: Path) -> None:
    seed = {
        "brand.hue": 295.044,
        "brand.chroma": 0.131,
        "brand.lightness": 0.45,
        "brand.dark.lightness": 0.8,
    }
    curator = profiles.Curator(
        seed | {"walk.chromaCeiling": "seed", "walk.lightness": 0.6}
    )
    ir = curator.run()
    assert ir["color.background.brand.bold"]["light"] == "#5c4295"
    assert curator.resolved["brand.dark.lightness"] == 0.8
    assert curator.resolved["walk.lightness"] == {"light": 0.6, "dark": 0.6}
    numeric = profiles.Curator(
        {"brand.hue": 10, "walk.chromaCeiling": 0.05, "secondary.hue": 90}
    ).run()
    assert (
        numeric["color.chart.categorical.1"]["$extensions"][profiles.EXT]["oklch"][
            "light"
        ][1]
        <= 0.05
    )


def test_unsolvable_targets_fail_loudly() -> None:
    with pytest.raises(SystemExit, match="unsolvable"):
        profiles.Curator({"brand.hue": 10, "target.link": 30.0}).run()


def test_seed_of_falls_back_to_the_irs_stated_parameters(store: Path) -> None:
    folder = seeded(store, "p", {"brand.hue": 77})
    profiles.curate_profile(folder)
    (folder / "seed.json").rename(folder / "seed.bak")
    assert profiles.seed_of(folder) == {"brand.hue": 77}
    empty = store / "empty"
    empty.mkdir()
    with pytest.raises(SystemExit, match="no seed.json"):
        profiles.seed_of(empty)


# ── Build ───────────────────────────────────────────────────────────────────
@pytest.fixture
def built(store: Path) -> Path:
    folder = seeded(
        store,
        "brand",
        {"brand.hue": 295, "font.stylesheet": "https://fonts.example/css"},
    )
    profiles.curate_profile(folder)
    return profiles.build_profile(folder)


def test_build_writes_one_resolver_document_that_validates(built: Path) -> None:
    doc = json.loads(built.read_text(encoding="utf-8"))
    jsonschema.Draft7Validator(SCHEMA).validate(doc)
    assert doc["resolutionOrder"] == [{"$ref": "#/modifiers/mode"}]
    assert set(doc["modifiers"]["mode"]["contexts"]) == {"light", "dark"}
    assert doc["modifiers"]["mode"]["$extensions"][profiles.EXT] == {
        "profile": "brand",
        "fontStylesheet": "https://fonts.example/css",
    }


def test_the_schema_rejects_a_broken_token(built: Path) -> None:
    doc = json.loads(built.read_text(encoding="utf-8"))
    doc["modifiers"]["mode"]["contexts"]["light"][0]["color"]["link"]["$value"] = {
        "colorSpace": "nope"
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft7Validator(SCHEMA).validate(doc)


def test_build_aliases_unedited_surfaces_and_the_reader_resolves_them(
    built: Path,
) -> None:
    doc = json.loads(built.read_text(encoding="utf-8"))
    light = doc["modifiers"]["mode"]["contexts"]["light"][0]
    assert light["color"]["border"]["focused"]["$value"] == "{color.border.selected}"
    assert light["color"]["text"]["selected"]["$value"] == "{color.text.default}"
    assert (
        light["surface"]["mermaid"]["primaryColor"]["$value"]
        == "{color.background.brand.subtlest}"
    )
    assert light["color"]["border"]["default"]["$value"]["alpha"] == 0.1412
    ir = ir_of(built.parent)
    for m in profiles.MODES:
        flat = profile_resolver.read_tokens(doc, m)
        assert flat["color.text"] == ir["color.text"][m]
        assert (
            flat["surface.mermaid.primaryColor"]
            == ir["color.background.brand.subtlest"][m]
        )
        assert flat["surface.deckgl.background"] == ir["color.surface"][m]
        assert flat["font.family.mono"] == profiles.SYSTEM_MONO


def test_a_stated_alias_is_built_as_its_value(store: Path) -> None:
    folder = seeded(store, "p", {"brand.hue": 10})
    profiles.curate_profile(folder)
    ir = ir_of(folder)
    ir["surface.mermaid.primaryColor"]["light"] = "#abcdef"
    ir["color.link"]["dark"] = "#abcdef80"
    (folder / "ir.json").write_text(json.dumps(ir), encoding="utf-8")
    doc = json.loads(profiles.build_profile(folder).read_text(encoding="utf-8"))
    flat = profile_resolver.read_tokens(doc, "light")
    assert flat["surface.mermaid.primaryColor"] == "#abcdef"
    assert profile_resolver.read_tokens(doc, "dark")["color.link"] == "#abcdef80"


@pytest.mark.parametrize(
    ("edit", "message"),
    [
        (lambda ir: ir["color.text"].pop("dark"), "has no dark value"),
        (
            lambda ir: ir.__setitem__("size.gap", {"light": 1, "dark": 1}),
            "outside the color",
        ),
    ],
)
def test_build_rejects_an_incomplete_ir(store: Path, edit: Any, message: str) -> None:
    folder = seeded(store, "p", {"brand.hue": 10})
    profiles.curate_profile(folder)
    ir = ir_of(folder)
    edit(ir)
    (folder / "ir.json").write_text(json.dumps(ir), encoding="utf-8")
    with pytest.raises(SystemExit, match=message):
        profiles.build_profile(folder)


def test_build_needs_an_ir(store: Path) -> None:
    with pytest.raises(SystemExit, match="run curate first"):
        profiles.build_profile(seeded(store, "p", {"brand.hue": 1}))


def test_lineage_and_generate() -> None:
    result = profiles.generate({"brand.hue": 120}, {"name": "live"})
    first, second = result["lineage"]["sankeys"]
    assert {
        "source": "param:brand.hue",
        "target": "color.background.brand.bold",
    } in first["links"]
    assert {n["id"] for n in second["nodes"]} >= {f"surface.{s}" for s in SURFACES}
    assert result["tokens"]["name"] == "live"
    assert "brand.lightness" in result["resolved"]


# ── CLI ─────────────────────────────────────────────────────────────────────
def run(*argv: str) -> None:
    profiles.main(list(argv))


def test_cli_end_to_end(
    store: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: Any
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    caplog.set_level("INFO")
    run("init", "hue", "--hue", "200")
    run("init", "acc", "--accent", "#5c4295")
    run("init", "ex", "--example", "osakanights")
    assert json.loads((store / "acc/seed.json").read_text())["brand.lightness"] == 0.45
    run("all")
    run("build", "hue")
    run("lineage", "hue")
    assert (tmp_path / "tmp/design-profiles/hue/lineage.json").is_file()
    run("set-default", "ex")
    assert (store / ".default-profile").read_text() == "ex\n"
    caplog.clear()
    run("status")
    text = caplog.text
    assert "default  ex" in text and "osakanights" in text and "0 defect" in text
    ir_path = store / "hue/ir.json"
    ir_path.write_text(ir_path.read_text())
    tokens = store / "hue/design-tokens.json"
    tokens.touch()
    caplog.clear()
    run("status", "hue")
    assert "profile  hue" in caplog.text and "profile  ex" not in caplog.text


def test_cli_errors(
    store: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Any
) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit, match="no profiles under"):
        run("curate")
    run("init", "p", "--hue", "1")
    with pytest.raises(SystemExit, match="exists"):
        run("init", "p", "--hue", "1")
    run("init", "p", "--hue", "2", "--force")
    with pytest.raises(SystemExit, match="unknown example"):
        run("init", "q", "--example", "nope")
    with pytest.raises(SystemExit, match="needs --hue"):
        run("init", "q")
    with pytest.raises(SystemExit, match="run build first"):
        run("set-default", "p")
    with pytest.raises(SystemExit, match="run curate first"):
        run("lineage", "p")
    run()
    assert "usage: profiles.py" in capsys.readouterr().out


def test_cli_user_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    run("init", "u", "--hue", "5", "--user")
    assert (tmp_path / ".design-profiles/u/seed.json").is_file()


def test_examples_are_valid_seeds() -> None:
    found = profiles.examples()
    assert set(found) == {
        "fernline",
        "freshgreens",
        "gandalf",
        "locomotif",
        "osakanights",
        "v2ai",
    }
    for path in found.values():
        profiles.resolve_params(json.loads(path.read_text(encoding="utf-8")))


if __name__ == "__main__":  # pragma: no cover
    script_dir = str(Path(__file__).parent.resolve())
    sys.exit(
        pytest.main(
            [__file__, "-v", "--rootdir", script_dir, "-o", "addopts=", *sys.argv[1:]]
        )
    )
