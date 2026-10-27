# Noise: improve the feedback filter

Noise threads consume attention without establishing an actionable improvement within this PR's intent.
Any of these is sufficient:

- **Pre-existing:** The issue occurs at the PR's base revision and the PR does not introduce the reported failure or a new path that triggers it.
- **Unrelated:** The issue has no causal relationship to this change, even if the referenced file is touched by the PR.
- **Stale:** The current head already addresses the issue.
  Confirm the fix in code or behavior; do not rely only on GitHub's outdated marker.
- **Scope creep:** The proposed remedy adds unrelated abstractions, defensive machinery, speculative requirements or broader redesign.
- **Unclear:** The comment does not establish a specific failure, relevant convention breach or concrete hygiene problem.
  Making it useful would require guessing the author's intent or inventing a scenario.

If a concern might have been Signal but is expressed so poorly that substantial interpretation is needed, classify the thread as Noise.
Default unresolved ambiguity to Noise.
Do a bounded check of nearby code and the base diff; do not turn triage into open-ended investigation.
The burden of proof and communication is on the reviewer.

## Required outcome

- Learn how to filter this category of distraction better in future reviews.
  Record the category, the missing evidence or scope boundary, and the resulting filter improvement.
- Identify the review pattern and its evidence, without treating an unproven concern as a confirmed product defect.
- Update applicable repository agent and review instructions, such as root `AGENTS.md` and existing review-tool configuration.
  When Copilot is configured, use `.github/copilot-instructions.md` and matching `.github/instructions/*.instructions.md` as applicable.
  Follow the repository instruction layout rather than introducing configuration for an unused tool.
  Preserve existing instructions and respect authorization for edits and thread actions.
  State what evidence reviewers must establish and which unsupported recommendation to omit.
- Generalize the prevention rule.
  For example, require a base-revision comparison for regression claims, a current-head check before repeating findings, or a concrete repository rule before requesting extra validation.
- If a rule already exists, strengthen its relevant wording or consolidate its application.
  Do not add a copy per thread, disable review, hide reproducible defects or weaken product safeguards.
- Reply with the classification, brief evidence and the prevention change, then resolve.
  For a stale thread, cite the existing fix as well.

The intended result is that reopening or reviewing the same PR does not repeat this class of low-value finding.
Instruction changes guide future reviews; they cannot guarantee their output.
Do not close and reopen a PR to test them without an explicit request.
