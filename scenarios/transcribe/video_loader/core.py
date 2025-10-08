"""
Video Loader Core Implementation

Extracts video information and downloads from YouTube or local files.
"""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from amplifier.utils.logger import get_logger

try:
    import yt_dlp

    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False

logger = get_logger(__name__)


@dataclass
class VideoInfo:
    """Video information container."""

    source: str  # URL or file path
    type: str  # "url" or "file"
    title: str
    id: str
    duration: float  # seconds
    description: str = ""
    uploader: str = ""
    audio_path: Path | None = None


class VideoLoader:
    """Load videos from URLs or local files."""

    def __init__(self, cookies_file: Path | None = None):
        """Initialize video loader.

        Args:
            cookies_file: Optional path to cookies file for yt-dlp
        """
        self.cookies_file = cookies_file
        self.yt_dlp_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
        }
        if cookies_file and cookies_file.exists():
            self.yt_dlp_opts["cookiefile"] = str(cookies_file)

    def load(self, source: str) -> VideoInfo:
        """Load video information from URL or file.

        Args:
            source: YouTube URL or local file path

        Returns:
            VideoInfo object with video metadata

        Raises:
            ValueError: If source cannot be loaded
        """
        if self._is_url(source):
            return self._load_from_url(source)
        return self._load_from_file(source)

    def _is_url(self, source: str) -> bool:
        """Check if source is a URL."""
        return source.startswith(("http://", "https://", "www."))

    def _load_from_url(self, url: str) -> VideoInfo:
        """Load video info from YouTube URL."""
        if not YT_DLP_AVAILABLE:
            raise ValueError("yt-dlp is not installed. Install with: pip install yt-dlp")

        logger.info(f"Loading video info from: {url}")

        try:
            with yt_dlp.YoutubeDL(self.yt_dlp_opts) as ydl:  # type: ignore
                info = ydl.extract_info(url, download=False)

            return VideoInfo(
                source=url,
                type="url",
                title=str(info.get("title", "Unknown")),
                id=str(info.get("id", url)),
                duration=float(info.get("duration") or 0),
                description=str(info.get("description", "")),
                uploader=str(info.get("uploader", "")),
            )
        except Exception as e:
            raise ValueError(f"Failed to load URL {url}: {e}")

    def _load_from_file(self, filepath: str) -> VideoInfo:
        """Load video info from local file."""
        path = Path(filepath)

        if not path.exists():
            raise ValueError(f"File not found: {filepath}")
        if not path.is_file():
            raise ValueError(f"Not a file: {filepath}")

        logger.info(f"Loading video info from: {path.name}")

        # Get duration using ffprobe
        duration = 0.0
        try:
            cmd = [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                str(path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            probe_info = json.loads(result.stdout)
            if "format" in probe_info and "duration" in probe_info["format"]:
                duration = float(probe_info["format"]["duration"])
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Could not get duration: {e}")

        return VideoInfo(
            source=str(path.absolute()),
            type="file",
            title=path.stem,
            id=path.stem,
            duration=duration,
        )

    def download_audio(
        self, url: str, output_dir: Path, output_filename: str = "audio.mp3", use_cache: bool = True
    ) -> Path:
        """Download audio from YouTube URL.

        Args:
            url: YouTube URL
            output_dir: Directory to save audio
            output_filename: Name for the output file (default: "audio.mp3")
            use_cache: If True, skip download if file exists (default: True)

        Returns:
            Path to downloaded audio file

        Raises:
            ValueError: If download fails
        """
        if not YT_DLP_AVAILABLE:
            raise ValueError("yt-dlp is not installed")

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / output_filename

        # Check cache
        if use_cache and output_path.exists():
            logger.info(f"✓ Using cached audio: {output_path.name}")
            return output_path

        logger.info(f"Downloading audio from: {url}")

        # Configure for audio extraction
        # Remove extension from output filename for yt-dlp template
        output_stem = output_path.stem
        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "outtmpl": str(output_dir / f"{output_stem}.%(ext)s"),
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
        }

        if self.cookies_file and self.cookies_file.exists():
            ydl_opts["cookiefile"] = str(self.cookies_file)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
                ydl.extract_info(url, download=True)

                # The file should be at output_path after conversion to mp3
                if output_path.exists():
                    logger.info(f"Audio saved to: {output_path.name}")
                    return output_path

                # If not at expected location, look for it
                # Check for various extensions in case conversion didn't happen
                for ext in [".mp3", ".m4a", ".opus", ".wav"]:
                    possible_path = output_dir / f"{output_stem}{ext}"
                    if possible_path.exists():
                        # Move to expected location
                        possible_path.rename(output_path)
                        logger.info(f"Audio saved to: {output_path.name}")
                        return output_path

                raise ValueError("Could not find downloaded audio file")

        except Exception as e:
            raise ValueError(f"Failed to download audio: {e}")
