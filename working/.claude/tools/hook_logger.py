#!/usr/bin/env python3
"""
Simple file-based logging for Claude Code hooks.
Following ruthless simplicity principle - just enough to debug effectively.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class HookLogger:
    """Simple logger that writes to both file and stderr"""

    def __init__(self, hook_name: str):
        """Initialize logger for a specific hook"""
        self.hook_name = hook_name

        # Create logs directory
        self.log_dir = Path(__file__).parent.parent / "logs"
        self.log_dir.mkdir(exist_ok=True)

        # Create log file with today's date
        today = datetime.now().strftime("%Y%m%d")
        self.log_file = self.log_dir / f"{hook_name}_{today}.log"

        # Log initialization
        self.info(f"Logger initialized for {hook_name}")

    def _format_message(self, level: str, message: str) -> str:
        """Format a log message with timestamp and level"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        return f"[{timestamp}] [{self.hook_name}] [{level}] {message}"

    def _write(self, level: str, message: str):
        """Write to both file and stderr"""
        formatted = self._format_message(level, message)

        # Write to stderr (existing behavior)
        print(formatted, file=sys.stderr)

        # Write to file
        try:
            with open(self.log_file, "a") as f:
                f.write(formatted + "\n")
        except Exception as e:
            # If file writing fails, just log to stderr
            print(f"Failed to write to log file: {e}", file=sys.stderr)

    def info(self, message: str):
        """Log info level message"""
        self._write("INFO", message)

    def debug(self, message: str):
        """Log debug level message"""
        self._write("DEBUG", message)

    def error(self, message: str):
        """Log error level message"""
        self._write("ERROR", message)

    def warning(self, message: str):
        """Log warning level message"""
        self._write("WARN", message)

    def json_preview(self, label: str, data: Any, max_length: int = 500):
        """Log a preview of JSON data"""
        try:
            json_str = json.dumps(data, default=str)
            if len(json_str) > max_length:
                json_str = json_str[:max_length] + "..."
            self.debug(f"{label}: {json_str}")
        except Exception as e:
            self.error(f"Failed to serialize {label}: {e}")

    def structure_preview(self, label: str, data: dict):
        """Log structure of a dict without full content"""
        structure = {}
        for key, value in data.items():
            if isinstance(value, list):
                structure[key] = f"list[{len(value)}]"
            elif isinstance(value, dict):
                structure[key] = (
                    f"dict[{list(value.keys())[:3]}...]" if len(value.keys()) > 3 else f"dict[{list(value.keys())}]"
                )
            elif isinstance(value, str):
                structure[key] = f"str[{len(value)} chars]"
            else:
                structure[key] = type(value).__name__
        self.debug(f"{label}: {json.dumps(structure)}")

    def exception(self, message: str, exc: Exception | None = None):
        """Log exception with traceback"""
        import traceback

        if exc:
            self.error(f"{message}: {exc}")
            self.error(f"Traceback:\n{traceback.format_exc()}")
        else:
            self.error(message)
            self.error(f"Traceback:\n{traceback.format_exc()}")

    def cleanup_old_logs(self, days_to_keep: int = 7):
        """Clean up log files older than specified days"""
        try:
            from datetime import date
            from datetime import timedelta

            # Use date instead of datetime to avoid timezone issues
            today = datetime.now().date()
            cutoff = today - timedelta(days=days_to_keep)

            for log_file in self.log_dir.glob(f"{self.hook_name}_*.log"):
                # Parse date from filename
                try:
                    date_str = log_file.stem.split("_")[-1]
                    # Parse date components manually to avoid strptime timezone warning
                    year = int(date_str[0:4])
                    month = int(date_str[4:6])
                    day = int(date_str[6:8])
                    file_date = date(year, month, day)
                    if file_date < cutoff:
                        log_file.unlink()
                        self.info(f"Deleted old log file: {log_file.name}")
                except (ValueError, IndexError):
                    # Skip files that don't match expected pattern
                    continue
        except Exception as e:
            self.warning(f"Failed to cleanup old logs: {e}")
