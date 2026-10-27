# TICKETING.md guidelines

The broad sections a `TICKETING.md` should cover.
Each section names a responsibility, not a convention: the repo's file decides how it is met.
Heading names are a suggestion, so match a section by what it covers, not by its exact title.

## Who Am I

How to identify the current user, and which sources must agree (for example the `git` config and the ticketing CLI's login).
Without it, `wip` cannot filter to the right person.

## Backlog

The ticketing system, the ticket categories, the title format, the labels and the default assignee.
Without it, `create` cannot file a ticket.

## Deduplication

How to search for an existing ticket before filing a new one, and what to do when a duplicate is found.
Name which ticket is canonical, how a duplicate is closed and linked to it, and how repeat demand is recorded on the canonical ticket.
Say whether the canonical ticket may be reworded with what a duplicate adds.
Without it, `create` cannot check for duplicates.

## Relationships

How tickets depend on each other, how to keep that graph sound, and how to choose the next piece of work.
Without it, `wip` cannot plan from the backlog when nothing is in flight.

## Works In Progress

The stages work passes through, and the naming rules for branches, PRs and worktrees that tie them to a ticket.
Without it, `wip` cannot group work by stage.

## Completed Work

What happens to tickets, branches and worktrees when a PR merges, when a PR closes unmerged and when a ticket closes.
Without it, `cleanup` has nothing it may act on.
