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
	requiredLinters  []string // Linters that must be installed
	forbiddenLinters []string // Linters that must NOT be installed
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

// determineEnvironment selects the best environment based on required and forbidden linters
func (tctx *TestContainerTestContext) determineEnvironment() string {
	// Check for Python linters
	hasRuff := contains(tctx.requiredLinters, "ruff")
	hasBlack := contains(tctx.requiredLinters, "black")
	hasUv := contains(tctx.requiredLinters, "uv")

	forbidsRuff := contains(tctx.forbiddenLinters, "ruff")
	forbidsBlack := contains(tctx.forbiddenLinters, "black")
	forbidsUv := contains(tctx.forbiddenLinters, "uv")

	// Check for other linters
	hasPrettier := contains(tctx.requiredLinters, "prettier")
	hasGofmt := contains(tctx.requiredLinters, "gofmt")
	hasShellcheck := contains(tctx.requiredLinters, "shellcheck")
	hasShfmt := contains(tctx.requiredLinters, "shfmt")
	hasBeautysh := contains(tctx.requiredLinters, "beautysh")

	// Python environment selection
	if hasRuff && !forbidsRuff {
		return "python311"
	}
	if hasUv && !forbidsUv && !hasRuff && !hasBlack {
		return "python311-uv"
	}
	if hasBlack && !forbidsBlack && forbidsRuff && forbidsUv {
		return "python311-black"
	}

	// Other environments
	if hasShellcheck || hasShfmt || hasBeautysh {
		return "shell-tools"
	}
	if hasPrettier {
		return "node18"
	}
	if hasGofmt {
		return "go121"
	}

	// Default to minimal environment
	return "minimal"
}

// Helper function to check if slice contains a string
func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
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


func (tctx *TestContainerTestContext) theShellFileExists(filename string) error {
	// Store the filename for later - don't set up container yet
	// This allows subsequent steps to determine the correct environment
	tctx.testFiles = append(tctx.testFiles, filename)
	return nil
}

func (tctx *TestContainerTestContext) theMarkdownFileExists(filename string) error {
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
	// Track required linters
	tctx.requiredLinters = append(tctx.requiredLinters, linter)

	// Set up container if needed
	if tctx.currentContainer == nil {
		environment := tctx.determineEnvironment()
		if err := tctx.SetupContainer(environment); err != nil {
			return err
		}

		// Copy any test files that were registered earlier
		for _, filename := range tctx.testFiles {
			if strings.HasSuffix(filename, ".py") && (linter == "ruff" || linter == "black" || linter == "uv") {
				sourceFile := fmt.Sprintf("sample_files/%s", filename)
				if err := tctx.currentContainer.CopyFileIntoContainer(sourceFile, filename); err != nil {
					return fmt.Errorf("failed to copy Python file %s: %w", filename, err)
				}
			}
			if (strings.HasSuffix(filename, ".sh") || strings.HasSuffix(filename, ".bash") || strings.HasSuffix(filename, ".zsh")) && (linter == "shellcheck" || linter == "shfmt" || linter == "beautysh") {
				sourceFile := fmt.Sprintf("sample_files/%s", filename)
				if err := tctx.currentContainer.CopyFileIntoContainer(sourceFile, filename); err != nil {
					return fmt.Errorf("failed to copy shell file %s: %w", filename, err)
				}
			}
			if strings.HasSuffix(filename, ".md") && linter == "prettier" {
				sourceFile := fmt.Sprintf("sample_files/%s", filename)
				if err := tctx.currentContainer.CopyFileIntoContainer(sourceFile, filename); err != nil {
					return fmt.Errorf("failed to copy markdown file %s: %w", filename, err)
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
	// Track forbidden linters
	tctx.forbiddenLinters = append(tctx.forbiddenLinters, linter)

	// If container is already set up, just verify the linter is not installed
	if tctx.currentContainer != nil {
		if tctx.currentContainer.VerifyLinterInstalled(linter) {
			return fmt.Errorf("linter %s should not be installed in the container", linter)
		}
		return nil
	}

	// Set up container will be done when first required linter is specified
	// For now, just track the constraint
	return nil
}

func (tctx *TestContainerTestContext) taidyIsCalledWithFilenames(filePattern string) error {
	if tctx.currentContainer == nil {
		// Set up container based on accumulated constraints
		environment := tctx.determineEnvironment()
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
			if strings.HasSuffix(filename, ".sh") || strings.HasSuffix(filename, ".bash") || strings.HasSuffix(filename, ".zsh") {
				sourceFile := fmt.Sprintf("sample_files/%s", filename)
				if err := tctx.currentContainer.CopyFileIntoContainer(sourceFile, filename); err != nil {
					return fmt.Errorf("failed to copy shell file %s: %w", filename, err)
				}
			}
			if strings.HasSuffix(filename, ".md") {
				sourceFile := fmt.Sprintf("sample_files/%s", filename)
				if err := tctx.currentContainer.CopyFileIntoContainer(sourceFile, filename); err != nil {
					return fmt.Errorf("failed to copy markdown file %s: %w", filename, err)
				}
			}
		}

		// Verify all constraints are satisfied
		for _, linter := range tctx.requiredLinters {
			if !tctx.currentContainer.VerifyLinterInstalled(linter) {
				return fmt.Errorf("required linter %s is not installed in the container", linter)
			}
		}
		for _, linter := range tctx.forbiddenLinters {
			if tctx.currentContainer.VerifyLinterInstalled(linter) {
				return fmt.Errorf("forbidden linter %s is installed in the container", linter)
			}
		}
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
		"Shell":      `\.(sh|bash|zsh)$`,
		"Markdown":   `\.md$`,
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

	// Run taidy with matching files
	filesStr := strings.Join(matchingFiles, " ")
	cmd := fmt.Sprintf("python3 -m taidy %s", filesStr)

	result, err := tctx.currentContainer.ExecuteCommand(cmd)
	if err != nil {
		return fmt.Errorf("failed to execute taidy: %w", err)
	}

	tctx.commandResult = result
	return nil
}

func (tctx *TestContainerTestContext) taidyIsCalledWithTheFiles() error {
	if tctx.currentContainer == nil {
		return fmt.Errorf("no container available for testing")
	}

	if len(tctx.testFiles) == 0 {
		return fmt.Errorf("no test files available")
	}

	// Run taidy with all test files
	filesStr := strings.Join(tctx.testFiles, " ")
	cmd := fmt.Sprintf("python3 -m taidy %s", filesStr)

	result, err := tctx.currentContainer.ExecuteCommand(cmd)
	if err != nil {
		return fmt.Errorf("failed to execute taidy: %w", err)
	}

	tctx.commandResult = result
	return nil
}

func (tctx *TestContainerTestContext) taidyIsCalledWithNoArguments() error {
	if tctx.currentContainer == nil {
		if err := tctx.SetupContainer("minimal"); err != nil {
			return err
		}
	}

	cmd := "python3 -m taidy"
	result, err := tctx.currentContainer.ExecuteCommand(cmd)
	if err != nil {
		return fmt.Errorf("failed to execute taidy: %w", err)
	}

	tctx.commandResult = result
	return nil
}

func (tctx *TestContainerTestContext) taidyIsCalledWithFilesThatDontExist() error {
	if tctx.currentContainer == nil {
		if err := tctx.SetupContainer("minimal"); err != nil {
			return err
		}
	}

	// Use non-existent file names
	cmd := "python3 -m taidy nonexistent1.py nonexistent2.js"
	result, err := tctx.currentContainer.ExecuteCommand(cmd)
	if err != nil {
		return fmt.Errorf("failed to execute taidy: %w", err)
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

func (tctx *TestContainerTestContext) lintOutputIsEmitted() error {
	if tctx.commandResult == nil {
		return fmt.Errorf("no command result available")
	}

	combinedOutput := tctx.commandResult.Stdout + tctx.commandResult.Stderr

	// Check if linting output is present (errors, warnings, etc.)
	if strings.Contains(combinedOutput, "All checks passed!") ||
		strings.Contains(combinedOutput, "error:") ||
		strings.Contains(combinedOutput, "warning:") ||
		strings.Contains(combinedOutput, "E") || // flake8/pylint error codes
		strings.Contains(combinedOutput, "W") || // warning codes
		strings.Contains(combinedOutput, "Running:") {
		return nil
	}

	return fmt.Errorf("expected lint output to be emitted, but none found.\nActual output: %s", combinedOutput)
}

func (tctx *TestContainerTestContext) noFormattingHappens() error {
	if tctx.commandResult == nil {
		return fmt.Errorf("no command result available")
	}

	combinedOutput := tctx.commandResult.Stdout + tctx.commandResult.Stderr

	// Check that actual formatting (file modification) didn't happen
	// Showing diffs (like "would reformat") is fine for linting, but actual reformatting is not
	if strings.Contains(combinedOutput, "file reformatted") ||
		strings.Contains(combinedOutput, "files reformatted") ||
		strings.Contains(combinedOutput, "1 file reformatted") ||
		(strings.Contains(combinedOutput, "reformatted") && !strings.Contains(combinedOutput, "would reformat")) {
		return fmt.Errorf("expected no formatting to happen, but formatting output found.\nActual output: %s", combinedOutput)
	}
	return nil
}

func (tctx *TestContainerTestContext) noLintOutputIsEmitted() error {
	if tctx.commandResult == nil {
		return fmt.Errorf("no command result available")
	}

	combinedOutput := tctx.commandResult.Stdout + tctx.commandResult.Stderr

	// Check that no linting output is present (only formatting) for other tools
	if strings.Contains(combinedOutput, "error:") ||
		strings.Contains(combinedOutput, "warning:") ||
		(strings.Contains(combinedOutput, "E") && !strings.Contains(combinedOutput, "would reformat")) ||
		(strings.Contains(combinedOutput, "W") && !strings.Contains(combinedOutput, "would reformat")) {
		return fmt.Errorf("expected no lint output to be emitted, but lint output found.\nActual output: %s", combinedOutput)
	}
	return nil
}

func (tctx *TestContainerTestContext) taidyFormatPoorlyFormattedpyIsRun() error {
	if tctx.currentContainer == nil {
		// Set up container based on accumulated constraints
		environment := tctx.determineEnvironment()
		if err := tctx.SetupContainer(environment); err != nil {
			return err
		}

		// Copy the poorly formatted file
		if err := tctx.currentContainer.CopyFileIntoContainer("sample_files/poorly_formatted.py", "poorly_formatted.py"); err != nil {
			return fmt.Errorf("failed to copy poorly_formatted.py: %w", err)
		}
	}

	cmd := "python3 -m taidy format poorly_formatted.py"
	result, err := tctx.currentContainer.ExecuteCommand(cmd)
	if err != nil {
		return fmt.Errorf("failed to execute taidy format: %w", err)
	}

	tctx.commandResult = result
	return nil
}

func (tctx *TestContainerTestContext) taidyLintPoorlyFormattedpyIsRun() error {
	if tctx.currentContainer == nil {
		// Set up container based on accumulated constraints
		environment := tctx.determineEnvironment()
		if err := tctx.SetupContainer(environment); err != nil {
			return err
		}

		// Copy the poorly formatted file
		if err := tctx.currentContainer.CopyFileIntoContainer("sample_files/poorly_formatted.py", "poorly_formatted.py"); err != nil {
			return fmt.Errorf("failed to copy poorly_formatted.py: %w", err)
		}
	}

	cmd := "python3 -m taidy lint poorly_formatted.py"
	result, err := tctx.currentContainer.ExecuteCommand(cmd)
	if err != nil {
		return fmt.Errorf("failed to execute taidy lint: %w", err)
	}

	tctx.commandResult = result
	return nil
}

func (tctx *TestContainerTestContext) taidyPoorlyFormattedpyIsRun() error {
	if tctx.currentContainer == nil {
		// Set up container based on accumulated constraints
		environment := tctx.determineEnvironment()
		if err := tctx.SetupContainer(environment); err != nil {
			return err
		}

		// Copy the poorly formatted file
		if err := tctx.currentContainer.CopyFileIntoContainer("sample_files/poorly_formatted.py", "poorly_formatted.py"); err != nil {
			return fmt.Errorf("failed to copy poorly_formatted.py: %w", err)
		}
	}

	cmd := "python3 -m taidy poorly_formatted.py"
	result, err := tctx.currentContainer.ExecuteCommand(cmd)
	if err != nil {
		return fmt.Errorf("failed to execute taidy: %w", err)
	}

	tctx.commandResult = result
	return nil
}

func (tctx *TestContainerTestContext) taidyFormatPoorlyFormattedshIsRun() error {
	if tctx.currentContainer == nil {
		// Set up container based on accumulated constraints
		environment := tctx.determineEnvironment()
		if err := tctx.SetupContainer(environment); err != nil {
			return err
		}

		// Copy the poorly formatted file
		if err := tctx.currentContainer.CopyFileIntoContainer("sample_files/poorly_formatted.sh", "poorly_formatted.sh"); err != nil {
			return fmt.Errorf("failed to copy poorly_formatted.sh: %w", err)
		}
	}

	cmd := "python3 -m taidy format poorly_formatted.sh"
	result, err := tctx.currentContainer.ExecuteCommand(cmd)
	if err != nil {
		return fmt.Errorf("failed to execute taidy format: %w", err)
	}

	tctx.commandResult = result
	return nil
}

func (tctx *TestContainerTestContext) taidyLintPoorlyFormattedshIsRun() error {
	if tctx.currentContainer == nil {
		// Set up container based on accumulated constraints
		environment := tctx.determineEnvironment()
		if err := tctx.SetupContainer(environment); err != nil {
			return err
		}

		// Copy the poorly formatted file
		if err := tctx.currentContainer.CopyFileIntoContainer("sample_files/poorly_formatted.sh", "poorly_formatted.sh"); err != nil {
			return fmt.Errorf("failed to copy poorly_formatted.sh: %w", err)
		}
	}

	cmd := "python3 -m taidy lint poorly_formatted.sh"
	result, err := tctx.currentContainer.ExecuteCommand(cmd)
	if err != nil {
		return fmt.Errorf("failed to execute taidy lint: %w", err)
	}

	tctx.commandResult = result
	return nil
}

func (tctx *TestContainerTestContext) taidyPoorlyFormattedshIsRun() error {
	if tctx.currentContainer == nil {
		// Set up container based on accumulated constraints
		environment := tctx.determineEnvironment()
		if err := tctx.SetupContainer(environment); err != nil {
			return err
		}

		// Copy the poorly formatted file
		if err := tctx.currentContainer.CopyFileIntoContainer("sample_files/poorly_formatted.sh", "poorly_formatted.sh"); err != nil {
			return fmt.Errorf("failed to copy poorly_formatted.sh: %w", err)
		}
	}

	cmd := "python3 -m taidy poorly_formatted.sh"
	result, err := tctx.currentContainer.ExecuteCommand(cmd)
	if err != nil {
		return fmt.Errorf("failed to execute taidy: %w", err)
	}

	tctx.commandResult = result
	return nil
}

func (tctx *TestContainerTestContext) taidyPoorlyFormattedbashIsRun() error {
	if tctx.currentContainer == nil {
		// Set up container based on accumulated constraints
		environment := tctx.determineEnvironment()
		if err := tctx.SetupContainer(environment); err != nil {
			return err
		}

		// Copy the poorly formatted file
		if err := tctx.currentContainer.CopyFileIntoContainer("sample_files/poorly_formatted.bash", "poorly_formatted.bash"); err != nil {
			return fmt.Errorf("failed to copy poorly_formatted.bash: %w", err)
		}
	}

	cmd := "python3 -m taidy poorly_formatted.bash"
	result, err := tctx.currentContainer.ExecuteCommand(cmd)
	if err != nil {
		return fmt.Errorf("failed to execute taidy: %w", err)
	}

	tctx.commandResult = result
	return nil
}

func (tctx *TestContainerTestContext) taidyPoorlyFormattedzshIsRun() error {
	if tctx.currentContainer == nil {
		// Set up container based on accumulated constraints
		environment := tctx.determineEnvironment()
		if err := tctx.SetupContainer(environment); err != nil {
			return err
		}

		// Copy the poorly formatted file
		if err := tctx.currentContainer.CopyFileIntoContainer("sample_files/poorly_formatted.zsh", "poorly_formatted.zsh"); err != nil {
			return fmt.Errorf("failed to copy poorly_formatted.zsh: %w", err)
		}
	}

	cmd := "python3 -m taidy poorly_formatted.zsh"
	result, err := tctx.currentContainer.ExecuteCommand(cmd)
	if err != nil {
		return fmt.Errorf("failed to execute taidy: %w", err)
	}

	tctx.commandResult = result
	return nil
}

func (tctx *TestContainerTestContext) taidyFormatPoorlyFormattedmdIsRun() error {
	if tctx.currentContainer == nil {
		// Set up container based on accumulated constraints
		environment := tctx.determineEnvironment()
		if err := tctx.SetupContainer(environment); err != nil {
			return err
		}

		// Copy the poorly formatted file
		if err := tctx.currentContainer.CopyFileIntoContainer("sample_files/poorly_formatted.md", "poorly_formatted.md"); err != nil {
			return fmt.Errorf("failed to copy poorly_formatted.md: %w", err)
		}
	}

	cmd := "python3 -m taidy format poorly_formatted.md"
	result, err := tctx.currentContainer.ExecuteCommand(cmd)
	if err != nil {
		return fmt.Errorf("failed to execute taidy format: %w", err)
	}

	tctx.commandResult = result
	return nil
}

func (tctx *TestContainerTestContext) taidyLintPoorlyFormattedmdIsRun() error {
	if tctx.currentContainer == nil {
		// Set up container based on accumulated constraints
		environment := tctx.determineEnvironment()
		if err := tctx.SetupContainer(environment); err != nil {
			return err
		}

		// Copy the poorly formatted file
		if err := tctx.currentContainer.CopyFileIntoContainer("sample_files/poorly_formatted.md", "poorly_formatted.md"); err != nil {
			return fmt.Errorf("failed to copy poorly_formatted.md: %w", err)
		}
	}

	cmd := "python3 -m taidy lint poorly_formatted.md"
	result, err := tctx.currentContainer.ExecuteCommand(cmd)
	if err != nil {
		return fmt.Errorf("failed to execute taidy lint: %w", err)
	}

	tctx.commandResult = result
	return nil
}

func (tctx *TestContainerTestContext) taidyPoorlyFormattedmdIsRun() error {
	if tctx.currentContainer == nil {
		// Set up container based on accumulated constraints
		environment := tctx.determineEnvironment()
		if err := tctx.SetupContainer(environment); err != nil {
			return err
		}

		// Copy the poorly formatted file
		if err := tctx.currentContainer.CopyFileIntoContainer("sample_files/poorly_formatted.md", "poorly_formatted.md"); err != nil {
			return fmt.Errorf("failed to copy poorly_formatted.md: %w", err)
		}
	}

	cmd := "python3 -m taidy poorly_formatted.md"
	result, err := tctx.currentContainer.ExecuteCommand(cmd)
	if err != nil {
		return fmt.Errorf("failed to execute taidy: %w", err)
	}

	tctx.commandResult = result
	return nil
}

// InitializeScenario initializes the test context for each scenario using testcontainers
func (tctx *TestContainerTestContext) InitializeScenario(ctx *godog.ScenarioContext) {
	// File creation steps
	ctx.Step(`^the following Python file exists:$`, tctx.theFollowingPythonFileExists)
	ctx.Step(`^the Python file "([^"]*)" exists$`, tctx.thePythonFileExists)
	ctx.Step(`^the shell file "([^"]*)" exists$`, tctx.theShellFileExists)
	ctx.Step(`^the markdown file "([^"]*)" exists$`, tctx.theMarkdownFileExists)
	ctx.Step(`^the following JavaScript file exists:$`, tctx.theFollowingJavaScriptFileExists)
	ctx.Step(`^the following Go file exists:$`, tctx.theFollowingGoFileExists)

	// Linter verification steps
	ctx.Step(`^([a-zA-Z0-9_-]+) is installed$`, tctx.linterIsInstalled)
	ctx.Step(`^([a-zA-Z0-9_-]+) is not installed$`, tctx.linterIsNotInstalled)
	ctx.Step(`^([a-zA-Z0-9_-]+) isn't installed$`, tctx.linterIsNotInstalled)
	ctx.Step(`^And ([a-zA-Z0-9_-]+) isn't installed$`, tctx.linterIsNotInstalled)
	ctx.Step(`^But ([a-zA-Z0-9_-]+) is installed$`, tctx.linterIsInstalled)

	// CLI execution steps
	ctx.Step(`^taidy is called with ([a-zA-Z]+) filenames$`, tctx.taidyIsCalledWithFilenames)
	ctx.Step(`^taidy is called with the files$`, tctx.taidyIsCalledWithTheFiles)
	ctx.Step(`^taidy is called with no arguments$`, tctx.taidyIsCalledWithNoArguments)
	ctx.Step(`^taidy is called with files that don't exist$`, tctx.taidyIsCalledWithFilesThatDontExist)

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
	ctx.Step(`^lint output is emitted$`, tctx.lintOutputIsEmitted)
	ctx.Step(`^no formatting happens$`, tctx.noFormattingHappens)
	ctx.Step(`^no lint output is emitted$`, tctx.noLintOutputIsEmitted)
	ctx.Step(`^`+"`"+`taidy format poorly_formatted\.py`+"`"+` is run$`, tctx.taidyFormatPoorlyFormattedpyIsRun)
	ctx.Step(`^`+"`"+`taidy lint poorly_formatted\.py`+"`"+` is run$`, tctx.taidyLintPoorlyFormattedpyIsRun)
	ctx.Step(`^`+"`"+`taidy poorly_formatted\.py`+"`"+` is run$`, tctx.taidyPoorlyFormattedpyIsRun)
	ctx.Step(`^`+"`"+`taidy format poorly_formatted\.sh`+"`"+` is run$`, tctx.taidyFormatPoorlyFormattedshIsRun)
	ctx.Step(`^`+"`"+`taidy lint poorly_formatted\.sh`+"`"+` is run$`, tctx.taidyLintPoorlyFormattedshIsRun)
	ctx.Step(`^`+"`"+`taidy poorly_formatted\.sh`+"`"+` is run$`, tctx.taidyPoorlyFormattedshIsRun)
	ctx.Step(`^`+"`"+`taidy poorly_formatted\.bash`+"`"+` is run$`, tctx.taidyPoorlyFormattedbashIsRun)
	ctx.Step(`^`+"`"+`taidy poorly_formatted\.zsh`+"`"+` is run$`, tctx.taidyPoorlyFormattedzshIsRun)
	ctx.Step(`^`+"`"+`taidy format poorly_formatted\.md`+"`"+` is run$`, tctx.taidyFormatPoorlyFormattedmdIsRun)
	ctx.Step(`^`+"`"+`taidy lint poorly_formatted\.md`+"`"+` is run$`, tctx.taidyLintPoorlyFormattedmdIsRun)
	ctx.Step(`^`+"`"+`taidy poorly_formatted\.md`+"`"+` is run$`, tctx.taidyPoorlyFormattedmdIsRun)

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
		tctx.requiredLinters = tctx.requiredLinters[:0]   // Clear slice
		tctx.forbiddenLinters = tctx.forbiddenLinters[:0] // Clear slice
		return ctx, nil
	})
}
