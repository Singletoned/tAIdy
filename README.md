# Taidy

A conservative linter/formatter for AI-agent and developer workflows. Taidy selects an available formatter or linter from its curated tool set, runs it, and reports files it could not check without failing merely because those files are unsupported or their tools are absent.

## Features

- **Automatic Tool Detection**: Tries multiple linters/formatters in priority order
- **Zero Configuration**: Works out of the box and delegates to each tool's own config
- **Extensible**: Easy to add support for new languages and tools
- **Python Package**: Easy to install with pip, or run directly with Python
- **Smart Fallbacks**: Gracefully falls back when preferred tools aren't available

## Curated Support

Taidy guarantees the following well-established tools when they are installed. Docker support is a separate promise because its image must contain and be tested with the tool.

| Files                               | Linter       | Formatter    | Local | Docker             |
| ----------------------------------- | ------------ | ------------ | ----- | ------------------ |
| Python                              | Ruff         | Ruff         | Yes   | Yes                |
| JavaScript and TypeScript           | ESLint       | Prettier     | Yes   | Yes                |
| JSON, CSS, SCSS, HTML, and Markdown | Prettier     | Prettier     | Yes   | Yes                |
| Go                                  | gofmt        | gofmt        | Yes   | Yes                |
| Rust                                | rustfmt      | rustfmt      | Yes   | Yes                |
| Ruby                                | RuboCop      | RuboCop      | Yes   | Yes                |
| PHP                                 | PHP CS Fixer | PHP CS Fixer | Yes   | Yes                |
| Shell                               | ShellCheck   | shfmt        | Yes   | Yes                |
| YAML                                | yamllint     | Prettier     | Yes   | Yes                |
| TOML                                | Taplo        | Taplo        | Yes   | Yes                |
| GitHub Actions workflows            | actionlint   | Prettier     | Yes   | Not yet guaranteed |

Taidy retains compatibility adapters and fallback candidates for some additional file types, but they are best-effort only and are not a release guarantee. The adapter manifest in `taidy/cli.py` is the canonical policy for command selection, tool suggestions, support tier, and Docker availability.

## Installation

### Option 1: uv tool install (Recommended)

```bash
# Install uv if you don't have it:
# curl -LsSf https://astral.sh/uv/install.sh | sh

uv tool install taidy
```

### Option 2: pip install

```bash
pip install taidy
```

### Option 3: Development Installation

```bash
git clone https://github.com/singletoned/taidy.git
cd taidy
pip install -e .
```

### Option 4: Docker (Curated Tool Set)

```bash
# Pull the pre-built image with the Docker-supported tool set
docker pull ghcr.io/singletoned/taidy:latest

# Use it to lint/format files in current directory
docker run --rm -v "$(pwd):/workspace" ghcr.io/singletoned/taidy:latest .
```

See [DOCKER.md](DOCKER.md) for detailed Docker usage instructions.

### Option 5: Run Directly (No Installation)

```bash
git clone https://github.com/singletoned/taidy.git
cd taidy
python -m taidy file.py
```

## Usage

### Basic Usage

```bash
# Lint/format specific files (default mode: both lint and format)
taidy main.py utils.js styles.css

# Or with python -m
python -m taidy main.py utils.js styles.css

# Process all supported files in current directory
taidy .

# Process all files in a directory
taidy src/

# Lint only (no formatting)
taidy lint main.py utils.js

# Format only (no linting)
taidy format main.py utils.js

# Analyze project and suggest missing tools
taidy suggest

# Run taidy in Docker with the Docker-supported tool set
taidy docker .

# Show help
taidy --help

# Show version
taidy --version
```

### Bootstrap

`taidy bootstrap` provisions `uv` and Node.js in Taidy's cache only when they are not already available on `PATH`. It is retained to make the Python and JavaScript tool paths usable; before the first public release, its downloads will be pinned and verified.

### Examples

```bash
# Python files - will use ruff if available, fall back to black, etc.
taidy src/main.py tests/test_utils.py

# Mixed file types - each gets the appropriate linter
taidy main.py app.js styles.css README.md

# Process entire project directory
taidy .

# TypeScript project
taidy src/

# Security scanning (if trufflehog is available)
taidy lint .  # Will include security scanning for all files

# Analyze what tools are missing for your project
taidy suggest
```

### Outcomes and Exit Codes

A zero exit status means every selected, available tool completed successfully. It does **not** mean every input file was formatted or linted: unsupported file types and recognized types with no available tool are reported as `not_checked` and do not fail the command.

A non-zero exit status means a selected tool reported findings or failed to run. `2` means invalid command usage. With `--json`, the result includes `files_processed`, `tools_used`, `errors`, and `not_checked` for automation.

## How It Works

Taidy examines each file's extension and tries linters/formatters in priority order:

1. **Check Availability**: Uses `shutil.which()` to see if each tool is installed
2. **Run First Available**: Executes the first available tool with appropriate arguments
3. **Report Results**: Shows what was run and any issues found

For example, with a Python file:

- First tries `ruff check file.py`
- If ruff isn't installed, tries `uvx ruff check file.py`
- If uv isn't available, falls back to `black --check --diff file.py`
- And so on...

## Development

### Requirements

- Python 3.8+
- [make](https://www.gnu.org/software/make/) (for running development targets)
- Docker (for Docker-based integration tests, optional)

### Building

```bash
# Build distribution packages
make dist

# Run fast tests (unit + integration)
make test

# Run all tests including Docker-based tests
make test-all

# Type checking
make typecheck

# Lint and format code
make format
```

### Testing

Three test layers, all Python:

- **Unit tests** (`tests/unit/`): Fast, mocked subprocess calls
- **Integration tests** (`tests/integration/`): Config and filesystem operations
- **Docker tests** (`tests/docker_tests/`): End-to-end in containers with real tools

```bash
make test          # Unit + integration (fast)
make test-docker   # Docker tests only
make test-all      # Everything
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for your changes
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.
