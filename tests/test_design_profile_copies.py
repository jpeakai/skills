"""The design-profiles resolver and its consumer copies stay in step.

DT-TOOL-1 has every consumer carry its own copy of the profile resolver and DTCG
reader, never an import of another skill's code. Copies drift, so this suite is
the one place that reads across skills and holds them together:

* richdocs' Python compatibility reader agrees with the canonical JavaScript reader;
* mermaidjs-diagrams' TypeScript reader agrees with both;
* legacy fixture profiles still read consistently across runtimes;
* the example seeds still state each richdocs brand's exact accents.

    uv run pytest tests/test_design_profile_copies.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
CANONICAL = REPO / "skills/design-profiles/scripts"
sys.path.insert(0, str(REPO / "skills/richdocs/scripts"))

import profile_resolver  # noqa: E402

FIXTURES = [
    REPO / "skills/richdocs/scripts/testdata/osakanights/design-tokens.json",
    REPO / "skills/mermaidjs-diagrams/scripts/testdata/osakanights/design-tokens.json",
    REPO / "skills/richdocs/vendor/mermaidjs-diagrams/scripts/testdata/osakanights/design-tokens.json",
]
TS_PORT = REPO / "skills/mermaidjs-diagrams/scripts/design_profile.ts"


def node_json(source: str, *args: str) -> object:
    run = subprocess.run(
        ["node", "--input-type=module", "-e", source, *args],
        cwd=CANONICAL, capture_output=True, text=True, check=True,
    )
    return json.loads(run.stdout)


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_python_compatibility_reader_matches_javascript(mode: str, built: Path) -> None:
    expected = node_json(
        'import {readFileSync} from "node:fs"; '
        'import {read_tokens} from "./profile_resolver.mjs"; '
        'console.log(JSON.stringify(read_tokens(JSON.parse(readFileSync(process.argv[1])), process.argv[2])));',
        str(built), mode,
    )
    assert profile_resolver.read_tokens(json.loads(built.read_text()), mode) == expected


@pytest.fixture(scope="module")
def built(tmp_path_factory: pytest.TempPathFactory) -> Path:
    folder = tmp_path_factory.mktemp("store") / "osakanights"
    folder.mkdir()
    shutil.copy(CANONICAL.parent / "resources/examples/osakanights/seed.json", folder / "seed.json")
    subprocess.run(
        ["node", str(CANONICAL / "profiles.mjs"), "all", "osakanights", "--store", str(folder.parent)],
        capture_output=True, text=True, check=True,
    )
    return folder / "design-tokens.json"


@pytest.mark.parametrize("consumer", [
    "skills/mermaidjs-diagrams",
    "skills/richdocs",
    "skills/richdocs/vendor/mermaidjs-diagrams",
])
def test_prebuilt_theme_matches_producer(consumer: str, built: Path) -> None:
    theme = REPO / consumer / "resources/themes/osakanights"
    tokens = theme / ("profile/design-tokens.json" if consumer == "skills/richdocs" else "design-tokens.json")
    assert tokens.read_bytes() == built.read_bytes()
    assert (theme / "themes.css").read_bytes() == built.with_name("theme.css").read_bytes()


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda p: str(p.relative_to(REPO)))
def test_legacy_fixtures_still_read_consistently(fixture: Path, built: Path) -> None:
    doc = json.loads(fixture.read_text(encoding="utf-8"))
    for mode in ("light", "dark"):
        expected = node_json(
            'import {readFileSync} from "node:fs"; '
            'import {read_tokens} from "./profile_resolver.mjs"; '
            'console.log(JSON.stringify(read_tokens(JSON.parse(readFileSync(process.argv[1])), process.argv[2])));',
            str(fixture), mode,
        )
        assert profile_resolver.read_tokens(doc, mode) == expected
        assert profile_resolver.read_tokens(json.loads(built.read_text()), mode)["dimension.radius"] == {"value": 12, "unit": "px"}


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_the_typescript_port_reads_what_python_reads(mode: str, built: Path, tmp_path: Path) -> None:
    store = tmp_path / ".design-profiles/osakanights"
    store.mkdir(parents=True)
    shutil.copy(built, store / "design-tokens.json")
    run = subprocess.run(
        ["bun", "run", str(TS_PORT), "mermaid-config", "--design-profile", "osakanights", "--mode", mode],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    variables = json.loads(run.stdout)["themeVariables"]
    flat = profile_resolver.read_tokens(json.loads(built.read_text(encoding="utf-8")), mode)
    expected = profile_resolver.group(flat, "surface.mermaid")
    assert {k: v for k, v in variables.items() if k not in ("darkMode", "fontFamily")} == expected
    assert variables["fontFamily"] == flat["font.family.body"]


@pytest.mark.parametrize("seed", sorted((CANONICAL.parent / "resources/examples").glob("*/seed.json")),
                         ids=lambda p: p.parent.name)
def test_example_seeds_state_each_brands_exact_accents(seed: Path) -> None:
    brand = json.loads((REPO / "skills/richdocs/resources/themes" / seed.parent.name / "design-tokens.json")
                       .read_text(encoding="utf-8"))
    stated = json.loads(seed.read_text(encoding="utf-8"))
    for mode, prefix in (("light", "brand"), ("dark", "brand.dark" if "brand.dark.hue" in stated else "brand")):
        lch = (stated[f"{prefix}.lightness"], stated[f"{prefix}.chroma"], stated[f"{prefix}.hue"])
        actual = node_json(
            'import {hex_of} from "./profiles.mjs"; console.log(JSON.stringify(hex_of(JSON.parse(process.argv[1]))));',
            json.dumps(lch),
        )
        assert actual == brand["themes"][mode]["accent"].lower()
