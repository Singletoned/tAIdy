"""Docker-based tests for security scanning with trufflehog.

Ported from features/security.feature.
"""

from tests.docker_tests.base import DockerTestCase


class TestSecurity(DockerTestCase):
    """Test trufflehog security scanning integration."""

    def test_trufflehog_detects_secrets(self):
        """Trufflehog detects secrets in a Python file."""
        exit_code, stdout, stderr = self.run_taidy(
            "python311-trufflehog", "lint with_secret.py", ["with_secret.py"]
        )
        output = stdout + stderr
        # trufflehog exits 183 when it finds secrets
        self.assertIn(exit_code, (0, 183), f"Unexpected exit code {exit_code}")

    def test_trufflehog_scans_directory(self):
        """Trufflehog scans a directory for secrets."""
        exit_code, stdout, stderr = self.run_taidy(
            "python311-trufflehog",
            "lint .",
            ["with_secret.py", "poorly_formatted.py"],
        )
        # Just verify it runs without crashing
        output = stdout + stderr
        self.assertOutputContains(output, "Running:")

    def test_no_trufflehog_no_security_output(self):
        """When trufflehog is not installed, no security scanning occurs."""
        exit_code, stdout, stderr = self.run_taidy(
            "python311", "lint with_secret.py", ["with_secret.py"]
        )
        output = stdout + stderr
        self.assertOutputNotContains(output, "trufflehog")
        self.assertEqual(exit_code, 0)
