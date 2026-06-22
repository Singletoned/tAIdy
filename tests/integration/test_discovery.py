#!/usr/bin/env python3
"""Integration tests for directory discovery."""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add the parent directory to the path to import taidy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from taidy.cli import discover_files_in_directory


class TestDiscoveryIntegration(unittest.TestCase):
    """Test directory discovery with real files."""

    def setUp(self):
        """Create temporary directory for each test."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.original_cwd = os.getcwd()

    def tearDown(self):
        """Clean up temporary directory and restore working directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_file_discovery_with_default_ignores(self):
        """Test that file discovery applies default ignore directories."""
        ignored_dirs = ["node_modules", "__pycache__", ".git", "dist", "build"]
        for dir_name in ignored_dirs:
            (self.test_dir / dir_name).mkdir()
            (self.test_dir / dir_name / "file.py").touch()

        (self.test_dir / "src").mkdir()
        (self.test_dir / "src" / "main.py").touch()
        (self.test_dir / "app.py").touch()

        os.chdir(self.test_dir)
        discovered_files = discover_files_in_directory(".")

        self.assertTrue(any("main.py" in f for f in discovered_files))
        self.assertTrue(any("app.py" in f for f in discovered_files))

        for ignored_dir in ignored_dirs:
            self.assertFalse(any(ignored_dir in f for f in discovered_files))

    def test_file_discovery_without_git_integration(self):
        """Test file discovery in non-git directory."""
        (self.test_dir / "src").mkdir()
        (self.test_dir / "src" / "main.py").touch()
        (self.test_dir / "script.js").touch()
        (self.test_dir / "styles.css").touch()

        os.chdir(self.test_dir)
        discovered_files = discover_files_in_directory(".")

        self.assertTrue(any("main.py" in f for f in discovered_files))
        self.assertTrue(any("script.js" in f for f in discovered_files))
        self.assertTrue(any("styles.css" in f for f in discovered_files))


if __name__ == "__main__":
    unittest.main()
