Feature: Formatting Python files

  Scenario: Ruff is installed
    Given the Python file "poorly_formatted.py" exists
    When ruff is installed
    And lintair is called with Python filenames
    Then those files get formatted

  Scenario: Ruff is not installed, uv is
    Given the Python file "poorly_formatted.py" exists
    When ruff isn't installed
    But uv is installed
    And lintair is called with Python filenames
    Then those files get formatted
