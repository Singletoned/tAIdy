"""
Unsupported environment tests using pytest-bdd.
"""
import pytest
from pytest_bdd import scenarios, given, when, then

# Import step definitions
from step_defs.common_steps import *

# Load scenarios from feature file
scenarios('features/unsupported_environments.feature')


@pytest.fixture(autouse=True)
def setup_minimal_container(bdd_context, minimal_container):
    """Set up minimal container for BDD context."""
    bdd_context.current_container = minimal_container
    return minimal_container