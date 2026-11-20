# Harness CI maintenance

Follow the repository's `CODING_STANDARDS.md` and the CLI skill.

Keep argument wiring in `app.py`, root resolution in `config.py`, and behavior in `commands/`.
Package shell assets under `src/harness_ci/assets/` and resolve them with `importlib.resources`.
Keep the environment and dependencies self-contained in `pyproject.toml` and `uv.lock`.

Run `make -C tools/harness-ci ci` after changes.

Maintain strict typing, a cognitive complexity ceiling of 15, and at least 90 percent coverage.

Tests must use real temporary files and subprocesses, without invoking live Claude or Codex installation.
The `run` command is an explicitly requested live integration check, not part of routine CI.
