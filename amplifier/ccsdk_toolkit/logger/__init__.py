"""
Structured logging and monitoring for CCSDK toolkit
"""

import json
import logging
import sys
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from typing import Optional
from typing import TextIO
from typing import Union

from rich.console import Console
from rich.logging import RichHandler


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class LogFormat(str, Enum):
    JSON = "json"
    PLAIN = "plain"
    RICH = "rich"


@dataclass
class LogEvent:
    """Structured log event"""

    timestamp: str
    level: str
    message: str
    context: dict[str, Any]
    session_id: str | None = None
    turn_number: int | None = None


class ToolkitLogger:
    """
    Structured logging for CCSDK toolkit.

    Supports JSON, plaintext, and rich console output.
    """

    def __init__(
        self,
        name: str = "ccsdk_toolkit",
        level: LogLevel = LogLevel.INFO,
        format: LogFormat = LogFormat.PLAIN,
        output_file: Path | None = None,
        stream: TextIO | None = None,
        enable_notifications: bool = False,
    ):
        self.name = name
        self.level = level
        self.format = format
        self.output_file = output_file
        self.stream = stream or sys.stdout
        self.session_id: str | None = None
        self.turn_number = 0
        self.enable_notifications = enable_notifications

        # Configure base logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.value))
        self.logger.handlers.clear()

        # Add appropriate handler based on format
        if format == LogFormat.RICH:
            console = Console(file=self.stream)
            handler = RichHandler(console=console, rich_tracebacks=True)
            handler.setFormatter(logging.Formatter("%(message)s"))
        else:
            handler = logging.StreamHandler(self.stream)
            if format == LogFormat.JSON:
                handler.setFormatter(logging.Formatter("%(message)s"))
            else:
                handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        self.logger.addHandler(handler)

        # Add file handler if specified
        if output_file:
            file_handler = logging.FileHandler(output_file, encoding="utf-8")
            if format == LogFormat.JSON:
                file_handler.setFormatter(logging.Formatter("%(message)s"))
            else:
                file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
            self.logger.addHandler(file_handler)

    def set_session(self, session_id: str) -> None:
        """Set current session ID for log context"""
        self.session_id = session_id
        self.turn_number = 0

    def increment_turn(self) -> None:
        """Increment turn counter"""
        self.turn_number += 1

    def _format_message(self, event: LogEvent) -> str:
        """Format log message based on configured format"""
        if self.format == LogFormat.JSON:
            return json.dumps(asdict(event), ensure_ascii=False)
        # Plain or rich format
        msg = event.message
        if event.session_id:
            msg = f"[{event.session_id}] {msg}"
        if event.turn_number:
            msg = f"[Turn {event.turn_number}] {msg}"
        if event.context:
            msg = f"{msg} | {json.dumps(event.context)}"
        return msg

    def _log(self, level: str, message: str, context: dict[str, Any] | None = None) -> None:
        """Internal logging method"""
        event = LogEvent(
            timestamp=datetime.now().isoformat(),
            level=level,
            message=message,
            context=context or {},
            session_id=self.session_id,
            turn_number=self.turn_number if self.turn_number > 0 else None,
        )

        formatted = self._format_message(event)
        log_method = getattr(self.logger, level.lower())
        log_method(formatted)

    def debug(self, message: str, **context: Any) -> None:
        """Log debug message"""
        self._log(LogLevel.DEBUG, message, context)

    def info(self, message: str, **context: Any) -> None:
        """Log info message"""
        self._log(LogLevel.INFO, message, context)

    def warning(self, message: str, **context: Any) -> None:
        """Log warning message"""
        self._log(LogLevel.WARNING, message, context)

    def error(self, message: str, error: Exception | None = None, **context: Any) -> None:
        """Log error message with optional exception"""
        if error:
            context["error_type"] = type(error).__name__
            context["error_message"] = str(error)
        self._log(LogLevel.ERROR, message, context)

    def log_query(self, prompt: str, response: str | None = None) -> None:
        """Log a query and optionally its response"""
        self.info(
            "Query executed",
            prompt=prompt[:500] if len(prompt) > 500 else prompt,
            response_preview=response[:500] if response and len(response) > 500 else response,
            has_response=response is not None,
        )

    def log_tool_use(self, tool_name: str, arguments: dict[str, Any], result: Any = None) -> None:
        """Log tool invocation"""
        self.debug(
            f"Tool invoked: {tool_name}",
            tool=tool_name,
            arguments=arguments,
            has_result=result is not None,
        )

    def stream_progress(self, message: str, progress: float | None = None) -> None:
        """Stream a progress update"""
        context = {}
        if progress is not None:
            context["progress"] = progress
        self.info(f"Progress: {message}", **context)

    def log_session_start(self, session_id: str, config: dict[str, Any], workspace: Path | None = None) -> None:
        """Log session start with configuration"""
        self.set_session(session_id)
        self.info(
            "Session started",
            session_id=session_id,
            config_summary={
                "max_turns": config.get("max_turns"),
                "model": config.get("model"),
                "agents": len(config.get("agents", [])),
            },
            workspace=str(workspace) if workspace else None,
        )

    def log_session_end(
        self,
        session_id: str,
        duration_ms: int,
        total_cost: float,
        turns_completed: int,
        status: str = "completed",
    ) -> None:
        """Log session end with summary"""
        self.info(
            "Session ended",
            session_id=session_id,
            duration_ms=duration_ms,
            total_cost=total_cost,
            turns_completed=turns_completed,
            status=status,
        )

    def stage_start(self, stage_name: str, message: str | None = None) -> None:
        """Mark the start of a processing stage"""
        if message:
            self.info(f"Starting stage: {stage_name} - {message}", stage=stage_name)
        else:
            self.info(f"Starting stage: {stage_name}", stage=stage_name)

    def stage_complete(self, stage_name: str, message: str, **kwargs: Any) -> None:
        """Mark stage completion (no longer sends notifications)"""
        # Log the completion
        context = {"stage": stage_name, **kwargs}
        self.info(f"Stage complete: {stage_name} - {message}", **context)

        # No longer send progress notifications - only final completion

    def task_complete(self, message: str, duration: float | None = None, success: bool = True) -> None:
        """Mark task completion and send final notification"""
        # Log the completion
        context: dict[str, Any] = {"success": success}
        if duration:
            context["duration_seconds"] = round(duration, 2)

        if success:
            self.info(f"Task complete: {message}", **context)
        else:
            self.error(f"Task failed: {message}", error=None, **context)

        # Send notification if enabled
        if self.enable_notifications:
            try:
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


def create_logger(
    name: str | None = None,
    level: Union[str, LogLevel] = LogLevel.INFO,
    format: Union[str, LogFormat] = LogFormat.PLAIN,
    output_file: Path | None = None,
    enable_notifications: bool = False,
) -> ToolkitLogger:
    """
    Create a configured logger instance.

    Args:
        name: Logger name (defaults to ccsdk_toolkit)
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        format: Output format (json, plain, rich)
        output_file: Optional file path for log output

    Returns:
        Configured ToolkitLogger instance
    """
    if isinstance(level, str):
        level = LogLevel(level.upper())
    if isinstance(format, str):
        format = LogFormat(format.lower())

    return ToolkitLogger(
        name=name or "ccsdk_toolkit",
        level=level,
        format=format,
        output_file=output_file,
        enable_notifications=enable_notifications,
    )


__all__ = [
    "ToolkitLogger",
    "create_logger",
    "LogLevel",
    "LogFormat",
    "LogEvent",
]
