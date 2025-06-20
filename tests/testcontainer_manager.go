package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"time"

	"github.com/testcontainers/testcontainers-go"
	"github.com/testcontainers/testcontainers-go/wait"
)

// CommandResult holds the result of a command execution
type CommandResult struct {
	Command  string
	ExitCode int
	Stdout   string
	Stderr   string
}

// TestContainerManager handles container operations using testcontainers-go
type TestContainerManager struct {
	ctx context.Context
}

// TestContainerContext holds information about a test container using testcontainers
type TestContainerContext struct {
	Container    testcontainers.Container
	Environment  string
	scenarioName string
}

// NewTestContainerManager creates a new testcontainer manager
func NewTestContainerManager() (*TestContainerManager, error) {
	return &TestContainerManager{
		ctx: context.Background(),
	}, nil
}

// Close cleans up the testcontainer manager
func (tcm *TestContainerManager) Close() error {
	return nil
}

// GetDockerfileContent generates dynamic Dockerfile content based on environment
// Build lintair binary inside container to ensure Linux compatibility
func (tcm *TestContainerManager) GetDockerfileContent(environment string) (string, error) {
	switch environment {
	case "python311":
		return `FROM golang:1.24-alpine AS builder
COPY . /src
WORKDIR /src
RUN go mod download
RUN go build -o lintair main.go

FROM python:3.11-slim
RUN pip install ruff
COPY --from=builder /src/lintair /app/lintair
RUN chmod +x /app/lintair
WORKDIR /tmp`, nil
	case "python311-uv":
		return `FROM golang:1.24-alpine AS builder
COPY . /src
WORKDIR /src
RUN go mod download
RUN go build -o lintair main.go

FROM python:3.11-slim
RUN pip install uv
COPY --from=builder /src/lintair /app/lintair
RUN chmod +x /app/lintair
WORKDIR /tmp`, nil
	case "python311-black":
		return `FROM golang:1.24-alpine AS builder
COPY . /src
WORKDIR /src
RUN go mod download
RUN go build -o lintair main.go

FROM python:3.11-slim
RUN pip install black
COPY --from=builder /src/lintair /app/lintair
RUN chmod +x /app/lintair
WORKDIR /tmp`, nil
	case "node18":
		return `FROM golang:1.24-alpine AS builder
COPY . /src
WORKDIR /src
RUN go mod download
RUN go build -o lintair main.go

FROM node:18-slim
RUN npm install -g prettier
COPY --from=builder /src/lintair /app/lintair
RUN chmod +x /app/lintair
WORKDIR /tmp`, nil
	case "go121":
		return `FROM golang:1.24-alpine AS builder
COPY . /src
WORKDIR /src
RUN go mod download
RUN go build -o lintair main.go

FROM golang:1.24-alpine
COPY --from=builder /src/lintair /app/lintair
RUN chmod +x /app/lintair
WORKDIR /tmp`, nil
	case "minimal":
		return `FROM golang:1.24-alpine AS builder
COPY . /src
WORKDIR /src
RUN go mod download
RUN go build -o lintair main.go

FROM alpine:latest
COPY --from=builder /src/lintair /app/lintair
RUN chmod +x /app/lintair
WORKDIR /tmp`, nil
	default:
		return "", fmt.Errorf("unknown environment: %s", environment)
	}
}

// NewTestContainerContext creates a new container context using testcontainers
func NewTestContainerContext(environment string, manager *TestContainerManager) (*TestContainerContext, error) {
	// Get Dockerfile content for the environment
	dockerfileContent, err := manager.GetDockerfileContent(environment)
	if err != nil {
		return nil, fmt.Errorf("failed to get dockerfile content: %w", err)
	}

	// Create build context directory
	buildDir, err := os.MkdirTemp("", "lintair-testcontainer-*")
	if err != nil {
		return nil, fmt.Errorf("failed to create build directory: %w", err)
	}
	defer func() {
		if err != nil {
			os.RemoveAll(buildDir)
		}
	}()

	// Write Dockerfile
	dockerfilePath := filepath.Join(buildDir, "Dockerfile")
	if err := os.WriteFile(dockerfilePath, []byte(dockerfileContent), 0644); err != nil {
		return nil, fmt.Errorf("failed to write Dockerfile: %w", err)
	}

	// Copy source files to build context (go.mod, main.go, and go.sum if it exists)
	sourceFiles := []string{
		"../go.mod",
		"../main.go",
	}

	// Add go.sum if it exists (minimal apps might not have one)
	if _, err := os.Stat("../go.sum"); err == nil {
		sourceFiles = append(sourceFiles, "../go.sum")
	}

	for _, srcFile := range sourceFiles {
		if _, err := os.Stat(srcFile); err == nil {
			content, err := os.ReadFile(srcFile)
			if err != nil {
				return nil, fmt.Errorf("failed to read source file %s: %w", srcFile, err)
			}
			filename := filepath.Base(srcFile)
			if err := os.WriteFile(filepath.Join(buildDir, filename), content, 0644); err != nil {
				return nil, fmt.Errorf("failed to write source file %s: %w", filename, err)
			}
		} else {
			log.Printf("Warning: source file not found at %s", srcFile)
		}
	}

	// Create container request
	req := testcontainers.ContainerRequest{
		FromDockerfile: testcontainers.FromDockerfile{
			Context:    buildDir,
			Dockerfile: "Dockerfile",
		},
		Cmd:        []string{"sleep", "300"},
		WaitingFor: wait.ForExec([]string{"echo", "ready"}).WithStartupTimeout(60 * time.Second), // Wait for container to be ready
	}

	// Start container
	container, err := testcontainers.GenericContainer(manager.ctx, testcontainers.GenericContainerRequest{
		ContainerRequest: req,
		Started:          true,
	})
	if err != nil {
		os.RemoveAll(buildDir)
		return nil, fmt.Errorf("failed to start container: %w", err)
	}

	// Clean up build directory after successful container start
	os.RemoveAll(buildDir)

	// Get container info for logging
	containerInfo, err := container.Inspect(manager.ctx)
	if err != nil {
		container.Terminate(manager.ctx)
		return nil, fmt.Errorf("failed to inspect container: %w", err)
	}

	log.Printf("Started testcontainer %s for environment %s", containerInfo.ID[:12], environment)

	return &TestContainerContext{
		Container:   container,
		Environment: environment,
	}, nil
}

// SetScenarioName sets the scenario name for logging purposes
func (tcc *TestContainerContext) SetScenarioName(scenarioName string) {
	tcc.scenarioName = scenarioName
}

// StopContainer stops and removes the container
func (tcc *TestContainerContext) StopContainer() error {
	if tcc.Container == nil {
		return nil
	}

	containerInfo, _ := tcc.Container.Inspect(context.Background())
	containerID := ""
	if containerInfo != nil {
		containerID = containerInfo.ID[:12]
	}

	if err := tcc.Container.Terminate(context.Background()); err != nil {
		log.Printf("Warning: failed to terminate container %s: %v", containerID, err)
		return err
	}

	log.Printf("Terminated testcontainer %s", containerID)
	return nil
}

// CreateFile creates a file inside the container
func (tcc *TestContainerContext) CreateFile(filename, content string) error {
	if tcc.Container == nil {
		return fmt.Errorf("container is not available")
	}

	// Use testcontainers CopyToContainer with proper method
	filePath := fmt.Sprintf("/tmp/%s", filename)
	err := tcc.Container.CopyToContainer(context.Background(),
		[]byte(content),
		filePath,
		0644)
	if err != nil {
		return fmt.Errorf("failed to create file %s: %w", filename, err)
	}

	containerInfo, _ := tcc.Container.Inspect(context.Background())
	containerID := ""
	if containerInfo != nil {
		containerID = containerInfo.ID[:12]
	}
	log.Printf("Created file %s in testcontainer %s", filename, containerID)
	return nil
}

// ExecuteCommand executes a command inside the container
func (tcc *TestContainerContext) ExecuteCommand(command string) (*CommandResult, error) {
	if tcc.Container == nil {
		return nil, fmt.Errorf("container is not available")
	}

	exitCode, reader, err := tcc.Container.Exec(context.Background(), []string{"sh", "-c", command})
	if err != nil {
		return nil, fmt.Errorf("failed to execute command: %w", err)
	}

	// Read the output
	output := make([]byte, 4096)
	n, _ := reader.Read(output)
	outputStr := string(output[:n])

	result := &CommandResult{
		Command:  command,
		ExitCode: exitCode,
		Stdout:   outputStr,
		Stderr:   "", // testcontainers combines stdout/stderr
	}

	containerInfo, _ := tcc.Container.Inspect(context.Background())
	containerID := ""
	if containerInfo != nil {
		containerID = containerInfo.ID[:12]
	}
	log.Printf("Executed command in testcontainer %s: %s, exit code: %d", containerID, command, result.ExitCode)
	if result.Stdout != "" {
		log.Printf("Output: %s", result.Stdout)
	}

	return result, nil
}

// CopyFileIntoContainer copies a file from the host into the container
func (tcc *TestContainerContext) CopyFileIntoContainer(sourcePath, destFilename string) error {
	if tcc.Container == nil {
		return fmt.Errorf("container is not available")
	}

	// Read source file
	content, err := os.ReadFile(sourcePath)
	if err != nil {
		return fmt.Errorf("failed to read source file %s: %w", sourcePath, err)
	}

	// Copy to container
	destPath := fmt.Sprintf("/tmp/%s", destFilename)
	err = tcc.Container.CopyToContainer(context.Background(),
		content,
		destPath,
		0644)
	if err != nil {
		return fmt.Errorf("failed to copy file %s to container: %w", sourcePath, err)
	}

	containerInfo, _ := tcc.Container.Inspect(context.Background())
	containerID := ""
	if containerInfo != nil {
		containerID = containerInfo.ID[:12]
	}
	log.Printf("Copied file %s to testcontainer %s as %s", sourcePath, containerID, destFilename)
	return nil
}

// VerifyLinterInstalled checks if a linter is installed in the container
func (tcc *TestContainerContext) VerifyLinterInstalled(linter string) bool {
	result, err := tcc.ExecuteCommand(fmt.Sprintf("which %s", linter))
	if err != nil {
		return false
	}
	return result.ExitCode == 0
}
