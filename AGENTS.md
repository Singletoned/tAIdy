# Repository Agent Guidelines

## Formatting

- Run `make format` regularly and before committing changes. It runs Taidy across the whole repository; Taidy is the sole formatting authority, so do not follow it with individual formatters such as Ruff.
- Treat any `make format` failure as an issue to fix; do not bypass it or hide failures.
