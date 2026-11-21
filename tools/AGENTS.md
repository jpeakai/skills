# Tool maintenance

Organise repository automation into focused Tool subprojects such as `tools/plugin-ci/` and `tools/harness-ci/`.
Each Tool must be a self-contained, well-structured CLI following the root [coding standards](../CODING_STANDARDS.md) and [CLI skill](../skills/cli/SKILL.md).
Keep related operations as subcommands of the appropriate Tool rather than adding loose root scripts.

Each Tool owns these files and directories:

- `pyproject.toml` and `uv.lock` for dependencies.
- `README.md` for usage.
- `AGENTS.md` for maintenance rules.
- A regular `CLAUDE.md` importing its sibling instructions.
- A source package and behavioral tests.
- A `Makefile` gate.

A `CLAUDE.md` contains only `@AGENTS.md`; never use a symlink.
Keep dependencies and configuration inside the Tool subproject rather than the root development environment.

Use `src/<package>/app.py` for argument wiring, `config.py` for root discovery and `commands/` for behavior.
Resolve the target repository explicitly, through a documented environment variable or by walking ancestor directories for a repository sentinel.
Do not derive a target repository from the installed package location.
Ship runtime assets as package data and send human diagnostics to standard error.

Every Tool's `make ci` must check formatting, lint, strict types, cognitive complexity and at least 90 percent coverage.
Keep cognitive complexity thresholds in the Tool's configuration and prefer Complexipy for Python.
Test real code and dependencies with temporary files and subprocesses; avoid mocks.
Keep live external installation checks separate from routine local gates.
Update root callers and documentation together when changing CLI contracts.
