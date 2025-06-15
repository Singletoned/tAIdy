"""
Common step definitions for pytest-bdd CLI testing scenarios.
"""
import re
import logging
from pathlib import Path
from typing import Dict, Any

from pytest_bdd import given, when, then, parsers
import pytest

logger = logging.getLogger(__name__)


# File creation steps
@given('the following Python file exists')
def step_create_python_file(bdd_context, step):
    """Create a Python test file with the given content."""
    if not hasattr(bdd_context, 'test_files'):
        bdd_context.test_files = []
        
    # Get file content from step data (docstring)
    content = step.doc_string.content if step.doc_string else ""
    filename = f"test_{len(bdd_context.test_files) + 1}.py"
    
    # Create file in container
    if bdd_context.current_container:
        bdd_context.current_container.create_file(filename, content)
        bdd_context.test_files.append(filename)
    else:
        pytest.fail("No container available for testing")


@given('the following JavaScript file exists')
def step_create_javascript_file(bdd_context, step):
    """Create a JavaScript test file with the given content."""
    if not hasattr(bdd_context, 'test_files'):
        bdd_context.test_files = []
        
    # Get file content from step data (docstring)
    content = step.doc_string.content if step.doc_string else ""
    filename = f"test_{len(bdd_context.test_files) + 1}.js"
    
    # Create file in container
    if bdd_context.current_container:
        bdd_context.current_container.create_file(filename, content)
        bdd_context.test_files.append(filename)
    else:
        pytest.fail("No container available for testing")


@given('the following Go file exists')
def step_create_go_file(bdd_context, step):
    """Create a Go test file with the given content."""
    if not hasattr(bdd_context, 'test_files'):
        bdd_context.test_files = []
        
    # Get file content from step data (docstring)
    content = step.doc_string.content if step.doc_string else ""
    filename = f"test_{len(bdd_context.test_files) + 1}.go"
    
    
    # Create file in container
    if bdd_context.current_container:
        bdd_context.current_container.create_file(filename, content)
        bdd_context.test_files.append(filename)
    else:
        pytest.fail("No container available for testing")


@given('the following files exist')
def step_create_multiple_files(bdd_context, step):
    """Create multiple test files from table data."""
    if not hasattr(bdd_context, 'test_files'):
        bdd_context.test_files = []
        
    # Parse table data from step data
    if not step.table:
        return
        
    # Process table data directly
    for row in step.table:
        filename = row['filename']
        content = row['content']
        
        # Unescape content
        content = content.replace('\\n', '\n')
        
        # Create file in container
        if bdd_context.current_container:
            bdd_context.current_container.create_file(filename, content)
            bdd_context.test_files.append(filename)
        else:
            pytest.fail("No container available for testing")


# Linter verification steps
@given(parsers.parse('{linter} is installed'))
def step_verify_linter_installed(bdd_context, linter: str):
    """Verify that a linter is installed in the container."""
    if not bdd_context.current_container:
        pytest.fail("No container available for testing")
        
    if not bdd_context.current_container.verify_linter_installed(linter):
        pytest.fail(f"Linter {linter} is not installed in the container")


@given(parsers.parse('{linter} is not installed'))
def step_verify_linter_not_installed(bdd_context, linter: str):
    """Verify that a linter is NOT installed in the container."""
    if not bdd_context.current_container:
        pytest.fail("No container available for testing")
        
    if bdd_context.current_container.verify_linter_installed(linter):
        pytest.fail(f"Linter {linter} should not be installed in the container")


# CLI execution steps
@when(parsers.parse('lintair is called with {file_pattern} filenames'))
def step_run_lintair_with_files(bdd_context, file_pattern: str):
    """Run lintair with files matching the pattern."""
    if not bdd_context.current_container:
        pytest.fail("No container available for testing")
        
    # Filter test files based on pattern
    pattern_map = {
        'Python': r'\.py$',
        'JavaScript': r'\.(js|jsx)$',
        'TypeScript': r'\.(ts|tsx)$',
        'Go': r'\.go$',
        'JSON': r'\.json$',
        'CSS': r'\.(css|scss)$',
        'HTML': r'\.html$'
    }
    
    if file_pattern in pattern_map:
        regex_pattern = pattern_map[file_pattern]
        matching_files = [f for f in bdd_context.test_files if re.search(regex_pattern, f)]
    else:
        # Assume it's a literal pattern
        matching_files = [f for f in bdd_context.test_files if file_pattern in f]
    
    if not matching_files:
        pytest.fail(f"No files found matching pattern: {file_pattern}")
    
    # Run lintair with matching files
    files_str = ' '.join(matching_files)
    cmd = f"/app/lintair {files_str}"
    
    result = bdd_context.current_container.execute_command(cmd)
    bdd_context.command_result = result


@when('lintair is called with the files')
def step_run_lintair_with_test_files(bdd_context):
    """Run lintair with all test files."""
    if not bdd_context.current_container:
        pytest.fail("No container available for testing")
        
    if not hasattr(bdd_context, 'test_files') or not bdd_context.test_files:
        pytest.fail("No test files available")
    
    # Run lintair with all test files
    files_str = ' '.join(bdd_context.test_files)
    cmd = f"/app/lintair {files_str}"
    
    result = bdd_context.current_container.execute_command(cmd)
    bdd_context.command_result = result


@when('lintair is called with no arguments')
def step_run_lintair_no_args(bdd_context):
    """Run lintair with no arguments."""
    if not bdd_context.current_container:
        pytest.fail("No container available for testing")
    
    cmd = "/app/lintair"
    result = bdd_context.current_container.execute_command(cmd)
    bdd_context.command_result = result


# Assertion steps
@then(parsers.parse('the exit code should be {expected_code:d}'))
def step_check_exit_code(bdd_context, expected_code: int):
    """Check that the command exit code matches expected value."""
    if not hasattr(bdd_context, 'command_result') or not bdd_context.command_result:
        pytest.fail("No command result available")
    
    actual_code = bdd_context.command_result['exit_code']
    if actual_code != expected_code:
        combined_output = bdd_context.command_result['stdout'] + bdd_context.command_result['stderr']
        pytest.fail(
            f"Expected exit code {expected_code}, but got {actual_code}.\n"
            f"Command: {bdd_context.command_result['command']}\n"
            f"Output: {combined_output}"
        )


@then(parsers.parse('the output should contain "{expected_text}"'))
def step_check_output_contains(bdd_context, expected_text: str):
    """Check that the output contains the expected text."""
    if not hasattr(bdd_context, 'command_result') or not bdd_context.command_result:
        pytest.fail("No command result available")
    
    combined_output = bdd_context.command_result['stdout'] + bdd_context.command_result['stderr']
    if expected_text not in combined_output:
        pytest.fail(
            f"Expected output to contain '{expected_text}', but it didn't.\n"
            f"Actual output: {combined_output}"
        )


@then(parsers.parse('the output should not contain "{unexpected_text}"'))
def step_check_output_not_contains(bdd_context, unexpected_text: str):
    """Check that the output does not contain the unexpected text."""
    if not hasattr(bdd_context, 'command_result') or not bdd_context.command_result:
        pytest.fail("No command result available")
    
    combined_output = bdd_context.command_result['stdout'] + bdd_context.command_result['stderr']
    if unexpected_text in combined_output:
        pytest.fail(
            f"Expected output to NOT contain '{unexpected_text}', but it did.\n"
            f"Actual output: {combined_output}"
        )


@then(parsers.parse('the output should match the pattern "{pattern}"'))
def step_check_output_matches_pattern(bdd_context, pattern: str):
    """Check that the output matches the given regex pattern."""
    if not hasattr(bdd_context, 'command_result') or not bdd_context.command_result:
        pytest.fail("No command result available")
    
    combined_output = bdd_context.command_result['stdout'] + bdd_context.command_result['stderr']
    if not re.search(pattern, combined_output, re.MULTILINE):
        pytest.fail(
            f"Expected output to match pattern '{pattern}', but it didn't.\n"
            f"Actual output: {combined_output}"
        )


@then(parsers.parse('the {linter} command should be executed'))
def step_check_linter_executed(bdd_context, linter: str):
    """Check that the specified linter was executed."""
    if not hasattr(bdd_context, 'command_result') or not bdd_context.command_result:
        pytest.fail("No command result available")
    
    combined_output = bdd_context.command_result['stdout'] + bdd_context.command_result['stderr']
    if f"Running: {linter}" not in combined_output:
        pytest.fail(
            f"Expected {linter} to be executed, but it wasn't found in output.\n"
            f"Actual output: {combined_output}"
        )


@then(parsers.parse('the {linter} command should not be executed'))
def step_check_linter_not_executed(bdd_context, linter: str):
    """Check that the specified linter was NOT executed."""
    if not hasattr(bdd_context, 'command_result') or not bdd_context.command_result:
        pytest.fail("No command result available")
    
    combined_output = bdd_context.command_result['stdout'] + bdd_context.command_result['stderr']
    if f"Running: {linter}" in combined_output:
        pytest.fail(
            f"Expected {linter} to NOT be executed, but it was found in output.\n"
            f"Actual output: {combined_output}"
        )


@then('those files get linted')
def step_check_files_linted(bdd_context):
    """Check that files were processed by linters."""
    if not hasattr(bdd_context, 'command_result') or not bdd_context.command_result:
        pytest.fail("No command result available")
    
    combined_output = bdd_context.command_result['stdout'] + bdd_context.command_result['stderr']
    
    # Should see "Running:" in output indicating linters were executed
    if "Running:" not in combined_output:
        pytest.fail(
            f"Expected files to be linted, but no linter execution found.\n"
            f"Actual output: {combined_output}"
        )


@then('a warning should be shown for unsupported files')
def step_check_unsupported_warning(bdd_context):
    """Check that warnings are shown for unsupported files."""
    if not hasattr(bdd_context, 'command_result') or not bdd_context.command_result:
        pytest.fail("No command result available")
    
    combined_output = bdd_context.command_result['stdout'] + bdd_context.command_result['stderr']
    
    if "Warning: No linter configured" not in combined_output:
        pytest.fail(
            f"Expected warning for unsupported files, but none found.\n"
            f"Actual output: {combined_output}"
        )