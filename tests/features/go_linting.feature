@env:go121
Feature: Go file linting with gofmt
  As a developer
  I want lintair to automatically format Go files with gofmt
  So that my Go code follows standard formatting

  Background:
    Given gofmt is installed

  Scenario: Single Go file gets formatted with gofmt
    Given the following Go file exists:
      """
      package main
      
      import "fmt"
      
      func main() {
          fmt.Println("Hello, World!")
      }
      """
    When lintair is called with Go filenames
    Then the gofmt command should be executed
    And the output should contain "Running: gofmt -l"

  Scenario: Multiple Go files get formatted together
    Given the following files exist:
      | filename    | content                                              |
      | main.go     | package main\n\nfunc main() { println("hello") }    |
      | utils.go    | package main\n\nfunc add(a, b int) int { return a+b }|
      | README.md   | # Go Project                                         |
    When lintair is called with Go filenames
    Then the gofmt command should be executed
    And the output should contain "main.go utils.go"
    And the output should not contain "README.md"

  Scenario: Go file with formatting issues
    Given the following Go file exists:
      """
      package main
      import"fmt"
      func main(){fmt.Println("badly formatted")}
      """
    When lintair is called with Go filenames
    Then the gofmt command should be executed
    And the output should contain "Running: gofmt -l"

  Scenario: Mixed file types - only Go files processed by gofmt
    Given the following files exist:
      | filename     | content                          |
      | server.go    | package main\n\nfunc main() {}  |
      | config.json  | {"port": 8080}                   |
      | script.py    | print("Hello from Python")      |
    When lintair is called with the files
    Then the gofmt command should be executed
    And the output should contain "server.go"
    And the output should not contain "config.json"
    And the output should not contain "script.py"