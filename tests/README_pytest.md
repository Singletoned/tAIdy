# LintAir BDD Testing Framework with Pytest-BDD

A comprehensive BDD testing framework for CLI applications using Python, pytest-bdd, and Docker. This framework enables testing of your CLI app across different software installation scenarios by spinning up isolated Docker containers.

## Features

- **BDD Testing with Gherkin**: Write tests in natural language using pytest-bdd
- **Docker Integration**: Each test scenario runs in a fresh, isolated container
- **Multiple Environments**: Test against different software environments (Node.js, Python, Go, etc.)
- **Container Lifecycle Management**: Automatic container creation, execution, and cleanup
- **CLI Testing**: Execute CLI commands inside containers with full output capture
- **Rich Reporting**: HTML reports, parallel execution, and pytest ecosystem integration

## Project Structure

```
tests/
├── features/                    # Gherkin feature files
│   ├── python_linting.feature  # Python-specific tests
│   ├── javascript_linting.feature
│   ├── go_linting.feature
│   ├── unsupported_environments.feature
│   └── cli_usage.feature
├── step_defs/                   # pytest-bdd step definitions
│   ├── __init__.py
│   └── common_steps.py          # Shared step implementations
├── docker/                     # Dockerfiles for test environments
│   ├── js/
│   │   └── node18.Dockerfile
│   ├── python/
│   │   └── python311.Dockerfile
│   ├── go/
│   │   └── go121.Dockerfile
│   └── minimal.Dockerfile
├── test_files/                 # Sample files for testing
├── reports/                    # Test reports (generated)
├── test_*.py                   # pytest-bdd test modules
├── conftest.py                 # Pytest fixtures and configuration
├── pytest.ini                 # Pytest configuration
├── config.yaml                # Test environment configuration
├── docker_manager.py          # Docker container management
├── requirements.txt           # Python dependencies
├── run_pytest.py             # Test runner script
└── README_pytest.md          # This file
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
   # For container testing, also build Linux version
   GOOS=linux GOARCH=amd64 go build -o lintair-linux
   ```

## Running Tests

### Using the Test Runner Script

```bash
# Run all tests
python run_pytest.py

# Run specific test suite
python run_pytest.py --test python
python run_pytest.py --test javascript

# Run tests for specific environment
python run_pytest.py --environment python311

# Generate HTML report
python run_pytest.py --html

# Run tests in parallel
python run_pytest.py --parallel

# Verbose output
python run_pytest.py --verbose

# Stop on first failure
python run_pytest.py -x

# Run only failed tests from last run
python run_pytest.py --lf

# List available environments
python run_pytest.py --list-environments
```

### Using Pytest Directly

```bash
# Run all tests
pytest

# Run specific test file
pytest test_python_linting.py

# Run tests with specific markers
pytest -m env_python311
pytest -m "not slow"

# Generate HTML report
pytest --html=reports/report.html --self-contained-html

# Run in parallel
pytest -n auto

# Verbose output
pytest -v -s

# Show local variables on failure
pytest -l

# Run specific test by name
pytest -k "test_python_linting"
```

## Configuration

The framework is configured via:

- **pytest.ini**: Pytest configuration (markers, log settings, etc.)
- **config.yaml**: Docker environments and CLI settings
- **conftest.py**: Pytest fixtures and container management

### Pytest Markers

The framework defines these markers:

- `@pytest.mark.env_python311`: Tests requiring Python 3.11 environment
- `@pytest.mark.env_node18`: Tests requiring Node.js 18 environment  
- `@pytest.mark.env_go121`: Tests requiring Go 1.21 environment
- `@pytest.mark.env_minimal`: Tests requiring minimal environment
- `@pytest.mark.slow`: Tests that run slowly
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.unit`: Unit tests

## Test Environments

### Available Environments

- **python311**: Ubuntu 22.04 with Python 3.11, pip and ruff
- **node18**: Ubuntu 22.04 with Node.js 18, npm and prettier
- **go121**: Ubuntu 22.04 with Go 1.21 and gofmt
- **minimal**: Minimal Ubuntu 22.04 without dev tools

### Adding New Environments

1. Create a new Dockerfile in `tests/docker/`
2. Add the environment to `config.yaml`
3. Create a new fixture in `conftest.py`
4. Add a pytest marker in `pytest.ini`

## Writing Tests

### BDD Test Structure

```python
# test_my_feature.py
import pytest
from pytest_bdd import scenarios, given, when, then
from step_defs.common_steps import *

# Load scenarios from feature file
scenarios('features/my_feature.feature')

@pytest.fixture
def setup_container(bdd_context, python311_container):
    """Set up container for BDD context."""
    bdd_context.current_container = python311_container
    return python311_container
```

### Feature Files

Feature files use standard Gherkin syntax:

```gherkin
Feature: Python file linting with ruff
  As a developer
  I want lintair to automatically lint Python files with ruff
  So that my Python code follows consistent style guidelines

  Scenario: Single Python file gets linted with ruff
    Given ruff is installed
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

The framework provides comprehensive step definitions:

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

## Container Management

The framework uses pytest fixtures to manage Docker containers:

- **Session-scoped**: `docker_manager` - One per test session
- **Function-scoped**: `python311_container`, `node18_container`, etc. - One per test
- **Context management**: Automatic cleanup after each test

## Pytest Integration Benefits

### Rich Reporting
- HTML reports with screenshots and logs
- JUnit XML for CI/CD integration
- Coverage reports
- Custom markers for test categorization

### Parallel Execution
```bash
# Run tests in parallel
pytest -n auto
pytest -n 4  # Use 4 workers
```

### Test Discovery and Selection
```bash
# Run by pattern
pytest -k "python and not slow"

# Run by marker
pytest -m "env_python311 and not integration"

# Run failed tests
pytest --lf

# Run new tests since last commit
pytest --lf --ff
```

### Fixtures and Dependency Injection
- Container fixtures automatically manage lifecycle
- Shared context between steps via `bdd_context` fixture
- Session-level setup and teardown

### IDE Integration
- Full pytest support in IDEs
- Test discovery and running
- Debugging support
- Code completion for fixtures

## Debugging

### Container Logs
When tests fail, container logs are automatically captured and displayed.

### Debug Mode
```bash
# Run with debugging
pytest --pdb  # Drop into debugger on failure
pytest --pdbcls=IPython.terminal.debugger:Pdb  # Use IPython debugger
```

### Verbose Logging
```bash
# Enable debug logging
pytest -v -s --log-cli-level=DEBUG
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
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd tests
          pip install -r requirements.txt
      - name: Build CLI binary
        run: GOOS=linux GOARCH=amd64 go build -o lintair-linux
      - name: Run tests
        run: |
          cd tests
          pytest --html=reports/report.html --junitxml=reports/junit.xml
      - name: Upload test reports
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-reports
          path: tests/reports/
```

## Migration from Behave

The framework was migrated from behave to pytest-bdd for better ecosystem integration:

### Key Changes
- `behave` → `pytest-bdd`
- `environment.py` → `conftest.py` fixtures
- Step definitions use `@given/@when/@then` decorators
- Better IDE support and debugging
- Rich reporting and parallel execution
- Plugin ecosystem integration

### Benefits
- **Better IDE Support**: Full pytest integration
- **Rich Ecosystem**: Hundreds of pytest plugins
- **Parallel Execution**: Built-in with pytest-xdist
- **Advanced Reporting**: HTML, coverage, custom reports
- **Debugging**: Full debugger integration
- **CI/CD Integration**: Better Jenkins, GitHub Actions support

## Best Practices

1. **Container Isolation**: Each test runs in a fresh container
2. **Fixture Usage**: Use environment-specific fixtures (`python311_container`, etc.)
3. **Step Reuse**: Import and reuse step definitions from `common_steps.py`
4. **Error Handling**: Tests automatically capture container logs on failure
5. **Markers**: Use pytest markers for test categorization and selection
6. **Parallel Testing**: Use `-n auto` for faster test execution

## Troubleshooting

### Common Issues

1. **Docker Not Running**: Ensure Docker daemon is started
2. **Binary Not Found**: Make sure CLI binary is built (especially Linux version)
3. **Container Build Failures**: Check Dockerfile syntax and base image availability
4. **Import Errors**: Ensure all dependencies are installed (`pip install -r requirements.txt`)

### Getting Help

```bash
# List all available pytest options
pytest --help

# List all available markers
pytest --markers

# Show fixtures
pytest --fixtures

# Run with maximum verbosity
pytest -vvv -s --tb=long
```

## Example Usage

Here's a complete example of adding a new test:

1. **Create feature file** (`features/rust_linting.feature`):
   ```gherkin
   Feature: Rust file linting with rustfmt
     Scenario: Rust file gets formatted
       Given the following Rust file exists:
         '''
         fn main(){println!("Hello");}
         '''
       When lintair is called with Rust filenames
       Then the rustfmt command should be executed
   ```

2. **Create test module** (`test_rust_linting.py`):
   ```python
   import pytest
   from pytest_bdd import scenarios
   from step_defs.common_steps import *

   scenarios('features/rust_linting.feature')

   @pytest.fixture
   def setup_rust_container(bdd_context, rust_container):
       bdd_context.current_container = rust_container
       return rust_container
   ```

3. **Add container fixture** (in `conftest.py`):
   ```python
   @pytest.fixture
   def rust_container(docker_manager, container_context):
       context = container_context("rust")
       context.start_container(docker_manager)
       yield context
   ```

4. **Run the tests**:
   ```bash
   pytest test_rust_linting.py
   ```

The framework handles all Docker management, file creation, command execution, and result validation automatically!