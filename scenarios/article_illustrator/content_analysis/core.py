"""Content analysis for illustration opportunities."""

from pathlib import Path

from openai import OpenAI

from amplifier.ccsdk_toolkit.defensive.llm_parsing import parse_llm_json
from amplifier.utils.logger import get_logger

from ..models import IllustrationPoint

logger = get_logger(__name__)


class ContentAnalyzer:
    """Analyzes markdown articles to identify illustration opportunities."""

    def __init__(self, max_images: int = 5):
        """Initialize content analyzer.

        Args:
            max_images: Maximum number of images to generate
        """
        self.max_images = max_images
        self.client = OpenAI()

    async def analyze(self, article_path: Path) -> list[IllustrationPoint]:
        """Analyze article and identify illustration points.

        Args:
            article_path: Path to markdown article

        Returns:
            List of illustration points ranked by importance
        """
        logger.info(f"Analyzing article: {article_path}")

        # Read article content
        content = article_path.read_text(encoding="utf-8")

        # Create analysis prompt
        prompt = self._create_analysis_prompt(content)

        try:
            # Call OpenAI to analyze content
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at identifying visual illustration opportunities in written content. Respond with JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )

            # Parse response
            message_content = response.choices[0].message.content
            if not message_content:
                raise ValueError("Empty response from OpenAI")

            analysis = parse_llm_json(message_content)

            # Ensure analysis is a dict
            if not isinstance(analysis, dict):
                raise ValueError("Expected dict response from LLM")

            # Convert to IllustrationPoint objects
            points = []
            for point_data in analysis.get("illustration_points", [])[: self.max_images]:
                points.append(IllustrationPoint(**point_data))

            logger.info(f"Identified {len(points)} illustration points")
            return points

        except Exception as e:
            logger.error(f"Failed to analyze content: {e}")
            # Return minimal fallback points
            return self._create_fallback_points(content)

    def _create_analysis_prompt(self, content: str) -> str:
        """Create prompt for content analysis.

        Args:
            content: Article content

        Returns:
            Analysis prompt
        """
        return f"""Analyze this markdown article and identify the {self.max_images} best places to add illustrations.

For each illustration point, provide:
- section_title: The section heading
- section_index: Index of the section (0-based)
- line_number: Approximate line number
- context_before: 100 chars of text before the point
- context_after: 100 chars of text after the point
- importance: "high", "medium", or "low"
- suggested_placement: "before_section", "after_intro", or "mid_section"

Focus on:
1. Key concepts that would benefit from visual explanation
2. Section transitions that need visual breaks
3. Complex ideas that images could clarify
4. Opening sections that set the tone

Article content:
```markdown
{content[:8000]}
```

Return JSON with structure:
{{
  "illustration_points": [
    {{
      "section_title": "...",
      "section_index": 0,
      "line_number": 10,
      "context_before": "...",
      "context_after": "...",
      "importance": "high",
      "suggested_placement": "before_section"
    }}
  ]
}}"""

    def _create_fallback_points(self, content: str) -> list[IllustrationPoint]:
        """Create basic illustration points as fallback.

        Args:
            content: Article content

        Returns:
            List of fallback illustration points
        """
        lines = content.split("\n")

        # Find headers
        headers = []
        for i, line in enumerate(lines):
            if line.startswith("#"):
                headers.append((i, line.strip("#").strip()))

        # Create points for first few headers
        points = []
        for i, (line_num, title) in enumerate(headers[: self.max_images]):
            points.append(
                IllustrationPoint(
                    section_title=title,
                    section_index=i,
                    line_number=line_num,
                    context_before=lines[max(0, line_num - 2)] if line_num > 0 else "",
                    context_after=lines[min(len(lines) - 1, line_num + 2)],
                    importance="medium",
                    suggested_placement="before_section",
                )
            )

        return points
