#!/usr/bin/env python3
"""Integration tests for configuration system with real file operations."""

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add the parent directory to the path to import taidy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from taidy.cli import discover_files_in_directory, load_config, should_ignore_file


class TestConfigurationSystemIntegration(unittest.TestCase):
    """Integration tests for configuration system using real files."""

    def setUp(self):
        """Create temporary directory for each test."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.original_cwd = os.getcwd()

    def tearDown(self):
        """Clean up temporary directory and restore working directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_load_config_valid_json_file(self):
        """Test loading a valid JSON configuration file."""
        # Create config file
        config_data = {"ignore": ["*.tmp", "build/*", "node_modules"]}
        config_file = self.test_dir / ".taidy.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f, indent=2)

        # Change to test directory and load config
        os.chdir(self.test_dir)
        result = load_config(".")

        self.assertEqual(result, config_data)

    def test_load_config_invalid_json_file(self):
        """Test loading an invalid JSON configuration file."""
        # Create invalid JSON file
        config_file = self.test_dir / ".taidy.json"
        with open(config_file, "w") as f:
            f.write('{"ignore": ["*.tmp",}')  # Missing closing bracket

        # Change to test directory and load config
        os.chdir(self.test_dir)
        result = load_config(".")

        # Should return empty config for invalid JSON
        self.assertEqual(result, {})

    def test_load_config_no_file_exists(self):
        """Test loading config when no .taidy.json file exists."""
        # Change to test directory (no config file)
        os.chdir(self.test_dir)
        result = load_config(".")

        # Should return empty config
        self.assertEqual(result, {})

    def test_load_config_directory_tree_search(self):
        """Test that config is found when searching up directory tree."""
        # Create nested directory structure
        nested_dir = self.test_dir / "project" / "src" / "subdir"
        nested_dir.mkdir(parents=True)

        # Create config file in project root
        config_data = {"ignore": ["*.test"]}
        config_file = self.test_dir / "project" / ".taidy.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Load config from nested directory
        os.chdir(nested_dir)
        result = load_config(".")

        self.assertEqual(result, config_data)

    def test_load_config_stops_at_first_found(self):
        """Test that config search stops at first .taidy.json found."""
        # Create nested directory structure
        nested_dir = self.test_dir / "project" / "subproject"
        nested_dir.mkdir(parents=True)

        # Create config files at different levels
        parent_config = {"ignore": ["parent_pattern"]}
        child_config = {"ignore": ["child_pattern"]}

        parent_config_file = self.test_dir / "project" / ".taidy.json"
        child_config_file = nested_dir / ".taidy.json"

        with open(parent_config_file, "w") as f:
            json.dump(parent_config, f)
        with open(child_config_file, "w") as f:
            json.dump(child_config, f)

        # Load config from nested directory - should get child config
        os.chdir(nested_dir)
        result = load_config(".")

        self.assertEqual(result, child_config)

    def test_load_config_empty_file(self):
        """Test loading empty configuration file."""
        # Create empty config file
        config_file = self.test_dir / ".taidy.json"
        config_file.touch()

        os.chdir(self.test_dir)
        result = load_config(".")

        # Should handle empty file gracefully
        self.assertEqual(result, {})

    def test_load_config_permission_error(self):
        """Test handling of permission errors when reading config file."""
        if os.name == "nt":  # Skip on Windows due to different permission model
            self.skipTest("Permission test not applicable on Windows")

        # Create config file and remove read permissions
        config_file = self.test_dir / ".taidy.json"
        with open(config_file, "w") as f:
            json.dump({"ignore": ["test"]}, f)

        # Remove read permissions
        os.chmod(config_file, 0o000)

        try:
            os.chdir(self.test_dir)
            result = load_config(".")
            # Should return empty config on permission error
            self.assertEqual(result, {})
        finally:
            # Restore permissions for cleanup
            os.chmod(config_file, 0o644)


class TestIgnorePatternsIntegration(unittest.TestCase):
    """Integration tests for ignore pattern functionality."""

    def setUp(self):
        """Create temporary directory for each test."""
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_ignore_patterns_with_real_files(self):
        """Test ignore patterns with actual files and directories."""
        # Create test file structure
        (self.test_dir / "src").mkdir()
        (self.test_dir / "build").mkdir()
        (self.test_dir / "node_modules").mkdir()

        # Create files
        (self.test_dir / "src" / "main.py").touch()
        (self.test_dir / "build" / "output.js").touch()
        (self.test_dir / "temp.tmp").touch()
        (self.test_dir / "README.md").touch()
        (self.test_dir / "node_modules" / "package.js").touch()

        # Test ignore patterns
        patterns = ["*.tmp", "build", "node_modules"]

        # Files that should be ignored
        self.assertTrue(should_ignore_file(self.test_dir / "temp.tmp", patterns))
        self.assertTrue(
            should_ignore_file(self.test_dir / "build" / "output.js", patterns)
        )  # Should ignore because "build" is in path parts
        self.assertTrue(should_ignore_file(self.test_dir / "node_modules", patterns))
        self.assertTrue(should_ignore_file(self.test_dir / "node_modules" / "package.js", patterns))

        # Files that should NOT be ignored
        self.assertFalse(should_ignore_file(self.test_dir / "src" / "main.py", patterns))
        self.assertFalse(should_ignore_file(self.test_dir / "README.md", patterns))

    def test_complex_ignore_patterns(self):
        """Test complex ignore patterns with wildcards."""
        # Create test structure
        (self.test_dir / "src" / "__pycache__").mkdir(parents=True)
        (self.test_dir / "tests" / "__pycache__").mkdir(parents=True)

        # Create files
        (self.test_dir / "src" / "__pycache__" / "main.cpython-39.pyc").touch()
        (self.test_dir / "tests" / "__pycache__" / "test.cpython-39.pyc").touch()
        (self.test_dir / "project.egg-info").mkdir()
        (self.test_dir / "dist").mkdir()

        patterns = ["**/__pycache__/**", "*.egg-info", "dist"]

        # Should be ignored
        self.assertTrue(
            should_ignore_file(
                self.test_dir / "src" / "__pycache__" / "main.cpython-39.pyc", patterns
            )
        )
        self.assertTrue(
            should_ignore_file(
                self.test_dir / "tests" / "__pycache__" / "test.cpython-39.pyc", patterns
            )
        )
        self.assertTrue(should_ignore_file(self.test_dir / "project.egg-info", patterns))
        self.assertTrue(should_ignore_file(self.test_dir / "dist", patterns))


class TestConfigurationIntegrationWithDiscovery(unittest.TestCase):
    """Test configuration integration with file discovery."""

    def setUp(self):
        """Create temporary directory for each test."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.original_cwd = os.getcwd()

    def tearDown(self):
        """Clean up temporary directory and restore working directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_file_discovery_with_config_ignores(self):
        """Test that file discovery respects config ignore patterns."""
        # Create file structure
        (self.test_dir / "src").mkdir()
        (self.test_dir / "tests").mkdir()
        (self.test_dir / "build").mkdir()

        # Create files
        (self.test_dir / "src" / "main.py").touch()
        (self.test_dir / "tests" / "test_main.py").touch()
        (self.test_dir / "build" / "output.py").touch()  # Should be ignored
        (self.test_dir / "temp.tmp").touch()  # Should be ignored
        (self.test_dir / "README.py").touch()  # Should be included

        # Create config to ignore build and *.tmp
        config_data = {"ignore": ["build", "*.tmp"]}
        config_file = self.test_dir / ".taidy.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Change to test directory and discover files
        os.chdir(self.test_dir)
        discovered_files = discover_files_in_directory(".")

        # Should find Python files but exclude ignored ones
        set(discovered_files)

        # These should be found
        self.assertTrue(any("main.py" in f for f in discovered_files))
        self.assertTrue(any("test_main.py" in f for f in discovered_files))
        self.assertTrue(any("README.py" in f for f in discovered_files))

        # These should be ignored
        self.assertFalse(any("output.py" in f for f in discovered_files))
        self.assertFalse(any("temp.tmp" in f for f in discovered_files))

    def test_file_discovery_with_default_ignores(self):
        """Test that file discovery applies default ignore patterns."""
        # Create typical project structure with ignored directories
        ignored_dirs = ["node_modules", "__pycache__", ".git", "dist", "build"]
        for dir_name in ignored_dirs:
            (self.test_dir / dir_name).mkdir()
            (self.test_dir / dir_name / "file.py").touch()

        # Create normal source files
        (self.test_dir / "src").mkdir()
        (self.test_dir / "src" / "main.py").touch()
        (self.test_dir / "app.py").touch()

        # No custom config file
        os.chdir(self.test_dir)
        discovered_files = discover_files_in_directory(".")

        # Should find source files
        self.assertTrue(any("main.py" in f for f in discovered_files))
        self.assertTrue(any("app.py" in f for f in discovered_files))

        # Should ignore files in default ignored directories
        for ignored_dir in ignored_dirs:
            self.assertFalse(any(ignored_dir in f for f in discovered_files))

    def test_file_discovery_without_git_integration(self):
        """Test file discovery in non-git directory."""
        # Create simple file structure (no .git directory)
        (self.test_dir / "src").mkdir()
        (self.test_dir / "src" / "main.py").touch()
        (self.test_dir / "script.js").touch()
        (self.test_dir / "styles.css").touch()

        os.chdir(self.test_dir)
        discovered_files = discover_files_in_directory(".")

        # Should find all supported files
        set(discovered_files)
        self.assertTrue(any("main.py" in f for f in discovered_files))
        self.assertTrue(any("script.js" in f for f in discovered_files))
        self.assertTrue(any("styles.css" in f for f in discovered_files))


if __name__ == "__main__":
    unittest.main()
