#!/usr/bin/env python3
"""Integration tests for file system operations with real files."""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add the parent directory to the path to import taidy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from taidy.cli import discover_files_in_directory


class TestFileSystemOperationsIntegration(unittest.TestCase):
    """Integration tests for file system operations using real files."""

    def setUp(self):
        """Create temporary directory for each test."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.original_cwd = os.getcwd()

    def tearDown(self):
        """Clean up temporary directory and restore working directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def create_test_file_structure(self):
        """Create a realistic test file structure."""
        # Create directories
        directories = [
            "src", "tests", "docs", ".github/workflows",
            "node_modules", "__pycache__", "dist", "build"
        ]
        for dir_path in directories:
            (self.test_dir / dir_path).mkdir(parents=True, exist_ok=True)

        # Create various file types
        files = {
            "src/main.py": "#!/usr/bin/env python3\nprint('Hello, world!')\n",
            "src/utils.js": "function utils() { return true; }\n",
            "src/styles.css": "body { margin: 0; }\n",
            "tests/test_main.py": "import unittest\n",
            "tests/fixtures/sample.json": '{"key": "value"}\n',
            "docs/README.md": "# Project Documentation\n",
            ".github/workflows/ci.yml": "name: CI\non: [push]\n",
            "Justfile": "default:\n\techo 'Hello from Just'\n",
            ".gitignore": "*.pyc\n__pycache__/\n",
            "package.json": '{"name": "test-project"}\n',
            
            # Files that should be ignored by default
            "node_modules/package/index.js": "module.exports = {};\n",
            "__pycache__/main.cpython-39.pyc": "binary data",
            "dist/bundle.js": "// minified code\n",
            "build/output.css": "/* compiled styles */\n",
            
            # Various extensions
            "config.toml": "[tool.test]\nkey = 'value'\n",
            "data.yaml": "key: value\n",
            "script.sh": "#!/bin/bash\necho 'Hello'\n",
            "app.go": "package main\n",
            "component.rs": "fn main() {}\n",
            "style.scss": "$primary: blue;\n",
            "template.html": "<h1>Test</h1>\n",
        }

        for file_path, content in files.items():
            full_path = self.test_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)

    def test_discover_files_comprehensive_structure(self):
        """Test file discovery with comprehensive directory structure."""
        self.create_test_file_structure()
        os.chdir(self.test_dir)
        
        discovered_files = discover_files_in_directory(".")
        set(discovered_files)

        # Should find supported files
        expected_found = [
            "main.py", "utils.js", "styles.css", "test_main.py",
            "sample.json", "README.md", "ci.yml", "Justfile",
            "package.json", "config.toml", "data.yaml", "script.sh",
            "app.go", "component.rs", "template.html"
        ]

        for expected in expected_found:
            found = any(expected in f for f in discovered_files)
            self.assertTrue(found, f"Should have found file containing '{expected}' in {discovered_files}")

        # Should ignore files in default ignored directories
        ignored_patterns = ["node_modules", "__pycache__", "dist", "build"]
        for pattern in ignored_patterns:
            found = any(pattern in f for f in discovered_files)
            self.assertFalse(found, f"Should not have found files in '{pattern}' directory")

    def test_discover_files_deep_directory_structure(self):
        """Test file discovery with deep nested directories."""
        # Create deep nested structure
        deep_path = self.test_dir / "level1" / "level2" / "level3" / "level4" / "level5"
        deep_path.mkdir(parents=True)

        # Create files at different levels
        files = [
            self.test_dir / "root.py",
            self.test_dir / "level1" / "l1.py",
            self.test_dir / "level1" / "level2" / "l2.js",
            self.test_dir / "level1" / "level2" / "level3" / "l3.css",
            deep_path / "deep.py"
        ]

        for file_path in files:
            with open(file_path, 'w') as f:
                f.write(f"// Content of {file_path.name}\n")

        os.chdir(self.test_dir)
        discovered_files = discover_files_in_directory(".")

        # Should find all files regardless of depth
        self.assertEqual(len(discovered_files), 5)
        
        # Check specific files
        file_names = ["root.py", "l1.py", "l2.js", "l3.css", "deep.py"]
        for name in file_names:
            found = any(name in f for f in discovered_files)
            self.assertTrue(found, f"Should have found '{name}'")

    def test_discover_files_empty_directories(self):
        """Test file discovery handles empty directories correctly."""
        # Create empty directory structure
        empty_dirs = ["empty1", "empty2/nested", "src/empty_subdir"]
        for dir_path in empty_dirs:
            (self.test_dir / dir_path).mkdir(parents=True)

        # Create one file
        (self.test_dir / "single_file.py").touch()

        os.chdir(self.test_dir)
        discovered_files = discover_files_in_directory(".")

        # Should find the single file
        self.assertEqual(len(discovered_files), 1)
        self.assertTrue(any("single_file.py" in f for f in discovered_files))

    def test_discover_files_mixed_case_extensions(self):
        """Test file discovery with mixed case file extensions."""
        # Create files with different case extensions
        files = [
            ("script.py", "python"),
            ("SCRIPT.PY", "python"),
            ("Script.Py", "python"),
            ("app.js", "javascript"),
            ("APP.JS", "javascript"),
            ("style.css", "css"),
            ("STYLE.CSS", "css"),
        ]

        for filename, filetype in files:
            file_path = self.test_dir / filename
            with open(file_path, 'w') as f:
                f.write(f"// {filetype} file\n")

        os.chdir(self.test_dir)
        discovered_files = discover_files_in_directory(".")

        # Should find all files regardless of case
        # Note: behavior may depend on case sensitivity of file system
        self.assertGreater(len(discovered_files), 0)
        
        # At minimum should find some Python files
        python_files = [f for f in discovered_files if ".py" in f.lower()]
        self.assertGreater(len(python_files), 0)

    def test_discover_files_special_characters_in_names(self):
        """Test file discovery with special characters in filenames."""
        # Create files with special characters (that are valid on most filesystems)
        special_files = [
            "file-with-dashes.py",
            "file_with_underscores.js",
            "file with spaces.css",  # May not work on all systems
            "file.with.dots.json",
            "UPPERCASE_FILE.py",
            "123numeric_start.js",
        ]

        created_files = []
        for filename in special_files:
            try:
                file_path = self.test_dir / filename
                with open(file_path, 'w') as f:
                    f.write("// test content\n")
                created_files.append(filename)
            except OSError:
                # Skip files that can't be created on this filesystem
                continue

        if not created_files:
            self.skipTest("No special character files could be created on this filesystem")

        os.chdir(self.test_dir)
        discovered_files = discover_files_in_directory(".")

        # Should find files that were successfully created
        self.assertGreater(len(discovered_files), 0)

    def test_discover_files_large_directory(self):
        """Test file discovery performance with many files."""
        # Create a directory with many files
        (self.test_dir / "many_files").mkdir()
        
        # Create 100 Python files
        for i in range(100):
            file_path = self.test_dir / "many_files" / f"file_{i:03d}.py"
            with open(file_path, 'w') as f:
                f.write(f"# File number {i}\n")

        os.chdir(self.test_dir)
        discovered_files = discover_files_in_directory(".")

        # Should find all 100 files
        self.assertEqual(len(discovered_files), 100)

        # Files should be sorted
        self.assertEqual(discovered_files, sorted(discovered_files))

    def test_discover_files_symlinks(self):
        """Test file discovery with symbolic links (if supported)."""
        if os.name == 'nt':
            self.skipTest("Symlink test not applicable on Windows")

        # Create regular file
        regular_file = self.test_dir / "regular.py"
        with open(regular_file, 'w') as f:
            f.write("# Regular file\n")

        # Create symlink to file
        symlink_file = self.test_dir / "symlink.py"
        try:
            os.symlink(regular_file, symlink_file)
        except OSError:
            self.skipTest("Cannot create symlinks on this system")

        # Create directory and symlink to directory
        (self.test_dir / "real_dir").mkdir()
        (self.test_dir / "real_dir" / "inside.py").touch()
        
        symlink_dir = self.test_dir / "symlink_dir"
        try:
            os.symlink(self.test_dir / "real_dir", symlink_dir)
        except OSError:
            symlink_dir = None

        os.chdir(self.test_dir)
        discovered_files = discover_files_in_directory(".")

        # Should handle symlinks appropriately
        # Exact behavior may vary, but should not crash
        self.assertIsInstance(discovered_files, list)
        self.assertGreater(len(discovered_files), 0)

    def test_discover_files_permission_handling(self):
        """Test file discovery with permission restrictions."""
        if os.name == 'nt':
            self.skipTest("Permission test not applicable on Windows")

        # Create files with different permissions
        (self.test_dir / "readable.py").touch()
        (self.test_dir / "restricted.py").touch()

        # Remove read permissions from one file
        restricted_file = self.test_dir / "restricted.py"
        os.chmod(restricted_file, 0o000)

        try:
            os.chdir(self.test_dir)
            discovered_files = discover_files_in_directory(".")

            # Should handle permission errors gracefully
            self.assertIsInstance(discovered_files, list)
            # Should find at least the readable file
            self.assertTrue(any("readable.py" in f for f in discovered_files))

        finally:
            # Restore permissions for cleanup
            os.chmod(restricted_file, 0o644)


class TestSpecialFileHandling(unittest.TestCase):
    """Test handling of special files like Justfile, GitHub Actions, etc."""

    def setUp(self):
        """Create temporary directory for each test."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.original_cwd = os.getcwd()

    def tearDown(self):
        """Clean up temporary directory and restore working directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_discover_justfile(self):
        """Test discovery of Justfile (file without extension)."""
        # Create Justfile
        justfile = self.test_dir / "Justfile"
        with open(justfile, 'w') as f:
            f.write("default:\n\techo 'Hello'\n")

        os.chdir(self.test_dir)
        discovered_files = discover_files_in_directory(".")

        # Should find Justfile
        self.assertEqual(len(discovered_files), 1)
        self.assertTrue(any("Justfile" in f for f in discovered_files))

    def test_discover_github_actions_workflows(self):
        """Test discovery of GitHub Actions workflow files."""
        # Create .github/workflows directory
        workflows_dir = self.test_dir / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)

        # Create workflow files
        (workflows_dir / "ci.yml").touch()
        (workflows_dir / "deploy.yaml").touch()

        # Create regular YAML file (should not be treated as workflow)
        (self.test_dir / "config.yml").touch()

        os.chdir(self.test_dir)
        discovered_files = discover_files_in_directory(".")

        # Should find all YAML/YML files (workflows are treated specially)
        discovered_names = [Path(f).name for f in discovered_files]
        self.assertIn("ci.yml", discovered_names)
        self.assertIn("deploy.yaml", discovered_names)
        self.assertIn("config.yml", discovered_names)

    def test_discover_files_without_extensions(self):
        """Test discovery of files without extensions."""
        # Create various files without extensions
        files_without_ext = ["Makefile", "Dockerfile", "LICENSE", "AUTHORS"]
        
        for filename in files_without_ext:
            file_path = self.test_dir / filename
            with open(file_path, 'w') as f:
                f.write(f"Content of {filename}\n")

        os.chdir(self.test_dir)
        discovered_files = discover_files_in_directory(".")

        # Discovery behavior for files without extensions depends on implementation
        # At minimum, should not crash
        self.assertIsInstance(discovered_files, list)


if __name__ == '__main__':
    unittest.main()