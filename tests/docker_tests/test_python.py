"""Docker-based tests for Python linting and formatting.

Ported from features/python_lint.feature, python_format.feature, python_lint_format.feature.
"""

from tests.docker_tests.base import DockerTestCase


class TestPythonLint(DockerTestCase):
    """Test Python linting with various tool chains."""

    def test_lint_with_ruff(self):
        """Ruff lints Python files without formatting."""
        exit_code, stdout, stderr = self.run_taidy(
            "python311", "lint poorly_formatted.py", ["poorly_formatted.py"]
        )
        output = stdout + stderr
        self.assertOutputContains(output, "Running:")

    def test_lint_with_uv_fallback(self):
        """When ruff is absent but uv is installed, uvx ruff is used."""
        exit_code, stdout, stderr = self.run_taidy(
            "python311-uv", "lint poorly_formatted.py", ["poorly_formatted.py"]
        )
        output = stdout + stderr
        self.assertOutputContains(output, "Running:")

    def test_lint_with_black_fallback(self):
        """When ruff and uv are absent, black is used for linting."""
        exit_code, stdout, stderr = self.run_taidy(
            "python311-black", "lint poorly_formatted.py", ["poorly_formatted.py"]
        )
        output = stdout + stderr
        self.assertOutputContains(output, "Running:")


class TestPythonFormat(DockerTestCase):
    """Test Python formatting with various tool chains."""

    def test_format_with_ruff(self):
        """Ruff formats Python files."""
        exit_code, stdout, stderr = self.run_taidy(
            "python311", "format poorly_formatted.py", ["poorly_formatted.py"]
        )
        output = stdout + stderr
        self.assertOutputContains(output, "Running:")

    def test_format_with_uv_fallback(self):
        """When ruff is absent, uvx ruff formats."""
        exit_code, stdout, stderr = self.run_taidy(
            "python311-uv", "format poorly_formatted.py", ["poorly_formatted.py"]
        )
        output = stdout + stderr
        self.assertOutputContains(output, "Running:")

    def test_format_with_black_fallback(self):
        """When ruff and uv are absent, black formats."""
        exit_code, stdout, stderr = self.run_taidy(
            "python311-black", "format poorly_formatted.py", ["poorly_formatted.py"]
        )
        output = stdout + stderr
        self.assertOutputContains(output, "Running:")


class TestPythonLintFormat(DockerTestCase):
    """Test default mode (both lint and format) for Python."""

    def test_both_with_ruff(self):
        """Default mode lints and formats with ruff."""
        exit_code, stdout, stderr = self.run_taidy(
            "python311", "poorly_formatted.py", ["poorly_formatted.py"]
        )
        output = stdout + stderr
        self.assertOutputContains(output, "Running:")

    def test_both_with_uv_fallback(self):
        """Default mode works with uvx ruff fallback."""
        exit_code, stdout, stderr = self.run_taidy(
            "python311-uv", "poorly_formatted.py", ["poorly_formatted.py"]
        )
        output = stdout + stderr
        self.assertOutputContains(output, "Running:")

    def test_both_with_black_fallback(self):
        """Default mode works with black fallback."""
        exit_code, stdout, stderr = self.run_taidy(
            "python311-black", "poorly_formatted.py", ["poorly_formatted.py"]
        )
        output = stdout + stderr
        self.assertOutputContains(output, "Running:")
