# plugins/

Installable packs, grouped by the job they do. Everything here is **generated**
from the canonical trees at the repo root — see [Editing](#editing) before
changing a file in this directory.

| Plugin | Skills | Hook |
|---|---|---|
| [`jpai-essentials`](jpai-essentials) | `librarian`, `gooddocs`, `mermaidjs-diagrams`, `richdocs`, `concise-decisions`, `agnostic` | yes |
| [`jpai-delivery`](jpai-delivery) | `plan-gap`, `concise-decisions` | yes |

`concise-decisions` is in both packs deliberately: it is the decision surface
`plan-gap` asks its questions through, and it stands alone for documentation
work. Installing both packs is fine — each harness namespaces skills by plugin.

The `cli` skill is not in either pack. It stays canonical in
[`../skills/cli`](../skills/cli) and is installed manually; add it to a pack by
naming it in [`composition.json`](composition.json).

## How a pack is built

`../skills/` and `../hooks/` are the source of truth. `composition.json`
declares which skills each pack composes, and
[`../scripts/sync_plugins.py`](../scripts/sync_plugins.py) copies them in.

```
skills/librarian/         ──copy──▶  plugins/jpai-essentials/skills/librarian/
hooks/tool_coach.py       ──copy──▶  plugins/*/hooks/tool_coach.py
composition.json          ──drives──▶ what lands where
```

### Why copies and not symlinks

Symlinks are the obvious way to compose packs from one canonical tree, and
Claude Code handles them: it follows links at load time and reports every skill.

Codex does not. `codex plugin add` copies the plugin into
`$CODEX_HOME/plugins/cache/<marketplace>/<plugin>/<version>` and skips symlink
entries, because its path handling refuses components containing a symlink. The
failure is silent and total — the plugin installs, reports `installed, enabled`,
and carries an **empty** `skills/` directory. Nothing errors on any surface.

So the packs hold real files. The duplication is cheaper than it looks: git
stores content addressed by hash, so every mirrored copy collapses onto the same
object. Mirroring all eight skill trees left `.git` *smaller* than before, and
the three copies of `concise-decisions/SKILL.md` share one blob:

```
$ git ls-files -s '*concise-decisions/SKILL.md'
100644 08fb9432e72f5928d31a232b36169834c49d03ff 0  plugins/jpai-delivery/skills/concise-decisions/SKILL.md
100644 08fb9432e72f5928d31a232b36169834c49d03ff 0  plugins/jpai-essentials/skills/concise-decisions/SKILL.md
100644 08fb9432e72f5928d31a232b36169834c49d03ff 0  skills/concise-decisions/SKILL.md
```

The cost is working-tree disk, not history.

## Editing

**Never edit a file under `plugins/*/skills/` or `plugins/*/hooks/`.** It is
generated output, and the next sync overwrites it.

| To do this | Change this | Then run |
|---|---|---|
| Change a skill | `../skills/<name>/` | `uv run scripts/sync_plugins.py` |
| Change the hook | `../hooks/` | `uv run scripts/sync_plugins.py` |
| Add or remove a skill from a pack | [`composition.json`](composition.json) | `uv run scripts/sync_plugins.py` |
| Change a pack's name, version or blurb | that pack's two `plugin.json` files | `uv run scripts/validate_plugins.py` |

Each pack carries two manifests, one per ecosystem:

- `.claude-plugin/plugin.json` — Claude Code. Skills and hooks are
  auto-discovered, so it declares no paths.
- `.codex-plugin/plugin.json` — Codex. Declares `skills` and `hooks`
  explicitly, plus an `interface` block for presentation.

`validate_plugins.py` asserts the two agree on name and version, so a rename
cannot land half-done.

## Checks

```sh
uv run scripts/sync_plugins.py --check   # mirror matches the canonical trees
uv run scripts/validate_plugins.py       # every layout invariant
./scripts/test_harness_install.sh        # real install into both harnesses
```

The last one clones HEAD into a temp directory and installs both packs into a
throwaway `CLAUDE_CONFIG_DIR` and a throwaway `CODEX_HOME` (plus a replaced
`HOME`, because Codex reads personal skills from `~/.agents/skills` and
`CODEX_HOME` does not cover that). It then asserts each skill reaches the
model-visible prompt and that no external skill root leaked into the sandbox.
