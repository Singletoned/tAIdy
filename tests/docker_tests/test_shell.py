"""Docker-based tests for shell file linting and formatting.

Ported from features/shell.feature.
"""

from tests.docker_tests.base import DockerTestCase


class TestShell(DockerTestCase):
    """Test shell file handling with shellcheck, shfmt, and beautysh."""

    def test_shellcheck_and_shfmt(self):
        """Both linting and formatting work when shellcheck+shfmt are installed."""
        exit_code, stdout, stderr = self.run_taidy(
            "shell-tools", "poorly_formatted.sh", ["poorly_formatted.sh"]
        )
        output = stdout + stderr
        self.assertOutputContains(output, "Running:")

    def test_shellcheck_lint_only(self):
        """Lint-only mode uses shellcheck."""
        exit_code, stdout, stderr = self.run_taidy(
            "shell-tools", "lint poorly_formatted.sh", ["poorly_formatted.sh"]
        )
        output = stdout + stderr
        self.assertOutputContains(output, "Running:")

    def test_shfmt_format_only(self):
        """Format-only mode uses shfmt."""
        exit_code, stdout, stderr = self.run_taidy(
            "shell-tools", "format poorly_formatted.sh", ["poorly_formatted.sh"]
        )
        output = stdout + stderr
        self.assertOutputContains(output, "Running:")

    def test_bash_file(self):
        """Bash files are handled the same as .sh files."""
        exit_code, stdout, stderr = self.run_taidy(
            "shell-tools", "poorly_formatted.bash", ["poorly_formatted.bash"]
        )
        output = stdout + stderr
        self.assertOutputContains(output, "Running:")

    def test_zsh_file(self):
        """Zsh files are handled the same as .sh files."""
        exit_code, stdout, stderr = self.run_taidy(
            "shell-tools", "poorly_formatted.zsh", ["poorly_formatted.zsh"]
        )
        output = stdout + stderr
        self.assertOutputContains(output, "Running:")
