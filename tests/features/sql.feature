Feature: Linting and formatting SQL files

  Scenario: sqlfluff is installed
    Given the SQL file "poorly_formatted.sql" exists
    When sqlfluff is installed
    And `taidy poorly_formatted.sql` is run
    Then those files get linted
    And those files get formatted

  Scenario: sqlfluff is not installed, uv is
    Given the SQL file "poorly_formatted.sql" exists
    When sqlfluff isn't installed
    But uv is installed
    And `taidy poorly_formatted.sql` is run
    Then those files get linted
    And those files get formatted

  Scenario: sqlfluff lint only
    Given the SQL file "poorly_formatted.sql" exists
    When sqlfluff is installed
    And `taidy lint poorly_formatted.sql` is run
    Then lint output is emitted
    And no formatting happens

  Scenario: sqlfluff format only
    Given the SQL file "poorly_formatted.sql" exists
    When sqlfluff is installed
    And `taidy format poorly_formatted.sql` is run
    Then those files get formatted
    But no lint output is emitted