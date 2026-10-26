---
name: snr-pr
description: Filter existing pull request code review results into Signal and Noise to improve the signal-to-noise ratio (SNR). Noise improves how future reviews filter distractions; Signal leads to fixes and safeguards against recurring problem categories. Use to triage review feedback or resolve PR discussions after code review. Code review itself is a separate skill.
---

# SNR PR

SNR means **Signal to Noise Ratio** for pull requests.
This skill curates where attention goes after code review has produced findings.
It consumes review results and verifies their claims against the code; it does not conduct an independent code review or generate a new review backlog.

- **Noise:** Feedback that distracts from this PR's intent or lacks actionable evidence. Learn how to filter this category of noise better.
- **Signal:** Feedback that warrants attention within this PR. Address the issue and learn how to prevent this category of problem from recurring.

Both outcomes must produce a reusable lesson, grounded in the feedback and evidence.
Prefer strengthening an existing filter or safeguard over adding a new mechanism.

## Select the PR

- Read applicable repository instructions, contribution guidance, review conventions and ADRs.
- Use the explicitly named PR URL or number when supplied. Otherwise identify the current branch with Git and find its open PR in the checkout's repository.
  Verify repository identity through the hosting service, not the checkout directory name.
  Scope every operation to that repository and PR.
  If none or several match, request the missing target rather than choosing arbitrarily.
- Read the PR intent, linked requirements, base branch, base SHA, current head SHA and complete diff.
  Before editing, ensure the checkout belongs to that PR's head branch and repository, accounting for forks.
  Preserve unrelated local changes.
- Fetch every discussion thread and its comments, following pagination.
  Inspect unresolved threads, current-head review findings and follow-ups on previously resolved threads.
  An outdated line annotation alone does not prove an issue was fixed.
- If no review feedback exists, report that there is nothing to filter and stop.
  Producing code review findings belongs to a separate code review skill.

## Stay current with the base branch

- Fetch the PR's actual base branch when feedback triage starts and before pushing.
  Determine its remote from the verified base repository; do not assume `origin/main`.
  Compare it with the feature branch and integrate missing base changes using repository conventions.
  Prefer merging when no policy is documented. Do not rebase shared history or force-push without authorization.
- Resolve conflicts while preserving the PR's intent and upstream changes.
  Read updated instructions and validate affected behavior before committing and pushing within the user's authorization.
  Do not blindly choose one side or discard unrelated work.
- Recheck freshness before reporting. State the upstream revision checked and any unresolved conflict.
  Updating the feature branch does not authorize merging the PR into its base.

## Classify before acting

Read both [Noise](resources/noise.md) and [Signal](resources/signal.md) rubrics.
Compare each claim with the actual changes, base revision and applicable conventions or ADRs.
Record the thread URL, classification, evidence and disposition.

Default to **Noise** when classification remains unclear after a bounded check of nearby code and the base diff.
A **Signal** finding must be actionable from its explanation and nearby evidence.
Do not reconstruct a poorly expressed concern into a hypothetical useful finding.
Classification does not establish that a potential defect is absent; report material uncertainty.

## Act on the classification

- **Noise:** Follow the prevention outcome in its rubric.
  Update the repository's applicable agent or review instructions with the smallest general rule that prevents the demonstrated pattern.
  Record the noise category, the evidence threshold future reviewers should apply, and the filter improvement made.
  Strengthen existing guidance rather than accumulating thread-specific exceptions.
  Make no unrelated product change.
  Reply with evidence and the prevention change, then resolve within the user's authorization.
- **Signal:** Reproduce the issue.
  For executable product defects, demonstrate a failing behavioral regression test, make the smallest fix and show it passing.
  Identify the underlying problem category and strengthen the narrowest durable safeguard against recurrence, such as a behavioral test, shared validation or an existing lint rule.
  Verify that the safeguard detects the demonstrated failure and covers the relevant category rather than only the reported instance.
  Keep prevention within the PR's intent; do not turn it into speculative hardening or unrelated redesign.
  Follow repository testing boundaries; documentation and infrastructure findings use appropriate validation rather than fabricated tests.
  Explain the fix, category-level prevention and evidence, then resolve after validation passes.
  Leave blocked fixes open with their concrete blocker.
- Begin every agent-authored discussion-thread reply with the literal prefix `Agent:` followed by a space.
  This applies regardless of posting tool or authenticated identity, including `gh` CLI replies posted on behalf of a user.
  Keep exactly one prefix when editing an agent-authored reply, and read back the posted reply to verify it.
- Reuse an earlier reply when it already answers the concern.
  Read back uncertain writes before retrying to avoid duplicate comments.
  Keep replies respectful; classification evaluates the finding, not its author.
- Apply existing authorization to commits, pushes, replies, resolutions and instruction edits.
  Prepare concrete changes before requesting any permission still required.

## Keep the PR body current

- Keep the description aligned with the current diff: problem, resulting behavior, scope and actual validation.
  Preserve the repository's template and required fields.
- Include exactly two Mermaid diagrams, labelled **BEFORE** and **AFTER**, unless repository conventions require another format.
  BEFORE shows the system at the merge base; AFTER shows the current head.
  Derive both from code and the complete diff, preserve comparable actor names and identify the revisions.
  Show a new component's previous absence rather than inventing a previous implementation.
  Validate Mermaid syntax and readability with available repository tooling.
- Revisit the description and diagrams after fixes or base-branch integration.
  Separate implementation claims from verified runtime results.
  Preserve evidence links with their observed revisions; historical evidence does not verify a newer head.
- Edit the existing PR body, then read it back to confirm the intended content and diagrams.

## Verify and report

- Run the repository's required checks for the affected changes before pushing and after final edits.
  Discover documented lint, type, test and complexity gates instead of inventing commands or thresholds.
  Report failures precisely; do not claim a gate passed while violations remain.
- Treat CI as a separate evidence stream. Inspect the configured provider's jobs for the current head.
  Report failing jobs, causes, impact and uncertainty. Triage CI unless fixes or retries are authorized.
  A neutral, skipped or incomplete scan is qualified coverage, not a clean pass.
  Passing validation or a responding preview URL does not prove deployment or authenticated UI behavior.
- Re-query the current head and every thread page after updates.
  If the head changes during verification, refresh affected checks before reporting.
  Report Signal and Noise dispositions, filter improvements, category-level safeguards, remaining open threads, validated scope, commit and CI/preview status.
  Never claim zero unresolved threads from a cached response.
- Do not merge, close or reopen the PR, request another review, change review settings or modify infrastructure solely to complete feedback triage.
  Such actions require a separate request.
  One invocation processes available feedback and rechecks after its updates; continuous monitoring needs an explicit duration or stopping condition.
