package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

// LinterConfig maps file extensions to their corresponding linter commands
var linterMap = map[string][]string{
	".py":   {"ruff", "check"},
	".js":   {"prettier", "--check"},
	".jsx":  {"prettier", "--check"},
	".ts":   {"prettier", "--check"},
	".tsx":  {"prettier", "--check"},
	".json": {"prettier", "--check"},
	".css":  {"prettier", "--check"},
	".scss": {"prettier", "--check"},
	".html": {"prettier", "--check"},
	".md":   {"prettier", "--check"},
	".go":   {"gofmt", "-l"},
	".rs":   {"rustfmt", "--check"},
	".rb":   {"rubocop"},
	".php":  {"php-cs-fixer", "fix", "--dry-run"},
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintf(os.Stderr, "Usage: %s <file1> <file2> ...\n", os.Args[0])
		os.Exit(1)
	}

	files := os.Args[1:]
	
	// Group files by their required linter
	linterGroups := make(map[string][]string)
	
	for _, file := range files {
		// Check if file exists
		if _, err := os.Stat(file); os.IsNotExist(err) {
			fmt.Printf("Warning: File %s does not exist, skipping\n", file)
			continue
		}
		
		ext := strings.ToLower(filepath.Ext(file))
		if linterCmd, exists := linterMap[ext]; exists {
			linterKey := strings.Join(linterCmd, " ")
			linterGroups[linterKey] = append(linterGroups[linterKey], file)
		} else {
			fmt.Printf("Warning: No linter configured for file %s (extension: %s)\n", file, ext)
		}
	}
	
	// Check if any files will be linted
	if len(linterGroups) == 0 {
		fmt.Println("No supported files provided, no files were linted")
		os.Exit(0)
	}
	
	// Execute each linter with its respective files
	exitCode := 0
	for linterKey, fileList := range linterGroups {
		linterCmd := strings.Fields(linterKey)
		cmd := linterCmd[0]
		args := append(linterCmd[1:], fileList...)
		
		fmt.Printf("Running: %s %s\n", cmd, strings.Join(args, " "))
		
		execCmd := exec.Command(cmd, args...)
		execCmd.Stdout = os.Stdout
		execCmd.Stderr = os.Stderr
		
		if err := execCmd.Run(); err != nil {
			if exitError, ok := err.(*exec.ExitError); ok {
				exitCode = exitError.ExitCode()
			} else {
				fmt.Fprintf(os.Stderr, "Error executing %s: %v\n", cmd, err)
				exitCode = 1
			}
		}
	}
	
	os.Exit(exitCode)
}