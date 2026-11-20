# Coding standards

Coding conventions and their enforcement for this repository.
Setup and contribution process live in [CONTRIBUTING.md](CONTRIBUTING.md).
Scoped skill instructions take precedence where they document an established local convention.

## Baseline tenets

These are the standard-flavour baseline.
The language tables distinguish observed enforcement from gaps; this document does not claim a missing gate already exists.

1. Autoformat code and fail checks on formatting drift.
2. Use strict lint rules and treat warnings as errors.
3. Use strict type checking.
4. Require at least 90 percent unit test coverage.
5. Test real code with real dependencies, temporary files and dependency injection; avoid mocks.
6. Test observable behavior against independently known expected results, never implementation tautologies.
7. Measure and cap complexity where tooling exists; keep thresholds in the enforcing configuration.

## Python

| Tenet | Observed enforcement or gap |
|---|---|
| Autoformatting | Tool and skill Makefiles run `ruff format --check` |
| Strict linting | Tool and skill Makefiles run `ruff check`; Tools enable broad error, import, modernization and correctness rules |
| Strict typing | Tool subprojects and the ADR skill run strict mypy |
| Coverage | Tool subprojects and the ADR skill enforce at least 90 percent coverage; root hook tests have no threshold |
| Real dependencies | ADR audit tests use real temporary Git repositories; no repository-wide mock prohibition is mechanically enforced |
| Behavioral tests | Publication and hook suites check observable contracts; review remains responsible for test quality |
| Complexity | Tools and Richdocs enforce cognitive complexity at most 15 per function with their local `pyproject.toml` |

Repository Tools own their dependencies and lockfiles under [tools/](tools/README.md).
The root [pyproject.toml](pyproject.toml) owns hook tests and evaluation dependencies.
Shipped Python helpers declare standalone dependencies through PEP-723 headers and run with `uv run --no-project`.
Do not add consumer dependencies to the repository's development environment to hide a missing script declaration.

## TypeScript and JavaScript

| Tenet | Observed enforcement or gap |
|---|---|
| Autoformatting | Skill Makefiles run Biome with skill-local configuration |
| Strict linting | Biome recommended rules are configured locally; strictest-rule and warning policy remain gaps |
| Strict typing | Skill `tsconfig.json` files enable `strict`; JavaScript assets have no uniform strict type-check gate |
| Coverage | Librarian Makefile uses Bun's `--coverage-threshold=0.90`; other scopes keep their existing gates |
| Real dependencies | Bun suites exercise real modules and DOM fixtures; no universal mock ban is mechanically enforced |
| Behavioral tests | Scoped Bun suites and review check behavior; no universal automatic tautology detector is configured |
| Complexity | No uniform complexity cap is declared in the skill-local Biome configurations |

Use each skill's existing Bun and TypeScript configuration.
Keep browser assets separate from Python generators that assemble them.
Do not duplicate a published tool's implementation inside a skill.

## Shell

| Tenet | Observed enforcement or gap |
|---|---|
| Autoformatting | No shell formatter gate is declared |
| Strict linting | No repository-wide ShellCheck gate is declared |
| Strict typing | No static shell type-check gate is declared |
| Coverage | No shell coverage threshold is declared |
| Real dependencies | Harness installation scripts use isolated real installs; routine test runs do not invoke them |
| Behavioral tests | Harness checks assert installed skill visibility; review checks changes to shell behavior |
| Complexity | No shell complexity gate is declared |

Quote paths and preserve argument boundaries.
Keep shell changes scoped to the command's actual contract.

## Markdown and structured data

Keep authored documentation generic and follow [docs/CONVENTIONS.md](docs/CONVENTIONS.md).
Use one sentence per line where practical and plain punctuation.
Keep each skill README's overview visible and its detailed diagram collapsed.
Derive diagram palettes from the Mermaid skill's color references and pass the published Mermaid lint without relaxing gates.

YAML decision sources must validate against [adrs/record.schema.json](adrs/record.schema.json).
Generated decision views and plugin mirrors are never edited by hand.
Publication constraints are enforced by [tools/plugin-ci/tests/test_publication_contract.py](tools/plugin-ci/tests/test_publication_contract.py).
