Feature: Formatting Python files

  Scenario: Ruff is installed
    When ruff is installed
    And lintair is called with Python filenames
    Then those files get formatted
