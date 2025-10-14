"""
Storage Core Implementation

Saves transcripts in multiple formats to organized directories.
"""

import json
from datetime import datetime
from pathlib import Path

from amplifier.config.paths import paths
from amplifier.utils.logger import get_logger

from ..video_loader.core import VideoInfo
from ..whisper_transcriber.core import Transcript

logger = get_logger(__name__)


class TranscriptStorage:
    """Save transcripts in multiple formats."""

    def __init__(self, output_dir: Path | None = None):
        """Initialize storage.

        Args:
            output_dir: Base output directory (default: AMPLIFIER_CONTENT_DIRS/transcripts)
        """
        # Track if we're in test mode (custom output directory provided)
        self._test_mode = output_dir is not None

        if output_dir:
            # Custom output directory (test scenario)
            # Use the provided directory as base for both content and data
            self._output_dir = output_dir
            self._data_dir = output_dir  # In test mode, keep everything together
        else:
            # Production scenario - use dual-directory architecture
            # Use first content directory if available, otherwise fall back to data_dir
            content_dirs = paths.get_all_content_paths()
            if content_dirs:
                self._output_dir = content_dirs[0] / "transcripts"
            else:
                logger.warning("No content directories found, using .data/transcripts instead")
                self._output_dir = paths.data_dir / "transcripts"

            # In production, technical artifacts go to .data directory
            self._data_dir = paths.data_dir / "transcripts"
            self._data_dir.mkdir(parents=True, exist_ok=True)

        self._output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def output_dir(self) -> Path:
        """Get the output directory."""
        return self._output_dir

    @output_dir.setter
    def output_dir(self, value: Path) -> None:
        """Set the output directory. In test mode, also updates data_dir."""
        self._output_dir = value
        if self._test_mode:
            # Keep data_dir synchronized with output_dir in test mode
            self._data_dir = value
        self._output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def data_dir(self) -> Path:
        """Get the data directory."""
        return self._data_dir

    def save(
        self,
        transcript: Transcript,
        video_info: VideoInfo,
        audio_path: Path | None = None,
        save_json: bool = True,
        save_markdown: bool = True,
        save_vtt: bool = True,
        save_srt: bool = True,
    ) -> Path:
        """Save transcript in multiple formats.

        Args:
            transcript: Transcript object
            video_info: Video information
            audio_path: Path to audio file to save (optional)
            save_json: Save as JSON
            save_markdown: Save as Markdown
            save_vtt: Save as WebVTT
            save_srt: Save as SRT

        Returns:
            Path to output directory containing all files
        """
        # Create output directories for this video
        video_id = self._sanitize_filename(video_info.id)

        # User content directory (AMPLIFIER_CONTENT_DIRS)
        video_dir = self.output_dir / video_id
        video_dir.mkdir(parents=True, exist_ok=True)

        # Technical artifacts directory (.data)
        data_video_dir = self.data_dir / video_id
        data_video_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Saving user content to: {video_dir}")
        logger.info(f"Saving technical artifacts to: {data_video_dir}")

        # Save audio file if provided (goes to content dir)
        saved_audio_path = None
        if audio_path and audio_path.exists():
            saved_audio_path = self.save_audio(audio_path, video_dir)

        # Save in requested formats
        saved_files = []

        if save_json:
            # JSON goes to .data directory
            json_path = self._save_json(transcript, video_info, data_video_dir, video_dir, saved_audio_path)
            saved_files.append(f"JSON: {json_path.name}")

        if save_markdown:
            # Markdown goes to content directory
            md_path = self._save_markdown(transcript, video_info, video_dir)
            saved_files.append(f"MD: {md_path.name}")

        if save_vtt and transcript.segments:
            # VTT goes to .data directory
            vtt_path = self._save_vtt(transcript, data_video_dir)
            saved_files.append(f"VTT: {vtt_path.name}")

        if save_srt and transcript.segments:
            # SRT goes to .data directory
            srt_path = self._save_srt(transcript, data_video_dir)
            saved_files.append(f"SRT: {srt_path.name}")

        logger.info(f"Saved {len(saved_files)} files: {', '.join(saved_files)}")
        return video_dir  # Return content dir for compatibility

    def save_audio(self, audio_path: Path, output_dir: Path) -> Path:
        """Save audio file to output directory.

        Args:
            audio_path: Source audio file path
            output_dir: Target directory

        Returns:
            Path to saved audio file
        """
        import shutil

        target_path = output_dir / "audio.mp3"

        # Don't copy if already in place
        if audio_path.absolute() == target_path.absolute():
            return target_path

        # Copy audio file
        shutil.copy2(audio_path, target_path)
        logger.info(f"Saved audio to: {target_path}")

        return target_path

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize filename for filesystem."""
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, "_")
        # Limit length
        return name[:100]

    def _save_json(
        self,
        transcript: Transcript,
        video_info: VideoInfo,
        data_dir: Path,
        content_dir: Path,
        audio_path: Path | None = None,
    ) -> Path:
        """Save transcript as JSON with storage location metadata."""
        json_path = data_dir / "transcript.json"

        # Add audio metadata if audio file exists
        audio_metadata = None
        if audio_path and audio_path.exists():
            audio_metadata = {
                "filename": audio_path.name,
                "size_mb": round(audio_path.stat().st_size / (1024 * 1024), 2),
                "format": "mp3",
                "bitrate": "192k",
            }

        data = {
            "video": {
                "source": video_info.source,
                "title": video_info.title,
                "id": video_info.id,
                "duration": video_info.duration,
                "uploader": video_info.uploader,
                "description": video_info.description,
            },
            "transcript": {
                "text": transcript.text,
                "language": transcript.language,
                "duration": transcript.duration,
                "segments": [
                    {
                        "id": seg.id,
                        "start": seg.start,
                        "end": seg.end,
                        "text": seg.text,
                    }
                    for seg in transcript.segments
                ],
            },
            "audio": audio_metadata,
            "metadata": {
                "transcribed_at": datetime.now().isoformat(),
                "version": "1.0",
                "storage": {
                    "content_dir": str(content_dir),  # Where user content is
                    "data_dir": str(data_dir),  # Where technical artifacts are
                },
            },
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return json_path

    def _save_markdown(self, transcript: Transcript, video_info: VideoInfo, output_dir: Path) -> Path:
        """Save transcript as readable Markdown using the new formatter."""
        from ..transcript_formatter import format_transcript

        md_path = output_dir / "transcript.md"

        # Format transcript with paragraphs and timestamps
        formatted_content = format_transcript(
            transcript=transcript,
            video_info=video_info,
            video_url=video_info.source if "youtube" in video_info.source.lower() else None,
        )

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(formatted_content)

        return md_path

    def _save_vtt(self, transcript: Transcript, output_dir: Path) -> Path:
        """Save transcript as WebVTT."""
        vtt_path = output_dir / "transcript.vtt"

        lines = ["WEBVTT", ""]

        for seg in transcript.segments:
            start = self._seconds_to_vtt(seg.start)
            end = self._seconds_to_vtt(seg.end)
            lines.append(f"{start} --> {end}")
            lines.append(seg.text.strip())
            lines.append("")

        with open(vtt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return vtt_path

    def _save_srt(self, transcript: Transcript, output_dir: Path) -> Path:
        """Save transcript as SRT."""
        srt_path = output_dir / "transcript.srt"

        lines = []

        for i, seg in enumerate(transcript.segments, 1):
            start = self._seconds_to_srt(seg.start)
            end = self._seconds_to_srt(seg.end)
            lines.append(str(i))
            lines.append(f"{start} --> {end}")
            lines.append(seg.text.strip())
            lines.append("")

        with open(srt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return srt_path

    def _format_duration(self, seconds: float) -> str:
        """Format duration as HH:MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def _format_timestamp(self, seconds: float) -> str:
        """Format timestamp for markdown."""
        return self._format_duration(seconds)

    def _seconds_to_vtt(self, seconds: float) -> str:
        """Convert seconds to WebVTT timestamp (HH:MM:SS.mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

    def _seconds_to_srt(self, seconds: float) -> str:
        """Convert seconds to SRT timestamp (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def save_insights(
        self,
        summary: object | None,
        quotes: list | None,
        title: str,
        output_dir: Path,
    ) -> Path:
        """Save combined insights document with summary and quotes.

        Args:
            summary: Summary object with overview, key_points, and themes
            quotes: List of Quote objects
            title: Title of the content
            output_dir: Directory to save the insights

        Returns:
            Path to saved insights file
        """
        from ..insights_generator import generate_insights
        from ..quote_extractor.core import Quote
        from ..summary_generator.core import Summary

        # Validate inputs
        validated_summary = None
        if summary and isinstance(summary, Summary):
            validated_summary = summary
        elif summary:
            logger.warning("Invalid summary object provided, skipping summary")

        validated_quotes = None
        if quotes:
            validated_quotes = [q for q in quotes if isinstance(q, Quote)]
            if len(validated_quotes) < len(quotes):
                logger.warning(f"Filtered out {len(quotes) - len(validated_quotes)} invalid quote objects")

        # Generate insights document
        insights_content = generate_insights(
            summary=validated_summary,
            quotes=validated_quotes,
            title=title,
        )

        # Save to file
        insights_path = output_dir / "insights.md"
        with open(insights_path, "w", encoding="utf-8") as f:
            f.write(insights_content)

        logger.info(f"Saved insights to: {insights_path}")
        return insights_path
