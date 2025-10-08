#!/usr/bin/env python3
"""
Smart Decomposer CLI - Main entry point.

Usage:
    python -m scenarios.smart_decomposer decompose --goal "Build feature X"
    python -m scenarios.smart_decomposer assign --project-id "proj123"
    python -m scenarios.smart_decomposer execute --project-id "proj123"
    python -m scenarios.smart_decomposer status --project-id "proj123"
"""

import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scenarios.smart_decomposer.cli import main

if __name__ == "__main__":
    main()
