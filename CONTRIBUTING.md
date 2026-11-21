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

## Choose plugin versions

Every PR must assess its semantic changes against the latest `origin/main` before choosing plugin version increments.
Fetch the current base and verify that it is included in the PR branch:

```sh
git fetch --no-tags origin main
git merge-base --is-ancestor origin/main HEAD
git diff --name-only origin/main...HEAD
```

If the ancestry check fails, update the PR branch from the latest `origin/main` through the repository's authorised branch-update workflow before calculating versions.
Repeat the assessment after the base advances or the PR's scope changes.

Identify every affected plugin using `plugins/composition.yaml`, including shared skills and hooks.
Read each affected plugin's version from the freshly fetched `origin/main` manifest.
Calculate one increment for the complete PR relative to that version; do not increment an already bumped branch version for each additional commit.

| Semantic change | Increment |
|---|---|
| Incompatible public behaviour or contract at version `1.0.0` or later | Major |
| New functionality compatible with existing usage | Minor |
| Corrections that preserve the public contract | Patch |
| Incompatible changes during `0.y.z` development | Minor |
| Repository-only maintenance with no shipped plugin change | None |

Use the highest required increment for each affected plugin.
Changes to shipped skill instructions count when they alter agent behaviour.
Unchanged plugins retain their versions.
Update all three manifests for each affected plugin in the PR:

- `plugins/<plugin>/.claude-plugin/plugin.json`
- `plugins/<plugin>/.codex-plugin/plugin.json`
- `plugins/<plugin>/plugin.json`

The PR description must state each affected plugin's base version, proposed version and semantic reason, or explain why no increment is needed.
Reviewers check that assessment against the current base before merge.
Version selection is a contributor and review responsibility; automation publishes mirrors and tags but does not choose or increment versions.

## Validate

```sh
uv run --project tools/plugin-ci plugin-ci validate
uv run pytest
make tools-ci
make docs-ci
make adr-ci
```

Run the affected skill's `scripts/Makefile` `ci` target when changing its executable code.
`make skills-ci` runs every opted-in skill gate.
`make ci` requires authored files to be committed and permits regenerated plugin changes.
`make harness-ci` clones HEAD into isolated harness installs; it verifies committed changes and depends on both external CLIs.

Live evaluation suites run only when an explicit eval path is supplied.
They may start billed agent sessions, so routine validation uses the repository's default test paths.

## Submit

Follow [docs/TICKETING.md](docs/TICKETING.md) for issues, branch naming and PR conventions.
Describe the resulting behavior and the validation actually performed.
Keep generated plugin copies out of feature PRs; the publication workflow owns their commits.
Publish or release only when requested.
Merging a plugin version bump to `main` tags that release automatically; see [release tags](plugins/README.md#release-tags).
