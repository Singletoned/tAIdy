Feature: Formatting Python files

  Scenario: Ruff is installed
    Given the Python file "poorly_formatted.py" exists
    When ruff is installed
    And taidy is called with Python filenames
    Then those files get formatted

  Scenario: Ruff is not installed, uv is
    Given the Python file "poorly_formatted.py" exists
    When ruff isn't installed
    But uv is installed
    And taidy is called with Python filenames
    Then those files get formatted

  Scenario: Ruff and uv are not installed, black is
    Given the Python file "poorly_formatted.py" exists
    When ruff isn't installed
    And uv isn't installed
    But black is installed
    And taidy is called with Python filenames
    Then those files get formatted
