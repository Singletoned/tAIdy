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

// TestContainerTestContext holds the state for BDD tests using testcontainers
type TestContainerTestContext struct {
	containerManager *TestContainerManager
	currentContainer *TestContainerContext
	testFiles        []string
	commandResult    *CommandResult
	scenarioName     string
}

// NewTestContainerTestContext creates a new test context using testcontainers
func NewTestContainerTestContext() *TestContainerTestContext {
	tcm, err := NewTestContainerManager()
	if err != nil {
		log.Fatalf("Failed to create TestContainer manager: %v", err)
	}

	return &TestContainerTestContext{
		containerManager: tcm,
		testFiles:        make([]string, 0),
	}
}

// Close cleans up the test context
func (tctx *TestContainerTestContext) Close() error {
	if tctx.currentContainer != nil {
		tctx.currentContainer.StopContainer()
	}
	return tctx.containerManager.Close()
}

// SetupContainer sets up a container for the given environment using testcontainers
func (tctx *TestContainerTestContext) SetupContainer(environment string) error {
	container, err := NewTestContainerContext(environment, tctx.containerManager)
	if err != nil {
		return fmt.Errorf("failed to create testcontainer for environment %s: %w", environment, err)
	}

	container.SetScenarioName(tctx.scenarioName)
	tctx.currentContainer = container
	return nil
}

// Step Definitions (using testcontainers)

func (tctx *TestContainerTestContext) theFollowingPythonFileExists(docString *godog.DocString) error {
	if tctx.currentContainer == nil {
		if err := tctx.SetupContainer("python311"); err != nil {
			return err
		}
	}

	content := ""
	if docString != nil {
		content = docString.Content
	}

	filename := fmt.Sprintf("test_%d.py", len(tctx.testFiles)+1)
	if err := tctx.currentContainer.CreateFile(filename, content); err != nil {
		return fmt.Errorf("failed to create Python file: %w", err)
	}

	tctx.testFiles = append(tctx.testFiles, filename)
	return nil
}

func (tctx *TestContainerTestContext) thePythonFileExists(filename string) error {
	// Store the filename for later - don't set up container yet
	// This allows subsequent steps to determine the correct environment
	tctx.testFiles = append(tctx.testFiles, filename)
	return nil
}

func (tctx *TestContainerTestContext) theFollowingJavaScriptFileExists(docString *godog.DocString) error {
	if tctx.currentContainer == nil {
		if err := tctx.SetupContainer("node18"); err != nil {
			return err
		}
	}

	content := ""
	if docString != nil {
		content = docString.Content
	}

	filename := fmt.Sprintf("test_%d.js", len(tctx.testFiles)+1)
	if err := tctx.currentContainer.CreateFile(filename, content); err != nil {
		return fmt.Errorf("failed to create JavaScript file: %w", err)
	}

	tctx.testFiles = append(tctx.testFiles, filename)
	return nil
}

func (tctx *TestContainerTestContext) theFollowingGoFileExists(docString *godog.DocString) error {
	if tctx.currentContainer == nil {
		if err := tctx.SetupContainer("go121"); err != nil {
			return err
		}
	}

	content := ""
	if docString != nil {
		content = docString.Content
	}

	filename := fmt.Sprintf("test_%d.go", len(tctx.testFiles)+1)
	if err := tctx.currentContainer.CreateFile(filename, content); err != nil {
		return fmt.Errorf("failed to create Go file: %w", err)
	}

	tctx.testFiles = append(tctx.testFiles, filename)
	return nil
}

func (tctx *TestContainerTestContext) linterIsInstalled(linter string) error {
	// Set up appropriate container based on linter
	if tctx.currentContainer == nil {
		var environment string
		switch linter {
		case "ruff":
			environment = "python311"
		case "prettier":
			environment = "node18"
		case "gofmt":
			environment = "go121"
		default:
			environment = "minimal"
		}

		if err := tctx.SetupContainer(environment); err != nil {
			return err
		}

		// Copy any test files that were registered earlier
		for _, filename := range tctx.testFiles {
			if strings.HasSuffix(filename, ".py") && linter == "ruff" {
				sourceFile := fmt.Sprintf("sample_files/%s", filename)
				if err := tctx.currentContainer.CopyFileIntoContainer(sourceFile, filename); err != nil {
					return fmt.Errorf("failed to copy Python file %s: %w", filename, err)
				}
			}
		}
	}

	if !tctx.currentContainer.VerifyLinterInstalled(linter) {
		return fmt.Errorf("linter %s is not installed in the container", linter)
	}
	return nil
}

func (tctx *TestContainerTestContext) linterIsNotInstalled(linter string) error {
	// Set up appropriate container that doesn't have the linter
	if tctx.currentContainer == nil {
		var environment string
		switch linter {
		case "ruff":
			environment = "python311-uv" // Use environment with uv but not ruff
		default:
			environment = "minimal"
		}

		if err := tctx.SetupContainer(environment); err != nil {
			return err
		}

		// Copy any test files that were registered earlier
		for _, filename := range tctx.testFiles {
			if strings.HasSuffix(filename, ".py") {
				sourceFile := fmt.Sprintf("sample_files/%s", filename)
				if err := tctx.currentContainer.CopyFileIntoContainer(sourceFile, filename); err != nil {
					return fmt.Errorf("failed to copy Python file %s: %w", filename, err)
				}
			}
		}
	}

	if tctx.currentContainer.VerifyLinterInstalled(linter) {
		return fmt.Errorf("linter %s should not be installed in the container", linter)
	}
	return nil
}

func (tctx *TestContainerTestContext) lintairIsCalledWithFilenames(filePattern string) error {
	if tctx.currentContainer == nil {
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
		for _, file := range tctx.testFiles {
			if regex.MatchString(file) {
				matchingFiles = append(matchingFiles, file)
			}
		}
	} else {
		// Assume it's a literal pattern
		for _, file := range tctx.testFiles {
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

	result, err := tctx.currentContainer.ExecuteCommand(cmd)
	if err != nil {
		return fmt.Errorf("failed to execute lintair: %w", err)
	}

	tctx.commandResult = result
	return nil
}

func (tctx *TestContainerTestContext) lintairIsCalledWithTheFiles() error {
	if tctx.currentContainer == nil {
		return fmt.Errorf("no container available for testing")
	}

	if len(tctx.testFiles) == 0 {
		return fmt.Errorf("no test files available")
	}

	// Run lintair with all test files
	filesStr := strings.Join(tctx.testFiles, " ")
	cmd := fmt.Sprintf("/app/lintair %s", filesStr)

	result, err := tctx.currentContainer.ExecuteCommand(cmd)
	if err != nil {
		return fmt.Errorf("failed to execute lintair: %w", err)
	}

	tctx.commandResult = result
	return nil
}

func (tctx *TestContainerTestContext) lintairIsCalledWithNoArguments() error {
	if tctx.currentContainer == nil {
		if err := tctx.SetupContainer("minimal"); err != nil {
			return err
		}
	}

	cmd := "/app/lintair"
	result, err := tctx.currentContainer.ExecuteCommand(cmd)
	if err != nil {
		return fmt.Errorf("failed to execute lintair: %w", err)
	}

	tctx.commandResult = result
	return nil
}

func (tctx *TestContainerTestContext) lintairIsCalledWithFilesThatDontExist() error {
	if tctx.currentContainer == nil {
		if err := tctx.SetupContainer("minimal"); err != nil {
			return err
		}
	}

	// Use non-existent file names
	cmd := "/app/lintair nonexistent1.py nonexistent2.js"
	result, err := tctx.currentContainer.ExecuteCommand(cmd)
	if err != nil {
		return fmt.Errorf("failed to execute lintair: %w", err)
	}

	tctx.commandResult = result
	return nil
}

func (tctx *TestContainerTestContext) theExitCodeShouldBe(expectedCode int) error {
	if tctx.commandResult == nil {
		return fmt.Errorf("no command result available")
	}

	if tctx.commandResult.ExitCode != expectedCode {
		combinedOutput := tctx.commandResult.Stdout + tctx.commandResult.Stderr
		return fmt.Errorf("expected exit code %d, but got %d.\nCommand: %s\nOutput: %s",
			expectedCode, tctx.commandResult.ExitCode, tctx.commandResult.Command, combinedOutput)
	}
	return nil
}

func (tctx *TestContainerTestContext) theOutputShouldContain(expectedText string) error {
	if tctx.commandResult == nil {
		return fmt.Errorf("no command result available")
	}

	combinedOutput := tctx.commandResult.Stdout + tctx.commandResult.Stderr
	if !strings.Contains(combinedOutput, expectedText) {
		return fmt.Errorf("expected output to contain '%s', but it didn't.\nActual output: %s",
			expectedText, combinedOutput)
	}
	return nil
}

func (tctx *TestContainerTestContext) theOutputShouldNotContain(unexpectedText string) error {
	if tctx.commandResult == nil {
		return fmt.Errorf("no command result available")
	}

	combinedOutput := tctx.commandResult.Stdout + tctx.commandResult.Stderr
	if strings.Contains(combinedOutput, unexpectedText) {
		return fmt.Errorf("expected output to NOT contain '%s', but it did.\nActual output: %s",
			unexpectedText, combinedOutput)
	}
	return nil
}

func (tctx *TestContainerTestContext) theOutputShouldMatchThePattern(pattern string) error {
	if tctx.commandResult == nil {
		return fmt.Errorf("no command result available")
	}

	combinedOutput := tctx.commandResult.Stdout + tctx.commandResult.Stderr
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

func (tctx *TestContainerTestContext) theLinterCommandShouldBeExecuted(linter string) error {
	if tctx.commandResult == nil {
		return fmt.Errorf("no command result available")
	}

	combinedOutput := tctx.commandResult.Stdout + tctx.commandResult.Stderr
	if !strings.Contains(combinedOutput, fmt.Sprintf("Running: %s", linter)) {
		return fmt.Errorf("expected %s to be executed, but it wasn't found in output.\nActual output: %s",
			linter, combinedOutput)
	}
	return nil
}

func (tctx *TestContainerTestContext) theLinterCommandShouldNotBeExecuted(linter string) error {
	if tctx.commandResult == nil {
		return fmt.Errorf("no command result available")
	}

	combinedOutput := tctx.commandResult.Stdout + tctx.commandResult.Stderr
	if strings.Contains(combinedOutput, fmt.Sprintf("Running: %s", linter)) {
		return fmt.Errorf("expected %s to NOT be executed, but it was found in output.\nActual output: %s",
			linter, combinedOutput)
	}
	return nil
}

func (tctx *TestContainerTestContext) thoseFilesGetLinted() error {
	if tctx.commandResult == nil {
		return fmt.Errorf("no command result available")
	}

	combinedOutput := tctx.commandResult.Stdout + tctx.commandResult.Stderr

	// Should see "Running:" in output indicating linters were executed
	if !strings.Contains(combinedOutput, "Running:") {
		return fmt.Errorf("expected files to be linted, but no linter execution found.\nActual output: %s",
			combinedOutput)
	}
	return nil
}

func (tctx *TestContainerTestContext) thoseFilesGetFormatted() error {
	return tctx.thoseFilesGetLinted() // Same logic for now
}

func (tctx *TestContainerTestContext) aWarningShouldBeShownForUnsupportedFiles() error {
	if tctx.commandResult == nil {
		return fmt.Errorf("no command result available")
	}

	combinedOutput := tctx.commandResult.Stdout + tctx.commandResult.Stderr

	if !strings.Contains(combinedOutput, "Warning: No linter configured") {
		return fmt.Errorf("expected warning for unsupported files, but none found.\nActual output: %s",
			combinedOutput)
	}
	return nil
}

// InitializeScenario initializes the test context for each scenario using testcontainers
func (tctx *TestContainerTestContext) InitializeScenario(ctx *godog.ScenarioContext) {
	// File creation steps
	ctx.Step(`^the following Python file exists:$`, tctx.theFollowingPythonFileExists)
	ctx.Step(`^the Python file "([^"]*)" exists$`, tctx.thePythonFileExists)
	ctx.Step(`^the following JavaScript file exists:$`, tctx.theFollowingJavaScriptFileExists)
	ctx.Step(`^the following Go file exists:$`, tctx.theFollowingGoFileExists)

	// Linter verification steps
	ctx.Step(`^([a-zA-Z0-9_-]+) is installed$`, tctx.linterIsInstalled)
	ctx.Step(`^([a-zA-Z0-9_-]+) is not installed$`, tctx.linterIsNotInstalled)
	ctx.Step(`^([a-zA-Z0-9_-]+) isn't installed$`, tctx.linterIsNotInstalled)

	// CLI execution steps
	ctx.Step(`^lintair is called with ([a-zA-Z]+) filenames$`, tctx.lintairIsCalledWithFilenames)
	ctx.Step(`^lintair is called with the files$`, tctx.lintairIsCalledWithTheFiles)
	ctx.Step(`^lintair is called with no arguments$`, tctx.lintairIsCalledWithNoArguments)
	ctx.Step(`^lintair is called with files that don't exist$`, tctx.lintairIsCalledWithFilesThatDontExist)

	// Assertion steps
	ctx.Step(`^the exit code should be (\d+)$`, func(codeStr string) error {
		code, err := strconv.Atoi(codeStr)
		if err != nil {
			return fmt.Errorf("invalid exit code: %s", codeStr)
		}
		return tctx.theExitCodeShouldBe(code)
	})
	ctx.Step(`^the output should contain "([^"]*)"$`, tctx.theOutputShouldContain)
	ctx.Step(`^the output should not contain "([^"]*)"$`, tctx.theOutputShouldNotContain)
	ctx.Step(`^the output should match the pattern "([^"]*)"$`, tctx.theOutputShouldMatchThePattern)
	ctx.Step(`^the ([a-zA-Z0-9_-]+) command should be executed$`, tctx.theLinterCommandShouldBeExecuted)
	ctx.Step(`^the ([a-zA-Z0-9_-]+) command should not be executed$`, tctx.theLinterCommandShouldNotBeExecuted)
	ctx.Step(`^those files get linted$`, tctx.thoseFilesGetLinted)
	ctx.Step(`^those files get formatted$`, tctx.thoseFilesGetFormatted)
	ctx.Step(`^a warning should be shown for unsupported files$`, tctx.aWarningShouldBeShownForUnsupportedFiles)

	// Set scenario name and clean up after each scenario
	ctx.Before(func(ctx context.Context, sc *godog.Scenario) (context.Context, error) {
		tctx.scenarioName = sc.Name
		return ctx, nil
	})

	ctx.After(func(ctx context.Context, sc *godog.Scenario, err error) (context.Context, error) {
		if tctx.currentContainer != nil {
			tctx.currentContainer.StopContainer()
			tctx.currentContainer = nil
		}
		tctx.testFiles = tctx.testFiles[:0] // Clear slice
		tctx.commandResult = nil
		return ctx, nil
	})
}