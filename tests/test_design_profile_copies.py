"""The design-profiles resolver and its consumer copies stay in step.

DT-TOOL-1 has every consumer carry its own copy of the profile resolver and DTCG
reader, never an import of another skill's code. Copies drift, so this suite is
the one place that reads across skills and holds them together:

* richdocs' ``profile_resolver.py`` is byte-identical to the canonical one;
* mermaidjs-diagrams' TypeScript port reads a profile exactly as Python does;
* the test-fixture profiles are what design-profiles builds today;
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
sys.path.insert(0, str(CANONICAL))

import profile_resolver  # noqa: E402
import profiles  # noqa: E402

PYTHON_COPIES = [REPO / "skills/richdocs/scripts/profile_resolver.py"]
FIXTURES = [
    REPO / "skills/richdocs/scripts/testdata/osakanights/design-tokens.json",
    REPO / "skills/mermaidjs-diagrams/scripts/testdata/osakanights/design-tokens.json",
    REPO / "skills/richdocs/vendor/mermaidjs-diagrams/scripts/testdata/osakanights/design-tokens.json",
]
TS_PORT = REPO / "skills/mermaidjs-diagrams/scripts/design_profile.ts"


@pytest.mark.parametrize("copy", PYTHON_COPIES, ids=lambda p: str(p.relative_to(REPO)))
def test_python_copies_are_byte_identical(copy: Path) -> None:
    assert copy.read_bytes() == (CANONICAL / "profile_resolver.py").read_bytes(), (
        f"{copy.relative_to(REPO)} drifted from the design-profiles resolver; copy it over again"
    )


@pytest.fixture(scope="module")
def built(tmp_path_factory: pytest.TempPathFactory) -> Path:
    folder = tmp_path_factory.mktemp("store") / "osakanights"
    folder.mkdir()
    shutil.copy(CANONICAL.parent / "resources/examples/osakanights/seed.json", folder / "seed.json")
    profiles.curate_profile(folder)
    return profiles.build_profile(folder)


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda p: str(p.relative_to(REPO)))
def test_fixtures_are_what_design_profiles_builds_today(fixture: Path, built: Path) -> None:
    assert fixture.read_text(encoding="utf-8") == built.read_text(encoding="utf-8"), (
        f"rebuild the osakanights example and copy design-tokens.json over {fixture.relative_to(REPO)}"
    )


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
        assert profiles.hex_of(lch) == brand["themes"][mode]["accent"].lower()
