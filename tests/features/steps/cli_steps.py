"""
Step definitions for CLI testing scenarios.
"""
import os
import re
from behave import given, when, then
from pathlib import Path


@given('the following {file_type} file exists')
def step_create_file(context, file_type):
    """Create a test file with the given content."""
    if not hasattr(context, 'test_files'):
        context.test_files = []
        
    # Get file content from docstring
    content = context.text if context.text else ""
    
    # Generate filename based on file type
    extensions = {
        'Python': '.py',
        'JavaScript': '.js', 
        'TypeScript': '.ts',
        'Go': '.go',
        'JSON': '.json',
        'CSS': '.css'
    }
    
    ext = extensions.get(file_type, '.txt')
    filename = f"test_{len(context.test_files) + 1}{ext}"
    
    # Write file content to container
    if context.current_container:
        # Write file directly in container using printf to avoid HEREDOC issues
        # Escape single quotes in content
        escaped_content = content.replace("'", "'\"'\"'")
        write_cmd = f"printf '%s' '{escaped_content}' > {filename}"
        result = context.docker_manager.execute_command(
            context.current_container.name,
            write_cmd
        )
        if result['exit_code'] != 0:
            raise Exception(f"Failed to create file {filename}: {result['stderr']}")
    else:
        # Write to local test_files directory
        test_file_path = Path("tests/test_files") / filename
        test_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(test_file_path, 'w') as f:
            f.write(content)
    
    context.test_files.append(filename)


@given('the following files exist')
def step_create_multiple_files(context):
    """Create multiple test files from table."""
    if not hasattr(context, 'test_files'):
        context.test_files = []
        
    for row in context.table:
        filename = row['filename']
        content = row.get('content', '')
        
        # Write file content to container
        if context.current_container:
            # Escape single quotes in content
            escaped_content = content.replace("'", "'\"'\"'")
            write_cmd = f"printf '%s' '{escaped_content}' > {filename}"
            result = context.docker_manager.execute_command(
                context.current_container.name,
                write_cmd
            )
            if result['exit_code'] != 0:
                raise Exception(f"Failed to create file {filename}: {result['stderr']}")
        else:
            # Write to local test_files directory
            test_file_path = Path("tests/test_files") / filename
            test_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(test_file_path, 'w') as f:
                f.write(content)
        
        context.test_files.append(filename)


@given('{linter} is installed')
def step_verify_linter_installed(context, linter):
    """Verify that a linter is installed in the container."""
    if not context.current_container:
        raise Exception("No container available for testing")
        
    # Check if linter is available
    check_cmd = f"which {linter}"
    result = context.docker_manager.execute_command(
        context.current_container.name,
        check_cmd
    )
    
    if result['exit_code'] != 0:
        raise Exception(f"Linter {linter} is not installed in the container")


@given('{linter} is not installed')
def step_verify_linter_not_installed(context, linter):
    """Verify that a linter is NOT installed in the container."""
    if not context.current_container:
        raise Exception("No container available for testing")
        
    # Check if linter is NOT available
    check_cmd = f"which {linter}"
    result = context.docker_manager.execute_command(
        context.current_container.name,
        check_cmd
    )
    
    if result['exit_code'] == 0:
        raise Exception(f"Linter {linter} should not be installed in the container")


@when('lintair is called with {file_pattern} filenames')
def step_run_lintair_with_files(context, file_pattern):
    """Run lintair with files matching the pattern."""
    if not context.current_container:
        raise Exception("No container available for testing")
        
    # Filter test files based on pattern
    pattern_map = {
        'Python': r'\.py$',
        'JavaScript': r'\.js$',
        'TypeScript': r'\.ts$',
        'Go': r'\.go$',
        'JSON': r'\.json$',
        'CSS': r'\.css$'
    }
    
    if file_pattern in pattern_map:
        regex_pattern = pattern_map[file_pattern]
        matching_files = [f for f in context.test_files if re.search(regex_pattern, f)]
    else:
        # Assume it's a literal pattern
        matching_files = [f for f in context.test_files if file_pattern in f]
    
    if not matching_files:
        raise Exception(f"No files found matching pattern: {file_pattern}")
    
    # Run lintair with matching files
    files_str = ' '.join(matching_files)
    cmd = f"/app/lintair {files_str}"
    
    result = context.docker_manager.execute_command(
        context.current_container.name,
        cmd
    )
    
    context.command_result = result


@when('lintair is called with the files')
def step_run_lintair_with_test_files(context):
    """Run lintair with all test files."""
    if not context.current_container:
        raise Exception("No container available for testing")
        
    if not hasattr(context, 'test_files') or not context.test_files:
        raise Exception("No test files available")
    
    # Run lintair with all test files
    files_str = ' '.join(context.test_files)
    cmd = f"/app/lintair {files_str}"
    
    result = context.docker_manager.execute_command(
        context.current_container.name,
        cmd
    )
    
    context.command_result = result


@when('lintair is called with no arguments')
def step_run_lintair_no_args(context):
    """Run lintair with no arguments."""
    if not context.current_container:
        raise Exception("No container available for testing")
    
    cmd = "/app/lintair"
    result = context.docker_manager.execute_command(
        context.current_container.name,
        cmd
    )
    
    context.command_result = result


@then('the exit code should be {expected_code:d}')
def step_check_exit_code(context, expected_code):
    """Check that the command exit code matches expected value."""
    if not hasattr(context, 'command_result') or not context.command_result:
        raise Exception("No command result available")
    
    actual_code = context.command_result['exit_code']
    if actual_code != expected_code:
        raise AssertionError(
            f"Expected exit code {expected_code}, but got {actual_code}.\n"
            f"STDOUT: {context.command_result['stdout']}\n"
            f"STDERR: {context.command_result['stderr']}"
        )


@then('the output should contain "{expected_text}"')
def step_check_output_contains(context, expected_text):
    """Check that the output contains the expected text."""
    if not hasattr(context, 'command_result') or not context.command_result:
        raise Exception("No command result available")
    
    combined_output = context.command_result['stdout'] + context.command_result['stderr']
    if expected_text not in combined_output:
        raise AssertionError(
            f"Expected output to contain '{expected_text}', but it didn't.\n"
            f"Actual output: {combined_output}"
        )


@then('the output should not contain "{unexpected_text}"')
def step_check_output_not_contains(context, unexpected_text):
    """Check that the output does not contain the unexpected text."""
    if not hasattr(context, 'command_result') or not context.command_result:
        raise Exception("No command result available")
    
    combined_output = context.command_result['stdout'] + context.command_result['stderr']
    if unexpected_text in combined_output:
        raise AssertionError(
            f"Expected output to NOT contain '{unexpected_text}', but it did.\n"
            f"Actual output: {combined_output}"
        )


@then('the output should match the pattern "{pattern}"')
def step_check_output_matches_pattern(context, pattern):
    """Check that the output matches the given regex pattern."""
    if not hasattr(context, 'command_result') or not context.command_result:
        raise Exception("No command result available")
    
    combined_output = context.command_result['stdout'] + context.command_result['stderr']
    if not re.search(pattern, combined_output, re.MULTILINE):
        raise AssertionError(
            f"Expected output to match pattern '{pattern}', but it didn't.\n"
            f"Actual output: {combined_output}"
        )


@then('the {linter} command should be executed')
def step_check_linter_executed(context, linter):
    """Check that the specified linter was executed."""
    if not hasattr(context, 'command_result') or not context.command_result:
        raise Exception("No command result available")
    
    combined_output = context.command_result['stdout'] + context.command_result['stderr']
    if f"Running: {linter}" not in combined_output:
        raise AssertionError(
            f"Expected {linter} to be executed, but it wasn't found in output.\n"
            f"Actual output: {combined_output}"
        )


@then('the {linter} command should not be executed')
def step_check_linter_not_executed(context, linter):
    """Check that the specified linter was NOT executed."""
    if not hasattr(context, 'command_result') or not context.command_result:
        raise Exception("No command result available")
    
    combined_output = context.command_result['stdout'] + context.command_result['stderr']
    if f"Running: {linter}" in combined_output:
        raise AssertionError(
            f"Expected {linter} to NOT be executed, but it was found in output.\n"
            f"Actual output: {combined_output}"
        )


@then('those files get linted')
def step_check_files_linted(context):
    """Check that files were processed by linters."""
    if not hasattr(context, 'command_result') or not context.command_result:
        raise Exception("No command result available")
    
    combined_output = context.command_result['stdout'] + context.command_result['stderr']
    
    # Should see "Running:" in output indicating linters were executed
    if "Running:" not in combined_output:
        raise AssertionError(
            f"Expected files to be linted, but no linter execution found.\n"
            f"Actual output: {combined_output}"
        )


@then('a warning should be shown for unsupported files')
def step_check_unsupported_warning(context):
    """Check that warnings are shown for unsupported files."""
    if not hasattr(context, 'command_result') or not context.command_result:
        raise Exception("No command result available")
    
    combined_output = context.command_result['stdout'] + context.command_result['stderr']
    
    if "Warning: No linter configured" not in combined_output:
        raise AssertionError(
            f"Expected warning for unsupported files, but none found.\n"
            f"Actual output: {combined_output}"
        )