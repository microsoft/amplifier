"""Hierarchical logging utilities for knowledge extraction.

This module provides clean, tree-structured logging for extraction processes,
showing progress at INFO level while keeping verbose details at DEBUG.
"""

import sys
import time
from typing import Any


class ExtractionLogger:
    """Hierarchical logger for knowledge extraction processes.

    Provides clean tree-structured output with progress indicators.
    """

    def __init__(self):
        """Initialize the extraction logger."""
        self.article_start_time: float | None = None
        self.phase_start_time: float | None = None
        self.current_phase: str | None = None
        self.article_count = 0
        self.total_count = 0

    def start_article(self, current: int, total: int, title: str, article_id: str) -> None:
        """Start processing a new article.

        Args:
            current: Current article number (1-based)
            total: Total number of articles
            title: Article title
            article_id: Article identifier
        """
        self.article_count = current
        self.total_count = total
        self.article_start_time = time.time()

        # Truncate long titles for clean display
        display_title = title[:60] + "..." if len(title) > 60 else title
        print(f"\n[{current}/{total}] {display_title} ({article_id})")

    def log_truncation(self, original_tokens: int, truncated_tokens: int) -> None:
        """Log text truncation if it occurred.

        Args:
            original_tokens: Original token count
            truncated_tokens: Token count after truncation
        """
        if original_tokens > truncated_tokens:
            print(f"  ├─ Truncating: {original_tokens:,} → {truncated_tokens:,} tokens")

    def start_phase(self, phase_name: str) -> None:
        """Start a new extraction phase.

        Args:
            phase_name: Name of the phase (e.g., "Concepts", "SPO")
        """
        self.current_phase = phase_name
        self.phase_start_time = time.time()
        # Use \r for single-line progress update
        sys.stdout.write(f"  ├─ {phase_name}: Extracting...")
        sys.stdout.flush()

    def complete_phase(self, phase_name: str, results: Any, elapsed: float | None = None) -> None:
        """Complete an extraction phase.

        Args:
            phase_name: Name of the phase
            results: Phase results (used to extract summary info)
            elapsed: Optional elapsed time (calculated if not provided)
        """
        if elapsed is None and self.phase_start_time:
            elapsed = time.time() - self.phase_start_time

        # Format result summary based on phase
        if phase_name == "Unified Extraction":
            # Handle unified extraction with concepts and relationships
            if isinstance(results, dict):
                concepts = results.get("concepts", [])
                relationships = results.get("relationships", [])
                concept_count = len(concepts) if concepts else 0
                relation_count = len(relationships) if relationships else 0
                summary = f"{concept_count} concepts, {relation_count} relations"
            else:
                summary = "complete"
        elif phase_name == "Concepts":
            if isinstance(results, list) or hasattr(results, "__len__"):
                summary = f"{len(results)} found"
            else:
                summary = "complete"
        elif phase_name == "SPO":
            if isinstance(results, list):
                summary = f"{len(results)} relations"
            elif hasattr(results, "triples") and isinstance(results.triples, list):
                summary = f"{len(results.triples)} relations"
            else:
                summary = "complete"
        else:
            summary = "complete"

        # Clear the line and write the complete status
        sys.stdout.write("\r")
        sys.stdout.write(" " * 80)  # Clear any remaining text
        sys.stdout.write("\r")

        elapsed_str = f"{elapsed:.1f}s" if elapsed else ""
        print(f"  ├─ {phase_name}: Done ({summary}, {elapsed_str})")

    def complete_article(self, status=None) -> None:
        """Complete processing of the current article.

        Args:
            status: Optional ArticleProcessingStatus to show failure details
        """
        if self.article_start_time:
            total_elapsed = time.time() - self.article_start_time
            base_msg = f"  └─ Complete ({total_elapsed:.1f}s total)"
        else:
            base_msg = "  └─ Complete"

        # Add partial failure warning if status provided
        if status and hasattr(status, "processor_results"):
            failed_processors = [name for name, result in status.processor_results.items() if result.status == "failed"]
            if failed_processors:
                print(base_msg)
                print(f"     ⚠ Partial: {', '.join(failed_processors)} failed")
            else:
                # All processors succeeded
                print(base_msg)
                print("     ✓ Complete: all processors succeeded")
        else:
            print(base_msg)

    def log_summary(self, concepts_count: int, relations_count: int) -> None:
        """Log a summary after completing an article.

        Args:
            concepts_count: Number of concepts extracted
            relations_count: Number of relations extracted
        """
        if self.article_start_time:
            total_elapsed = time.time() - self.article_start_time
            print(f"  └─ Complete: {concepts_count} concepts, {relations_count} relations ({total_elapsed:.1f}s total)")
        else:
            print(f"  └─ Complete: {concepts_count} concepts, {relations_count} relations")
