# LintAir BDD Testing Framework

A comprehensive BDD testing framework for CLI applications using Python, behave, and Docker. This framework enables testing of your CLI app across different software installation scenarios by spinning up isolated Docker containers.

## Features

- **BDD Testing with Gherkin**: Write tests in natural language using behave
- **Docker Integration**: Each test scenario runs in a fresh, isolated container
- **Multiple Environments**: Test against different software environments (Node.js, Python, Go, etc.)
- **Container Lifecycle Management**: Automatic container creation, execution, and cleanup
- **CLI Testing**: Execute CLI commands inside containers with full output capture
- **Comprehensive Reporting**: Detailed test results with container logs on failures

## Project Structure

```
tests/
├── features/                    # Gherkin feature files
│   ├── steps/                  # Step definitions
│   │   └── cli_steps.py
│   ├── environment.py          # Behave hooks and setup
│   ├── python_linting.feature  # Python-specific tests
│   ├── javascript_linting.feature
│   ├── go_linting.feature
│   ├── unsupported_environments.feature
│   └── cli_usage.feature
├── docker/                     # Dockerfiles for test environments
│   ├── js/
│   │   └── node18.Dockerfile
│   ├── python/
│   │   └── python311.Dockerfile
│   ├── go/
│   │   └── go121.Dockerfile
│   └── minimal.Dockerfile
├── test_files/                 # Sample files for testing
│   ├── sample.py
│   ├── sample.js
│   ├── sample.go
│   ├── sample.json
│   └── sample.css
├── config.yaml                 # Test configuration
├── docker_manager.py          # Docker container management
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Installation

1. **Install Dependencies**:
   ```bash
   cd tests
   pip install -r requirements.txt
   ```

2. **Install Docker**: Make sure Docker is installed and running on your system.

3. **Build CLI Binary**: Ensure your CLI binary is built:
   ```bash
   go build -o lintair
   ```

## Configuration

The framework is configured via `config.yaml`. Key settings include:

- **Docker Settings**: Container cleanup policy, timeouts, network mode
- **CLI Settings**: Binary path, default timeout
- **Test Environments**: Available Docker environments with their Dockerfiles
- **Logging**: Log levels and container log capture

## Test Environments

### Available Environments

- **node18**: Node.js 18 with npm and prettier
- **python311**: Python 3.11 with pip and ruff  
- **go121**: Go 1.21 with gofmt
- **minimal**: Minimal Alpine Linux without dev tools

### Adding New Environments

1. Create a new Dockerfile in `tests/docker/`
2. Add the environment to `config.yaml`:
   ```yaml
   environments:
     myenv:
       dockerfile: "tests/docker/myenv.Dockerfile"
       tag: "lintair-test:myenv"
       description: "My custom environment"
   ```

## Running Tests

### Run All Tests
```bash
cd tests
behave
```

### Run Specific Feature
```bash
behave features/python_linting.feature
```

### Run Tests with Specific Tags
```bash
behave --tags=env:python311
```

### Verbose Output
```bash
behave --verbose --capture=no
```

## Writing Tests

### Feature Files

Feature files use Gherkin syntax and should specify the environment using tags:

```gherkin
@env:python311
Feature: Python file linting with ruff
  As a developer
  I want lintair to automatically lint Python files with ruff
  So that my Python code follows consistent style guidelines

  Scenario: Single Python file gets linted with ruff
    Given the following Python file exists:
      '''
      def hello():
          print("Hello, World!")
      '''
    When lintair is called with Python filenames
    Then the exit code should be 0
    And the ruff command should be executed
```

### Available Step Definitions

#### File Management
- `Given the following {file_type} file exists:`
- `Given the following files exist:`

#### Environment Checks
- `Given {linter} is installed`
- `Given {linter} is not installed`

#### CLI Execution
- `When lintair is called with {file_pattern} filenames`
- `When lintair is called with the files`
- `When lintair is called with no arguments`

#### Assertions
- `Then the exit code should be {expected_code:d}`
- `Then the output should contain "{expected_text}"`
- `Then the output should not contain "{unexpected_text}"`
- `Then the output should match the pattern "{pattern}"`
- `Then the {linter} command should be executed`
- `Then the {linter} command should not be executed`
- `Then those files get linted`
- `Then a warning should be shown for unsupported files`

## Docker Container Management

The `DockerManager` class handles all container operations:

- **Image Building**: Builds Docker images from Dockerfiles
- **Container Lifecycle**: Starts, monitors, and stops containers
- **Command Execution**: Runs CLI commands inside containers
- **Volume Mounting**: Mounts CLI binary and test files
- **Log Capture**: Captures container logs for debugging

## Debugging

### Container Logs
When tests fail, container logs are automatically captured and displayed.

### Manual Container Inspection
To manually inspect a container, modify the cleanup policy in `config.yaml`:
```yaml
docker:
  cleanup_policy: "never"  # Keep containers after tests
```

### Debug Logging
Enable debug logging in `config.yaml`:
```yaml
logging:
  level: "DEBUG"
```

## Parallel Testing

Enable parallel test execution in `config.yaml`:
```yaml
parallel:
  enabled: true
  max_workers: 3
```

## Best Practices

1. **Environment Isolation**: Each scenario should run in a fresh container
2. **Tag Usage**: Use `@env:` tags to specify test environments
3. **File Cleanup**: Test files are automatically cleaned up between scenarios
4. **Error Handling**: Always check exit codes and output in assertions
5. **Container Resources**: Keep Dockerfiles minimal for faster builds

## Troubleshooting

### Common Issues

1. **Docker Not Running**: Ensure Docker daemon is started
2. **Binary Not Found**: Make sure CLI binary is built and accessible
3. **Container Build Failures**: Check Dockerfile syntax and base image availability
4. **Port Conflicts**: Ensure no other containers are using the same ports

### Log Files

- Test execution logs: `tests.log`
- Container logs: Captured automatically on test failures

## Contributing

When adding new test scenarios:

1. Create appropriate feature files with clear descriptions
2. Use existing step definitions when possible
3. Add new step definitions to `cli_steps.py` for reusability
4. Document any new Docker environments
5. Update this README with new features or changes

## Example Usage

Here's a complete example of testing a new linter:

1. **Add Dockerfile** (`tests/docker/rust/rust.Dockerfile`):
   ```dockerfile
   FROM rust:1.70-alpine
   RUN apk add --no-cache bash curl
   RUN cargo install rustfmt
   CMD ["tail", "-f", "/dev/null"]
   ```

2. **Update config.yaml**:
   ```yaml
   environments:
     rust170:
       dockerfile: "tests/docker/rust/rust.Dockerfile"
       tag: "lintair-test:rust170"
       description: "Rust 1.70 with rustfmt"
   ```

3. **Create feature file** (`features/rust_linting.feature`):
   ```gherkin
   @env:rust170
   Feature: Rust file linting with rustfmt
     Scenario: Rust file gets formatted
       Given the following Rust file exists:
         '''
         fn main(){println!("Hello");}
         '''
       When lintair is called with Rust filenames
       Then the rustfmt command should be executed
   ```

The framework will automatically build the Docker image, start a container, execute your CLI, and verify the results!