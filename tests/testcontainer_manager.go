package main

import (
	"context"
	"fmt"
	"io"
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

// copyDir recursively copies a directory tree
func copyDir(src, dst string) error {
	info, err := os.Stat(src)
	if err != nil {
		return err
	}

	if err := os.MkdirAll(dst, info.Mode()); err != nil {
		return err
	}

	entries, err := os.ReadDir(src)
	if err != nil {
		return err
	}

	for _, entry := range entries {
		srcPath := filepath.Join(src, entry.Name())
		dstPath := filepath.Join(dst, entry.Name())

		if entry.IsDir() {
			if err := copyDir(srcPath, dstPath); err != nil {
				return err
			}
		} else {
			if err := copyFile(srcPath, dstPath); err != nil {
				return err
			}
		}
	}

	return nil
}

// copyFile copies a single file
func copyFile(src, dst string) error {
	srcFile, err := os.Open(src)
	if err != nil {
		return err
	}
	defer srcFile.Close()

	info, err := srcFile.Stat()
	if err != nil {
		return err
	}

	dstFile, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer dstFile.Close()

	if err := dstFile.Chmod(info.Mode()); err != nil {
		return err
	}

	_, err = io.Copy(dstFile, srcFile)
	return err
}

// GetDockerfileContent generates dynamic Dockerfile content based on environment
// Expects pre-built taidy binary to be copied in
func (tcm *TestContainerManager) GetDockerfileContent(environment string) (string, error) {
	switch environment {
	case "python311":
		return `FROM python:3.11-slim
RUN pip install ruff
COPY taidy /app/taidy
ENV PYTHONPATH=/app
WORKDIR /tmp`, nil
	case "python311-uv":
		return `FROM python:3.11-slim
RUN pip install uv
COPY taidy /app/taidy
ENV PYTHONPATH=/app
WORKDIR /tmp`, nil
	case "python311-black":
		return `FROM python:3.11-slim
RUN pip install black
COPY taidy /app/taidy
ENV PYTHONPATH=/app
WORKDIR /tmp`, nil
	case "node18":
		return `FROM node:18-slim
RUN apt-get update && apt-get install -y python3
RUN npm install -g prettier
COPY taidy /app/taidy
ENV PYTHONPATH=/app
WORKDIR /tmp`, nil
	case "go121":
		return `FROM golang:1.24-alpine
RUN apk add --no-cache python3
COPY taidy /app/taidy
ENV PYTHONPATH=/app
WORKDIR /tmp`, nil
	case "shell-tools":
		return `FROM ubuntu:22.04
RUN apt-get update && apt-get install -y shellcheck
RUN apt-get install -y wget && \
    wget -O /usr/local/bin/shfmt https://github.com/mvdan/sh/releases/download/v3.7.0/shfmt_v3.7.0_linux_amd64 && \
    chmod +x /usr/local/bin/shfmt
RUN apt-get install -y python3 python3-pip && pip3 install beautysh
COPY taidy /app/taidy
ENV PYTHONPATH=/app
WORKDIR /tmp`, nil
	case "minimal":
		return `FROM alpine:latest
RUN apk add --no-cache python3
COPY taidy /app/taidy
ENV PYTHONPATH=/app
WORKDIR /tmp`, nil
	case "python311-trufflehog":
		return `FROM python:3.11-slim
RUN pip install ruff
RUN apt-get update && apt-get install -y wget && \
    wget -O /tmp/trufflehog.tar.gz https://github.com/trufflesecurity/trufflehog/releases/download/v3.89.2/trufflehog_3.89.2_linux_amd64.tar.gz && \
    tar -xzf /tmp/trufflehog.tar.gz -C /usr/local/bin/ && \
    chmod +x /usr/local/bin/trufflehog && \
    rm /tmp/trufflehog.tar.gz
COPY taidy /app/taidy
ENV PYTHONPATH=/app
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

	// Copy Python package to build context
	packagePath := "../taidy"
	if _, err := os.Stat(packagePath); err != nil {
		return nil, fmt.Errorf("taidy package not found at %s", packagePath)
	}

	// Copy the entire taidy package
	if err := copyDir(packagePath, filepath.Join(buildDir, "taidy")); err != nil {
		return nil, fmt.Errorf("failed to copy taidy package: %w", err)
	}

	// Create container request with optimizations
	req := testcontainers.ContainerRequest{
		FromDockerfile: testcontainers.FromDockerfile{
			Context:    buildDir,
			Dockerfile: "Dockerfile",
			// Cache intermediate layers for faster builds
			BuildArgs: map[string]*string{},
		},
		Cmd:        []string{"sleep", "300"},
		WaitingFor: wait.ForExec([]string{"echo", "ready"}).WithStartupTimeout(45 * time.Second), // Reduced timeout
		Labels: map[string]string{
			"taidy.environment": environment,
			"taidy.test":        "true",
		},
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

	// Silently started container

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

	if err := tcc.Container.Terminate(context.Background()); err != nil {
		// Silently ignore termination errors - container may already be terminated
		return nil
	}

	// Silently terminated container
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

	// Silently created file
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

	// Silently executed command

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

	// Silently copied file
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
