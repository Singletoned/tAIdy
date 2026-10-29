"""Docker-based tests for HTML formatting."""

import shutil
import tempfile
from pathlib import Path

from tests.docker_tests.base import SAMPLE_FILES, DockerTestCase


class TestHtml(DockerTestCase):
    """Test HTML formatting with Prettier."""

    def test_formatting_inline_style_is_idempotent(self):
        """Taidy settles Prettier's inline-style formatting in one invocation."""
        with tempfile.TemporaryDirectory() as directory:
            working_directory = Path(directory)
            html_file = working_directory / "inline_style.html"
            shutil.copy2(SAMPLE_FILES / html_file.name, html_file)

            first_exit_code, _stdout, _stderr = self.run_taidy(
                "node18", f"format {html_file.name}", working_directory=working_directory
            )
            first_contents = html_file.read_bytes()
            second_exit_code, _stdout, _stderr = self.run_taidy(
                "node18", f"format {html_file.name}", working_directory=working_directory
            )

            self.assertEqual(first_exit_code, 0)
            self.assertEqual(second_exit_code, 0)
            self.assertEqual(html_file.read_bytes(), first_contents)
