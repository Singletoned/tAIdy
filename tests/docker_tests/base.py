"""Base class for Docker-based integration tests.

Provides helpers to build Docker images and run taidy commands inside containers.
Ported from the Go testcontainer infrastructure.
"""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

# Project root is two levels up from this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SAMPLE_FILES = PROJECT_ROOT / "tests" / "sample_files"

# Dockerfile templates for each test environment
DOCKERFILES = {
    "python311": """\
FROM python:3.11-slim
RUN pip install ruff
COPY taidy /app/taidy
ENV PYTHONPATH=/app
WORKDIR /tmp
""",
    "python311-uv": """\
FROM python:3.11-slim
RUN pip install uv
COPY taidy /app/taidy
ENV PYTHONPATH=/app
WORKDIR /tmp
""",
    "python311-black": """\
FROM python:3.11-slim
RUN pip install black
COPY taidy /app/taidy
ENV PYTHONPATH=/app
WORKDIR /tmp
""",
    "python311-trufflehog": (  # noqa: E501
        "FROM python:3.11-slim\n"
        "RUN pip install ruff\n"
        "RUN apt-get update && apt-get install -y wget && \\\n"
        "    wget -O /tmp/trufflehog.tar.gz \\\n"
        "    https://github.com/trufflesecurity/trufflehog/releases/"
        "download/v3.89.2/trufflehog_3.89.2_linux_amd64.tar.gz && \\\n"
        "    tar -xzf /tmp/trufflehog.tar.gz -C /usr/local/bin/ && \\\n"
        "    chmod +x /usr/local/bin/trufflehog && \\\n"
        "    rm /tmp/trufflehog.tar.gz\n"
        "COPY taidy /app/taidy\n"
        "ENV PYTHONPATH=/app\n"
        "WORKDIR /tmp\n"
    ),
    "node18": """\
FROM node:18-slim
RUN apt-get update && apt-get install -y python3
RUN npm install -g prettier
COPY taidy /app/taidy
ENV PYTHONPATH=/app
WORKDIR /tmp
""",
    "go121": """\
FROM golang:1.24-alpine
RUN apk add --no-cache python3
COPY taidy /app/taidy
ENV PYTHONPATH=/app
WORKDIR /tmp
""",
    "shell-tools": """\
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y shellcheck
RUN apt-get install -y wget && \
    wget -O /usr/local/bin/shfmt \
    https://github.com/mvdan/sh/releases/download/v3.7.0/shfmt_v3.7.0_linux_amd64 && \
    chmod +x /usr/local/bin/shfmt
RUN apt-get install -y python3 python3-pip && pip3 install beautysh
COPY taidy /app/taidy
ENV PYTHONPATH=/app
WORKDIR /tmp
""",
    "minimal": """\
FROM alpine:latest
RUN apk add --no-cache python3
COPY taidy /app/taidy
ENV PYTHONPATH=/app
WORKDIR /tmp
""",
}

# Cache for built image tags so we don't rebuild within a test run
_built_images: dict = {}


def _docker_available() -> bool:
    """Check if Docker is available."""
    return shutil.which("docker") is not None


def build_environment(name: str) -> str:
    """Build a Docker image for the given environment name.

    Returns the image tag. Caches so repeated calls are free.
    """
    if name in _built_images:
        return _built_images[name]

    if name not in DOCKERFILES:
        raise ValueError(f"Unknown environment: {name}")

    tag = f"taidy-test:{name}"
    build_dir = tempfile.mkdtemp(prefix="taidy-docker-test-")
    try:
        # Write Dockerfile
        dockerfile = os.path.join(build_dir, "Dockerfile")
        with open(dockerfile, "w") as f:
            f.write(DOCKERFILES[name])

        # Copy the taidy package into the build context
        shutil.copytree(PROJECT_ROOT / "taidy", os.path.join(build_dir, "taidy"))

        # Build image
        result = subprocess.run(
            ["docker", "build", "-t", tag, "."],
            cwd=build_dir,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Docker build failed for {name}:\nstdout: {result.stdout}\nstderr: {result.stderr}"
            )
    finally:
        shutil.rmtree(build_dir, ignore_errors=True)

    _built_images[name] = tag
    return tag


def run_taidy(image_tag: str, command: str, sample_files: list[str] | None = None) -> tuple:
    """Run a taidy command inside a container.

    Args:
        image_tag: Docker image tag to use.
        command: The taidy command string (e.g. "lint poorly_formatted.py").
        sample_files: List of filenames from tests/sample_files/ to copy in.

    Returns:
        (exit_code, stdout, stderr) tuple.
    """
    # Build the docker run command
    docker_cmd = ["docker", "run", "--rm"]

    # Copy sample files into container via volume mount of a temp dir
    tmp_dir = None
    if sample_files:
        tmp_dir = tempfile.mkdtemp(prefix="taidy-test-files-")
        for filename in sample_files:
            src = SAMPLE_FILES / filename
            if src.exists():
                shutil.copy2(src, os.path.join(tmp_dir, filename))
        docker_cmd.extend(["-v", f"{tmp_dir}:/tmp/workdir"])
        docker_cmd.extend(["-w", "/tmp/workdir"])

    docker_cmd.append(image_tag)
    docker_cmd.extend(["sh", "-c", f"python3 -m taidy --verbose {command}"])

    try:
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return result.returncode, result.stdout, result.stderr
    finally:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)


@unittest.skipUnless(_docker_available(), "Docker not available")
class DockerTestCase(unittest.TestCase):
    """Base class for Docker-based tests.

    Skips automatically if Docker is not available.
    """

    def run_taidy(self, env_name: str, command: str, sample_files: list[str] | None = None):
        """Build environment and run taidy, returning (exit_code, stdout, stderr)."""
        tag = build_environment(env_name)
        return run_taidy(tag, command, sample_files)

    def assertOutputContains(self, output: str, text: str, msg: str | None = None):
        """Assert that combined output contains the given text."""
        if text not in output:
            self.fail(msg or f"Expected output to contain {text!r}, got:\n{output}")

    def assertOutputNotContains(self, output: str, text: str, msg: str | None = None):
        """Assert that combined output does NOT contain the given text."""
        if text in output:
            self.fail(msg or f"Expected output to NOT contain {text!r}, got:\n{output}")
