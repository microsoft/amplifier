"""Structured logger for CCSDK toolkit."""

import json
import sys
from pathlib import Path
from typing import Any

from .models import LogEntry
from .models import LogLevel


class ToolkitLogger:
    """Structured logger with JSON and text output.

    Provides structured logging with:
    - JSON or plaintext output formats
    - Real-time streaming to stdout/stderr
    - File logging support
    - Debug mode with verbose output
    - Parent process log aggregation
    """

    def __init__(
        self,
        output_format: str = "text",
        output_file: Path | None = None,
        debug: bool = False,
        source: str | None = None,
    ):
        """Initialize logger.

        Args:
            output_format: "json" or "text" output format
            output_file: Optional file to write logs to
            debug: Enable debug logging
            source: Default source identifier
        """
        self.output_format = output_format
        self.output_file = output_file
        self.debug_mode = debug  # Renamed to avoid conflict with debug method
        self.source = source
        self.min_level = LogLevel.DEBUG if debug else LogLevel.INFO

    def log(self, level: LogLevel, message: str, metadata: dict[str, Any] | None = None, source: str | None = None):
        """Log a message.

        Args:
            level: Log level
            message: Log message
            metadata: Additional structured data
            source: Source identifier (overrides default)
        """
        # Skip debug logs if not in debug mode
        if level == LogLevel.DEBUG and not self.debug_mode:
            return

        entry = LogEntry(level=level, message=message, metadata=metadata or {}, source=source or self.source)

        # Format output
        if self.output_format == "json":
            output = json.dumps(entry.to_json()) + "\n"
        else:
            output = entry.to_text() + "\n"

        # Write to appropriate stream
        stream = sys.stderr if level in [LogLevel.ERROR, LogLevel.CRITICAL] else sys.stdout
        stream.write(output)
        stream.flush()

        # Write to file if configured
        if self.output_file:
            with open(self.output_file, "a") as f:
                f.write(output)

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.log(LogLevel.DEBUG, message, metadata=kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self.log(LogLevel.INFO, message, metadata=kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.log(LogLevel.WARNING, message, metadata=kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self.log(LogLevel.ERROR, message, metadata=kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.log(LogLevel.CRITICAL, message, metadata=kwargs)

    def stream_action(self, action: str, details: dict | None = None):
        """Log a real-time action for streaming output.

        Args:
            action: Action being performed
            details: Additional action details
        """
        metadata = {"action": action}
        if details:
            metadata.update(details)
        self.info(f"Action: {action}", **metadata)

    def set_level(self, level: LogLevel):
        """Set minimum log level.

        Args:
            level: Minimum level to log
        """
        self.min_level = level

    def child(self, source: str) -> "ToolkitLogger":
        """Create a child logger with a new source.

        Args:
            source: Source identifier for child logger

        Returns:
            New ToolkitLogger instance
        """
        return ToolkitLogger(
            output_format=self.output_format,
            output_file=self.output_file,
            debug=self.debug_mode,
            source=f"{self.source}.{source}" if self.source else source,
        )
