#!/usr/bin/env python3
"""
Claude Code SubagentStop validation hook.
Checks that subagents actually produced output (not empty result).
Logs dispatch success/failure rate alongside subagent-logger dispatch logs.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import NoReturn


def ensure_log_directory() -> Path:
    """Ensure the log directory exists and return its path."""
    project_root = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
    log_dir = project_root / ".claude" / "logs" / "subagent-logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def assess_result(data: dict[str, Any]) -> dict[str, Any]:
    """Determine if the subagent produced meaningful output."""
    result = data.get("result", "")
    result_str = str(result) if result is not None else ""

    is_empty = len(result_str.strip()) == 0
    is_minimal = len(result_str.strip()) < 50

    # Look for explicit status markers from Amplifier subagents
    has_done = any(
        marker in result_str
        for marker in ["Status: DONE", "Status: BLOCKED", "Status: NEEDS_CONTEXT", "Status: DONE_WITH_CONCERNS"]
    )
    has_trailing_continuation = result_str.rstrip().endswith(("I'll now", "Let me", "Next,", "I will"))

    return {
        "is_empty": is_empty,
        "is_minimal": is_minimal,
        "has_explicit_status": has_done,
        "has_trailing_continuation": has_trailing_continuation,
        "result_length": len(result_str),
    }


def log_subagent_result(data: dict[str, Any]) -> None:
    """Log subagent result assessment to daily JSONL file."""
    log_dir = ensure_log_directory()
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"subagent-results-{today}.jsonl"

    assessment = assess_result(data)

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": data.get("session_id"),
        "hook_event": data.get("hook_event_name"),
        "result_length": assessment["result_length"],
        "is_empty": assessment["is_empty"],
        "is_minimal": assessment["is_minimal"],
        "has_explicit_status": assessment["has_explicit_status"],
        "has_trailing_continuation": assessment["has_trailing_continuation"],
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    update_result_summary(log_dir, log_entry)


def update_result_summary(log_dir: Path, log_entry: dict[str, Any]) -> None:
    """Update running summary of subagent result quality."""
    summary_file = log_dir / "results-summary.json"

    if summary_file.exists():
        with open(summary_file) as f:
            summary = json.load(f)
    else:
        summary = {
            "total_completions": 0,
            "empty_results": 0,
            "minimal_results": 0,
            "has_explicit_status": 0,
            "trailing_continuations": 0,
            "first_seen": None,
            "last_seen": None,
        }

    summary["total_completions"] += 1
    if log_entry["is_empty"]:
        summary["empty_results"] += 1
    if log_entry["is_minimal"]:
        summary["minimal_results"] += 1
    if log_entry["has_explicit_status"]:
        summary["has_explicit_status"] += 1
    if log_entry["has_trailing_continuation"]:
        summary["trailing_continuations"] += 1
    if not summary["first_seen"]:
        summary["first_seen"] = log_entry["timestamp"]
    summary["last_seen"] = log_entry["timestamp"]

    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)


def main() -> NoReturn:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    if data.get("hook_event_name") == "SubagentStop":
        try:
            log_subagent_result(data)
        except Exception:
            pass  # Never block Claude's operation

    sys.exit(0)


if __name__ == "__main__":
    main()
