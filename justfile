# Taidy Justfile

# Default recipe
default: test

# Create distribution packages
dist:
    python3 -m build

# Run BDD tests
test *features:
    cd tests && go run . {{features}}

# Clean build artifacts
clean:
    rm -rf dist/ build/ *.egg-info/
    rm -rf __pycache__ *.pyc
    rm -rf taidy/__pycache__ taidy/*.pyc
