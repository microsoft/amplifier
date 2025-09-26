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
    - Optional desktop notifications for stage/task completion
    """

    def __init__(
        self,
        output_format: str = "text",
        output_file: Path | None = None,
        debug: bool = False,
        source: str | None = None,
        enable_notifications: bool = False,
    ):
        """Initialize logger.

        Args:
            output_format: "json" or "text" output format
            output_file: Optional file to write logs to
            debug: Enable debug logging
            source: Default source identifier
            enable_notifications: Enable desktop notifications for stage/task completion
        """
        self.output_format = output_format
        self.output_file = output_file
        self.debug_mode = debug  # Renamed to avoid conflict with debug method
        self.source = source
        self.min_level = LogLevel.DEBUG if debug else LogLevel.INFO
        self.enable_notifications = enable_notifications

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
            enable_notifications=self.enable_notifications,
        )

    def stage_start(self, stage_name: str, message: str | None = None):
        """Mark the start of a processing stage.

        Args:
            stage_name: Name of the stage
            message: Optional message to log
        """
        if message:
            self.info(f"Starting stage: {stage_name} - {message}", stage=stage_name)
        else:
            self.info(f"Starting stage: {stage_name}", stage=stage_name)

    def stage_complete(self, stage_name: str, message: str, **kwargs):
        """Mark stage completion (no longer sends notifications).

        Args:
            stage_name: Name of the completed stage
            message: Completion message
            **kwargs: Additional metadata to include
        """
        # Log the completion
        metadata = {"stage": stage_name, **kwargs}
        self.info(f"Stage complete: {stage_name} - {message}", **metadata)

        # No longer send progress notifications - only final completion

    def task_complete(self, message: str, duration: float | None = None, success: bool = True):
        """Mark task completion and send final notification.

        Args:
            message: Completion message
            duration: Total task duration in seconds (ignored for notifications)
            success: Whether the task completed successfully
        """
        # Log the completion
        metadata: dict[str, Any] = {"success": success}
        if duration:
            metadata["duration_seconds"] = round(duration, 2)

        if success:
            self.info(f"Task complete: {message}", **metadata)
        else:
            self.error(f"Task failed: {message}", **metadata)

        # Send notification if enabled
        if self.enable_notifications:
            try:
                # Lazy import to avoid dependency when not needed
                import os

                from amplifier.utils.notifications import send_notification

                send_notification(
                    title="Amplifier",
                    message=message,
                    cwd=os.getcwd(),
                )
            except ImportError:
                self.debug("Notifications not available - amplifier.utils.notifications not found")
            except Exception as e:
                self.debug(f"Failed to send notification: {e}")
