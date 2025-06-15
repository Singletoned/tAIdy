"""
CLI usage tests using pytest-bdd.
"""
import pytest
from pytest_bdd import scenarios, given, when, then

# Import step definitions
from step_defs.common_steps import *

# Load scenarios from feature file
scenarios('features/cli_usage.feature')


@pytest.fixture(autouse=True)
def setup_cli_container(bdd_context, node18_container):
    """Set up container for CLI usage tests."""
    bdd_context.current_container = node18_container
    return node18_container