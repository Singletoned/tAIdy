#!/usr/bin/env python3
"""Unit tests for linter execution logic."""

import unittest
from unittest.mock import patch, MagicMock, call
import subprocess
import sys
import os

# Add the parent directory to the path to import taidy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from taidy.cli import execute_batched_command, execute_linters, LinterCommand


class TestExecuteBatchedCommand(unittest.TestCase):
    """Test batched command execution functionality."""

    @patch('subprocess.run')
    @patch('taidy.cli.logger')
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
            env=os.environ
        )

    @patch('subprocess.run')
    @patch('taidy.cli.logger')
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

    @patch('subprocess.run')
    @patch('taidy.cli.logger')
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

    @patch('subprocess.run')
    @patch('taidy.cli.logger')
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

    @patch('subprocess.run')
    @patch('taidy.cli.logger')
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
            env=os.environ
        )

    @patch('subprocess.run')
    @patch('taidy.cli.logger')
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
            ["just", "--fmt", "--check"],
            capture_output=True,
            text=True,
            env=os.environ
        )

    @patch('subprocess.run')
    @patch('taidy.cli.logger')
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
            env=os.environ
        )

    @patch('subprocess.run')
    @patch('taidy.cli.logger')
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
            ["taplo", "format", "config.toml"],
            capture_output=True,
            text=True,
            env=expected_env
        )


class TestExecuteLinters(unittest.TestCase):
    """Test linter execution with command fallback."""

    @patch('subprocess.run')
    @patch('taidy.cli.logger')
    def test_execute_linters_first_available(self, mock_logger, mock_subprocess):
        """Test execution when first command is available."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Linting output\n"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        # Create mock linter commands
        linter1 = LinterCommand(
            available=lambda: True,  # First command available
            command=lambda files: ("ruff", ["check"] + files),
            supports_directories=True
        )
        linter2 = LinterCommand(
            available=lambda: True,  # Second command also available but shouldn't be used
            command=lambda files: ("flake8", files),
            supports_directories=False
        )

        commands = [linter1, linter2]
        file_list = ["test.py"]

        result = execute_linters(commands, file_list)

        # Should return success
        self.assertEqual(result, 0)
        
        # Should use first available command
        mock_subprocess.assert_called_once_with(
            ["ruff", "check", "test.py"],
            capture_output=True,
            text=True,
            env=os.environ
        )

    @patch('subprocess.run')
    @patch('taidy.cli.logger')
    def test_execute_linters_fallback(self, mock_logger, mock_subprocess):
        """Test execution falls back to second command when first is unavailable."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        # Create mock linter commands
        linter1 = LinterCommand(
            available=lambda: False,  # First command unavailable
            command=lambda files: ("ruff", ["check"] + files),
            supports_directories=True
        )
        linter2 = LinterCommand(
            available=lambda: True,   # Second command available
            command=lambda files: ("flake8", files),
            supports_directories=False
        )

        commands = [linter1, linter2]
        file_list = ["test.py"]

        result = execute_linters(commands, file_list)

        # Should return success
        self.assertEqual(result, 0)
        
        # Should use second command
        mock_subprocess.assert_called_once_with(
            ["flake8", "test.py"],
            capture_output=True,
            text=True,
            env=os.environ
        )

    @patch('subprocess.run')
    @patch('taidy.cli.logger')
    def test_execute_linters_no_available_commands(self, mock_logger, mock_subprocess):
        """Test when no commands are available."""
        # Create mock linter commands - all unavailable
        linter1 = LinterCommand(
            available=lambda: False,
            command=lambda files: ("ruff", ["check"] + files),
            supports_directories=True
        )
        linter2 = LinterCommand(
            available=lambda: False,
            command=lambda files: ("flake8", files),
            supports_directories=False
        )

        commands = [linter1, linter2]
        file_list = ["test.py"]

        result = execute_linters(commands, file_list)

        # Should return "no available command" code
        self.assertEqual(result, 2)
        
        # Should not call subprocess
        mock_subprocess.assert_not_called()

    @patch('subprocess.run')
    @patch('taidy.cli.logger')
    def test_execute_linters_command_failure(self, mock_logger, mock_subprocess):
        """Test when available command fails."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Linting errors found\n"
        mock_subprocess.return_value = mock_result

        linter = LinterCommand(
            available=lambda: True,
            command=lambda files: ("pylint", files),
            supports_directories=False
        )

        commands = [linter]
        file_list = ["bad_code.py"]

        result = execute_linters(commands, file_list)

        # Should return the command's exit code
        self.assertEqual(result, 1)

    @patch('subprocess.run')
    @patch('taidy.cli.logger')
    def test_execute_linters_command_not_found(self, mock_logger, mock_subprocess):
        """Test when available command is not actually found at execution."""
        # Mock FileNotFoundError during execution
        mock_subprocess.side_effect = FileNotFoundError("Command not found")

        linter = LinterCommand(
            available=lambda: True,  # Claims to be available but isn't
            command=lambda files: ("fake_linter", files),
            supports_directories=False
        )

        commands = [linter]
        file_list = ["test.py"]

        result = execute_linters(commands, file_list)

        # Should return command not found exit code
        self.assertEqual(result, 127)
        
        # Should log error
        mock_logger.error.assert_called_once()

    @patch('subprocess.run')
    @patch('taidy.cli.logger')
    def test_execute_linters_general_exception(self, mock_logger, mock_subprocess):
        """Test general exception handling during command execution."""
        # Mock general exception
        mock_subprocess.side_effect = Exception("Unexpected error")

        linter = LinterCommand(
            available=lambda: True,
            command=lambda files: ("linter", files),
            supports_directories=False
        )

        commands = [linter]
        file_list = ["test.py"]

        result = execute_linters(commands, file_list)

        # Should return general error code
        self.assertEqual(result, 1)
        
        # Should log error
        mock_logger.error.assert_called_once()

    @patch('subprocess.run')
    @patch('taidy.cli.logger')
    def test_execute_linters_empty_command_list(self, mock_logger, mock_subprocess):
        """Test execution with empty command list."""
        commands = []
        file_list = ["test.py"]

        result = execute_linters(commands, file_list)

        # Should return "no available command" code
        self.assertEqual(result, 2)
        
        # Should not call subprocess
        mock_subprocess.assert_not_called()

    @patch('subprocess.run')
    @patch('taidy.cli.logger')
    def test_execute_linters_taplo_environment(self, mock_logger, mock_subprocess):
        """Test special environment handling for taplo in execute_linters."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        linter = LinterCommand(
            available=lambda: True,
            command=lambda files: ("taplo", ["check"] + files),
            supports_directories=False
        )

        commands = [linter]
        file_list = ["config.toml"]

        execute_linters(commands, file_list)

        # Should set RUST_LOG environment variable
        expected_env = os.environ.copy()
        expected_env["RUST_LOG"] = "warn"
        
        mock_subprocess.assert_called_once_with(
            ["taplo", "check", "config.toml"],
            capture_output=True,
            text=True,
            env=expected_env
        )


if __name__ == '__main__':
    unittest.main()