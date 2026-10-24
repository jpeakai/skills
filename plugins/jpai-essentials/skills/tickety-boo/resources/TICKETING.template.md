# Ticketing

This repo tracks work in {GitHub Issues | Jira project KEY | Linear team}.

## Who am I

Identify the current user with {`git config user.email`} and corroborate it with {`gh api user`}.
When they disagree, stop and ask.

## Backlog

Tickets are one of these categories:

| Category | Title prefix | Label |
|---|---|---|
| Bug | `[bug]` | `bug` |
| Feature | `[feat]` | `enhancement` |

Every ticket is assigned to {the person creating it | a named owner}.

## Work in progress

Work moves through these stages: branch only, draft PR, PR ready for review.

| Item | Pattern |
|---|---|
| Ticket key | `{KEY}-{issue_number}` |
| Branch | `{fix or feat}/{KEY}-{issue_number}-{four-word-kebab}` |
| PR title | `[{bug or feat}] {KEY}-{issue_number} {four words}` |
| PR body | `Closes #{issue_number}` |
| Worktree | `{KEY}-{issue_number}-{four-word-kebab}` under `{.claude/worktrees/}` |

## Completed work

- When a PR is merged, delete its branch and close its ticket.
- When a PR is closed without merging, delete its branch and keep its ticket open.
- When a ticket is closed, its worktree may be removed.
