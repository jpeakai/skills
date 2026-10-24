---
name: tickety-boo
description: "Follow a repo's own ticketing conventions from its TICKETING.md (or docs/TICKETING.md). Use when creating a ticket or issue, when asking what work is in flight for the current user (assigned issues, draft and ready PRs, branches, git worktrees), or when cleaning up finished work (closing issues whose PR merged, deleting merged branches and worktrees). Invoke as /tickety-boo create {description}, /tickety-boo wip, or /tickety-boo cleanup."
argument-hint: "create <issue description> | wip | cleanup"
user-invocable: true
---

# tickety-boo

A top-level skill that respects local conventions.
`TICKETING.md` decides **what** to do and **how**: the ticketing system, the commands, the naming rules and any repo scripts.
This skill only routes each command to what the file says, and never fills a gap with conventions of its own.

## First, every time

1. Read `TICKETING.md` at the repo root, else `docs/TICKETING.md`.
   If neither exists, stop and say so.
2. Identify the current user exactly as the file documents.
   If the sources it names disagree, stop and say which said what.
3. When the file names a command or script for a step, use it as written.
   When a step is not documented, say so and ask, rather than inventing one.

## `create {issue description}`

Create the ticket the way `TICKETING.md` describes: its system, category, title, labels and assignee.
Check for an existing duplicate first, and report the new ticket's URL.

## `wip`

Report the current user's work in progress, as `TICKETING.md` defines it:
open assigned tickets, open PRs (draft and ready), their branches and their git worktrees.
Group them by the stages the file names, and list anything that fits none.

## `cleanup`

Find finished work and plan only the actions the file's completion rules state.
Show the plan and ask once before closing tickets or removing branches and worktrees.
Never force a removal, and report anything left untouched with the reason.
