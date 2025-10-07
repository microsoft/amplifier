#!/usr/bin/env python3
"""
Transcription Pipeline - Main Orchestrator and CLI

Coordinates video transcription with state management for resume capability.
"""

import sys
from pathlib import Path

import click

from amplifier.utils.logger import get_logger

from .audio_extractor import AudioExtractor
from .state import StateManager
from .state import VideoProcessingResult
from .storage import TranscriptStorage
from .video_loader import VideoLoader
from .whisper_transcriber import WhisperTranscriber

logger = get_logger(__name__)


class TranscriptionPipeline:
    """Orchestrates the transcription pipeline."""

    def __init__(self, state_manager: StateManager | None = None, enhance: bool = True, force_download: bool = False):
        """Initialize pipeline.

        Args:
            state_manager: State manager for persistence (creates new if None)
            enhance: Whether to enable AI enhancements (summaries/quotes)
            force_download: If True, skip cache and re-download audio
        """
        self.state = state_manager or StateManager()
        self.enhance = enhance
        self.force_download = force_download

        # Initialize components
        self.video_loader = VideoLoader()
        self.audio_extractor = AudioExtractor(temp_dir=self.state.session_dir / "audio")
        self.transcriber = WhisperTranscriber()
        self.storage = TranscriptStorage()

        # Initialize AI enhancement components if enabled
        self.summary_generator = None
        self.quote_extractor = None
        if enhance:
            try:
                from .quote_extractor import QuoteExtractor
                from .summary_generator import SummaryGenerator

                self.summary_generator = SummaryGenerator()
                self.quote_extractor = QuoteExtractor()
                logger.info("AI enhancement enabled (summaries and quotes)")
            except (ImportError, ValueError) as e:
                logger.warning(f"AI enhancement disabled: {e}")
                self.enhance = False

    def process_video(self, source: str) -> bool:
        """Process a single video/audio source.

        Args:
            source: URL or file path

        Returns:
            True if successful, False otherwise
        """
        try:
            # Stage 1: Load video info
            self.state.update_stage("loading", source)
            video_info = self.video_loader.load(source)

            # Check if already processed
            if self.state.is_already_processed(video_info.id):
                logger.info(f"⏭ Skipping (already processed): {video_info.title}")
                return True

            logger.info(f"Processing: {video_info.title}")
            logger.info(f"  Duration: {video_info.duration / 60:.1f} minutes")

            # Estimate cost
            cost = self.transcriber.estimate_cost(video_info.duration)
            logger.info(f"  Estimated cost: ${cost:.3f}")

            # Determine output directory for this video
            video_id = self.storage._sanitize_filename(video_info.id)
            output_dir = self.storage.output_dir / video_id
            output_dir.mkdir(parents=True, exist_ok=True)

            # Stage 2: Extract/download audio
            self.state.update_stage("extracting", video_info.id)

            if video_info.type == "url":
                # Download audio directly to output directory (with caching)
                audio_path = self.video_loader.download_audio(
                    source, output_dir, output_filename="audio.mp3", use_cache=(not self.force_download)
                )
            else:
                # Extract audio from local file
                temp_audio = self.audio_extractor.extract(Path(source))
                # Save to output directory
                audio_path = self.storage.save_audio(temp_audio, output_dir)
                # Clean up temp file
                if temp_audio != audio_path:
                    self.audio_extractor.cleanup(temp_audio)

            # Stage 3: Compress if needed
            audio_path = self.audio_extractor.compress_for_api(audio_path)

            # Stage 4: Transcribe
            self.state.update_stage("transcribing", video_info.id)
            transcript = self.transcriber.transcribe(audio_path, prompt=f"Transcription of: {video_info.title}")

            # Stage 5: Save outputs
            self.state.update_stage("saving", video_info.id)
            output_dir = self.storage.save(transcript, video_info, audio_path)

            # Stage 6: AI Enhancement (if enabled)
            if self.enhance and self.summary_generator and self.quote_extractor:
                try:
                    self.state.update_stage("enhancing", video_info.id)
                    logger.info("Generating AI enhancements...")

                    # Generate summary
                    summary = self.summary_generator.generate(transcript.text, video_info.title)

                    # Extract quotes
                    video_url = source if "youtube" in source.lower() else None
                    quotes = self.quote_extractor.extract(transcript, video_url, video_info.id)

                    # Save combined insights document
                    self.storage.save_insights(
                        summary=summary,
                        quotes=quotes,
                        title=video_info.title,
                        output_dir=output_dir,
                    )

                    logger.info("✓ AI enhancements complete")
                except Exception as e:
                    logger.warning(f"AI enhancement failed (transcript saved): {e}")

            # Record success
            result = VideoProcessingResult(
                video_id=video_info.id,
                source=source,
                status="success",
                output_dir=str(output_dir),
                duration_seconds=video_info.duration,
                cost_estimate=cost,
            )
            self.state.add_processed(result)

            # Audio file is preserved in output directory (not cleaned up)

            return True

        except Exception as e:
            logger.error(f"Failed to process {source}: {e}")

            # Record failure
            result = VideoProcessingResult(
                video_id=source,
                source=source,
                status="failed",
                error=str(e),
            )
            self.state.add_failed(result)

            return False

    def run(self, sources: list[str], resume: bool = False) -> bool:
        """Run the transcription pipeline.

        Args:
            sources: List of video sources (URLs or files)
            resume: Whether to resume from saved state

        Returns:
            True if all videos processed successfully
        """
        # Store sources in state
        if not resume or not self.state.state.sources:
            self.state.state.sources = sources
            self.state.state.total_videos = len(sources)
            self.state.state.output_dir = str(self.storage.output_dir)
            self.state.save()

        # Get pending sources
        if resume:
            pending = self.state.get_pending_sources()
            if not pending:
                logger.info("No pending videos to process")
                self.state.mark_complete()
                return True
            logger.info(f"Resuming with {len(pending)} pending videos")
            sources_to_process = pending
        else:
            sources_to_process = sources

        logger.info(f"Processing {len(sources_to_process)} videos")
        logger.info(f"Output directory: {self.storage.output_dir}")

        # Process each video
        all_success = True
        for i, source in enumerate(sources_to_process, 1):
            logger.info(f"\n[{i}/{len(sources_to_process)}] {source}")

            if not self.process_video(source):
                all_success = False

            # Save state after each video
            self.state.save()

        # Mark complete
        self.state.mark_complete()

        # Auto-update index
        try:
            from .index_generator import write_index

            logger.info("\nUpdating transcript index...")
            write_index(self.storage.output_dir)
        except Exception as e:
            logger.warning(f"Failed to update index (transcripts saved successfully): {e}")

        return all_success


@click.group()
def cli():
    """Transcribe videos and manage transcripts."""
    pass


@cli.command()
def index():
    """Generate index.md for all transcripts."""
    from amplifier.config.paths import paths

    from .index_generator import write_index

    # Get transcripts directory
    content_dirs = paths.get_all_content_paths()
    transcripts_dir = content_dirs[0] / "transcripts" if content_dirs else paths.data_dir / "transcripts"

    if not transcripts_dir.exists():
        logger.error(f"No transcripts directory found at {transcripts_dir}")
        return 1

    write_index(transcripts_dir)
    logger.info(f"✓ Index generated at {transcripts_dir / 'index.md'}")
    return 0


@cli.command()
@click.argument("sources", nargs=-1, required=True)
@click.option("--resume", is_flag=True, help="Resume from last saved state")
@click.option(
    "--session-dir", type=click.Path(path_type=Path), help="Session directory for state (for resuming specific session)"
)
@click.option("--output-dir", type=click.Path(path_type=Path), help="Output directory for transcripts")
@click.option("--no-enhance", is_flag=True, help="Skip AI enhancements (summaries/quotes)")
@click.option("--force-download", is_flag=True, help="Skip cache and re-download audio even if it exists")
def transcribe(
    sources: tuple[str],
    resume: bool,
    session_dir: Path | None,
    output_dir: Path | None,
    no_enhance: bool,
    force_download: bool,
) -> int:
    """Transcribe videos or audio files.

    SOURCES can be YouTube URLs or local file paths.

    Examples:
        amplifier transcribe https://youtube.com/watch?v=...
        amplifier transcribe video.mp4 audio.mp3
        amplifier transcribe *.mp4 --resume
    """
    try:
        # Create state manager
        state_manager = StateManager(session_dir) if session_dir else StateManager()

        # Create pipeline with enhancement setting
        enhance = not no_enhance
        pipeline = TranscriptionPipeline(state_manager, enhance=enhance, force_download=force_download)

        # Override output directory if specified
        if output_dir:
            pipeline.storage.output_dir = output_dir
            pipeline.storage.output_dir.mkdir(parents=True, exist_ok=True)

        # Run pipeline
        success = pipeline.run(list(sources), resume=resume)

        return 0 if success else 1

    except KeyboardInterrupt:
        logger.info("\n⚠ Pipeline interrupted - state saved for resume")
        return 130

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return 1


def main():
    """Entry point for the CLI."""
    return cli()


if __name__ == "__main__":
    sys.exit(main())
