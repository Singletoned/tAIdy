# Taidy

A linter/formatter for all file types. Designed for AI agents to be able to easily use, so that you can tell them to use this for every file and it won't fail.  Detects what tools are installed and uses them.  If it can't find a tool, it passes silently.

Mostly written by AI (Claude Sonnet).

## Features

- 🔍 **Automatic Tool Detection**: Tries multiple linters/formatters in priority order
- 🚀 **Zero Configuration**: Works out of the box (but respects existing config)
- 🔧 **Extensible**: Easy to add support for new languages and tools
- 📦 **Python Package**: Easy to install with pip, or run directly with Python
- 🎯 **Smart Fallbacks**: Gracefully falls back when preferred tools aren't available

## Supported Languages & Tools

| Language   | Priority Order |
|------------|----------------|
| **Python** | ruff → uvx ruff → black → flake8 → pylint → python -m py_compile |
| **JavaScript** | eslint → prettier → node --check |
| **TypeScript** | eslint → tsc --noEmit → prettier |
| **Go** | gofmt |
| **Rust** | rustfmt |
| **Ruby** | rubocop |
| **PHP** | php-cs-fixer |
| **JSON/CSS** | prettier |

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

### Option 4: Run Directly (No Installation)

```bash
git clone https://github.com/singletoned/taidy.git
cd taidy
python -m taidy file.py
```

## Usage

### Basic Usage

```bash
# Lint/format specific files
taidy main.py utils.js styles.css

# Or with python -m
python -m taidy main.py utils.js styles.css

# Lint/format all files in current directory (with find)
find . -name "*.py" -o -name "*.js" | xargs taidy

# Show help
taidy --help

# Show version
taidy --version
```

### Examples

```bash
# Python files - will use ruff if available, fall back to black, etc.
taidy src/main.py tests/test_utils.py

# Mixed file types - each gets the appropriate linter
taidy main.py app.js styles.css README.md

# TypeScript project
taidy src/**/*.ts src/**/*.tsx
```

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

- Python 3.6+
- [just](https://github.com/casey/just) (for build scripts)
- Docker (for integration tests)

### Building

```bash
# Install in development mode
pip install -e .

# Build distribution packages
python -m build

# Run tests
just test

# Clean build artifacts
just clean
```

### Testing

The project uses Behavior Driven Development (BDD) with [Godog](https://github.com/cucumber/godog) and [testcontainers](https://golang.testcontainers.org/).

```bash
# Run all tests
just test

# Run specific feature
just test-feature features/python.feature
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for your changes
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Roadmap

- [ ] Configuration file support (.taidy.yaml)
- [ ] Custom linter definitions
- [ ] Parallel execution for multiple files
- [ ] Plugin system
- [ ] More language support (C++, C#, Kotlin, etc.)
- [ ] Integration with popular editors (VS Code, vim, emacs)

## Inspiration

Inspired by tools like:
- [trunk](https://trunk.io/) - Universal linter/formatter
- [mega-linter](https://megalinter.io/) - Comprehensive linting suite
- [pre-commit](https://pre-commit.com/) - Git hook framework

Taidy aims to be simpler and more focused: just automatically run the right linter for each file type.
