"""
Go linting tests using pytest-bdd.
"""
import pytest
from pytest_bdd import scenarios, given, when, then

# Import step definitions
from step_defs.common_steps import *

# Load scenarios from feature file
scenarios('features/go_linting.feature')


@pytest.fixture(autouse=True)
def setup_go_container(bdd_context, go121_container):
    """Set up Go container for BDD context."""
    bdd_context.current_container = go121_container
    return go121_container