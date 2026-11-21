# Coding standards template: the baseline tenets and their per-stack mapping

The shape the librarian prefers for `CODING_STANDARDS.md`.
Seven baseline tenets apply to every coding project, including applications, libraries, services and command-line tools.
Each tenet is mapped to the concrete tool, config key or command that enforces it in each language the repo uses.
Init writes this file; audit checks that every tenet is present and mapped for every language, and never judges whether the code complies (ADR-1).

----

## The template

```markdown
# Coding standards

How code in `<repo>` is written.
Process (setup, branches, PRs, review) lives in [CONTRIBUTING.md](CONTRIBUTING.md).
A rule a tool enforces is a pointer to that tool's config here, never restated prose.

## Baseline tenets

1. **Autoformatting is a must.** No hand-formatted code; CI fails on any unformatted file.
2. **Linting runs on the strictest rule set, and every warning is an error.**
3. **Type checking runs on the strictest rule set.**
4. **Unit test coverage stays above 90%.** CI fails below the threshold.
5. **Test real code without mocks.**

   Use real dependencies, real temporary files and dependency injection; code that cannot be tested for real is not tested at all.
6. **Never write tests that are tautologies of the implementation.**

   A test asserts observable behaviour against an independently known expected value.

   It never re-derives that value with the code under test.

   It never asserts that the code calls what the code calls.
7. **Cognitive complexity is measured and capped for all project code where the language supports a checker.**

   The cognitive complexity check runs in CI.

   Its threshold lives in the checker's configuration, and a breach fails the build.

   Cyclomatic complexity and maintainability metrics may supplement this gate.

## <Language>

| Tenet | Enforced by |
|---|---|
| Autoformatting | <tool + check command> |
| Strict linting, warnings as errors | <tool + config key or flag> |
| Strict type checking | <tool + config key or flag> |
| Coverage above 90% | <tool + threshold config> |
| No mocks | <lint rule or review gate> |
| No tautological tests | <review gate> |
| Cognitive complexity capped | <tool + threshold config, or "no cognitive complexity tool for this stack"> |

<Repo-specific idioms for this language: naming, error handling, module layout, dependency policy.>
```

One `## <Language>` section per language the repo ships.
A tenet the stack cannot enforce mechanically names the gate that does (code review, a CI grep), never "n/a".
The complexity tenet is the one exception: it applies only where a tool exists, so a stack without one says so.

Check for an existing cognitive complexity section and gate before adding one.
Preserve an equivalent existing gate and its configured threshold; cyclomatic complexity alone does not cover cognitive complexity.

The language recommendations below are defaults for any coding project.
For Python, prefer [Complexipy](https://complexipy.com/configuration/), configured in `pyproject.toml` under `[tool.complexipy]`.
For JavaScript and TypeScript, prefer [Biome](https://biomejs.dev/linter/rules/no-excessive-cognitive-complexity/), using `linter.rules.complexity.noExcessiveCognitiveComplexity`.

Map the selected gate to its configuration and CI command.
If it is not configured, report the missing gate rather than claiming enforcement or rewriting an existing standards file during init.

----

## Audit findings

Structural only: none of these judges whether the code meets a tenet.

| Finding | Severity |
|---|---|
| A baseline tenet is missing from `CODING_STANDARDS.md` | 🔴 |
| A language the repo ships has no `## <Language>` section | 🟡 |
| A tenet in a language section names no enforcing tool, config key or gate | 🟡 |
| A tenet is restated as prose where a tool config already enforces it | 🟡 (smell P8 in reverse: point at the config) |
