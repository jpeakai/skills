---
paths:
  - "**/README.md"
  - "**/CONTRIBUTING.md"
---

# Never write a number the tooling already reports

Name the command that prints the number, and let the reader run it.
A written number is right the day it is written and wrong after the next change.
No gate reads prose, so nothing fails when it rots.

Do not write:

- Test or check counts: "52 passing cases".
- Measurements: "96% line coverage".
- Counts of things in the repo: "the six skills".
- Versions and dates that a manifest, lockfile or tag already carries.

Write instead:

| Instead of | Write |
|---|---|
| "That reports 52 passing cases and 96% coverage." | "The run reports the case count and the coverage." |
| "The six skills in this pack..." | "The skills in this pack..." |
| "Requires Python 3.12." | "See `requires-python` in `pyproject.toml`." |

A number is allowed when something breaks if it drifts.
A limit a gate enforces, a port, a flag value or a default timeout all qualify.
Nothing else does.
