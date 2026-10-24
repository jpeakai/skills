---
name: tickety-boo
description: "Follow a repo's own ticketing conventions, read from its TICKETING.md (or docs/TICKETING.md), for the whole flow of work. Use when: creating a ticket, issue, bug or feature request and deciding its title, prefix, labels and assignee; asking what is in flight, in progress or WIP for the current user (assigned issues, draft and ready PRs, open branches, git worktrees); or tidying finished work (closing issues whose PR merged, deleting merged or closed branches, removing worktrees). Identifies the current user only by the method TICKETING.md documents. Stops loudly when no TICKETING.md exists. Invoke as /tickety-boo create {description}, /tickety-boo wip, or /tickety-boo cleanup."
argument-hint: "create <issue description> | wip | cleanup"
user-invocable: true
---

# tickety-boo: work the way this repo says to

The repo decides how work is tracked, named and finished. This skill reads that decision from
`TICKETING.md` and carries it out. It never invents a convention the file does not state.

## Step 0: load the conventions (every command)

1. Find the file, first hit wins: `TICKETING.md` at the repo root, then `docs/TICKETING.md`.
   When both exist, use the root one and say so.
2. **No file is a stop, not a guess.** Say that no `TICKETING.md` was found, and offer to write
   one from [resources/TICKETING.template.md](resources/TICKETING.template.md) with the user.
   Do not fall back to "usual" conventions.
3. Read the whole file and extract each convention below. Keep a note of which ones it does not
   state, because an unstated convention is never acted on.

| Convention | Example from a TICKETING.md |
|---|---|
| Ticketing system | GitHub Issues, Jira, Linear |
| Who am I | git config corroborated by `gh api user` |
| Categories, title prefixes, labels | `[bug]` with `bug`, `[feat]` with the feature label |
| Assignee rule | every ticket assigned to the repo owner |
| Ticket key | `SKILLS-{issue_number}` |
| Branch name | `feat/SKILLS-{n}-{four-word-kebab}` |
| PR title and link | `[feat] SKILLS-{n} {four words}`, body `Closes #{n}` |
| Worktree name and place | `SKILLS-{n}-{four-word-kebab}` |
| Completion rules | merged PR closes the issue; closed PR keeps it open |

4. Load the system's command reference. GitHub is in [resources/github.md](resources/github.md).
   For any other system, use the commands `TICKETING.md` documents. If it documents none, stop
   and ask how this repo talks to that system.

## Step 1: who am I

Identify the user **only** by the method `TICKETING.md` documents, and corroborate every source it
names (for GitHub, `git config user.name` and `user.email` against `gh api user`).
When the sources disagree, or a CLI is not signed in, stop and say which source said what.
Filtering someone else's work as "mine" is worse than doing nothing.

## `/tickety-boo create {issue description}`

1. **Classify** the description into one documented category. When two fit, ask one question.
2. **Search for duplicates** among open and recently closed tickets with the description's key
   words. A likely duplicate is shown to the user before anything is created.
3. **Draft** the ticket: the documented title prefix, a short title, the documented labels and
   assignee. The body restates the description, then lists acceptance criteria it implies.
4. **Create it.** An explicit `/tickety-boo create` is the request to create, so proceed. Confirm
   first only when step 1 or 2 raised a question.
5. **Report** the ticket URL, plus the branch, worktree and PR title its conventions imply, so the
   next step needs no lookup. Do not create the branch or worktree unless asked.

## `/tickety-boo wip`

Gather, for the user from Step 1:

- **Tickets:** open tickets assigned to them, per the system's commands.
- **PRs:** their open PRs, split into draft and ready for review.
- **Branches and worktrees:** run the local report, passing the documented ticket key as a regex:

  ```bash
  uv run --no-project <skill>/scripts/git_wip.py status --key-pattern 'SKILLS-\d+' --json
  ```

  `<skill>` is this skill's directory. Run it from the repo root. It reports every local branch
  (whether it is the user's by commit author, merged into the remote default branch, its own
  upstream or `upstream_gone`) and every worktree (clean, dirty or prunable), each with its ticket
  key. A branch with no commits of its own yet is `fresh`, never merged, and the local default
  branch is marked `default`. It fails loudly when `origin/HEAD` or `user.email` is unset.

Join everything on the ticket key and report one table, ordered by the stages `TICKETING.md`
names (for example: assigned and not started, branch only, draft PR, open PR). Then list
**loose ends** on their own: a branch or PR with no ticket key, a PR that does not link its ticket
the documented way, a worktree whose ticket is closed, and a merged branch still present.
Name `/tickety-boo cleanup` when there are loose ends it would tidy.

## `/tickety-boo cleanup`

Cleanup changes the forge and deletes work, so it **plans first, asks once, then acts**.

1. `git fetch --prune` so merge and upstream state is current.
2. Gather what `wip` gathers, plus the user's recently merged and closed PRs with each PR's head
   branch, head commit and linked tickets.
3. **Plan** each action from a completion rule `TICKETING.md` states, and from nothing else. For
   example:
   - **PR merged:** close its linked ticket if it is still open, then delete its branch and worktree.
   - **PR closed without merging:** delete its branch. The ticket stays open.
   - **Ticket closed:** its worktree may go.
   A rule the file does not state produces no action. Report such items as "not covered by
   TICKETING.md".
4. **Show the plan** as one table (ticket, PR, branch, worktree, action, rule), and ask for
   confirmation once. Offer to run all of it, choose rows, or cancel.
5. **Act** through the helper, which refuses anything unsafe and says why:

   ```bash
   uv run --no-project <skill>/scripts/git_wip.py remove --branch BRANCH --expect-sha HEAD_SHA --remote
   uv run --no-project <skill>/scripts/git_wip.py remove --worktree PATH
   ```

   `--expect-sha` is the merged PR's head commit. A squash or rebase merge leaves the branch
   unmerged by ancestry, and the helper deletes it only when its tip is that commit or behind it.
   `--remote` also deletes the remote branch if the forge did not. Run with `--dry-run` first to
   preview the exact git steps.
6. **Report** each action and each refusal (a dirty or locked worktree, a branch with commits the PR
   never had). A refusal is left for the user. Never force past it.

## Rules

- **The file is the authority.** When the user's request and `TICKETING.md` disagree, say so and
  ask. Do not quietly pick one.
- **Never guess identity, keys or systems.** Missing information stops the command with what is
  missing.
- **Outward-facing steps are visible.** Every ticket created or closed is reported with its URL.
- **Local git is the helper's job.** Branch and worktree removal goes through `git_wip.py`, never
  `git branch -D` or `git worktree remove --force` by hand.

## Files

| Path | Holds |
|---|---|
| `scripts/git_wip.py` | `status` (local branches and worktrees with keys) and `remove` (safe deletion). Stdlib only |
| `resources/github.md` | The `gh` commands for each step, for repos on GitHub Issues |
| `resources/TICKETING.template.md` | A starting `TICKETING.md` for a repo that has none |
