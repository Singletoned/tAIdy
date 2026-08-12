"""Characterization inventory for Taidy's pre-catalogue adapters.

This snapshot deliberately lives in tests until TASK-1.2 replaces the parallel
maps with a typed catalogue. It prevents that refactor from silently dropping
an existing selector or changing the command fallback order.
"""

from __future__ import annotations

import os
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from taidy.cli import (
    ADAPTER_CATALOGUE,
    ADAPTER_MANIFEST,
    FORMATTER_MAP,
    LINTER_MAP,
    Mode,
    get_tool_suggestions,
    process_files,
)


@dataclass(frozen=True)
class AdapterInventory:
    """Expected current behavior for one selector before catalogue extraction."""

    linters: tuple[str, ...]
    formatters: tuple[str, ...]
    docker_status: str
    setup_status: str


# Docker status describes the current Dockerfile, not a future support promise:
# - supported: the adapter has a usable installed fallback in the current image.
# - conditional: the image's installation of a required tool may be skipped.
# - unavailable: the image lacks a required tool.
# Setup status describes current `suggest` behavior, not the future `setup` command:
# - suggestion-only: `get_tool_suggestions()` has installation advice.
# - not-suggested: no current installation recommendation exists.
ADAPTER_INVENTORY: dict[str, AdapterInventory] = {
    ".py": AdapterInventory(
        ("ruff", "uvx", "black", "flake8", "pylint", "python"),
        ("ruff", "uvx", "black"),
        "supported",
        "suggestion-only",
    ),
    ".js": AdapterInventory(
        ("eslint", "prettier", "node"), ("prettier",), "supported", "suggestion-only"
    ),
    ".jsx": AdapterInventory(("eslint", "prettier"), ("prettier",), "supported", "suggestion-only"),
    ".ts": AdapterInventory(
        ("eslint", "tsc", "prettier"), ("prettier",), "supported", "suggestion-only"
    ),
    ".tsx": AdapterInventory(
        ("eslint", "tsc", "prettier"), ("prettier",), "supported", "suggestion-only"
    ),
    ".json": AdapterInventory(("prettier",), ("prettier",), "supported", "suggestion-only"),
    ".css": AdapterInventory(("prettier",), ("prettier",), "supported", "suggestion-only"),
    ".scss": AdapterInventory(("prettier",), ("prettier",), "supported", "suggestion-only"),
    ".jinja.html": AdapterInventory(("djlint",), ("djlint",), "unavailable", "suggestion-only"),
    ".html": AdapterInventory(("prettier",), ("prettier",), "supported", "suggestion-only"),
    ".md": AdapterInventory(("prettier",), ("prettier",), "supported", "suggestion-only"),
    ".pug": AdapterInventory((), ("node",), "unavailable", "not-suggested"),
    ".go": AdapterInventory(("gofmt",), ("gofmt",), "supported", "suggestion-only"),
    ".rs": AdapterInventory(("rustfmt",), ("rustfmt",), "supported", "suggestion-only"),
    ".rb": AdapterInventory(("rubocop",), ("rubocop",), "supported", "suggestion-only"),
    ".php": AdapterInventory(("php-cs-fixer",), ("php-cs-fixer",), "supported", "suggestion-only"),
    ".sh": AdapterInventory(
        ("shellcheck", "beautysh"), ("shfmt", "beautysh"), "supported", "suggestion-only"
    ),
    ".bash": AdapterInventory(
        ("shellcheck", "beautysh"), ("shfmt", "beautysh"), "supported", "suggestion-only"
    ),
    ".zsh": AdapterInventory(
        ("shellcheck", "beautysh"), ("shfmt", "beautysh"), "supported", "suggestion-only"
    ),
    ".yaml": AdapterInventory(
        ("yamllint", "prettier"), ("prettier",), "supported", "suggestion-only"
    ),
    ".yml": AdapterInventory(
        ("yamllint", "prettier"), ("prettier",), "supported", "suggestion-only"
    ),
    ".toml": AdapterInventory(("taplo",), ("taplo",), "supported", "suggestion-only"),
    ".tf": AdapterInventory(
        ("terraform", "tflint"), ("terraform",), "supported", "suggestion-only"
    ),
    ".tfvars": AdapterInventory(
        ("terraform", "tflint"), ("terraform",), "supported", "suggestion-only"
    ),
    ".github-workflow": AdapterInventory(
        ("actionlint", "yamllint", "prettier"), ("prettier",), "conditional", "suggestion-only"
    ),
    "makefile": AdapterInventory((), ("mbake",), "unavailable", "suggestion-only"),
    "justfile": AdapterInventory((), ("just",), "supported", "suggestion-only"),
    ".security": AdapterInventory(("trufflehog",), (), "conditional", "suggestion-only"),
}

SELECTOR_PATHS = {
    ".jinja.html": "template.jinja.html",
    ".github-workflow": ".github/workflows/ci.yml",
    "makefile": "Makefile",
    "justfile": "Justfile",
}


class TestAdapterInventory(unittest.TestCase):
    """Freeze current adapter selectors, command ordering, and support status."""

    def command_names(self, commands):
        with patch(
            "taidy.cli._ensure_prettier_pug_install",
            return_value=(Path("/tmp/prettier.cjs"), Path("/tmp/plugin-pug.js")),
        ):
            return tuple(command.command([])[0] for command in commands)

    def test_inventory_covers_every_configured_selector(self):
        configured_selectors = set(LINTER_MAP) | set(FORMATTER_MAP)
        self.assertEqual(set(ADAPTER_INVENTORY), configured_selectors)

    def test_command_fallback_order_matches_inventory(self):
        for selector, inventory in ADAPTER_INVENTORY.items():
            with self.subTest(selector=selector, operation="lint"):
                commands = LINTER_MAP.get(selector, [])
                self.assertEqual(self.command_names(commands), inventory.linters)
            with self.subTest(selector=selector, operation="format"):
                commands = FORMATTER_MAP.get(selector, [])
                self.assertEqual(self.command_names(commands), inventory.formatters)

    @patch("taidy.cli.execute_batched_command", return_value=0)
    @patch("taidy.cli.os.path.isdir", return_value=False)
    @patch("taidy.cli.os.path.exists", return_value=True)
    @patch("taidy.cli.is_command_available", return_value=True)
    def test_every_non_security_selector_dispatches_to_its_first_candidate(
        self, mock_available, mock_exists, mock_isdir, mock_execute
    ):
        del mock_available, mock_exists, mock_isdir
        for selector, inventory in ADAPTER_INVENTORY.items():
            if selector == ".security":
                continue
            file_path = SELECTOR_PATHS.get(selector, f"fixture{selector}")
            mode = Mode.LINT if inventory.linters else Mode.FORMAT
            expected_command = (inventory.linters or inventory.formatters)[0]

            with self.subTest(selector=selector, mode=mode):
                mock_execute.reset_mock()
                with patch(
                    "taidy.cli._ensure_prettier_pug_install",
                    return_value=(Path("/tmp/prettier.cjs"), Path("/tmp/plugin-pug.js")),
                ):
                    result = process_files([file_path], mode)

                self.assertEqual(result.exit_code, 0)
                self.assertEqual(result.tools_used, [expected_command])
                self.assertTrue(mock_execute.called)

    @patch("taidy.cli.get_platform_info", return_value={"system": "unknown"})
    @patch("taidy.cli.is_command_available", return_value=False)
    def test_suggestions_derive_from_manifest(self, mock_available, mock_platform):
        del mock_available, mock_platform

        suggestions = get_tool_suggestions({".py"})

        self.assertEqual(
            [suggestion.split(":", 1)[0] for suggestion in suggestions[".py"]],
            list(ADAPTER_MANIFEST[".py"].suggestion_tools),
        )

    @patch("taidy.cli.execute_batched_command", return_value=0)
    @patch("taidy.cli.discover_files_in_directory", return_value=[".env", "schema.sql"])
    @patch("taidy.cli.os.path.isdir", return_value=True)
    @patch("taidy.cli.os.path.exists", return_value=True)
    @patch("taidy.cli.is_command_available", side_effect=lambda command: command == "trufflehog")
    @patch("taidy.cli.logger")
    def test_security_selector_dispatches_for_a_single_directory(
        self, mock_logger, mock_available, mock_exists, mock_isdir, mock_discover, mock_execute
    ):
        del mock_available, mock_exists, mock_isdir, mock_discover
        result = process_files(["fixture-directory"], Mode.LINT)

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.tools_used, ["trufflehog"])
        self.assertEqual(result.not_checked, [])
        mock_logger.warning.assert_not_called()
        self.assertTrue(mock_execute.called)

    def test_manifest_covers_command_maps_and_drives_adapter_policy(self):
        valid_docker_statuses = {"supported", "conditional", "unavailable"}
        valid_support_levels = {"curated", "compatibility"}
        valid_setup_statuses = {"suggestion-only", "not-suggested"}

        self.assertEqual(set(ADAPTER_MANIFEST), set(ADAPTER_INVENTORY))
        self.assertEqual(set(ADAPTER_CATALOGUE), set(ADAPTER_MANIFEST))
        for selector, inventory in ADAPTER_INVENTORY.items():
            adapter = ADAPTER_CATALOGUE[selector]
            manifest = ADAPTER_MANIFEST[selector]
            with self.subTest(selector=selector):
                self.assertEqual(tuple(LINTER_MAP.get(selector, [])), adapter.linters)
                self.assertEqual(tuple(FORMATTER_MAP.get(selector, [])), adapter.formatters)
                self.assertEqual(adapter.suggestion_tools, manifest.suggestion_tools)
                self.assertEqual(adapter.docker_status, manifest.docker_status)
                self.assertEqual(adapter.docker_status, inventory.docker_status)
                self.assertEqual(adapter.setup_status, inventory.setup_status)
                self.assertIn(adapter.docker_status, valid_docker_statuses)
                self.assertIn(adapter.support_level, valid_support_levels)
                self.assertIn(adapter.setup_status, valid_setup_statuses)


if __name__ == "__main__":
    unittest.main()
