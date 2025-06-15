"""
JavaScript linting tests using pytest-bdd.
"""
import pytest
from pytest_bdd import scenarios, given, when, then

# Import step definitions
from step_defs.common_steps import *

# Load scenarios from feature file
scenarios('features/javascript_linting.feature')


@pytest.fixture(autouse=True)
def setup_javascript_container(bdd_context, node18_container):
    """Set up JavaScript container for BDD context."""
    bdd_context.current_container = node18_container
    return node18_container