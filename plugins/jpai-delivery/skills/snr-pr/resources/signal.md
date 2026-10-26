# Signal: prevent the problem category

Signal threads are clearly relevant, specific and worth acting on.
The explanation and nearby evidence establish a problem caused by, exposed by or directly belonging to this PR's scope, with at least one concrete outcome:

- **Reproducible defect:** A stated trigger produces incorrect behavior, with enough detail to reproduce it and write a regression test.
- **Material product impact:** The change breaks function, security, correctness or robustness through a concrete path.
  Severity labels and hypothetical risks alone are insufficient.
- **Convention breach:** The change violates an applicable repository convention or existing ADR.
  Identify the rule and the conflicting code; do not invent a standard.
- **Related repo hygiene:** This PR introduces stale documentation, lint or type errors, or a meaningful gap in coverage of changed behavior.
  A general demand for more tests is insufficient.

The finding should be definitively actionable.
Imperfect grammar does not matter when the trigger and consequence are clear.
If substantial interpretation is needed to establish the actual problem, use the [Noise rubric](noise.md) instead.

## Required outcome

- Learn how to prevent the category of problem revealed by this finding, alongside fixing the reported instance.
- Establish the trigger, expected result, actual result and relationship to the diff.
  Compare the base revision where needed to confirm attribution.
- For executable product defects, write the smallest behavioral regression test, run it to demonstrate the failure, implement the fix and rerun it successfully.
  Do not merely assert source text or mirror implementation details.
- For a convention or hygiene issue, correct the affected code or documentation and run the applicable checks.
  Respect applicable testing instructions and documented infrastructure-testing boundaries.
- Identify the underlying failure pattern and strengthen the narrowest durable safeguard against recurrence.
  Use an appropriate behavioral test, shared validation, lint rule, contract check or repository instruction.
  Prefer existing mechanisms and verify that the safeguard detects the demonstrated failure.
  Explain how it covers the relevant category; do not claim that one fix guarantees the category can never recur.
- Keep the change within PR intent.
  Improve product quality, security or robustness without adopting unrelated refactors from the review comment.
- Reply with the fix, problem category, prevention safeguard, commit and actual validation result.
  Resolve only after the concern is addressed; keep a blocked issue open and explain the blocker.

Examples include:

- A new form discarding the selected option before submitting a request.
- A new command bypassing an existing permission guard.
- Documentation describing a contract that this PR changed.
