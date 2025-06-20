package main

import (
	"bytes"
	"context"
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

// DockerManager handles Docker operations for testing
type DockerManager struct {
	ctx context.Context
}

// ContainerContext holds information about a test container
type ContainerContext struct {
	ID           string
	Name         string
	Environment  string
	dockerFile   string
	tag          string
	manager      *DockerManager
	scenarioName string
}

// NewDockerManager creates a new Docker manager
func NewDockerManager() (*DockerManager, error) {
	// Check if Docker is available
	cmd := exec.Command("docker", "--version")
	if err := cmd.Run(); err != nil {
		return nil, fmt.Errorf("Docker not available: %w", err)
	}

	return &DockerManager{
		ctx: context.Background(),
	}, nil
}

// Close closes the Docker manager
func (dm *DockerManager) Close() error {
	return nil
}

// BuildImage builds a Docker image from a Dockerfile
func (dm *DockerManager) BuildImage(dockerFile, tag string) error {
	log.Printf("Building image %s from %s", tag, dockerFile)

	// Create a temporary directory for build context
	buildDir, err := os.MkdirTemp("", "lintair-build-*")
	if err != nil {
		return fmt.Errorf("failed to create build directory: %w", err)
	}
	defer os.RemoveAll(buildDir)

	// Copy Dockerfile to build directory
	dockerFileContent, err := os.ReadFile(dockerFile)
	if err != nil {
		return fmt.Errorf("failed to read Dockerfile: %w", err)
	}

	if err := os.WriteFile(filepath.Join(buildDir, "Dockerfile"), dockerFileContent, 0644); err != nil {
		return fmt.Errorf("failed to write Dockerfile: %w", err)
	}

	// Copy lintair binary to build directory
	// Try both relative and absolute paths
	binaryPath := "../lintair"
	if _, err := os.Stat(binaryPath); err != nil {
		// Try from current working directory
		binaryPath = "lintair"
	}
	if _, err := os.Stat(binaryPath); err == nil {
		binaryContent, err := os.ReadFile(binaryPath)
		if err != nil {
			return fmt.Errorf("failed to read binary: %w", err)
		}

		if err := os.WriteFile(filepath.Join(buildDir, "lintair"), binaryContent, 0755); err != nil {
			return fmt.Errorf("failed to write binary: %w", err)
		}
	} else {
		log.Printf("Warning: lintair binary not found at %s", binaryPath)
	}

	// Run docker build
	cmd := exec.Command("docker", "build", "-t", tag, buildDir)
	output, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("failed to build image: %w, output: %s", err, string(output))
	}

	log.Printf("Build output: %s", string(output))
	return nil
}

// CheckImageExists checks if a Docker image exists locally
func (dm *DockerManager) CheckImageExists(tag string) bool {
	cmd := exec.Command("docker", "images", "-q", tag)
	output, err := cmd.Output()
	return err == nil && len(strings.TrimSpace(string(output))) > 0
}

// NewContainerContext creates a new container context
func NewContainerContext(environment, dockerFile, tag string, manager *DockerManager) *ContainerContext {
	return &ContainerContext{
		Environment: environment,
		dockerFile:  dockerFile,
		tag:         tag,
		manager:     manager,
	}
}

// SetScenarioName sets the scenario name for container naming
func (cc *ContainerContext) SetScenarioName(scenarioName string) {
	cc.scenarioName = scenarioName
}

// StartContainer starts a new container for testing
func (cc *ContainerContext) StartContainer() error {
	// Build image if it doesn't exist locally
	if !cc.manager.CheckImageExists(cc.tag) {
		if err := cc.manager.BuildImage(cc.dockerFile, cc.tag); err != nil {
			return fmt.Errorf("failed to build image: %w", err)
		}
	}

	// Create and start container with scenario-based name
	scenarioKey := strings.ReplaceAll(strings.ToLower(cc.scenarioName), " ", "-")
	scenarioKey = strings.ReplaceAll(scenarioKey, ",", "")
	scenarioKey = strings.ReplaceAll(scenarioKey, "'", "")
	containerName := fmt.Sprintf("lintair-%s-%s", scenarioKey, cc.Environment)

	cmd := exec.Command("docker", "run", "-d", "--rm", "--name", containerName,
		"-w", "/tmp", cc.tag, "sleep", "300")
	output, err := cmd.Output()
	if err != nil {
		return fmt.Errorf("failed to start container: %w, output: %s", err, string(output))
	}

	cc.ID = strings.TrimSpace(string(output))
	cc.Name = containerName

	log.Printf("Started container %s (%s)", cc.Name, cc.ID[:12])
	return nil
}

// StopContainer stops and removes the container
func (cc *ContainerContext) StopContainer() error {
	if cc.ID == "" {
		return nil
	}

	cmd := exec.Command("docker", "stop", cc.ID)
	if err := cmd.Run(); err != nil {
		log.Printf("Warning: failed to stop container %s: %v", cc.ID[:12], err)
	}

	log.Printf("Stopped container %s", cc.ID[:12])
	return nil
}

// CreateFile creates a file inside the container
func (cc *ContainerContext) CreateFile(filename, content string) error {
	// Create file using docker exec
	cmd := exec.Command("docker", "exec", cc.ID, "sh", "-c",
		fmt.Sprintf("cat > /tmp/%s", filename))
	cmd.Stdin = strings.NewReader(content)

	if err := cmd.Run(); err != nil {
		return fmt.Errorf("failed to create file %s: %w", filename, err)
	}

	log.Printf("Created file %s in container %s", filename, cc.ID[:12])
	return nil
}

// ExecuteCommand executes a command inside the container
func (cc *ContainerContext) ExecuteCommand(command string) (*CommandResult, error) {
	// Execute command using docker exec
	dockerCmd := exec.Command("docker", "exec", cc.ID, "sh", "-c", command)

	var stdout, stderr bytes.Buffer
	dockerCmd.Stdout = &stdout
	dockerCmd.Stderr = &stderr

	err := dockerCmd.Run()
	exitCode := 0
	if err != nil {
		if exitError, ok := err.(*exec.ExitError); ok {
			exitCode = exitError.ExitCode()
		} else {
			exitCode = 1
		}
	}

	result := &CommandResult{
		Command:  command,
		ExitCode: exitCode,
		Stdout:   stdout.String(),
		Stderr:   stderr.String(),
	}

	log.Printf("Executed command: %s, exit code: %d", command, result.ExitCode)
	if result.Stdout != "" {
		log.Printf("Stdout: %s", result.Stdout)
	}
	if result.Stderr != "" {
		log.Printf("Stderr: %s", result.Stderr)
	}

	return result, nil
}

// CopyFileIntoContainer copies a file from the host into the container
func (cc *ContainerContext) CopyFileIntoContainer(sourcePath, destFilename string) error {
	// Use docker cp to copy file into container
	containerPath := fmt.Sprintf("%s:/tmp/%s", cc.ID, destFilename)
	cmd := exec.Command("docker", "cp", sourcePath, containerPath)

	if err := cmd.Run(); err != nil {
		return fmt.Errorf("failed to copy file %s to container: %w", sourcePath, err)
	}

	log.Printf("Copied file %s to container %s as %s", sourcePath, cc.ID[:12], destFilename)
	return nil
}

// VerifyLinterInstalled checks if a linter is installed in the container
func (cc *ContainerContext) VerifyLinterInstalled(linter string) bool {
	result, err := cc.ExecuteCommand(fmt.Sprintf("which %s", linter))
	if err != nil {
		return false
	}
	return result.ExitCode == 0
}

// CommandResult holds the result of a command execution
type CommandResult struct {
	Command  string
	ExitCode int
	Stdout   string
	Stderr   string
}
