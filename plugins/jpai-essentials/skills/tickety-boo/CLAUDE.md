# tickety-boo: maintainer guide

The skill reads a repo's `TICKETING.md` and carries out its conventions for creating tickets,
reporting work in progress and cleaning up finished work. Dev loop:

```bash
make -C skills/tickety-boo/scripts fix   # mutate: format + lint-fix
make -C skills/tickety-boo/scripts ci    # gate: must exit 0 before handoff
```

## File map

| File | Role |
|------|------|
| `SKILL.md` | agent operating manual: Step 0 conventions, identity, the three commands, rules |
| `scripts/git_wip.py` | `status` and `remove` for local branches and git worktrees. Stdlib only (Tier B) |
| `scripts/test_git_wip.py` | tests against real repositories: a bare origin and a clone, no mocks |
| `resources/github.md` | `gh` commands per step for GitHub Issues |
| `resources/TICKETING.template.md` | the starting file offered when a repo has none |

## Invariants

- **The script never talks to a forge.** Tickets and PRs differ per system and are read through
  the commands `TICKETING.md` or a `resources/<system>.md` documents. The script owns only what
  every repo shares: branches and worktrees.
- **Merged is judged against the remote default branch** (`origin/HEAD`), never the local `HEAD`.
  That is why `remove` deletes with `git branch -D` only after its own ancestry or
  `--expect-sha` check.
- **Refusals are loud and final.** A dirty, locked or main worktree, or a branch holding commits the
  merged PR never had, raises `WipError`. There is no `--force`.
- **No fallback conventions.** A missing `TICKETING.md`, an unset `origin/HEAD` or an unset
  `user.email` stops the command with what to set.

## Adding a ticketing system

Add `resources/<system>.md` with the same four sections as `resources/github.md` (Who am I,
Create a ticket, Work in progress, Finished work), then name it in `SKILL.md` Step 0.4.
Document only commands that were run against a real instance.

## Known gotchas

- **Symptom: a branch shows `upstream origin/main`.** It was cut from the default branch, which
  sets tracking until the first push. `status` reports such a branch as having no upstream of its
  own (`upstream: null`).
- **Symptom: a branch just started reads as merged.** Its tip is the default tip, which is an
  ancestor of itself. `merged()` excludes that case and `status` reports it as `fresh`, so
  cleanup never deletes work that has only begun.
- **Symptom: `remove` says a merged branch is not merged.** The PR was squash or rebase merged, so
  no ancestry exists. Pass the PR's `headRefOid` as `--expect-sha`.
