#!/usr/bin/env python3

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import NoReturn

# Try to import centralized path config, fall back to .data if not available
try:
    from amplifier.config.paths import paths
except ImportError:
    paths = None  # type: ignore


def ensure_log_directory() -> Path:
    """Ensure the log directory exists and return its path."""
    # Use .claude/logs directory for consistency with other Claude Code hooks
    project_root = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
    log_dir = project_root / ".claude" / "logs" / "subagent-logs"

    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def create_log_entry(data: dict[str, Any]) -> dict[str, Any]:
    """Create a structured log entry from the hook data."""
    tool_input = data.get("tool_input", {})

    return {
        "timestamp": datetime.now().isoformat(),
        "session_id": data.get("session_id"),
        "cwd": data.get("cwd"),
        "subagent_type": tool_input.get("subagent_type"),
        "description": tool_input.get("description"),
        "prompt_length": len(tool_input.get("prompt", "")),
        "prompt": tool_input.get("prompt", ""),  # Store full prompt for debugging
    }


def log_subagent_usage(data: dict[str, Any]) -> None:
    """Log subagent usage to a daily log file."""
    log_dir = ensure_log_directory()

    # Create daily log file
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"subagent-usage-{today}.jsonl"

    # Create log entry
    log_entry = create_log_entry(data)

    # Append to log file (using JSONL format for easy parsing)
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    # Also create/update a summary file
    update_summary(log_dir, log_entry)


def update_summary(log_dir: Path, log_entry: dict[str, Any]) -> None:
    """Update the summary file with aggregated statistics."""
    summary_file = log_dir / "summary.json"

    # Load existing summary or create new one
    if summary_file.exists():
        with open(summary_file) as f:
            summary = json.load(f)
    else:
        summary = {
            "total_invocations": 0,
            "subagent_counts": {},
            "first_invocation": None,
            "last_invocation": None,
            "sessions": set(),
        }

    # Convert sessions to set if loading from JSON (where it's a list)
    if isinstance(summary.get("sessions"), list):
        summary["sessions"] = set(summary["sessions"])

    # Update summary
    summary["total_invocations"] += 1

    subagent_type = log_entry["subagent_type"]
    if subagent_type:
        summary["subagent_counts"][subagent_type] = summary["subagent_counts"].get(subagent_type, 0) + 1

    if not summary["first_invocation"]:
        summary["first_invocation"] = log_entry["timestamp"]
    summary["last_invocation"] = log_entry["timestamp"]

    if log_entry["session_id"]:
        summary["sessions"].add(log_entry["session_id"])

    # Convert sessions set to list for JSON serialization
    summary_to_save = summary.copy()
    summary_to_save["sessions"] = list(summary["sessions"])
    summary_to_save["unique_sessions"] = len(summary["sessions"])

    # Save updated summary
    with open(summary_file, "w") as f:
        json.dump(summary_to_save, f, indent=2)


def main() -> NoReturn:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        # Silently fail to not disrupt Claude's workflow
        print(f"Warning: Could not parse JSON input: {e}", file=sys.stderr)
        sys.exit(0)

    # Only process if this is a Task tool for subagents
    if data.get("hook_event_name") == "PreToolUse" and data.get("tool_name") == "Task":
        try:
            log_subagent_usage(data)
        except Exception as e:
            # Log error but don't block Claude's operation
            print(f"Warning: Failed to log subagent usage: {e}", file=sys.stderr)

    # Always exit successfully to not block Claude's workflow
    sys.exit(0)


if __name__ == "__main__":
    main()
