@env_minimal
Feature: Handling unsupported environments
  As a developer
  I want lintair to handle missing linters gracefully
  So that I get helpful error messages when tools aren't available

  Scenario: Python files in environment without ruff
    Given ruff is not installed
    And the following Python file exists:
      """
      def hello():
          print("Hello, World!")
      """
    When lintair is called with Python filenames
    Then the exit code should be 1
    And the output should contain "Error executing ruff"

  Scenario: JavaScript files in environment without prettier
    Given prettier is not installed  
    And the following JavaScript file exists:
      """
      function hello() {
        console.log("Hello, World!");
      }
      """
    When lintair is called with JavaScript filenames
    Then the exit code should be 1
    And the output should contain "Error executing prettier"

  Scenario: Unsupported file extensions show warnings
    Given the following files exist:
      | filename      | content                 |
      | data.xml      | <root><item/></root>    |
      | config.toml   | [section]\nkey = "val" |
      | script.sh     | #!/bin/bash\necho hi   |
    When lintair is called with the files
    Then the exit code should be 0
    And a warning should be shown for unsupported files
    And the output should contain "Warning: No linter configured for file data.xml"
    And the output should contain "Warning: No linter configured for file config.toml"
    And the output should contain "Warning: No linter configured for file script.sh"

  Scenario: Mixed supported and unsupported files
    Given the following files exist:
      | filename     | content                    |
      | script.py    | print("Hello")             |
      | data.xml     | <root><item/></root>       |
    When lintair is called with the files
    Then a warning should be shown for unsupported files
    And the output should contain "Warning: No linter configured for file data.xml"
    And the output should contain "Error executing ruff"