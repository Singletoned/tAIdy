package main

import (
	"strings"
	"testing"
)

func TestLinterMap(t *testing.T) {
	// Test that we have configurations for expected file types
	expectedExtensions := []string{".py", ".js", ".ts", ".go", ".rs", ".rb", ".php"}
	
	for _, ext := range expectedExtensions {
		if commands, exists := linterMap[ext]; !exists {
			t.Errorf("Expected linter configuration for %s, but none found", ext)
		} else if len(commands) == 0 {
			t.Errorf("Expected at least one linter command for %s, but got empty list", ext)
		}
	}
}

func TestPythonLinterPriority(t *testing.T) {
	pythonCommands := linterMap[".py"]
	if len(pythonCommands) == 0 {
		t.Fatal("Expected Python linter commands, but got none")
	}
	
	// Test that we have expected linters in some order
	// We can't test exact order since it depends on what's installed,
	// but we can test that we have the major ones
	expectedLinters := []string{"ruff", "black", "flake8", "pylint", "python"}
	found := make(map[string]bool)
	
	for _, cmd := range pythonCommands {
		// Try to get the command for a dummy file to see what it would run
		if cmd.Available != nil {
			// We can't actually test availability without the tools installed,
			// but we can test that the Command function works
			if cmd.Command != nil {
				command, args := cmd.Command([]string{"test.py"})
				found[command] = true
				
				// Verify args contain the test file
				argsStr := strings.Join(args, " ")
				if !strings.Contains(argsStr, "test.py") {
					t.Errorf("Expected command args to contain test.py, got: %v", args)
				}
			}
		}
	}
	
	// Check that we found at least some expected linters
	foundCount := 0
	for _, linter := range expectedLinters {
		if found[linter] || found["uvx"] { // uvx is special case
			foundCount++
		}
	}
	
	if foundCount == 0 {
		t.Error("Expected to find at least one of the expected Python linters in the configuration")
	}
}

func TestJavaScriptLinterConfiguration(t *testing.T) {
	jsCommands := linterMap[".js"]
	if len(jsCommands) == 0 {
		t.Fatal("Expected JavaScript linter commands, but got none")
	}
	
	// Test first command generates correct args
	if jsCommands[0].Command != nil {
		command, args := jsCommands[0].Command([]string{"test.js", "app.js"})
		
		if command == "" {
			t.Error("Expected non-empty command")
		}
		
		// Verify args contain the test files
		argsStr := strings.Join(args, " ")
		if !strings.Contains(argsStr, "test.js") || !strings.Contains(argsStr, "app.js") {
			t.Errorf("Expected command args to contain test files, got: %v", args)
		}
	}
}

func TestVersionVariables(t *testing.T) {
	// Test that version variables exist and have default values
	if Version == "" {
		t.Error("Version should not be empty")
	}
	
	if GitCommit == "" {
		t.Error("GitCommit should not be empty")
	}
	
	if BuildDate == "" {
		t.Error("BuildDate should not be empty")
	}
	
	// Test default values
	if Version != "dev" {
		t.Logf("Version is set to: %s (expected 'dev' for test builds)", Version)
	}
}