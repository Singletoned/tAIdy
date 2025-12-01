#!/usr/bin/env python3
"""Unit tests for tool detection functions."""

import os
import sys
import unittest
from unittest.mock import patch

# Add the parent directory to the path to import taidy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from taidy.cli import detect_linux_distribution, get_platform_info, is_command_available


class TestToolDetection(unittest.TestCase):
    """Test tool detection functionality."""

    @patch('shutil.which')
    def test_is_command_available_found(self, mock_which):
        """Test command availability when command exists."""
        mock_which.return_value = "/usr/bin/python3"
        
        result = is_command_available("python3")
        
        self.assertTrue(result)
        mock_which.assert_called_once_with("python3")

    @patch('shutil.which')
    def test_is_command_available_not_found(self, mock_which):
        """Test command availability when command doesn't exist."""
        mock_which.return_value = None
        
        result = is_command_available("nonexistent_command")
        
        self.assertFalse(result)
        mock_which.assert_called_once_with("nonexistent_command")

    @patch('shutil.which')
    def test_is_command_available_caching(self, mock_which):
        """Test that command availability is cached."""
        mock_which.return_value = "/usr/bin/python3"
        
        # Call twice
        result1 = is_command_available("python3")
        result2 = is_command_available("python3")
        
        self.assertTrue(result1)
        self.assertTrue(result2)
        # Should only call shutil.which once due to caching
        mock_which.assert_called_once_with("python3")

    @patch('shutil.which')
    def test_is_command_available_different_commands(self, mock_which):
        """Test availability check for different commands."""
        def which_side_effect(cmd):
            return "/usr/bin/python3" if cmd == "python3" else None
        
        mock_which.side_effect = which_side_effect
        
        result_python = is_command_available("python3")
        result_missing = is_command_available("missing_tool")
        
        self.assertTrue(result_python)
        self.assertFalse(result_missing)


class TestPlatformDetection(unittest.TestCase):
    """Test platform detection functionality."""

    @patch('platform.system')
    @patch('platform.release')
    @patch('platform.machine')
    @patch('taidy.cli.detect_linux_distribution')
    def test_get_platform_info_linux(self, mock_detect_linux, mock_machine, mock_release, mock_system):
        """Test platform info detection on Linux."""
        mock_system.return_value = "Linux"
        mock_release.return_value = "5.4.0"
        mock_machine.return_value = "x86_64"
        mock_detect_linux.return_value = {"id": "ubuntu", "version": "20.04"}
        
        result = get_platform_info()
        
        expected = {
            "system": "Linux",
            "release": "5.4.0", 
            "machine": "x86_64",
            "distribution": {"id": "ubuntu", "version": "20.04"}
        }
        self.assertEqual(result, expected)

    @patch('platform.system')
    @patch('platform.release')
    @patch('platform.machine')
    @patch('taidy.cli.detect_linux_distribution')
    def test_get_platform_info_macos(self, mock_detect_linux, mock_machine, mock_release, mock_system):
        """Test platform info detection on macOS."""
        mock_system.return_value = "Darwin"
        mock_release.return_value = "20.6.0"
        mock_machine.return_value = "x86_64"
        mock_detect_linux.return_value = None  # Not Linux
        
        result = get_platform_info()
        
        expected = {
            "system": "Darwin",
            "release": "20.6.0",
            "machine": "x86_64", 
            "distribution": None
        }
        self.assertEqual(result, expected)

    @patch('platform.system')
    @patch('platform.release')
    @patch('platform.machine')
    @patch('taidy.cli.detect_linux_distribution')
    def test_get_platform_info_windows(self, mock_detect_linux, mock_machine, mock_release, mock_system):
        """Test platform info detection on Windows."""
        mock_system.return_value = "Windows"
        mock_release.return_value = "10"
        mock_machine.return_value = "AMD64"
        mock_detect_linux.return_value = None  # Not Linux
        
        result = get_platform_info()
        
        expected = {
            "system": "Windows",
            "release": "10",
            "machine": "AMD64",
            "distribution": None
        }
        self.assertEqual(result, expected)


class TestLinuxDistributionDetection(unittest.TestCase):
    """Test Linux distribution detection functionality."""

    @patch('builtins.open')
    @patch('os.path.exists')
    def test_detect_linux_distribution_ubuntu(self, mock_exists, mock_open_func):
        """Test detection of Ubuntu distribution."""
        # Mock os-release file content
        os_release_content = '''ID=ubuntu
VERSION_ID="20.04"
NAME="Ubuntu"
VERSION="20.04.3 LTS (Focal Fossa)"
'''
        
        mock_exists.return_value = True
        mock_open_func.return_value.__enter__.return_value = os_release_content.splitlines()
        
        result = detect_linux_distribution()
        
        expected = {"id": "ubuntu", "version": "20.04"}
        self.assertEqual(result, expected)

    @patch('builtins.open')
    @patch('os.path.exists')
    def test_detect_linux_distribution_centos(self, mock_exists, mock_open_func):
        """Test detection of CentOS distribution."""
        os_release_content = '''ID="centos"
VERSION_ID="8"
NAME="CentOS Linux"
VERSION="8 (Core)"
'''
        
        mock_exists.return_value = True
        mock_open_func.return_value.__enter__.return_value = os_release_content.splitlines()
        
        result = detect_linux_distribution()
        
        expected = {"id": "centos", "version": "8"}
        self.assertEqual(result, expected)

    @patch('builtins.open')
    @patch('os.path.exists')
    def test_detect_linux_distribution_no_file(self, mock_exists, mock_open_func):
        """Test when os-release file doesn't exist."""
        mock_exists.return_value = False
        
        result = detect_linux_distribution()
        
        self.assertIsNone(result)

    @patch('builtins.open')
    @patch('os.path.exists')
    def test_detect_linux_distribution_read_error(self, mock_exists, mock_open_func):
        """Test when os-release file can't be read."""
        mock_exists.return_value = True
        mock_open_func.side_effect = IOError("Permission denied")
        
        result = detect_linux_distribution()
        
        self.assertIsNone(result)

    @patch('builtins.open')
    @patch('os.path.exists')
    def test_detect_linux_distribution_malformed_file(self, mock_exists, mock_open_func):
        """Test with malformed os-release file."""
        # File without ID or VERSION_ID
        os_release_content = '''NAME="Some Linux"
VERSION="1.0"
'''
        
        mock_exists.return_value = True
        mock_open_func.return_value.__enter__.return_value = os_release_content.splitlines()
        
        result = detect_linux_distribution()
        
        # Should return None or partial info
        # The function should handle missing required fields gracefully
        if result is not None:
            self.assertIn("id", result)

    @patch('builtins.open')
    @patch('os.path.exists')
    def test_detect_linux_distribution_quoted_values(self, mock_exists, mock_open_func):
        """Test parsing of quoted values in os-release."""
        os_release_content = '''ID="fedora"
VERSION_ID="35"
NAME="Fedora Linux"
'''
        
        mock_exists.return_value = True
        mock_open_func.return_value.__enter__.return_value = os_release_content.splitlines()
        
        result = detect_linux_distribution()
        
        expected = {"id": "fedora", "version": "35"}
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()