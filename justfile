# Taidy Justfile

# Default recipe
default: test

# Colors for output
red := '\033[0;31m'
green := '\033[0;32m'
yellow := '\033[1;33m'
blue := '\033[0;34m'
nc := '\033[0m'

# Default format for tests
format := env_var_or_default('FORMAT', 'pretty')

# Create distribution packages
dist: build
    @echo "{{blue}}[INFO]{{nc}} Creating distribution packages..."
    python3 setup.py sdist bdist_wheel
    @echo "{{green}}[SUCCESS]{{nc}} Distribution packages created in dist/"

# Variables for release builds
VERSION := env_var_or_default('VERSION', 'dev')
BUILDDATE := `date -u +%Y-%m-%dT%H:%M:%SZ`
GITCOMMIT := `git rev-parse --short HEAD 2>/dev/null || echo "unknown"`

# Run BDD tests
test: build-linux check-docker
    @echo "{{blue}}[INFO]{{nc}} Running BDD tests..."
    cd tests && go run .

# Run specific feature file
test-feature feature: build-linux check-docker
    @echo "{{blue}}[INFO]{{nc}} Running feature: {{feature}}"
    cd tests && go run . {{feature}}

# Build test binary
build-tests: build-linux
    @echo "{{blue}}[INFO]{{nc}} Building test binary..."
    cd tests && go build -o taidy-tests
    @echo "{{green}}[SUCCESS]{{nc}} Built test binary at tests/taidy-tests"
