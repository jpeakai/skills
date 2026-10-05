# Contributing

## Setup

```sh
uv sync
```

## Pull requests

Open a PR against `main`, keep it under 400 lines, and wait for one review.

## Code style

- Name functions with a verb first: `load_widget`, never `widget_loader`.
- Raise a `WidgetError` subclass for every domain failure; never return `None` to signal an error.
- Tests use `pytest.mark.parametrize` instead of loops inside a test.
- Imports are sorted by ruff; do not hand-order them.
