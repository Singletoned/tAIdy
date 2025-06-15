"""
Python linting tests using pytest-bdd.
"""
import pytest
from pytest_bdd import scenarios, given, when, then

# Import step definitions
from step_defs.common_steps import *

# Load scenarios from feature file
scenarios('features/python_linting.feature')


@pytest.fixture(autouse=True)
def setup_python_container(bdd_context, python311_container):
    """Set up Python container for BDD context."""
    bdd_context.current_container = python311_container
    return python311_container