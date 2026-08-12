"""Docker-based tests for the production Dockerfile."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from taidy.cli import ADAPTER_MANIFEST
from tests.docker_tests.base import PROJECT_ROOT

IMAGE_TAG = "taidy:test-build"


@unittest.skipUnless(shutil.which("docker"), "Docker not available")
class TestDockerBuild(unittest.TestCase):
    """Build and validate the exact image users receive."""

    @classmethod
    def setUpClass(cls):
        result = subprocess.run(
            ["docker", "build", "-t", IMAGE_TAG, "."],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
        if result.returncode:
            raise RuntimeError(f"Docker build failed:\n{result.stderr}")

    def test_dockerfile_entrypoint_runs_taidy(self):
        """The image entrypoint invokes the packaged Taidy CLI."""
        result = subprocess.run(
            ["docker", "run", "--rm", IMAGE_TAG, "--version"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("taidy", result.stdout.lower())

    def test_docker_image_contains_manifest_tools(self):
        """Every Docker-supported manifest suggestion is executable in the image."""
        for selector, adapter in ADAPTER_MANIFEST.items():
            if adapter.docker_status != "supported":
                continue
            for tool in adapter.suggestion_tools:
                with self.subTest(selector=selector, tool=tool):
                    result = subprocess.run(
                        [
                            "docker",
                            "run",
                            "--rm",
                            "--entrypoint",
                            "sh",
                            IMAGE_TAG,
                            "-c",
                            f"command -v {tool}",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        check=False,
                    )
                    self.assertEqual(
                        result.returncode,
                        0,
                        f"{selector} requires {tool}, but it is absent from the Docker image:\n"
                        f"{result.stderr}",
                    )

    def test_docker_image_reports_unsupported_files_in_json(self):
        """JSON reports an existing unsupported file as not checked without failing."""
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            workspace.joinpath("unknown.flibble").write_text("content\n")
            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{workspace}:/workspace",
                    "-w",
                    "/workspace",
                    IMAGE_TAG,
                    "--json",
                    "unknown.flibble",
                ],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout)["not_checked"],
            ["unknown.flibble: no adapter for both"],
        )

    def test_docker_image_dry_run_does_not_modify_files(self):
        """Dry runs expose selected commands without changing the mounted workspace."""
        source = "value=1\n"
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            source_path = workspace / "example.py"
            source_path.write_text(source)
            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{workspace}:/workspace",
                    "-w",
                    "/workspace",
                    IMAGE_TAG,
                    "--dry-run",
                    "example.py",
                ],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            contents_after_run = source_path.read_text()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ruff format --quiet example.py", result.stdout)
        self.assertIn("ruff check --quiet example.py", result.stdout)
        self.assertEqual(contents_after_run, source)
