# Harness CI

Check plugin installation in isolated Claude and Codex homes.
This command performs live harness installations and retains its sandbox for inspection.
It requires Bash, Git, uv, Python 3, Claude Code and Codex on `PATH`.

```bash
uv run --project tools/harness-ci harness-ci --help
uv run --project tools/harness-ci harness-ci run
uv run --project tools/harness-ci harness-ci run --project-dir /path/to/repository /path/to/sandbox
```

The repository comes from `--project-dir`, then `HARNESS_CI_PROJECT_DIR`, then a working-directory ancestor containing `plugins/composition.yaml`.
The default sandbox lives under the repository's `tmp/harness-ci/` directory.
Diagnostics go to standard error; exit status is nonzero when any check fails.
The checkout contains committed repository content, so commit authored changes before checking installation.

Run local checks without installing either harness:

```bash
make -C tools/harness-ci ci
```
