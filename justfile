# Taidy Justfile

# Default recipe
default: test

# Create distribution packages
dist:
    python3 -m build

# Run BDD tests
test *features:
    cd tests && go run . {{ features }}

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
