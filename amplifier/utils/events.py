"""
Structured event logging system with JSONL output.

Provides consistent event tracking across all pipeline stages.
"""

import json
import time
from dataclasses import asdict
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from enum import Enum
from pathlib import Path


class EventStatus(str, Enum):
    """Standard event statuses."""

    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CACHED = "cached"
    IN_PROGRESS = "in_progress"


class EventStage(str, Enum):
    """Standard pipeline stages."""

    EXTRACTION = "extraction"
    SYNTHESIS = "synthesis"
    TRIAGE = "triage"
    ANALYSIS = "analysis"
    STORE = "store"
    CACHE = "cache"
    SYSTEM = "system"


@dataclass
class Event:
    """Structured event for pipeline tracking."""

    stage: str
    status: str
    item_id: str | None = None
    fingerprint: str | None = None
    message: str | None = None
    cost: float | None = None
    latency: float | None = None
    error: str | None = None
    metadata: dict | None = None
    timestamp: str | None = None

    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now(tz=UTC).isoformat()


class EventLogger:
    """
    JSONL event logger for observable pipeline execution.

    Emits structured events that can be tailed, queried, and analyzed.
    """

    def __init__(self, event_file: Path | None = None):
        """Initialize event logger with optional custom file."""
        self.event_file = event_file or Path(".data/events/events.jsonl")
        self.event_file.parent.mkdir(parents=True, exist_ok=True)
        self._start_times = {}  # Track timing for latency

    def emit(self, event: Event) -> None:
        """Write an event to the JSONL log."""
        with open(self.event_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")
            f.flush()  # Ensure immediate write for tailing

    def start_operation(
        self, stage: str, item_id: str | None = None, message: str | None = None, metadata: dict | None = None
    ) -> str:
        """
        Log the start of an operation and track timing.

        Returns:
            Operation ID for tracking
        """
        op_id = f"{stage}:{item_id or 'batch'}:{time.time()}"
        self._start_times[op_id] = time.time()

        self.emit(Event(stage=stage, status=EventStatus.STARTED, item_id=item_id, message=message, metadata=metadata))

        return op_id

    def complete_operation(
        self,
        op_id: str,
        status: str = EventStatus.COMPLETED,
        cost: float | None = None,
        message: str | None = None,
        error: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Complete an operation with timing and status."""
        latency = None
        if op_id in self._start_times:
            latency = time.time() - self._start_times[op_id]
            del self._start_times[op_id]

        # Parse op_id to get stage and item_id
        parts = op_id.split(":", 2)
        stage = parts[0] if parts else "unknown"
        item_id = parts[1] if len(parts) > 1 and parts[1] != "batch" else None

        self.emit(
            Event(
                stage=stage,
                status=status,
                item_id=item_id,
                latency=latency,
                cost=cost,
                message=message,
                error=error,
                metadata=metadata,
            )
        )

    def log_cache_hit(self, stage: str, item_id: str, fingerprint: str, metadata: dict | None = None) -> None:
        """Log a cache hit event."""
        self.emit(
            Event(
                stage=stage,
                status=EventStatus.CACHED,
                item_id=item_id,
                fingerprint=fingerprint,
                message="Retrieved from cache",
                metadata=metadata,
            )
        )

    def log_error(self, stage: str, error: str, item_id: str | None = None, metadata: dict | None = None) -> None:
        """Log an error event."""
        self.emit(Event(stage=stage, status=EventStatus.FAILED, item_id=item_id, error=error, metadata=metadata))

    def tail(self, lines: int = 10, follow: bool = False) -> None:
        """
        Tail the event log (for CLI).

        Args:
            lines: Number of recent lines to show
            follow: Continue watching for new events
        """
        if not self.event_file.exists():
            print("No events found")
            return

        # Read last N lines
        with open(self.event_file, encoding="utf-8") as f:
            all_lines = f.readlines()
            for line in all_lines[-lines:]:
                event = json.loads(line)
                self._print_event(event)

        if follow:
            print("\nFollowing events... (Ctrl+C to stop)")
            # This would need a proper implementation with file watching
            # For now, just a placeholder
            import time

            try:
                last_pos = self.event_file.stat().st_size
                while True:
                    time.sleep(0.5)
                    current_size = self.event_file.stat().st_size
                    if current_size > last_pos:
                        with open(self.event_file, encoding="utf-8") as f:
                            f.seek(last_pos)
                            for line in f:
                                event = json.loads(line)
                                self._print_event(event)
                        last_pos = current_size
            except KeyboardInterrupt:
                print("\nStopped following events")

    def _print_event(self, event: dict) -> None:
        """Format and print an event."""
        timestamp = event.get("timestamp", "")[:19]  # Just date and time
        stage = event.get("stage", "unknown")
        status = event.get("status", "")
        item_id = event.get("item_id", "")
        message = event.get("message", "")

        # Color codes for different statuses
        status_colors = {
            "completed": "\033[92m",  # Green
            "failed": "\033[91m",  # Red
            "cached": "\033[93m",  # Yellow
            "started": "\033[94m",  # Blue
        }
        reset = "\033[0m"

        color = status_colors.get(status, "")

        # Build output
        output = f"[{timestamp}] {stage:12} {color}{status:10}{reset}"
        if item_id:
            output += f" {item_id}"
        if message:
            output += f" - {message}"
        if event.get("latency"):
            output += f" ({event['latency']:.2f}s)"
        if event.get("cost"):
            output += f" (${event['cost']:.4f})"

        print(output)

    def get_summary(self, stage: str | None = None) -> dict:
        """
        Get summary statistics from events.

        Args:
            stage: Optional stage filter

        Returns:
            Summary statistics dict
        """
        if not self.event_file.exists():
            return {"error": "No events found"}

        stats = {
            "total_events": 0,
            "by_stage": {},
            "by_status": {},
            "total_cost": 0.0,
            "total_latency": 0.0,
            "errors": [],
        }

        with open(self.event_file, encoding="utf-8") as f:
            for line in f:
                event = json.loads(line)

                # Apply stage filter
                if stage and event.get("stage") != stage:
                    continue

                stats["total_events"] += 1

                # Count by stage
                event_stage = event.get("stage", "unknown")
                stats["by_stage"][event_stage] = stats["by_stage"].get(event_stage, 0) + 1

                # Count by status
                event_status = event.get("status", "unknown")
                stats["by_status"][event_status] = stats["by_status"].get(event_status, 0) + 1

                # Sum costs
                if event.get("cost"):
                    stats["total_cost"] += event["cost"]

                # Sum latency
                if event.get("latency"):
                    stats["total_latency"] += event["latency"]

                # Collect errors
                if event.get("error"):
                    stats["errors"].append(
                        {
                            "stage": event_stage,
                            "item_id": event.get("item_id"),
                            "error": event["error"],
                            "timestamp": event.get("timestamp"),
                        }
                    )

        return stats


# Global logger instance
_logger: EventLogger | None = None


def get_event_logger() -> EventLogger:
    """Get or create the global event logger."""
    global _logger
    if _logger is None:
        _logger = EventLogger()
    return _logger


def log_event(stage: str, status: str, item_id: str | None = None, message: str | None = None, **kwargs) -> None:
    """Convenience function to log an event."""
    logger = get_event_logger()
    logger.emit(Event(stage=stage, status=status, item_id=item_id, message=message, **kwargs))
