Feature: Linting Python files

  Scenario: Ruff is installed
    Given the Python file "poorly_formatted.py" exists
    When ruff is installed
    And `taidy lint poorly_formatted.py` is run
    Then lint output is emitted
    And no formatting happens

  Scenario: Ruff is not installed, uv is
    Given the Python file "poorly_formatted.py" exists
    When ruff isn't installed
    But uv is installed
    And `taidy lint poorly_formatted.py` is run
    Then lint output is emitted
    And no formatting happens

  Scenario: Ruff and uv are not installed, black is
    Given the Python file "poorly_formatted.py" exists
    When ruff isn't installed
    And uv isn't installed
    But black is installed
    And `taidy lint poorly_formatted.py` is run
    Then lint output is emitted
    And no formatting happens
