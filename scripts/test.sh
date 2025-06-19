#!/bin/bash

# LintAir Test Runner Script
# Run BDD tests from the project root

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show help
show_help() {
    echo "LintAir BDD Test Runner"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -f, --format FORMAT Set output format (pretty, progress, json)"
    echo "  -v, --verbose       Enable verbose output"
    echo "  --feature FILE      Run specific feature file"
    echo "  --build-only        Only build binaries, don't run tests"
    echo "  --no-build          Skip building binaries"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Run all tests"
    echo "  $0 --format=pretty                   # Run with pretty format"
    echo "  $0 --feature=features/cli_usage.feature  # Run specific feature"
    echo "  $0 --build-only                      # Just build binaries"
}

# Default values
FORMAT="pretty"
VERBOSE=false
FEATURE=""
BUILD_ONLY=false
NO_BUILD=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -f|--format)
            FORMAT="$2"
            shift 2
            ;;
        --format=*)
            FORMAT="${1#*=}"
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --feature)
            FEATURE="$2"
            shift 2
            ;;
        --feature=*)
            FEATURE="${1#*=}"
            shift
            ;;
        --build-only)
            BUILD_ONLY=true
            shift
            ;;
        --no-build)
            NO_BUILD=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if we're in the project root
if [[ ! -f "main.go" ]] || [[ ! -d "tests" ]]; then
    print_error "This script must be run from the project root directory"
    exit 1
fi

# Build binaries unless --no-build is specified
if [[ "$NO_BUILD" != true ]]; then
    print_info "Building lintair binary..."
    if go build -o lintair; then
        print_success "Built lintair binary"
    else
        print_error "Failed to build lintair binary"
        exit 1
    fi

    print_info "Building Linux binary for Docker containers..."
    if GOOS=linux GOARCH=amd64 go build -o lintair-linux; then
        print_success "Built lintair-linux binary"
    else
        print_error "Failed to build lintair-linux binary"
        exit 1
    fi
fi

# Exit if build-only is specified
if [[ "$BUILD_ONLY" == true ]]; then
    print_success "Build completed successfully"
    exit 0
fi

# Check if Docker is running
print_info "Checking Docker availability..."
if ! docker version >/dev/null 2>&1; then
    print_warning "Docker is not running. Tests will fail if they require containers."
    print_info "Please start Docker and try again."
fi

# Prepare test command
TEST_CMD="go run ."

# Add format option
if [[ -n "$FORMAT" ]]; then
    TEST_CMD="$TEST_CMD --godog.format=$FORMAT"
fi

# Add feature file if specified
if [[ -n "$FEATURE" ]]; then
    TEST_CMD="$TEST_CMD $FEATURE"
fi

# Run tests
print_info "Running BDD tests..."
print_info "Command: cd tests && $TEST_CMD"

cd tests

if [[ "$VERBOSE" == true ]]; then
    print_info "Running with verbose output..."
fi

if eval "$TEST_CMD"; then
    print_success "All tests completed successfully!"
    exit 0
else
    exit_code=$?
    print_error "Tests failed with exit code $exit_code"
    exit $exit_code
fi