# Contributing

Follow [CODING_STANDARDS.md](CODING_STANDARDS.md) before writing code.
Read [AGENTS.md](AGENTS.md), [documentation conventions](docs/CONVENTIONS.md) and the affected skill's maintainer instructions.

## Setup

Use the Python version declared in [pyproject.toml](pyproject.toml) with `uv`.
Use Bun for TypeScript tools and documentation gates.
Run `uv sync` to install repository development dependencies.
Skill executables declare their own dependencies and run independently of the repository environment.

## Make a change

Edit canonical files under `skills/` or `hooks/`.
Change plugin membership in [plugins/composition.yaml](plugins/composition.yaml).
Run `make fix` to update generated plugin copies.
Keep both manifests for an affected plugin consistent.
See [plugins/README.md](plugins/README.md#editing) for the source-to-plugin workflow.

Update each affected skill's README when its behavior changes.
Keep examples generic and link new documentation from an existing entry point.
Record binding repository decisions in [adrs/](adrs/index.md), then run `make adrs` and `make adr-ci`.

## Validate

```sh
uv run scripts/validate_plugins.py
uv run pytest
make docs-ci
make adr-ci
```

Run the affected skill's `scripts/Makefile` `ci` target when changing its executable code. `make skills-ci` runs every opted-in skill gate. `make ci` additionally requires a clean, committed tree and checks generated-file drift. `make harness-ci` clones HEAD into isolated harness installs; it verifies committed changes and depends on both external CLIs.

Live evaluation suites run only when an explicit eval path is supplied.
They may start billed agent sessions, so routine validation uses the repository's default test paths.

## Submit

Follow [docs/TICKETING.md](docs/TICKETING.md) for issues, branch naming and PR conventions.
Describe the resulting behavior and the validation actually performed.
Keep generated plugin files in the same change as their canonical sources.
Publish or release only when requested.
