# Taidy Justfile

# Default recipe — fast tests only
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

# Run Docker-based integration tests (requires Docker)
test-docker:
    python3 -m unittest discover tests/docker_tests -v

# Fast tests (unit + integration, no Docker)
test: test-unit test-integration

# All tests including Docker
test-all: test test-docker

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
