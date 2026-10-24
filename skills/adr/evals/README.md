# Evals

Live agent evals for the adr skill, run by the [`pytest-xharness-eval`](https://github.com/neozenith/pytest-xharness-eval) pytest plugin.
Each case covers one value of a permutation axis; [Coverage](#coverage) maps every axis value to the case that exercises it.
Every case is pinned to `claude/claude-sonnet-5-5` for quick, cheap runs.

| Path | What it covers |
|------|----------------|
| `eval_audit.py` | Audit on a compliant surface and on one with a defect per check |
| `eval_setup.py` | Setup of a file-per-decision surface and of a single-file log |
| `eval_migrate.py` | Migrate an OKF markdown surface with a consumer to `okf-yaml` |
| `_adr.py` | Shared structural checks |
| `fixtures/<name>/` | The seed workspace each case starts from |

`scripts/test_adr_audit.py` pins the two audit fixtures deterministically and runs in `make ci`, so a failing live audit case points at the agent, not the script.

## Run

Run from the repository root.
Preview the matrix first; nothing is invoked or billed:

```sh
uv run pytest skills/adr/evals --dry-run
```

Then run it live. **Every cell is a billed agent session.**

```sh
uv run pytest skills/adr/evals -v
uv run pytest skills/adr/evals -v -k audit_violations
```

Session logs and a browsable report land in `.xharness_eval_cache/` at the repository root.

## Coverage

| Axis | Values |
|---|---|
| Mode | audit, setup, migrate (render is covered by `make ci`) |
| Layout | file-per-decision, single-file log, okf-yaml |
| Repo state | no surface, compliant surface, every markdown violation, OKF markdown with a consumer |

| Case | Mode | Layout | Repo state | Asserts |
|---|---|---|---|---|
| `audit_compliant` | audit | file-per-decision | compliant, one supersession | no writes; audit script ran; `0 🔴` reported |
| `audit_violations` | audit | file-per-decision + scoped log | one defect per check | no writes; audit script ran; every check named |
| `setup_files` | setup | file-per-decision | no surface | `adrs/TEMPLATE.md` lens headings; index; AGENTS.md wired; audit ran |
| `setup_log` | setup | single-file log | no surface | `ADRs.md` Template section with lens headings; AGENTS.md wired; audit ran |
| `migrate_okf_yaml` | migrate | okf-yaml | OKF markdown + consumer | `.yml` records, schema and `graph.html`; convention read; generator ran |
