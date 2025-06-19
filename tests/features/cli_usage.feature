Feature: CLI usage and error handling

  Scenario: Running lintair without arguments shows usage
    When lintair is called with no arguments
    Then the exit code should be 1
    And the output should contain "Usage:"
    And the output should contain "lintair"

  Scenario: Non-existent files are handled gracefully
    When lintair is called with files that don't exist
    Then the exit code should be 0
    And the output should contain "no files were linted"
