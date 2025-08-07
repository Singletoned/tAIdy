# Taidy Justfile

# Default recipe
default: test

# Create distribution packages
dist:
    python3 -m build

# Run unit tests
test-unit:
    python3 -m unittest discover tests/unit -v

# Run integration tests
test-integration:
    python3 -m unittest discover tests/integration -v

# Run all Python tests (unit + integration)
test-python: test-unit test-integration

# Run BDD tests
test *features:
    cd tests && go run . {{ features }}

# Run all tests (unit + integration + BDD)
test-all: test-python test

# Run only working Python tests (skips problematic unit test files)
test-working:
    python3 -m unittest tests.integration tests.unit.test_linter_execution -v

# Run type checking with mypy
typecheck:
    mypy taidy/

# Run all checks (type checking and tests)
check: typecheck test

# Clean build artifacts
clean:
    rm -rf dist/ build/ *.egg-info/
    rm -rf __pycache__ *.pyc
    rm -rf taidy/__pycache__ taidy/*.pyc

format *files:
    taidy {{ if files == "" { "." } else { files } }}
