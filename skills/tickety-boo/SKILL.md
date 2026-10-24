---
name: tickety-boo
description: "Follow a repo's own ticketing conventions from its TICKETING.md (or docs/TICKETING.md). Use when creating a ticket or issue, when asking what work is in flight for the current user (assigned issues, draft and ready PRs, branches, git worktrees), or when cleaning up finished work (closing issues whose PR merged, deleting merged branches and worktrees). Invoke as /tickety-boo create {description}, /tickety-boo wip, or /tickety-boo cleanup."
argument-hint: "create <issue description> | wip | cleanup"
user-invocable: true
---

# tickety-boo

## First, every time

1. Read `TICKETING.md` at the repo root, else `docs/TICKETING.md`.
   If neither exists, stop and say so. Do not assume conventions.
2. Identify the current user exactly as the file documents (for example `git config user.email` corroborated with `gh api user`).
   If the sources disagree, stop and say which said what.
3. Use only the ticketing system, naming rules and completion rules the file states.

## `create {issue description}`

1. Pick the documented category; ask one question if two fit.
2. Search existing tickets for a duplicate and show any likely match first.
3. Create the ticket with the documented title prefix, labels and assignee.
4. Report its URL and the branch, worktree and PR names the conventions give it.

## `wip`

Report, for the current user only:

- open tickets assigned to them;
- open PRs they authored, split into draft and ready;
- their local branches (`git for-each-ref refs/heads`), marking ones already merged;
- git worktrees (`git worktree list`), marking dirty ones.

Group items by the documented ticket key, and list anything that matches no ticket.

## `cleanup`

1. `git fetch --prune`, then find the user's merged and closed PRs and their tickets.
2. Plan actions from the file's completion rules only, for example:
   merged PR → close its ticket if still open, delete its branch and worktree;
   closed PR → delete its branch, keep the ticket open;
   closed ticket → remove its worktree.
3. Show the plan and ask once before changing anything.
4. Remove worktrees with `git worktree remove` and branches with `git branch -d`, never forcing.
   A squash-merged branch needs `-D`: use it only when the branch tip equals the merged PR's head commit.
   Skip and report anything dirty or unproven.
