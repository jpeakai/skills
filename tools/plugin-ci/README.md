# Plugin CI

Generate and validate plugin mirrors, enforce publication boundaries and create immutable version tags.
This Tool owns its Python environment and lockfile independently of the repository's root environment.

```sh
uv run --locked --project tools/plugin-ci plugin-ci --help
uv run --locked --project tools/plugin-ci plugin-ci sync
uv run --locked --project tools/plugin-ci plugin-ci sync --check
uv run --locked --project tools/plugin-ci plugin-ci validate
uv run --locked --project tools/plugin-ci plugin-ci check-worktree
uv run --locked --project tools/plugin-ci plugin-ci tag --dry-run
```

Set `--project-dir /path/to/repository` before or after a subcommand, or set `PLUGIN_CI_PROJECT_DIR`.
Otherwise the Tool searches the current directory and its ancestors for `plugins/`.
An explicit invalid root fails rather than silently selecting another repository.
Human diagnostics go to standard error and failures return a nonzero exit status.

`sync` rebuilds generated skills and hooks from canonical sources and `plugins/composition.yaml`.
Its `--check` flag reports drift without writing.
Canonical development caches and evaluation suites are excluded from plugin mirrors.
Missing canonical inputs fail even when other mirrors were successfully regenerated.

`validate` checks mirror freshness, composition, manifests, hook wiring, skill frontmatter and marketplaces.
The Tool's tests also enforce marketplace publication constraints.

`check-worktree` permits generated mirror changes but rejects uncommitted authored files.
`commit --push` requires `main`, an empty staging index and only generated changes; it commits those changes and pushes normally without force.
`tag --push` creates and pushes missing annotated version tags from the Claude plugin manifests.
Existing tags remain unchanged.
These publication commands mutate Git state and are invoked by the main-branch workflow after validation.

Run the complete local gate:

```sh
make -C tools/plugin-ci ci
```

The gate enforces Ruff formatting and lint, strict mypy, cognitive complexity at most 15 and at least 90 percent coverage.
Tests use real temporary repositories and bare remotes.
