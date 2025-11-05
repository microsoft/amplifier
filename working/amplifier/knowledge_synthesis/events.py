"""
Lightweight event emitter for the knowledge synthesis pipeline.

Writes newline-delimited JSON events to a fixed path for easy tailing/replay.
Follows incremental processing principles: append-only, resilient, minimal.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from amplifier.config.paths import paths

logger = logging.getLogger(__name__)

DEFAULT_EVENTS_PATH = paths.data_dir / "knowledge" / "events.jsonl"


@dataclass
class Event:
    """A single pipeline event."""

    timestamp: float
    event: str
    source_id: str | None = None
    stage: str | None = None
    data: dict[str, Any] | None = None


class EventEmitter:
    """Append-only JSONL event emitter."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or DEFAULT_EVENTS_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def emit(
        self,
        event: str,
        *,
        source_id: str | None = None,
        stage: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        rec = Event(timestamp=time.time(), event=event, source_id=source_id, stage=stage, data=data)

        # Retry logic for WSL I/O errors
        max_retries = 3
        retry_delay = 0.1  # Start with 100ms

        for attempt in range(max_retries):
            try:
                with open(self.path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(asdict(rec), ensure_ascii=False) + "\n")
                    f.flush()  # Ensure write is committed
                return  # Success
            except OSError as e:
                if e.errno == 5 and attempt < max_retries - 1:  # I/O error, not last attempt
                    if attempt == 0:  # Log warning on first retry
                        logger.warning(
                            f"File I/O error writing to {self.path} - retrying. "
                            "This may be due to cloud-synced files (OneDrive, Dropbox, etc.). "
                            "If using cloud sync, consider enabling 'Always keep on this device' "
                            f"for the data folder: {self.path.parent}"
                        )
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise  # Re-raise on last attempt or different error

    def tail(self, n: int = 50, event_filter: str | None = None) -> list[Event]:
        """Return the last N events, optionally filtered by event type."""
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()
        selected: list[Event] = []
        for raw in lines[-n:]:
            if not raw.strip():
                continue
            try:
                obj = json.loads(raw)
                if event_filter and obj.get("event") != event_filter:
                    continue
                selected.append(
                    Event(
                        timestamp=float(obj.get("timestamp", 0.0)),
                        event=str(obj.get("event", "")),
                        source_id=obj.get("source_id"),
                        stage=obj.get("stage"),
                        data=obj.get("data"),
                    )
                )
            except json.JSONDecodeError:
                continue
        return selected
