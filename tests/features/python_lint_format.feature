Feature: Linting and formatting Python files

  Scenario: Ruff is installed
    Given the Python file "poorly_formatted.py" exists
    When ruff is installed
    And `taidy poorly_formatted.py` is run
    Then those files get formatted
    And lint output is emitted

  Scenario: Ruff is not installed, uv is
    Given the Python file "poorly_formatted.py" exists
    When ruff isn't installed
    But uv is installed
    And `taidy poorly_formatted.py` is run
    Then those files get formatted
    And lint output is emitted

  Scenario: Ruff and uv are not installed, black is
    Given the Python file "poorly_formatted.py" exists
    When ruff isn't installed
    And uv isn't installed
    But black is installed
    And `taidy poorly_formatted.py` is run
    Then those files get formatted
    But no lint output is emitted
