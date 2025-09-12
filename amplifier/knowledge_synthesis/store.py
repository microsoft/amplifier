"""
Simple JSON Lines storage for knowledge extractions.
Supports incremental saves and tracking of processed sources.
"""

import json
import logging
from pathlib import Path
from typing import Any

from amplifier.config.paths import paths

logger = logging.getLogger(__name__)


class KnowledgeStore:
    """Simple, incremental knowledge storage using JSON Lines format."""

    def __init__(self, path: Path | None = None):
        """
        Initialize the knowledge store.

        Args:
            path: Path to the JSON Lines file (default: {data_dir}/knowledge/extractions.jsonl)
        """
        self.path = path or paths.data_dir / "knowledge" / "extractions.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

        # Track processed sources in memory for fast lookups
        self._processed_sources: set[str] | None = None

        # Track error statistics
        self.error_stats = {
            "parse_errors": 0,
            "failed_extractions": 0,
            "successful_extractions": 0,
        }

    def save(self, extraction: dict[str, Any]) -> None:
        """
        Append extraction to JSON Lines file.

        Args:
            extraction: Extraction dict with source_id, concepts, relationships, etc.
        """
        if not extraction:
            return

        # Ensure source_id exists
        if "source_id" not in extraction:
            logger.warning("Extraction missing source_id - skipping save")
            return

        # Track success/failure
        if extraction.get("success") is False:
            self.error_stats["failed_extractions"] += 1
            logger.warning(
                f"Saving failed extraction for {extraction.get('source_id')}: "
                f"error_type={extraction.get('error_type')}, "
                f"detail={extraction.get('error_detail', '')[:100]}"
            )
        else:
            self.error_stats["successful_extractions"] += 1

        # Don't save empty extractions
        if not any(
            [
                extraction.get("concepts"),
                extraction.get("relationships"),
                extraction.get("insights"),
                extraction.get("patterns"),
            ]
        ):
            logger.info(f"Empty extraction for {extraction.get('source_id')} - not saving")
            return

        # Append to JSON Lines file
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(extraction, ensure_ascii=False) + "\n")

        # Update processed cache
        if self._processed_sources is not None:
            self._processed_sources.add(extraction["source_id"])

        logger.info(
            f"Saved extraction for {extraction.get('source_id')}: "
            f"{len(extraction.get('concepts', []))} concepts, "
            f"{len(extraction.get('relationships', []))} relationships"
        )

    def load_all(self) -> list[dict[str, Any]]:
        """
        Load all extractions from storage.

        Returns:
            List of extraction dicts
        """
        if not self.path.exists():
            return []

        extractions = []
        with open(self.path, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    extraction = json.loads(line)
                    extractions.append(extraction)
                except json.JSONDecodeError as e:
                    self.error_stats["parse_errors"] += 1
                    logger.warning(f"Invalid JSON on line {line_num}: {e}")
                    continue

        return extractions

    def is_processed(self, source_id: str) -> bool:
        """
        Check if source has already been processed.

        Args:
            source_id: Unique identifier for the source

        Returns:
            True if already processed
        """
        # Load processed sources on first check
        if self._processed_sources is None:
            self._load_processed_sources()

        # Type guard to ensure _processed_sources is not None
        assert self._processed_sources is not None
        return source_id in self._processed_sources

    def _load_processed_sources(self) -> None:
        """Load set of processed source IDs for fast lookups."""
        self._processed_sources = set()

        if not self.path.exists():
            return

        with open(self.path, encoding="utf-8") as f:
            for line in f:
                try:
                    extraction = json.loads(line)
                    if source_id := extraction.get("source_id"):
                        self._processed_sources.add(source_id)
                except json.JSONDecodeError:
                    self.error_stats["parse_errors"] += 1
                    continue

    def get_by_source(self, source_id: str) -> dict[str, Any] | None:
        """
        Get extraction for a specific source.

        Args:
            source_id: Source identifier

        Returns:
            Extraction dict or None if not found
        """
        if not self.path.exists():
            return None

        with open(self.path, encoding="utf-8") as f:
            for line in f:
                try:
                    extraction = json.loads(line)
                    if extraction.get("source_id") == source_id:
                        return extraction
                except json.JSONDecodeError:
                    self.error_stats["parse_errors"] += 1
                    continue

        return None

    def count(self) -> int:
        """Count total number of extractions."""
        if not self.path.exists():
            return 0

        count = 0
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    count += 1
        return count

    def clear(self) -> None:
        """Clear all stored extractions."""
        if self.path.exists():
            self.path.unlink()
        self._processed_sources = None
        self.error_stats = {
            "parse_errors": 0,
            "failed_extractions": 0,
            "successful_extractions": 0,
        }
        logger.info("Cleared all knowledge extractions")

    def get_error_summary(self) -> str:
        """Get a summary of error statistics."""
        total = self.error_stats["successful_extractions"] + self.error_stats["failed_extractions"]
        if total == 0:
            return "No extractions processed yet"

        success_rate = (self.error_stats["successful_extractions"] / total) * 100 if total > 0 else 0
        return (
            f"Success rate: {success_rate:.1f}% "
            f"({self.error_stats['successful_extractions']}/{total} successful, "
            f"{self.error_stats['failed_extractions']} failed, "
            f"{self.error_stats['parse_errors']} parse errors)"
        )
