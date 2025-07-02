#!/usr/bin/env python3
"""Taidy CLI - Smart linter/formatter with automatic tool detection."""

import fnmatch
import json
import logging
import os
import shutil
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

# Version information - can be overridden at build time
VERSION = "0.1.0"
GIT_COMMIT = "unknown"
BUILD_DATE = "unknown"

# Help text constants
USAGE_TEXT = """
Usage: taidy [command] <files_or_directories...>

Commands:
  lint     Lint files only (no formatting)
  format   Format files only (no linting)
  (none)   Both lint and format (default)

Examples:
  taidy file.py               # Lint and format a single file
  taidy .                     # Process all supported files in current directory
  taidy src/                  # Process all supported files in src/ directory
  taidy lint file1.py file2.js  # Lint multiple files

Flags:
  -h, --help     Show this help message
  -v, --version  Show version information"""

DIRECTORY_PROCESSING_TEXT = """Directory Processing:
  When a directory is specified, taidy recursively finds all supported files
  and processes them. Common directories like .git/, node_modules/, and
  __pycache__/ are automatically ignored."""

SUPPORTED_LANGUAGES_TEXT = """Supported file types and linters:
  Python:       ruff → uvx ruff → black → flake8 → pylint → python -m py_compile
  JavaScript:   eslint → prettier → node --check
  TypeScript:   eslint → tsc --noEmit → prettier
  Go:           gofmt
  Rust:         rustfmt
  Ruby:         rubocop
  PHP:          php-cs-fixer
  Shell:        shellcheck → beautysh (linting), shfmt → beautysh (formatting)
  JSON/CSS:     prettier
  YAML:         yamllint → prettier
  TOML:         taplo check → taplo format
  Terraform:    terraform validate/tflint → terraform fmt
  Docker:       hadolint (Dockerfile, .dockerfile)
  GitHub Actions: actionlint → yamllint → prettier (.github/workflows/*.yml)

Taidy automatically detects which linters are available and uses the best one for each file type."""

CONFIGURATION_TEXT = """Configuration:
  Create a .taidy.json file in your project root to customize behavior.
  Example configuration:
    {
      "ignore": [
        "tests/fixtures/*",
        "vendor/**",
        "*.generated.*"
      ]
    }
""".strip()

# Configure logging
logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Setup logging to stdout with appropriate format"""
    # Only setup if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(levelname)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)


class Mode(Enum):
    BOTH = "both"  # Both lint and format
    LINT = "lint"  # Lint only
    FORMAT = "format"  # Format only


@dataclass
class LinterCommand:
    """Represents a linter command that can be tried"""

    available: Callable[[], bool]
    command: Callable[[List[str]], Tuple[str, List[str]]]
    supports_directories: bool = False


# Cache for command availability to avoid repeated shutil.which() calls
_command_availability_cache: Dict[str, bool] = {}


def is_command_available(cmd: str) -> bool:
    """Check if a command is available in PATH, with caching"""
    if cmd not in _command_availability_cache:
        _command_availability_cache[cmd] = shutil.which(cmd) is not None
    return _command_availability_cache[cmd]


def load_config(start_path: str = ".") -> Dict[str, Any]:
    """Load configuration from .taidy.json file, searching up directory tree"""
    current_path = Path(start_path).resolve()

    # Search up directory tree for .taidy.json
    for path in [current_path] + list(current_path.parents):
        config_file = path / ".taidy.json"
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    config = json.load(f) or {}
                    return config
            except Exception as e:
                logger.warning(f"Failed to parse {config_file}: {e}")
                return {}

    return {}


def should_ignore_file(file_path: Path, ignore_patterns: List[str]) -> bool:
    """Check if a file should be ignored based on ignore patterns"""
    file_str = str(file_path)

    for pattern in ignore_patterns:
        # Check if pattern matches the full path
        if fnmatch.fnmatch(file_str, pattern):
            return True

        # Check if pattern matches any part of the path
        if fnmatch.fnmatch(file_path.name, pattern):
            return True

        # Check if any parent directory matches the pattern
        for part in file_path.parts:
            if fnmatch.fnmatch(part, pattern):
                return True

    return False


def discover_files_in_directory(directory_path: str) -> List[str]:
    """Discover all supported files in a directory recursively"""
    supported_extensions: Set[str] = set()
    supported_extensions.update(LINTER_MAP.keys())
    supported_extensions.update(FORMATTER_MAP.keys())

    # Load config and get ignore patterns
    config = load_config(directory_path)
    config_ignores = config.get("ignore", [])

    # Common directories to ignore (defaults)
    default_ignore_patterns = [
        ".git",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        "dist",
        "build",
        ".venv",
        "venv",
        ".env",
        "env",
        "*.egg-info",
        ".mypy_cache",
        ".ruff_cache",
        ".coverage",
    ]

    # Combine default and config ignore patterns
    all_ignore_patterns = default_ignore_patterns + config_ignores

    discovered_files = []
    directory = Path(directory_path)

    for file_path in directory.rglob("*"):
        # Skip if it's not a file
        if not file_path.is_file():
            continue

        # Skip if file should be ignored
        if should_ignore_file(file_path, all_ignore_patterns):
            continue

        # Check if extension is supported
        ext = file_path.suffix.lower()
        is_supported = ext in supported_extensions

        # Special case: Dockerfile files without extension
        if not is_supported and file_path.name.lower() in ["dockerfile"]:
            is_supported = True

        # Special case: GitHub Actions workflow files
        if not is_supported and file_path.suffix.lower() in [".yml", ".yaml"]:
            if ".github/workflows" in str(file_path):
                is_supported = True

        if not is_supported:
            continue

        discovered_files.append(str(file_path))

    return sorted(discovered_files)


# LinterConfig maps file extensions to sequences of linter commands to try in order
LINTER_MAP: Dict[str, List[LinterCommand]] = {
    ".py": [
        LinterCommand(
            available=lambda: is_command_available("ruff"),
            command=lambda files: ("ruff", ["check", "--quiet"] + files),
            supports_directories=True,
        ),
        LinterCommand(
            available=lambda: is_command_available("uvx"),
            command=lambda files: ("uvx", ["ruff", "check", "--quiet"] + files),
            supports_directories=True,
        ),
        LinterCommand(
            available=lambda: is_command_available("black"),
            command=lambda files: ("black", ["--check", "--quiet"] + files),
        ),
        LinterCommand(
            available=lambda: is_command_available("flake8"),
            command=lambda files: ("flake8", ["--quiet"] + files),
        ),
        LinterCommand(
            available=lambda: is_command_available("pylint"),
            command=lambda files: ("pylint", ["--quiet"] + files),
        ),
        LinterCommand(
            available=lambda: is_command_available("python"),
            command=lambda files: ("python", ["-m", "py_compile"] + files),
        ),
    ],
    ".js": [
        LinterCommand(
            available=lambda: is_command_available("eslint"),
            command=lambda files: ("eslint", ["--quiet"] + files),
        ),
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: (
                "prettier",
                ["--check", "--log-level", "error"] + files,
            ),
        ),
        LinterCommand(
            available=lambda: is_command_available("node"),
            command=lambda files: ("node", ["--check"] + files),
        ),
    ],
    ".jsx": [
        LinterCommand(
            available=lambda: is_command_available("eslint"),
            command=lambda files: ("eslint", ["--quiet"] + files),
        ),
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: (
                "prettier",
                ["--check", "--log-level", "error"] + files,
            ),
        ),
    ],
    ".ts": [
        LinterCommand(
            available=lambda: is_command_available("eslint"),
            command=lambda files: ("eslint", ["--quiet"] + files),
        ),
        LinterCommand(
            available=lambda: is_command_available("tsc"),
            command=lambda files: ("tsc", ["--noEmit"] + files),
        ),
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: (
                "prettier",
                ["--check", "--log-level", "error"] + files,
            ),
        ),
    ],
    ".tsx": [
        LinterCommand(
            available=lambda: is_command_available("eslint"),
            command=lambda files: ("eslint", ["--quiet"] + files),
        ),
        LinterCommand(
            available=lambda: is_command_available("tsc"),
            command=lambda files: ("tsc", ["--noEmit"] + files),
        ),
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: (
                "prettier",
                ["--check", "--log-level", "error"] + files,
            ),
        ),
    ],
    ".json": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: (
                "prettier",
                ["--check", "--log-level", "error"] + files,
            ),
        ),
    ],
    ".css": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: (
                "prettier",
                ["--check", "--log-level", "error"] + files,
            ),
        ),
    ],
    ".scss": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: (
                "prettier",
                ["--check", "--log-level", "error"] + files,
            ),
        ),
    ],
    ".html": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: (
                "prettier",
                ["--check", "--log-level", "error"] + files,
            ),
        ),
    ],
    ".md": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: (
                "prettier",
                ["--check", "--log-level", "error"] + files,
            ),
        ),
    ],
    ".go": [
        LinterCommand(
            available=lambda: is_command_available("gofmt"),
            command=lambda files: ("gofmt", ["-l"] + files),
        ),
    ],
    ".rs": [
        LinterCommand(
            available=lambda: is_command_available("rustfmt"),
            command=lambda files: ("rustfmt", ["--check", "--quiet"] + files),
        ),
    ],
    ".rb": [
        LinterCommand(
            available=lambda: is_command_available("rubocop"),
            command=lambda files: ("rubocop", ["--quiet"] + files),
        ),
    ],
    ".php": [
        LinterCommand(
            available=lambda: is_command_available("php-cs-fixer"),
            command=lambda files: (
                "php-cs-fixer",
                ["fix", "--dry-run", "--quiet"] + files,
            ),
        ),
    ],
    ".sh": [
        LinterCommand(
            available=lambda: is_command_available("shellcheck"),
            command=lambda files: ("shellcheck", ["--quiet"] + files),
        ),
        LinterCommand(
            available=lambda: is_command_available("beautysh"),
            command=lambda files: ("beautysh", ["--check"] + files),
        ),
    ],
    ".bash": [
        LinterCommand(
            available=lambda: is_command_available("shellcheck"),
            command=lambda files: ("shellcheck", ["--quiet"] + files),
        ),
        LinterCommand(
            available=lambda: is_command_available("beautysh"),
            command=lambda files: ("beautysh", ["--check"] + files),
        ),
    ],
    ".zsh": [
        LinterCommand(
            available=lambda: is_command_available("shellcheck"),
            command=lambda files: ("shellcheck", ["--quiet"] + files),
        ),
        LinterCommand(
            available=lambda: is_command_available("beautysh"),
            command=lambda files: ("beautysh", ["--check"] + files),
        ),
    ],
    ".yaml": [
        LinterCommand(
            available=lambda: is_command_available("yamllint"),
            command=lambda files: ("yamllint", ["--quiet"] + files),
        ),
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: (
                "prettier",
                ["--check", "--log-level", "error"] + files,
            ),
        ),
    ],
    ".yml": [
        LinterCommand(
            available=lambda: is_command_available("yamllint"),
            command=lambda files: ("yamllint", ["--quiet"] + files),
        ),
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: (
                "prettier",
                ["--check", "--log-level", "error"] + files,
            ),
        ),
    ],
    ".toml": [
        LinterCommand(
            available=lambda: is_command_available("taplo"),
            command=lambda files: ("taplo", ["check", "--quiet"] + files),
        ),
    ],
    ".tf": [
        LinterCommand(
            available=lambda: is_command_available("terraform"),
            command=lambda files: ("terraform", ["validate"] + files),
        ),
        LinterCommand(
            available=lambda: is_command_available("tflint"),
            command=lambda files: ("tflint", ["--quiet"] + files),
        ),
    ],
    ".tfvars": [
        LinterCommand(
            available=lambda: is_command_available("terraform"),
            command=lambda files: ("terraform", ["validate"] + files),
        ),
        LinterCommand(
            available=lambda: is_command_available("tflint"),
            command=lambda files: ("tflint", ["--quiet"] + files),
        ),
    ],
    ".dockerfile": [
        LinterCommand(
            available=lambda: is_command_available("hadolint"),
            command=lambda files: ("hadolint", ["--quiet"] + files),
        ),
    ],
    ".github-workflow": [
        LinterCommand(
            available=lambda: is_command_available("actionlint"),
            command=lambda files: ("actionlint", ["-quiet"] + files),
        ),
        LinterCommand(
            available=lambda: is_command_available("yamllint"),
            command=lambda files: ("yamllint", ["--quiet"] + files),
        ),
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: (
                "prettier",
                ["--check", "--log-level", "error"] + files,
            ),
        ),
    ],
}

# FormatterConfig maps file extensions to sequences of formatter commands to try in order
FORMATTER_MAP: Dict[str, List[LinterCommand]] = {
    ".py": [
        LinterCommand(
            available=lambda: is_command_available("ruff"),
            command=lambda files: ("ruff", ["format", "--quiet"] + files),
            supports_directories=True,
        ),
        LinterCommand(
            available=lambda: is_command_available("uvx"),
            command=lambda files: ("uvx", ["ruff", "format", "--quiet"] + files),
            supports_directories=True,
        ),
        LinterCommand(
            available=lambda: is_command_available("black"),
            command=lambda files: ("black", ["--quiet"] + files),
            supports_directories=True,
        ),
    ],
    ".js": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: (
                "prettier",
                ["--write", "--log-level", "error"] + files,
            ),
            supports_directories=True,
        ),
    ],
    ".jsx": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: (
                "prettier",
                ["--write", "--log-level", "error"] + files,
            ),
            supports_directories=True,
        ),
    ],
    ".ts": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: (
                "prettier",
                ["--write", "--log-level", "error"] + files,
            ),
            supports_directories=True,
        ),
    ],
    ".tsx": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: (
                "prettier",
                ["--write", "--log-level", "error"] + files,
            ),
            supports_directories=True,
        ),
    ],
    ".json": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: (
                "prettier",
                ["--write", "--log-level", "error"] + files,
            ),
            supports_directories=True,
        ),
    ],
    ".css": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: (
                "prettier",
                ["--write", "--log-level", "error"] + files,
            ),
            supports_directories=True,
        ),
    ],
    ".scss": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: (
                "prettier",
                ["--write", "--log-level", "error"] + files,
            ),
            supports_directories=True,
        ),
    ],
    ".html": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: (
                "prettier",
                ["--write", "--log-level", "error"] + files,
            ),
            supports_directories=True,
        ),
    ],
    ".md": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: (
                "prettier",
                ["--write", "--log-level", "error"] + files,
            ),
            supports_directories=True,
        ),
    ],
    ".go": [
        LinterCommand(
            available=lambda: is_command_available("gofmt"),
            command=lambda files: ("gofmt", ["-w"] + files),
            supports_directories=True,
        ),
    ],
    ".rs": [
        LinterCommand(
            available=lambda: is_command_available("rustfmt"),
            command=lambda files: ("rustfmt", ["--quiet"] + files),
            supports_directories=True,
        ),
    ],
    ".rb": [
        LinterCommand(
            available=lambda: is_command_available("rubocop"),
            command=lambda files: ("rubocop", ["-a", "--quiet"] + files),
            supports_directories=True,
        ),
    ],
    ".php": [
        LinterCommand(
            available=lambda: is_command_available("php-cs-fixer"),
            command=lambda files: ("php-cs-fixer", ["fix", "--quiet"] + files),
        ),
    ],
    ".sh": [
        LinterCommand(
            available=lambda: is_command_available("shfmt"),
            command=lambda files: ("shfmt", ["-w"] + files),
        ),
        LinterCommand(
            available=lambda: is_command_available("beautysh"),
            command=lambda files: ("beautysh", files),
        ),
    ],
    ".bash": [
        LinterCommand(
            available=lambda: is_command_available("shfmt"),
            command=lambda files: ("shfmt", ["-w"] + files),
        ),
        LinterCommand(
            available=lambda: is_command_available("beautysh"),
            command=lambda files: ("beautysh", files),
        ),
    ],
    ".zsh": [
        LinterCommand(
            available=lambda: is_command_available("shfmt"),
            command=lambda files: ("shfmt", ["-w"] + files),
        ),
        LinterCommand(
            available=lambda: is_command_available("beautysh"),
            command=lambda files: ("beautysh", files),
        ),
    ],
    ".yaml": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: (
                "prettier",
                ["--write", "--log-level", "error"] + files,
            ),
            supports_directories=True,
        ),
    ],
    ".yml": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: (
                "prettier",
                ["--write", "--log-level", "error"] + files,
            ),
            supports_directories=True,
        ),
    ],
    ".toml": [
        LinterCommand(
            available=lambda: is_command_available("taplo"),
            command=lambda files: ("taplo", ["format"] + files),
        ),
    ],
    ".tf": [
        LinterCommand(
            available=lambda: is_command_available("terraform"),
            command=lambda files: ("terraform", ["fmt"] + files),
        ),
    ],
    ".tfvars": [
        LinterCommand(
            available=lambda: is_command_available("terraform"),
            command=lambda files: ("terraform", ["fmt"] + files),
        ),
    ],
    ".github-workflow": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: (
                "prettier",
                ["--write", "--log-level", "error"] + files,
            ),
            supports_directories=True,
        ),
    ],
}


def show_usage() -> None:
    """Show usage information"""
    print(USAGE_TEXT, file=sys.stderr)


def show_help() -> None:
    """Show detailed help information"""
    print("Taidy - Smart linter/formatter with automatic tool detection\n")
    show_usage()
    print(f"\n{DIRECTORY_PROCESSING_TEXT}")
    print(f"\n{SUPPORTED_LANGUAGES_TEXT}")
    print(f"\n{CONFIGURATION_TEXT}")


def show_version() -> None:
    """Show version information"""
    print(f"Taidy {VERSION}")
    if GIT_COMMIT != "unknown":
        print(f"Git commit: {GIT_COMMIT}")
    if BUILD_DATE != "unknown":
        print(f"Built: {BUILD_DATE}")


# Thread-safe output lock
output_lock = threading.Lock()


def execute_linters(commands: List[LinterCommand], file_list: List[str]) -> int:
    """Try each command in order until one is available"""
    for linter_cmd in commands:
        if linter_cmd.available():
            cmd, args = linter_cmd.command(file_list)

            with output_lock:
                logger.info(f"Running: {cmd} {' '.join(args)}")

            try:
                result = subprocess.run([cmd] + args, capture_output=True, text=True)

                # Print output atomically to avoid mixing
                with output_lock:
                    if result.stdout:
                        print(result.stdout, end="", flush=True)
                    if result.stderr:
                        print(result.stderr, end="", file=sys.stderr, flush=True)

                return result.returncode
            except FileNotFoundError:
                with output_lock:
                    logger.error(f"Error executing {cmd}: command not found")
                return 127  # Standard exit code for command not found
            except Exception as e:
                with output_lock:
                    logger.error(f"Error executing {cmd}: {e}")
                return 1  # General error

    return 2  # No available command found


def process_file_group(
    ext: str,
    file_list: List[str],
    mode: Mode,
    original_dirs: Optional[List[str]] = None,
    has_custom_ignores: bool = False,
) -> int:
    """Process a group of files with the same extension"""
    exit_code = 0

    if mode in [Mode.LINT, Mode.BOTH]:
        if ext in LINTER_MAP:
            # Check if we can use directory processing for linters
            inputs = file_list
            if original_dirs and not has_custom_ignores:
                # Find the first available linter that supports directories
                for linter_cmd in LINTER_MAP[ext]:
                    if linter_cmd.available() and linter_cmd.supports_directories:
                        inputs = original_dirs
                        break

            result = execute_linters(LINTER_MAP[ext], inputs)
            if result == 2:
                with output_lock:
                    logger.warning(f"No available linter found for {ext} files")
            elif result != 0:
                exit_code = result

    if mode in [Mode.FORMAT, Mode.BOTH]:
        if ext in FORMATTER_MAP:
            # Check if we can use directory processing for formatters
            inputs = file_list
            if original_dirs and not has_custom_ignores:
                # Find the first available formatter that supports directories
                for formatter_cmd in FORMATTER_MAP[ext]:
                    if formatter_cmd.available() and formatter_cmd.supports_directories:
                        inputs = original_dirs
                        break

            result = execute_linters(FORMATTER_MAP[ext], inputs)
            if result == 2:
                with output_lock:
                    logger.warning(f"No available formatter found for {ext} files")
            elif result != 0:
                exit_code = result

    return exit_code


def process_files(files: List[str], mode: Mode) -> int:
    """Process files according to the specified mode"""
    # Track which inputs were directories for potential direct passing to formatters
    input_directories = [f for f in files if os.path.isdir(f) and os.path.exists(f)]

    # Check if we have custom ignore patterns (beyond the defaults)
    config = load_config(".")
    config_ignores = config.get("ignore", [])
    has_custom_ignores = len(config_ignores) > 0

    # Expand directories to files
    expanded_files = []
    for file_or_dir in files:
        if not os.path.exists(file_or_dir):
            logger.warning(f"Path {file_or_dir} does not exist, skipping")
            continue

        if os.path.isdir(file_or_dir):
            discovered = discover_files_in_directory(file_or_dir)
            if discovered:
                logger.info(f"Discovered {len(discovered)} supported files in {file_or_dir}")
                expanded_files.extend(discovered)
            else:
                logger.warning(f"No supported files found in directory {file_or_dir}")
        else:
            expanded_files.append(file_or_dir)

    # Group files by their file extension
    file_groups: Dict[str, List[str]] = {}

    for file in expanded_files:
        file_path = Path(file)
        ext = file_path.suffix.lower()

        # Handle special cases for file mapping
        mapped_ext = ext

        # Special case: Dockerfile files without extension
        if file_path.name.lower() == "dockerfile":
            mapped_ext = ".dockerfile"

        # Special case: GitHub Actions workflow files
        if ext in [".yml", ".yaml"] and ".github/workflows" in str(file_path):
            mapped_ext = ".github-workflow"

        # Check if we have configuration for this extension based on mode
        has_config = False
        if mode == Mode.LINT:
            has_config = mapped_ext in LINTER_MAP
        elif mode == Mode.FORMAT:
            has_config = mapped_ext in FORMATTER_MAP
        elif mode == Mode.BOTH:
            has_config = mapped_ext in LINTER_MAP or mapped_ext in FORMATTER_MAP

        if has_config:
            if mapped_ext not in file_groups:
                file_groups[mapped_ext] = []
            file_groups[mapped_ext].append(file)
        else:
            logger.warning(f"No linter configured for file {file} (extension: {ext})")

    # Check if any files will be processed
    if not file_groups:
        logger.info("No supported files provided, no files were linted")
        return 0

    # Execute linters/formatters for each file extension in parallel
    exit_code = 0

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=min(len(file_groups), os.cpu_count() or 1)) as executor:
        # Submit all file groups for processing
        future_to_ext = {
            executor.submit(
                process_file_group,
                ext,
                file_list,
                mode,
                input_directories or None,
                has_custom_ignores,
            ): ext
            for ext, file_list in file_groups.items()
        }

        # Collect results as they complete
        for future in as_completed(future_to_ext):
            ext = future_to_ext[future]
            try:
                result = future.result()
                if result != 0:
                    exit_code = result
            except Exception as e:
                with output_lock:
                    logger.error(f"Error processing {ext} files: {e}")
                exit_code = 1

    return exit_code


def main() -> None:
    """Main entry point"""
    setup_logging()

    if len(sys.argv) < 2:
        show_usage()
        sys.exit(1)

    # Handle version and help flags
    arg = sys.argv[1]
    if arg in ["-v", "--version"]:
        show_version()
        sys.exit(0)
    elif arg in ["-h", "--help"]:
        show_help()
        sys.exit(0)

    # Parse command and files
    mode = Mode.BOTH
    files = []

    if sys.argv[1] == "lint":
        mode = Mode.LINT
        if len(sys.argv) < 3:
            show_usage()
            sys.exit(1)
        files = sys.argv[2:]
    elif sys.argv[1] == "format":
        mode = Mode.FORMAT
        if len(sys.argv) < 3:
            show_usage()
            sys.exit(1)
        files = sys.argv[2:]
    else:
        # No subcommand, treat first arg as file
        mode = Mode.BOTH
        files = sys.argv[1:]

    exit_code = process_files(files, mode)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
