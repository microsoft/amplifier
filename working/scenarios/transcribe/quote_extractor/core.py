"""
Quote Extractor Core Implementation

Uses Anthropic Claude to extract memorable quotes from transcripts.
"""

import json
import os
from dataclasses import dataclass

from amplifier.utils.logger import get_logger

try:
    from anthropic import Anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = get_logger(__name__)


@dataclass
class Quote:
    """A memorable quote with context and timing."""

    text: str  # The quote itself
    timestamp: float  # Seconds into video
    timestamp_link: str | None  # YouTube link if applicable
    context: str  # Why this quote matters


class QuoteExtractor:
    """Extract memorable quotes from transcripts using Claude."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """Initialize quote extractor.

        Args:
            api_key: Anthropic API key. If not provided, reads from ANTHROPIC_API_KEY env var.
            model: Model to use. If not provided, uses AMPLIFIER_MODEL_DEFAULT or claude-3-haiku-20240307.
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic package not available. Install with: pip install anthropic")

        # Get API key from param or environment
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set. Please set it in your environment or pass it as a parameter.")

        # Get model from param or environment
        self.model = model or os.getenv("AMPLIFIER_MODEL_DEFAULT", "claude-3-haiku-20240307")

        # Initialize Anthropic client
        self.client = Anthropic(api_key=self.api_key)

    def extract(self, transcript, video_url: str | None, video_id: str) -> list[Quote]:
        """Extract memorable quotes from a transcript.

        Args:
            transcript: Transcript object with segments
            video_url: Optional YouTube URL for generating timestamp links
            video_id: Video ID for reference

        Returns:
            List of Quote objects with timestamps and context
        """
        # Prepare transcript text with timestamps for better extraction
        transcript_with_timestamps = self._format_transcript_with_timestamps(transcript)

        prompt = f"""Extract 3-5 memorable, insightful quotes from this transcript.

Choose quotes that:
- Capture key ideas or surprising insights
- Are complete thoughts (not fragments)
- Would stand alone as meaningful statements
- Represent different aspects of the content

For each quote, provide:
1. The exact quote text
2. The timestamp (in seconds) when it appears
3. Context explaining why this quote is significant

Transcript:
{transcript_with_timestamps[:15000]}  # Limit to first 15k chars

Please respond in JSON format with an array of quotes:
[
  {{
    "text": "The exact quote here",
    "timestamp": 123.5,
    "context": "Why this quote matters"
  }}
]
"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,  # Lower temperature for accurate extraction
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            # Parse the response - extract text from the first text block
            content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    content = block.text  # type: ignore[attr-defined]
                    break
            if not content:
                content = str(response.content[0])
            quotes_data = self._parse_quotes_response(content)

            # Convert to Quote objects with YouTube links if applicable
            quotes = []
            for quote_data in quotes_data:
                timestamp_link = None
                if video_url and "youtube.com" in video_url:
                    seconds = int(quote_data.get("timestamp", 0))
                    timestamp_link = f"https://youtube.com/watch?v={video_id}&t={seconds}s"

                quotes.append(
                    Quote(
                        text=quote_data.get("text", ""),
                        timestamp=quote_data.get("timestamp", 0.0),
                        timestamp_link=timestamp_link,
                        context=quote_data.get("context", ""),
                    )
                )

            return quotes

        except Exception as e:
            logger.error(f"Failed to extract quotes: {e}")
            # Return empty list on failure
            return []

    def _format_transcript_with_timestamps(self, transcript) -> str:
        """Format transcript with timestamps for better quote extraction.

        Args:
            transcript: Transcript object with segments

        Returns:
            Formatted transcript text with timestamps
        """
        if not transcript.segments:
            # If no segments, return plain text
            return transcript.text

        # Format with timestamps every few segments
        formatted = []
        for i, segment in enumerate(transcript.segments[:100]):  # Limit segments to avoid token limits
            if i % 5 == 0:  # Add timestamp every 5 segments
                minutes = int(segment.start // 60)
                seconds = int(segment.start % 60)
                formatted.append(f"\n[{minutes:02d}:{seconds:02d}] ")
            formatted.append(segment.text + " ")

        return "".join(formatted)

    def _parse_quotes_response(self, response_text: str) -> list[dict]:
        """Parse Claude's response to extract quote data.

        Args:
            response_text: Raw response from Claude

        Returns:
            List of quote dictionaries
        """
        try:
            # Try to find JSON in the response
            response_text = response_text.strip()

            # If the response starts with ```json, extract the JSON
            if response_text.startswith("```json"):
                response_text = response_text[7:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
            elif response_text.startswith("```"):
                response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]

            # Parse the JSON
            quotes_data = json.loads(response_text.strip())

            # Ensure it's a list
            if not isinstance(quotes_data, list):
                logger.warning("Quote response was not a list")
                return []

            return quotes_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse quotes JSON: {e}")
            logger.debug(f"Response text: {response_text[:500]}")
            return []
        except Exception as e:
            logger.error(f"Error parsing quotes response: {e}")
            return []
