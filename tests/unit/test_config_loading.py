#!/usr/bin/env python3
"""Unit tests for configuration loading functions."""

import json
import os
import sys
import unittest
from unittest.mock import MagicMock, mock_open, patch

# Add the parent directory to the path to import taidy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from taidy.cli import load_config


class TestConfigLoading(unittest.TestCase):
    """Test configuration loading functionality."""

    @patch("taidy.cli.Path")
    def test_load_config_valid_json(self, mock_path):
        """Test loading valid JSON configuration."""
        # Mock config content
        config_data = {"ignore": ["*.tmp", "build/*"]}
        config_json = json.dumps(config_data)

        # Mock Path behavior
        mock_config_path = MagicMock()
        mock_config_path.exists.return_value = True
        mock_config_path.is_file.return_value = True

        # Mock Path construction and iteration
        mock_path_obj = MagicMock()
        mock_path.return_value = mock_path_obj
        mock_path_obj.resolve.return_value.parents = [mock_path_obj, mock_path_obj.parent]

        # Mock the config file being found
        mock_path_obj.parent = mock_path_obj  # Simplified parent chain

        with patch("builtins.open", mock_open(read_data=config_json)):
            with patch.object(mock_path_obj, "__truediv__", return_value=mock_config_path):
                result = load_config(".")

        # Should return the loaded config when file exists and is valid
        expected = config_data
        self.assertEqual(result, expected)

    @patch("taidy.cli.Path")
    def test_load_config_invalid_json(self, mock_path):
        """Test loading invalid JSON configuration."""
        # Mock invalid JSON content
        invalid_json = '{"ignore": ["*.tmp",}'  # Missing closing bracket

        # Mock Path behavior
        mock_config_path = MagicMock()
        mock_config_path.exists.return_value = True
        mock_config_path.is_file.return_value = True

        # Mock Path construction and iteration
        mock_path_obj = MagicMock()
        mock_path.return_value = mock_path_obj
        mock_path_obj.resolve.return_value.parents = [mock_path_obj, mock_path_obj.parent]
        mock_path_obj.parent = mock_path_obj

        with patch("builtins.open", mock_open(read_data=invalid_json)):
            with patch.object(mock_path_obj, "__truediv__", return_value=mock_config_path):
                with patch("taidy.cli.logger") as mock_logger:
                    result = load_config(".")

        # Should return empty config and log warning
        self.assertEqual(result, {})
        mock_logger.warning.assert_called_once()

    @patch("taidy.cli.Path")
    def test_load_config_no_file(self, mock_path):
        """Test behavior when no config file exists."""
        # Mock Path behavior - no config file found
        mock_config_path = MagicMock()
        mock_config_path.exists.return_value = False

        mock_path_obj = MagicMock()
        mock_path.return_value = mock_path_obj
        mock_path_obj.resolve.return_value.parents = [
            mock_path_obj,
            mock_path_obj.parent,
            mock_path_obj.parent.parent,
        ]
        mock_path_obj.parent = mock_path_obj

        with patch.object(mock_path_obj, "__truediv__", return_value=mock_config_path):
            result = load_config(".")

        # Should return empty config when no file found
        self.assertEqual(result, {})

    @patch("taidy.cli.Path")
    def test_load_config_permission_error(self, mock_path):
        """Test behavior when config file can't be read due to permissions."""
        # Mock Path behavior
        mock_config_path = MagicMock()
        mock_config_path.exists.return_value = True
        mock_config_path.is_file.return_value = True

        mock_path_obj = MagicMock()
        mock_path.return_value = mock_path_obj
        mock_path_obj.resolve.return_value.parents = [mock_path_obj, mock_path_obj.parent]
        mock_path_obj.parent = mock_path_obj

        # Mock permission error when opening file
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with patch.object(mock_path_obj, "__truediv__", return_value=mock_config_path):
                with patch("taidy.cli.logger") as mock_logger:
                    result = load_config(".")

        # Should return empty config and log warning
        self.assertEqual(result, {})
        mock_logger.warning.assert_called_once()

    @patch("taidy.cli.Path")
    def test_load_config_directory_tree_search(self, mock_path):
        """Test that config is searched up the directory tree."""
        # Mock config content
        config_data = {"ignore": ["*.test"]}
        config_json = json.dumps(config_data)

        # Mock Path behavior - config found in parent directory
        mock_config_path1 = MagicMock()
        mock_config_path1.exists.return_value = False  # Not in current dir

        mock_config_path2 = MagicMock()
        mock_config_path2.exists.return_value = True  # Found in parent
        mock_config_path2.is_file.return_value = True

        mock_path_obj = MagicMock()
        mock_path.return_value = mock_path_obj
        mock_path_obj.resolve.return_value.parents = [
            mock_path_obj,
            mock_path_obj.parent,
            mock_path_obj.parent.parent,
        ]

        def mock_truediv(other):
            if str(other) == ".taidy.json":
                # Return different mocks for different directory levels
                if hasattr(mock_truediv, "call_count"):
                    mock_truediv.call_count += 1
                else:
                    mock_truediv.call_count = 1

                if mock_truediv.call_count == 1:
                    return mock_config_path1  # First call - current dir (not found)
                else:
                    return mock_config_path2  # Second call - parent dir (found)
            return MagicMock()

        # Setup the path traversal
        mock_path_obj.__truediv__ = mock_truediv
        mock_path_obj.parent = mock_path_obj  # Simplified parent chain

        with patch("builtins.open", mock_open(read_data=config_json)):
            result = load_config("deep/nested/path")

        self.assertEqual(result, config_data)

    def test_load_config_empty_file(self):
        """Test loading empty configuration file."""
        with patch("taidy.cli.Path") as mock_path:
            # Mock Path behavior
            mock_config_path = MagicMock()
            mock_config_path.exists.return_value = True
            mock_config_path.is_file.return_value = True

            mock_path_obj = MagicMock()
            mock_path.return_value = mock_path_obj
            mock_path_obj.resolve.return_value.parents = [mock_path_obj]

            with patch("builtins.open", mock_open(read_data="")):
                with patch.object(mock_path_obj, "__truediv__", return_value=mock_config_path):
                    with patch("taidy.cli.logger") as mock_logger:
                        result = load_config(".")

            # Should return empty config and log error for empty JSON
            self.assertEqual(result, {})
            mock_logger.error.assert_called_once()

    def test_load_config_with_unknown_fields(self):
        """Test loading config with unknown fields."""
        # Mock config with unknown field
        config_data = {"ignore": ["*.tmp"], "unknown_field": "value", "another_unknown": 123}
        config_json = json.dumps(config_data)

        with patch("taidy.cli.Path") as mock_path:
            # Mock Path behavior
            mock_config_path = MagicMock()
            mock_config_path.exists.return_value = True
            mock_config_path.is_file.return_value = True

            mock_path_obj = MagicMock()
            mock_path.return_value = mock_path_obj
            mock_path_obj.resolve.return_value.parents = [mock_path_obj]

            with patch("builtins.open", mock_open(read_data=config_json)):
                with patch.object(mock_path_obj, "__truediv__", return_value=mock_config_path):
                    result = load_config(".")

            # Should return the config including unknown fields
            self.assertEqual(result, config_data)


if __name__ == "__main__":
    unittest.main()
