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

## Deduplication

Before creating an issue, search open and closed issues for the same work.

```sh
gh issue list --state all --search "{key words} in:title,body" --json number,title,state,createdAt --limit 50
```

The earliest issue is the **canonical** issue.
Every later issue for the same work is closed as a duplicate of it, never the other way round.

```sh
gh issue close {duplicate} --duplicate-of {canonical}
```

The canonical issue keeps a count of its duplicates in one tracking comment, edited in place rather than added to:

```
Duplicates: 2
- #31
- #35
```

Create the comment on the first duplicate, then edit it for each later one, increasing the count and adding the issue number.

When a duplicate sheds new light on the work, rewrite the canonical issue's title and body into a refined, updated version.
GH Issues keeps every edit of the body in its history, so nothing is lost.

```sh
gh issue edit {canonical} --title "{refined title}" --body-file {refined body}
```

Emoji reactions on the canonical issue are upvotes.
Anyone who hits the same need reacts with 👍 instead of filing a new issue.
An issue's **demand** is its duplicate count plus its total reactions.

## Relationships

Issues are linked with GH Issues `blocked by` / `blocking` relationships so the backlog forms a DAG of the work.

- An issue that cannot start until another is done is `blocked by` it.
- The graph must stay acyclic: before adding a link, check the blocker is not already (transitively) blocked by the issue.
- When creating an issue, ask whether it is blocked by or blocking any open issue, and link it then.

```sh
gh issue create ... --blocked-by 12,14 --blocking 20
gh issue edit 23 --add-blocked-by 12
gh issue edit 23 --remove-blocked-by 12
gh issue list --state open --json number,title,labels,blockedBy,blocking --limit 200
```

An issue is **ready** when every issue it is blocked by is CLOSED.

To choose the next piece of work, take the ready issues in dependency order (topological order of the DAG).
Among ready issues, prefer the one blocking the most open work, then `[bug]` before `[feat]`, then the highest demand, then the lowest issue number.

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

Worktrees are sibling directories of the main checkout, never inside it.

```sh
git worktree add -b feat/SKILLS-{issue_number}-{description} ../SKILLS-{issue_number}-{description} main
```

## Completed Work

When a PR is MERGED the related branch should also be cleaned up too.
When a PR is MERGED the related GH Issue should be CLOSED.

When a PR is CLOSED the related branch should also be cleaned up too.
When a PR is CLOSED the related GH Issue should remain OPEN.

When an Issue is CLOSED, any related git worktrees can be cleaned up.

