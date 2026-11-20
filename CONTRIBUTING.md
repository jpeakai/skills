# Contributing

Follow [CODING_STANDARDS.md](CODING_STANDARDS.md) before writing code.
Read [AGENTS.md](AGENTS.md), [documentation conventions](docs/CONVENTIONS.md) and the affected skill's maintainer instructions.

## Setup

Use the Python version declared in [pyproject.toml](pyproject.toml) with `uv`.
Use Bun for TypeScript tools and documentation gates.
Run `uv sync` to install repository development dependencies.
[Tools](tools/README.md) own independent environments and lockfiles under `tools/<category>/`.
Skill executables declare their own dependencies and run independently of the repository environment.

## Make a change

Edit canonical files under `skills/` or `hooks/`.
Change plugin membership in [plugins/composition.yaml](plugins/composition.yaml).
Run `make fix` to regenerate plugin copies for local validation.

Feature PRs contain canonical changes, plugin manifests and plugin overviews; omit generated `plugins/*/skills/` and `plugins/*/hooks/` changes.
The main-branch publication workflow validates and commits those generated copies before creating release tags.
Keep all three manifests for an affected plugin consistent.
See [plugins/README.md](plugins/README.md#editing) for the source-to-plugin workflow.

Update each affected skill's README when its behavior changes.
Keep examples generic and link new documentation from an existing entry point.
Record binding repository decisions in [adrs/](adrs/index.md), then run `make adrs` and `make adr-ci`.

## Validate

```sh
uv run --project tools/plugin-ci plugin-ci validate
uv run pytest
make tools-ci
make docs-ci
make adr-ci
```

Run the affected skill's `scripts/Makefile` `ci` target when changing its executable code. `make skills-ci` runs every opted-in skill gate. `make ci` requires authored files to be committed and permits regenerated plugin changes. `make harness-ci` clones HEAD into isolated harness installs; it verifies committed changes and depends on both external CLIs.

Live evaluation suites run only when an explicit eval path is supplied.
They may start billed agent sessions, so routine validation uses the repository's default test paths.

## Submit

Follow [docs/TICKETING.md](docs/TICKETING.md) for issues, branch naming and PR conventions.
Describe the resulting behavior and the validation actually performed.
Keep generated plugin copies out of feature PRs; the publication workflow owns their commits.
Publish or release only when requested.
Merging a plugin version bump to `main` tags that release automatically; see [release tags](plugins/README.md#release-tags).
