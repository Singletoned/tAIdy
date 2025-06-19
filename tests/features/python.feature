Feature: Formatting Python files

  Scenario: Ruff is installed and Python files get formatted
    Given the following Python file exists:
      """
      def hello():
          print("Hello, World!")
      """
    When ruff is installed
    And lintair is called with Python filenames
    Then those files get formatted
