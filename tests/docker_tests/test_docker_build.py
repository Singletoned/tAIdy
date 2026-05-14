"""Docker-based tests for the main Dockerfile build.

Ported from features/docker_build.feature.
"""

import shutil
import subprocess
import unittest

from tests.docker_tests.base import PROJECT_ROOT


@unittest.skipUnless(shutil.which("docker"), "Docker not available")
class TestDockerBuild(unittest.TestCase):
    """Test that the production Dockerfile builds and works."""

    @unittest.skip("Slow: builds the full production image with all tools")
    def test_dockerfile_builds_successfully(self):
        """The production Dockerfile builds without errors."""
        result = subprocess.run(
            ["docker", "build", "-t", "taidy:test-build", "."],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=600,
        )
        self.assertEqual(result.returncode, 0, f"Docker build failed:\n{result.stderr}")

    @unittest.skip("Slow: builds the full production image with all tools")
    def test_docker_image_contains_tools(self):
        """The built image contains key tools."""
        # This depends on the image being built by the previous test
        tools = ["ruff", "black", "prettier", "gofmt"]
        for tool in tools:
            result = subprocess.run(
                ["docker", "run", "--rm", "taidy:test-build", "which", tool],
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, f"Tool {tool} not found in Docker image")
