Feature: Linting and formatting shell files

  Scenario: shellcheck is installed
    Given the shell file "poorly_formatted.sh" exists
    When shellcheck is installed
    And `taidy poorly_formatted.sh` is run
    Then those files get linted
    And those files get formatted

  Scenario: shellcheck is not installed, beautysh is
    Given the shell file "poorly_formatted.sh" exists
    When shellcheck isn't installed
    But beautysh is installed
    And `taidy poorly_formatted.sh` is run
    Then those files get linted
    And those files get formatted

  Scenario: shellcheck lint only
    Given the shell file "poorly_formatted.sh" exists
    When shellcheck is installed
    And `taidy lint poorly_formatted.sh` is run
    Then lint output is emitted
    And no formatting happens

  Scenario: shfmt format only
    Given the shell file "poorly_formatted.sh" exists
    When shfmt is installed
    And `taidy format poorly_formatted.sh` is run
    Then those files get formatted
    But no lint output is emitted

  Scenario: bash file with shellcheck
    Given the shell file "poorly_formatted.bash" exists
    When shellcheck is installed
    And `taidy poorly_formatted.bash` is run
    Then those files get linted
    And those files get formatted

  Scenario: zsh file with shellcheck
    Given the shell file "poorly_formatted.zsh" exists
    When shellcheck is installed
    And `taidy poorly_formatted.zsh` is run
    Then those files get linted
    And those files get formatted