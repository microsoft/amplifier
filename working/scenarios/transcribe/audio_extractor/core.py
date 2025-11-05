"""
Audio Extractor Core Implementation

Extracts audio from video files and compresses for API limits.
"""

import subprocess
from pathlib import Path

from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class AudioExtractor:
    """Extract and compress audio from video files."""

    def __init__(self, temp_dir: Path | None = None):
        """Initialize audio extractor.

        Args:
            temp_dir: Temporary directory for audio files
        """
        self.temp_dir = temp_dir or Path(".data/transcribe/temp")
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def extract(self, video_path: Path, output_format: str = "mp3") -> Path:
        """Extract audio from video file.

        Args:
            video_path: Path to video file
            output_format: Audio format (mp3, wav, m4a)

        Returns:
            Path to extracted audio file

        Raises:
            ValueError: If extraction fails
        """
        # Generate output path
        output_path = self.temp_dir / f"{video_path.stem}.{output_format}"

        # Skip if already extracted
        if output_path.exists() and output_path.stat().st_size > 0:
            logger.info(f"Using existing audio: {output_path.name}")
            return output_path

        logger.info(f"Extracting audio from: {video_path.name}")

        # Build ffmpeg command
        cmd = [
            "ffmpeg",
            "-i",
            str(video_path),
            "-vn",  # No video
            "-acodec",
            self._get_codec(output_format),
            "-y",  # Overwrite
            str(output_path),
        ]

        # Add quality settings for mp3
        if output_format == "mp3":
            cmd.extend(["-ab", "192k"])

        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Audio extracted to: {output_path.name}")
            return output_path
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Failed to extract audio: {e.stderr}")

    def compress_for_api(self, audio_path: Path, max_size_mb: int = 25) -> Path:
        """Compress audio to fit within API size limit.

        Args:
            audio_path: Path to audio file
            max_size_mb: Maximum size in MB (25MB for OpenAI)

        Returns:
            Path to compressed audio (or original if small enough)

        Raises:
            ValueError: If compression fails
        """
        max_size_bytes = max_size_mb * 1024 * 1024

        # Check if compression needed
        if audio_path.stat().st_size <= max_size_bytes:
            logger.info(f"Audio size OK: {audio_path.stat().st_size / 1024 / 1024:.1f}MB")
            return audio_path

        logger.info(f"Compressing audio from {audio_path.stat().st_size / 1024 / 1024:.1f}MB")

        # Create compressed output path
        compressed_path = audio_path.parent / f"{audio_path.stem}_compressed.mp3"

        # Get duration for bitrate calculation
        try:
            duration_cmd = [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(audio_path),
            ]
            result = subprocess.run(duration_cmd, capture_output=True, text=True, check=True)
            duration = float(result.stdout.strip())

            # Calculate target bitrate (90% of max for safety)
            target_bitrate = int((max_size_bytes * 8 * 0.9) / duration / 1000)  # kbps
            target_bitrate = min(target_bitrate, 128)  # Cap at 128kbps
            target_bitrate = max(target_bitrate, 16)  # Min 16kbps

            logger.info(f"Target bitrate: {target_bitrate}kbps")

            # Compress audio
            cmd = [
                "ffmpeg",
                "-i",
                str(audio_path),
                "-vn",
                "-acodec",
                "libmp3lame",
                "-b:a",
                f"{target_bitrate}k",
                "-ar",
                "16000",  # Lower sample rate for speech
                "-ac",
                "1",  # Mono
                "-y",
                str(compressed_path),
            ]

            subprocess.run(cmd, capture_output=True, check=True)

            final_size = compressed_path.stat().st_size
            logger.info(f"Compressed to: {final_size / 1024 / 1024:.1f}MB")

            # If still too large, try even lower bitrate
            if final_size > max_size_bytes:
                logger.warning("Still too large, trying lower bitrate")
                target_bitrate = int(target_bitrate * 0.7)
                cmd[cmd.index("-b:a") + 1] = f"{target_bitrate}k"
                subprocess.run(cmd, capture_output=True, check=True)
                final_size = compressed_path.stat().st_size
                logger.info(f"Re-compressed to: {final_size / 1024 / 1024:.1f}MB")

            return compressed_path

        except subprocess.CalledProcessError as e:
            logger.error(f"Compression failed: {e}")
            # Return original and let caller handle
            return audio_path

    def _get_codec(self, format: str) -> str:
        """Get appropriate codec for audio format."""
        codec_map = {
            "mp3": "libmp3lame",
            "wav": "pcm_s16le",
            "m4a": "aac",
            "aac": "aac",
            "opus": "libopus",
            "flac": "flac",
        }
        return codec_map.get(format, "copy")

    def cleanup(self, audio_path: Path) -> None:
        """Remove temporary audio file.

        Args:
            audio_path: Path to audio file to remove
        """
        if audio_path.exists():
            try:
                audio_path.unlink()
                logger.debug(f"Cleaned up: {audio_path.name}")
            except OSError as e:
                logger.warning(f"Could not remove {audio_path.name}: {e}")

    def cleanup_all(self) -> None:
        """Remove all temporary audio files."""
        if self.temp_dir.exists():
            for audio_file in self.temp_dir.glob("*"):
                if audio_file.is_file():
                    self.cleanup(audio_file)
