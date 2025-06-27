Feature: Formatting Markdown files

  Scenario: Prettier is installed for markdown formatting
    Given the markdown file "poorly_formatted.md" exists
    When prettier is installed
    And `taidy format poorly_formatted.md` is run
    Then those files get formatted
    But no lint output is emitted

  Scenario: Prettier is installed for markdown linting
    Given the markdown file "poorly_formatted.md" exists
    When prettier is installed
    And `taidy lint poorly_formatted.md` is run
    Then those files get linted
    But no formatting happens

  Scenario: Prettier is installed for markdown both lint and format
    Given the markdown file "poorly_formatted.md" exists
    When prettier is installed
    And `taidy poorly_formatted.md` is run
    Then those files get linted
    And those files get formatted

  Scenario: Prettier is not installed for markdown
    Given the markdown file "poorly_formatted.md" exists
    When prettier is not installed
    And `taidy poorly_formatted.md` is run
    Then the output should contain "Warning: No available linter found for .md files"
    And the output should contain "Warning: No available formatter found for .md files"