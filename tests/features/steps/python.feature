Feature: Formatting Python files

  Scenario: Ruff is installed
    When lintair is called with Python filenames
    And ruff is installed
    And ruff isn't installed
    Then those files get formatted
