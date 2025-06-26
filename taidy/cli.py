#!/usr/bin/env python3
"""Taidy CLI - Smart linter/formatter with automatic tool detection."""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from enum import Enum
from typing import List, Dict, Tuple, Callable, Optional
from dataclasses import dataclass

# Version information - can be overridden at build time
VERSION = "0.1.0"
GIT_COMMIT = "unknown"
BUILD_DATE = "unknown"

class Mode(Enum):
    BOTH = "both"      # Both lint and format
    LINT = "lint"      # Lint only
    FORMAT = "format"  # Format only

@dataclass
class LinterCommand:
    """Represents a linter command that can be tried"""
    available: Callable[[], bool]
    command: Callable[[List[str]], Tuple[str, List[str]]]

def is_command_available(cmd: str) -> bool:
    """Check if a command is available in PATH"""
    return shutil.which(cmd) is not None

# LinterConfig maps file extensions to sequences of linter commands to try in order
LINTER_MAP: Dict[str, List[LinterCommand]] = {
    ".py": [
        LinterCommand(
            available=lambda: is_command_available("ruff"),
            command=lambda files: ("ruff", ["check", "--quiet"] + files)
        ),
        LinterCommand(
            available=lambda: is_command_available("uvx"),
            command=lambda files: ("uvx", ["ruff", "check", "--quiet"] + files)
        ),
        LinterCommand(
            available=lambda: is_command_available("black"),
            command=lambda files: ("black", ["--check", "--quiet"] + files)
        ),
        LinterCommand(
            available=lambda: is_command_available("flake8"),
            command=lambda files: ("flake8", ["--quiet"] + files)
        ),
        LinterCommand(
            available=lambda: is_command_available("pylint"),
            command=lambda files: ("pylint", ["--quiet"] + files)
        ),
        LinterCommand(
            available=lambda: is_command_available("python"),
            command=lambda files: ("python", ["-m", "py_compile"] + files)
        ),
    ],
    ".js": [
        LinterCommand(
            available=lambda: is_command_available("eslint"),
            command=lambda files: ("eslint", ["--quiet"] + files)
        ),
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: ("prettier", ["--check", "--loglevel", "error"] + files)
        ),
        LinterCommand(
            available=lambda: is_command_available("node"),
            command=lambda files: ("node", ["--check"] + files)
        ),
    ],
    ".jsx": [
        LinterCommand(
            available=lambda: is_command_available("eslint"),
            command=lambda files: ("eslint", ["--quiet"] + files)
        ),
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: ("prettier", ["--check", "--loglevel", "error"] + files)
        ),
    ],
    ".ts": [
        LinterCommand(
            available=lambda: is_command_available("eslint"),
            command=lambda files: ("eslint", ["--quiet"] + files)
        ),
        LinterCommand(
            available=lambda: is_command_available("tsc"),
            command=lambda files: ("tsc", ["--noEmit"] + files)
        ),
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: ("prettier", ["--check", "--loglevel", "error"] + files)
        ),
    ],
    ".tsx": [
        LinterCommand(
            available=lambda: is_command_available("eslint"),
            command=lambda files: ("eslint", ["--quiet"] + files)
        ),
        LinterCommand(
            available=lambda: is_command_available("tsc"),
            command=lambda files: ("tsc", ["--noEmit"] + files)
        ),
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: ("prettier", ["--check", "--loglevel", "error"] + files)
        ),
    ],
    ".json": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: ("prettier", ["--check", "--loglevel", "error"] + files)
        ),
    ],
    ".css": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: ("prettier", ["--check", "--loglevel", "error"] + files)
        ),
    ],
    ".scss": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: ("prettier", ["--check", "--loglevel", "error"] + files)
        ),
    ],
    ".html": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: ("prettier", ["--check", "--loglevel", "error"] + files)
        ),
    ],
    ".md": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: ("prettier", ["--check", "--loglevel", "error"] + files)
        ),
    ],
    ".go": [
        LinterCommand(
            available=lambda: is_command_available("gofmt"),
            command=lambda files: ("gofmt", ["-l"] + files)
        ),
    ],
    ".rs": [
        LinterCommand(
            available=lambda: is_command_available("rustfmt"),
            command=lambda files: ("rustfmt", ["--check", "--quiet"] + files)
        ),
    ],
    ".rb": [
        LinterCommand(
            available=lambda: is_command_available("rubocop"),
            command=lambda files: ("rubocop", ["--quiet"] + files)
        ),
    ],
    ".php": [
        LinterCommand(
            available=lambda: is_command_available("php-cs-fixer"),
            command=lambda files: ("php-cs-fixer", ["fix", "--dry-run", "--quiet"] + files)
        ),
    ],
    ".sql": [
        LinterCommand(
            available=lambda: is_command_available("sqlfluff"),
            command=lambda files: ("sqlfluff", ["lint", "--dialect", "ansi"] + files)
        ),
        LinterCommand(
            available=lambda: is_command_available("uvx"),
            command=lambda files: ("uvx", ["sqlfluff", "lint", "--dialect", "ansi"] + files)
        ),
    ],
    ".sh": [
        LinterCommand(
            available=lambda: is_command_available("shellcheck"),
            command=lambda files: ("shellcheck", ["--quiet"] + files)
        ),
        LinterCommand(
            available=lambda: is_command_available("beautysh"),
            command=lambda files: ("beautysh", ["--check"] + files)
        ),
    ],
    ".bash": [
        LinterCommand(
            available=lambda: is_command_available("shellcheck"),
            command=lambda files: ("shellcheck", ["--quiet"] + files)
        ),
        LinterCommand(
            available=lambda: is_command_available("beautysh"),
            command=lambda files: ("beautysh", ["--check"] + files)
        ),
    ],
    ".zsh": [
        LinterCommand(
            available=lambda: is_command_available("shellcheck"),
            command=lambda files: ("shellcheck", ["--quiet"] + files)
        ),
        LinterCommand(
            available=lambda: is_command_available("beautysh"),
            command=lambda files: ("beautysh", ["--check"] + files)
        ),
    ],
}

# FormatterConfig maps file extensions to sequences of formatter commands to try in order
FORMATTER_MAP: Dict[str, List[LinterCommand]] = {
    ".py": [
        LinterCommand(
            available=lambda: is_command_available("ruff"),
            command=lambda files: ("ruff", ["format", "--quiet"] + files)
        ),
        LinterCommand(
            available=lambda: is_command_available("uvx"),
            command=lambda files: ("uvx", ["ruff", "format", "--quiet"] + files)
        ),
        LinterCommand(
            available=lambda: is_command_available("black"),
            command=lambda files: ("black", ["--quiet"] + files)
        ),
    ],
    ".js": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: ("prettier", ["--write", "--loglevel", "error"] + files)
        ),
    ],
    ".jsx": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: ("prettier", ["--write", "--loglevel", "error"] + files)
        ),
    ],
    ".ts": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: ("prettier", ["--write", "--loglevel", "error"] + files)
        ),
    ],
    ".tsx": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: ("prettier", ["--write", "--loglevel", "error"] + files)
        ),
    ],
    ".json": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: ("prettier", ["--write", "--loglevel", "error"] + files)
        ),
    ],
    ".css": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: ("prettier", ["--write", "--loglevel", "error"] + files)
        ),
    ],
    ".scss": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: ("prettier", ["--write", "--loglevel", "error"] + files)
        ),
    ],
    ".html": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: ("prettier", ["--write", "--loglevel", "error"] + files)
        ),
    ],
    ".md": [
        LinterCommand(
            available=lambda: is_command_available("prettier"),
            command=lambda files: ("prettier", ["--write", "--loglevel", "error"] + files)
        ),
    ],
    ".go": [
        LinterCommand(
            available=lambda: is_command_available("gofmt"),
            command=lambda files: ("gofmt", ["-w"] + files)
        ),
    ],
    ".rs": [
        LinterCommand(
            available=lambda: is_command_available("rustfmt"),
            command=lambda files: ("rustfmt", ["--quiet"] + files)
        ),
    ],
    ".rb": [
        LinterCommand(
            available=lambda: is_command_available("rubocop"),
            command=lambda files: ("rubocop", ["-a", "--quiet"] + files)
        ),
    ],
    ".php": [
        LinterCommand(
            available=lambda: is_command_available("php-cs-fixer"),
            command=lambda files: ("php-cs-fixer", ["fix", "--quiet"] + files)
        ),
    ],
    ".sql": [
        LinterCommand(
            available=lambda: is_command_available("sqlfluff"),
            command=lambda files: ("sqlfluff", ["format", "--dialect", "ansi"] + files)
        ),
        LinterCommand(
            available=lambda: is_command_available("uvx"),
            command=lambda files: ("uvx", ["sqlfluff", "format", "--dialect", "ansi"] + files)
        ),
    ],
    ".sh": [
        LinterCommand(
            available=lambda: is_command_available("shfmt"),
            command=lambda files: ("shfmt", ["-w"] + files)
        ),
        LinterCommand(
            available=lambda: is_command_available("beautysh"),
            command=lambda files: ("beautysh", files)
        ),
    ],
    ".bash": [
        LinterCommand(
            available=lambda: is_command_available("shfmt"),
            command=lambda files: ("shfmt", ["-w"] + files)
        ),
        LinterCommand(
            available=lambda: is_command_available("beautysh"),
            command=lambda files: ("beautysh", files)
        ),
    ],
    ".zsh": [
        LinterCommand(
            available=lambda: is_command_available("shfmt"),
            command=lambda files: ("shfmt", ["-w"] + files)
        ),
        LinterCommand(
            available=lambda: is_command_available("beautysh"),
            command=lambda files: ("beautysh", files)
        ),
    ],
}

def show_usage():
    """Show usage information"""
    prog_name = "taidy"
    print(f"Usage: {prog_name} [command] <file1> <file2> ...", file=sys.stderr)
    print("\nCommands:", file=sys.stderr)
    print("  lint     Lint files only (no formatting)", file=sys.stderr)
    print("  format   Format files only (no linting)", file=sys.stderr)
    print("  (none)   Both lint and format (default)", file=sys.stderr)
    print("\nFlags:", file=sys.stderr)
    print("  -h, --help     Show this help message", file=sys.stderr)
    print("  -v, --version  Show version information", file=sys.stderr)

def show_help():
    """Show detailed help information"""
    print("Taidy - Smart linter/formatter with automatic tool detection\n")
    show_usage()
    print("\nSupported file types and linters:")
    print("  Python:     ruff → uvx ruff → black → flake8 → pylint → python -m py_compile")
    print("  JavaScript: eslint → prettier → node --check")
    print("  TypeScript: eslint → tsc --noEmit → prettier")
    print("  Go:         gofmt")
    print("  Rust:       rustfmt")
    print("  Ruby:       rubocop")
    print("  PHP:        php-cs-fixer")
    print("  SQL:        sqlfluff → uvx sqlfluff")
    print("  Shell:      shellcheck → beautysh (linting), shfmt → beautysh (formatting)")
    print("  JSON/CSS:   prettier")
    print("\nTaidy automatically detects which linters are available and uses the best one for each file type.")

def show_version():
    """Show version information"""
    print(f"Taidy {VERSION}")
    if GIT_COMMIT != "unknown":
        print(f"Git commit: {GIT_COMMIT}")
    if BUILD_DATE != "unknown":
        print(f"Built: {BUILD_DATE}")

def execute_linters(commands: List[LinterCommand], file_list: List[str]) -> bool:
    """Try each command in order until one is available"""
    for linter_cmd in commands:
        if linter_cmd.available():
            cmd, args = linter_cmd.command(file_list)
            
            print(f"Running: {cmd} {' '.join(args)}", flush=True)
            
            try:
                result = subprocess.run([cmd] + args, capture_output=False)
                # We don't check exit code here - let the tool output speak for itself
            except FileNotFoundError:
                print(f"Error executing {cmd}: command not found", file=sys.stderr, flush=True)
            except Exception as e:
                print(f"Error executing {cmd}: {e}", file=sys.stderr, flush=True)
            
            return True  # Executed successfully
    
    return False  # No available command found

def process_files(files: List[str], mode: Mode) -> int:
    """Process files according to the specified mode"""
    # Group files by their file extension
    file_groups: Dict[str, List[str]] = {}
    
    for file in files:
        # Check if file exists
        if not os.path.exists(file):
            print(f"Warning: File {file} does not exist, skipping")
            continue
        
        ext = Path(file).suffix.lower()
        
        # Check if we have configuration for this extension based on mode
        has_config = False
        if mode == Mode.LINT:
            has_config = ext in LINTER_MAP
        elif mode == Mode.FORMAT:
            has_config = ext in FORMATTER_MAP
        elif mode == Mode.BOTH:
            has_config = ext in LINTER_MAP or ext in FORMATTER_MAP
        
        if has_config:
            if ext not in file_groups:
                file_groups[ext] = []
            file_groups[ext].append(file)
        else:
            print(f"Warning: No linter configured for file {file} (extension: {ext})")
    
    # Check if any files will be processed
    if not file_groups:
        print("No supported files provided, no files were linted")
        return 0
    
    # Execute linters/formatters for each file extension
    exit_code = 0
    for ext, file_list in file_groups.items():
        if mode in [Mode.LINT, Mode.BOTH]:
            if ext in LINTER_MAP:
                executed = execute_linters(LINTER_MAP[ext], file_list)
                if not executed:
                    print(f"Warning: No available linter found for {ext} files")
        
        if mode in [Mode.FORMAT, Mode.BOTH]:
            if ext in FORMATTER_MAP:
                executed = execute_linters(FORMATTER_MAP[ext], file_list)
                if not executed:
                    print(f"Warning: No available formatter found for {ext} files")
    
    return exit_code

def main():
    """Main entry point"""
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