#!/usr/bin/env python3
"""Unit tests for linter execution logic."""

import logging
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the parent directory to the path to import taidy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from taidy.cli import (
    _get_trufflehog_command,
    execute_batched_command,
)


class TestExecuteBatchedCommand(unittest.TestCase):
    """Test batched command execution functionality."""

    @patch("subprocess.run")
    @patch("taidy.cli.logger")
    def test_execute_batched_command_success(self, mock_logger, mock_subprocess):
        """Test successful batched command execution."""
        # Mock successful subprocess execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Command output\n"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        # Test command execution
        cmd_signature = ("ruff", ("check", "--quiet"))
        file_list = ["file1.py", "file2.py"]

        result = execute_batched_command(cmd_signature, file_list)

        # Should return success
        self.assertEqual(result, 0)

        # Should call subprocess with correct arguments
        mock_subprocess.assert_called_once_with(
            ["ruff", "check", "--quiet", "file1.py", "file2.py"],
            capture_output=True,
            text=True,
            env=os.environ,
        )

    @patch("subprocess.run")
    @patch("taidy.cli.logger")
    def test_execute_batched_command_failure(self, mock_logger, mock_subprocess):
        """Test failed batched command execution."""
        # Mock failed subprocess execution
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error message\n"
        mock_subprocess.return_value = mock_result

        cmd_signature = ("eslint", ("--format", "compact"))
        file_list = ["app.js"]

        result = execute_batched_command(cmd_signature, file_list)

        # Should return error code
        self.assertEqual(result, 1)

    @patch("subprocess.run")
    @patch("taidy.cli.logger")
    def test_execute_batched_command_not_found(self, mock_logger, mock_subprocess):
        """Test command not found scenario."""
        # Mock FileNotFoundError
        mock_subprocess.side_effect = FileNotFoundError("Command not found")

        cmd_signature = ("nonexistent", ("--help",))
        file_list = ["file.txt"]

        result = execute_batched_command(cmd_signature, file_list)

        # Should return command not found exit code
        self.assertEqual(result, 127)

        # Should log error
        mock_logger.error.assert_called_once()

    @patch("subprocess.run")
    @patch("taidy.cli.logger")
    def test_execute_batched_command_exception(self, mock_logger, mock_subprocess):
        """Test general exception handling."""
        # Mock general exception
        mock_subprocess.side_effect = Exception("General error")

        cmd_signature = ("tool", ("arg",))
        file_list = ["file.txt"]

        result = execute_batched_command(cmd_signature, file_list)

        # Should return general error code
        self.assertEqual(result, 1)

        # Should log error
        mock_logger.error.assert_called_once()

    @patch("subprocess.run")
    @patch("taidy.cli.logger")
    def test_execute_batched_command_deduplication(self, mock_logger, mock_subprocess):
        """Test file deduplication in batched commands."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        # Test with duplicate files
        cmd_signature = ("prettier", ("--write",))
        file_list = ["file1.js", "file2.js", "file1.js", "file3.js", "file2.js"]

        execute_batched_command(cmd_signature, file_list)

        # Should call with deduplicated files in original order
        mock_subprocess.assert_called_once_with(
            ["prettier", "--write", "file1.js", "file2.js", "file3.js"],
            capture_output=True,
            text=True,
            env=os.environ,
        )

    @patch("subprocess.run")
    @patch("taidy.cli.logger")
    def test_execute_batched_command_just_fmt_special(self, mock_logger, mock_subprocess):
        """Test special handling for 'just --fmt' command."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        # Test just --fmt command (doesn't take file arguments)
        cmd_signature = ("just", ("--fmt", "--check"))
        file_list = ["Justfile"]

        execute_batched_command(cmd_signature, file_list)

        # Should call without file arguments
        mock_subprocess.assert_called_once_with(
            ["just", "--fmt", "--check"], capture_output=True, text=True, env=os.environ
        )

    @patch("subprocess.run")
    @patch("taidy.cli.logger")
    def test_execute_batched_command_trufflehog_git_special(self, mock_logger, mock_subprocess):
        """Test special handling for 'trufflehog git' command."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        # Test trufflehog git command (doesn't take file arguments)
        cmd_signature = ("trufflehog", ("git", "--no-update", "file://"))
        file_list = ["file1.py", "file2.js"]

        execute_batched_command(cmd_signature, file_list)

        # Should call without file arguments
        mock_subprocess.assert_called_once_with(
            ["trufflehog", "git", "--no-update", "file://"],
            capture_output=True,
            text=True,
            env=os.environ,
        )

    @patch("builtins.print")
    @patch("subprocess.run")
    @patch("taidy.cli.logger")
    def test_execute_batched_command_trufflehog_quiet_on_success(
        self, mock_logger, mock_subprocess, mock_print
    ):
        """Trufflehog should be quiet on clean scans by default."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "banner output\n"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        mock_logger.getEffectiveLevel.return_value = logging.WARNING

        cmd_signature = ("trufflehog", ("filesystem", "--no-update", "--fail", "--log-level=-1"))
        file_list = ["file1.py"]

        execute_batched_command(cmd_signature, file_list)

        mock_print.assert_not_called()

    @patch("builtins.print")
    @patch("subprocess.run")
    @patch("taidy.cli.logger")
    def test_execute_batched_command_trufflehog_strips_banner_on_findings(
        self, mock_logger, mock_subprocess, mock_print
    ):
        """Trufflehog banner should be removed while keeping findings."""
        mock_result = MagicMock()
        mock_result.returncode = 183
        mock_result.stdout = "🐷🔑🐷  TruffleHog. Unearth your secrets. 🐷🔑🐷\nFinding line\n"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        mock_logger.getEffectiveLevel.return_value = logging.WARNING

        cmd_signature = ("trufflehog", ("filesystem", "--no-update", "--fail", "--log-level=-1"))
        file_list = ["file1.py"]

        execute_batched_command(cmd_signature, file_list)

        mock_print.assert_any_call("Finding line\n", end="", flush=True)

    @patch("subprocess.run")
    @patch("taidy.cli.logger")
    def test_execute_batched_command_taplo_environment(self, mock_logger, mock_subprocess):
        """Test special environment variable for taplo command."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        cmd_signature = ("taplo", ("format",))
        file_list = ["config.toml"]

        execute_batched_command(cmd_signature, file_list)

        # Should set RUST_LOG environment variable
        expected_env = os.environ.copy()
        expected_env["RUST_LOG"] = "warn"

        mock_subprocess.assert_called_once_with(
            ["taplo", "format", "config.toml"], capture_output=True, text=True, env=expected_env
        )


class TestTrufflehogCommand(unittest.TestCase):
    """Test trufflehog command construction."""

    @patch("taidy.cli.is_git_repository", return_value=False)
    @patch("taidy.cli.logger")
    def test_trufflehog_quiet_log_level_by_default(self, mock_logger, mock_is_git_repository):
        """Default runs should use quiet trufflehog logging."""
        mock_logger.getEffectiveLevel.return_value = logging.WARNING

        cmd, args = _get_trufflehog_command(["sample.py"])

        self.assertEqual(cmd, "trufflehog")
        self.assertIn("--log-level=-1", args)

    @patch("taidy.cli.is_git_repository", return_value=False)
    @patch("taidy.cli.logger")
    def test_trufflehog_respects_verbose_logging(self, mock_logger, mock_is_git_repository):
        """Verbose runs should allow more chatty trufflehog logs."""
        mock_logger.getEffectiveLevel.return_value = logging.INFO

        _, args = _get_trufflehog_command(["sample.py"])

        self.assertIn("--log-level=0", args)

    @patch("taidy.cli.Path.cwd", return_value=Path("/path/with space/repo"))
    @patch("taidy.cli.is_git_repository", return_value=True)
    @patch("taidy.cli.logger")
    def test_trufflehog_git_uses_encoded_uri(self, mock_logger, mock_is_git_repository, mock_cwd):
        """Git mode should use a properly encoded file URI even with spaces."""
        mock_logger.getEffectiveLevel.return_value = logging.WARNING

        cmd, args = _get_trufflehog_command(["sample.py"])

        self.assertEqual(cmd, "trufflehog")
        self.assertEqual(args[0], "git")
        self.assertEqual(args[-1], Path("/path/with space/repo").resolve().as_uri())


if __name__ == "__main__":
    unittest.main()
