# Ticketing

This repo will use Github Issues to track work items.
Github Issue may be shortened to 'GH Issues'.

## Who Am I

When working in a repo with multiple contributors identity is important.

Look at the `git` config as well as the `gh` CLI to corroborate we are filtering to the right person.

## Backlog

Issues are subdivided into:
- Bugs
- Features

(Other categories may be added overtime)

Each issue title should be prefixed with:
- `[bug]`
- `[feat]`

And also tagged accordingly.

This categorisation will assist with prioritising types of work to work on.

For this repo, the owener is `neozenith` and all tickets should be assigned to them.

## Works In Progress (WIP)

There are 3 possible stages of WIP:
- feature branch (no PR yet)
- draft PR
- Open PR

When work is opened the branch naming convention should be:
- bug: `fix/SKILLS-{issue_number}-{4 words description in kebab-case}`
- feature: `feat/SKILLS-{issue_number}-{4 words description in kebab-case}`

The PR title should be named:
- bug: `[bug] SKILLS-{issue_number} {4 words description}`
- feat: `[feat] SKILLS-{issue_number} {4 words description}`

The related GH Issue should be mentioned in the PR as `Closes #{issue_number}`.

When working on an open issue it should ideally be in a new git worktree named `SKILLS-{issue_number}-{4 words description in kebab-case}`.

## Completed Work

When a PR is MERGED the related branch should also be cleaned up too.
When a PR is MERGED the related GH Issue should be CLOSED.

When a PR is CLOSED the related branch should also be cleaned up too.
When a PR is CLOSED the related GH Issue should remain OPEN.

When an Issue is CLOSED, any related git worktrees can be cleaned up.

