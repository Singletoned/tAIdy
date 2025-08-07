#!/usr/bin/env python3
"""Unit tests for file discovery functions."""

import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import sys
import os

# Add the parent directory to the path to import taidy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from taidy.cli import discover_files_in_directory, should_ignore_file


class TestFileDiscovery(unittest.TestCase):
    """Test file discovery functionality."""

    @patch('taidy.cli.Path')
    @patch('taidy.cli.load_config')
    @patch('taidy.cli.get_git_ignored_files')
    @patch('taidy.cli.is_git_repository')
    def test_discover_basic_files(self, mock_is_git, mock_git_ignored, mock_load_config, mock_path):
        """Test basic file discovery in a directory."""
        # Setup mocks
        mock_is_git.return_value = False
        mock_git_ignored.return_value = set()
        mock_load_config.return_value = {"ignore": []}
        
        # Mock Path object and its methods
        mock_path_obj = MagicMock()
        mock_path.return_value = mock_path_obj
        mock_path_obj.exists.return_value = True
        mock_path_obj.is_dir.return_value = True
        
        # Mock discovered files
        mock_files = [
            MagicMock(spec=Path),
            MagicMock(spec=Path),
            MagicMock(spec=Path)
        ]
        mock_files[0].suffix = ".py"
        mock_files[0].name = "test.py"
        mock_files[0].__str__ = lambda: "test.py"
        mock_files[1].suffix = ".js"
        mock_files[1].name = "script.js"
        mock_files[1].__str__ = lambda: "script.js"
        mock_files[2].suffix = ""
        mock_files[2].name = "Justfile"
        mock_files[2].__str__ = lambda: "Justfile"
        
        mock_path_obj.rglob.return_value = mock_files
        
        result = discover_files_in_directory(".")
        
        # Should find all files
        self.assertEqual(len(result), 3)
        self.assertIn("test.py", result)
        self.assertIn("script.js", result)
        self.assertIn("Justfile", result)

    @patch('taidy.cli.Path')
    @patch('taidy.cli.load_config')
    @patch('taidy.cli.get_git_ignored_files')
    @patch('taidy.cli.is_git_repository')
    def test_discover_with_ignore_patterns(self, mock_is_git, mock_git_ignored, mock_load_config, mock_path):
        """Test file discovery with ignore patterns."""
        # Setup mocks
        mock_is_git.return_value = False
        mock_git_ignored.return_value = set()
        mock_load_config.return_value = {"ignore": ["*.tmp", "build/*"]}
        
        # Mock Path object
        mock_path_obj = MagicMock()
        mock_path.return_value = mock_path_obj
        mock_path_obj.exists.return_value = True
        mock_path_obj.is_dir.return_value = True
        
        # Mock discovered files - including some that should be ignored
        mock_files = [
            MagicMock(spec=Path),
            MagicMock(spec=Path),
            MagicMock(spec=Path)
        ]
        mock_files[0].suffix = ".py"
        mock_files[0].name = "test.py"
        mock_files[0].__str__ = lambda: "test.py"
        mock_files[1].suffix = ".tmp"
        mock_files[1].name = "temp.tmp"
        mock_files[1].__str__ = lambda: "temp.tmp"
        mock_files[2].suffix = ".js"
        mock_files[2].name = "build.js"
        mock_files[2].__str__ = lambda: "build/build.js"
        
        mock_path_obj.rglob.return_value = mock_files
        
        result = discover_files_in_directory(".")
        
        # Should only find the Python file, others ignored
        self.assertEqual(len(result), 1)
        self.assertIn("test.py", result)

    @patch('taidy.cli.Path')
    @patch('taidy.cli.load_config')
    @patch('taidy.cli.get_git_ignored_files')
    @patch('taidy.cli.is_git_repository')
    def test_discover_git_ignored_files(self, mock_is_git, mock_git_ignored, mock_load_config, mock_path):
        """Test that git-ignored files are excluded."""
        # Setup mocks
        mock_is_git.return_value = True
        mock_load_config.return_value = {"ignore": []}
        
        # Mock Path object
        mock_path_obj = MagicMock()
        mock_path.return_value = mock_path_obj
        mock_path_obj.exists.return_value = True
        mock_path_obj.is_dir.return_value = True
        
        # Mock git ignored files
        git_ignored = {Path("ignored.py")}
        mock_git_ignored.return_value = git_ignored
        
        # Mock discovered files
        mock_files = [
            MagicMock(spec=Path),
            MagicMock(spec=Path)
        ]
        mock_files[0].suffix = ".py"
        mock_files[0].name = "test.py"
        mock_files[0].__str__ = lambda: "test.py"
        mock_files[1].suffix = ".py"
        mock_files[1].name = "ignored.py"
        mock_files[1].__str__ = lambda: "ignored.py"
        
        mock_path_obj.rglob.return_value = mock_files
        
        result = discover_files_in_directory(".")
        
        # Should only find non-ignored file
        self.assertEqual(len(result), 1)
        self.assertIn("test.py", result)
        self.assertNotIn("ignored.py", result)

    @patch('taidy.cli.Path')
    @patch('taidy.cli.load_config')
    @patch('taidy.cli.get_git_ignored_files')
    @patch('taidy.cli.is_git_repository')
    def test_discover_single_directory_with_files(self, mock_is_git, mock_git_ignored, mock_load_config, mock_path):
        """Test discovery in a directory with supported files."""
        # Setup mocks
        mock_is_git.return_value = False
        mock_git_ignored.return_value = set()
        mock_load_config.return_value = {"ignore": []}
        
        # Mock Path object
        mock_path_obj = MagicMock()
        mock_path.return_value = mock_path_obj
        
        # Mock discovered files with proper extension support
        mock_py_file = MagicMock(spec=Path)
        mock_py_file.suffix = ".py"
        mock_py_file.name = "script.py"
        mock_py_file.is_file.return_value = True
        mock_py_file.__str__ = lambda: "script.py"
        
        mock_path_obj.rglob.return_value = [mock_py_file]
        
        result = discover_files_in_directory(".")
        
        self.assertEqual(len(result), 1)
        self.assertIn("script.py", result)

    @patch('taidy.cli.Path')
    def test_discover_nonexistent_path(self, mock_path):
        """Test discovery with nonexistent path."""
        mock_path_obj = MagicMock()
        mock_path.return_value = mock_path_obj
        mock_path_obj.exists.return_value = False
        
        result = discover_files_in_directory("nonexistent")
        
        self.assertEqual(result, [])


class TestIgnorePatterns(unittest.TestCase):
    """Test ignore pattern functionality."""

    def test_should_ignore_file_glob_pattern(self):
        """Test glob pattern matching."""
        patterns = ["*.tmp", "*.log"]
        
        self.assertTrue(should_ignore_file(Path("file.tmp"), patterns))
        self.assertTrue(should_ignore_file(Path("debug.log"), patterns))
        self.assertFalse(should_ignore_file(Path("file.py"), patterns))

    def test_should_ignore_file_directory_pattern(self):
        """Test directory-based ignore patterns."""
        patterns = ["build/*", "node_modules"]
        
        self.assertTrue(should_ignore_file(Path("build/output.js"), patterns))
        self.assertTrue(should_ignore_file(Path("node_modules"), patterns))
        self.assertTrue(should_ignore_file(Path("node_modules/package/file.js"), patterns))
        self.assertFalse(should_ignore_file(Path("src/file.js"), patterns))

    def test_should_ignore_file_exact_name(self):
        """Test exact file name matching."""
        patterns = ["Dockerfile", ".DS_Store"]
        
        self.assertTrue(should_ignore_file(Path("Dockerfile"), patterns))
        self.assertTrue(should_ignore_file(Path("subdir/Dockerfile"), patterns))
        self.assertTrue(should_ignore_file(Path(".DS_Store"), patterns))
        self.assertFalse(should_ignore_file(Path("Dockerfile.bak"), patterns))

    def test_should_ignore_file_complex_pattern(self):
        """Test complex ignore patterns."""
        patterns = ["**/__pycache__/**", "*.egg-info", "dist"]
        
        self.assertTrue(should_ignore_file(Path("src/__pycache__/file.pyc"), patterns))
        self.assertTrue(should_ignore_file(Path("project.egg-info"), patterns))
        self.assertTrue(should_ignore_file(Path("dist"), patterns))
        self.assertFalse(should_ignore_file(Path("src/main.py"), patterns))

    def test_should_ignore_file_empty_patterns(self):
        """Test with empty ignore patterns."""
        patterns = []
        
        self.assertFalse(should_ignore_file(Path("any_file.py"), patterns))


if __name__ == '__main__':
    unittest.main()