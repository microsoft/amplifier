"""
Resilient Knowledge Mining System

Purpose: Provide failure-resilient knowledge mining with partial result handling
Contract: Process articles with graceful degradation and partial result saving
"""

import asyncio
import json
import logging
import time
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from amplifier.config.paths import paths
from amplifier.content_loader import ContentItem
from amplifier.knowledge_integration import UnifiedKnowledgeExtractor
from amplifier.utils.logging_utils import ExtractionLogger
from amplifier.utils.token_utils import truncate_to_tokens

logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class ProcessorResult:
    """Result from a single processor/extractor."""

    processor_name: str  # e.g., "concepts", "relationships", "insights"
    status: str  # "success", "failed", "empty", "skipped"
    error_message: str | None = None
    retry_count: int = 0
    extracted_count: int = 0


@dataclass
class ArticleProcessingStatus:
    """Complete processing status for a single article."""

    article_id: str
    title: str
    last_processed: datetime
    processor_results: dict[str, ProcessorResult]
    is_complete: bool  # All processors succeeded or explicitly marked empty

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "article_id": self.article_id,
            "title": self.title,
            "last_processed": self.last_processed.isoformat(),
            "processor_results": {name: asdict(result) for name, result in self.processor_results.items()},
            "is_complete": self.is_complete,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ArticleProcessingStatus":
        """Create from dictionary."""
        return cls(
            article_id=data["article_id"],
            title=data["title"],
            last_processed=datetime.fromisoformat(data["last_processed"]),
            processor_results={
                name: ProcessorResult(**result_data) for name, result_data in data["processor_results"].items()
            },
            is_complete=data["is_complete"],
        )


# ============================================================================
# STATUS STORAGE
# ============================================================================


class ProcessingStatusStore:
    """Simple JSON-based status storage with incremental saves."""

    def __init__(self, status_dir: Path | None = None):
        """Initialize status store.

        Args:
            status_dir: Directory for status files (default: data_dir/processing_status)
        """
        self.status_dir = status_dir or paths.data_dir / "processing_status"
        self.status_dir.mkdir(parents=True, exist_ok=True)

    def save_status(self, status: ArticleProcessingStatus) -> None:
        """Save status for a single article.

        Args:
            status: Processing status to save
        """
        # Use article_id as filename (sanitized)
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in status.article_id)
        status_file = self.status_dir / f"{safe_id}.json"

        # Save atomically
        status_file.write_text(json.dumps(status.to_dict(), indent=2))

    def load_status(self, article_id: str) -> ArticleProcessingStatus | None:
        """Load status for a single article.

        Args:
            article_id: Article ID to load

        Returns:
            Processing status or None if not found
        """
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in article_id)
        status_file = self.status_dir / f"{safe_id}.json"

        if not status_file.exists():
            return None

        try:
            data = json.loads(status_file.read_text())
            return ArticleProcessingStatus.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to load status for {article_id}: {e}")
            return None

    def get_all_statuses(self) -> list[ArticleProcessingStatus]:
        """Get all processing statuses.

        Returns:
            List of all processing statuses
        """
        statuses = []
        for status_file in self.status_dir.glob("*.json"):
            try:
                data = json.loads(status_file.read_text())
                statuses.append(ArticleProcessingStatus.from_dict(data))
            except Exception as e:
                logger.warning(f"Failed to load status from {status_file}: {e}")

        return statuses


# ============================================================================
# RESILIENT KNOWLEDGE MINER
# ============================================================================


class ResilientKnowledgeMiner:
    """Failure-resilient knowledge mining with partial result handling."""

    def __init__(
        self,
        extractor: UnifiedKnowledgeExtractor | None = None,
        status_store: ProcessingStatusStore | None = None,
        use_focused_extractors: bool = True,
    ):
        """Initialize resilient miner.

        Args:
            extractor: Unified knowledge extractor (old method)
            status_store: Processing status store
            use_focused_extractors: Whether to use focused extractors (new method)
        """
        self.extractor = extractor
        self.status_store = status_store or ProcessingStatusStore()
        self.extraction_logger = ExtractionLogger()
        self.use_focused_extractors = use_focused_extractors
        self.focused_extractor = None

        if use_focused_extractors:
            try:
                from amplifier.knowledge_synthesis.focused_extractors import FocusedKnowledgeExtractor

                self.focused_extractor = FocusedKnowledgeExtractor()
                logger.info("Using focused extractors for knowledge mining")
            except ImportError:
                logger.warning("Focused extractors not available, falling back to unified extractor")
                self.use_focused_extractors = False

        # Statistics tracking
        self.stats = {
            "total_processed": 0,
            "fully_successful": 0,
            "partially_successful": 0,
            "failed": 0,
            "total_concepts": 0,
            "total_relationships": 0,
            "total_insights": 0,
            "total_patterns": 0,
        }

    async def process_article_with_logging(
        self, article: ContentItem, current: int, total: int
    ) -> ArticleProcessingStatus:
        """Process a single article with detailed logging.

        Args:
            article: Content item to process
            current: Current article number (1-based)
            total: Total number of articles

        Returns:
            Processing status with results from all processors
        """
        # Start article processing with clean logging
        self.extraction_logger.start_article(current, total, article.title, article.content_id)

        # Truncate content to token limit
        truncated_content, original_tokens, final_tokens = truncate_to_tokens(article.content)
        self.extraction_logger.log_truncation(original_tokens, final_tokens)

        # Load existing status or create new
        status = self.status_store.load_status(article.content_id)
        if status is None:
            status = ArticleProcessingStatus(
                article_id=article.content_id,
                title=article.title,
                last_processed=datetime.now(),
                processor_results={},
                is_complete=False,
            )

        # Process extraction based on mode
        extraction_data = {}
        concept_count = 0
        relation_count = 0

        try:
            if self.use_focused_extractors and self.focused_extractor:
                # Use focused extractors for better quality
                import sys
                import threading

                # Show initial extraction status
                sys.stdout.write(
                    "├─ Running 4 extractors in parallel (concepts, relationships, insights, patterns)...\n"
                )
                sys.stdout.flush()

                # Track extraction start time
                extraction_start = time.time()

                # Create a simple progress indicator thread
                stop_progress = threading.Event()
                progress_line = [""]
                completed_extractors = []
                extractor_names = ["concepts", "relationships", "insights", "patterns"]

                def show_progress():
                    """Show a simple animated progress indicator with extractor status"""
                    spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
                    spinner_idx = 0
                    last_update = time.time()
                    prev_len = 0  # Track previous message length

                    while not stop_progress.is_set():
                        current_time = time.time()
                        elapsed = current_time - extraction_start

                        # Update spinner every 0.3 seconds
                        if current_time - last_update >= 0.3:
                            # Build status of extractors
                            active_extractors = [e for e in extractor_names if e not in completed_extractors]

                            if active_extractors:
                                status = f"Extracting: {', '.join(active_extractors)}"
                            else:
                                status = "Finalizing results"

                            # Add completed count if any
                            if completed_extractors:
                                status += f" (✓ {len(completed_extractors)}/4 complete)"

                            message = f"├─ {spinner[spinner_idx]} {status} ({elapsed:.0f}s)"

                            # Clear the line first using the max of previous and current message length
                            # This ensures we clear any leftover characters from longer messages
                            clear_len = max(prev_len, len(message))
                            sys.stdout.write("\r" + " " * clear_len + "\r")

                            # Now write the new message
                            sys.stdout.write(message)
                            sys.stdout.flush()

                            prev_len = len(message)
                            progress_line[0] = message  # Store without \r for length calculation
                            spinner_idx = (spinner_idx + 1) % len(spinner)
                            last_update = current_time

                        stop_progress.wait(0.1)  # Check every 100ms

                    # Clear the progress line when done
                    sys.stdout.write("\r" + " " * prev_len + "\r")
                    sys.stdout.flush()

                # Start progress indicator in background
                progress_thread = threading.Thread(target=show_progress, daemon=True)
                progress_thread.start()

                # Run focused extractors (they run in parallel internally)
                # We'll wrap this to track individual completions
                async def extract_with_tracking():
                    """Wrapper to track which extractors complete"""
                    if not self.focused_extractor:
                        # Fallback to regular extract_all if focused_extractor is None
                        return {}

                    # Start all extractors in parallel
                    tasks = {
                        "concepts": asyncio.create_task(
                            self.focused_extractor.concept_extractor.extract(truncated_content, article.title)
                        ),
                        "relationships": asyncio.create_task(
                            self.focused_extractor.relationship_extractor.extract(truncated_content, article.title)
                        ),
                        "insights": asyncio.create_task(
                            self.focused_extractor.insight_extractor.extract(truncated_content, article.title)
                        ),
                        "patterns": asyncio.create_task(
                            self.focused_extractor.pattern_extractor.extract(truncated_content, article.title)
                        ),
                    }

                    # Import here to avoid circular dependencies
                    from amplifier.knowledge_synthesis.focused_extractors import FocusedExtractionResult

                    results = {}

                    # Create a mapping of tasks to names for tracking
                    task_to_name = {task: name for name, task in tasks.items()}

                    # Use asyncio.as_completed to track completions as they happen
                    for coro in asyncio.as_completed(tasks.values()):
                        try:
                            result = await coro
                            # Find which task completed
                            for task in tasks.values():
                                if task.done() and task in task_to_name:
                                    name = task_to_name[task]
                                    if name not in completed_extractors:
                                        results[name] = result
                                        completed_extractors.append(name)
                                        # Log individual completion
                                        elapsed = time.time() - extraction_start
                                        # Clear current line and show completion
                                        sys.stdout.write("\r" + " " * 100 + "\r")  # Clear line
                                        sys.stdout.write(f"├─ ✓ {name} completed ({elapsed:.1f}s)\n")
                                        sys.stdout.flush()
                                        del task_to_name[task]  # Remove from mapping
                                        break
                        except Exception as e:
                            # Find which task failed
                            for task in tasks.values():
                                if task.done() and task in task_to_name:
                                    name = task_to_name[task]
                                    if name not in completed_extractors:
                                        logger.error(f"Extraction {name} failed: {e}")
                                        results[name] = FocusedExtractionResult(
                                            extraction_type=name, data=[], extraction_time=0.0, error=str(e)
                                        )
                                        completed_extractors.append(name)
                                        # Log failure
                                        elapsed = time.time() - extraction_start
                                        sys.stdout.write("\r" + " " * 100 + "\r")  # Clear line
                                        sys.stdout.write(f"├─ ✗ {name} failed ({elapsed:.1f}s)\n")
                                        sys.stdout.flush()
                                        del task_to_name[task]  # Remove from mapping
                                        break

                    return results

                extraction_results = await extract_with_tracking()

                # Stop the progress indicator
                stop_progress.set()
                progress_thread.join(timeout=0.5)  # Wait briefly for thread to clean up

                # Process and display results for each extractor
                # Process concepts
                concept_result = extraction_results.get("concepts")
                if concept_result and not concept_result.error:
                    concepts = concept_result.data
                    concept_count = len(concepts)
                    extraction_data["concepts"] = concepts
                    sys.stdout.write(
                        f"├─ Concepts: Done ({concept_count} found, {concept_result.extraction_time:.1f}s)\n"
                    )
                    status.processor_results["concepts"] = ProcessorResult(
                        processor_name="concepts",
                        status="success" if concepts else "empty",
                        extracted_count=concept_count,
                    )
                else:
                    sys.stdout.write("├─ Concepts: Failed\n")
                    status.processor_results["concepts"] = ProcessorResult(
                        processor_name="concepts",
                        status="failed",
                        error_message=concept_result.error if concept_result else "Unknown error",
                    )

                # Process relationships
                relationship_result = extraction_results.get("relationships")
                if relationship_result and not relationship_result.error:
                    relationships = relationship_result.data
                    relation_count = len(relationships)
                    extraction_data["relationships"] = relationships
                    sys.stdout.write(
                        f"├─ Relationships: Done ({relation_count} found, {relationship_result.extraction_time:.1f}s)\n"
                    )
                    status.processor_results["relationships"] = ProcessorResult(
                        processor_name="relationships",
                        status="success" if relationships else "empty",
                        extracted_count=relation_count,
                    )
                else:
                    sys.stdout.write("├─ Relationships: Failed\n")
                    status.processor_results["relationships"] = ProcessorResult(
                        processor_name="relationships",
                        status="failed",
                        error_message=relationship_result.error if relationship_result else "Unknown error",
                    )

                # Process insights
                insight_result = extraction_results.get("insights")
                if insight_result and not insight_result.error:
                    insights = insight_result.data
                    insight_count = len(insights)
                    extraction_data["insights"] = insights
                    sys.stdout.write(
                        f"├─ Insights: Done ({insight_count} found, {insight_result.extraction_time:.1f}s)\n"
                    )
                    status.processor_results["insights"] = ProcessorResult(
                        processor_name="insights",
                        status="success" if insights else "empty",
                        extracted_count=insight_count,
                    )
                else:
                    sys.stdout.write("├─ Insights: Failed\n")
                    status.processor_results["insights"] = ProcessorResult(
                        processor_name="insights",
                        status="failed",
                        error_message=insight_result.error if insight_result else "Unknown error",
                    )

                # Process patterns
                pattern_result = extraction_results.get("patterns")
                if pattern_result and not pattern_result.error:
                    patterns = pattern_result.data
                    pattern_count = len(patterns)
                    extraction_data["patterns"] = patterns
                    sys.stdout.write(
                        f"└─ Patterns: Done ({pattern_count} found, {pattern_result.extraction_time:.1f}s)\n"
                    )
                    status.processor_results["patterns"] = ProcessorResult(
                        processor_name="patterns",
                        status="success" if patterns else "empty",
                        extracted_count=pattern_count,
                    )
                else:
                    sys.stdout.write("└─ Patterns: Failed\n")
                    status.processor_results["patterns"] = ProcessorResult(
                        processor_name="patterns",
                        status="failed",
                        error_message=pattern_result.error if pattern_result else "Unknown error",
                    )

                sys.stdout.flush()
                status.is_complete = all(r.status in ["success", "empty"] for r in status.processor_results.values())

            elif self.extractor:
                # Use unified extractor (old behavior)
                self.extraction_logger.start_phase("Unified Extraction")
                phase_start = time.time()

                async with asyncio.timeout(120):  # 120 seconds per DISCOVERIES.md
                    extraction = await self.extractor.extract_from_text(
                        text=truncated_content, title=article.title, source=article.content_id
                    )

                phase_elapsed = time.time() - phase_start

                # Process concepts
                concepts = extraction.concepts
                concept_count = len(concepts) if concepts else 0
                extraction_data["concepts"] = concepts

                # Process SPO relationships
                relationships = extraction.relationships
                relation_count = len(relationships) if relationships else 0
                extraction_data["relationships"] = [
                    {"subject": r.subject, "predicate": r.predicate, "object": r.object, "confidence": r.confidence}
                    for r in relationships
                ]

                # Log unified extraction completion with breakdown
                self.extraction_logger.complete_phase(
                    "Unified Extraction", {"concepts": concepts, "relationships": relationships}, phase_elapsed
                )

                # Store other extracted data
                extraction_data["insights"] = extraction.key_insights
                extraction_data["patterns"] = extraction.code_patterns

                # Update status for all processors
                status.processor_results["concepts"] = ProcessorResult(
                    processor_name="concepts", status="success" if concepts else "empty", extracted_count=concept_count
                )
                status.processor_results["relationships"] = ProcessorResult(
                    processor_name="relationships",
                    status="success" if relationships else "empty",
                    extracted_count=relation_count,
                )
                status.processor_results["insights"] = ProcessorResult(
                    processor_name="insights",
                    status="success" if extraction.key_insights else "empty",
                    extracted_count=len(extraction.key_insights) if extraction.key_insights else 0,
                )
                status.processor_results["patterns"] = ProcessorResult(
                    processor_name="patterns",
                    status="success" if extraction.code_patterns else "empty",
                    extracted_count=len(extraction.code_patterns) if extraction.code_patterns else 0,
                )

                status.is_complete = True
            else:
                raise RuntimeError("No extractor available")

        except Exception as e:
            logger.debug(f"Extraction failed: {e}")
            # Mark processors as failed if extraction failed
            for processor_name in ["concepts", "relationships", "insights", "patterns"]:
                if processor_name not in status.processor_results:
                    status.processor_results[processor_name] = ProcessorResult(
                        processor_name=processor_name, status="failed", error_message=str(e)
                    )

        # Save status after processing
        status.last_processed = datetime.now()
        self.status_store.save_status(status)

        # Save extracted data if we have any
        if extraction_data:
            self._save_extraction_data(article.content_id, extraction_data)

        # Update statistics
        self._update_stats(status)

        # Log completion
        self.extraction_logger.complete_article()

        return status

    def _save_extraction_data(self, article_id: str, data: dict[str, Any]) -> None:
        """Save extracted data to JSON file.

        Args:
            article_id: Article ID
            data: Extraction data to save
        """
        # Create extractions directory
        extractions_dir = paths.data_dir / "extractions"
        extractions_dir.mkdir(parents=True, exist_ok=True)

        # Save to JSON file
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in article_id)
        output_file = extractions_dir / f"{safe_id}.json"

        # Save with timestamp
        save_data = {"article_id": article_id, "extracted_at": datetime.now().isoformat(), "data": data}

        output_file.write_text(json.dumps(save_data, indent=2, ensure_ascii=False))

    def _update_stats(self, status: ArticleProcessingStatus) -> None:
        """Update mining statistics based on processing status.

        Args:
            status: Processing status to analyze
        """
        self.stats["total_processed"] += 1

        # Count successful processors
        successful_count = sum(1 for r in status.processor_results.values() if r.status in ["success", "empty"])

        if successful_count == len(status.processor_results):
            self.stats["fully_successful"] += 1
        elif successful_count > 0:
            self.stats["partially_successful"] += 1
        else:
            self.stats["failed"] += 1

        # Count extracted items
        for result in status.processor_results.values():
            if result.status == "success":
                if result.processor_name == "concepts":
                    self.stats["total_concepts"] += result.extracted_count
                elif result.processor_name == "relationships":
                    self.stats["total_relationships"] += result.extracted_count
                elif result.processor_name == "insights":
                    self.stats["total_insights"] += result.extracted_count
                elif result.processor_name == "patterns":
                    self.stats["total_patterns"] += result.extracted_count

    def get_processing_report(self) -> dict[str, Any]:
        """Get comprehensive processing report.

        Returns:
            Report with statistics and details
        """
        all_statuses = self.status_store.get_all_statuses()

        # Categorize articles
        complete = []
        partial = []
        failed = []
        needs_retry = []

        for status in all_statuses:
            if status.is_complete:
                complete.append(status)
            else:
                # Count successful processors
                success_count = sum(1 for r in status.processor_results.values() if r.status in ["success", "empty"])

                if success_count == 0:
                    failed.append(status)
                    needs_retry.append(status)
                else:
                    partial.append(status)
                    # Only retry if some processors failed
                    if any(r.status == "failed" for r in status.processor_results.values()):
                        needs_retry.append(status)

        # Calculate processor-level stats
        processor_stats = {
            "concepts": {"success": 0, "failed": 0, "empty": 0},
            "relationships": {"success": 0, "failed": 0, "empty": 0},
            "insights": {"success": 0, "failed": 0, "empty": 0},
            "patterns": {"success": 0, "failed": 0, "empty": 0},
        }

        for status in all_statuses:
            for processor_name, result in status.processor_results.items():
                if processor_name in processor_stats and result.status in processor_stats[processor_name]:
                    processor_stats[processor_name][result.status] += 1

        return {
            "summary": {
                "total_articles": len(all_statuses),
                "complete": len(complete),
                "partial": len(partial),
                "failed": len(failed),
                "needs_retry": len(needs_retry),
            },
            "extraction_stats": self.stats,
            "processor_stats": processor_stats,
            "failed_articles": [{"id": s.article_id, "title": s.title} for s in failed[:10]],  # First 10
            "needs_retry": [{"id": s.article_id, "title": s.title} for s in needs_retry[:10]],  # First 10
        }

    async def process_batch_with_retry(self, articles: list[ContentItem], retry_failed: bool = True) -> dict[str, Any]:
        """Process a batch of articles with optional retry for failed items.

        Args:
            articles: List of articles to process
            retry_failed: Whether to retry failed processors

        Returns:
            Processing report
        """
        total = len(articles)
        logger.info(f"Processing batch of {total} articles")

        for idx, article in enumerate(articles, 1):
            # Check if already processed
            existing_status = self.status_store.load_status(article.content_id)

            if existing_status and existing_status.is_complete and not retry_failed:
                logger.info(f"Skipping already complete: {article.title}")
                continue

            # Process or reprocess
            await self.process_article_with_logging(article, idx, total)

        # Return final report
        return self.get_processing_report()
