"""
State Management Module

Handles pipeline state persistence for resume capability.
Saves state after every operation to enable interruption recovery.
"""

import re
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from pathlib import Path
from typing import Any

from amplifier.ccsdk_toolkit.defensive.file_io import read_json_with_retry
from amplifier.ccsdk_toolkit.defensive.file_io import write_json_with_retry
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


def extract_title_from_markdown(content: str) -> str | None:
    """Extract the first H1 heading from markdown content.

    Args:
        content: Markdown content

    Returns:
        Title string or None if no title found
    """
    lines = content.strip().split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return None


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug.

    Args:
        text: Text to slugify

    Returns:
        Slugified string (lowercase, dashes for spaces, no special chars)
    """
    # Convert to lowercase
    slug = text.lower()
    # Replace spaces and underscores with dashes
    slug = re.sub(r"[\s_]+", "-", slug)
    # Remove special characters (keep alphanumeric and dashes)
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    # Remove multiple consecutive dashes
    slug = re.sub(r"-+", "-", slug)
    # Strip leading/trailing dashes
    slug = slug.strip("-")
    return slug


@dataclass
class PipelineState:
    """Complete pipeline state for persistence."""

    # Current pipeline stage
    stage: str = "initialized"
    iteration: int = 0
    max_iterations: int = 10

    # Module outputs
    style_profile: dict[str, Any] = field(default_factory=dict)
    current_draft: str = ""
    source_review: dict[str, Any] = field(default_factory=dict)
    style_review: dict[str, Any] = field(default_factory=dict)
    user_feedback: list[dict[str, Any]] = field(default_factory=list)

    # Iteration history for debugging
    iteration_history: list[dict[str, Any]] = field(default_factory=list)

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Input parameters
    brain_dump_path: str | None = None
    writings_dir: str | None = None
    output_path: str | None = None
    additional_instructions: str | None = None


class StateManager:
    """Manages pipeline state with automatic persistence."""

    def __init__(self, session_dir: Path | None = None):
        """Initialize state manager.

        Args:
            session_dir: Path to session directory (default: .data/blog_post_writer/<timestamp>/)
        """
        if session_dir is None:
            # Create new session directory with timestamp
            base_dir = Path(".data/blog_post_writer")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_dir = base_dir / timestamp

        self.session_dir = session_dir
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.session_dir / "state.json"
        self.state = self._load_state()

    def _load_state(self) -> PipelineState:
        """Load state from file or create new."""
        if self.state_file.exists():
            try:
                data = read_json_with_retry(self.state_file)
                logger.info(f"Resumed state from: {self.state_file}")
                logger.info(f"  Stage: {data.get('stage', 'unknown')}")
                logger.info(f"  Iteration: {data.get('iteration', 0)}")
                return PipelineState(**data)
            except Exception as e:
                logger.warning(f"Could not load state: {e}")
                logger.info("Starting fresh pipeline")

        return PipelineState()

    def save(self) -> None:
        """Save current state to file."""
        self.state.updated_at = datetime.now().isoformat()

        try:
            state_dict = asdict(self.state)
            write_json_with_retry(state_dict, self.state_file)
            logger.debug(f"State saved to: {self.state_file}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            # Don't fail the pipeline on state save errors

    def update_stage(self, stage: str) -> None:
        """Update pipeline stage and save."""
        old_stage = self.state.stage
        self.state.stage = stage
        logger.info(f"Pipeline stage: {old_stage} → {stage}")
        self.save()

    def increment_iteration(self) -> bool:
        """Increment iteration counter.

        Returns:
            True if within max iterations, False if exceeded
        """
        self.state.iteration += 1
        logger.info(f"Iteration {self.state.iteration}/{self.state.max_iterations}")

        if self.state.iteration > self.state.max_iterations:
            logger.warning(f"Exceeded max iterations ({self.state.max_iterations})")
            return False

        self.save()
        return True

    def add_iteration_history(self, entry: dict[str, Any]) -> None:
        """Add entry to iteration history for debugging."""
        entry["iteration"] = self.state.iteration
        entry["timestamp"] = datetime.now().isoformat()
        self.state.iteration_history.append(entry)
        self.save()

    def set_style_profile(self, profile: dict[str, Any]) -> None:
        """Save extracted style profile."""
        self.state.style_profile = profile
        self.save()

    def update_draft(self, draft: str) -> None:
        """Update current blog draft."""
        self.state.current_draft = draft
        # Save draft to separate file for easy access in session directory
        draft_file = self.session_dir / f"draft_iter_{self.state.iteration}.md"
        try:
            draft_file.write_text(draft)
            logger.info(f"Draft saved to: {draft_file}")
        except Exception as e:
            logger.warning(f"Could not save draft file: {e}")
        self.save()

    def set_source_review(self, review: dict[str, Any]) -> None:
        """Save source review results."""
        self.state.source_review = review
        self.save()

    def set_style_review(self, review: dict[str, Any]) -> None:
        """Save style review results."""
        self.state.style_review = review
        self.save()

    def add_user_feedback(self, feedback: dict[str, Any]) -> None:
        """Add user feedback to history."""
        feedback["iteration"] = self.state.iteration
        self.state.user_feedback.append(feedback)
        self.save()

    def is_complete(self) -> bool:
        """Check if pipeline is complete."""
        return self.state.stage == "complete"

    def mark_complete(self) -> None:
        """Mark pipeline as complete."""
        self.update_stage("complete")
        logger.info("✅ Pipeline complete!")

    def reset(self) -> None:
        """Reset state for fresh run."""
        self.state = PipelineState()
        self.save()
        logger.info("State reset for fresh pipeline run")
