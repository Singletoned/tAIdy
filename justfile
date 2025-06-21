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

# Build the main binary (same as Linux for consistency)
build:
    @echo "{{blue}}[INFO]{{nc}} Building taidy binary..."
    go build -o taidy
    @echo "{{green}}[SUCCESS]{{nc}} Built taidy binary"

# Build Linux binary for Docker containers (same as main binary)
build-linux:
    @echo "{{blue}}[INFO]{{nc}} Building Linux binary for Docker containers..."
    env GOOS=linux GOARCH=amd64 go build -o taidy
    @echo "{{green}}[SUCCESS]{{nc}} Built taidy binary"

# Build both binaries (now just one build)
build-all: build

# Build for all platforms
build-cross-platform: clean
    @echo "{{blue}}[INFO]{{nc}} Building for multiple platforms..."
    @mkdir -p dist
    env GOOS=linux GOARCH=amd64 go build -ldflags="-X main.Version={{VERSION}} -X main.BuildDate={{BUILDDATE}}" -o dist/taidy-linux-amd64
    env GOOS=linux GOARCH=arm64 go build -ldflags="-X main.Version={{VERSION}} -X main.BuildDate={{BUILDDATE}}" -o dist/taidy-linux-arm64
    env GOOS=darwin GOARCH=amd64 go build -ldflags="-X main.Version={{VERSION}} -X main.BuildDate={{BUILDDATE}}" -o dist/taidy-darwin-amd64  
    env GOOS=darwin GOARCH=arm64 go build -ldflags="-X main.Version={{VERSION}} -X main.BuildDate={{BUILDDATE}}" -o dist/taidy-darwin-arm64
    env GOOS=windows GOARCH=amd64 go build -ldflags="-X main.Version={{VERSION}} -X main.BuildDate={{BUILDDATE}}" -o dist/taidy-windows-amd64.exe
    @echo "{{green}}[SUCCESS]{{nc}} Built binaries for all platforms in dist/"

# Variables for release builds
VERSION := env_var_or_default('VERSION', 'dev')
BUILDDATE := `date -u +%Y-%m-%dT%H:%M:%SZ`
GITCOMMIT := `git rev-parse --short HEAD 2>/dev/null || echo "unknown"`

# Build with version information
build-release:
    @echo "{{blue}}[INFO]{{nc}} Building release version {{VERSION}}..."
    go build -ldflags="-X main.Version={{VERSION}} -X main.GitCommit={{GITCOMMIT}} -X main.BuildDate={{BUILDDATE}}" -o taidy
    @echo "{{green}}[SUCCESS]{{nc}} Built taidy {{VERSION}}"

# Create release archives
package: build-cross-platform
    @echo "{{blue}}[INFO]{{nc}} Packaging releases..."
    cd dist && tar -czf taidy-{{VERSION}}-linux-amd64.tar.gz taidy-linux-amd64
    cd dist && tar -czf taidy-{{VERSION}}-linux-arm64.tar.gz taidy-linux-arm64
    cd dist && tar -czf taidy-{{VERSION}}-darwin-amd64.tar.gz taidy-darwin-amd64
    cd dist && tar -czf taidy-{{VERSION}}-darwin-arm64.tar.gz taidy-darwin-arm64
    cd dist && zip taidy-{{VERSION}}-windows-amd64.zip taidy-windows-amd64.exe
    @echo "{{green}}[SUCCESS]{{nc}} Created release packages in dist/"

# Clean build artifacts
clean:
    @echo "{{blue}}[INFO]{{nc}} Cleaning build artifacts..."
    rm -rf dist/
    rm -f taidy lintair
    @echo "{{green}}[SUCCESS]{{nc}} Cleaned build artifacts"

# Check if Docker is running
check-docker:
    @echo "{{blue}}[INFO]{{nc}} Checking Docker availability..."
    @if ! docker version >/dev/null 2>&1; then \
        echo "{{yellow}}[WARNING]{{nc}} Docker is not running. Tests will fail if they require containers."; \
        echo "{{blue}}[INFO]{{nc}} Please start Docker and try again."; \
    fi

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
check: fmt lint test

# Dev workflow: format, lint, build, test
dev: fmt lint build-all test

# CI workflow: all checks including coverage
ci: fmt lint build-all test-coverage

# Quick smoke test (just build and run one feature)
smoke: build-linux
    @echo "{{blue}}[INFO]{{nc}} Running smoke test..."
    cd tests && go run . --godog.format=progress features/cli_usage.feature
