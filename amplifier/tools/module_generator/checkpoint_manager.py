"""Checkpoint manager for saving and resuming pipeline state."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from amplifier.utils.file_io import read_json
from amplifier.utils.file_io import write_json

logger = logging.getLogger(__name__)


class CheckpointManager:
    """Manages pipeline checkpoints for resume capability."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.checkpoint_dir = repo_root / ".pipeline_checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save(self, state: PipelineState) -> Path:  # type: ignore # noqa: F821
        """Save a pipeline state checkpoint.

        Creates immutable checkpoint file with timestamp.
        Returns the path to the saved checkpoint.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        module_name = state.context.module_name
        stage_name = state.current_stage.value

        checkpoint_file = self.checkpoint_dir / f"{module_name}_{stage_name}_{timestamp}.json"

        # Convert state to dictionary
        state_dict = state.to_dict()

        # Save with retry logic for cloud sync
        write_json(state_dict, checkpoint_file, indent=2)
        logger.info(f"Saved checkpoint: {checkpoint_file.name}")

        return checkpoint_file

    def load_latest(self, module_name: str) -> PipelineState | None:  # type: ignore # noqa: F821
        """Load the most recent checkpoint for a module.

        Returns None if no checkpoint exists.
        """
        # Import here to avoid circular dependency
        from .pipeline_orchestrator import PipelineState

        # Find all checkpoints for this module
        pattern = f"{module_name}_*.json"
        checkpoints = sorted(self.checkpoint_dir.glob(pattern))

        if not checkpoints:
            logger.info(f"No checkpoints found for module: {module_name}")
            return None

        # Get the most recent checkpoint
        latest = checkpoints[-1]
        logger.info(f"Loading checkpoint: {latest.name}")

        try:
            state_dict = read_json(latest)
            return PipelineState.from_dict(state_dict)
        except Exception as e:
            logger.error(f"Failed to load checkpoint {latest}: {e}")
            return None

    def list_checkpoints(self, module_name: str | None = None) -> list[dict]:
        """List all available checkpoints.

        If module_name is provided, only list checkpoints for that module.
        Returns list of checkpoint info dictionaries.
        """
        pattern = f"{module_name}_*.json" if module_name else "*.json"
        checkpoints = []

        for checkpoint_file in sorted(self.checkpoint_dir.glob(pattern)):
            # Parse filename
            parts = checkpoint_file.stem.split("_")
            if len(parts) >= 4:
                module = parts[0]
                stage = parts[1]
                # Rest is timestamp
                timestamp_parts = parts[2:]
                timestamp_str = "_".join(timestamp_parts)

                checkpoints.append(
                    {
                        "file": checkpoint_file.name,
                        "path": str(checkpoint_file),
                        "module": module,
                        "stage": stage,
                        "timestamp": timestamp_str,
                        "size": checkpoint_file.stat().st_size,
                    }
                )

        return checkpoints

    def clean_old_checkpoints(self, module_name: str, keep_count: int = 10):
        """Remove old checkpoints, keeping only the most recent ones.

        Args:
            module_name: Module to clean checkpoints for
            keep_count: Number of recent checkpoints to keep
        """
        pattern = f"{module_name}_*.json"
        checkpoints = sorted(self.checkpoint_dir.glob(pattern))

        if len(checkpoints) <= keep_count:
            return

        to_remove = checkpoints[:-keep_count]
        for checkpoint in to_remove:
            checkpoint.unlink()
            logger.info(f"Removed old checkpoint: {checkpoint.name}")

        logger.info(f"Cleaned {len(to_remove)} old checkpoints for {module_name}")

    def get_checkpoint_path(self, module_name: str, stage: str | None = None) -> Path | None:
        """Get the path to a specific checkpoint.

        Args:
            module_name: Module name
            stage: Optional stage name to find specific checkpoint

        Returns:
            Path to checkpoint or None if not found
        """
        if stage:
            pattern = f"{module_name}_{stage}_*.json"
        else:
            pattern = f"{module_name}_*.json"

        checkpoints = sorted(self.checkpoint_dir.glob(pattern))
        if checkpoints:
            return checkpoints[-1]
        return None
