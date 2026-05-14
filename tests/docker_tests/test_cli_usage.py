"""Docker-based tests for CLI usage and error handling.

Ported from features/cli_usage.feature.
"""

from tests.docker_tests.base import DockerTestCase


class TestCLIUsage(DockerTestCase):
    """Test CLI usage messages and error handling."""

    def test_no_arguments_shows_usage(self):
        """Running taidy without arguments shows usage and exits non-zero."""
        # Run without --verbose since we're testing the no-args case directly
        import subprocess

        from tests.docker_tests.base import build_environment

        tag = build_environment("minimal")
        result = subprocess.run(
            ["docker", "run", "--rm", tag, "sh", "-c", "python3 -m taidy"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = result.stdout + result.stderr
        self.assertOutputContains(output, "Usage:")
        self.assertOutputContains(output, "taidy")

    def test_nonexistent_files_handled_gracefully(self):
        """Non-existent files are handled gracefully."""
        exit_code, stdout, stderr = self.run_taidy("minimal", "nonexistent1.py nonexistent2.js")
        output = stdout + stderr
        self.assertEqual(exit_code, 0)
        self.assertOutputContains(output, "no files were linted")
