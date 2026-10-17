#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Curate design profiles: seed.json -> ir.json -> design-tokens.json. Stdlib only.

    seed.json            optional: a few parameters and one brand hue      what the user states
    ir.json              every role and every surface, light and dark        what curation imputes
    design-tokens.json   one DTCG 2025.10 resolver document, both modes      the only runtime artifact

Curation imputes what is absent, never overwrites a stated value, and scores every
text pairing against WCAG AA. Build is a pure IR -> DTCG transform. Profiles live in
a shared store, `.design-profiles/<name>/`, that every consumer skill reads.

Every default parameter carries its source: a decision ID (DT-*) or a curation stage.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
from collections.abc import Callable
from pathlib import Path
from typing import Any

import profile_resolver as resolver

log = logging.getLogger(__name__)

# ── Configuration ───────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
EXAMPLES_DIR = SKILL_DIR / "resources" / "examples"
LINEAGE_DIR = Path("tmp/design-profiles")
EXT = resolver.EXT
MODES = ("light", "dark")
STEP = 0.005
SCHEMA = "https://www.designtokens.org/schemas/2025.10/resolver.json"

SYSTEM_SANS = "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"
SYSTEM_MONO = "ui-monospace, 'SF Mono', Menlo, Consolas, monospace"

# Key -> (value, source). A seed overrides any key; everything else is imputed.
DEFAULTS: dict[str, tuple[Any, str]] = {
    "brand.hue": (None, "DT-ACCENT-1 (required)"),
    "brand.chroma": (
        "cusp",
        "CURATION stage 3 (hue-only: the hue's most colourful in-gamut point)",
    ),
    "brand.lightness": (
        "cusp",
        "CURATION stage 3 (hue-only; a stated value pins the light accent)",
    ),
    "brand.dark.hue": (None, "DT-ACCENT-1 (defaults to brand.hue)"),
    "brand.dark.chroma": (None, "DT-ACCENT-1 (defaults to brand.chroma)"),
    "brand.dark.lightness": (
        None,
        "DT-ACCENT-1 (stated: pins the dark accent verbatim; else solved)",
    ),
    "L-dark-bg": (0.15, "DT-REF-1"),
    "L-light-bg": (0.97, "DT-REF-1"),
    "offset.surface.sunken": (-0.05, "DT-REF-1"),
    "offset.surface.raised": (0.05, "DT-REF-1"),
    "offset.text": (0.90, "DT-REF-1"),
    "offset.text.subtle": (0.65, "DT-REF-1"),
    "target.text.subtlest": (
        4.5,
        "WCAG 2.2 SC 1.4.3 (AA: the lowest text tier still reads)",
    ),
    "alpha.border": (0.14, "DT-BORDER-1"),
    "offset.border.bold": (0.35, "DT-BORDER-1 (search start; solved to 3:1)"),
    "target.graphic": (3.0, "WCAG 2.2 SC 1.4.11"),
    "target.text.inverse": (
        7.0,
        "DT-CONTRAST-1 (maximise: WCAG 2.2 SC 1.4.6 AAA on the brand fill)",
    ),
    "target.link": (4.5, "WCAG 2.2 SC 1.4.3 (AA text)"),
    "alpha.brand.subtlest": (
        0.16,
        "CURATION stage 3 (the fill at 16% over the surface)",
    ),
    "secondary.hue": (None, "DT-ACCENT-1 (defaults to brand.hue)"),
    "secondary.chromaRatio": (0.444, "DT-ACCENT-1 (M3 chroma 16/36)"),
    "offset.background.selected": (
        0.07,
        "DT-ACCENT-1 (M3 secondaryContainer sits 0.068 L from its surface)",
    ),
    "walk.slots": (12, "DT-WALK-1"),
    "walk.angle": (137.5, "DT-WALK-1"),
    "walk.lightness": ("brand", "DT-WALK-2 (each mode's accent lightness)"),
    "walk.chromaCeiling": ("floor", "DT-WALK-2"),
    "status.hue.danger": (
        25.0,
        "CURATION stage 5 (Primer danger.fg 24.6, Tailwind red-600 27.3, M3 error 28.7)",
    ),
    "status.hue.warning": (
        75.0,
        "CURATION stage 5 (Primer attention.fg 75.0, a text role)",
    ),
    "status.hue.success": (
        148.0,
        "CURATION stage 5 (Primer success.fg 148.0, Tailwind green-600 149.2)",
    ),
    "status.chromaCap": (0.18, "CURATION stage 5 (M3 error chroma 0.178)"),
    "target.status": (4.5, "WCAG 2.2 SC 1.4.3 (AA text)"),
    "mode.default": ("light", "DT-DTCG-1 (modifiers.mode.default)"),
    "font.display": (SYSTEM_SANS, "MIGRATION M4 (system stack)"),
    "font.body": (SYSTEM_SANS, "MIGRATION M4 (system stack)"),
    "font.mono": (SYSTEM_MONO, "MIGRATION M4 (system stack)"),
    "font.stylesheet": (None, "MIGRATION M4 (optional web-font stylesheet URL)"),
}

# ── Colour maths: OKLCH <-> sRGB (Ottosson), gamut, WCAG contrast, alpha ──────
_LMS_FROM_LAB = (
    (1.0, 0.3963377774, 0.2158037573),
    (1.0, -0.1055613458, -0.0638541728),
    (1.0, -0.0894841775, -1.2914855480),
)
_RGB_FROM_LMS = (
    (4.0767416621, -3.3077115913, 0.2309699292),
    (-1.2684380046, 2.6097574011, -0.3413193965),
    (-0.0041960863, -0.7034186147, 1.7076147010),
)
_LMS_FROM_RGB = (
    (0.4122214708, 0.5363325363, 0.0514459929),
    (0.2119034982, 0.6806995451, 0.1073969566),
    (0.0883024619, 0.2817188376, 0.6299787005),
)
_LAB_FROM_LMS = (
    (0.2104542553, 0.7936177850, -0.0040720468),
    (1.9779984951, -2.4285922050, 0.4505937099),
    (0.0259040371, 0.7827717662, -0.8086757660),
)

LCH = tuple[float, float, float]
Vec = tuple[float, float, float]
Matrix = tuple[Vec, Vec, Vec]


def _mul(m: Matrix, v: Vec) -> Vec:
    return (
        m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
        m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
        m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2],
    )


def _to_lin(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else float(((c + 0.055) / 1.055) ** 2.4)


def _to_srgb(c: float) -> float:
    c = min(max(c, 0.0), 1.0)
    return c * 12.92 if c <= 0.0031308 else float(1.055 * c ** (1 / 2.4) - 0.055)


def _lin_rgb(lch: LCH) -> Vec:
    lightness, chroma, hue = lch
    rad = math.radians(hue)
    lms = _mul(
        _LMS_FROM_LAB, (lightness, chroma * math.cos(rad), chroma * math.sin(rad))
    )
    return _mul(_RGB_FROM_LMS, (lms[0] ** 3, lms[1] ** 3, lms[2] ** 3))


def max_chroma(lightness: float, hue: float) -> float:
    """The most chroma sRGB can show at this lightness and hue (bisection)."""
    if lightness <= 0.0 or lightness >= 1.0:
        return 0.0
    lo, hi = 0.0, 0.4
    for _ in range(26):
        mid = (lo + hi) / 2
        ok = all(-1e-4 <= c <= 1 + 1e-4 for c in _lin_rgb((lightness, mid, hue)))
        lo, hi = (mid, hi) if ok else (lo, mid)
    return lo


def hex_of(lch: LCH) -> str:
    return "#" + "".join(f"{round(_to_srgb(c) * 255):02x}" for c in _lin_rgb(lch))


def oklch_of(hexs: str) -> LCH:
    h = hexs.lstrip("#")
    lin = (
        _to_lin(int(h[0:2], 16) / 255),
        _to_lin(int(h[2:4], 16) / 255),
        _to_lin(int(h[4:6], 16) / 255),
    )
    lms = _mul(_LMS_FROM_RGB, lin)
    lab = _mul(_LAB_FROM_LMS, tuple(math.copysign(abs(x) ** (1 / 3), x) for x in lms))  # type: ignore[arg-type]
    return (
        lab[0],
        math.hypot(lab[1], lab[2]),
        math.degrees(math.atan2(lab[2], lab[1])) % 360,
    )


def _rgb8(hexs: str) -> tuple[tuple[int, int, int], float]:
    h = hexs.lstrip("#")
    alpha = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)), alpha


def composite(fg: str, bg: str) -> str:
    """`fg` (which may carry alpha) flattened onto the opaque `bg`."""
    (f, a), (b, _) = _rgb8(fg), _rgb8(bg)
    return "#" + "".join(f"{round(x * a + y * (1 - a)):02x}" for x, y in zip(f, b))


def contrast(a: str, b: str) -> float:
    def lum(hexs: str) -> float:
        (r, g, bl), _ = _rgb8(hexs)
        return (
            0.2126 * _to_lin(r / 255)
            + 0.7152 * _to_lin(g / 255)
            + 0.0722 * _to_lin(bl / 255)
        )

    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def best_text(fill: str) -> str:
    """Black or white, whichever reads better on `fill`."""
    return (
        "#000000"
        if contrast(fill, "#000000") >= contrast(fill, "#ffffff")
        else "#ffffff"
    )


def rgba(hexs: str) -> list[int]:
    (r, g, b), alpha = _rgb8(hexs)
    return [r, g, b, round(alpha * 255)]


def grey(lightness: float) -> LCH:
    return (min(max(lightness, 0.0), 1.0), 0.0, 0.0)


def exact_oklch(hexs: str) -> LCH:
    """A hex as OKLCH at the fewest decimals that still round-trip to exactly that hex."""
    exact = oklch_of(hexs)
    for places in range(3, 9):
        lch = (
            round(exact[0], places),
            round(exact[1], places),
            round(exact[2], places),
        )
        if hex_of(lch) == hexs.lower():
            return lch
    raise SystemExit(f"error: {hexs} does not round-trip through OKLCH")


# ── Seeds ───────────────────────────────────────────────────────────────────
def resolve_params(
    seed: dict[str, Any], defaults: dict[str, tuple[Any, str]] | None = None
) -> dict[str, tuple[Any, str]]:
    """Merge a seed over the defaults. Each value is tagged 'stated' or 'default (<source>)'."""
    defaults = DEFAULTS if defaults is None else defaults
    unknown = set(seed) - set(defaults)
    if unknown:
        raise SystemExit(f"error: unknown seed parameter(s): {sorted(unknown)}")
    if "brand.hue" not in seed:
        raise SystemExit("error: a seed must state brand.hue")
    if seed.get("mode.default", "light") not in MODES:
        raise SystemExit(f"error: mode.default must be one of {MODES}")
    return {
        k: ((seed[k], "stated") if k in seed else (v, f"default ({src})"))
        for k, (v, src) in defaults.items()
    }


# ── Curation: seed -> IR ────────────────────────────────────────────────────
class Curator:
    """Runs CURATION stages 1 to 6 for one seed, keeping every stated IR value (DT-PROV-1)."""

    def __init__(
        self,
        seed: dict[str, Any],
        stated: dict[str, dict[str, Any]] | None = None,
        defaults: dict[str, tuple[Any, str]] | None = None,
    ) -> None:
        self.p = resolve_params(seed, defaults)
        # Values the IR states (hand edits), per role per mode. They are final: put() keeps
        # them in place of what the rule derives, and every later stage reads them.
        self.stated = stated or {}
        # What each keyword or implied default resolved to.
        self.resolved: dict[str, Any] = {}
        self.ir: dict[str, dict[str, Any]] = {}

    def v(self, key: str) -> Any:
        return self.p[key][0]

    def cite(self, *keys: str) -> list[str]:
        return [f"{k}={self.p[k][0]} [{self.p[k][1]}]" for k in keys]

    def put(
        self,
        role: str,
        values: dict[str, Any],
        rule: str,
        inputs: list[str],
        lch: dict[str, LCH] | None = None,
        alias: str | None = None,
        roles: list[str] | None = None,
    ) -> None:
        # `derived` is what the rule produced. A value equal to it was not edited and is
        # rederived on the next run; a value that differs is stated, and kept.
        pinned = self.stated.get(role, {})
        ext: dict[str, Any] = {
            "origin": {m: "stated" if m in pinned else "imputed" for m in values},
            "derived": dict(values),
            "rule": rule,
            "inputs": inputs,
        }
        if roles or alias:
            ext["roles"] = roles or [alias]
        if lch:
            ext["oklch"] = {m: [round(x, 4) for x in lch[m]] for m in lch}
            for m, value in pinned.items():
                if isinstance(value, str) and len(value) == 7:
                    ext["oklch"][m] = [round(x, 4) for x in oklch_of(value)]
        if alias:
            ext["alias"] = alias
        self.ir[role] = {**values, **pinned, "$extensions": {EXT: ext}}

    def val(self, role: str, mode: str) -> Any:
        return self.ir[role][mode]

    def same(self, key: str, role: str) -> None:
        """A surface key that is exactly one role: an alias in the DTCG."""
        self.put(
            key,
            {m: self.val(role, m) for m in MODES},
            f"alias of {role}",
            [],
            alias=role,
        )

    def over(self, key: str, fg: str, bg: str) -> None:
        """A surface key that is `fg` flattened onto `bg` (DT-BORDER-1: projections flatten alpha)."""
        self.put(
            key,
            {m: composite(self.val(fg, m), self.val(bg, m)) for m in MODES},
            f"{fg} flattened onto {bg}",
            [],
            roles=[fg, bg],
        )

    def text_on(self, key: str, fill: str) -> None:
        self.put(
            key,
            {m: best_text(self.val(fill, m)) for m in MODES},
            f"black or white, whichever reads better on {fill}",
            [],
            roles=[fill],
        )

    def grounds(self, mode: str) -> list[str]:
        return [
            self.val(r, mode)
            for r in ("color.surface.sunken", "color.surface", "color.surface.raised")
        ]

    def sign(self, mode: str) -> float:
        return 1.0 if mode == "dark" else -1.0

    def bg(self, mode: str) -> float:
        return float(self.v("L-dark-bg") if mode == "dark" else self.v("L-light-bg"))

    def solve(
        self,
        hue: float,
        cmax: float,
        anchor: float,
        test: Callable[[str], bool],
        what: str,
    ) -> LCH:
        """The lightness nearest `anchor` whose colour passes `test`, chroma capped at `cmax`."""
        for step in range(int(1 / STEP) + 1):
            for lightness in sorted({anchor + step * STEP, anchor - step * STEP}):
                if 0.0 <= lightness <= 1.0:
                    lch = (lightness, min(max_chroma(lightness, hue), cmax), hue)
                    if test(hex_of(lch)):
                        return lch
        raise SystemExit(f"error: unsolvable: {what} at hue {hue:.1f}")

    def on_all_grounds(self, mode: str, target: float) -> Callable[[str], bool]:
        return lambda colour: (
            min(contrast(colour, g) for g in self.grounds(mode)) >= target
        )

    # ── stage 1 and 2: neutrals and borders (DT-REF-1, DT-BORDER-1) ──────────
    def neutrals(self) -> None:
        for role, key, absolute in (
            ("color.surface.sunken", "offset.surface.sunken", True),
            ("color.surface", None, True),
            ("color.surface.raised", "offset.surface.raised", True),
            ("color.text", "offset.text", False),
            ("color.text.subtle", "offset.text.subtle", False),
        ):
            lch = {}
            for m in MODES:
                off = float(self.v(key)) if key else 0.0
                lch[m] = grey(self.bg(m) + (off if absolute else self.sign(m) * off))
            rule = (
                "mode reference"
                if key is None
                else (
                    "reference + absolute offset"
                    if absolute
                    else "reference + offset toward text"
                )
            )
            self.put(
                role,
                {m: hex_of(lch[m]) for m in MODES},
                rule,
                self.cite("L-light-bg", "L-dark-bg", *([key] if key else [])),
                lch,
            )

        # An opaque grey solved to the lightness nearest the offset that reaches 3:1 against
        # every ground. The offset is where the search starts, not the answer.
        lch = {}
        for m in MODES:
            anchor = self.bg(m) + self.sign(m) * float(self.v("offset.border.bold"))
            passes = self.on_all_grounds(m, float(self.v("target.graphic")))
            lch[m] = next(
                grey(lt)
                for step in range(int(1 / STEP) + 1)
                for lt in sorted({anchor + step * STEP, anchor - step * STEP})
                if 0.0 <= lt <= 1.0 and passes(hex_of(grey(lt)))
            )
        self.put(
            "color.border.bold",
            {m: hex_of(lch[m]) for m in MODES},
            "grey nearest reference + offset toward text reaching the target on every ground",
            self.cite(
                "L-light-bg", "L-dark-bg", "offset.border.bold", "target.graphic"
            ),
            lch,
        )

        lch = {}
        for m in MODES:
            for step in range(1, int(1 / STEP)):
                cand = grey(self.bg(m) + self.sign(m) * step * STEP)
                if self.on_all_grounds(m, float(self.v("target.text.subtlest")))(
                    hex_of(cand)
                ):
                    lch[m] = cand
                    break
        self.put(
            "color.text.subtlest",
            {m: hex_of(lch[m]) for m in MODES},
            "nearest the ground reaching the target on every ground",
            self.cite("target.text.subtlest"),
            lch,
        )

        alpha = round(float(self.v("alpha.border")) * 255)
        self.put(
            "color.border",
            {m: f"{self.val('color.text', m)}{alpha:02x}" for m in MODES},
            "color.text at alpha",
            self.cite("alpha.border"),
            roles=["color.text"],
        )

    def fill_test(self, mode: str) -> Callable[[str], bool]:
        """A brand fill passes when inverse text reaches its target and it reaches 3:1 on every ground."""
        grounds = self.on_all_grounds(mode, float(self.v("target.graphic")))
        target = float(self.v("target.text.inverse"))
        return lambda col: contrast(col, best_text(col)) >= target and grounds(col)

    # ── stage 3: brand roles (DT-ACCENT-1, DT-WALK-2) ────────────────────────
    def brand(self) -> None:
        hue = float(self.v("brand.hue"))
        cusp_l = max(
            (i * STEP for i in range(1, int(1 / STEP))),
            key=lambda lt: max_chroma(lt, hue),
        )
        cusp_c = max_chroma(cusp_l, hue)
        chroma = (
            cusp_c
            if self.v("brand.chroma") == "cusp"
            else float(self.v("brand.chroma"))
        )
        brand_l = (
            cusp_l
            if self.v("brand.lightness") == "cusp"
            else float(self.v("brand.lightness"))
        )
        self.brand_hue, self.brand_c, self.brand_l = hue, chroma, brand_l
        # Light is the brand.* accent; dark defaults to it, and any brand.dark.* key overrides
        # one coordinate. A stated lightness pins that mode's fill verbatim (DT-CONTRAST-1).
        dark = {k: self.v(f"brand.dark.{k}") for k in ("hue", "chroma", "lightness")}
        self.accent: dict[str, LCH] = {
            "light": (brand_l, chroma, hue),
            "dark": (
                brand_l if dark["lightness"] is None else float(dark["lightness"]),
                chroma if dark["chroma"] is None else float(dark["chroma"]),
                hue if dark["hue"] is None else float(dark["hue"]),
            ),
        }
        pinned = {
            "light": self.v("brand.lightness") != "cusp",
            "dark": dark["lightness"] is not None,
        }
        self.resolved.update(
            {
                "brand.lightness": brand_l,
                "brand.chroma": chroma,
                **{
                    f"brand.dark.{k}": v
                    for k, v in zip(("lightness", "chroma", "hue"), self.accent["dark"])
                },
            }
        )
        stated_dark = [f"brand.dark.{k}" for k, v in dark.items() if v is not None]
        base = self.cite(
            "brand.hue", "brand.chroma", "brand.lightness", *stated_dark
        ) + [f"cusp L={cusp_l:.3f} C={cusp_c:.4f} (derived)"]

        lch = {}
        for m in MODES:
            anchor, c, h = self.accent[m]
            lch[m] = (
                self.accent[m]
                if pinned[m]
                else self.solve(
                    h,
                    c,
                    anchor,
                    self.fill_test(m),
                    "brand fill",
                )
            )
        solved = (
            "lightness solved: inverse text reaches target, and 3:1 on every ground"
        )
        rule = "; ".join(
            f"{m}: " + ("the stated accent, verbatim" if pinned[m] else solved)
            for m in MODES
        )
        self.put(
            "color.background.brand.bold",
            {m: hex_of(lch[m]) for m in MODES},
            rule,
            base + self.cite("target.text.inverse", "target.graphic"),
            lch,
        )
        self.text_on("color.text.inverse", "color.background.brand.bold")
        alpha = f"{round(float(self.v('alpha.brand.subtlest')) * 255):02x}"
        self.put(
            "color.background.brand.subtlest",
            {
                m: composite(
                    self.val("color.background.brand.bold", m) + alpha,
                    self.val("color.surface", m),
                )
                for m in MODES
            },
            "brand fill at alpha over color.surface",
            self.cite("alpha.brand.subtlest"),
            roles=["color.background.brand.bold", "color.surface"],
        )
        for role, key in (
            ("color.border.brand", "target.graphic"),
            ("color.link", "target.link"),
        ):
            lch = {
                m: self.solve(
                    self.accent[m][2],
                    self.accent[m][1],
                    self.accent[m][0],
                    self.on_all_grounds(m, float(self.v(key))),
                    role,
                )
                for m in MODES
            }
            self.put(
                role,
                {m: hex_of(lch[m]) for m in MODES},
                "the mode's accent, lightness solved to reach the target on every ground",
                base + self.cite(key),
                lch,
            )

    def secondary(self) -> None:
        hue = float(
            self.v("secondary.hue")
            if self.v("secondary.hue") is not None
            else self.brand_hue
        )
        chroma = self.brand_c * float(self.v("secondary.chromaRatio"))
        inputs = self.cite(
            "secondary.hue", "secondary.chromaRatio", "brand.hue", "brand.chroma"
        )
        for role, extra in (
            ("color.background.selected", 0.0),
            ("color.background.selected.hovered", STEP * 10),
        ):
            lch = {}
            for m in MODES:
                lightness = self.bg(m) + self.sign(m) * (
                    float(self.v("offset.background.selected")) + extra
                )
                lch[m] = (lightness, min(max_chroma(lightness, hue), chroma), hue)
            self.put(
                role,
                {m: hex_of(lch[m]) for m in MODES},
                "secondary at reduced chroma, offset from the ground toward text",
                inputs + self.cite("offset.background.selected"),
                lch,
            )
        lch = {
            m: self.solve(
                hue,
                self.brand_c,
                self.brand_l,
                self.on_all_grounds(m, float(self.v("target.graphic"))),
                "selected",
            )
            for m in MODES
        }
        self.put(
            "color.border.selected",
            {m: hex_of(lch[m]) for m in MODES},
            "secondary hue reaching 3:1 on every ground",
            inputs + self.cite("target.graphic"),
            lch,
        )
        self.same("color.border.focused", "color.border.selected")
        self.same("color.text.selected", "color.text")

    # ── stage 5: status colours ──────────────────────────────────────────────
    def status(self) -> None:
        for name in ("danger", "warning", "success"):
            key = f"status.hue.{name}"
            lch = {
                m: self.solve(
                    float(self.v(key)),
                    float(self.v("status.chromaCap")),
                    0.6,
                    self.on_all_grounds(m, float(self.v("target.status"))),
                    name,
                )
                for m in MODES
            }
            self.put(
                f"color.text.{name}",
                {m: hex_of(lch[m]) for m in MODES},
                "conventional hue reaching the target on every ground",
                self.cite(key, "status.chromaCap", "target.status"),
                lch,
            )

    # ── stage 4: categorical walk (DT-WALK-1, DT-WALK-2) ─────────────────────
    def walk(self) -> None:
        n, angle = int(self.v("walk.slots")), float(self.v("walk.angle"))
        hues = [(self.brand_hue + i * angle) % 360 for i in range(n)]
        ceiling = self.v("walk.chromaCeiling")
        follow = self.v("walk.lightness") == "brand"
        inputs = self.cite(
            "brand.hue",
            "walk.slots",
            "walk.angle",
            "walk.lightness",
            "walk.chromaCeiling",
            "target.graphic",
            *(["brand.chroma"] if ceiling == "seed" else []),
            *(["brand.lightness"] if follow else []),
            *(
                ["brand.dark.lightness"]
                if follow and self.v("brand.dark.lightness") is not None
                else []
            ),
        )
        per_mode: dict[str, list[LCH]] = {}
        for m in MODES:
            test = self.on_all_grounds(m, float(self.v("target.graphic")))
            anchor = self.accent[m][0] if follow else float(self.v("walk.lightness"))
            self.resolved.setdefault("walk.lightness", {})[m] = anchor
            if ceiling == "floor":
                first = [self.solve(h, 1.0, anchor, test, "walk") for h in hues]
                floor = min(max_chroma(lt, h) for lt, _c, h in first)
                slots = [self.solve(h, floor, anchor, test, "walk") for h in hues]
                floor = min(max_chroma(lt, h) for lt, _c, h in slots)
                per_mode[m] = [(lt, floor, h) for lt, _c, h in slots]
            else:
                cap = self.brand_c if ceiling == "seed" else float(ceiling)
                per_mode[m] = [self.solve(h, cap, anchor, test, "walk") for h in hues]
        for i in range(n):
            lch = {m: per_mode[m][i] for m in MODES}
            self.put(
                f"color.chart.categorical.{i + 1}",
                {m: hex_of(lch[m]) for m in MODES},
                f"golden walk slot {i + 1}: hue +{i}x{angle} deg, lightness solved to 3:1, chroma ceiling",
                inputs,
                lch,
            )

    def ramps(self) -> None:
        """Ordered chart ramps: sequential, diverging and muted, both modes."""
        spans = {"light": (0.88, 0.42), "dark": (0.30, 0.82)}
        danger = float(self.v("status.hue.danger"))
        success = float(self.v("status.hue.success"))
        cap = float(self.v("status.chromaCap"))
        brand_keys = ("brand.hue", "brand.chroma")
        for name, hue, chroma, count, keys in (
            ("sequential", self.brand_hue, self.brand_c, 5, brand_keys),
            ("diverging.positive", self.brand_hue, self.brand_c, 3, brand_keys),
            (
                "diverging.negative",
                danger,
                cap,
                3,
                ("status.hue.danger", "status.chromaCap"),
            ),
            (
                "diverging.alt-positive",
                success,
                cap,
                3,
                ("status.hue.success", "status.chromaCap"),
            ),
        ):
            for i in range(count):
                lch = {}
                for m in MODES:
                    lo, hi = spans[m]
                    lightness = lo + (hi - lo) * (i / (count - 1))
                    lch[m] = (lightness, min(max_chroma(lightness, hue), chroma), hue)
                self.put(
                    f"color.chart.{name}.{i + 1}",
                    {m: hex_of(lch[m]) for m in MODES},
                    "evenly spaced lightness at a fixed hue, chroma capped",
                    self.cite(*keys),
                    lch,
                )
        for i in range(4):
            lch = {}
            for m in MODES:
                a = self.bg(m) + self.sign(m) * float(self.v("offset.border.bold"))
                b = self.bg(m) + self.sign(m) * float(self.v("offset.text.subtle"))
                lch[m] = grey(a + (b - a) * i / 3)
            self.put(
                f"color.chart.muted.{i + 1}",
                {m: hex_of(lch[m]) for m in MODES},
                "greys from border.bold to text.subtle",
                self.cite(
                    "L-light-bg",
                    "L-dark-bg",
                    "offset.border.bold",
                    "offset.text.subtle",
                ),
                lch,
            )

    def fonts(self) -> None:
        for name in ("display", "body", "mono"):
            key = f"font.{name}"
            self.put(
                f"font.family.{name}",
                {m: self.v(key) for m in MODES},
                "the seed's font stack",
                self.cite(key),
            )

    # ── stage 6: surface expansion (DT-BUILD-1) ──────────────────────────────
    def surfaces(self) -> None:
        """Bake every rendering surface into the IR, so no consumer computes one."""
        n = int(self.v("walk.slots"))
        slots = [f"color.chart.categorical.{i}" for i in range(1, n + 1)]

        # Chrome custom properties. CSS composites alpha itself, but every surface flattens
        # it so a consumer can drop a value anywhere (DT-BORDER-1).
        for key, role in (
            ("page", "color.surface"),
            ("sunken", "color.surface.sunken"),
            ("raised", "color.surface.raised"),
            ("text", "color.text"),
            ("text-subtle", "color.text.subtle"),
            ("text-subtlest", "color.text.subtlest"),
            ("accent", "color.background.brand.bold"),
            ("on-accent", "color.text.inverse"),
            ("accent-subtlest", "color.background.brand.subtlest"),
            ("link", "color.link"),
            ("border-bold", "color.border.bold"),
            ("focus", "color.border.focused"),
            ("selected", "color.background.selected"),
        ):
            self.same(f"surface.css.{key}", role)
        self.over("surface.css.border", "color.border", "color.surface")

        # Cytoscape paints to a canvas: selector -> style property, in Cytoscape's own names.
        for key, role in (
            ("node.background-color", "color.background.brand.subtlest"),
            ("node.border-color", "color.border.brand"),
            ("node.color", "color.text"),
            ("node-alt.background-color", "color.background.selected"),
            ("edge.line-color", "color.border.bold"),
            ("edge.color", "color.text.subtle"),
            ("edge.text-background-color", "color.surface"),
            ("compound.background-color", "color.surface.sunken"),
            ("selected.border-color", "color.border.selected"),
        ):
            self.same(f"surface.cytoscape.{key}", role)
        self.over(
            "surface.cytoscape.compound.border-color",
            "color.border",
            "color.surface.sunken",
        )

        # Plotly: layout colours in Plotly's names, the categorical colorway, and the ramps.
        for key, role in (
            ("paper_bgcolor", "color.surface.raised"),
            ("plot_bgcolor", "color.surface"),
            ("font_color", "color.text"),
            ("diverging.zero", "color.surface.sunken"),
        ):
            self.same(f"surface.plotly.{key}", role)
        self.over("surface.plotly.gridcolor", "color.border", "color.surface")
        for i, slot in enumerate(slots, 1):
            self.same(f"surface.plotly.colorway.{i}", slot)
        for ramp, count in (
            ("sequential", 5),
            ("muted", 4),
            ("diverging.positive", 3),
            ("diverging.negative", 3),
            ("diverging.alt-positive", 3),
        ):
            for i in range(1, count + 1):
                self.same(f"surface.plotly.{ramp}.{i}", f"color.chart.{ramp}.{i}")

        # deck.gl takes RGBA arrays.
        for key, role in (
            ("background", "color.surface"),
            ("ink", "color.text.subtle"),
            ("text", "color.text"),
            ("warn", "color.text.warning"),
        ):
            self.put(
                f"surface.deckgl.{key}",
                {m: rgba(self.val(role, m)) for m in MODES},
                f"{role} as RGBA",
                [],
                roles=[role],
            )

        # draw.io: container, edge, and one stencil style per shape class. A class takes the
        # next categorical slot, for separation only (DT-CAT-1).
        for key, role in (
            ("container.fillColor", "color.surface.sunken"),
            ("container.fontColor", "color.text"),
            ("edge.strokeColor", "color.border.bold"),
            ("edge.fontColor", "color.text.subtle"),
        ):
            self.same(f"surface.drawio.{key}", role)
        self.over(
            "surface.drawio.container.strokeColor",
            "color.border",
            "color.surface.sunken",
        )
        for i, slot in enumerate(slots, 1):
            self.same(f"surface.drawio.stencil.{i}.fillColor", slot)
            self.same(f"surface.drawio.stencil.{i}.strokeColor", "color.border.bold")
            self.text_on(f"surface.drawio.stencil.{i}.fontColor", slot)

        self.mermaid(slots)

    def mermaid(self, slots: list[str]) -> None:
        """Mermaid `themeVariables`, every key explicit and opaque.

        Mermaid derives what it is not given by hue rotation from primaryColor
        (secondaryColor at h-120, tertiaryColor at h-160, cScale1 = secondary), so a key
        left out paints an off-brand colour. 8-digit hex is dropped for primaryColor.
        """
        prefix = "surface.mermaid"
        for key, role in (
            ("background", "color.surface"),
            ("mainBkg", "color.background.brand.subtlest"),
            ("primaryColor", "color.background.brand.subtlest"),
            ("primaryTextColor", "color.text"),
            ("primaryBorderColor", "color.border.brand"),
            ("secondaryColor", "color.background.selected"),
            ("secondaryTextColor", "color.text.selected"),
            ("secondaryBorderColor", "color.border.selected"),
            ("tertiaryColor", "color.surface.sunken"),
            ("tertiaryTextColor", "color.text"),
            ("tertiaryBorderColor", "color.border.bold"),
            ("nodeBorder", "color.border.brand"),
            ("nodeTextColor", "color.text"),
            ("textColor", "color.text"),
            ("titleColor", "color.text"),
            ("lineColor", "color.border.bold"),
            ("defaultLinkColor", "color.border.bold"),
            ("edgeLabelBackground", "color.surface"),
            ("clusterBkg", "color.surface.sunken"),
            ("clusterBorder", "color.border.bold"),
            ("noteBkgColor", "color.surface.raised"),
            ("noteTextColor", "color.text"),
            ("noteBorderColor", "color.border.bold"),
            ("actorBkg", "color.background.brand.subtlest"),
            ("actorBorder", "color.border.brand"),
            ("actorTextColor", "color.text"),
            ("actorLineColor", "color.border.bold"),
            ("signalColor", "color.text"),
            ("signalTextColor", "color.text"),
            ("labelBoxBkgColor", "color.surface.raised"),
            ("labelBoxBorderColor", "color.border.bold"),
            ("labelTextColor", "color.text"),
            ("loopTextColor", "color.text"),
            ("activationBkgColor", "color.background.selected"),
            ("activationBorderColor", "color.border.selected"),
            ("sequenceNumberColor", "color.text.inverse"),
            ("errorBkgColor", "color.surface.raised"),
            ("errorTextColor", "color.text.danger"),
            ("pieTitleTextColor", "color.text"),
            ("pieLegendTextColor", "color.text"),
            ("pieStrokeColor", "color.surface"),
            ("pieOuterStrokeColor", "color.border.bold"),
        ):
            self.same(f"{prefix}.{key}", role)
        for i, slot in enumerate(slots):
            self.same(f"{prefix}.cScale{i}", slot)
            self.text_on(f"{prefix}.cScaleLabel{i}", slot)
            self.same(f"{prefix}.pie{i + 1}", slot)
        for i, slot in enumerate(slots[:8]):
            self.same(f"{prefix}.git{i}", slot)
            self.text_on(f"{prefix}.gitBranchLabel{i}", slot)

        # One label colour serves every pie slice: whichever of black or white has the best
        # worst case across the slots.
        def worst(text: str, mode: str) -> float:
            return min(contrast(text, self.val(s, mode)) for s in slots)

        self.put(
            f"{prefix}.pieSectionTextColor",
            {m: max(("#000000", "#ffffff"), key=lambda t: worst(t, m)) for m in MODES},
            "black or white, whichever has the best worst case across the categorical slots",
            [],
            roles=slots,
        )

    def run(self) -> dict[str, Any]:
        self.neutrals()
        self.brand()
        self.secondary()
        self.status()
        self.walk()
        self.ramps()
        self.fonts()
        self.surfaces()
        params = {k: {"value": v, "source": s} for k, (v, s) in self.p.items()}
        return {"$extensions": {EXT: {"params": params}}, **self.ir}


def stated_values(ir: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """DT-PROV-1: every value in an existing IR that is not what curation derived for it.

    A value already marked stated stays stated. A value with no `derived` record was not
    written by curation, so it is stated too.
    """
    stated: dict[str, dict[str, Any]] = {}
    for role, node in ir.items():
        if role.startswith("$"):
            continue
        ext = node.get("$extensions", {}).get(EXT, {})
        origin, derived = ext.get("origin", {}), ext.get("derived", {})
        for m in MODES:
            if m not in node:
                continue
            if origin.get(m) == "stated" or node[m] != derived.get(m):
                stated.setdefault(role, {})[m] = node[m]
    return stated


AA_TEXT = 4.5  # WCAG 2.2 SC 1.4.3: the floor every text pairing is scored against

GROUNDS = ("color.surface.sunken", "color.surface", "color.surface.raised")
TEXT_CHECKS = [
    ("color.text", GROUNDS),
    ("color.text.subtle", GROUNDS),
    ("color.text.subtlest", GROUNDS),
    ("color.link", GROUNDS),
    ("color.text.danger", ("color.surface",)),
    ("color.text.warning", ("color.surface",)),
    ("color.text.success", ("color.surface",)),
    ("color.text.inverse", ("color.background.brand.bold",)),
    ("color.text", ("color.background.brand.subtlest",)),
    (
        "color.text.selected",
        ("color.background.selected", "color.background.selected.hovered"),
    ),
]


def score_contrast(ir: dict[str, Any]) -> list[dict[str, Any]]:
    """CURATION stage 7 / DT-CONTRAST-1: score every text-on-background pairing, per mode.

    A miss is a `defect` in the defaults only when both colours are imputed and neither was
    driven by a stated seed parameter (the brand hue aside, which every seed states). Any
    other miss is the user's `choice`: reported, never a failure.
    """

    def driven_by_statement(role: str, m: str) -> bool:
        ext = ir[role]["$extensions"][EXT]
        if ext["origin"].get(m) == "stated":
            return True
        return any(
            c.endswith("[stated]") and not c.startswith("brand.hue=")
            for c in ext["inputs"]
        )

    scores = []
    for text, grounds in TEXT_CHECKS:
        for ground in grounds:
            for m in MODES:
                ratio = contrast(ir[text][m], ir[ground][m])
                verdict = (
                    "pass"
                    if ratio >= AA_TEXT
                    else (
                        "choice"
                        if driven_by_statement(text, m)
                        or driven_by_statement(ground, m)
                        else "defect"
                    )
                )
                scores.append(
                    {
                        "text": text,
                        "on": ground,
                        "mode": m,
                        "ratio": round(ratio, 2),
                        "target": AA_TEXT,
                        "verdict": verdict,
                    }
                )
    return scores


def seed_of(folder: Path) -> dict[str, Any]:
    """The profile's seed.json, or the parameters its IR records as stated. A seed is optional."""
    seed_path = folder / "seed.json"
    if seed_path.is_file():
        seed: dict[str, Any] = json.loads(seed_path.read_text(encoding="utf-8"))
        return seed
    ir_path = folder / "ir.json"
    if ir_path.is_file():
        params = (
            json.loads(ir_path.read_text(encoding="utf-8"))
            .get("$extensions", {})
            .get(EXT, {})
            .get("params", {})
        )
        recorded = {
            k: p["value"] for k, p in params.items() if p.get("source") == "stated"
        }
        if recorded:
            return recorded
    raise SystemExit(
        f"error: {folder} has no seed.json and its ir.json records no stated parameters to curate from"
    )


def curate_profile(
    folder: Path, defaults: dict[str, tuple[Any, str]] | None = None
) -> list[str]:
    """Curate one profile in place: idempotent and additive (DT-BUILD-1, DT-PROV-1).

    Stated values are kept and feed every value derived after them; unedited values are
    rederived from the seed; absent roles are imputed; a role curation does not know is
    kept as stated. Returns the report lines.
    """
    seed = seed_of(folder)
    ir_path = folder / "ir.json"
    old = json.loads(ir_path.read_text(encoding="utf-8")) if ir_path.is_file() else {}
    stated = stated_values(old)
    ir = Curator(seed, stated, defaults).run()
    report = []
    unknown = [k for k in old if not k.startswith("$") and k not in ir]
    for role in unknown:
        ir[role] = old[role]
        report.append(f"held    {role} (not a curated role; kept as stated)")
    for role in (k for k in ir if not k.startswith("$") and k not in unknown):
        for m in MODES:
            before, after = old.get(role, {}).get(m), ir[role].get(m)
            if role in stated and m in stated[role]:
                derived = ir[role]["$extensions"][EXT].get("derived", {}).get(m)
                note = (
                    "" if derived in (None, after) else f" (rule would give {derived})"
                )
                report.append(f"held    {role} {m} {after} stated{note}")
            elif before is None:
                report.append(f"new     {role} {m} {after}")
            elif before != after:
                report.append(f"updated {role} {m} {before} -> {after}")
    scores = score_contrast(ir)
    ir["$extensions"][EXT]["contrast"] = scores
    for sc in scores:
        if sc["verdict"] != "pass":
            report.append(
                f"{sc['verdict']:7} {sc['text']} on {sc['on']} {sc['mode']} {sc['ratio']}:1 (AA {sc['target']}:1)"
            )
    folder.mkdir(parents=True, exist_ok=True)
    ir_path.write_text(json.dumps(ir, indent=2) + "\n", encoding="utf-8")
    return report


# ── Build: IR -> DTCG (DT-DTCG-1) ───────────────────────────────────────────
TYPES = {"color": "color", "surface": "color", "font": "fontFamily"}


def dtcg_colour(value: str | list[int], lch: list[float] | None) -> dict[str, Any]:
    hexs = value if isinstance(value, str) else "#" + "".join(f"{x:02x}" for x in value)
    (r, g, b), alpha = _rgb8(hexs)
    if lch is not None and alpha == 1.0:
        return {"colorSpace": "oklch", "components": lch, "hex": hexs[:7]}
    colour: dict[str, Any] = {
        "colorSpace": "srgb",
        "components": [round(r / 255, 4), round(g / 255, 4), round(b / 255, 4)],
        "hex": hexs[:7],
    }
    if alpha != 1.0:
        colour["alpha"] = round(alpha, 4)
    return colour


def font_families(stack: str) -> list[str]:
    """A CSS font stack as the DTCG fontFamily array of names."""
    return [f.strip().strip("'\"") for f in stack.split(",") if f.strip()]


def dtcg_path(role: str, roles: set[str]) -> list[str]:
    """DTCG forbids a group holding a value, so a role with children gets `.default`."""
    parts = role.split(".")
    return (
        parts + ["default"] if any(r.startswith(role + ".") for r in roles) else parts
    )


def build_tokens(ir: dict[str, Any], name: str) -> dict[str, Any]:
    """One DTCG 2025.10 resolver document holding both modes inline. No design knowledge."""
    roles = {k for k in ir if not k.startswith("$")}
    params = ir.get("$extensions", {}).get(EXT, {}).get("params", {})
    for role in sorted(roles):
        missing = [m for m in MODES if m not in ir[role]]
        if missing:
            raise SystemExit(
                f"error: {role} has no {'/'.join(missing)} value; a profile carries every permutation"
            )
        if role.split(".")[0] not in TYPES:
            raise SystemExit(
                f"error: {role} is outside the color, surface and font groups"
            )
    contexts: dict[str, list[dict[str, Any]]] = {}
    for m in MODES:
        tree: dict[str, Any] = {group: {"$type": kind} for group, kind in TYPES.items()}
        for role in sorted(roles):
            node = ir[role]
            ext = node.get("$extensions", {}).get(EXT, {})
            branch = tree
            *groups, leaf = dtcg_path(role, roles)
            for part in groups:
                branch = branch.setdefault(part, {})
            unedited = all(
                node[mode] == ext.get("derived", {}).get(mode) for mode in MODES
            )
            if "alias" in ext and unedited:
                branch[leaf] = {
                    "$value": "{" + ".".join(dtcg_path(ext["alias"], roles)) + "}"
                }
            elif TYPES[role.split(".")[0]] == "fontFamily":
                branch[leaf] = {"$value": font_families(node[m])}
            else:
                # A hand edit made since the last curate leaves the recorded OKLCH stale, so
                # it is used only when it still produces this exact hex.
                lch = ext.get("oklch", {}).get(m)
                if lch is not None and hex_of((lch[0], lch[1], lch[2])) != node[m]:
                    lch = None
                branch[leaf] = {"$value": dtcg_colour(node[m], lch)}
        contexts[m] = [{k: v for k, v in tree.items() if len(v) > 1}]
    meta: dict[str, Any] = {"profile": name}
    stylesheet = params.get("font.stylesheet", {}).get("value")
    if stylesheet:
        meta["fontStylesheet"] = stylesheet
    default = params.get("mode.default", {}).get("value", "light")
    return {
        "$schema": SCHEMA,
        "version": "2025.10",
        "name": name,
        "modifiers": {
            "mode": {
                "contexts": contexts,
                "default": default,
                "$extensions": {EXT: meta},
            }
        },
        "resolutionOrder": [{"$ref": "#/modifiers/mode"}],
    }


def build_profile(folder: Path) -> Path:
    ir_path = folder / "ir.json"
    if not ir_path.is_file():
        raise SystemExit(
            f"error: {ir_path} not found; run curate first, or hand-author an ir.json"
        )
    ir = json.loads(ir_path.read_text(encoding="utf-8"))
    out = folder / resolver.TOKENS_FILE
    out.write_text(
        json.dumps(build_tokens(ir, folder.name), indent=2) + "\n", encoding="utf-8"
    )
    return out


# ── Lineage ─────────────────────────────────────────────────────────────────
def build_lineage(ir: dict[str, Any]) -> dict[str, Any]:
    """Two Sankeys in richdocs' lineage.json contract: seed -> roles, and roles -> surfaces.

    Each link is one recorded dependency (value 1), so a node's thickness is how many
    values it feeds or reads. Role nodes are painted in their own colour per mode.
    """
    params = ir["$extensions"][EXT]["params"]
    keys = [k for k in ir if not k.startswith("$")]
    roles = [k for k in keys if not k.startswith("surface.")]
    neutral = {"light": "#8a8a8a", "dark": "#8a8a8a"}

    def colour(role: str) -> dict[str, str]:
        values = {m: ir[role][m] for m in MODES}
        if all(isinstance(v, str) and v.startswith("#") for v in values.values()):
            return {m: v[:7] for m, v in values.items()}
        return neutral

    links: list[dict[str, str]] = []
    used: set[str] = set()
    for role in roles:
        ext = ir[role]["$extensions"][EXT]
        for cite in ext["inputs"]:
            key = cite.split("=", 1)[0]
            if key in params:
                links.append({"source": f"param:{key}", "target": role})
                used.add(key)
        links += [{"source": dep, "target": role} for dep in ext.get("roles", [])]
    brand = colour("color.background.brand.bold")
    nodes = [
        {
            "id": f"param:{k}",
            "label": f"{k} = {params[k]['value']}",
            "group": "stated" if params[k]["source"] == "stated" else "default",
            "colour": brand if params[k]["source"] == "stated" else neutral,
        }
        for k in params
        if k in used
    ]
    nodes += [
        {"id": r, "label": r, "group": "IR role", "colour": colour(r)} for r in roles
    ]
    seed_to_ir = {
        "title": "Seed → IR",
        "caption": (
            "Every parameter on the left is stated in the seed (brand colour) or a default (grey). "
            "Each band is one recorded input of an IR role; roles that read other roles chain right."
        ),
        "nodes": nodes,
        "links": links,
    }

    links, groups = [], {}
    for key in (k for k in keys if k.startswith("surface.")):
        target = ".".join(key.split(".")[:2])
        groups[target] = {
            "id": target,
            "label": target,
            "group": "surface",
            "colour": neutral,
        }
        links += [
            {"source": dep, "target": target}
            for dep in ir[key]["$extensions"][EXT].get("roles", [])
        ]
    sources = sorted({lk["source"] for lk in links}, key=roles.index)
    ir_to_dtcg = {
        "title": "IR → surfaces",
        "caption": "Each IR role on the left feeds the surfaces the DTCG carries. One role often feeds several.",
        "nodes": [
            {"id": r, "label": r, "group": "IR role", "colour": colour(r)}
            for r in sources
        ]
        + list(groups.values()),
        "links": links,
    }
    return {"sankeys": [seed_to_ir, ir_to_dtcg]}


def generate(
    seed: dict[str, Any], context: dict[str, Any] | None = None
) -> dict[str, Any]:
    """The live-generator entry point: one seed in; IR, DTCG and lineage out. Pure.

    `context.stated` carries a profile's hand edits (DT-PROV-1), so tuning a seed live keeps
    them exactly as `curate` would.
    """
    curator = Curator(seed, (context or {}).get("stated"))
    ir = curator.run()
    name = str((context or {}).get("name", "live"))
    return {
        "ir": ir,
        "tokens": build_tokens(ir, name),
        "lineage": build_lineage(ir),
        "resolved": curator.resolved,
    }


# ── Store ───────────────────────────────────────────────────────────────────
def store_dir(args: argparse.Namespace) -> Path:
    if args.store:
        return Path(args.store)
    return (Path.home() if args.user else Path.cwd()) / resolver.STORE


def profile_names(args: argparse.Namespace) -> list[str]:
    store = store_dir(args)
    names: list[str] = args.name or sorted(
        p.name
        for p in store.glob("*")
        if p.is_dir() and ((p / "seed.json").is_file() or (p / "ir.json").is_file())
    )
    if not names:
        raise SystemExit(f"error: no profiles under {store}; create one with `init`")
    return names


def examples() -> dict[str, Path]:
    return {p.parent.name: p for p in sorted(EXAMPLES_DIR.glob("*/seed.json"))}


# ── CLI ─────────────────────────────────────────────────────────────────────
def cmd_init(args: argparse.Namespace) -> None:
    folder = store_dir(args) / args.profile
    seed_path = folder / "seed.json"
    if seed_path.exists() and not args.force:
        raise SystemExit(f"error: {seed_path} exists; pass --force to replace it")
    if args.example:
        known = examples()
        if args.example not in known:
            raise SystemExit(
                f"error: unknown example {args.example!r}. Available: {', '.join(known)}"
            )
        seed = json.loads(known[args.example].read_text(encoding="utf-8"))
    elif args.hue is not None:
        seed = {"brand.hue": args.hue}
    elif args.accent:
        lightness, chroma, hue = exact_oklch(args.accent)
        seed = {"brand.hue": hue, "brand.chroma": chroma, "brand.lightness": lightness}
    else:
        raise SystemExit("error: init needs --hue, --accent or --example")
    resolve_params(seed)
    folder.mkdir(parents=True, exist_ok=True)
    seed_path.write_text(json.dumps(seed, indent=2) + "\n", encoding="utf-8")
    log.info("seed     %s", seed_path)


def cmd_curate(args: argparse.Namespace) -> None:
    defects = 0
    for name in profile_names(args):
        report = curate_profile(store_dir(args) / name)
        count = {
            k: sum(r.startswith(k) for r in report)
            for k in ("held", "updated", "new", "defect", "choice")
        }
        log.info(
            "curated  %-16s held %d stated, updated %d, imputed %d new; contrast: %d defect, %d choice",
            name,
            count["held"],
            count["updated"],
            count["new"],
            count["defect"],
            count["choice"],
        )
        for line in report:
            if not line.startswith("new"):
                log.info("  %s", line)
        defects += count["defect"]
    if defects:
        # DT-CONTRAST-1: a miss the defaults caused is a failure of curation, never of the user.
        raise SystemExit(
            f"error: curation failed: {defects} text pairing(s) below AA from defaults alone"
        )


def cmd_build(args: argparse.Namespace) -> None:
    for name in profile_names(args):
        log.info("built    %-16s %s", name, build_profile(store_dir(args) / name))


def cmd_all(args: argparse.Namespace) -> None:
    cmd_curate(args)
    cmd_build(args)


def cmd_lineage(args: argparse.Namespace) -> None:
    for name in profile_names(args):
        ir_path = store_dir(args) / name / "ir.json"
        if not ir_path.is_file():
            raise SystemExit(f"error: {ir_path} not found; run curate first")
        out = LINEAGE_DIR / name / "lineage.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        lineage = build_lineage(json.loads(ir_path.read_text(encoding="utf-8")))
        out.write_text(json.dumps(lineage, indent=2) + "\n", encoding="utf-8")
        log.info("lineage  %-16s %s", name, out)


def cmd_set_default(args: argparse.Namespace) -> None:
    store = store_dir(args)
    if not (store / args.profile / resolver.TOKENS_FILE).is_file():
        raise SystemExit(
            f"error: {store / args.profile} has no {resolver.TOKENS_FILE}; run build first"
        )
    marker = store / resolver.DEFAULT_FILE
    marker.write_text(args.profile + "\n", encoding="utf-8")
    log.info("default  %s -> %s", marker, args.profile)


def cmd_status(args: argparse.Namespace) -> None:
    store = store_dir(args)
    default = resolver.default_profile_name(Path.cwd(), Path.home())
    log.info("store    %s", store.resolve())
    log.info("default  %s", default or "(none: consumers use their built-in themes)")
    log.info("examples %s", ", ".join(examples()))
    folders = sorted(p for p in store.glob("*") if p.is_dir()) if store.is_dir() else []
    for folder in folders:
        if args.name and folder.name not in args.name:
            continue
        files = [
            f
            for f in ("seed.json", "ir.json", resolver.TOKENS_FILE)
            if (folder / f).is_file()
        ]
        newer = (
            "ir.json" in files
            and resolver.TOKENS_FILE in files
            and (folder / "ir.json").stat().st_mtime
            > (folder / resolver.TOKENS_FILE).stat().st_mtime
        )
        stale = " (ir.json is newer: rebuild)" if newer else ""
        verdicts = ""
        if "ir.json" in files:
            ir = json.loads((folder / "ir.json").read_text(encoding="utf-8"))
            scores = ir.get("$extensions", {}).get(EXT, {}).get("contrast", [])
            verdicts = "; contrast: {} defect, {} choice".format(
                sum(s["verdict"] == "defect" for s in scores),
                sum(s["verdict"] == "choice" for s in scores),
            )
        log.info(
            "profile  %-16s %s%s%s",
            folder.name,
            ", ".join(files) or "(empty)",
            verdicts,
            stale,
        )


def build_parser() -> argparse.ArgumentParser:
    def _help(p: argparse.ArgumentParser) -> Callable[[argparse.Namespace], None]:
        def _print_help(_: argparse.Namespace) -> None:
            p.print_help()

        return _print_help

    store = argparse.ArgumentParser(add_help=False)
    where = store.add_mutually_exclusive_group()
    where.add_argument(
        "--store", help=f"Profile store directory (default: ./{resolver.STORE})"
    )
    where.add_argument(
        "--user",
        action="store_true",
        help=f"Use the user-global store ~/{resolver.STORE}",
    )

    parser = argparse.ArgumentParser(
        prog="profiles.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.set_defaults(func=_help(parser))
    sub = parser.add_subparsers(dest="cmd", required=False)

    init = sub.add_parser("init", parents=[store], help="Write a profile's seed.json")
    init.add_argument("profile", help="Profile name (a directory in the store)")
    source = init.add_mutually_exclusive_group()
    source.add_argument(
        "--hue",
        type=float,
        help="Brand hue in OKLCH degrees; everything else is imputed",
    )
    source.add_argument(
        "--accent",
        help="Brand accent hex; states its exact OKLCH lightness, chroma and hue",
    )
    source.add_argument("--example", help="Copy a shipped example seed (see `status`)")
    init.add_argument(
        "--force", action="store_true", help="Replace an existing seed.json"
    )
    init.set_defaults(func=cmd_init)

    for name, func, text in (
        (
            "curate",
            cmd_curate,
            "seed.json -> ir.json: impute what is absent, score contrast",
        ),
        (
            "build",
            cmd_build,
            "ir.json -> design-tokens.json (DTCG 2025.10 resolver document)",
        ),
        ("all", cmd_all, "curate, then build"),
        (
            "lineage",
            cmd_lineage,
            f"Write the seed -> IR -> surfaces Sankeys to {LINEAGE_DIR}/<name>/",
        ),
        (
            "status",
            cmd_status,
            "Show the store, the default profile and each profile's state",
        ),
    ):
        p = sub.add_parser(name, parents=[store], help=text)
        p.add_argument(
            "name",
            nargs="*",
            help="Limit to these profiles (default: every profile in the store)",
        )
        p.set_defaults(func=func)

    default = sub.add_parser(
        "set-default",
        parents=[store],
        help=f"Write {resolver.DEFAULT_FILE} in the store",
    )
    default.add_argument("profile", help="A built profile in the store")
    default.set_defaults(func=cmd_set_default)
    return parser


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":  # pragma: no cover
    main()
