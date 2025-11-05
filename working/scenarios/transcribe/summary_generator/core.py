"""
Summary Generator Core Implementation

Uses Anthropic Claude to generate concise summaries from transcripts.
"""

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
class Summary:
    """Structured summary with overview and key points."""

    overview: str  # 2-3 sentence overview
    key_points: list[str]  # 3-5 bullet points
    themes: list[str]  # Main themes discussed


class SummaryGenerator:
    """Generate concise summaries from transcripts using Claude."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """Initialize summary generator.

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

    def generate(self, transcript_text: str, title: str) -> Summary:
        """Generate a concise summary from transcript text.

        Args:
            transcript_text: Full transcript text
            title: Title of the video/content

        Returns:
            Summary object with overview, key points, and themes
        """
        prompt = f"""Please summarize this transcript titled "{title}".

Provide:
1. A 2-3 sentence overview that captures the essence of the content
2. 3-5 key takeaways or insights (as bullet points)
3. 2-4 main themes discussed

Focus on actionable insights and important ideas. Be concise.

Transcript:
{transcript_text[:15000]}  # Limit to first 15k chars to avoid token limits

Please respond in this exact format:
OVERVIEW:
[Your 2-3 sentence overview here]

KEY POINTS:
- [Point 1]
- [Point 2]
- [Point 3]
[etc.]

THEMES:
- [Theme 1]
- [Theme 2]
[etc.]
"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,  # Lower temperature for more focused summaries
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
            return self._parse_summary(content)

        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            # Return a fallback summary
            return Summary(
                overview=f"Summary generation failed for '{title}'.",
                key_points=["Unable to extract key points due to API error"],
                themes=["Error occurred during processing"],
            )

    def _parse_summary(self, response_text: str) -> Summary:
        """Parse Claude's response into a Summary object.

        Args:
            response_text: Raw response from Claude

        Returns:
            Parsed Summary object
        """
        lines = response_text.strip().split("\n")
        overview = ""
        key_points = []
        themes = []

        section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("OVERVIEW:"):
                section = "overview"
                continue
            if line.startswith("KEY POINTS:"):
                section = "key_points"
                continue
            if line.startswith("THEMES:"):
                section = "themes"
                continue

            if section == "overview":
                if overview:
                    overview += " " + line
                else:
                    overview = line
            elif section == "key_points" and line.startswith("- "):
                key_points.append(line[2:])
            elif section == "themes" and line.startswith("- "):
                themes.append(line[2:])

        # Ensure we have at least some content
        if not overview:
            overview = "Summary could not be generated."
        if not key_points:
            key_points = ["No key points extracted"]
        if not themes:
            themes = ["No themes identified"]

        return Summary(overview=overview, key_points=key_points, themes=themes)
