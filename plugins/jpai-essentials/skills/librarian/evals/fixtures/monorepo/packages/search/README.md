# search

The search package of ledgerly.

## Releasing

1. Bump the version in `packages/search/pyproject.toml`.
2. Tag `search-vX.Y.Z` and push; CI publishes.
3. Post the changelog in the team channel.

## Code style

- Every public function in search has a docstring.
- Never import from a sibling package's private modules.
