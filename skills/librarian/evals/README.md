# Evals

Live agent evals for the librarian, run by the [`pytest-xharness-eval`](https://github.com/neozenith/pytest-xharness-eval) pytest plugin.
Each case covers one value of a permutation axis; [Coverage](#coverage) maps every axis value to the case that exercises it.
Every case is pinned to `claude/claude-sonnet-5-5` for quick, cheap runs.

| Path | What it covers |
|------|----------------|
| `eval_audit.py` | Audit on a greenfield repo, agent-file drift, a declared dialect, a due graduation, and a path-scoped monorepo |
| `eval_apply.py` | Apply on the drift fixture: AGENTS.md + stub, coding rules extracted |
| `eval_init.py` | Init with no flavour, each of the three flavours, and a full CLAUDE.md to migrate |
| `eval_index.py` | Index with no consumer (refuses) and `okf-yaml` with a consumer (builds) |
| `_librarian.py` | Shared structural checks |
| `fixtures/<name>/` | The seed workspace each case starts from |

## Run

Run from the repository root.
Preview the matrix first; nothing is invoked or billed:

```sh
uv run pytest skills/librarian/evals --dry-run
```

Then run it live. **Every cell is a billed agent session.**

```sh
uv run pytest skills/librarian/evals -v
uv run pytest skills/librarian/evals -v -k init_minimal
```

Session logs and a browsable report land in `.xharness_eval_cache/` at the repository root.

## Coverage

The full product of these axes is too large to run, so the cases cover every value of every axis at least once.
The mode diagrams these axes expand are in [ARCHITECTURE.md](../ARCHITECTURE.md).

| Axis | Values |
|---|---|
| Mode | audit, apply, init, index |
| Mode argument | bare, path scope, flavour (none / minimal / standard / rigorous), convention (okf-yaml) |
| Dialect rung | declared, observed, baseline |
| Repo state | greenfield, agent-file drift, misplaced sections, graduation due, monorepo, ADR log |
| Index trigger | consumer present, consumer absent |

| Case | Mode | Argument | Rung | Repo state | Asserts |
|---|---|---|---|---|---|
| `audit_greenfield` | audit | bare | baseline | greenfield | no writes; every missing core doc named |
| `audit_drift` | audit | bare | baseline | agent-file drift, P7, P8 | no writes; M3 and P8 named |
| `audit_declared_dialect` | audit | bare | declared | single-file ADR log declared | no writes; declared rung named; ADR layout not a finding |
| `audit_graduation` | audit | bare | declared | minimal flavour outgrown | no writes; Graduation section |
| `audit_scoped` | audit | path scope | observed | monorepo | no writes; no finding row against the sibling package |
| `apply_drift` | apply | bare | baseline | agent-file drift, P8 | AGENTS.md holds old content; CLAUDE.md is the stub; CODING_STANDARDS.md linked |
| `init_infer` | init | none | baseline | greenfield | five core docs; ADR template; seven coding tenets; flavour named; glossary shape |
| `init_minimal` | init | minimal | baseline | greenfield | core docs; Flavour line reads minimal |
| `init_standard` | init | standard | baseline | greenfield | core docs; Flavour line reads standard |
| `init_rigorous` | init | rigorous | baseline | greenfield | core docs; Flavour line reads rigorous |
| `init_migrate_claude` | init | none | observed | full CLAUDE.md | content moved into AGENTS.md; stub left |
| `index_no_consumer` | index | bare | baseline | docs, no consumer | no writes; reports no trigger |
| `index_okf_yaml` | index | okf-yaml | baseline | ADR log + consumer | `.yml` records, schema and `graph.html` |
