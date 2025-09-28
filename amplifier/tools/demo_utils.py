#!/usr/bin/env python3
"""Simplified demo utilities module."""


def process_data(data, mode="fast"):
    """Process data with simplified logic."""
    if not data:
        return 0

    if isinstance(data, list):
        if mode == "fast":
            return sum(item.get("value", 0) for item in data)
        # Slow mode with detailed processing
        result = 0
        for item in data:
            result += process_item(item)
        return result
    if isinstance(data, dict):
        return sum(data.values()) if data else 0
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
