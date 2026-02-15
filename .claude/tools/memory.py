#!/usr/bin/env python3
"""Memory convenience wrapper for Claude Code agents.

Wraps the Node.js git-notes memory tools from superpowers.

Usage:
    python memory.py recall <path>                  - Query memory at dot-path
    python memory.py memorize <section> <value>     - Store value in memory
    python memory.py snapshot                       - Generate markdown snapshot
"""

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hook_logger import HookLogger

logger = HookLogger("memory_wrapper")


def find_superpowers_dir():
    """Find the superpowers directory (plugin cache or local)."""
    cache_base = os.path.expanduser(
        "~/.claude/plugins/cache/superpowers-marketplace/superpowers"
    )
    if os.path.isdir(cache_base):
        try:
            versions = [
                d
                for d in os.listdir(cache_base)
                if os.path.isdir(os.path.join(cache_base, d))
                and os.path.isfile(os.path.join(cache_base, d, "commands", "recall.js"))
            ]
            if versions:
                versions.sort()
                return os.path.join(cache_base, versions[-1])
        except OSError:
            pass

        if os.path.isfile(os.path.join(cache_base, "commands", "recall.js")):
            return cache_base

    local_dir = "C:/Przemek/superpowers"
    if os.path.isdir(local_dir) and os.path.isfile(
        os.path.join(local_dir, "commands", "recall.js")
    ):
        return local_dir

    return None


def recall(path):
    """Query memory at given dot-path."""
    sp_dir = find_superpowers_dir()
    if not sp_dir:
        return "Error: superpowers directory not found"

    cmd = ["node", os.path.join(sp_dir, "commands", "recall.js"), path]
    logger.info(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=sp_dir, timeout=15
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr.strip() or result.stdout.strip()}"
    except subprocess.TimeoutExpired:
        return "Error: command timed out"
    except Exception as e:
        return f"Error: {e}"


def memorize(section, value):
    """Store a value in memory at given section."""
    sp_dir = find_superpowers_dir()
    if not sp_dir:
        return "Error: superpowers directory not found"

    if isinstance(value, (dict, list)):
        value = json.dumps(value)

    cmd = [
        "node",
        os.path.join(sp_dir, "commands", "memorize.js"),
        "--section",
        section,
        "--value",
        value,
    ]
    logger.info(f"Running memorize for section: {section}")

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=sp_dir, timeout=15
        )
        if result.returncode == 0:
            return result.stdout.strip() or "OK"
        else:
            return f"Error: {result.stderr.strip() or result.stdout.strip()}"
    except subprocess.TimeoutExpired:
        return "Error: command timed out"
    except Exception as e:
        return f"Error: {e}"


def snapshot():
    """Generate human-readable memory snapshot."""
    sp_dir = find_superpowers_dir()
    if not sp_dir:
        return "Error: superpowers directory not found"

    cmd = ["node", os.path.join(sp_dir, "commands", "snapshot-memory.js")]
    logger.info(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=sp_dir, timeout=15
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr.strip() or result.stdout.strip()}"
    except subprocess.TimeoutExpired:
        return "Error: command timed out"
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "help"

    if action == "recall" and len(sys.argv) > 2:
        print(recall(sys.argv[2]))
    elif action == "memorize" and len(sys.argv) > 3:
        print(memorize(sys.argv[2], sys.argv[3]))
    elif action == "snapshot":
        print(snapshot())
    else:
        print("Usage:")
        print(
            "  memory.py recall <path>              - Query memory (e.g. 'knowledge_base.decisions')"
        )
        print("  memory.py memorize <section> <value>  - Store value")
        print("  memory.py snapshot                    - Generate markdown snapshot")
