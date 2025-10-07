"""
Whisper Transcriber Core Implementation

Uses OpenAI Whisper API to transcribe audio files.
"""

import os
import time
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

from amplifier.utils.logger import get_logger

try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = get_logger(__name__)


@dataclass
class TranscriptSegment:
    """Individual transcript segment with timing."""

    id: int
    start: float
    end: float
    text: str


@dataclass
class Transcript:
    """Complete transcript with segments and metadata."""

    text: str
    language: str | None = None
    duration: float | None = None
    segments: list[TranscriptSegment] = field(default_factory=list)


class WhisperTranscriber:
    """Transcribe audio using OpenAI Whisper API."""

    def __init__(self, api_key: str | None = None, model: str = "whisper-1"):
        """Initialize transcriber.

        Args:
            api_key: OpenAI API key (or from OPENAI_API_KEY env)
            model: Whisper model to use
        """
        if not OPENAI_AVAILABLE:
            raise ValueError("openai package not installed. Install with: pip install openai")

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required (set OPENAI_API_KEY env var)")

        self.client = OpenAI(api_key=self.api_key)
        self.model = model

    def transcribe(
        self,
        audio_path: Path,
        language: str | None = None,
        prompt: str | None = None,
        max_retries: int = 3,
    ) -> Transcript:
        """Transcribe audio file.

        Args:
            audio_path: Path to audio file
            language: Optional language code (e.g., 'en')
            prompt: Optional prompt to guide transcription
            max_retries: Maximum retry attempts

        Returns:
            Transcript object with text and segments

        Raises:
            ValueError: If transcription fails
        """
        if not audio_path.exists():
            raise ValueError(f"Audio file not found: {audio_path}")

        logger.info(f"Transcribing: {audio_path.name}")

        # Validate file size
        max_size = 25 * 1024 * 1024  # 25MB
        if audio_path.stat().st_size > max_size:
            raise ValueError(f"Audio file too large: {audio_path.stat().st_size / 1024 / 1024:.1f}MB (max 25MB)")

        # Attempt transcription with retries
        last_error = None
        for attempt in range(max_retries):
            try:
                with open(audio_path, "rb") as audio_file:
                    # Build kwargs
                    kwargs = {
                        "model": self.model,
                        "file": audio_file,
                        "response_format": "verbose_json",
                    }
                    if language:
                        kwargs["language"] = language
                    if prompt:
                        kwargs["prompt"] = prompt

                    response = self.client.audio.transcriptions.create(**kwargs)

                # Convert response to Transcript
                segments = []
                if hasattr(response, "segments"):
                    for seg in response.segments:
                        segments.append(
                            TranscriptSegment(
                                id=getattr(seg, "id", 0),
                                start=getattr(seg, "start", 0.0),
                                end=getattr(seg, "end", 0.0),
                                text=getattr(seg, "text", ""),
                            )
                        )

                transcript = Transcript(
                    text=response.text,
                    language=getattr(response, "language", language),
                    duration=getattr(response, "duration", None),
                    segments=segments,
                )

                logger.info(f"Transcription complete: {len(transcript.text)} chars, {len(segments)} segments")
                return transcript

            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                    continue

        raise ValueError(f"Transcription failed after {max_retries} attempts: {last_error}")

    def estimate_cost(self, duration_seconds: float) -> float:
        """Estimate transcription cost.

        Args:
            duration_seconds: Audio duration in seconds

        Returns:
            Estimated cost in USD
        """
        # OpenAI Whisper pricing: $0.006 per minute
        cost_per_minute = 0.006
        duration_minutes = duration_seconds / 60
        return duration_minutes * cost_per_minute
