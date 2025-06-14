/**
 * Sample JavaScript file for testing lintair functionality.
 */

function calculateSum(numbers) {
  let total = 0;
  for (const num of numbers) {
    total += num;
  }
  return total;
}

function formatGreeting(name, title = null) {
  if (title) {
    return `Hello, ${title} ${name}!`;
  }
  return `Hello, ${name}!`;
}

class Calculator {
  constructor() {
    this.history = [];
  }

  add(a, b) {
    const result = a + b;
    this.history.push(`${a} + ${b} = ${result}`);
    return result;
  }

  multiply(a, b) {
    const result = a * b;
    this.history.push(`${a} * ${b} = ${result}`);
    return result;
  }

  getHistory() {
    return [...this.history];
  }
}

// Example usage
if (typeof require !== "undefined" && require.main === module) {
  const calc = new Calculator();
  console.log(calc.add(5, 3));
  console.log(calc.multiply(4, 2));
  console.log("History:", calc.getHistory());
}

module.exports = { Calculator, calculateSum, formatGreeting };