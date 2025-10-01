#!/usr/bin/env python3
"""
Standalone CLI for Claude session awareness.

Usage:
    python scripts/claude_cli.py status
    python scripts/claude_cli.py track "Working on feature X"
    python scripts/claude_cli.py broadcast "Starting deployment"
"""

import sys
from pathlib import Path

# Add amplifier to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from amplifier.claude.cli import claude_group

if __name__ == "__main__":
    claude_group()
