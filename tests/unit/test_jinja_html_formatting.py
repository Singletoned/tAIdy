#!/usr/bin/env python3
"""Unit tests for Jinja HTML handling."""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

# Add the parent directory to the path to import taidy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from taidy.cli import Mode, process_files


class TestJinjaHtmlFormatting(unittest.TestCase):
    """Test Jinja HTML formatting behavior."""

    @patch("taidy.cli.load_config")
    @patch("taidy.cli.execute_batched_command")
    @patch("taidy.cli.is_command_available")
    def test_jinja_html_uses_djlint_for_format(
        self, mock_is_available, mock_execute, mock_load_config
    ):
        """Ensure .jinja.html files format with djlint."""
        mock_is_available.side_effect = lambda cmd: cmd == "djlint"
        mock_execute.return_value = 0
        mock_load_config.return_value = {"ignore": []}

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "template.jinja.html")
            with open(file_path, "w", encoding="utf-8") as handle:
                handle.write("<div>{{ name }}</div>")

            result = process_files([file_path], Mode.FORMAT)

        self.assertEqual(result.exit_code, 0)
        mock_execute.assert_called_once()
        cmd_signature, file_list = mock_execute.call_args[0]
        self.assertEqual(cmd_signature, ("djlint", ("--reformat",)))
        self.assertEqual(file_list, [file_path])


if __name__ == "__main__":
    unittest.main()
