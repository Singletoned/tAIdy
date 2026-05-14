"""Docker-based tests for Markdown linting and formatting.

Ported from features/markdown.feature.
"""

from tests.docker_tests.base import DockerTestCase


class TestMarkdown(DockerTestCase):
    """Test Markdown file handling with prettier."""

    def test_format_with_prettier(self):
        """Prettier formats markdown files."""
        exit_code, stdout, stderr = self.run_taidy(
            "node18", "format poorly_formatted.md", ["poorly_formatted.md"]
        )
        output = stdout + stderr
        self.assertOutputContains(output, "Running:")

    def test_lint_with_prettier(self):
        """Prettier lints markdown files."""
        exit_code, stdout, stderr = self.run_taidy(
            "node18", "lint poorly_formatted.md", ["poorly_formatted.md"]
        )
        output = stdout + stderr
        self.assertOutputContains(output, "Running:")

    def test_both_with_prettier(self):
        """Default mode lints and formats markdown with prettier."""
        exit_code, stdout, stderr = self.run_taidy(
            "node18", "poorly_formatted.md", ["poorly_formatted.md"]
        )
        output = stdout + stderr
        self.assertOutputContains(output, "Running:")

    def test_no_prettier_warns(self):
        """When prettier is not installed, warnings are shown."""
        exit_code, stdout, stderr = self.run_taidy(
            "minimal", "poorly_formatted.md", ["poorly_formatted.md"]
        )
        output = stdout + stderr
        self.assertOutputContains(output, "No available linter found for .md files")
        self.assertOutputContains(output, "No available formatter found for .md files")
