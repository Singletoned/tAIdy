"""
Sample Python file for testing lintair functionality.
"""
import os
import sys


def calculate_sum(numbers):
    """Calculate the sum of a list of numbers."""
    total = 0
    for num in numbers:
        total += num
    return total


def format_greeting(name, title=None):
    """Format a greeting message."""
    if title:
        return f"Hello, {title} {name}!"
    return f"Hello, {name}!"


class Calculator:
    """A simple calculator class."""
    
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        """Add two numbers."""
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def multiply(self, a, b):
        """Multiply two numbers.""" 
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result


if __name__ == "__main__":
    calc = Calculator()
    print(calc.add(5, 3))
    print(calc.multiply(4, 2))
    print("History:", calc.history)