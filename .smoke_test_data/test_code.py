#!/usr/bin/env python3
"""Sample Python code for smoke testing."""


def calculate_sum(numbers):
    """Calculate the sum of a list of numbers."""
    return sum(numbers)


def find_maximum(numbers):
    """Find the maximum value in a list."""
    if not numbers:
        return None
    return max(numbers)


def main():
    """Main function for testing."""
    test_data = [1, 2, 3, 4, 5]
    print(f"Sum: {calculate_sum(test_data)}")
    print(f"Max: {find_maximum(test_data)}")


if __name__ == "__main__":
    main()
