# Repository Tools

A Tool is a self-contained command-line subproject under `tools/<category>/`.
Each Tool owns its package, dependencies, lockfile, tests and maintenance instructions.
Tools follow the repository's [coding standards](../CODING_STANDARDS.md).

| Tool | Responsibility | Local checks |
|---|---|---|
| [plugin-ci](plugin-ci/README.md) | Generate, validate and publish plugin packages | `make -C tools/plugin-ci ci` |
| [harness-ci](harness-ci/README.md) | Check committed plugin installation in isolated harness homes | `make -C tools/harness-ci ci` |

Run `make tools-ci` for all local Tool gates.
Run `make harness-ci` only when live harness installation is required.
Skill-local executable helpers remain in their canonical skill's `scripts/` directory.
