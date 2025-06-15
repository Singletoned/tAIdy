"""
Pytest configuration and fixtures for the BDD testing framework.
"""
import pytest
import logging
import os
import sys
from pathlib import Path
from typing import Generator, Dict, Any, Optional

# Add the tests directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from docker_manager import DockerManager

logger = logging.getLogger(__name__)


def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Ensure reports directory exists
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add environment markers."""
    for item in items:
        # Add environment markers based on test module/function names
        if "python311" in item.nodeid:
            item.add_marker(pytest.mark.env_python311)
        elif "node18" in item.nodeid:
            item.add_marker(pytest.mark.env_node18)
        elif "go121" in item.nodeid:
            item.add_marker(pytest.mark.env_go121)
        elif "minimal" in item.nodeid:
            item.add_marker(pytest.mark.env_minimal)


@pytest.fixture(scope="session")
def docker_manager() -> Generator[DockerManager, None, None]:
    """Create and manage DockerManager for the test session."""
    logger.info("Initializing Docker manager for test session")
    
    # Ensure CLI binary exists
    linux_binary = Path("../lintair-linux").resolve()
    regular_binary = Path("../lintair").resolve()
    cli_binary = linux_binary if linux_binary.exists() else regular_binary
    
    if not cli_binary.exists():
        pytest.fail(f"CLI binary not found: {cli_binary}. Please build it first.")
    
    manager = DockerManager("config.yaml")
    
    try:
        yield manager
    finally:
        logger.info("Cleaning up Docker manager")
        try:
            manager.cleanup_all_containers()
        except Exception as e:
            logger.error(f"Error during Docker cleanup: {e}")


@pytest.fixture
def container_context():
    """Context manager for test containers."""
    contexts = {}
    
    def get_context(environment: str, container_name: str = None):
        """Get or create a container context for the given environment."""
        if environment not in contexts:
            contexts[environment] = ContainerContext(environment, container_name)
        return contexts[environment]
    
    yield get_context
    
    # Cleanup all contexts
    for context in contexts.values():
        try:
            context.cleanup()
        except Exception as e:
            logger.error(f"Error cleaning up container context: {e}")


class ContainerContext:
    """Context manager for individual test containers."""
    
    def __init__(self, environment: str, container_name: str = None):
        self.environment = environment
        self.container_name = container_name
        self.container = None
        self.docker_manager = None
        self.test_files = []
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        
    def start_container(self, docker_manager: DockerManager) -> None:
        """Start the container for this environment."""
        self.docker_manager = docker_manager
        
        if not self.container_name:
            import time
            self.container_name = f"test-{self.environment}-{int(time.time())}"
            
        logger.info(f"Starting container {self.container_name} for environment {self.environment}")
        
        try:
            self.container = docker_manager.start_container(
                self.environment,
                self.container_name
            )
            logger.info(f"Container {self.container_name} started successfully")
        except Exception as e:
            logger.error(f"Failed to start container: {e}")
            raise
            
    def execute_command(self, command: str, timeout: int = None) -> Dict[str, Any]:
        """Execute a command in the container."""
        if not self.container or not self.docker_manager:
            raise RuntimeError("Container not started")
            
        return self.docker_manager.execute_command(
            self.container_name,
            command,
            timeout
        )
        
    def create_file(self, filename: str, content: str) -> None:
        """Create a file in the container."""
        if not self.container or not self.docker_manager:
            raise RuntimeError("Container not started")
            
        # Escape single quotes in content
        escaped_content = content.replace("'", "'\"'\"'")
        write_cmd = f"printf '%s' '{escaped_content}' > {filename}"
        
        result = self.execute_command(write_cmd)
        if result['exit_code'] != 0:
            raise Exception(f"Failed to create file {filename}: {result['stderr']}")
            
        self.test_files.append(filename)
        
    def verify_linter_installed(self, linter: str) -> bool:
        """Verify that a linter is installed in the container."""
        if not self.container or not self.docker_manager:
            raise RuntimeError("Container not started")
            
        result = self.execute_command(f"which {linter}")
        return result['exit_code'] == 0
        
    def cleanup(self) -> None:
        """Clean up the container."""
        if self.container and self.docker_manager:
            try:
                self.docker_manager.stop_container(self.container_name)
                logger.info(f"Container {self.container_name} stopped")
            except Exception as e:
                logger.error(f"Failed to stop container {self.container_name}: {e}")
            finally:
                self.container = None
                self.docker_manager = None


@pytest.fixture
def python311_container(docker_manager, container_context):
    """Fixture for Python 3.11 container."""
    context = container_context("python311")
    context.start_container(docker_manager)
    yield context
    

@pytest.fixture  
def node18_container(docker_manager, container_context):
    """Fixture for Node.js 18 container."""
    context = container_context("node18")
    context.start_container(docker_manager)
    yield context


@pytest.fixture
def go121_container(docker_manager, container_context):
    """Fixture for Go 1.21 container."""
    context = container_context("go121")
    context.start_container(docker_manager)
    yield context


@pytest.fixture
def minimal_container(docker_manager, container_context):
    """Fixture for minimal container."""
    context = container_context("minimal")
    context.start_container(docker_manager)
    yield context


# Helper functions for BDD step implementations
def file_extensions_map():
    """Map file types to extensions."""
    return {
        'Python': '.py',
        'JavaScript': '.js', 
        'TypeScript': '.ts',
        'Go': '.go',
        'JSON': '.json',
        'CSS': '.css',
        'HTML': '.html',
        'Markdown': '.md'
    }


def linter_pattern_map():
    """Map file patterns to their linters."""
    return {
        'Python': r'\.py$',
        'JavaScript': r'\.(js|jsx)$',
        'TypeScript': r'\.(ts|tsx)$',
        'Go': r'\.go$',
        'JSON': r'\.json$',
        'CSS': r'\.(css|scss)$',
        'HTML': r'\.html$'
    }


# Pytest-BDD fixtures for step context
@pytest.fixture
def bdd_context():
    """BDD context object to share state between steps."""
    return type('Context', (), {
        'test_files': [],
        'command_result': None,
        'expected_files': [],
        'current_container': None
    })()


def pytest_bdd_step_error(request, feature, scenario, step, step_func, exception):
    """Handle BDD step errors."""
    logger.error(f"Step failed in {feature.name}::{scenario.name}::{step.name}")
    logger.error(f"Exception: {exception}")
    
    # Try to capture container logs if available
    if hasattr(request, 'node') and hasattr(request.node, 'container_context'):
        try:
            context = request.node.container_context
            if context.container and context.docker_manager:
                logs = context.docker_manager.get_container_logs(context.container_name)
                if logs:
                    logger.error(f"Container logs:\n{logs}")
        except Exception as e:
            logger.error(f"Failed to capture container logs: {e}")


def pytest_runtest_makereport(item, call):
    """Generate test report with container information."""
    if call.when == "call":
        # Add container information to test report
        if hasattr(item, 'container_context'):
            try:
                context = item.container_context
                if context.container:
                    item.user_properties.append(
                        ("container_name", context.container_name)
                    )
                    item.user_properties.append(
                        ("environment", context.environment)
                    )
            except Exception:
                pass