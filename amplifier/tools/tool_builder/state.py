"""
State management for AI-first tool builder with resumability.

This module handles persistent state tracking across tool building stages,
enabling interruption and resumption from any point in the pipeline.
"""

import logging
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from pathlib import Path
from typing import Any

from amplifier.utils.file_io import read_json
from amplifier.utils.file_io import write_json

logger = logging.getLogger(__name__)


@dataclass
class ToolBuilderState:
    """Persistent state for tool building pipeline.

    Tracks progress through stages and preserves outputs for resumability.
    """

    # Core metadata
    tool_name: str
    description: str
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Progress tracking
    current_stage: str | None = None
    completed_stages: list[str] = field(default_factory=list)
    failed_attempts: dict[str, list[str]] = field(default_factory=dict)  # stage -> error messages

    # Stage outputs
    stage_outputs: dict[str, Any] = field(default_factory=dict)

    # Generated artifacts
    requirements: dict[str, Any] | None = None
    analysis: dict[str, Any] | None = None
    generated_code: dict[str, str] | None = None  # filename -> content
    validation_results: dict[str, Any] | None = None
    integration_results: dict[str, Any] | None = None  # Integration stage output

    # Execution metadata
    total_ai_calls: int = 0
    total_tokens_used: int = 0
    last_checkpoint: str | None = None

    def save(self, filepath: Path) -> None:
        """Save state to disk with retry logic for cloud-synced directories."""
        data = asdict(self)
        write_json(data, filepath)
        logger.info(f"State saved to {filepath}")

    @classmethod
    def load(cls, filepath: Path) -> "ToolBuilderState":
        """Load state from disk."""
        if not filepath.exists():
            raise FileNotFoundError(f"State file not found: {filepath}")

        data = read_json(filepath)
        return cls(**data)

    def mark_stage_complete(self, stage: str, output: Any) -> None:
        """Mark a stage as complete and save its output."""
        if stage not in self.completed_stages:
            self.completed_stages.append(stage)
        self.stage_outputs[stage] = output
        self.current_stage = None
        self.last_checkpoint = datetime.now().isoformat()

    def mark_stage_failed(self, stage: str, error: str) -> None:
        """Track stage failure for debugging."""
        if stage not in self.failed_attempts:
            self.failed_attempts[stage] = []
        self.failed_attempts[stage].append(error)
        self.current_stage = None

    def start_stage(self, stage: str) -> None:
        """Mark a stage as in progress."""
        self.current_stage = stage
        logger.info(f"Starting stage: {stage}")

    def can_skip_stage(self, stage: str) -> bool:
        """Check if a stage can be skipped due to prior completion."""
        return stage in self.completed_stages

    def get_resume_point(self) -> str | None:
        """Determine the next stage to execute based on completed stages."""
        pipeline_order = ["requirements", "analysis", "generation", "validation"]

        for stage in pipeline_order:
            if stage not in self.completed_stages:
                return stage

        return None  # All stages complete

    def increment_ai_metrics(self, tokens: int = 0) -> None:
        """Track AI usage metrics."""
        self.total_ai_calls += 1
        self.total_tokens_used += tokens


class StateManager:
    """Manages state persistence and recovery for tool building."""

    def __init__(self, state_dir: Path):
        """Initialize state manager with a directory for state files."""
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def get_state_path(self, tool_name: str) -> Path:
        """Get the state file path for a tool."""
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in tool_name)
        return self.state_dir / f"{safe_name}_state.json"

    def create_state(self, tool_name: str, description: str) -> ToolBuilderState:
        """Create a new state for tool building."""
        state = ToolBuilderState(tool_name=tool_name, description=description)
        state.save(self.get_state_path(tool_name))
        return state

    def load_state(self, tool_name: str) -> ToolBuilderState | None:
        """Load existing state for a tool."""
        state_path = self.get_state_path(tool_name)
        if state_path.exists():
            return ToolBuilderState.load(state_path)
        return None

    def save_checkpoint(self, state: ToolBuilderState) -> None:
        """Save a checkpoint of the current state."""
        state.save(self.get_state_path(state.tool_name))

    def list_incomplete_tools(self) -> list[str]:
        """List tools with incomplete builds."""
        incomplete = []
        for state_file in self.state_dir.glob("*_state.json"):
            try:
                state = ToolBuilderState.load(state_file)
                if state.get_resume_point() is not None:
                    incomplete.append(state.tool_name)
            except Exception as e:
                logger.warning(f"Failed to load state from {state_file}: {e}")
        return incomplete

    def cleanup_completed(self) -> int:
        """Remove state files for completed tools."""
        cleaned = 0
        for state_file in self.state_dir.glob("*_state.json"):
            try:
                state = ToolBuilderState.load(state_file)
                if state.get_resume_point() is None:
                    state_file.unlink()
                    cleaned += 1
            except Exception:
                pass
        return cleaned
