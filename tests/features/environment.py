"""
Behave environment setup for Docker-based CLI testing.
"""
import logging
import os
import sys
from pathlib import Path

# Add the tests directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from docker_manager import DockerManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('tests.log')
    ]
)
logger = logging.getLogger(__name__)


def before_all(context):
    """Set up test environment before all scenarios."""
    logger.info("Initializing test environment")
    
    # Initialize Docker manager
    context.docker_manager = DockerManager()
    
    # Initialize test state
    context.test_results = {}
    context.current_container = None
    context.current_environment = None
    
    # Ensure CLI binary exists
    cli_binary = os.path.abspath("lintair")
    if not os.path.exists(cli_binary):
        logger.error(f"CLI binary not found: {cli_binary}")
        logger.error("Please build the lintair binary first: go build -o lintair")
        sys.exit(1)
        
    logger.info("Test environment initialized successfully")


def before_scenario(context, scenario):
    """Set up before each scenario."""
    logger.info(f"Starting scenario: {scenario.name}")
    
    # Reset test state for new scenario
    context.command_result = None
    context.test_files = []
    context.expected_files = []
    
    # Extract environment from scenario tags
    environment = None
    for tag in scenario.tags:
        if tag.startswith('env:'):
            environment = tag.split(':', 1)[1]
            break
            
    if environment:
        context.current_environment = environment
        logger.info(f"Using environment: {environment}")
        
        # Start container for this environment
        try:
            container_name = f"test-{scenario.name.lower().replace(' ', '-')}"
            context.current_container = context.docker_manager.start_container(
                environment, 
                container_name
            )
            logger.info(f"Container started: {container_name}")
        except Exception as e:
            logger.error(f"Failed to start container for environment {environment}: {e}")
            raise


def after_scenario(context, scenario):
    """Clean up after each scenario."""
    logger.info(f"Cleaning up scenario: {scenario.name}")
    
    # Capture container logs if scenario failed
    if scenario.status == "failed" and context.current_container:
        logger.info("Scenario failed, capturing container logs...")
        logs = context.docker_manager.get_container_logs(context.current_container.name)
        if logs:
            logger.error(f"Container logs:\n{logs}")
            
    # Stop container
    if context.current_container:
        try:
            context.docker_manager.stop_container(context.current_container.name)
            logger.info(f"Container stopped: {context.current_container.name}")
        except Exception as e:
            logger.error(f"Failed to stop container: {e}")
        finally:
            context.current_container = None
            context.current_environment = None


def after_all(context):
    """Clean up after all scenarios."""
    logger.info("Cleaning up test environment")
    
    # Clean up any remaining containers
    try:
        context.docker_manager.cleanup_all_containers()
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        
    logger.info("Test environment cleanup completed")


def before_step(context, step):
    """Before each step."""
    logger.debug(f"Executing step: {step.name}")


def after_step(context, step):
    """After each step."""
    if step.status == "failed":
        logger.error(f"Step failed: {step.name}")
        if hasattr(context, 'command_result') and context.command_result:
            logger.error(f"Last command result: {context.command_result}")
    else:
        logger.debug(f"Step passed: {step.name}")


def before_tag(context, tag):
    """Handle specific tags."""
    if tag.startswith('env:'):
        # Environment tag is handled in before_scenario
        pass
    elif tag == 'skip':
        # Skip scenarios with @skip tag
        context.scenario.skip("Scenario marked as @skip")
        

def after_tag(context, tag):
    """After tag processing."""
    pass