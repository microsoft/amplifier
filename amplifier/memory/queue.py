"""JSONL-based extraction queue for deferred memory processing.

Simple file-based queue using JSONL format. Each line is a queued extraction task
that will be processed asynchronously by the extraction worker.
"""

import json
import logging
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

QUEUE_FILE = Path(".data/extraction_queue.jsonl")


@dataclass
class QueuedExtraction:
    """Extraction task queued for asynchronous processing."""

    session_id: str
    transcript_path: str
    timestamp: str
    hook_event: str
    retries: int = 0
    last_error: str | None = None


def queue_extraction(item: QueuedExtraction) -> None:
    """Append extraction task to queue file.

    Args:
        item: Extraction task to queue

    Non-blocking operation that appends to JSONL file.
    Creates directory structure if needed.
    """
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)

    with QUEUE_FILE.open("a") as f:
        f.write(json.dumps(asdict(item)) + "\n")

    logger.info(f"Queued extraction for session {item.session_id}")


def get_queued_items() -> list[QueuedExtraction]:
    """Read all queued extraction tasks.

    Returns:
        List of queued items, empty if queue file doesn't exist
    """
    if not QUEUE_FILE.exists():
        return []

    items = []
    with QUEUE_FILE.open() as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                items.append(QueuedExtraction(**data))

    return items


def remove_from_queue(session_id: str) -> None:
    """Remove item from queue by session_id.

    Args:
        session_id: Session ID to remove

    Rewrites queue file without the matching item.
    """
    if not QUEUE_FILE.exists():
        return

    items = get_queued_items()
    remaining = [item for item in items if item.session_id != session_id]

    with QUEUE_FILE.open("w") as f:
        for item in remaining:
            f.write(json.dumps(asdict(item)) + "\n")

    logger.info(f"Removed session {session_id} from queue")


def clear_queue() -> None:
    """Delete queue file.

    For testing and maintenance.
    """
    if QUEUE_FILE.exists():
        QUEUE_FILE.unlink()
        logger.info("Cleared extraction queue")
