"""
State management for repository analyzer pipeline.

Handles persistence and recovery for long-running analyses.
"""

import shutil
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


@dataclass
class AnalyzerState:
    """Complete analyzer state for persistence."""

    # Pipeline stage tracking
    stage: str = "initialized"
    iteration: int = 0
    max_iterations: int = 3

    # Input parameters
    source_path: str | None = None
    target_path: str | None = None
    analysis_request: str | None = None
    focus_areas: list[str] = field(default_factory=list)
    output_path: str | None = None

    # Processing results
    source_file: str | None = None
    target_file: str | None = None
    analysis_results: dict[str, Any] = field(default_factory=dict)
    opportunities: list[dict[str, Any]] = field(default_factory=list)

    # Review results
    grounding_review: dict[str, Any] = field(default_factory=dict)
    philosophy_review: dict[str, Any] = field(default_factory=dict)
    completeness_review: dict[str, Any] = field(default_factory=dict)
    human_feedback: list[dict[str, Any]] = field(default_factory=list)

    # Iteration history
    iteration_history: list[dict[str, Any]] = field(default_factory=list)

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed: bool = False


class StateManager:
    """Manages pipeline state with automatic persistence."""

    def __init__(self, session_dir: Path | None = None):
        """Initialize state manager.

        Args:
            session_dir: Path to session directory (default: .data/repo_analyzer/<timestamp>/)
        """
        if session_dir is None:
            # Create new session directory with timestamp
            base_dir = Path(".data/repo_analyzer")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_dir = base_dir / timestamp

        self.session_dir = session_dir
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.session_dir / "state.json"
        self.state = self._load_state()

    def _load_state(self) -> AnalyzerState:
        """Load state from file or create new."""
        if self.state_file.exists():
            try:
                data = read_json_with_retry(self.state_file)
                logger.info(f"Resumed state from: {self.state_file}")
                logger.info(f"  Stage: {data.get('stage', 'unknown')}")
                logger.info(f"  Iteration: {data.get('iteration', 0)}")

                # Validate critical fields before loading
                if not isinstance(data, dict):
                    raise ValueError("State file is not a valid dictionary")

                # Ensure critical fields have valid values
                if "stage" in data and data["stage"] not in [
                    "initialized",
                    "processing_repos",
                    "repos_processed",
                    "analyzing",
                    "analysis_complete",
                    "generating_opportunities",
                    "opportunities_generated",
                    "feedback_applied",
                    "complete",
                ]:
                    logger.warning(f"Invalid stage in state: {data['stage']}, resetting to initialized")
                    data["stage"] = "initialized"

                if "iteration" in data and not isinstance(data["iteration"], int):
                    logger.warning("Invalid iteration in state, resetting to 0")
                    data["iteration"] = 0

                if "max_iterations" in data and not isinstance(data["max_iterations"], int):
                    logger.warning("Invalid max_iterations in state, resetting to 3")
                    data["max_iterations"] = 3

                # Create state with validated data
                return AnalyzerState(**data)

            except (TypeError, ValueError) as e:
                logger.warning(f"State file corrupted or incompatible: {e}")
                logger.info("Starting fresh analysis")
                # Backup corrupted state for debugging
                backup_file = self.state_file.with_suffix(".corrupted.json")
                try:
                    shutil.copy2(self.state_file, backup_file)
                    logger.debug(f"Backed up corrupted state to: {backup_file}")
                except Exception:
                    pass
            except Exception as e:
                logger.warning(f"Could not load state: {e}")
                logger.info("Starting fresh analysis")

        return AnalyzerState()

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

    def set_repo_files(self, source_file: Path, target_file: Path) -> None:
        """Save repository file paths."""
        self.state.source_file = str(source_file)
        self.state.target_file = str(target_file)
        self.save()

    def set_analysis_results(self, results: dict[str, Any]) -> None:
        """Save analysis results."""
        self.state.analysis_results = results
        self.save()

    def set_opportunities(self, opportunities: list[dict[str, Any]]) -> None:
        """Save generated opportunities."""
        self.state.opportunities = opportunities
        self.save()

    def set_review_results(
        self,
        grounding: dict[str, Any] | None = None,
        philosophy: dict[str, Any] | None = None,
        completeness: dict[str, Any] | None = None,
    ) -> None:
        """Save review results."""
        if grounding is not None:
            self.state.grounding_review = grounding
        if philosophy is not None:
            self.state.philosophy_review = philosophy
        if completeness is not None:
            self.state.completeness_review = completeness
        self.save()

    def add_human_feedback(self, feedback: dict[str, Any]) -> None:
        """Add human feedback to history."""
        feedback["iteration"] = self.state.iteration
        feedback["timestamp"] = datetime.now().isoformat()
        self.state.human_feedback.append(feedback)
        self.save()

    def is_complete(self) -> bool:
        """Check if analysis is complete."""
        return self.state.completed

    def mark_complete(self) -> None:
        """Mark analysis as complete."""
        self.state.completed = True
        self.update_stage("complete")
        logger.info("✅ Analysis complete!")

    def reset(self) -> None:
        """Reset state for fresh run."""
        self.state = AnalyzerState()
        self.save()
        logger.info("State reset for fresh analysis")

    def get_output_file(self, suffix: str = "") -> Path:
        """Get output file path in session directory."""
        if suffix:
            return self.session_dir / f"opportunities_{suffix}.json"
        return self.session_dir / "opportunities.json"
