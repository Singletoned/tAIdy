package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"os"

	"github.com/cucumber/godog"
	"github.com/cucumber/godog/colors"
)

var opts = godog.Options{
	Output: colors.Colored(os.Stdout),
	Format: "pretty", // or "progress"
	Paths:  []string{"features"},
	Randomize: 0, // randomize scenario execution order
}

func init() {
	godog.BindCommandLineFlags("godog.", &opts)
}

func InitializeTestSuite(ctx *godog.TestSuiteContext) {
	ctx.BeforeSuite(func() {
		log.Println("Starting BDD test suite...")
	})
	
	ctx.AfterSuite(func() {
		log.Println("BDD test suite completed.")
	})
}

func InitializeScenario(ctx *godog.ScenarioContext) {
	testContext := NewTestContext()
	
	// Clean up at the end
	ctx.After(func(ctx context.Context, sc *godog.Scenario, err error) (context.Context, error) {
		testContext.Close()
		return ctx, nil
	})
	
	testContext.InitializeScenario(ctx)
}

func main() {
	flag.Parse()
	opts.Paths = flag.Args()

	if len(opts.Paths) == 0 {
		opts.Paths = []string{"features"}
	}

	status := godog.TestSuite{
		Name:                "lintair BDD tests",
		ScenarioInitializer: InitializeScenario,
		TestSuiteInitializer: InitializeTestSuite,
		Options:             &opts,
	}.Run()

	if st := status; st > 0 {
		fmt.Printf("Tests failed with status: %d\n", st)
		os.Exit(st)
	}
}