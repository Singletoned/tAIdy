@env_node18
Feature: CLI usage and error handling
  As a developer
  I want lintair to provide helpful usage information
  So that I understand how to use the tool correctly

  Scenario: Running lintair without arguments shows usage
    When lintair is called with no arguments
    Then the exit code should be 1
    And the output should contain "Usage:"
    And the output should contain "lintair"

  Scenario: Empty file list handling
    Given the following files exist:
      | filename | content |
    When lintair is called with the files
    Then the exit code should be 1
    And the output should contain "Usage:"

  Scenario: Non-existent files are handled gracefully
    When lintair is called with Python filenames
    Then the prettier command should be executed
    And the output should contain "Running: prettier --check"