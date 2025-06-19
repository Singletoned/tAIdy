# LintAir BDD Testing Framework with Godog

A comprehensive BDD testing framework for CLI applications using Go, Godog, and Docker. This framework enables testing of your CLI app across different software installation scenarios by spinning up isolated Docker containers.

## Features

- **BDD Testing with Gherkin**: Write tests in natural language using Godog
- **Docker Integration**: Each test scenario runs in a fresh, isolated container
- **Multiple Environments**: Test against different software environments (Node.js, Python, Go, etc.)
- **Container Lifecycle Management**: Automatic container creation, execution, and cleanup
- **CLI Testing**: Execute CLI commands inside containers with full output capture
- **Native Go Integration**: Built with Go for better integration with the main application

## Project Structure

```
tests/
├── features/                    # Gherkin feature files
│   ├── cli_usage.feature       # CLI usage and error handling tests
│   └── python.feature          # Python-specific formatting tests
├── docker/                     # Dockerfiles for test environments
│   ├── js/
│   │   └── node18.Dockerfile
│   ├── python/
│   │   └── python311.Dockerfile
│   ├── go/
│   │   └── go121.Dockerfile
│   └── minimal.Dockerfile
├── test_files/                 # Sample files for testing
├── main.go                     # Godog test runner
├── step_definitions.go         # Step definitions implementation
├── docker_manager.go          # Docker container management
├── go.mod                      # Go module dependencies
├── config.yaml                # Test environment configuration
└── README.md                  # This file
```

## Installation

1. **Install Dependencies**:
   ```bash
   cd tests
   go mod tidy
   ```

2. **Install Docker**: Make sure Docker is installed and running on your system.

3. **Build CLI Binary**: Ensure your CLI binary is built:
   ```bash
   cd ..
   go build -o lintair
   # For container testing, also build Linux version
   GOOS=linux GOARCH=amd64 go build -o lintair-linux
   ```

## Running Tests

### Using Go Run

```bash
# Run all tests
go run .

# Run with verbose output
go run . --godog.format=pretty

# Run specific feature
go run . features/cli_usage.feature

# Show available options
go run . -h
```

### Building and Running

```bash
# Build the test binary
go build -o lintair-tests

# Run all tests
./lintair-tests

# Run with different format
./lintair-tests --godog.format=progress
```

## Configuration

The framework is configured via:

- **config.yaml**: Docker environments and CLI settings
- **go.mod**: Go dependencies

### Test Environments

#### Available Environments

- **python311**: Ubuntu 22.04 with Python 3.11, pip and ruff
- **node18**: Ubuntu 22.04 with Node.js 18, npm and prettier
- **go121**: Ubuntu 22.04 with Go 1.21 and gofmt
- **minimal**: Minimal Ubuntu 22.04 without dev tools

#### Adding New Environments

1. Create a new Dockerfile in `docker/`
2. Add the environment to the `environments` map in `step_definitions.go`
3. Create corresponding step definitions if needed

## Writing Tests

### Feature Files

Feature files use standard Gherkin syntax:

```gherkin
Feature: Python file formatting with ruff
  As a developer
  I want lintair to automatically format Python files with ruff
  So that my Python code follows consistent style guidelines

  Scenario: Single Python file gets formatted with ruff
    Given the following Python file exists:
      """
      def hello():
          print("Hello, World!")
      """
    When ruff is installed
    And lintair is called with Python filenames
    Then those files get formatted
```

### Available Step Definitions

The framework provides comprehensive step definitions:

#### File Management
- `Given the following Python file exists:`
- `Given the following JavaScript file exists:`
- `Given the following Go file exists:`

#### Environment Checks
- `Given {linter} is installed`
- `Given {linter} is not installed`

#### CLI Execution
- `When lintair is called with {file_pattern} filenames`
- `When lintair is called with the files`
- `When lintair is called with no arguments`
- `When lintair is called with files that don't exist`

#### Assertions
- `Then the exit code should be {code}`
- `Then the output should contain "{text}"`
- `Then the output should not contain "{text}"`
- `Then the output should match the pattern "{pattern}"`
- `Then the {linter} command should be executed`
- `Then the {linter} command should not be executed`
- `Then those files get formatted`
- `Then those files get linted`
- `Then a warning should be shown for unsupported files`

## Container Management

The framework automatically manages Docker containers:

- **Automatic Build**: Images are built automatically if they don't exist
- **Isolation**: Each scenario runs in a fresh container
- **Cleanup**: Containers are automatically stopped and removed after tests
- **File Management**: Test files are created inside containers dynamically

## Godog Integration Benefits

### Native Go Support
- Full integration with Go toolchain
- No dependency on Python or virtual environments
- Better performance and resource usage

### Rich Testing Features
- Scenario outlines for data-driven tests
- Background steps for common setup
- Hooks for setup and teardown
- Multiple output formats (pretty, progress, JSON, etc.)

## Adding New Step Definitions

To add new step definitions:

1. **Add to `step_definitions.go`**:
   ```go
   func (tc *TestContext) myNewStep(param string) error {
       // Implementation
       return nil
   }
   ```

2. **Register in `InitializeScenario`**:
   ```go
   ctx.Step(`^my new step with "([^"]*)"$`, tc.myNewStep)
   ```

## Example Usage

Here's a complete example of adding a new test:

1. **Create feature file** (`features/rust_formatting.feature`):
   ```gherkin
   Feature: Rust file formatting with rustfmt
     Scenario: Rust file gets formatted
       Given the following Rust file exists:
         """
         fn main(){println!("Hello");}
         """
       When rustfmt is installed
       And lintair is called with Rust filenames
       Then the rustfmt command should be executed
   ```

2. **Add environment** (in `step_definitions.go`):
   ```go
   "rust": {"docker/rust/rust.Dockerfile", "lintair-test:rust"},
   ```

3. **Add step definition**:
   ```go
   func (tc *TestContext) theFollowingRustFileExists(docString *godog.DocString) error {
       // Implementation similar to other file creation steps
   }
   ```

4. **Register step**:
   ```go
   ctx.Step(`^the following Rust file exists:$`, tc.theFollowingRustFileExists)
   ```

## Debugging

### Container Logs
When tests fail, container logs are automatically captured and displayed.

### Verbose Output
```bash
# Run with pretty format for detailed output
go run . --godog.format=pretty
```

### Manual Container Inspection
If needed, you can manually inspect containers:
```bash
# List running containers
docker ps

# Connect to a container
docker exec -it <container-name> sh
```

## Continuous Integration

### GitHub Actions Example
```yaml
name: BDD Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-go@v4
        with:
          go-version: '1.24'
      - name: Build CLI binary
        run: GOOS=linux GOARCH=amd64 go build -o lintair-linux
      - name: Run tests
        run: |
          cd tests
          go test -v
```

## Migration from Python/pytest-bdd

The framework was migrated from Python/pytest-bdd to Go/Godog for better integration:

### Key Changes
- `pytest-bdd` → `Godog`
- `conftest.py` → `main.go` and `step_definitions.go`
- Python step definitions → Go step definitions
- Better performance and native integration
- Simplified dependency management

### Benefits
- **Native Integration**: No Python dependency, pure Go
- **Better Performance**: Faster startup and execution
- **Simpler Deployment**: Single binary, no virtual environments
- **Type Safety**: Compile-time error checking
- **Tool Integration**: Better IDE support for Go development

## Best Practices

1. **Container Isolation**: Each test runs in a fresh container
2. **Resource Cleanup**: Containers are automatically cleaned up
3. **Error Handling**: Tests capture and display container logs on failure
4. **Feature Organization**: Group related scenarios in feature files
5. **Step Reuse**: Create reusable step definitions for common operations

## Troubleshooting

### Common Issues

1. **Docker Not Running**: Ensure Docker daemon is started
2. **Binary Not Found**: Make sure CLI binary is built (especially Linux version)
3. **Container Build Failures**: Check Dockerfile syntax and base image availability
4. **Module Errors**: Run `go mod tidy` to ensure dependencies are correct

### Getting Help

```bash
# Show command line options
go run . -h

# Run with verbose output
go run . --godog.format=pretty

# Check Go module status
go mod tidy
go mod verify
```

The framework handles all Docker management, file creation, command execution, and result validation automatically while providing a clean, maintainable Go-based testing solution!