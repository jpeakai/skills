#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Find a design profile and read its design-tokens.json. Stdlib only.

The design-profiles skill owns this file. Every skill that reads profiles carries
its own byte-identical copy and never imports another skill's code (DT-TOOL-1).

A profile name resolves through five tiers, first hit wins (DT-LOC-1):

    1  <project>/.design-profiles/<name>/
    2  ~/.design-profiles/<name>/
    3  <project>/.{codex,claude}/skills/<skill>/resources/profile/<name>/
    4  ~/.{codex,claude}/skills/<skill>/resources/profile/<name>/
    5  the consumer's own built-in fallback (resolve_profile returns None)

With no name, `.default-profile` (one line, in a `.design-profiles/` store) names
the profile, and that name resolves through the same tiers. A name that resolves
nowhere fails loudly.

The reader picks one mode's context from the DTCG 2025.10 resolver document,
merges its token sets and resolves aliases (DT-DTCG-1). It computes nothing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

STORE = ".design-profiles"
DEFAULT_FILE = ".default-profile"
TOKENS_FILE = "design-tokens.json"
EXT = "ai.jpeak.design-profiles"
HARNESSES = (".codex", ".claude")


class ProfileError(SystemExit):
    """A profile that was asked for and cannot be used. Never a silent fallback."""


def candidate_dirs(name: str, skill: str, project: Path, home: Path) -> list[Path]:
    """Every directory tiers 1 to 4 would try for `name`, in precedence order."""
    skill_tier = [
        Path(h) / "skills" / skill / "resources" / "profile" / name for h in HARNESSES
    ]
    return [
        project / STORE / name,
        home / STORE / name,
        *(project / p for p in skill_tier),
        *(home / p for p in skill_tier),
    ]


def default_profile_name(project: Path, home: Path) -> str | None:
    """The name a `.default-profile` file states, project store first. None when neither exists."""
    for store in (project / STORE, home / STORE):
        marker = store / DEFAULT_FILE
        if marker.is_file():
            name = marker.read_text(encoding="utf-8").strip()
            if not name:
                raise ProfileError(
                    f"error: {marker} is empty; it must name one profile"
                )
            return name
    return None


def resolve_profile(
    name: str | None,
    skill: str,
    project: Path | None = None,
    home: Path | None = None,
) -> Path | None:
    """The design-tokens.json for `name` (or the default profile), or None for tier 5.

    None means no profile was asked for and none is the default: the caller uses its
    own built-in behaviour and says so. A name that was asked for, explicitly or by
    `.default-profile`, and resolves nowhere raises ProfileError.
    """
    project = Path.cwd() if project is None else project
    home = Path.home() if home is None else home
    source = "--profile"
    if name is None:
        name = default_profile_name(project, home)
        if name is None:
            return None
        source = DEFAULT_FILE
    tried = candidate_dirs(name, skill, project, home)
    for folder in tried:
        if (folder / TOKENS_FILE).is_file():
            return folder / TOKENS_FILE
    listing = "\n".join(f"  {d / TOKENS_FILE}" for d in tried)
    raise ProfileError(
        f"error: design profile {name!r} (from {source}) resolves nowhere. Tried:\n{listing}"
    )


# ── Reader ──────────────────────────────────────────────────────────────────
def modes(doc: dict[str, Any]) -> list[str]:
    """The mode names a profile carries, e.g. ["light", "dark"]."""
    return list(doc["modifiers"]["mode"]["contexts"])


def default_mode(doc: dict[str, Any]) -> str:
    return str(doc["modifiers"]["mode"]["default"])


def extension(doc: dict[str, Any]) -> dict[str, Any]:
    """The profile's own metadata, which the resolver schema allows only on the modifier."""
    ext: dict[str, Any] = doc["modifiers"]["mode"].get("$extensions", {}).get(EXT, {})
    return ext


def _merge(into: dict[str, Any], src: dict[str, Any]) -> None:
    for key, value in src.items():
        if (
            isinstance(value, dict)
            and isinstance(into.get(key), dict)
            and "$value" not in value
        ):
            _merge(into[key], value)
        else:
            into[key] = value


def _walk(
    node: dict[str, Any],
    path: tuple[str, ...],
    kind: str | None,
    out: dict[str, tuple[str, Any]],
) -> None:
    kind = node.get("$type", kind)
    for key, child in node.items():
        if key.startswith("$") or not isinstance(child, dict):
            continue
        if "$value" in child:
            out[".".join((*path, key))] = (
                child.get("$type", kind) or "",
                child["$value"],
            )
        else:
            _walk(child, (*path, key), kind, out)


def _plain(kind: str, value: Any) -> Any:
    """A DTCG value as a consumer uses it: a colour as hex, a font stack as one CSS string."""
    if kind == "color":
        alpha = value.get("alpha", 1.0)
        return value["hex"] + (f"{round(alpha * 255):02x}" if alpha < 1.0 else "")
    if kind == "fontFamily" and isinstance(value, list):
        return ", ".join(
            f"'{f}'" if " " in f and not f.startswith("'") else f for f in value
        )
    return value


def read_tokens(doc: dict[str, Any], mode: str | None = None) -> dict[str, Any]:
    """Every token of one mode as `{dotted.path: plain value}`, aliases resolved.

    DTCG forbids a group holding a value, so `color.text` is stored as
    `color.text.default`; the flat names restore the bare form (DT-ROLES-1).
    """
    mode = default_mode(doc) if mode is None else mode
    contexts = doc["modifiers"]["mode"]["contexts"]
    if mode not in contexts:
        raise ProfileError(
            f"error: profile has no mode {mode!r}; it carries {sorted(contexts)}"
        )
    tree: dict[str, Any] = {}
    for token_set in contexts[mode]:
        _merge(tree, token_set)
    raw: dict[str, tuple[str, Any]] = {}
    _walk(tree, (), None, raw)

    def resolve(path: str, seen: tuple[str, ...] = ()) -> tuple[str, Any]:
        if path in seen:
            raise ProfileError(
                f"error: alias cycle through {' -> '.join((*seen, path))}"
            )
        if path not in raw:
            raise ProfileError(
                f"error: alias to {path!r}, which the profile does not define"
            )
        kind, value = raw[path]
        if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
            target_kind, target = resolve(value[1:-1], (*seen, path))
            return kind or target_kind, target
        return kind, value

    flat: dict[str, Any] = {}
    for path in raw:
        kind, value = resolve(path)
        flat[path.removesuffix(".default")] = _plain(kind, value)
    return flat


def group(flat: dict[str, Any], prefix: str) -> dict[str, Any]:
    """The tokens under `prefix.`, keyed by the rest of their path."""
    head = prefix + "."
    return {k.removeprefix(head): v for k, v in flat.items() if k.startswith(head)}


def series(flat: dict[str, Any], prefix: str) -> list[Any]:
    """Numbered tokens `prefix.1 … prefix.N` as an ordered list."""
    items = group(flat, prefix)
    return [items[str(i)] for i in range(1, len(items) + 1) if str(i) in items]
