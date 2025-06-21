Feature: CLI usage and error handling

  Scenario: Running taidy without arguments shows usage
    When taidy is called with no arguments
    Then the exit code should be 1
    And the output should contain "Usage:"
    And the output should contain "taidy"

  Scenario: Non-existent files are handled gracefully
    When taidy is called with files that don't exist
    Then the exit code should be 0
    And the output should contain "no files were linted"
