// Sample Go file for testing lintair functionality
package main

import (
	"fmt"
	"strconv"
	"strings"
)

// Calculator represents a simple calculator
type Calculator struct {
	history []string
}

// NewCalculator creates a new calculator instance
func NewCalculator() *Calculator {
	return &Calculator{
		history: make([]string, 0),
	}
}

// Add adds two numbers and records the operation
func (c *Calculator) Add(a, b int) int {
	result := a + b
	operation := fmt.Sprintf("%d + %d = %d", a, b, result)
	c.history = append(c.history, operation)
	return result
}

// Multiply multiplies two numbers and records the operation
func (c *Calculator) Multiply(a, b int) int {
	result := a * b
	operation := fmt.Sprintf("%d * %d = %d", a, b, result)
	c.history = append(c.history, operation)
	return result
}

// GetHistory returns the calculation history
func (c *Calculator) GetHistory() []string {
	return c.history
}

// CalculateSum calculates the sum of a slice of integers
func CalculateSum(numbers []int) int {
	total := 0
	for _, num := range numbers {
		total += num
	}
	return total
}

// FormatGreeting formats a greeting message
func FormatGreeting(name, title string) string {
	if title != "" {
		return fmt.Sprintf("Hello, %s %s!", title, name)
	}
	return fmt.Sprintf("Hello, %s!", name)
}

// ParseNumbers parses a comma-separated string of numbers
func ParseNumbers(input string) ([]int, error) {
	parts := strings.Split(input, ",")
	numbers := make([]int, 0, len(parts))

	for _, part := range parts {
		trimmed := strings.TrimSpace(part)
		if trimmed == "" {
			continue
		}

		num, err := strconv.Atoi(trimmed)
		if err != nil {
			return nil, fmt.Errorf("invalid number: %s", trimmed)
		}
		numbers = append(numbers, num)
	}

	return numbers, nil
}

func main() {
	calc := NewCalculator()

	fmt.Println(calc.Add(5, 3))
	fmt.Println(calc.Multiply(4, 2))
	fmt.Println("History:", calc.GetHistory())

	numbers := []int{1, 2, 3, 4, 5}
	sum := CalculateSum(numbers)
	fmt.Printf("Sum of %v = %d\n", numbers, sum)

	greeting := FormatGreeting("World", "")
	fmt.Println(greeting)
}
