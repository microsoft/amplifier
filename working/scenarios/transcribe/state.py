"""
State Management Module

Handles pipeline state persistence for resume capability.
"""

from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from pathlib import Path

from amplifier.ccsdk_toolkit.defensive.file_io import read_json_with_retry
from amplifier.ccsdk_toolkit.defensive.file_io import write_json_with_retry
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class VideoProcessingResult:
    """Result of processing a single video."""

    video_id: str
    source: str
    status: str  # "success", "failed", "skipped"
    output_dir: str | None = None
    error: str | None = None
    duration_seconds: float = 0.0
    cost_estimate: float = 0.0
    processed_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PipelineState:
    """Complete pipeline state for persistence."""

    # Current status
    stage: str = "initialized"  # initialized, loading, extracting, transcribing, saving, complete
    current_video: str | None = None
    total_videos: int = 0

    # Processing results
    processed_videos: list[VideoProcessingResult] = field(default_factory=list)
    failed_videos: list[VideoProcessingResult] = field(default_factory=list)

    # Statistics
    total_duration_seconds: float = 0.0
    total_cost_estimate: float = 0.0

    # Input parameters
    sources: list[str] = field(default_factory=list)
    output_dir: str | None = None

    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class StateManager:
    """Manages pipeline state with automatic persistence."""

    def __init__(self, session_dir: Path | None = None):
        """Initialize state manager.

        Args:
            session_dir: Session directory (default: .data/transcribe/<timestamp>/)
        """
        if session_dir is None:
            base_dir = Path(".data/transcribe")
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
                logger.info(f"  Processed: {len(data.get('processed_videos', []))}")
                logger.info(f"  Failed: {len(data.get('failed_videos', []))}")

                # Convert dicts back to dataclass instances
                state = PipelineState(**data)
                state.processed_videos = [
                    VideoProcessingResult(**v) if isinstance(v, dict) else v for v in state.processed_videos
                ]
                state.failed_videos = [
                    VideoProcessingResult(**v) if isinstance(v, dict) else v for v in state.failed_videos
                ]
                return state
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

    def update_stage(self, stage: str, current_video: str | None = None) -> None:
        """Update pipeline stage."""
        old_stage = self.state.stage
        self.state.stage = stage
        self.state.current_video = current_video

        if current_video:
            logger.info(f"Stage: {old_stage} → {stage} (processing: {current_video})")
        else:
            logger.info(f"Stage: {old_stage} → {stage}")

        self.save()

    def add_processed(self, result: VideoProcessingResult) -> None:
        """Add successfully processed video."""
        self.state.processed_videos.append(result)
        self.state.total_duration_seconds += result.duration_seconds
        self.state.total_cost_estimate += result.cost_estimate
        self.save()

        logger.info(f"✓ Processed {len(self.state.processed_videos)}/{self.state.total_videos}: {result.video_id}")

    def add_failed(self, result: VideoProcessingResult) -> None:
        """Add failed video."""
        self.state.failed_videos.append(result)
        self.save()

        logger.warning(f"✗ Failed: {result.video_id} - {result.error}")

    def is_already_processed(self, video_id: str) -> bool:
        """Check if video was already processed."""
        return any(result.video_id == video_id for result in self.state.processed_videos)

    def get_pending_sources(self) -> list[str]:
        """Get list of sources not yet processed."""
        processed_sources = {r.source for r in self.state.processed_videos}
        processed_sources.update({r.source for r in self.state.failed_videos})

        return [s for s in self.state.sources if s not in processed_sources]

    def is_complete(self) -> bool:
        """Check if pipeline is complete."""
        return self.state.stage == "complete"

    def mark_complete(self) -> None:
        """Mark pipeline as complete."""
        self.update_stage("complete")

        # Summary statistics
        total = len(self.state.processed_videos)
        failed = len(self.state.failed_videos)

        logger.info("=" * 60)
        logger.info("✅ Transcription Pipeline Complete!")
        logger.info(f"  Processed: {total} videos")
        if failed > 0:
            logger.info(f"  Failed: {failed} videos")
        logger.info(f"  Total Duration: {self.state.total_duration_seconds / 60:.1f} minutes")
        logger.info(f"  Estimated Cost: ${self.state.total_cost_estimate:.2f}")
        logger.info("=" * 60)

    def reset(self) -> None:
        """Reset state for fresh run."""
        self.state = PipelineState()
        self.save()
        logger.info("State reset for fresh pipeline run")
