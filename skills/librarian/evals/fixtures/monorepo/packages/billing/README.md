# billing

The billing package of ledgerly.

## Releasing

1. Bump the version in `packages/billing/pyproject.toml`.
2. Tag `billing-vX.Y.Z` and push; CI publishes.
3. Post the changelog in the team channel.

## Code style

- Every public function in billing has a docstring.
- Never import from a sibling package's private modules.
