# Repository Agent Guidelines

## Project

- Taidy is a Python 3.8+ CLI meta-formatter/linter. It uses only the standard library at runtime.
- Keep the agent-first contract intact: default execution formats then lints; tools retain their documented priority/fallback order.
- Adapter policy lives in `taidy/cli.py`. Preserve selector coverage and candidate priority with `tests/unit/test_adapter_inventory.py` when changing it.

## Formatting

- Run `make format` regularly and before committing changes. It runs Taidy across the whole repository; Taidy is the sole formatting authority, so do not follow it with individual formatters such as Ruff.
- Treat any `make format` failure as an issue to fix; do not bypass it or hide failures.

## Development

- Use the repository `Makefile` and its `mate`-listed targets for development workflows.
- Run `make test` for fast validation, `make test-docker` when Docker coverage is relevant, and `make typecheck` after Python changes.
- Tests use `unittest`: unit tests are in `tests/unit/`, integration tests in `tests/integration/`, and Docker tests in `tests/docker_tests/`.
- Add adapter changes with selector/fallback characterization coverage and applicable Docker coverage.
