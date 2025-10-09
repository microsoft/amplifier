#!/usr/bin/env python3
"""
Project Planner CLI - Main entry point.

Usage:
    python -m scenarios.project_planner init --name "Project Name"
    python -m scenarios.project_planner plan --goals "Build authentication system"
    python -m scenarios.project_planner status
    python -m scenarios.project_planner execute
"""

import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scenarios.project_planner.cli import main

if __name__ == "__main__":
    main()
