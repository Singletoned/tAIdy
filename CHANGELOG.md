# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2024-12-26

### Added
- Python implementation of Taidy smart linter/formatter
- Automatic tool detection with priority-based fallback chains
- Support for multiple programming languages:
  - Python: ruff → uvx ruff → black → flake8 → pylint → python -m py_compile
  - JavaScript/TypeScript: eslint → tsc → prettier → node --check
  - Go: gofmt
  - Rust: rustfmt
  - Ruby: rubocop
  - PHP: php-cs-fixer
  - SQL: sqlfluff → uvx sqlfluff
  - Shell scripts (.sh/.bash/.zsh): shellcheck → beautysh + shfmt
  - Web files: prettier (JSON, CSS, HTML, Markdown)
- Command-line interface with lint, format, and both modes
- Version and help flags
- Comprehensive BDD test suite using Godog and Docker containers

### Changed
- **BREAKING**: Rewritten from Go to Python while maintaining identical CLI interface
- Build system now validates Python syntax instead of compiling binaries
- Test framework generates Docker environments dynamically instead of using static files
- Documentation updated to reflect Python implementation

### Removed
- Go source code and module files (go.mod, go.sum)
- Static Docker files (now generated dynamically)
- Obsolete test configuration files
- Outdated Homebrew formula (binary distribution model)
- Build artifacts directory

### Technical Details
- Python 3.6+ required for type hints and f-strings
- Tests remain in Go using Godog framework for BDD testing
- Docker containers automatically include Python 3 and required tools
- Single Python file implementation (~400 lines)
- Zero external configuration files - tool chains defined in code
- Maintains same priority-based tool detection as original Go version

### Testing
- All 21 test scenarios pass (114 test steps)
- Docker-based isolated test environments
- Support for multiple tool environments (ruff, black, prettier, etc.)
- CLI usage and error handling verification
- Cross-language linting and formatting validation