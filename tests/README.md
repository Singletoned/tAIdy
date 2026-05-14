# Taidy Test Suite

Three test layers, all Python:

## Unit Tests (`tests/unit/`)

Fast tests that mock subprocess calls. No Docker needed.

```bash
just test-unit
# or: python3 -m unittest discover tests/unit -v
```

## Integration Tests (`tests/integration/`)

Test config loading and file system operations. No Docker needed.

```bash
just test-integration
# or: python3 -m unittest discover tests/integration -v
```

## Docker Tests (`tests/docker_tests/`)

End-to-end tests that build Docker images with specific tool chains installed,
then run `python3 -m taidy` inside containers. Requires Docker.

Each test environment is defined in `base.py` as a Dockerfile template:

- **python311**: Python 3.11 + ruff
- **python311-uv**: Python 3.11 + uv (no ruff)
- **python311-black**: Python 3.11 + black (no ruff, no uv)
- **python311-trufflehog**: Python 3.11 + ruff + trufflehog
- **node18**: Node 18 + prettier + Python 3
- **shell-tools**: Ubuntu 22.04 + shellcheck + shfmt + beautysh + Python 3
- **minimal**: Alpine + Python 3 (no linter tools)

```bash
just test-docker
# or: python3 -m unittest discover tests/docker_tests -v
```

Tests auto-skip when Docker is not available.

## Running Everything

```bash
just test       # Fast tests only (unit + integration)
just test-all   # Everything including Docker tests
```

## Sample Files

`tests/sample_files/` contains test fixtures used by Docker tests:

- `poorly_formatted.py` — Python file for lint/format testing
- `poorly_formatted.sh` / `.bash` / `.zsh` — Shell files
- `poorly_formatted.md` — Markdown file
- `with_secret.py` — Python file with fake secrets for trufflehog testing
