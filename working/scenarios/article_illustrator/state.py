"""
State Management Module

Handles session state persistence for resume capability.
Saves state after every operation to enable interruption recovery.
"""

from pathlib import Path

from amplifier.ccsdk_toolkit.defensive.file_io import read_json_with_retry
from amplifier.ccsdk_toolkit.defensive.file_io import write_json_with_retry
from amplifier.utils.logger import get_logger

from .models import SessionState

logger = get_logger(__name__)


class StageState:
    """Track completion status of pipeline stages."""

    ANALYSIS = "analysis"
    PROMPTS = "prompts"
    IMAGES = "images"
    MARKDOWN = "markdown"


class SessionManager:
    """Manages persistent session state for resumable processing."""

    def __init__(self, output_dir: Path):
        """Initialize session manager.

        Args:
            output_dir: Directory for session files and outputs
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = output_dir / ".session_state.json"

    def create_new(self, article_path: Path, style_params: dict | None = None) -> SessionState:
        """Create a fresh session state - never loads existing.

        Args:
            article_path: Path to article being processed
            style_params: Style parameters for generation

        Returns:
            New session state
        """
        return SessionState(
            article_path=article_path,
            output_dir=self.output_dir,
            style_params=style_params or {},
        )

    def load_existing(self) -> SessionState:
        """Load existing session from state file.

        Raises:
            FileNotFoundError: If no session state file exists
            ValueError: If state file is corrupted

        Returns:
            Loaded session state
        """
        if not self.state_file.exists():
            raise FileNotFoundError(f"No session found at {self.state_file}")

        try:
            state_dict = read_json_with_retry(self.state_file)

            # Convert paths back from strings
            state_dict["article_path"] = Path(state_dict["article_path"])
            state_dict["output_dir"] = Path(state_dict["output_dir"])

            # Reconstruct model objects
            state = SessionState(**state_dict)

            return state

        except Exception as e:
            raise ValueError(f"Failed to load session state: {e}")

    def validate_compatibility(
        self, existing: SessionState, article_path: Path, style: str | None
    ) -> tuple[bool, list[str]]:
        """Check if existing session is compatible with current parameters.

        Args:
            existing: Existing session state
            article_path: Current article path
            style: Current style setting

        Returns:
            (is_compatible, reasons) - bool and list of mismatch descriptions
        """
        mismatches = []

        # Check article path
        if existing.article_path != article_path:
            mismatches.append(f"Article: session={existing.article_path.name}, current={article_path.name}")

        # Check style if provided
        existing_style = existing.style_params.get("style", "")
        current_style = style or ""
        if current_style and existing_style != current_style:
            mismatches.append(f"Style: session='{existing_style}', current='{current_style}'")

        return (len(mismatches) == 0, mismatches)

    def save(self, state: SessionState) -> None:
        """Save current session state.

        Args:
            state: Current session state to persist
        """
        try:
            # Convert to dict for JSON serialization
            state_dict = state.dict()

            # Convert paths to strings
            state_dict["article_path"] = str(state.article_path)
            state_dict["output_dir"] = str(state.output_dir)

            # Convert complex objects to dicts
            state_dict["illustration_points"] = [p.dict() for p in state.illustration_points]
            state_dict["prompts"] = [p.dict() for p in state.prompts]
            state_dict["images"] = [img.dict() for img in state.images]

            # Handle Path objects in nested structures
            for img_data in state_dict["images"]:
                if "primary" in img_data:
                    img_data["primary"]["local_path"] = str(img_data["primary"]["local_path"])
                for alt in img_data.get("alternatives", []):
                    alt["local_path"] = str(alt["local_path"])

            # Save with retry logic for cloud sync
            write_json_with_retry(state_dict, self.state_file)
            logger.debug(f"Saved session state to {self.state_file}")

        except Exception as e:
            logger.error(f"Failed to save session state: {e}")
            # Don't fail the whole process for state saving issues

    def save_prompts(self, state: SessionState) -> None:
        """Save prompts to a separate file for reference.

        Args:
            state: Session state with prompts
        """
        if not state.prompts:
            return

        prompts_file = self.output_dir / "prompts.json"
        prompts_data = []

        for prompt in state.prompts:
            prompts_data.append(
                {
                    "id": prompt.illustration_id,
                    "section": prompt.point.section_title,
                    "full_prompt": prompt.full_prompt,
                    "style_modifiers": prompt.style_modifiers,
                    "metadata": prompt.metadata,
                }
            )

        try:
            write_json_with_retry(prompts_data, prompts_file)
            logger.info(f"Saved prompts to {prompts_file}")
        except Exception as e:
            logger.error(f"Failed to save prompts file: {e}")

    def mark_complete(self, state: SessionState, stage: str) -> None:
        """Mark a stage as complete and save state.

        Args:
            state: Current session state
            stage: Stage name to mark complete
        """
        if stage == StageState.ANALYSIS:
            state.analysis_complete = True
        elif stage == StageState.PROMPTS:
            state.prompts_complete = True
        elif stage == StageState.IMAGES:
            state.images_complete = True
        elif stage == StageState.MARKDOWN:
            state.markdown_complete = True

        self.save(state)
        logger.info(f"✅ Stage complete: {stage}")

    def add_error(self, state: SessionState, stage: str, error: str) -> None:
        """Add an error to the session and save.

        Args:
            state: Current session state
            stage: Stage where error occurred
            error: Error description
        """
        state.errors.append({"stage": stage, "error": str(error)})
        self.save(state)
        logger.error(f"Error in {stage}: {error}")

    def log_progress(self, state: SessionState) -> None:
        """Log current progress status.

        Args:
            state: Current session state
        """
        logger.info("Resumed session - Progress:")
        logger.info(f"  Analysis: {'✓' if state.analysis_complete else '✗'}")
        logger.info(f"  Prompts: {'✓' if state.prompts_complete else '✗'}")
        logger.info(f"  Images: {'✓' if state.images_complete else '✗'} ({state.images_generated} generated)")
        logger.info(f"  Markdown: {'✓' if state.markdown_complete else '✗'}")
        logger.info(f"  Total cost: ${state.total_cost:.2f}")

    def is_complete(self, state: SessionState) -> bool:
        """Check if all stages are complete.

        Args:
            state: Current session state

        Returns:
            True if all stages complete, False otherwise
        """
        return state.analysis_complete and state.prompts_complete and state.images_complete and state.markdown_complete

    def reset(self, state: SessionState) -> SessionState:
        """Reset state for fresh run.

        Args:
            state: Current state to reset

        Returns:
            Fresh session state
        """
        logger.info("Resetting session state")
        return SessionState(
            article_path=state.article_path,
            output_dir=state.output_dir,
            style_params=state.style_params,
        )
