package main

import (
	"context"
	"flag"
	"fmt"
	"os"

	"github.com/cucumber/godog"
	"github.com/cucumber/godog/colors"
)

var opts = godog.Options{
	Output:      colors.Colored(os.Stdout),
	Format:      "progress", // better for parallel execution
	Paths:       []string{"features"},
	Randomize:   0, // randomize scenario execution order
	Concurrency: 4, // run scenarios in parallel
}

var format = flag.String("format", "progress", "Output format")

func init() {
	godog.BindCommandLineFlags("", &opts)
}

func InitializeTestSuite(ctx *godog.TestSuiteContext) {
	ctx.BeforeSuite(func() {
		// Test suite starting silently
	})

	ctx.AfterSuite(func() {
		// Test suite completed silently
	})
}

func InitializeScenario(ctx *godog.ScenarioContext) {
	// Use testcontainer test context instead of the old one
	testContext := NewTestContainerTestContext()

	// Clean up at the end
	ctx.After(func(ctx context.Context, sc *godog.Scenario, err error) (context.Context, error) {
		testContext.Close()
		return ctx, nil
	})

	testContext.InitializeScenario(ctx)
}

func main() {
	flag.Parse()

	// Set format from command line
	if *format != "progress" {
		opts.Format = *format
	}

	// Handle output redirection for JSON format
	if *format == "cucumber" {
		jsonFile, err := os.Create("bdd-results.json")
		if err != nil {
			fmt.Printf("Failed to create JSON report: %v\n", err)
			os.Exit(1)
		}
		defer jsonFile.Close()
		opts.Output = jsonFile
	}

	opts.Paths = flag.Args()
	if len(opts.Paths) == 0 {
		opts.Paths = []string{"features"}
	}

	status := godog.TestSuite{
		Name:                 "lintair BDD tests",
		ScenarioInitializer:  InitializeScenario,
		TestSuiteInitializer: InitializeTestSuite,
		Options:              &opts,
	}.Run()

	if st := status; st > 0 {
		fmt.Printf("Tests failed with status: %d\n", st)
		os.Exit(st)
	}
}
