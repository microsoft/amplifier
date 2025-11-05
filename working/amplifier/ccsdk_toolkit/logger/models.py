"""Log entry models for CCSDK toolkit."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel
from pydantic import Field


class LogLevel(str, Enum):
    """Log levels for the toolkit."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogEntry(BaseModel):
    """Structured log entry.

    Attributes:
        timestamp: When the log was created
        level: Log level
        message: Log message
        metadata: Additional structured data
        source: Source module/function
    """

    timestamp: datetime = Field(default_factory=datetime.now)
    level: LogLevel = Field(default=LogLevel.INFO)
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    source: str | None = Field(default=None)

    def to_json(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "message": self.message,
            "metadata": self.metadata,
            "source": self.source,
        }

    def to_text(self) -> str:
        """Convert to text format."""
        parts = [
            self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            f"[{self.level.value}]",
        ]
        if self.source:
            parts.append(f"[{self.source}]")
        parts.append(self.message)

        result = " ".join(parts)
        if self.metadata:
            result += f" | {self.metadata}"
        return result

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-01-01T10:00:00",
                "level": "INFO",
                "message": "Processing started",
                "metadata": {"task": "analysis", "items": 100},
                "source": "processor",
            }
        }
