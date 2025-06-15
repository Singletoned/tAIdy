#!/usr/bin/env python3
"""
Pytest test runner script for the LintAir BDD testing framework.
Provides a convenient way to run tests with different options using pytest-bdd.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Run BDD tests for LintAir CLI using pytest-bdd",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_pytest.py                                   # Run all tests
  python run_pytest.py --test python                     # Run Python linting tests
  python run_pytest.py --environment python311          # Run tests for Python environment
  python run_pytest.py --verbose                        # Verbose output
  python run_pytest.py --dry-run                        # Show what would be run
  python run_pytest.py --list-environments              # List available environments
  python run_pytest.py --html                           # Generate HTML report
  python run_pytest.py --parallel                       # Run tests in parallel
        """
    )
    
    parser.add_argument(
        "--test", "-t",
        choices=["python", "javascript", "go", "cli", "unsupported"],
        help="Run specific test suite"
    )
    
    parser.add_argument(
        "--environment", "-e",
        choices=["python311", "node18", "go121", "minimal"],
        help="Run tests for specific environment"
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
        "--html",
        action="store_true",
        help="Generate HTML test report"
    )
    
    parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="Run tests in parallel"
    )
    
    parser.add_argument(
        "--stop-on-first-failure", "-x",
        action="store_true",
        help="Stop on first test failure"
    )
    
    parser.add_argument(
        "--lf", "--last-failed",
        action="store_true",
        help="Run only tests that failed in the last run"
    )
    
    parser.add_argument(
        "--markers", "-m",
        help="Run tests matching given mark expression"
    )
    
    args = parser.parse_args()
    
    # Change to tests directory
    tests_dir = Path(__file__).parent
    os.chdir(tests_dir)
    
    if args.list_environments:
        list_environments()
        return 0
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add specific test file if requested
    if args.test:
        test_files = {
            "python": "test_python_linting.py",
            "javascript": "test_javascript_linting.py", 
            "go": "test_go_linting.py",
            "cli": "test_cli_usage.py",
            "unsupported": "test_unsupported_environments.py"
        }
        test_file = test_files.get(args.test)
        if test_file and Path(test_file).exists():
            cmd.append(test_file)
        else:
            print(f"Error: Test file not found for {args.test}")
            return 1
    
    # Add environment marker if specified
    if args.environment:
        cmd.extend(["-m", f"env_{args.environment}"])
    
    # Add custom markers
    if args.markers:
        cmd.extend(["-m", args.markers])
    
    # Add verbose flag
    if args.verbose:
        cmd.extend(["-v", "-s"])
    
    # Add HTML report
    if args.html:
        cmd.extend(["--html=reports/report.html", "--self-contained-html"])
    
    # Add parallel execution
    if args.parallel:
        cmd.extend(["-n", "auto"])
    
    # Stop on first failure
    if args.stop_on_first_failure:
        cmd.append("-x")
    
    # Last failed tests
    if args.lf:
        cmd.append("--lf")
    
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
            
        print("\nPytest markers:")
        print("=" * 40)
        markers = ["env_python311", "env_node18", "env_go121", "env_minimal", "slow", "integration", "unit"]
        for marker in markers:
            print(f"  {marker}")
            
    except Exception as e:
        print(f"Error reading environments: {e}")


def check_prerequisites():
    """Check that all prerequisites are met."""
    errors = []
    
    # Check if CLI binary exists
    cli_binary = Path("../lintair").resolve()
    linux_binary = Path("../lintair-linux").resolve()
    
    if not cli_binary.exists() and not linux_binary.exists():
        errors.append(f"CLI binary not found: {cli_binary} or {linux_binary}")
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
        import pytest
        import pytest_bdd
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