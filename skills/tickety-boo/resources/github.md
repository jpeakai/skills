# GitHub Issues and pull requests with `gh`

The commands for each tickety-boo step when `TICKETING.md` names GitHub Issues.
Run them from the repo root, so `gh` resolves the repository from the git remote.
Where `TICKETING.md` documents a different command, its command wins.

## Who am I

```bash
git config user.name
git config user.email
gh auth status
gh api user --jq '{login, name, email}'
```

`gh api user` returns `email` only when the user made it public.
Corroborate on what both sides carry: the name, plus the email when present.
Use the `login` as the GitHub identity in every filter below, and as `@me` where `gh` accepts it.

## Create a ticket

```bash
gh issue list --state all --search "KEY WORDS in:title" --limit 10 --json number,title,state,url
gh label list --limit 100
gh issue create --title "[feat] Short title" --label enhancement --assignee LOGIN --body-file tmp/issue.md
```

Check the documented labels exist before creating, since `gh issue create` fails on an unknown label.
Write the body to a file under `tmp/` and pass `--body-file`, so quoting never mangles it.

## Work in progress

```bash
gh issue list --assignee @me --state open --json number,title,labels,url,updatedAt
gh pr list --author @me --state open --json number,title,isDraft,headRefName,url,closingIssuesReferences
```

`isDraft` splits draft PRs from those ready for review.
`closingIssuesReferences` lists the issues a PR closes through a closing keyword such as `Closes #12`.
An empty list on a PR whose branch carries a ticket key is a loose end: the link is missing.

## Finished work

```bash
gh pr list --author @me --state merged --limit 30 \
  --json number,headRefName,headRefOid,mergedAt,closingIssuesReferences,url
gh pr list --author @me --state closed --limit 30 \
  --json number,state,headRefName,headRefOid,closingIssuesReferences,url
gh issue view NUMBER --json state,stateReason,url
gh issue close NUMBER --reason completed --comment "Done in #PR"
```

`--state closed` returns merged PRs too, so a PR counts as closed without merging only when its `state` is `CLOSED`.
GitHub closes an issue on its own when a PR that names it with a closing keyword merges into the default branch.
Check the issue's state before closing it, and close it only when it is still open.
`headRefOid` is the value for `git_wip.py remove --expect-sha`.
