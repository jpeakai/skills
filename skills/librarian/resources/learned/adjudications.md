# Adjudications

Placement rulings the user has already made.
Treat every entry as decided: honour it, and do not re-raise the finding it rejects.

Each entry records the ruling, the doctrine it overrides, and the date, so a later reader can tell a deliberate exception from a drift.

## 2026-09-20 — Housekeeping markdown in an okf-yaml bundle is exempt from OKF conformance

**Repo**: robovis.
**Scope**: the `adrs/` bundle.

Four filenames inside an okf-yaml bundle are **not** OKF concepts and carry **no** frontmatter:

| File | Why it is not a concept |
|---|---|
| `README.md` | Orientation for the bundle itself, not a decision |
| `graph.md` | A generated view of the records, not a record |
| `CLAUDE.md` | An agent-file surface |
| `AGENTS.md` | An agent-file surface |

They join `index.md` and `log.md` as reserved names for conformance purposes.
A missing `type` in any of them is **never a finding**.

**Overrides**:

- [adr_okf_yaml.md](../adr_okf_yaml.md) OKF conformance rule 1, "every non-reserved `.md` has parseable YAML frontmatter carrying a non-empty `type`", and rule 2, "`index.md` and `log.md` are the only reserved names".
- The known gotcha in the same file that reads "A `README.md` in the bundle is a concept, not a reserved name, so OKF requires it to carry frontmatter."
  The user's ruling is the opposite: leave it alone, do not rename it to `index.md`, and do not give it frontmatter.

**Consequence for the shipped generator**: `okf_render.py` emits `graph.md` without frontmatter, which is correct under this ruling.
An earlier audit of this repo raised that as an upstream defect; that finding is **withdrawn**.

**Still in scope**: the per-decision `NNNN-slug.md` files remain OKF concepts and must carry frontmatter with a non-empty `type`.
