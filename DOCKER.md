# Taidy Docker Usage

Run taidy with the curated Docker-supported linting and formatting tool set pre-installed, without needing to install them on your system. Jinja (`djlint`) and Makefile (`mbake`) support require local installation. GitHub Actions workflow linting is bundled on a best-effort basis but is not a Docker release guarantee until the production image is tested on every supported platform.

## Quick Start

```bash
# Pull the pre-built image
docker pull ghcr.io/singletoned/taidy:latest

# Lint and format files in current directory
docker run --rm -v "$(pwd):/workspace" ghcr.io/singletoned/taidy:latest .

# Lint only
docker run --rm -v "$(pwd):/workspace" ghcr.io/singletoned/taidy:latest lint .

# Format only
docker run --rm -v "$(pwd):/workspace" ghcr.io/singletoned/taidy:latest format .
```

## Using the `taidy docker` Command

If you have taidy installed locally, you can use the built-in Docker integration:

```bash
# Run taidy in Docker (pulls image automatically)
taidy docker .

# Always pull latest image
taidy docker --pull-always .

# Build image locally from Dockerfile
taidy docker --build-local .

# Use a custom image
taidy docker --image my-registry/taidy:custom .
```

## Building Locally

```bash
# Build the Docker image
docker build -t taidy:latest .

# Run with the local build
docker run --rm -v "$(pwd):/workspace" taidy:latest .
```

## Bundled Tools

The Docker image currently includes:

| Language       | Tools                         |
| -------------- | ----------------------------- |
| Python         | ruff, black, flake8, pylint   |
| JavaScript/TS  | eslint, prettier, typescript  |
| Go             | gofmt                         |
| Rust           | rustfmt                       |
| Ruby           | rubocop                       |
| PHP            | php-cs-fixer                  |
| Shell          | shellcheck, shfmt, beautysh   |
| YAML           | yamllint, prettier            |
| TOML           | taplo                         |
| Terraform      | terraform, tflint             |
| Justfile       | just                          |
| Security       | trufflehog                    |
| GitHub Actions | actionlint (best effort only) |
