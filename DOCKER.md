# Taidy Docker Usage

Run taidy with all linting and formatting tools pre-installed, without needing to install them on your system.

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

## Included Tools

The Docker image includes:

| Language       | Tools                        |
| -------------- | ---------------------------- |
| Python         | ruff, black, flake8, pylint  |
| JavaScript/TS  | eslint, prettier, typescript |
| Go             | gofmt                        |
| Rust           | rustfmt                      |
| Ruby           | rubocop                      |
| PHP            | php-cs-fixer                 |
| Shell          | shellcheck, shfmt, beautysh  |
| YAML           | yamllint, prettier           |
| TOML           | taplo                        |
| Terraform      | terraform, tflint            |
| Makefile       | just                         |
| Security       | trufflehog                   |
| GitHub Actions | actionlint                   |
