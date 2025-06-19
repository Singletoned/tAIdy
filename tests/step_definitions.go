package main

import (
	"context"
	"fmt"
	"log"
	"regexp"
	"strconv"
	"strings"

	"github.com/cucumber/godog"
)

// TestContext holds the state for BDD tests
type TestContext struct {
	dockerManager    *DockerManager
	currentContainer *ContainerContext
	testFiles        []string
	commandResult    *CommandResult
}

// NewTestContext creates a new test context
func NewTestContext() *TestContext {
	dm, err := NewDockerManager()
	if err != nil {
		log.Fatalf("Failed to create Docker manager: %v", err)
	}
	
	return &TestContext{
		dockerManager: dm,
		testFiles:     make([]string, 0),
	}
}

// Close cleans up the test context
func (tc *TestContext) Close() error {
	if tc.currentContainer != nil {
		tc.currentContainer.StopContainer()
	}
	return tc.dockerManager.Close()
}

// SetupContainer sets up a container for the given environment
func (tc *TestContext) SetupContainer(environment string) error {
	environments := map[string]struct {
		dockerfile string
		tag        string
	}{
		"python311": {"docker/python/python311.Dockerfile", "lintair-test:python311"},
		"node18":    {"docker/js/node18.Dockerfile", "lintair-test:node18"},
		"go121":     {"docker/go/go121.Dockerfile", "lintair-test:go121"},
		"minimal":   {"docker/minimal.Dockerfile", "lintair-test:minimal"},
	}

	envConfig, exists := environments[environment]
	if !exists {
		return fmt.Errorf("unknown environment: %s", environment)
	}

	tc.currentContainer = NewContainerContext(environment, envConfig.dockerfile, envConfig.tag, tc.dockerManager)
	return tc.currentContainer.StartContainer()
}

// Step Definitions

func (tc *TestContext) theFollowingPythonFileExists(docString *godog.DocString) error {
	if tc.currentContainer == nil {
		if err := tc.SetupContainer("python311"); err != nil {
			return err
		}
	}

	content := ""
	if docString != nil {
		content = docString.Content
	}
	
	filename := fmt.Sprintf("test_%d.py", len(tc.testFiles)+1)
	if err := tc.currentContainer.CreateFile(filename, content); err != nil {
		return fmt.Errorf("failed to create Python file: %w", err)
	}
	
	tc.testFiles = append(tc.testFiles, filename)
	return nil
}

func (tc *TestContext) theFollowingJavaScriptFileExists(docString *godog.DocString) error {
	if tc.currentContainer == nil {
		if err := tc.SetupContainer("node18"); err != nil {
			return err
		}
	}

	content := ""
	if docString != nil {
		content = docString.Content
	}
	
	filename := fmt.Sprintf("test_%d.js", len(tc.testFiles)+1)
	if err := tc.currentContainer.CreateFile(filename, content); err != nil {
		return fmt.Errorf("failed to create JavaScript file: %w", err)
	}
	
	tc.testFiles = append(tc.testFiles, filename)
	return nil
}

func (tc *TestContext) theFollowingGoFileExists(docString *godog.DocString) error {
	if tc.currentContainer == nil {
		if err := tc.SetupContainer("go121"); err != nil {
			return err
		}
	}

	content := ""
	if docString != nil {
		content = docString.Content
	}
	
	filename := fmt.Sprintf("test_%d.go", len(tc.testFiles)+1)
	if err := tc.currentContainer.CreateFile(filename, content); err != nil {
		return fmt.Errorf("failed to create Go file: %w", err)
	}
	
	tc.testFiles = append(tc.testFiles, filename)
	return nil
}

func (tc *TestContext) linterIsInstalled(linter string) error {
	if tc.currentContainer == nil {
		return fmt.Errorf("no container available for testing")
	}

	if !tc.currentContainer.VerifyLinterInstalled(linter) {
		return fmt.Errorf("linter %s is not installed in the container", linter)
	}
	return nil
}

func (tc *TestContext) linterIsNotInstalled(linter string) error {
	if tc.currentContainer == nil {
		return fmt.Errorf("no container available for testing")
	}

	if tc.currentContainer.VerifyLinterInstalled(linter) {
		return fmt.Errorf("linter %s should not be installed in the container", linter)
	}
	return nil
}

func (tc *TestContext) lintairIsCalledWithFilenames(filePattern string) error {
	if tc.currentContainer == nil {
		return fmt.Errorf("no container available for testing")
	}

	// Filter test files based on pattern
	patternMap := map[string]string{
		"Python":     `\.py$`,
		"JavaScript": `\.(js|jsx)$`,
		"TypeScript": `\.(ts|tsx)$`,
		"Go":         `\.go$`,
		"JSON":       `\.json$`,
		"CSS":        `\.(css|scss)$`,
		"HTML":       `\.html$`,
	}

	var matchingFiles []string
	if regexPattern, exists := patternMap[filePattern]; exists {
		regex := regexp.MustCompile(regexPattern)
		for _, file := range tc.testFiles {
			if regex.MatchString(file) {
				matchingFiles = append(matchingFiles, file)
			}
		}
	} else {
		// Assume it's a literal pattern
		for _, file := range tc.testFiles {
			if strings.Contains(file, filePattern) {
				matchingFiles = append(matchingFiles, file)
			}
		}
	}

	if len(matchingFiles) == 0 {
		return fmt.Errorf("no files found matching pattern: %s", filePattern)
	}

	// Run lintair with matching files
	filesStr := strings.Join(matchingFiles, " ")
	cmd := fmt.Sprintf("/app/lintair %s", filesStr)

	result, err := tc.currentContainer.ExecuteCommand(cmd)
	if err != nil {
		return fmt.Errorf("failed to execute lintair: %w", err)
	}
	
	tc.commandResult = result
	return nil
}

func (tc *TestContext) lintairIsCalledWithTheFiles() error {
	if tc.currentContainer == nil {
		return fmt.Errorf("no container available for testing")
	}

	if len(tc.testFiles) == 0 {
		return fmt.Errorf("no test files available")
	}

	// Run lintair with all test files
	filesStr := strings.Join(tc.testFiles, " ")
	cmd := fmt.Sprintf("/app/lintair %s", filesStr)

	result, err := tc.currentContainer.ExecuteCommand(cmd)
	if err != nil {
		return fmt.Errorf("failed to execute lintair: %w", err)
	}
	
	tc.commandResult = result
	return nil
}

func (tc *TestContext) lintairIsCalledWithNoArguments() error {
	if tc.currentContainer == nil {
		if err := tc.SetupContainer("minimal"); err != nil {
			return err
		}
	}

	cmd := "/app/lintair"
	result, err := tc.currentContainer.ExecuteCommand(cmd)
	if err != nil {
		return fmt.Errorf("failed to execute lintair: %w", err)
	}
	
	tc.commandResult = result
	return nil
}

func (tc *TestContext) lintairIsCalledWithFilesThatDontExist() error {
	if tc.currentContainer == nil {
		if err := tc.SetupContainer("minimal"); err != nil {
			return err
		}
	}

	// Use non-existent file names
	cmd := "/app/lintair nonexistent1.py nonexistent2.js"
	result, err := tc.currentContainer.ExecuteCommand(cmd)
	if err != nil {
		return fmt.Errorf("failed to execute lintair: %w", err)
	}
	
	tc.commandResult = result
	return nil
}

func (tc *TestContext) theExitCodeShouldBe(expectedCode int) error {
	if tc.commandResult == nil {
		return fmt.Errorf("no command result available")
	}

	if tc.commandResult.ExitCode != expectedCode {
		combinedOutput := tc.commandResult.Stdout + tc.commandResult.Stderr
		return fmt.Errorf("expected exit code %d, but got %d.\nCommand: %s\nOutput: %s",
			expectedCode, tc.commandResult.ExitCode, tc.commandResult.Command, combinedOutput)
	}
	return nil
}

func (tc *TestContext) theOutputShouldContain(expectedText string) error {
	if tc.commandResult == nil {
		return fmt.Errorf("no command result available")
	}

	combinedOutput := tc.commandResult.Stdout + tc.commandResult.Stderr
	if !strings.Contains(combinedOutput, expectedText) {
		return fmt.Errorf("expected output to contain '%s', but it didn't.\nActual output: %s",
			expectedText, combinedOutput)
	}
	return nil
}

func (tc *TestContext) theOutputShouldNotContain(unexpectedText string) error {
	if tc.commandResult == nil {
		return fmt.Errorf("no command result available")
	}

	combinedOutput := tc.commandResult.Stdout + tc.commandResult.Stderr
	if strings.Contains(combinedOutput, unexpectedText) {
		return fmt.Errorf("expected output to NOT contain '%s', but it did.\nActual output: %s",
			unexpectedText, combinedOutput)
	}
	return nil
}

func (tc *TestContext) theOutputShouldMatchThePattern(pattern string) error {
	if tc.commandResult == nil {
		return fmt.Errorf("no command result available")
	}

	combinedOutput := tc.commandResult.Stdout + tc.commandResult.Stderr
	matched, err := regexp.MatchString(pattern, combinedOutput)
	if err != nil {
		return fmt.Errorf("invalid regex pattern '%s': %w", pattern, err)
	}
	
	if !matched {
		return fmt.Errorf("expected output to match pattern '%s', but it didn't.\nActual output: %s",
			pattern, combinedOutput)
	}
	return nil
}

func (tc *TestContext) theLinterCommandShouldBeExecuted(linter string) error {
	if tc.commandResult == nil {
		return fmt.Errorf("no command result available")
	}

	combinedOutput := tc.commandResult.Stdout + tc.commandResult.Stderr
	if !strings.Contains(combinedOutput, fmt.Sprintf("Running: %s", linter)) {
		return fmt.Errorf("expected %s to be executed, but it wasn't found in output.\nActual output: %s",
			linter, combinedOutput)
	}
	return nil
}

func (tc *TestContext) theLinterCommandShouldNotBeExecuted(linter string) error {
	if tc.commandResult == nil {
		return fmt.Errorf("no command result available")
	}

	combinedOutput := tc.commandResult.Stdout + tc.commandResult.Stderr
	if strings.Contains(combinedOutput, fmt.Sprintf("Running: %s", linter)) {
		return fmt.Errorf("expected %s to NOT be executed, but it was found in output.\nActual output: %s",
			linter, combinedOutput)
	}
	return nil
}

func (tc *TestContext) thoseFilesGetLinted() error {
	if tc.commandResult == nil {
		return fmt.Errorf("no command result available")
	}

	combinedOutput := tc.commandResult.Stdout + tc.commandResult.Stderr
	
	// Should see "Running:" in output indicating linters were executed
	if !strings.Contains(combinedOutput, "Running:") {
		return fmt.Errorf("expected files to be linted, but no linter execution found.\nActual output: %s",
			combinedOutput)
	}
	return nil
}

func (tc *TestContext) thoseFilesGetFormatted() error {
	return tc.thoseFilesGetLinted() // Same logic for now
}

func (tc *TestContext) aWarningShouldBeShownForUnsupportedFiles() error {
	if tc.commandResult == nil {
		return fmt.Errorf("no command result available")
	}

	combinedOutput := tc.commandResult.Stdout + tc.commandResult.Stderr
	
	if !strings.Contains(combinedOutput, "Warning: No linter configured") {
		return fmt.Errorf("expected warning for unsupported files, but none found.\nActual output: %s",
			combinedOutput)
	}
	return nil
}

// InitializeScenario initializes the test context for each scenario
func (tc *TestContext) InitializeScenario(ctx *godog.ScenarioContext) {
	// File creation steps
	ctx.Step(`^the following Python file exists:$`, tc.theFollowingPythonFileExists)
	ctx.Step(`^the following JavaScript file exists:$`, tc.theFollowingJavaScriptFileExists)
	ctx.Step(`^the following Go file exists:$`, tc.theFollowingGoFileExists)

	// Linter verification steps
	ctx.Step(`^([a-zA-Z0-9_-]+) is installed$`, tc.linterIsInstalled)
	ctx.Step(`^([a-zA-Z0-9_-]+) is not installed$`, tc.linterIsNotInstalled)

	// CLI execution steps
	ctx.Step(`^lintair is called with ([a-zA-Z]+) filenames$`, tc.lintairIsCalledWithFilenames)
	ctx.Step(`^lintair is called with the files$`, tc.lintairIsCalledWithTheFiles)
	ctx.Step(`^lintair is called with no arguments$`, tc.lintairIsCalledWithNoArguments)
	ctx.Step(`^lintair is called with files that don't exist$`, tc.lintairIsCalledWithFilesThatDontExist)

	// Assertion steps
	ctx.Step(`^the exit code should be (\d+)$`, func(codeStr string) error {
		code, err := strconv.Atoi(codeStr)
		if err != nil {
			return fmt.Errorf("invalid exit code: %s", codeStr)
		}
		return tc.theExitCodeShouldBe(code)
	})
	ctx.Step(`^the output should contain "([^"]*)"$`, tc.theOutputShouldContain)
	ctx.Step(`^the output should not contain "([^"]*)"$`, tc.theOutputShouldNotContain)
	ctx.Step(`^the output should match the pattern "([^"]*)"$`, tc.theOutputShouldMatchThePattern)
	ctx.Step(`^the ([a-zA-Z0-9_-]+) command should be executed$`, tc.theLinterCommandShouldBeExecuted)
	ctx.Step(`^the ([a-zA-Z0-9_-]+) command should not be executed$`, tc.theLinterCommandShouldNotBeExecuted)
	ctx.Step(`^those files get linted$`, tc.thoseFilesGetLinted)
	ctx.Step(`^those files get formatted$`, tc.thoseFilesGetFormatted)
	ctx.Step(`^a warning should be shown for unsupported files$`, tc.aWarningShouldBeShownForUnsupportedFiles)

	// Clean up after each scenario
	ctx.After(func(ctx context.Context, sc *godog.Scenario, err error) (context.Context, error) {
		if tc.currentContainer != nil {
			tc.currentContainer.StopContainer()
			tc.currentContainer = nil
		}
		tc.testFiles = tc.testFiles[:0] // Clear slice
		tc.commandResult = nil
		return ctx, nil
	})
}