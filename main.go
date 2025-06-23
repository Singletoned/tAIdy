package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

// Version information - can be overridden at build time
var (
	Version   = "dev"
	GitCommit = "unknown"
	BuildDate = "unknown"
)

// LinterCommand represents a linter command that can be tried
type LinterCommand struct {
	Available func() bool
	Command   func(files []string) (string, []string)
}

// Mode represents the operation mode
type Mode int

const (
	ModeBoth   Mode = iota // Both lint and format
	ModeLint               // Lint only
	ModeFormat             // Format only
)

// LinterConfig maps file extensions to sequences of linter commands to try in order
var linterMap = map[string][]LinterCommand{
	".py": {
		{
			Available: func() bool {
				_, err := exec.LookPath("ruff")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "ruff", append([]string{"check"}, files...)
			},
		},
		{
			Available: func() bool {
				_, err := exec.LookPath("uvx")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "uvx", append([]string{"ruff", "check"}, files...)
			},
		},
		{
			Available: func() bool {
				_, err := exec.LookPath("black")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "black", append([]string{"--check", "--diff"}, files...)
			},
		},
		{
			Available: func() bool {
				_, err := exec.LookPath("flake8")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "flake8", files
			},
		},
		{
			Available: func() bool {
				_, err := exec.LookPath("pylint")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "pylint", files
			},
		},
		{
			Available: func() bool {
				_, err := exec.LookPath("python")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				// Basic syntax check as final fallback
				args := []string{"-m", "py_compile"}
				return "python", append(args, files...)
			},
		},
	},
	".js": {
		{
			Available: func() bool {
				_, err := exec.LookPath("eslint")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "eslint", files
			},
		},
		{
			Available: func() bool {
				_, err := exec.LookPath("prettier")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "prettier", append([]string{"--check"}, files...)
			},
		},
		{
			Available: func() bool {
				_, err := exec.LookPath("node")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				// Basic syntax check as fallback
				args := []string{"--check"}
				return "node", append(args, files...)
			},
		},
	},
	".jsx": {
		{
			Available: func() bool {
				_, err := exec.LookPath("eslint")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "eslint", files
			},
		},
		{
			Available: func() bool {
				_, err := exec.LookPath("prettier")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "prettier", append([]string{"--check"}, files...)
			},
		},
	},
	".ts": {
		{
			Available: func() bool {
				_, err := exec.LookPath("eslint")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "eslint", files
			},
		},
		{
			Available: func() bool {
				_, err := exec.LookPath("tsc")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "tsc", append([]string{"--noEmit"}, files...)
			},
		},
		{
			Available: func() bool {
				_, err := exec.LookPath("prettier")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "prettier", append([]string{"--check"}, files...)
			},
		},
	},
	".tsx": {
		{
			Available: func() bool {
				_, err := exec.LookPath("eslint")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "eslint", files
			},
		},
		{
			Available: func() bool {
				_, err := exec.LookPath("tsc")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "tsc", append([]string{"--noEmit"}, files...)
			},
		},
		{
			Available: func() bool {
				_, err := exec.LookPath("prettier")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "prettier", append([]string{"--check"}, files...)
			},
		},
	},
	".json": {
		{
			Available: func() bool {
				_, err := exec.LookPath("prettier")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "prettier", append([]string{"--check"}, files...)
			},
		},
	},
	".css": {
		{
			Available: func() bool {
				_, err := exec.LookPath("prettier")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "prettier", append([]string{"--check"}, files...)
			},
		},
	},
	".scss": {
		{
			Available: func() bool {
				_, err := exec.LookPath("prettier")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "prettier", append([]string{"--check"}, files...)
			},
		},
	},
	".html": {
		{
			Available: func() bool {
				_, err := exec.LookPath("prettier")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "prettier", append([]string{"--check"}, files...)
			},
		},
	},
	".md": {
		{
			Available: func() bool {
				_, err := exec.LookPath("prettier")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "prettier", append([]string{"--check"}, files...)
			},
		},
	},
	".go": {
		{
			Available: func() bool {
				_, err := exec.LookPath("gofmt")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "gofmt", append([]string{"-l"}, files...)
			},
		},
	},
	".rs": {
		{
			Available: func() bool {
				_, err := exec.LookPath("rustfmt")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "rustfmt", append([]string{"--check"}, files...)
			},
		},
	},
	".rb": {
		{
			Available: func() bool {
				_, err := exec.LookPath("rubocop")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "rubocop", files
			},
		},
	},
	".php": {
		{
			Available: func() bool {
				_, err := exec.LookPath("php-cs-fixer")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "php-cs-fixer", append([]string{"fix", "--dry-run"}, files...)
			},
		},
	},
}

// FormatterConfig maps file extensions to sequences of formatter commands to try in order
var formatterMap = map[string][]LinterCommand{
	".py": {
		{
			Available: func() bool {
				_, err := exec.LookPath("ruff")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "ruff", append([]string{"format"}, files...)
			},
		},
		{
			Available: func() bool {
				_, err := exec.LookPath("uvx")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "uvx", append([]string{"ruff", "format"}, files...)
			},
		},
		{
			Available: func() bool {
				_, err := exec.LookPath("black")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "black", files
			},
		},
	},
	".js": {
		{
			Available: func() bool {
				_, err := exec.LookPath("prettier")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "prettier", append([]string{"--write"}, files...)
			},
		},
	},
	".jsx": {
		{
			Available: func() bool {
				_, err := exec.LookPath("prettier")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "prettier", append([]string{"--write"}, files...)
			},
		},
	},
	".ts": {
		{
			Available: func() bool {
				_, err := exec.LookPath("prettier")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "prettier", append([]string{"--write"}, files...)
			},
		},
	},
	".tsx": {
		{
			Available: func() bool {
				_, err := exec.LookPath("prettier")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "prettier", append([]string{"--write"}, files...)
			},
		},
	},
	".json": {
		{
			Available: func() bool {
				_, err := exec.LookPath("prettier")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "prettier", append([]string{"--write"}, files...)
			},
		},
	},
	".css": {
		{
			Available: func() bool {
				_, err := exec.LookPath("prettier")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "prettier", append([]string{"--write"}, files...)
			},
		},
	},
	".scss": {
		{
			Available: func() bool {
				_, err := exec.LookPath("prettier")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "prettier", append([]string{"--write"}, files...)
			},
		},
	},
	".html": {
		{
			Available: func() bool {
				_, err := exec.LookPath("prettier")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "prettier", append([]string{"--write"}, files...)
			},
		},
	},
	".md": {
		{
			Available: func() bool {
				_, err := exec.LookPath("prettier")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "prettier", append([]string{"--write"}, files...)
			},
		},
	},
	".go": {
		{
			Available: func() bool {
				_, err := exec.LookPath("gofmt")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "gofmt", append([]string{"-w"}, files...)
			},
		},
	},
	".rs": {
		{
			Available: func() bool {
				_, err := exec.LookPath("rustfmt")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "rustfmt", files
			},
		},
	},
	".rb": {
		{
			Available: func() bool {
				_, err := exec.LookPath("rubocop")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "rubocop", append([]string{"-a"}, files...)
			},
		},
	},
	".php": {
		{
			Available: func() bool {
				_, err := exec.LookPath("php-cs-fixer")
				return err == nil
			},
			Command: func(files []string) (string, []string) {
				return "php-cs-fixer", append([]string{"fix"}, files...)
			},
		},
	},
}

func showUsage() {
	fmt.Fprintf(os.Stderr, "Usage: %s [command] <file1> <file2> ...\n", os.Args[0])
	fmt.Fprintf(os.Stderr, "\nCommands:\n")
	fmt.Fprintf(os.Stderr, "  lint     Lint files only (no formatting)\n")
	fmt.Fprintf(os.Stderr, "  format   Format files only (no linting)\n")
	fmt.Fprintf(os.Stderr, "  (none)   Both lint and format (default)\n")
	fmt.Fprintf(os.Stderr, "\nFlags:\n")
	fmt.Fprintf(os.Stderr, "  -h, --help     Show this help message\n")
	fmt.Fprintf(os.Stderr, "  -v, --version  Show version information\n")
}

func showHelp() {
	fmt.Printf("Taidy - Smart linter/formatter with automatic tool detection\n\n")
	showUsage()
	fmt.Printf("\nSupported file types and linters:\n")
	fmt.Printf("  Python:     ruff → uvx ruff → black → flake8 → pylint → python -m py_compile\n")
	fmt.Printf("  JavaScript: eslint → prettier → node --check\n")
	fmt.Printf("  TypeScript: eslint → tsc --noEmit → prettier\n")
	fmt.Printf("  Go:         gofmt\n")
	fmt.Printf("  Rust:       rustfmt\n")
	fmt.Printf("  Ruby:       rubocop\n")
	fmt.Printf("  PHP:        php-cs-fixer\n")
	fmt.Printf("  JSON/CSS:   prettier\n")
	fmt.Printf("\nTaidy automatically detects which linters are available and uses the best one for each file type.\n")
}

func showVersion() {
	fmt.Printf("Taidy %s\n", Version)
	if GitCommit != "unknown" {
		fmt.Printf("Git commit: %s\n", GitCommit)
	}
	if BuildDate != "unknown" {
		fmt.Printf("Built: %s\n", BuildDate)
	}
}

func processFiles(files []string, mode Mode) int {
	// Group files by their file extension
	fileGroups := make(map[string][]string)

	for _, file := range files {
		// Check if file exists
		if _, err := os.Stat(file); os.IsNotExist(err) {
			fmt.Printf("Warning: File %s does not exist, skipping\n", file)
			continue
		}

		ext := strings.ToLower(filepath.Ext(file))

		// Check if we have configuration for this extension based on mode
		var hasConfig bool
		switch mode {
		case ModeLint:
			_, hasConfig = linterMap[ext]
		case ModeFormat:
			_, hasConfig = formatterMap[ext]
		case ModeBoth:
			_, hasLinter := linterMap[ext]
			_, hasFormatter := formatterMap[ext]
			hasConfig = hasLinter || hasFormatter
		}

		if hasConfig {
			fileGroups[ext] = append(fileGroups[ext], file)
		} else {
			fmt.Printf("Warning: No linter configured for file %s (extension: %s)\n", file, ext)
		}
	}

	// Check if any files will be processed
	if len(fileGroups) == 0 {
		fmt.Println("No supported files provided, no files were linted")
		return 0
	}

	// Execute linters/formatters for each file extension
	exitCode := 0
	for ext, fileList := range fileGroups {
		if mode == ModeLint || mode == ModeBoth {
			if linterCommands, exists := linterMap[ext]; exists {
				executed := executeLinters(linterCommands, fileList)
				if !executed {
					fmt.Printf("Warning: No available linter found for %s files\n", ext)
				}
			}
		}

		if mode == ModeFormat || mode == ModeBoth {
			if formatterCommands, exists := formatterMap[ext]; exists {
				executed := executeLinters(formatterCommands, fileList)
				if !executed {
					fmt.Printf("Warning: No available formatter found for %s files\n", ext)
				}
			}
		}
	}

	return exitCode
}

func executeLinters(commands []LinterCommand, fileList []string) bool {
	// Try each command in order until one is available
	for _, linterCmd := range commands {
		if linterCmd.Available() {
			cmd, args := linterCmd.Command(fileList)

			fmt.Printf("Running: %s %s\n", cmd, strings.Join(args, " "))

			execCmd := exec.Command(cmd, args...)
			execCmd.Stdout = os.Stdout
			execCmd.Stderr = os.Stderr

			if err := execCmd.Run(); err != nil {
				if exitError, ok := err.(*exec.ExitError); ok {
					_ = exitError.ExitCode() // We could track this but for now just continue
				} else {
					fmt.Fprintf(os.Stderr, "Error executing %s: %v\n", cmd, err)
				}
			}
			return true // Executed successfully
		}
	}
	return false // No available command found
}

func main() {
	if len(os.Args) < 2 {
		showUsage()
		os.Exit(1)
	}

	// Handle version and help flags
	arg := os.Args[1]
	switch arg {
	case "-v", "--version":
		showVersion()
		os.Exit(0)
	case "-h", "--help":
		showHelp()
		os.Exit(0)
	}

	// Parse command and files
	var mode Mode = ModeBoth
	var files []string

	switch os.Args[1] {
	case "lint":
		mode = ModeLint
		if len(os.Args) < 3 {
			showUsage()
			os.Exit(1)
		}
		files = os.Args[2:]
	case "format":
		mode = ModeFormat
		if len(os.Args) < 3 {
			showUsage()
			os.Exit(1)
		}
		files = os.Args[2:]
	default:
		// No subcommand, treat first arg as file
		mode = ModeBoth
		files = os.Args[1:]
	}

	exitCode := processFiles(files, mode)
	os.Exit(exitCode)
}
