# Vendored dependencies

Wholesale copies of capabilities `plan-gap` needs but does not author. Vendoring is
how this skill stays self-contained (`skills/CLAUDE.md` → "skills are fully
self-contained"): no runtime surface here may read, run, or be aware of a sibling
skill's files, so a needed capability is copied in and operated from this folder.

| Vendored | Operated by | Runtime authority |
|----------|-------------|-------------------|
| `concise-decisions/` | `resources/phase2-refinement.md` (Phase 2) | `concise-decisions.md` + its `resources/**` |
| `discovery/` | `resources/phase1-bootstrap.md` (Phase 1, step 1b) | `discovery.md` + its `resources/**` |

## Rules for the copies

- **Read-only.** Never hand-edit a vendored file. A change you want is either a
  plan-gap overlay (write it in the phase file that operates the copy, per the
  table above) or an upstream change followed by a re-vendor.
- **A vendored copy carries no `SKILL.md`.** Upstream's `SKILL.md` is renamed to
  `<name>.md` on the way in, because a harness treats every `SKILL.md` under a
  plugin as a skill to register and rejects the whole plugin when two of them
  declare the same name. The rename is mechanical, part of the refresh below, and
  the only edit ever made to a vendored file.
- **Runtime authority is the vendored `<name>.md` and the resources it names.**
  Each copy also carries its upstream `README.md`, `CLAUDE.md`, and `docs/adrs/` —
  development-time documents kept for provenance, addressed to whoever *edits* the
  upstream skill. They are **not** plan-gap's decision log (that is `../CLAUDE.md`),
  they are not decision records for a run, and they are never cited as authority
  while running.
- **A vendored copy accumulates nothing.** No session writes into this tree — not a
  learning file, not a cache, not a note. Everything a run produces belongs to the
  spec being refined; everything a *maintainer* learns belongs in `../CLAUDE.md`
  and the surface it governs. That is what keeps the refresh below a clean
  wholesale replace with nothing to preserve.

## Refresh procedure

Re-vendor wholesale, never cherry-pick individual files:

```sh
rsync -a --delete \
  --exclude node_modules --exclude '.*cache*' --exclude .DS_Store --exclude evals \
  <upstream-skill-dir>/ skills/plan-gap/vendor/<name>/

# Demote the entrypoint so the harness does not register it as a second skill.
cd skills/plan-gap/vendor/<name>
mv SKILL.md <name>.md

# Repoint the links upstream wrote to it, anywhere in the copy.
grep -rl 'SKILL\.md' . | xargs sed -i '' \
  -e 's|\.\./\.\./SKILL\.md|../../<name>.md|g' -e 's|\.\./SKILL\.md|../<name>.md|g' \
  -e 's|](SKILL\.md)|](<name>.md)|g'

# Repoint every remaining mention in the runtime surfaces.
grep -rl 'SKILL\.md' resources | xargs sed -i '' 's|SKILL\.md|<name>.md|g'
```

The split in those last two commands is the rule. A **runtime surface** —
`<name>.md` and `resources/**` — may not name a file that is not there, because a
run following the citation would open nothing. A **provenance document** —
`README.md`, `CLAUDE.md`, `docs/adrs/**` — keeps upstream's wording, because it is
addressed to whoever edits the upstream skill, where the file really is
`SKILL.md`. Only links are rewritten there.

`uv run scripts/validate_plugins.py` fails if a vendored `SKILL.md` survives, so a
refresh that forgets the rename is caught before it reaches a marketplace.

Then re-read the overlay that operates it and reconcile: if upstream renamed a
resource, changed a step number, or altered the question anatomy, the overlay's
citations must be updated in the same commit. Drift from upstream is accepted
between refreshes; a stale copy that still works is preferred to a live reference
that couples two skills.
