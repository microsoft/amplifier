"""
Transcript Formatter Core Implementation

Formats transcript segments into readable paragraphs with timestamp links.
"""

from datetime import datetime

from amplifier.utils.logger import get_logger

from ..video_loader.core import VideoInfo
from ..whisper_transcriber.core import Transcript
from ..whisper_transcriber.core import TranscriptSegment

logger = get_logger(__name__)


def format_transcript(
    transcript: Transcript,
    video_info: VideoInfo,
    video_url: str | None = None,
    target_paragraph_seconds: int = 30,
) -> str:
    """
    Format transcript segments into readable paragraphs with timestamps.

    Uses a two-stage approach:
    1. Build continuous text with inline timestamps every 30 seconds
    2. Add paragraph breaks every 4-5 sentences

    Args:
        transcript: Transcript object with segments
        video_info: Video information
        video_url: Optional URL for timestamp linking
        target_paragraph_seconds: Target seconds between timestamps (default 30)

    Returns:
        Formatted markdown with timestamped paragraphs
    """
    lines = [
        f"# {video_info.title}",
        "",
        "## Video Information",
        "",
        f"- **Source**: {video_info.source}",
        f"- **Duration**: {_format_duration(video_info.duration)}",
    ]

    if video_info.uploader:
        lines.append(f"- **Uploader**: {video_info.uploader}")

    if transcript.language:
        lines.append(f"- **Language**: {transcript.language}")

    lines.extend(
        [
            f"- **Transcribed**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]
    )

    if video_info.description:
        lines.extend(
            [
                "## Description",
                "",
                video_info.description,
                "",
            ]
        )

    lines.extend(
        [
            "## Transcript",
            "",
        ]
    )

    # Format segments using two-stage approach
    if transcript.segments:
        # Stage 1: Build continuous text with inline timestamps
        continuous_text = _build_continuous_text_with_timestamps(
            transcript.segments, video_url, target_paragraph_seconds
        )

        # Stage 2: Add paragraph breaks
        formatted_text = _add_paragraph_breaks(continuous_text)

        lines.append(formatted_text)
        lines.append("")
    else:
        # No segments, just use plain text
        lines.append(transcript.text)
        lines.append("")

    return "\n".join(lines)


def _build_continuous_text_with_timestamps(
    segments: list[TranscriptSegment],
    video_url: str | None,
    timestamp_interval: int = 30,
) -> str:
    """Build continuous text with inline timestamps every 30 seconds.

    Stage 1 of the formatting process: Creates flowing text with timestamps
    inserted inline at regular intervals.

    Args:
        segments: List of transcript segments
        video_url: Optional URL for timestamp linking
        timestamp_interval: Seconds between timestamps (default 30)

    Returns:
        Continuous text with inline timestamps
    """
    if not segments:
        return ""

    text_parts = []
    last_timestamp_time = 0.0

    for segment in segments:
        # Check if we need a timestamp (every interval)
        if segment.start >= last_timestamp_time + timestamp_interval:
            # Create timestamp link
            timestamp_str = _format_timestamp(segment.start)

            if video_url and _is_youtube_url(video_url):
                video_id = _extract_youtube_id(video_url)
                if video_id:
                    link = f"https://youtube.com/watch?v={video_id}&t={int(segment.start)}"
                    timestamp_text = f" [{timestamp_str}]({link})"
                else:
                    timestamp_text = f" [{timestamp_str}]"
            else:
                timestamp_text = f" [{timestamp_str}]"

            text_parts.append(timestamp_text)
            last_timestamp_time = segment.start

        # Add segment text with space
        text_parts.append(" " + segment.text.strip())

    return "".join(text_parts).strip()


def _add_paragraph_breaks(text: str) -> str:
    """Add paragraph breaks every 4-5 sentences without changing content.

    Stage 2 of the formatting process: Inserts paragraph breaks (double newlines)
    at natural boundaries without altering the text content.

    Args:
        text: Continuous text with inline timestamps

    Returns:
        Text with paragraph breaks added
    """
    import re

    if not text:
        return ""

    # Split on sentence endings while preserving everything
    # Pattern: look for . ! ? followed by space
    sentences = re.split(r"(?<=[.!?])\s+", text)

    result = []
    sentence_count = 0
    current_paragraph = []

    for i, sentence in enumerate(sentences):
        current_paragraph.append(sentence)
        sentence_count += 1

        # Add paragraph break after 4-5 sentences
        if sentence_count >= 4:
            # Check if next sentence starts with continuation word
            if i + 1 < len(sentences):
                next_sentence = sentences[i + 1]
                # Get first word (ignoring timestamp links)
                # Remove timestamp pattern first
                clean_next = re.sub(r"\s*\[[^\]]+\](?:\([^)]+\))?\s*", " ", next_sentence).strip()
                words = clean_next.split()

                if words:
                    first_word = words[0].lower()

                    # Don't break before continuations
                    continuation_words = [
                        "but",
                        "and",
                        "so",
                        "because",
                        "however",
                        "although",
                        "while",
                        "yet",
                        "furthermore",
                        "moreover",
                        "therefore",
                        "thus",
                    ]

                    if first_word not in continuation_words:
                        # Join current paragraph and add to result
                        result.append(" ".join(current_paragraph))
                        result.append("\n\n")
                        current_paragraph = []
                        sentence_count = 0
            else:
                # Last sentence, just add it
                result.append(" ".join(current_paragraph))

    # Add any remaining sentences
    if current_paragraph:
        result.append(" ".join(current_paragraph))

    return "".join(result)


def _format_duration(seconds: float) -> str:
    """Format duration as HH:MM:SS or MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def _format_timestamp(seconds: float) -> str:
    """Format timestamp as MM:SS or HH:MM:SS."""
    return _format_duration(seconds)


def _is_youtube_url(url: str) -> bool:
    """Check if URL is from YouTube."""
    youtube_domains = [
        "youtube.com",
        "youtu.be",
        "www.youtube.com",
        "m.youtube.com",
    ]
    return any(domain in url.lower() for domain in youtube_domains)


def _extract_youtube_id(url: str) -> str | None:
    """Extract YouTube video ID from URL.

    Handles formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    """
    import re

    # Pattern for various YouTube URL formats
    patterns = [
        r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None
