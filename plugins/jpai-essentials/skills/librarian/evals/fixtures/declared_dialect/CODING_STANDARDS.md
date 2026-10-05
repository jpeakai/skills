# Coding standards

How code in this repo is written.

## Python

- Formatting and import order are enforced by ruff; see `[tool.ruff]` in `pyproject.toml`.
- Raise a `ReconcileError` subclass for every domain failure.
- Money is `decimal.Decimal`, never `float`.
