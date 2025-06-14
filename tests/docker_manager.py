"""
Docker container management for BDD testing framework.
"""
import docker
import logging
import os
import time
import yaml
from pathlib import Path
from typing import Dict, Optional, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DockerManager:
    """Manages Docker containers for CLI testing scenarios."""
    
    def __init__(self, config_path: str = "tests/config.yaml"):
        self.config = self._load_config(config_path)
        self.client = docker.from_env()
        self.containers: Dict[str, docker.models.containers.Container] = {}
        self.images: Dict[str, str] = {}
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Config file not found: {config_path}")
            raise
            
    def build_environment_image(self, env_name: str) -> str:
        """Build Docker image for specified environment."""
        if env_name not in self.config['testing']['environments']:
            raise ValueError(f"Unknown environment: {env_name}")
            
        env_config = self.config['testing']['environments'][env_name]
        dockerfile_path = env_config['dockerfile']
        tag = env_config['tag']
        
        if not os.path.exists(dockerfile_path):
            raise FileNotFoundError(f"Dockerfile not found: {dockerfile_path}")
            
        logger.info(f"Building image {tag} from {dockerfile_path}")
        
        # Build context is the directory containing the Dockerfile
        build_context = str(Path(dockerfile_path).parent)
        dockerfile_name = Path(dockerfile_path).name
        
        try:
            image, logs = self.client.images.build(
                path=build_context,
                dockerfile=dockerfile_name,
                tag=tag,
                rm=True,
                timeout=self.config['testing']['docker']['build_timeout'],
                pull=True
            )
            
            # Log build output
            for log in logs:
                if 'stream' in log:
                    logger.debug(f"Build: {log['stream'].strip()}")
                    
            self.images[env_name] = tag
            logger.info(f"Successfully built image: {tag}")
            return tag
            
        except docker.errors.BuildError as e:
            logger.error(f"Failed to build image {tag}: {e}")
            raise
            
    def start_container(self, env_name: str, container_name: str = None) -> docker.models.containers.Container:
        """Start a container for the specified environment."""
        if env_name not in self.config['testing']['environments']:
            raise ValueError(f"Unknown environment: {env_name}")
            
        # Build image if not already built
        if env_name not in self.images:
            self.build_environment_image(env_name)
            
        tag = self.images[env_name]
        container_name = container_name or f"lintair-test-{env_name}-{int(time.time())}"
        
        # Mount the CLI binary into the container
        cli_binary_host = os.path.abspath("lintair")
        if not os.path.exists(cli_binary_host):
            raise FileNotFoundError(f"CLI binary not found: {cli_binary_host}")
            
        volumes = {
            cli_binary_host: {
                'bind': self.config['testing']['cli']['binary_path'],
                'mode': 'ro'
            },
            os.path.abspath("tests/test_files"): {
                'bind': '/test_files',
                'mode': 'rw'
            }
        }
        
        logger.info(f"Starting container {container_name} from image {tag}")
        
        try:
            container = self.client.containers.run(
                tag,
                name=container_name,
                detach=True,
                tty=True,
                stdin_open=True,
                volumes=volumes,
                network_mode=self.config['testing']['docker']['network_mode'],
                auto_remove=self.config['testing']['docker']['auto_remove'],
                working_dir="/test_files"
            )
            
            # Wait for container to be ready
            self._wait_for_container(container)
            
            self.containers[container_name] = container
            logger.info(f"Container {container_name} started successfully")
            return container
            
        except docker.errors.ContainerError as e:
            logger.error(f"Failed to start container {container_name}: {e}")
            raise
            
    def _wait_for_container(self, container: docker.models.containers.Container, timeout: int = 10):
        """Wait for container to be ready."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            container.reload()
            if container.status == 'running':
                # Test if we can execute commands
                try:
                    result = container.exec_run("echo 'ready'", timeout=5)
                    if result.exit_code == 0:
                        return
                except:
                    pass
            time.sleep(0.5)
            
        raise TimeoutError(f"Container {container.name} not ready after {timeout}s")
        
    def execute_command(self, container_name: str, command: str, timeout: int = None) -> Dict[str, Any]:
        """Execute a command in the specified container."""
        if container_name not in self.containers:
            raise ValueError(f"Container not found: {container_name}")
            
        container = self.containers[container_name]
        timeout = timeout or self.config['testing']['cli']['default_timeout']
        
        logger.debug(f"Executing in {container_name}: {command}")
        
        try:
            result = container.exec_run(
                command,
                stdout=True,
                stderr=True,
                stdin=False,
                tty=False,
                privileged=False,
                user='',
                environment=None,
                workdir='/test_files',
                detach=False,
                stream=False,
                socket=False,
                demux=True,
                timeout=timeout
            )
            
            stdout = result.output[0].decode('utf-8') if result.output[0] else ""
            stderr = result.output[1].decode('utf-8') if result.output[1] else ""
            
            command_result = {
                'exit_code': result.exit_code,
                'stdout': stdout,
                'stderr': stderr,
                'command': command,
                'container': container_name
            }
            
            logger.debug(f"Command result: exit_code={result.exit_code}")
            if stdout:
                logger.debug(f"STDOUT: {stdout}")
            if stderr:
                logger.debug(f"STDERR: {stderr}")
                
            return command_result
            
        except Exception as e:
            logger.error(f"Failed to execute command in {container_name}: {e}")
            raise
            
    def get_container_logs(self, container_name: str) -> str:
        """Get logs from specified container."""
        if container_name not in self.containers:
            return ""
            
        container = self.containers[container_name]
        try:
            return container.logs().decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to get logs from {container_name}: {e}")
            return ""
            
    def stop_container(self, container_name: str):
        """Stop and remove specified container."""
        if container_name not in self.containers:
            return
            
        container = self.containers[container_name]
        logger.info(f"Stopping container {container_name}")
        
        try:
            container.stop(timeout=10)
            if not self.config['testing']['docker']['auto_remove']:
                container.remove()
            del self.containers[container_name]
        except Exception as e:
            logger.error(f"Failed to stop container {container_name}: {e}")
            
    def cleanup_all_containers(self):
        """Stop and remove all managed containers."""
        for container_name in list(self.containers.keys()):
            self.stop_container(container_name)
            
    @contextmanager
    def container_context(self, env_name: str, container_name: str = None):
        """Context manager for container lifecycle."""
        container = None
        try:
            container = self.start_container(env_name, container_name)
            yield container
        finally:
            if container:
                self.stop_container(container.name)
                
    def list_environments(self) -> Dict[str, str]:
        """List available test environments."""
        return {
            name: config['description'] 
            for name, config in self.config['testing']['environments'].items()
        }