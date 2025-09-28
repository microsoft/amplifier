#!/usr/bin/env python3
"""Test the healing workflow with a mock Aider."""

import shutil
from pathlib import Path

from amplifier.tools.healing_validator import validate_module
from amplifier.tools.health_monitor import HealthMonitor

# Create a backup
test_module = Path("amplifier/tools/demo_utils.py")
backup = Path("amplifier/tools/demo_utils.py.backup")
shutil.copy(test_module, backup)

print("Testing healing workflow (without actual Aider call)...")

# Check health before
monitor = HealthMonitor()
health_before = monitor.analyze_module(test_module)
print("\nBefore healing:")
print(f"  Health: {health_before.health_score:.1f}")
print(f"  Complexity: {health_before.complexity}")
print(f"  LOC: {health_before.loc}")

# Simulate a successful healing by simplifying the module
simplified_code = '''#!/usr/bin/env python3
"""Simplified demo utilities module."""


def process_data(data, mode="fast"):
    """Process data with simplified logic."""
    if not data:
        return 0

    if isinstance(data, list):
        if mode == "fast":
            return sum(item.get("value", 0) for item in data)
        else:
            # Slow mode with detailed processing
            result = 0
            for item in data:
                result += process_item(item)
            return result
    elif isinstance(data, dict):
        return sum(data.values()) if data else 0
    else:
        return 0


def process_item(item):
    """Process a single item."""
    if not item:
        return 0

    value = item.get("value", 0)
    if item.get("special"):
        return value * 2
    return value


def calculate_sum(*args):
    """Simple sum calculation."""
    return sum(args)
'''

# Write simplified version
test_module.write_text(simplified_code)

# Check health after
health_after = monitor.analyze_module(test_module)
print("\nAfter healing:")
print(f"  Health: {health_after.health_score:.1f}")
print(f"  Complexity: {health_after.complexity}")
print(f"  LOC: {health_after.loc}")

improvement = health_after.health_score - health_before.health_score
print(f"\nImprovement: {improvement:+.1f} points")

# Test validation
validation_passed = validate_module(test_module, Path("."))
print(f"Validation: {'✅ Passed' if validation_passed else '❌ Failed'}")

# Restore original
shutil.copy(backup, test_module)
backup.unlink()

print("\n✅ Healing workflow test complete!")
print("The healing process would:")
print("1. Create a git branch for isolation")
print("2. Call Aider with healing prompt")
print("3. Validate the healed module")
print("4. Merge if successful, rollback if not")
