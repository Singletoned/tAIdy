@env_node18
Feature: JavaScript file linting with prettier
  As a developer
  I want lintair to automatically format JavaScript files with prettier
  So that my JavaScript code follows consistent formatting

  Background:
    Given prettier is installed

  Scenario: Single JavaScript file gets formatted with prettier
    Given the following JavaScript file exists:
      """
      function hello() {
        console.log("Hello, World!");
      }
      
      hello();
      """
    When lintair is called with JavaScript filenames
    Then the prettier command should be executed
    And the output should contain "Running: prettier --check"

  Scenario: Multiple JavaScript files get formatted together  
    Given the following files exist:
      | filename      | content                                           |
      | app.js        | const greeting = "hello";\nconsole.log(greeting); |
      | utils.js      | export function add(a, b) { return a + b; }      |
      | script.py     | print("This is Python")                          |
    When lintair is called with JavaScript filenames
    Then the prettier command should be executed
    And the output should contain "app.js utils.js"
    And the output should not contain "script.py"

  Scenario: JavaScript file with formatting issues
    Given the following JavaScript file exists:
      """
      const data={name:"test",value:123};
      if(data.name==="test"){console.log("match");}
      """
    When lintair is called with JavaScript filenames
    Then the prettier command should be executed
    And the output should contain "Running: prettier --check"

  Scenario: TypeScript files also use prettier
    Given the following files exist:
      | filename     | content                                    |
      | main.ts      | interface User { name: string; }           |
      | component.tsx| export const App = () => <div>Hello</div>; |
    When lintair is called with the files
    Then the prettier command should be executed
    And the output should contain "main.ts component.tsx"

  Scenario: JSON and CSS files also use prettier
    Given the following files exist:
      | filename     | content                    |
      | config.json  | {"name": "test"}           |
      | styles.css   | body { margin: 0; }        |
      | index.html   | <html><body></body></html> |
    When lintair is called with the files
    Then the prettier command should be executed
    And the output should contain "config.json styles.css index.html"