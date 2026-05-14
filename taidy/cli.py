#!/usr/bin/env python3
"""Taidy CLI - Smart linter/formatter with automatic tool detection."""

import fnmatch
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from taidy import __version__ as VERSION

# Help text constants
USAGE_TEXT = """
Usage: taidy [flags] [command] <files_or_directories...>

Commands:
  lint       Lint files only (no formatting)
  format     Format files only (no linting)
  suggest    Analyze project and suggest tools to install
  bootstrap  Install uv and node to ~/.cache/taidy (only if missing)
  docker     Run taidy in Docker with all tools pre-installed
  (none)     Both lint and format (default)

Flags:
  -h, --help     Show this help message
  --version      Show version information
  -q, --quiet    Suppress warnings (errors only)
  --verbose      Show verbose output (info level)
  --json         Output results as JSON (for automation)
  --dry-run      Show what would be run without executing

Examples:
  taidy file.py          # Lint and format a single file
  taidy .                # Process current directory
  taidy lint src/        # Lint only
  taidy --json .         # JSON output for automation
  taidy suggest          # Show missing tools

Supported: Python, JS/TS, Go, Rust, Ruby, PHP, Shell, JSON, CSS, HTML, YAML, TOML, Terraform"""

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
  Jinja HTML:   djlint
  HTML:         prettier
  YAML:         yamllint → prettier
  TOML:         taplo check → taplo format
  Terraform:    terraform validate/tflint → terraform fmt
  Makefile:     mbake format
  Justfile:     just --fmt --check → just --fmt
  GitHub Actions: actionlint → yamllint → prettier (.github/workflows/*.yml)
  Security:     trufflehog (scans for secrets across all file types)

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

JUSTFILE_NAMES: Set[str] = {"justfile", "justfile.just"}
MAKEFILE_NAMES: Set[str] = {"makefile", "gnumakefile"}
JINJA_HTML_SUFFIX = ".jinja.html"

# Extensions eligible for security scanning (trufflehog)
SECURITY_EXTENSIONS: Set[str] = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".sh",
    ".bash",
    ".zsh",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".tf",
    ".tfvars",
    ".env",
    ".txt",
    ".md",
    ".sql",
    ".xml",
    ".html",
    ".css",
}

# Extensions that are inherently unlintable/unformattable (binary/opaque assets)
ALWAYS_UNFORMATTABLE_EXTENSIONS: Set[str] = {
    ".txt",
    ".log",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".class",
    ".o",
    ".obj",
    ".wasm",
    ".zip",
    ".tar",
    ".gz",
    ".tgz",
    ".rar",
    ".7z",
    ".dmg",
    ".iso",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".svg",
    ".ico",
    ".bmp",
    ".psd",
    ".ai",
    ".tif",
    ".tiff",
    ".mp3",
    ".wav",
    ".flac",
    ".aac",
    ".m4a",
    ".ogg",
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".ttf",
    ".otf",
    ".woff",
    ".woff2",
    ".eot",
    ".bin",
    ".dat",
    ".img",
}


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Setup logging to stdout with appropriate format"""
    # Only setup if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(levelname)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Set log level based on verbosity flags
        if quiet:
            logger.setLevel(logging.ERROR)
        elif verbose:
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.WARNING)


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


@dataclass
class ProcessingResult:
    """Result of processing files"""

    files_processed: int
    exit_code: int
    tools_used: List[str]
    errors: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "files_processed": self.files_processed,
            "exit_code": self.exit_code,
            "tools_used": self.tools_used,
            "errors": self.errors,
        }


# Cache for command availability to avoid repeated shutil.which() calls
_command_availability_cache: Dict[str, bool] = {}


def is_command_available(cmd: str) -> bool:
    """Check if a command is available in PATH, with caching"""
    if cmd not in _command_availability_cache:
        _command_availability_cache[cmd] = shutil.which(cmd) is not None
    return _command_availability_cache[cmd]


def _taidy_cache_dir() -> Path:
    cache_root = os.environ.get("XDG_CACHE_HOME")
    if cache_root:
        return Path(cache_root) / "taidy"
    return Path.home() / ".cache" / "taidy"


def _find_nvm_node_bin() -> Optional[Path]:
    """Find the bin directory of the node version installed by nvm in our cache."""
    nvm_dir = _taidy_cache_dir() / "nvm"
    versions_dir = nvm_dir / "versions" / "node"
    if not versions_dir.exists():
        return None
    # Pick the first (usually only) installed version
    for version_dir in sorted(versions_dir.iterdir(), reverse=True):
        bin_dir = version_dir / "bin"
        if bin_dir.exists() and (bin_dir / "node").exists():
            return bin_dir
    return None


def _add_bootstrapped_paths() -> None:
    """Add bootstrapped tool directories to PATH so is_command_available finds them."""
    path_dirs = []

    # uv bin dir
    uv_bin = _taidy_cache_dir() / "uv" / "bin"
    if uv_bin.exists():
        path_dirs.append(str(uv_bin))

    # node bin dir (installed via nvm)
    node_bin = _find_nvm_node_bin()
    if node_bin:
        path_dirs.append(str(node_bin))

    if path_dirs:
        current_path = os.environ.get("PATH", "")
        os.environ["PATH"] = os.pathsep.join(path_dirs) + os.pathsep + current_path


def _download(url: str) -> str:
    """Download a URL and return the content as a string. Uses curl or wget."""
    if shutil.which("curl"):
        result = subprocess.run(["curl", "-fsSL", url], capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(f"curl failed: {result.stderr}")
        return result.stdout
    elif shutil.which("wget"):
        result = subprocess.run(["wget", "-qO-", url], capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(f"wget failed: {result.stderr}")
        return result.stdout
    else:
        raise RuntimeError("Neither curl nor wget is available")


def bootstrap_uv() -> bool:
    """Install uv to the taidy cache directory. Returns True if installed."""
    install_dir = _taidy_cache_dir() / "uv" / "bin"
    uv_bin = install_dir / "uv"

    if uv_bin.exists():
        print(f"  uv: already installed at {uv_bin}")
        return False

    print("  uv: installing...")
    install_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["UV_INSTALL_DIR"] = str(install_dir)
    env["UV_NO_MODIFY_PATH"] = "1"

    script = _download("https://astral.sh/uv/install.sh")
    result = subprocess.run(
        ["sh"], input=script, capture_output=True, text=True, env=env, timeout=120
    )
    if result.returncode != 0:
        raise RuntimeError(f"uv installer failed: {result.stderr}")

    if not uv_bin.exists():
        raise RuntimeError(f"uv installer completed but {uv_bin} not found")

    print(f"  uv: installed to {uv_bin}")
    return True


def bootstrap_node() -> bool:
    """Install nvm and node to the taidy cache directory. Returns True if installed."""
    nvm_dir = _taidy_cache_dir() / "nvm"
    nvm_sh = nvm_dir / "nvm.sh"

    # Check if node is already available via our nvm install
    node_bin = _find_nvm_node_bin()
    if node_bin and (node_bin / "node").exists():
        print(f"  node: already installed at {node_bin / 'node'}")
        return False

    print("  nvm: installing...")
    nvm_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["NVM_DIR"] = str(nvm_dir)
    env["PROFILE"] = "/dev/null"  # Don't modify shell profiles

    script = _download("https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh")
    result = subprocess.run(
        ["sh"], input=script, capture_output=True, text=True, env=env, timeout=120
    )
    if result.returncode != 0:
        raise RuntimeError(f"nvm installer failed: {result.stderr}")

    if not nvm_sh.exists():
        raise RuntimeError(f"nvm installer completed but {nvm_sh} not found")

    print("  nvm: installed")

    # Now install the latest LTS node using nvm
    print("  node: installing LTS version...")
    install_cmd = f'source "{nvm_sh}" && nvm install --lts'
    result = subprocess.run(
        ["bash", "-c", install_cmd],
        capture_output=True,
        text=True,
        env=env,
        timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(f"node installation failed: {result.stderr}")

    node_bin = _find_nvm_node_bin()
    if not node_bin:
        raise RuntimeError("node installation completed but node binary not found")

    print(f"  node: installed to {node_bin / 'node'}")
    return True


def bootstrap() -> int:
    """Install missing tools (uv, node) to the taidy cache directory."""
    cache_dir = _taidy_cache_dir()
    print(f"Taidy bootstrap (cache: {cache_dir})")
    print()

    installed = []
    skipped = []

    # Check what's already available system-wide
    checks = [
        ("uv", ["uv", "uvx"], bootstrap_uv),
        ("node", ["node", "npm", "npx"], bootstrap_node),
    ]

    for name, commands, installer in checks:
        # If all commands are already on PATH, skip
        all_available = all(shutil.which(cmd) is not None for cmd in commands)
        if all_available:
            print(f"  {name}: already available on system PATH")
            skipped.append(name)
            continue

        try:
            did_install = installer()
            if did_install:
                installed.append(name)
            else:
                skipped.append(name)
        except RuntimeError as e:
            print(f"  {name}: FAILED - {e}", file=sys.stderr)
            return 1

    # Update PATH so subsequent commands find the new tools
    _add_bootstrapped_paths()

    print()
    if installed:
        print(f"Installed: {', '.join(installed)}")
    if skipped:
        print(f"Already available: {', '.join(skipped)}")
    if not installed:
        print("Nothing to install.")

    return 0


def _ensure_prettier_pug_install() -> Tuple[Path, Path]:
    cache_dir = _taidy_cache_dir() / "prettier-pug"
    prettier_bin = cache_dir / "node_modules" / "prettier" / "bin" / "prettier.cjs"
    plugin_file = cache_dir / "node_modules" / "@prettier" / "plugin-pug" / "dist" / "index.js"
    if not (prettier_bin.exists() and plugin_file.exists()):
        cache_dir.mkdir(parents=True, exist_ok=True)
        if not is_command_available("npm"):
            raise RuntimeError("npm is required to install prettier and @prettier/plugin-pug")
        subprocess.run(
            [
                "npm",
                "install",
                "--no-save",
                "--prefix",
                str(cache_dir),
                "prettier",
                "@prettier/plugin-pug",
            ],
            check=True,
        )
    return prettier_bin, plugin_file


def _pug_prettier_command(files: List[str]) -> Tuple[str, List[str]]:
    prettier_bin, plugin_file = _ensure_prettier_pug_install()
    return (
        "node",
        [
            str(prettier_bin),
            "--write",
            "--log-level",
            "error",
            "--plugin",
            str(plugin_file),
        ]
        + files,
    )


def detect_linux_distribution() -> Optional[Dict[str, str]]:
    """Detect Linux distribution using /etc/os-release file"""
    try:
        os_release_path = Path("/etc/os-release")
        if not os_release_path.exists():
            return None

        with open(os_release_path, "r") as f:
            content = f.read()

        # Parse os-release file
        info = {}
        for line in content.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                # Remove quotes from value
                value = value.strip('"').strip("'")
                info[key] = value

        # Map common distribution identifiers
        distribution_map = {
            "ubuntu": "ubuntu",
            "debian": "debian",
            "fedora": "fedora",
            "rhel": "rhel",
            "centos": "centos",
            "arch": "arch",
            "manjaro": "arch",  # Manjaro is Arch-based
            "opensuse": "opensuse",
            "suse": "opensuse",
            "alpine": "alpine",
        }

        # Try to identify distribution
        distribution = None
        if "ID" in info:
            distribution = distribution_map.get(info["ID"].lower())

        if not distribution and "ID_LIKE" in info:
            # Check ID_LIKE for derivative distributions
            for id_like in info["ID_LIKE"].split():
                distribution = distribution_map.get(id_like.lower())
                if distribution:
                    break

        if not distribution:
            distribution = "generic"

        return {
            "distribution": distribution,
            "version": info.get("VERSION_ID", ""),
            "name": info.get("NAME", ""),
            "pretty_name": info.get("PRETTY_NAME", ""),
        }
    except Exception:
        return None


def get_platform_info() -> Dict[str, Any]:
    """Get platform information including OS type and Linux distribution details"""
    system = platform.system().lower()

    info = {
        "system": system,
        "distribution": None,
        "version": "",
        "name": "",
        "pretty_name": "",
    }

    if system == "linux":
        linux_info = detect_linux_distribution()
        if linux_info:
            info.update(linux_info)
    elif system == "darwin":
        info["pretty_name"] = "macOS"
    elif system == "windows":
        info["pretty_name"] = "Windows"

    return info


def is_git_repository(directory: Path) -> bool:
    """Check if a directory is inside a git repository"""
    return find_git_root(directory) is not None


def find_git_root(directory: Path) -> Optional[Path]:
    """Find the root of the git repository containing the directory"""
    current = directory.resolve()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return None


def get_git_ignored_files(git_root: Path) -> Set[Path]:
    """Get set of files ignored by git using git status --ignored"""
    ignored_files = set()

    try:
        result = subprocess.run(
            ["git", "status", "--ignored", "--porcelain=v1"],
            cwd=git_root,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.startswith("!!"):
                    # Remove the '!! ' prefix and get the file path
                    file_path = line[3:]
                    ignored_files.add(git_root / file_path)
    except Exception as e:
        logger.debug(f"Failed to get git ignored files: {e}")

    return ignored_files


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


def _get_logger_level() -> int:
    """Return a usable numeric log level even when logger is patched."""
    level = logger.getEffectiveLevel()
    if isinstance(level, int):
        return level
    return logging.WARNING


def _get_trufflehog_log_level() -> str:
    """Choose log level for trufflehog, keeping default runs quiet."""
    if _get_logger_level() <= logging.INFO:
        return "0"
    return "-1"


def _strip_trufflehog_banner(output: str) -> str:
    """Remove the banner line from trufflehog output."""
    if not output:
        return output

    banner_text = "TruffleHog. Unearth your secrets."
    filtered_lines = [line for line in output.splitlines() if banner_text not in line]

    if not filtered_lines:
        return ""

    joined = "\n".join(filtered_lines)
    if output.endswith("\n"):
        return joined + "\n"
    return joined


def _get_trufflehog_command(files: List[str]) -> Tuple[str, List[str]]:
    """Get the appropriate trufflehog command based on git repository status."""
    log_level = _get_trufflehog_log_level()
    log_level_arg = f"--log-level={log_level}"

    # Check if we're in a git repository
    current_dir = Path.cwd()
    if is_git_repository(current_dir):
        # Use git mode with max-depth=1 to scan current state while respecting gitignore
        # Use file:// URI for local git repository
        git_uri = current_dir.resolve().as_uri()
        return (
            "trufflehog",
            [
                "git",
                "--max-depth=1",
                "--no-update",
                "--fail",
                log_level_arg,
                git_uri,
            ],
        )
    else:
        # Use filesystem mode for non-git directories
        return (
            "trufflehog",
            ["filesystem", "--no-update", "--fail", log_level_arg] + files,
        )


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

    # Check if directory is in a git repository and get ignored files
    git_ignored_files = set()
    if is_git_repository(directory):
        git_root = find_git_root(directory)
        if git_root:
            git_ignored_files = get_git_ignored_files(git_root)

    for file_path in directory.rglob("*"):
        # Skip if it's not a file
        if not file_path.is_file():
            continue

        # Skip if file should be ignored by taidy patterns
        if should_ignore_file(file_path, all_ignore_patterns):
            continue

        # Skip if file should be ignored by git (only if we're in a git repo)
        if file_path.resolve() in git_ignored_files:
            continue

        # Check if extension is supported
        ext = file_path.suffix.lower()
        is_supported = ext in supported_extensions

        # Special case: Justfile files
        if not is_supported and file_path.name.lower() in JUSTFILE_NAMES:
            is_supported = True

        # Special case: Makefile files
        if not is_supported and file_path.name.lower() in MAKEFILE_NAMES:
            is_supported = True

        # Special case: GitHub Actions workflow files
        if not is_supported and file_path.suffix.lower() in [".yml", ".yaml"]:
            if ".github/workflows" in str(file_path):
                is_supported = True

        # Special case: Security scanning - include all files if trufflehog is available
        if not is_supported and is_command_available("trufflehog"):
            if ext in SECURITY_EXTENSIONS or file_path.name.startswith(".env"):
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
    ".jinja.html": [
        LinterCommand(
            available=lambda: is_command_available("djlint"),
            command=lambda files: ("djlint", ["--check"] + files),
            supports_directories=True,
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
            command=lambda files: ("shellcheck", ["-S", "warning"] + files),
        ),
        LinterCommand(
            available=lambda: is_command_available("beautysh"),
            command=lambda files: ("beautysh", ["--check"] + files),
        ),
    ],
    ".bash": [
        LinterCommand(
            available=lambda: is_command_available("shellcheck"),
            command=lambda files: ("shellcheck", ["-S", "warning"] + files),
        ),
        LinterCommand(
            available=lambda: is_command_available("beautysh"),
            command=lambda files: ("beautysh", ["--check"] + files),
        ),
    ],
    ".zsh": [
        LinterCommand(
            available=lambda: is_command_available("shellcheck"),
            command=lambda files: ("shellcheck", ["-S", "warning"] + files),
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
            command=lambda files: ("taplo", ["check"] + files),
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
    ".security": [
        LinterCommand(
            available=lambda: is_command_available("trufflehog"),
            command=lambda files: _get_trufflehog_command(files),
            supports_directories=True,
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
    ".jinja.html": [
        LinterCommand(
            available=lambda: is_command_available("djlint"),
            command=lambda files: ("djlint", ["--reformat"] + files),
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
    ".pug": [
        LinterCommand(
            available=lambda: is_command_available("node") and is_command_available("npm"),
            command=_pug_prettier_command,
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
    "makefile": [
        LinterCommand(
            available=lambda: is_command_available("mbake"),
            command=lambda files: ("mbake", ["format"] + files),
        ),
    ],
    "justfile": [
        LinterCommand(
            available=lambda: is_command_available("just"),
            command=lambda files: ("just", ["--fmt", "--unstable"]),
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


# Thread-safe output lock
output_lock = threading.Lock()


def execute_batched_command(
    cmd_signature: Tuple[str, Tuple[str, ...]], file_list: List[str]
) -> int:
    """Execute a batched command with deduplicated file list"""
    cmd, base_args = cmd_signature

    # Remove duplicates from file list while preserving order
    unique_files = []
    seen = set()
    for file in file_list:
        if file not in seen:
            seen.add(file)
            unique_files.append(file)

    # Special handling for commands that don't take file arguments
    if cmd == "just" and "--fmt" in base_args:
        # just --fmt operates on the justfile in the current directory
        args = list(base_args)
    elif cmd == "trufflehog" and "git" in base_args:
        # trufflehog git mode scans the repository, doesn't take file arguments
        args = list(base_args)
    else:
        # Build final command with files
        args = list(base_args) + unique_files

    with output_lock:
        logger.info(f"Running: {cmd} {' '.join(args)}")

    try:
        # Set environment for taplo to suppress info messages
        env = os.environ.copy()
        if cmd == "taplo":
            env["RUST_LOG"] = "warn"

        result = subprocess.run([cmd] + args, capture_output=True, text=True, env=env)

        suppress_output = (
            cmd == "trufflehog" and result.returncode == 0 and _get_logger_level() > logging.INFO
        )

        stdout = result.stdout
        stderr = result.stderr

        if cmd == "trufflehog" and not suppress_output and _get_logger_level() > logging.INFO:
            stdout = _strip_trufflehog_banner(stdout)
            stderr = _strip_trufflehog_banner(stderr)

        # Print output atomically to avoid mixing
        if not suppress_output:
            with output_lock:
                if stdout:
                    print(stdout, end="", flush=True)
                if stderr:
                    print(stderr, end="", file=sys.stderr, flush=True)

        return result.returncode
    except FileNotFoundError:
        with output_lock:
            logger.error(f"Error executing {cmd}: command not found")
        return 127  # Standard exit code for command not found
    except Exception as e:
        with output_lock:
            logger.error(f"Error executing {cmd}: {e}")
        return 1  # General error


def process_files(files: List[str], mode: Mode, dry_run: bool = False) -> ProcessingResult:
    """Process files according to the specified mode"""
    tools_used: List[str] = []
    errors: List[str] = []

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
    # Track which extensions we've already warned about
    warned_extensions: Set[str] = set()

    for file in expanded_files:
        file_path = Path(file)
        ext = file_path.suffix.lower()

        # Handle special cases for file mapping
        mapped_ext = ext

        # Special case: Jinja HTML files
        if file_path.name.lower().endswith(JINJA_HTML_SUFFIX):
            mapped_ext = JINJA_HTML_SUFFIX

        # Special case: Justfile files
        if file_path.name.lower() in JUSTFILE_NAMES:
            mapped_ext = "justfile"
        elif file_path.name.lower() in MAKEFILE_NAMES:
            mapped_ext = "makefile"

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
            # Only warn once per extension, and skip known unformattable types
            if ext not in warned_extensions and ext not in ALWAYS_UNFORMATTABLE_EXTENSIONS:
                logger.warning(
                    f"No linter configured for extension {ext}. "
                    "Run 'taidy suggest' for tool recommendations."
                )
                warned_extensions.add(ext)

        # Add to security scanning group if trufflehog is available, we're linting,
        # and we're scanning a single directory (not individual files)
        if (
            mode in [Mode.LINT, Mode.BOTH]
            and is_command_available("trufflehog")
            and len(input_directories) == 1
            and len(files) == 1
        ):
            if ext in SECURITY_EXTENSIONS or file_path.name.startswith(".env"):
                if ".security" not in file_groups:
                    file_groups[".security"] = []
                file_groups[".security"].append(file)

    # Check if any files will be processed
    if not file_groups:
        logger.info("No supported files provided, no files were linted")
        return ProcessingResult(files_processed=0, exit_code=0, tools_used=[], errors=[])

    # Batch commands by their command signature to avoid duplicate runs
    command_batches: Dict[Tuple[str, Tuple[str, ...]], List[str]] = {}

    # Collect all commands that would be run
    for ext, file_list in file_groups.items():
        # Process linting commands
        if mode in [Mode.LINT, Mode.BOTH] and ext in LINTER_MAP:
            for linter_cmd in LINTER_MAP[ext]:
                if linter_cmd.available():
                    # Use directory if supported and no custom ignores
                    inputs = file_list
                    if (
                        input_directories
                        and not has_custom_ignores
                        and linter_cmd.supports_directories
                    ):
                        inputs = input_directories

                    cmd, args = linter_cmd.command(inputs)
                    # Create a signature excluding the file arguments
                    base_args = [arg for arg in args if arg not in inputs]
                    cmd_signature = (cmd, tuple(base_args))

                    if cmd_signature not in command_batches:
                        command_batches[cmd_signature] = []
                    command_batches[cmd_signature].extend(inputs)
                    break  # Only use the first available command

        # Process formatting commands
        if mode in [Mode.FORMAT, Mode.BOTH] and ext in FORMATTER_MAP:
            for formatter_cmd in FORMATTER_MAP[ext]:
                if formatter_cmd.available():
                    # Use directory if supported and no custom ignores
                    inputs = file_list
                    if (
                        input_directories
                        and not has_custom_ignores
                        and formatter_cmd.supports_directories
                    ):
                        inputs = input_directories

                    cmd, args = formatter_cmd.command(inputs)
                    # Create a signature excluding the file arguments
                    base_args = [arg for arg in args if arg not in inputs]
                    cmd_signature = (cmd, tuple(base_args))

                    if cmd_signature not in command_batches:
                        command_batches[cmd_signature] = []
                    command_batches[cmd_signature].extend(inputs)
                    break  # Only use the first available command

    # Track tools used
    for cmd_signature in command_batches.keys():
        cmd = cmd_signature[0]
        if cmd not in tools_used:
            tools_used.append(cmd)

    # Count files processed (unique files across all batches)
    all_files = set()
    for file_list in command_batches.values():
        all_files.update(file_list)
    files_processed = len(all_files)

    # Handle dry-run mode
    if dry_run:
        print("Dry run - commands that would be executed:")
        for cmd_signature, file_list in command_batches.items():
            cmd, base_args = cmd_signature
            unique_files = list(dict.fromkeys(file_list))  # Preserve order, remove duplicates
            if cmd == "just" and "--fmt" in base_args:
                args = list(base_args)
            elif cmd == "trufflehog" and "git" in base_args:
                args = list(base_args)
            else:
                args = list(base_args) + unique_files
            print(f"  {cmd} {' '.join(args)}")
        return ProcessingResult(
            files_processed=files_processed,
            exit_code=0,
            tools_used=tools_used,
            errors=[],
        )

    # Execute batched commands
    exit_code = 0

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=min(len(command_batches), os.cpu_count() or 1)) as executor:
        # Submit all batched commands for processing
        future_to_cmd = {
            executor.submit(
                execute_batched_command,
                cmd_signature,
                file_list,
            ): cmd_signature
            for cmd_signature, file_list in command_batches.items()
        }

        # Collect results as they complete
        for future in as_completed(future_to_cmd):
            cmd_signature = future_to_cmd[future]
            try:
                result = future.result()
                if result != 0:
                    exit_code = result
                    errors.append(f"{cmd_signature[0]} failed with exit code {result}")
            except Exception as e:
                with output_lock:
                    logger.error(f"Error executing {cmd_signature[0]}: {e}")
                exit_code = 1
                errors.append(f"Error executing {cmd_signature[0]}: {e}")

    return ProcessingResult(
        files_processed=files_processed,
        exit_code=exit_code,
        tools_used=tools_used,
        errors=errors,
    )


def analyze_project_files(directory: str = ".") -> Dict[str, Set[str]]:
    """Analyze project files and return found extensions and their tools"""
    found_extensions = set()

    # Discover all files in the project
    all_files = discover_files_in_directory(directory)

    # Extract extensions and special cases
    for file_path_str in all_files:
        file_path = Path(file_path_str)
        ext = file_path.suffix.lower()
        file_name = file_path.name.lower()

        # Handle special cases
        if file_name.endswith(JINJA_HTML_SUFFIX):
            found_extensions.add(JINJA_HTML_SUFFIX)
        elif file_name in JUSTFILE_NAMES:
            found_extensions.add("justfile")
        elif file_name in MAKEFILE_NAMES:
            found_extensions.add("makefile")
        elif ext in [".yml", ".yaml"] and ".github/workflows" in str(file_path):
            found_extensions.add(".github-workflow")
        elif ext:
            found_extensions.add(ext)

    # Group by available vs missing tools
    result = {
        "available_linters": set(),
        "missing_linters": set(),
        "available_formatters": set(),
        "missing_formatters": set(),
        "found_extensions": found_extensions,
    }

    for ext in found_extensions:
        # Check linters
        if ext in LINTER_MAP:
            available_linter = None
            for linter_cmd in LINTER_MAP[ext]:
                if linter_cmd.available():
                    available_linter = linter_cmd
                    break

            if available_linter:
                result["available_linters"].add(ext)
            else:
                result["missing_linters"].add(ext)

        # Check formatters
        if ext in FORMATTER_MAP:
            available_formatter = None
            for formatter_cmd in FORMATTER_MAP[ext]:
                if formatter_cmd.available():
                    available_formatter = formatter_cmd
                    break

            if available_formatter:
                result["available_formatters"].add(ext)
            else:
                result["missing_formatters"].add(ext)

    return result


def get_install_commands(platform_info: Dict[str, Any]) -> Dict[str, str]:
    """Get installation commands for tools based on platform information"""
    system = platform_info["system"]
    distribution = platform_info.get("distribution")

    # Base installation commands - these work across platforms
    install_commands = {
        "ruff": "pip install ruff",
        "black": "pip install black",
        "eslint": "npm install -g eslint",
        "prettier": "npm install -g prettier",
        "tsc": "npm install -g typescript",
        "rubocop": "gem install rubocop",
        "php-cs-fixer": "composer global require friendsofphp/php-cs-fixer",
        "yamllint": "pip install yamllint",
        "djlint": "pip install djlint",
        "mbake": "pip install mbake",
        "taplo": "cargo install taplo-cli",
        "just": "cargo install just",
        "trufflehog": "go install github.com/trufflesecurity/trufflehog/v3@latest",
    }

    # Platform-specific commands
    if system == "darwin":
        install_commands.update(
            {
                "gofmt": "brew install go",
                "rustfmt": "brew install rust",
                "shellcheck": "brew install shellcheck",
                "shfmt": "brew install shfmt",
                "terraform": "brew install terraform",
                "tflint": "brew install tflint",
                "actionlint": "brew install actionlint",
                "just": "brew install just",
                "trufflehog": "brew install trufflehog",
            }
        )
    elif system == "linux" and distribution:
        if distribution in ["ubuntu", "debian"]:
            # Ubuntu/Debian package manager commands
            install_commands.update(
                {
                    "gofmt": "sudo apt install golang-go",
                    "rustfmt": "sudo apt install rustc",
                    "shellcheck": "sudo apt install shellcheck",
                    "shfmt": "go install mvdan.cc/sh/v3/cmd/shfmt@latest",
                    "terraform": "https://terraform.io/downloads",
                    "tflint": (
                        "curl -s https://raw.githubusercontent.com/terraform-linters/tflint/"
                        "master/install_linux.sh | bash"
                    ),
                    "actionlint": "go install github.com/rhymond/actionlint@latest",
                    "eslint": "sudo apt install npm && npm install -g eslint",
                    "prettier": "sudo apt install npm && npm install -g prettier",
                    "tsc": "sudo apt install npm && npm install -g typescript",
                }
            )
        elif distribution in ["fedora", "rhel", "centos"]:
            # Fedora/RHEL/CentOS package manager commands
            pkg_manager = "dnf" if distribution == "fedora" else "yum"
            install_commands.update(
                {
                    "gofmt": f"sudo {pkg_manager} install golang",
                    "rustfmt": f"sudo {pkg_manager} install rust",
                    "shellcheck": f"sudo {pkg_manager} install ShellCheck",
                    "shfmt": "go install mvdan.cc/sh/v3/cmd/shfmt@latest",
                    "terraform": "https://terraform.io/downloads",
                    "tflint": (
                        "curl -s https://raw.githubusercontent.com/terraform-linters/tflint/"
                        "master/install_linux.sh | bash"
                    ),
                    "actionlint": "go install github.com/rhymond/actionlint@latest",
                    "eslint": f"sudo {pkg_manager} install npm && npm install -g eslint",
                    "prettier": f"sudo {pkg_manager} install npm && npm install -g prettier",
                    "tsc": f"sudo {pkg_manager} install npm && npm install -g typescript",
                }
            )
        elif distribution == "arch":
            # Arch Linux package manager commands
            install_commands.update(
                {
                    "gofmt": "sudo pacman -S go",
                    "rustfmt": "sudo pacman -S rust",
                    "shellcheck": "sudo pacman -S shellcheck",
                    "shfmt": "go install mvdan.cc/sh/v3/cmd/shfmt@latest",
                    "terraform": "sudo pacman -S terraform",
                    "tflint": "yay -S tflint-bin",  # AUR package
                    "actionlint": "go install github.com/rhymond/actionlint@latest",
                    "eslint": "sudo pacman -S npm && npm install -g eslint",
                    "prettier": "sudo pacman -S npm && npm install -g prettier",
                    "tsc": "sudo pacman -S npm && npm install -g typescript",
                }
            )
        elif distribution == "opensuse":
            # openSUSE package manager commands
            install_commands.update(
                {
                    "gofmt": "sudo zypper install go",
                    "rustfmt": "sudo zypper install rust",
                    "shellcheck": "sudo zypper install ShellCheck",
                    "shfmt": "go install mvdan.cc/sh/v3/cmd/shfmt@latest",
                    "terraform": "https://terraform.io/downloads",
                    "tflint": (
                        "curl -s https://raw.githubusercontent.com/terraform-linters/tflint/"
                        "master/install_linux.sh | bash"
                    ),
                    "actionlint": "go install github.com/rhymond/actionlint@latest",
                    "eslint": "sudo zypper install npm && npm install -g eslint",
                    "prettier": "sudo zypper install npm && npm install -g prettier",
                    "tsc": "sudo zypper install npm && npm install -g typescript",
                }
            )
        elif distribution == "alpine":
            # Alpine Linux package manager commands
            install_commands.update(
                {
                    "gofmt": "sudo apk add go",
                    "rustfmt": "sudo apk add rust",
                    "shellcheck": "sudo apk add shellcheck",
                    "shfmt": "go install mvdan.cc/sh/v3/cmd/shfmt@latest",
                    "terraform": "https://terraform.io/downloads",
                    "tflint": (
                        "curl -s https://raw.githubusercontent.com/terraform-linters/tflint/"
                        "master/install_linux.sh | bash"
                    ),
                    "actionlint": "go install github.com/rhymond/actionlint@latest",
                    "eslint": "sudo apk add npm && npm install -g eslint",
                    "prettier": "sudo apk add npm && npm install -g prettier",
                    "tsc": "sudo apk add npm && npm install -g typescript",
                }
            )
        else:
            # Generic Linux fallback
            install_commands.update(
                {
                    "gofmt": "install Go from https://golang.org/dl/",
                    "rustfmt": "install Rust from https://rustup.rs/",
                    "shellcheck": "install ShellCheck from https://github.com/koalaman/shellcheck",
                    "shfmt": "go install mvdan.cc/sh/v3/cmd/shfmt@latest",
                    "terraform": "https://terraform.io/downloads",
                    "tflint": "https://github.com/terraform-linters/tflint",
                    "actionlint": "go install github.com/rhymond/actionlint@latest",
                }
            )
    else:
        # Generic fallback for other systems
        install_commands.update(
            {
                "gofmt": "install Go from https://golang.org/dl/",
                "rustfmt": "install Rust from https://rustup.rs/",
                "shellcheck": "install ShellCheck from https://github.com/koalaman/shellcheck",
                "shfmt": "go install mvdan.cc/sh/v3/cmd/shfmt@latest",
                "terraform": "https://terraform.io/downloads",
                "tflint": "https://github.com/terraform-linters/tflint",
                "actionlint": "go install github.com/rhymond/actionlint@latest",
            }
        )

    return install_commands


def get_tool_suggestions(extensions: Set[str]) -> Dict[str, List[str]]:
    """Get tool installation suggestions for missing extensions"""
    suggestions = {}
    platform_info = get_platform_info()

    # Map extensions to their primary recommended tools
    tool_recommendations = {
        ".py": ["ruff", "black"],
        ".js": ["eslint", "prettier"],
        ".jsx": ["eslint", "prettier"],
        ".ts": ["eslint", "tsc", "prettier"],
        ".tsx": ["eslint", "tsc", "prettier"],
        ".go": ["gofmt"],
        ".rs": ["rustfmt"],
        ".rb": ["rubocop"],
        ".php": ["php-cs-fixer"],
        ".sh": ["shellcheck", "shfmt"],
        ".bash": ["shellcheck", "shfmt"],
        ".zsh": ["shellcheck", "shfmt"],
        ".json": ["prettier"],
        ".css": ["prettier"],
        ".scss": ["prettier"],
        ".jinja.html": ["djlint"],
        ".html": ["prettier"],
        ".md": ["prettier"],
        ".yaml": ["yamllint", "prettier"],
        ".yml": ["yamllint", "prettier"],
        ".toml": ["taplo"],
        ".tf": ["terraform", "tflint"],
        ".tfvars": ["terraform", "tflint"],
        ".github-workflow": ["actionlint", "yamllint", "prettier"],
        "makefile": ["mbake"],
        "justfile": ["just"],
        ".security": ["trufflehog"],
    }

    # Get platform-specific installation commands
    install_commands = get_install_commands(platform_info)

    for ext in extensions:
        if ext in tool_recommendations:
            ext_suggestions = []
            for tool in tool_recommendations[ext]:
                if not is_command_available(tool):
                    install_cmd = install_commands.get(tool, f"install {tool}")
                    ext_suggestions.append(f"{tool}: {install_cmd}")

            if ext_suggestions:
                suggestions[ext] = ext_suggestions

    return suggestions


def suggest_tools(quiet: bool = False) -> int:
    """Analyze project and suggest missing tools"""
    if not quiet:
        print("Analyzing project files...")

    # Get platform information
    platform_info = get_platform_info()

    # Show platform information
    if not quiet:
        if platform_info["system"] == "linux" and platform_info["distribution"]:
            platform_name = platform_info.get("pretty_name", platform_info["name"])
            if platform_name:
                print(f"Detected platform: {platform_name}")
            else:
                print(f"Detected platform: Linux ({platform_info['distribution']})")
        elif platform_info["system"] == "darwin":
            print("Detected platform: macOS")
        elif platform_info["system"] == "windows":
            print("Detected platform: Windows")

    analysis = analyze_project_files()
    found_extensions = analysis["found_extensions"]

    if not found_extensions:
        if not quiet:
            print("No supported files found in project.")
        return 0

    if not quiet:
        print(f"\nFound file types: {', '.join(sorted(found_extensions))}")

    # Show what's already available
    if not quiet and (analysis["available_linters"] or analysis["available_formatters"]):
        print("\nAvailable tools:")
        all_available = analysis["available_linters"] | analysis["available_formatters"]
        for ext in sorted(all_available):
            tools = []
            if ext in LINTER_MAP:
                for linter_cmd in LINTER_MAP[ext]:
                    if linter_cmd.available():
                        cmd, _ = linter_cmd.command([])
                        tools.append(cmd)
                        break
            if ext in FORMATTER_MAP:
                for formatter_cmd in FORMATTER_MAP[ext]:
                    if formatter_cmd.available():
                        cmd, _ = formatter_cmd.command([])
                        if cmd not in tools:
                            tools.append(cmd)
                        break
            print(f"  {ext}: {', '.join(tools)}")

    # Show suggested installations
    missing_extensions = analysis["missing_linters"] | analysis["missing_formatters"]

    if missing_extensions:
        if not quiet:
            # Show platform-specific header
            if platform_info["system"] == "linux" and platform_info["distribution"]:
                platform_name = platform_info.get("pretty_name", platform_info["name"])
                if platform_name:
                    print(f"\nSuggested tool installations for {platform_name}:")
                else:
                    distribution = platform_info["distribution"]
                    print(f"\nSuggested tool installations for Linux ({distribution}):")
            else:
                print("\nSuggested tool installations:")

            suggestions = get_tool_suggestions(missing_extensions)

            for ext in sorted(suggestions.keys()):
                print(f"\n  {ext} files:")
                for suggestion in suggestions[ext]:
                    print(f"    {suggestion}")

            # Add helpful notes for Linux users
            if platform_info["system"] == "linux":
                print("\nInstallation notes:")
                print("  - Some tools may require additional setup (e.g., adding to PATH)")
                print("  - For Go tools, ensure Go is installed and GOPATH is configured")
                print("  - For npm tools, ensure Node.js and npm are installed")
                print("  - For pip tools, ensure Python and pip are installed")
                print("  - For cargo tools, ensure Rust is installed")
    elif not quiet:
        print("\nAll recommended tools are already available!")

    return 0


def docker_run(
    args: List[str],
    pull_always: bool = False,
    build_local: bool = False,
    custom_image: Optional[str] = None,
) -> int:
    """Run taidy in Docker container with all tools pre-installed

    Args:
        args: Arguments to pass to taidy inside the container
        pull_always: Always pull the latest image, even if exists locally
        build_local: Build the image locally instead of pulling from registry
        custom_image: Custom Docker image name/tag to use
    """
    # Use custom image or default to GitHub Container Registry image
    docker_image = custom_image or "ghcr.io/singletoned/taidy:latest"

    # Check if Docker is available
    if not is_command_available("docker"):
        print("Error: Docker is not installed or not available in PATH.", file=sys.stderr)
        print("Please install Docker to use this feature.", file=sys.stderr)
        return 1

    # Handle image acquisition
    try:
        # If building locally, use local Dockerfile
        if build_local:
            local_image = "taidy:latest"
            print("Building Docker image locally from Dockerfile...")
            print("This may take several minutes...")
            build_result = subprocess.run(
                ["docker", "build", "-t", local_image, "."], cwd=os.getcwd()
            )

            if build_result.returncode != 0:
                print("Error: Failed to build Docker image.", file=sys.stderr)
                return 1

            print(f"Successfully built local image '{local_image}'")
            docker_image = local_image
        else:
            # Check if image exists locally
            inspect_result = subprocess.run(
                ["docker", "image", "inspect", docker_image], capture_output=True, text=True
            )
            image_exists = inspect_result.returncode == 0

            # Pull image if it doesn't exist or if pull_always is set
            if not image_exists or pull_always:
                action = "Pulling latest" if pull_always else "Downloading"
                print(f"{action} Docker image from GitHub Container Registry...")
                print(f"Image: {docker_image}")
                pull_result = subprocess.run(["docker", "pull", docker_image])

                if pull_result.returncode != 0:
                    print(f"Error: Failed to pull Docker image '{docker_image}'.", file=sys.stderr)
                    print("\nYou can try:", file=sys.stderr)
                    print(
                        "  1. Run 'taidy docker --build-local .' to build locally", file=sys.stderr
                    )
                    print("  2. Check your internet connection", file=sys.stderr)
                    print(
                        "  3. Verify the image exists at "
                        "https://github.com/Singletoned/tAIdy/pkgs/container/taidy",
                        file=sys.stderr,
                    )
                    return 1

                print(f"Successfully pulled image '{docker_image}'")
            else:
                print(f"Using cached Docker image '{docker_image}'")

    except Exception as e:
        print(f"Error preparing Docker image: {e}", file=sys.stderr)
        return 1

    # Get current working directory for mounting
    current_dir = os.getcwd()

    # Build Docker command
    docker_cmd = [
        "docker",
        "run",
        "--rm",  # Remove container after run
        "-v",
        f"{current_dir}:/workspace",  # Mount current directory
        "-w",
        "/workspace",  # Set working directory
        docker_image,
    ] + args

    print("Running taidy in Docker container...")
    args_str = " ".join(args)
    print(
        f"Command: docker run --rm -v {current_dir}:/workspace "
        f"-w /workspace {docker_image} {args_str}"
    )

    # Execute the Docker command
    try:
        result = subprocess.run(docker_cmd)
        return result.returncode
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 130
    except Exception as e:
        print(f"Error running Docker container: {e}", file=sys.stderr)
        return 1


def main() -> None:
    """Main entry point"""
    # Make bootstrapped tools available on PATH before anything else
    _add_bootstrapped_paths()

    # Parse flags first
    args = sys.argv[1:]
    verbose = False
    quiet = False
    json_output = False
    dry_run = False

    # Process flags and remove them from args
    filtered_args = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--verbose":
            verbose = True
        elif arg in ["-q", "--quiet"]:
            quiet = True
        elif arg == "--json":
            json_output = True
            quiet = True  # JSON mode implies quiet
        elif arg == "--dry-run":
            dry_run = True
        elif arg in ["-h", "--help"]:
            show_help()
            sys.exit(0)
        elif arg == "--version":
            show_version()
            sys.exit(0)
        else:
            filtered_args.append(arg)
        i += 1

    # Setup logging with parsed flags
    setup_logging(verbose=verbose, quiet=quiet)

    if len(filtered_args) < 1:
        show_usage()
        sys.exit(2)

    # Parse command and files
    mode = Mode.BOTH
    files = []

    if filtered_args[0] == "lint":
        mode = Mode.LINT
        if len(filtered_args) < 2:
            show_usage()
            sys.exit(2)
        files = filtered_args[1:]
    elif filtered_args[0] == "format":
        mode = Mode.FORMAT
        if len(filtered_args) < 2:
            show_usage()
            sys.exit(2)
        files = filtered_args[1:]
    elif filtered_args[0] == "suggest":
        exit_code = suggest_tools(quiet=quiet)
        sys.exit(exit_code)
    elif filtered_args[0] == "bootstrap":
        exit_code = bootstrap()
        sys.exit(exit_code)
    elif filtered_args[0] == "docker":
        # Parse docker-specific flags
        docker_args = filtered_args[1:]
        pull_always = False
        build_local = False
        custom_image = None
        taidy_args = []

        i = 0
        while i < len(docker_args):
            arg = docker_args[i]
            if arg == "--pull-always":
                pull_always = True
            elif arg == "--build-local":
                build_local = True
            elif arg == "--image":
                if i + 1 >= len(docker_args):
                    print("Error: --image flag requires an argument", file=sys.stderr)
                    sys.exit(2)
                custom_image = docker_args[i + 1]
                i += 1  # Skip the next arg
            else:
                taidy_args.append(arg)
            i += 1

        if len(taidy_args) < 1:
            show_usage()
            sys.exit(2)

        exit_code = docker_run(
            taidy_args, pull_always=pull_always, build_local=build_local, custom_image=custom_image
        )
        sys.exit(exit_code)
    else:
        # No subcommand, treat first arg as file
        mode = Mode.BOTH
        files = filtered_args

    result = process_files(files, mode, dry_run=dry_run)

    if json_output:
        print(json.dumps(result.to_dict()))
        sys.exit(result.exit_code)
    else:
        sys.exit(result.exit_code)


if __name__ == "__main__":
    main()
