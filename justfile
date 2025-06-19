# LintAir Justfile

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

# Build the main binary
build:
    @echo "{{blue}}[INFO]{{nc}} Building lintair binary..."
    go build -o lintair
    @echo "{{green}}[SUCCESS]{{nc}} Built lintair binary"

# Build Linux binary for Docker containers
build-linux:
    @echo "{{blue}}[INFO]{{nc}} Building Linux binary for Docker containers..."
    env GOOS=linux GOARCH=amd64 go build -o lintair-linux
    @echo "{{green}}[SUCCESS]{{nc}} Built lintair-linux binary"

# Build both binaries
build-all: build build-linux

# Check if Docker is running
check-docker:
    @echo "{{blue}}[INFO]{{nc}} Checking Docker availability..."
    @if ! docker version >/dev/null 2>&1; then \
        echo "{{yellow}}[WARNING]{{nc}} Docker is not running. Tests will fail if they require containers."; \
        echo "{{blue}}[INFO]{{nc}} Please start Docker and try again."; \
    fi

# Run BDD tests with default format
test: build-linux check-docker
    @echo "{{blue}}[INFO]{{nc}} Running BDD tests with {{format}} format..."
    cd tests && go run . --godog.format={{format}}

# Run BDD tests with pretty format
test-pretty: build-linux check-docker
    @echo "{{blue}}[INFO]{{nc}} Running BDD tests with pretty format..."
    cd tests && go run . --godog.format=pretty

# Run BDD tests with progress format
test-progress: build-linux check-docker
    @echo "{{blue}}[INFO]{{nc}} Running BDD tests with progress format..."
    cd tests && go run . --godog.format=progress

# Run BDD tests with JSON format
test-json: build-linux check-docker
    @echo "{{blue}}[INFO]{{nc}} Running BDD tests with JSON format..."
    cd tests && go run . --godog.format=json

# Run specific feature file
test-feature feature: build-linux check-docker
    @echo "{{blue}}[INFO]{{nc}} Running feature: {{feature}}"
    cd tests && go run . --godog.format={{format}} {{feature}}

# Build test binary
build-tests: build-linux
    @echo "{{blue}}[INFO]{{nc}} Building test binary..."
    cd tests && go build -o lintair-tests
    @echo "{{green}}[SUCCESS]{{nc}} Built test binary at tests/lintair-tests"

# Run tests using built binary
run-tests: build-tests check-docker
    @echo "{{blue}}[INFO]{{nc}} Running tests using built binary..."
    cd tests && ./lintair-tests --godog.format={{format}}

# Install test dependencies
deps:
    @echo "{{blue}}[INFO]{{nc}} Installing test dependencies..."
    cd tests && go mod tidy
    @echo "{{green}}[SUCCESS]{{nc}} Test dependencies updated"

# Clean build artifacts
clean:
    @echo "{{blue}}[INFO]{{nc}} Cleaning build artifacts..."
    rm -f lintair lintair-linux
    cd tests && rm -f lintair-tests
    @echo "{{green}}[SUCCESS]{{nc}} Cleaned build artifacts"

# Run tests and generate coverage (if supported)
test-coverage: build-linux check-docker
    @echo "{{blue}}[INFO]{{nc}} Running tests with coverage..."
    cd tests && go test -coverprofile=coverage.out ./...
    cd tests && go tool cover -html=coverage.out -o coverage.html
    @echo "{{green}}[SUCCESS]{{nc}} Coverage report generated at tests/coverage.html"

# Lint Go code
lint:
    @echo "{{blue}}[INFO]{{nc}} Running Go linter..."
    @if command -v golangci-lint >/dev/null 2>&1; then \
        golangci-lint run; \
        cd tests && golangci-lint run; \
    else \
        echo "{{yellow}}[WARNING]{{nc}} golangci-lint not installed, running go vet instead"; \
        go vet ./...; \
        cd tests && go vet ./...; \
    fi

# Format Go code
fmt:
    @echo "{{blue}}[INFO]{{nc}} Formatting Go code..."
    go fmt ./...
    cd tests && go fmt ./...
    @echo "{{green}}[SUCCESS]{{nc}} Code formatted"

# Run all checks (format, lint, test)
check: fmt lint test-pretty

# List all available recipes
list:
    @just --list

# Quick test with specific format
test-with format: build-linux check-docker
    @echo "{{blue}}[INFO]{{nc}} Running BDD tests with {{format}} format..."
    cd tests && go run . --godog.format={{format}}

# Watch and run tests on file changes (requires watchexec)
watch:
    @echo "{{blue}}[INFO]{{nc}} Watching for changes and running tests..."
    @if command -v watchexec >/dev/null 2>&1; then \
        watchexec --exts go,feature --ignore tests/lintair-tests -- just test; \
    else \
        echo "{{red}}[ERROR]{{nc}} watchexec not installed. Install with: brew install watchexec"; \
    fi

# Dev workflow: format, lint, build, test
dev: fmt lint build-all test-pretty

# CI workflow: all checks including coverage
ci: fmt lint build-all test-coverage

# Quick smoke test (just build and run one feature)
smoke: build-linux
    @echo "{{blue}}[INFO]{{nc}} Running smoke test..."
    cd tests && go run . --godog.format=progress features/cli_usage.feature
