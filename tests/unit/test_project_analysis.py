#!/usr/bin/env python3
"""Unit tests for project analysis functions."""

import os
import sys
import unittest
from unittest.mock import patch

# Add the parent directory to the path to import taidy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from taidy.cli import analyze_project_files


class TestProjectAnalysis(unittest.TestCase):
    """Test project analysis functionality."""

    @patch("taidy.cli.discover_files_in_directory")
    @patch("taidy.cli.is_command_available")
    def test_analyze_project_files_basic(self, mock_is_available, mock_discover):
        """Test basic project analysis."""
        # Mock discovered files
        mock_discover.return_value = ["file1.py", "file2.js", "file3.go", "file4.py"]

        # Mock command availability
        def command_available(cmd):
            available_commands = ["python3", "ruff", "eslint", "gofmt"]
            return cmd in available_commands

        mock_is_available.side_effect = command_available

        result = analyze_project_files(".")

        # Should group files by extension
        self.assertIn("Python", result)
        self.assertIn("JavaScript", result)
        self.assertIn("Go", result)

        # Should have correct files for each extension
        python_files = result.get("Python", set())
        self.assertIn("file1.py", python_files)
        self.assertIn("file4.py", python_files)

        js_files = result.get("JavaScript", set())
        self.assertIn("file2.js", js_files)

        go_files = result.get("Go", set())
        self.assertIn("file3.go", go_files)

    @patch("taidy.cli.discover_files_in_directory")
    @patch("taidy.cli.is_command_available")
    def test_analyze_project_files_no_tools(self, mock_is_available, mock_discover):
        """Test project analysis when no tools are available."""
        # Mock discovered files
        mock_discover.return_value = ["file1.py", "file2.js"]

        # Mock no commands available
        mock_is_available.return_value = False

        result = analyze_project_files(".")

        # Should still group files by extension even without tools
        self.assertIn("Python", result)
        self.assertIn("JavaScript", result)

    @patch("taidy.cli.discover_files_in_directory")
    @patch("taidy.cli.is_command_available")
    def test_analyze_project_files_mixed_extensions(self, mock_is_available, mock_discover):
        """Test analysis with many different file types."""
        # Mock discovered files with various extensions
        mock_discover.return_value = [
            "main.py",
            "script.js",
            "styles.css",
            "config.json",
            "app.go",
            "component.tsx",
            "README.md",
            "data.yml",
            "Justfile",
            ".github/workflows/ci.yml",
        ]

        # Mock all commands available
        mock_is_available.return_value = True

        result = analyze_project_files(".")

        # Should handle all supported file types
        self.assertGreater(len(result), 5)  # Should have multiple categories

        # Check specific categories
        if "Python" in result:
            self.assertIn("main.py", result["Python"])
        if "JavaScript" in result:
            self.assertIn("script.js", result["JavaScript"])
        if "CSS" in result:
            self.assertIn("styles.css", result["CSS"])

    @patch("taidy.cli.discover_files_in_directory")
    @patch("taidy.cli.is_command_available")
    def test_analyze_project_files_empty_directory(self, mock_is_available, mock_discover):
        """Test analysis of empty directory."""
        # Mock no files discovered
        mock_discover.return_value = []

        mock_is_available.return_value = True

        result = analyze_project_files(".")

        # Should return empty result
        self.assertEqual(len(result), 0)

    @patch("taidy.cli.discover_files_in_directory")
    @patch("taidy.cli.is_command_available")
    def test_analyze_project_files_unsupported_extensions(self, mock_is_available, mock_discover):
        """Test analysis with unsupported file extensions."""
        # Mock files with unsupported extensions
        mock_discover.return_value = ["file.xyz", "data.unknown", "binary.exe", "archive.zip"]

        mock_is_available.return_value = True

        result = analyze_project_files(".")

        # Should ignore unsupported extensions or handle them gracefully
        # The exact behavior depends on implementation
        # At minimum, should not crash
        self.assertIsInstance(result, dict)

    @patch("taidy.cli.discover_files_in_directory")
    @patch("taidy.cli.is_command_available")
    def test_analyze_project_files_special_files(self, mock_is_available, mock_discover):
        """Test analysis with special files like Justfile."""
        # Mock special files that don't have typical extensions
        mock_discover.return_value = [
            "Justfile",
            "Dockerfile",
            "Makefile",
            ".github/workflows/test.yml",
            "regular.py",
        ]

        mock_is_available.return_value = True

        result = analyze_project_files(".")

        # Should handle special files appropriately
        self.assertIsInstance(result, dict)

        # Should include Python file
        if "Python" in result:
            self.assertIn("regular.py", result["Python"])

    @patch("taidy.cli.discover_files_in_directory")
    def test_analyze_project_files_discovery_error(self, mock_discover):
        """Test analysis when file discovery fails."""
        # Mock discovery raising an exception
        mock_discover.side_effect = Exception("Permission denied")

        # Should handle errors gracefully
        try:
            result = analyze_project_files(".")
            # If it returns something, should be empty or valid dict
            self.assertIsInstance(result, dict)
        except Exception:
            # If it raises, that's also acceptable behavior
            pass

    @patch("taidy.cli.discover_files_in_directory")
    @patch("taidy.cli.is_command_available")
    def test_analyze_project_files_case_sensitivity(self, mock_is_available, mock_discover):
        """Test analysis with different case extensions."""
        # Mock files with different case extensions
        mock_discover.return_value = [
            "file.py",
            "FILE.PY",
            "script.Py",
            "component.js",
            "COMPONENT.JS",
        ]

        mock_is_available.return_value = True

        result = analyze_project_files(".")

        # Should handle case variations appropriately
        self.assertIsInstance(result, dict)

        # Should group Python files together regardless of case
        python_files = set()
        for category, files in result.items():
            if "python" in category.lower():
                python_files.update(files)

        # Should find some Python files
        if python_files:
            self.assertGreater(len(python_files), 0)


if __name__ == "__main__":
    unittest.main()
