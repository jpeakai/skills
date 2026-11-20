# Plugin CI maintenance

Follow [the Tool conventions](../AGENTS.md) and [repository coding standards](../../CODING_STANDARDS.md).
Keep argument wiring in `app.py`, repository discovery in `config.py`, and operations in `commands/`.
Pass the resolved repository explicitly into operations; never depend on package installation paths.
Keep `pyproject.toml` and `uv.lock` self-contained.

Run `make -C tools/plugin-ci ci` after code changes.
Keep strict typing, cognitive complexity at most 15 and at least 90 percent coverage.
Use real temporary files, Git repositories and bare remotes in tests.
Never publish to the real remote during routine checks.

Only `plugins/<plugin>/skills/` and `plugins/<plugin>/hooks/` are automatically committed generated output.
Do not broaden that boundary to authored manifests, documentation or canonical sources.
Preserve immutable release tags and ordinary non-force pushes.
Keep the workflow YAML, workflow README and root Makefile aligned with CLI changes.
