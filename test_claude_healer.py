#!/usr/bin/env python3
"""Test script for the Claude healer implementation."""

import asyncio
import tempfile
from pathlib import Path

import pytest

from amplifier.tools.claude_healer import heal_with_claude


@pytest.mark.asyncio
async def test_claude_healer():
    """Test the Claude healer with a simple example."""
    # Create a test module with complex code
    test_code = '''
def process_data(data, flag1, flag2, flag3):
    """Process data with too many parameters and complexity."""
    result = []
    for item in data:
        if flag1:
            if flag2:
                if flag3:
                    if item > 10:
                        result.append(item * 2)
                    else:
                        result.append(item)
                else:
                    result.append(item + 1)
            else:
                if flag3:
                    result.append(item - 1)
                else:
                    result.append(0)
        else:
            result.append(item)
    return result
'''

    # Create a temporary file with the test code
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(test_code)
        test_file = Path(f.name)

    try:
        print(f"Test file created: {test_file}")
        print("Original code:")
        print(test_code)
        print("\nApplying healing...")

        # Create a healing prompt
        healing_prompt = """
SIMPLIFY this code following these principles:
1. Reduce nesting to maximum 2 levels
2. Use early returns and guard clauses
3. Extract complex logic into helper functions
4. Each function should do ONE thing
5. Maximum 10 lines per function

Make it clean, simple, and readable.
"""

        # Apply healing
        success = await heal_with_claude(test_file, healing_prompt)

        if success:
            print("\n✓ Healing successful!")
            print("\nImproved code:")
            with open(test_file) as f:
                print(f.read())
        else:
            print("\n✗ Healing failed")

        return success

    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()
            print(f"\nTest file cleaned up: {test_file}")


if __name__ == "__main__":
    success = asyncio.run(test_claude_healer())
    exit(0 if success else 1)
