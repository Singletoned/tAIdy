#!/usr/bin/env python3
"""
Test runner script for the LintAir BDD testing framework.
Provides a convenient way to run tests with different options.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Run BDD tests for LintAir CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                                    # Run all tests
  python run_tests.py --feature python_linting          # Run specific feature
  python run_tests.py --tag env:python311               # Run tests for Python environment
  python run_tests.py --verbose                         # Verbose output
  python run_tests.py --dry-run                         # Show what would be run
  python run_tests.py --list-environments               # List available environments
        """
    )
    
    parser.add_argument(
        "--feature", "-f",
        help="Run specific feature file (e.g., python_linting)"
    )
    
    parser.add_argument(
        "--tag", "-t",
        help="Run tests with specific tag (e.g., env:python311)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true", 
        help="Show what would be run without executing"
    )
    
    parser.add_argument(
        "--list-environments",
        action="store_true",
        help="List available test environments"
    )
    
    parser.add_argument(
        "--format", 
        choices=["pretty", "plain", "json"],
        default="pretty",
        help="Output format (default: pretty)"
    )
    
    parser.add_argument(
        "--stop-on-first-failure",
        action="store_true",
        help="Stop on first test failure"
    )
    
    parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="Run tests in parallel (if configured)"
    )
    
    args = parser.parse_args()
    
    # Change to tests directory
    tests_dir = Path(__file__).parent
    os.chdir(tests_dir)
    
    if args.list_environments:
        list_environments()
        return 0
    
    # Build behave command
    cmd = ["behave"]
    
    # Add format
    cmd.extend(["--format", args.format])
    
    # Add feature if specified
    if args.feature:
        feature_file = f"features/{args.feature}.feature"
        if not Path(feature_file).exists():
            print(f"Error: Feature file not found: {feature_file}")
            return 1
        cmd.append(feature_file)
    
    # Add tag if specified
    if args.tag:
        cmd.extend(["--tags", args.tag])
    
    # Add verbose flag
    if args.verbose:
        cmd.extend(["--verbose", "--capture=no"])
    
    # Stop on first failure
    if args.stop_on_first_failure:
        cmd.append("--stop")
    
    # Show command that would be run
    print(f"Running: {' '.join(cmd)}")
    
    if args.dry_run:
        print("Dry run - command not executed")
        return 0
    
    # Check prerequisites
    if not check_prerequisites():
        return 1
    
    # Run the tests
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 130
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


def list_environments():
    """List available test environments."""
    try:
        import yaml
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
        
        environments = config.get("testing", {}).get("environments", {})
        
        print("Available test environments:")
        print("=" * 40)
        for name, env_config in environments.items():
            description = env_config.get("description", "No description")
            dockerfile = env_config.get("dockerfile", "Unknown")
            print(f"  {name:15} - {description}")
            print(f"  {' ' * 15}   Dockerfile: {dockerfile}")
            print()
            
    except Exception as e:
        print(f"Error reading environments: {e}")


def check_prerequisites():
    """Check that all prerequisites are met."""
    errors = []
    
    # Check if CLI binary exists
    cli_binary = Path("../lintair").resolve()
    if not cli_binary.exists():
        errors.append(f"CLI binary not found: {cli_binary}")
        errors.append("Please build it first: go build -o lintair")
    
    # Check if Docker is running
    try:
        result = subprocess.run(
            ["docker", "info"], 
            capture_output=True, 
            check=False,
            timeout=10
        )
        if result.returncode != 0:
            errors.append("Docker is not running or not accessible")
            errors.append("Please start Docker and ensure it's accessible")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        errors.append("Docker command not found or not responding")
        errors.append("Please install Docker and ensure it's in your PATH")
    
    # Check Python dependencies
    try:
        import behave
        import docker
        import yaml
    except ImportError as e:
        errors.append(f"Missing Python package: {e}")
        errors.append("Please install dependencies: pip install -r requirements.txt")
    
    if errors:
        print("Prerequisites check failed:")
        for error in errors:
            print(f"  ❌ {error}")
        return False
    
    print("✅ All prerequisites met")
    return True


if __name__ == "__main__":
    sys.exit(main())