"""
Review state tracking.

Manages the state of the human review process with resume capability.
"""

from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any

from amplifier.ccsdk_toolkit.defensive import read_json_with_retry
from amplifier.ccsdk_toolkit.defensive import write_json_with_retry
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ReviewState:
    """State tracking for review workflow."""

    # Files tracking
    markdown_files: list[str] = field(default_factory=list)
    reviewed_files: list[str] = field(default_factory=list)
    pending_files: list[str] = field(default_factory=list)
    rejected_indices: list[int] = field(default_factory=list)

    # Opportunities tracking
    original_count: int = 0
    enhanced_count: int = 0
    rejected_count: int = 0

    # Process state
    review_complete: bool = False
    merge_complete: bool = False

    # Results
    enhanced_opportunities: list[dict[str, Any]] = field(default_factory=list)
    rejected_opportunities: list[dict[str, Any]] = field(default_factory=list)


class ReviewStateManager:
    """Manages review state with auto-save."""

    def __init__(self, review_dir: Path):
        """Initialize state manager.

        Args:
            review_dir: Directory for review files
        """
        self.review_dir = review_dir
        self.state_file = review_dir / "review_state.json"
        self.state = self._load_state()

    def _load_state(self) -> ReviewState:
        """Load state from file or create new."""
        if self.state_file.exists():
            try:
                data = read_json_with_retry(self.state_file, default={})
                if data:
                    logger.info(
                        f"Resumed review state: {data.get('enhanced_count', 0)} enhanced, {data.get('rejected_count', 0)} rejected"
                    )
                    return ReviewState(**data)
            except Exception as e:
                logger.warning(f"Could not load review state: {e}")

        return ReviewState()

    def save(self) -> None:
        """Save current state to file."""
        try:
            state_dict = asdict(self.state)
            write_json_with_retry(state_dict, self.state_file)
            logger.debug("Review state saved")
        except Exception as e:
            logger.error(f"Failed to save review state: {e}")

    def set_markdown_files(self, files: list[Path]) -> None:
        """Set the list of markdown files."""
        self.state.markdown_files = [str(f) for f in files]
        self.state.pending_files = self.state.markdown_files.copy()
        self.state.original_count = len(files)
        self.save()

    def mark_reviewed(self, filepath: Path) -> None:
        """Mark a file as reviewed."""
        file_str = str(filepath)
        if file_str in self.state.pending_files:
            self.state.pending_files.remove(file_str)
            self.state.reviewed_files.append(file_str)
            self.save()

    def mark_rejected(self, index: int) -> None:
        """Mark an opportunity as rejected."""
        if index not in self.state.rejected_indices:
            self.state.rejected_indices.append(index)
            self.state.rejected_count += 1
            self.save()

    def set_results(self, enhanced: list[dict[str, Any]], rejected: list[dict[str, Any]]) -> None:
        """Set the final results."""
        self.state.enhanced_opportunities = enhanced
        self.state.rejected_opportunities = rejected
        self.state.enhanced_count = len(enhanced)
        self.state.rejected_count = len(rejected)
        self.state.merge_complete = True
        self.save()

    def is_complete(self) -> bool:
        """Check if review is complete."""
        return self.state.review_complete and self.state.merge_complete

    def mark_review_complete(self) -> None:
        """Mark human review as complete."""
        self.state.review_complete = True
        self.save()

    def get_progress(self) -> str:
        """Get progress summary."""
        reviewed = len(self.state.reviewed_files)
        total = len(self.state.markdown_files)
        return f"Progress: {reviewed}/{total} files reviewed, {self.state.rejected_count} rejected"

    def reset(self) -> None:
        """Reset state for fresh review."""
        self.state = ReviewState()
        self.save()
        logger.info("Review state reset")
