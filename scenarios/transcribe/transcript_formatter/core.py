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

    Groups segments into paragraphs based on:
    - Target duration (30-60 seconds)
    - Natural pauses (>1.5 second gaps)
    - Maximum 5 minutes per paragraph

    Args:
        transcript: Transcript object with segments
        video_info: Video information
        video_url: Optional URL for timestamp linking
        target_paragraph_seconds: Target seconds per paragraph (default 30)

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

    # Format segments into paragraphs
    if transcript.segments:
        paragraphs = _group_segments_into_paragraphs(transcript.segments, target_paragraph_seconds, video_url)

        for paragraph in paragraphs:
            lines.append(paragraph)
            lines.append("")
    else:
        # No segments, just use plain text
        lines.append(transcript.text)
        lines.append("")

    return "\n".join(lines)


def _is_sentence_end(text: str) -> bool:
    """Check if text ends at a natural sentence boundary.

    Args:
        text: Text to check

    Returns:
        True if text ends with sentence-ending punctuation
    """
    if not text:
        return False

    # Strip trailing whitespace
    text = text.rstrip()
    if not text:
        return False

    # Check for sentence-ending punctuation
    # Handle: period, question mark, exclamation, with or without quotes
    sentence_endings = (".", "!", "?", '."', '!"', '?"', ".'", "!'", "?'")

    return text.endswith(sentence_endings)


def _group_segments_into_paragraphs(
    segments: list[TranscriptSegment],
    target_seconds: int,
    video_url: str | None = None,
    max_paragraph_seconds: int = 600,  # 10 minutes max (increased from 5)
) -> list[str]:
    """Group segments into readable paragraphs.

    Args:
        segments: List of transcript segments
        target_seconds: Target duration per paragraph
        video_url: Optional video URL for timestamp links
        max_paragraph_seconds: Maximum seconds per paragraph

    Returns:
        List of formatted paragraph strings
    """
    if not segments:
        return []

    paragraphs = []
    current_paragraph = []
    paragraph_start = segments[0].start
    paragraph_duration = 0

    for i, segment in enumerate(segments):
        # Check if we should start a new paragraph
        should_break = False

        # Calculate current paragraph duration
        if current_paragraph:
            paragraph_duration = segment.end - paragraph_start

        # Check for natural break at sentence boundary
        if i > 0 and current_paragraph:
            pause_duration = segment.start - segments[i - 1].end

            # Build current text to check sentence boundary
            current_text = " ".join(seg.text.strip() for seg in current_paragraph)

            # Break only if:
            # 1. There's a natural pause (>1.5 seconds)
            # 2. We've met minimum duration (target_seconds)
            # 3. We're at a sentence boundary
            if pause_duration > 1.5 and paragraph_duration >= target_seconds and _is_sentence_end(current_text):
                should_break = True

            # Log warning if paragraph is getting very long but not at sentence boundary
            if paragraph_duration >= max_paragraph_seconds and not _is_sentence_end(current_text):
                logger.warning(
                    f"Paragraph at {paragraph_duration:.1f}s exceeds max {max_paragraph_seconds}s "
                    "but not at sentence boundary - continuing to wait for punctuation"
                )

        # Start new paragraph if needed
        if should_break and current_paragraph:
            # Format and add current paragraph
            para_text = _format_paragraph(current_paragraph, paragraph_start, video_url)
            paragraphs.append(para_text)

            # Reset for new paragraph
            current_paragraph = []
            paragraph_start = segment.start
            paragraph_duration = 0

        # Add segment to current paragraph
        current_paragraph.append(segment)

    # Add final paragraph if any segments remain
    if current_paragraph:
        para_text = _format_paragraph(current_paragraph, paragraph_start, video_url)
        paragraphs.append(para_text)

    return paragraphs


def _format_paragraph(
    segments: list[TranscriptSegment],
    start_time: float,
    video_url: str | None = None,
) -> str:
    """Format a group of segments into a paragraph with timestamp.

    Args:
        segments: List of segments in the paragraph
        start_time: Start time in seconds
        video_url: Optional video URL for timestamp link

    Returns:
        Formatted paragraph string
    """
    # Combine segment texts
    text = " ".join(seg.text.strip() for seg in segments)

    # Format timestamp
    timestamp = _format_timestamp(start_time)

    # Create timestamp link if YouTube URL provided
    if video_url and _is_youtube_url(video_url):
        # Extract video ID and create timestamp link
        video_id = _extract_youtube_id(video_url)
        if video_id:
            timestamp_link = f"https://youtube.com/watch?v={video_id}&t={int(start_time)}"
            timestamp_prefix = f"[{timestamp}]({timestamp_link})"
        else:
            timestamp_prefix = f"[{timestamp}]"
    else:
        timestamp_prefix = f"[{timestamp}]"

    return f"{timestamp_prefix} {text}"


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
