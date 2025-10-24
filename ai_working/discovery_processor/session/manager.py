from typing import List, Dict, Tuple, Optional
"""Session manager for tracking Discovery content processing progress."""

import logging
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from amplifier.ccsdk_toolkit.defensive.file_io import read_json_with_retry, write_json_with_retry

from ..models import ProcessingResult, ProcessingStatus, SessionState

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages processing session state for resume capability.

    Tracks which content items have been processed, stores results,
    and enables resuming interrupted processing sessions.
    """

    def __init__(self, session_file: Optional[Path] = None, session_id: Optional[str] = None):
        """Initialize session manager.

        Args:
            session_file: Path to session state file (default: discovery_session.json)
            session_id: Unique session ID (generates new if not provided)
        """
        self.session_file = session_file or Path("discovery_session.json")
        self.session_id = session_id or str(uuid4())
        self.state = self._load_state()

    def _load_state(self) -> SessionState:
        """Load existing session state or create new."""
        if self.session_file.exists():
            try:
                data = read_json_with_retry(self.session_file)

                # Check if this is our session
                if data.get("session_id") == self.session_id:
                    logger.info(f"Resuming session {self.session_id}: {len(data['processed_items'])} items already processed")

                    # Reconstruct ProcessingResult objects
                    results = []
                    for r in data.get("results", []):
                        results.append(
                            ProcessingResult(
                                content_id=r["content_id"],
                                status=ProcessingStatus(r["status"]),
                                analysis=r.get("analysis", ""),
                                extracted_text=r.get("extracted_text", ""),
                                insights=r.get("insights", []),
                                design_elements=r.get("design_elements", {}),
                                warnings=r.get("warnings", []),
                                error_message=r.get("error_message"),
                                processing_time_ms=r.get("processing_time_ms"),
                                processed_at=datetime.fromisoformat(r["processed_at"]),
                            )
                        )

                    return SessionState(
                        session_id=self.session_id,
                        processed_items=data.get("processed_items", []),
                        results=results,
                        failed_items=[(f[0], f[1]) for f in data.get("failed_items", [])],
                        total_items=data.get("total_items", 0),
                        current_item=data.get("current_item"),
                        started_at=datetime.fromisoformat(data["started_at"]),
                        updated_at=datetime.fromisoformat(data.get("updated_at", data["started_at"])),
                    )

            except Exception as e:
                logger.warning(f"Could not load session state: {e}")

        # Create new session
        logger.info(f"Starting new session: {self.session_id}")
        return SessionState(session_id=self.session_id)

    def _save_state(self):
        """Save current state to disk."""
        try:
            self.state.updated_at = datetime.now()

            data = {
                "session_id": self.state.session_id,
                "processed_items": self.state.processed_items,
                "results": [
                    {
                        "content_id": r.content_id,
                        "status": r.status.value,
                        "analysis": r.analysis,
                        "extracted_text": r.extracted_text,
                        "insights": r.insights,
                        "design_elements": r.design_elements,
                        "warnings": r.warnings,
                        "error_message": r.error_message,
                        "processing_time_ms": r.processing_time_ms,
                        "processed_at": r.processed_at.isoformat(),
                    }
                    for r in self.state.results
                ],
                "failed_items": self.state.failed_items,
                "total_items": self.state.total_items,
                "current_item": self.state.current_item,
                "started_at": self.state.started_at.isoformat(),
                "updated_at": self.state.updated_at.isoformat(),
            }

            write_json_with_retry(data, self.session_file)
            logger.debug(f"Session state saved: {len(self.state.processed_items)}/{self.state.total_items} processed")

        except Exception as e:
            logger.error(f"Failed to save session state: {e}")

    def is_processed(self, content_id: str) -> bool:
        """Check if a content item has already been processed.

        Args:
            content_id: Content ID to check

        Returns:
            True if item was already processed
        """
        return content_id in self.state.processed_items

    def start_item(self, content_id: str):
        """Mark a content item as being processed.

        Args:
            content_id: ID of content item being started
        """
        self.state.current_item = content_id
        self._save_state()
        logger.info(f"Started processing: {content_id}")

    def complete_item(self, result: ProcessingResult):
        """Mark a content item as successfully processed.

        Args:
            result: Processing result to store
        """
        if result.content_id not in self.state.processed_items:
            self.state.processed_items.append(result.content_id)

        self.state.results.append(result)
        self.state.current_item = None
        self._save_state()

        # Log progress
        progress = len(self.state.processed_items)
        total = self.state.total_items
        percent = (progress / total * 100) if total > 0 else 0
        logger.info(f"Completed: {result.content_id} | Progress: {progress}/{total} ({percent:.1f}%)")

    def fail_item(self, content_id: str, error: str):
        """Mark a content item as failed.

        Args:
            content_id: ID of content item that failed
            error: Error message
        """
        if content_id not in self.state.processed_items:
            self.state.processed_items.append(content_id)

        self.state.failed_items.append((content_id, error))
        self.state.current_item = None
        self._save_state()

        logger.error(f"Failed: {content_id} | Error: {error}")

    def set_total_items(self, count: int):
        """Set the total number of items to process.

        Args:
            count: Total item count
        """
        self.state.total_items = count
        self._save_state()
        logger.info(f"Session setup: {count} items to process")

    def get_results(self) -> List[ProcessingResult]:
        """Get all successful processing results.

        Returns:
            List of processing results
        """
        return [r for r in self.state.results if r.status == ProcessingStatus.COMPLETED]

    def get_failed(self) -> List[Tuple[str, str]]:
        """Get all failed items.

        Returns:
            List of (content_id, error_message) tuples
        """
        return self.state.failed_items

    def get_summary(self) -> dict:
        """Get session summary statistics.

        Returns:
            Summary dictionary with counts and percentages
        """
        successful = len([r for r in self.state.results if r.status == ProcessingStatus.COMPLETED])
        failed = len(self.state.failed_items)

        return {
            "session_id": self.state.session_id,
            "total_items": self.state.total_items,
            "processed": len(self.state.processed_items),
            "successful": successful,
            "failed": failed,
            "completion_percent": (len(self.state.processed_items) / self.state.total_items * 100)
            if self.state.total_items > 0
            else 0,
            "started_at": self.state.started_at.isoformat(),
            "updated_at": self.state.updated_at.isoformat(),
        }

    def clear(self):
        """Clear session state and delete session file."""
        self.state = SessionState(session_id=self.session_id)
        if self.session_file.exists():
            self.session_file.unlink()
        logger.info(f"Session {self.session_id} cleared")
