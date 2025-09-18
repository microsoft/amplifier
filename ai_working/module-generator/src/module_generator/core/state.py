"""
State management for Module Generator with checkpoint support.

This module provides reliable state persistence with immediate saves after
every mutation, retry logic for cloud sync issues, and checkpoint recovery.
"""

import json
import logging
import time
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class GenerationState:
    """
    Manages generation state with checkpoint support.

    Critical: Saves immediately after every mutation to preserve progress.
    Handles cloud sync issues with exponential backoff retries.
    """

    module_name: str
    current_phase: str | None = None
    completed_phases: list[str] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def save(self) -> None:
        """
        Save state immediately with retry logic for cloud sync issues.

        Uses exponential backoff: 0.5s, 1s, 2s for OSError errno 5.
        This handles OneDrive/Dropbox sync delays in WSL environments.
        """
        checkpoint_dir = Path(".checkpoints")
        checkpoint_dir.mkdir(exist_ok=True)

        checkpoint_file = checkpoint_dir / f"{self.module_name}.json"

        # Retry with exponential backoff for cloud sync issues
        max_retries = 3
        retry_delay = 0.5  # Start with 0.5 seconds

        for attempt in range(max_retries):
            try:
                # Write state to JSON file
                with open(checkpoint_file, "w", encoding="utf-8") as f:
                    json.dump(asdict(self), f, indent=2, ensure_ascii=False)
                    f.flush()  # Ensure write is committed
                return

            except OSError as e:
                if e.errno == 5 and attempt < max_retries - 1:
                    # File I/O error - likely cloud sync issue
                    if attempt == 0:
                        logger.warning(
                            f"File I/O error writing checkpoint for {self.module_name}. "
                            "This may be due to cloud-synced files (OneDrive, Dropbox, etc.). "
                            "Retrying with exponential backoff..."
                        )
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff: 0.5, 1, 2
                else:
                    # Final attempt failed or different error
                    logger.error(f"Failed to save checkpoint after {max_retries} attempts")
                    raise

    @classmethod
    def load_or_create(cls, module_name: str) -> "GenerationState":
        """
        Load existing checkpoint or create new state.

        Args:
            module_name: Name of the module being generated

        Returns:
            GenerationState: Either loaded from checkpoint or newly created
        """
        checkpoint_file = Path(f".checkpoints/{module_name}.json")

        if checkpoint_file.exists():
            try:
                with open(checkpoint_file, encoding="utf-8") as f:
                    data = json.load(f)
                    logger.info(f"Loaded checkpoint for module: {module_name}")
                    return cls(**data)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to load checkpoint: {e}. Creating new state.")

        logger.info(f"Creating new state for module: {module_name}")
        return cls(module_name=module_name)

    def add_artifact(self, key: str, value: Any) -> None:
        """
        Add an artifact and save state immediately.

        Args:
            key: Artifact identifier (e.g., 'interface_code', 'tests')
            value: Artifact content
        """
        self.artifacts[key] = value
        self.save()  # CRITICAL: Save immediately after mutation

    def mark_phase_complete(self, phase: str) -> None:
        """
        Mark a phase as complete and save state immediately.

        Args:
            phase: Name of the completed phase
        """
        if phase not in self.completed_phases:
            self.completed_phases.append(phase)

        # Update current phase to None when completed
        if self.current_phase == phase:
            self.current_phase = None

        self.save()  # CRITICAL: Save immediately after mutation

    def set_current_phase(self, phase: str) -> None:
        """
        Set the current phase being worked on and save immediately.

        Args:
            phase: Name of the phase being started
        """
        self.current_phase = phase
        self.save()  # CRITICAL: Save immediately after mutation

    def add_error(self, error: str) -> None:
        """
        Record an error and save state immediately.

        Args:
            error: Error message or description
        """
        self.errors.append(error)
        self.save()  # CRITICAL: Save immediately after mutation

    def is_phase_complete(self, phase: str) -> bool:
        """
        Check if a phase has been completed.

        Args:
            phase: Name of the phase to check

        Returns:
            bool: True if phase is complete, False otherwise
        """
        return phase in self.completed_phases

    def get_artifact(self, key: str) -> Any | None:
        """
        Retrieve an artifact by key.

        Args:
            key: Artifact identifier

        Returns:
            The artifact value or None if not found
        """
        return self.artifacts.get(key)

    def clear_errors(self) -> None:
        """
        Clear all recorded errors and save state immediately.
        """
        self.errors = []
        self.save()  # CRITICAL: Save immediately after mutation

    def summary(self) -> dict[str, Any]:
        """
        Get a summary of the current state.

        Returns:
            Dictionary with state summary information
        """
        return {
            "module_name": self.module_name,
            "current_phase": self.current_phase,
            "completed_phases": self.completed_phases,
            "artifact_keys": list(self.artifacts.keys()),
            "error_count": len(self.errors),
            "has_errors": bool(self.errors),
        }
