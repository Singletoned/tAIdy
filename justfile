# Taidy Justfile

# Default recipe
default: test

# Create distribution packages
dist: build
    python3 -m build

# Run BDD tests
test feature:
    cd tests && go run . {{feature}}

# Clean build artifacts
clean:
    rm -rf dist/ build/ *.egg-info/
    rm -rf __pycache__ *.pyc
    rm -rf taidy/__pycache__ taidy/*.pyc
