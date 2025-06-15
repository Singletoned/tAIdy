@env_python311
Feature: Python file linting with ruff
  As a developer
  I want lintair to automatically lint Python files with ruff
  So that my Python code follows consistent style guidelines

  Background:
    Given ruff is installed

  Scenario: Single Python file gets linted with ruff
    Given the following Python file exists:
      """
      def hello():
          print("Hello, World!")
      
      hello()
      """
    When lintair is called with Python filenames
    Then the exit code should be 0
    And the ruff command should be executed
    And the output should contain "Running: ruff check"

  Scenario: Multiple Python files get linted together
    Given the following files exist:
      | filename    | content                                    |
      | test1.py    | def func1():\n    return "hello"          |
      | test2.py    | def func2():\n    return "world"          |
      | README.md   | # This is a markdown file                  |
    When lintair is called with Python filenames
    Then the exit code should be 0
    And the ruff command should be executed
    And the output should contain "test1.py test2.py"
    And the output should not contain "README.md"

  Scenario: Python file with linting errors
    Given the following Python file exists:
      """
      import os
      import sys
      
      def unused_function():
          pass
      
      print( "badly formatted" )
      """
    When lintair is called with Python filenames
    Then the ruff command should be executed
    And the output should contain "Running: ruff check"

  Scenario: Mixed file types - only Python files processed by ruff
    Given the following files exist:
      | filename     | content                          |
      | script.py    | print("Hello from Python")      |
      | styles.css   | body { margin: 0; }              |
      | config.json  | {"key": "value"}                 |
    When lintair is called with the files
    Then the ruff command should be executed
    And the output should contain "script.py"
    And the output should not contain "styles.css"
    And the output should not contain "config.json"