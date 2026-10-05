# CLAUDE.md

Instructions for coding agents in this repo.

## Commands

```sh
uv run pytest
uv run ruff check .
```

## Never

- Never commit a file under `data/raw/`; it holds customer exports.
- Never call the pricing API from a test.
