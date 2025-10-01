"""Prompt generation for illustration points."""

from pathlib import Path

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit.defensive.llm_parsing import parse_llm_json
from amplifier.utils.logger import get_logger

from ..models import IllustrationPoint
from ..models import ImagePrompt

logger = get_logger(__name__)


class PromptGenerator:
    """Generates image prompts using Claude for consistency."""

    def __init__(self, style_params: dict[str, str] | None = None):
        """Initialize prompt generator.

        Args:
            style_params: Style parameters for image generation
        """
        self.style_params = style_params or {}

    async def generate_prompts(
        self,
        points: list[IllustrationPoint],
        article_path: Path,
    ) -> list[ImagePrompt]:
        """Generate image prompts for illustration points.

        Args:
            points: List of identified illustration points
            article_path: Path to original article for context

        Returns:
            List of image prompts with style consistency
        """
        logger.info(f"Generating prompts for {len(points)} illustration points")

        # Read article for context
        article_content = article_path.read_text(encoding="utf-8")[:4000]

        # Extract or define style
        if not self.style_params:
            self.style_params = self._extract_style_from_article(article_content)

        style_description = self._create_style_description()

        prompts = []
        for i, point in enumerate(points):
            try:
                prompt = await self._generate_single_prompt(point, i, article_content, style_description)
                prompts.append(prompt)
                logger.info(f"Generated prompt {i + 1}/{len(points)}")
            except Exception as e:
                logger.error(f"Failed to generate prompt {i + 1}: {e}")
                # Create fallback prompt
                prompts.append(self._create_fallback_prompt(point, i))

        return prompts

    async def _generate_single_prompt(
        self,
        point: IllustrationPoint,
        index: int,
        article_context: str,
        style_description: str,
    ) -> ImagePrompt:
        """Generate a single image prompt.

        Args:
            point: Illustration point
            index: Point index
            article_context: Article content for context
            style_description: Style requirements

        Returns:
            Generated image prompt
        """
        prompt = f"""Generate an image prompt for an illustration at this point in an article.

Article context (truncated):
{article_context}

Illustration point:
- Section: {point.section_title}
- Context before: {point.context_before}
- Context after: {point.context_after}
- Placement: {point.suggested_placement}
- Importance: {point.importance}

Style requirements:
{style_description}

Create a detailed image generation prompt that:
1. Relates directly to the content
2. Is appropriate for AI image generation (no text, clear subjects)
3. Maintains consistent style with other images
4. Avoids controversial or problematic content

Return JSON with:
{{
  "base_prompt": "Main description of the image",
  "style_modifiers": ["modifier1", "modifier2"],
  "full_prompt": "Complete prompt combining base and modifiers",
  "metadata": {{
    "mood": "...",
    "color_palette": "...",
    "composition": "..."
  }}
}}"""

        # Use ClaudeSession as async context manager
        async with ClaudeSession(
            options=SessionOptions(
                system_prompt="You are an expert at creating image generation prompts. Respond with JSON only.",
                stream_output=False,
            )
        ) as session:
            response = await session.query(prompt)

            if response.error:
                raise RuntimeError(f"Claude query failed: {response.error}")

            if not response.content:
                raise RuntimeError("Empty response from Claude")

            parsed = parse_llm_json(response.content)

        # Ensure parsed is a dict
        if not isinstance(parsed, dict):
            raise ValueError("Expected dict response from LLM")

        return ImagePrompt(
            illustration_id=f"illustration-{index + 1}",
            point=point,
            base_prompt=parsed.get("base_prompt", "Abstract illustration"),
            style_modifiers=parsed.get("style_modifiers", []),
            full_prompt=parsed.get("full_prompt", "Abstract illustration"),
            metadata=parsed.get("metadata", {}),
        )

    def _create_style_description(self) -> str:
        """Create style description from parameters.

        Returns:
            Style description string
        """
        if self.style_params.get("style"):
            return self.style_params["style"]

        # Build style from detected parameters
        if self.style_params:
            visual_style = self.style_params.get("visual_style", "")
            if visual_style:
                return visual_style

        # Default style
        return """Modern, clean illustration style:
- Minimalist with bold colors
- Professional and technical aesthetic
- Abstract or conceptual rather than literal
- Consistent color palette across all images
- High contrast for web viewing
- No text or words in images"""

    def _create_fallback_prompt(self, point: IllustrationPoint, index: int) -> ImagePrompt:
        """Create a basic fallback prompt.

        Args:
            point: Illustration point
            index: Point index

        Returns:
            Fallback image prompt
        """
        return ImagePrompt(
            illustration_id=f"illustration-{index + 1}",
            point=point,
            base_prompt=f"Abstract illustration for {point.section_title}",
            style_modifiers=["minimalist", "professional", "technical"],
            full_prompt=f"Abstract minimalist professional technical illustration for {point.section_title}",
            metadata={"fallback": "true"},
        )

    def _extract_style_from_article(self, content: str) -> dict[str, str]:
        """Extract style hints from article content.

        Args:
            content: Article content

        Returns:
            Dictionary of style parameters
        """
        style = {
            "tone": self._detect_tone(content),
            "domain": self._detect_domain(content),
            "technical_level": self._detect_technical_level(content),
        }

        # Suggest visual style based on analysis
        style["visual_style"] = self._suggest_visual_style(style)

        return style

    def _detect_tone(self, content: str) -> str:
        """Detect the tone of the article.

        Args:
            content: Article content

        Returns:
            Detected tone
        """
        content_lower = content.lower()

        if any(word in content_lower for word in ["joke", "funny", "humor", "lol", "haha"]):
            return "humorous"
        if any(word in content_lower for word in ["research", "study", "analysis", "data"]):
            return "academic"
        if any(word in content_lower for word in ["tutorial", "how to", "step by step", "guide"]):
            return "instructional"
        if any(word in content_lower for word in ["opinion", "believe", "think", "feel"]):
            return "opinion"
        return "professional"

    def _detect_domain(self, content: str) -> str:
        """Detect the domain/topic of the article.

        Args:
            content: Article content

        Returns:
            Detected domain
        """
        content_lower = content.lower()

        # Technology indicators
        tech_words = ["software", "code", "programming", "api", "database", "cloud", "ai", "machine learning"]
        business_words = ["business", "market", "customer", "revenue", "strategy", "growth"]
        science_words = ["research", "experiment", "hypothesis", "theory", "study"]

        tech_count = sum(1 for word in tech_words if word in content_lower)
        business_count = sum(1 for word in business_words if word in content_lower)
        science_count = sum(1 for word in science_words if word in content_lower)

        if tech_count > business_count and tech_count > science_count:
            return "technology"
        if business_count > science_count:
            return "business"
        if science_count > 0:
            return "science"
        return "general"

    def _detect_technical_level(self, content: str) -> str:
        """Detect the technical level of the article.

        Args:
            content: Article content

        Returns:
            Technical level
        """
        # Count code blocks
        code_blocks = content.count("```")

        # Count technical terms
        technical_terms = [
            "algorithm",
            "implementation",
            "architecture",
            "protocol",
            "framework",
            "library",
            "interface",
            "abstraction",
        ]
        tech_term_count = sum(1 for term in technical_terms if term.lower() in content.lower())

        if code_blocks > 5 or tech_term_count > 10:
            return "highly_technical"
        if code_blocks > 0 or tech_term_count > 3:
            return "technical"
        return "non_technical"

    def _suggest_visual_style(self, style_params: dict[str, str]) -> str:
        """Suggest a visual style based on content analysis.

        Args:
            style_params: Detected style parameters

        Returns:
            Suggested visual style
        """
        tone = style_params.get("tone", "professional")
        domain = style_params.get("domain", "general")
        tech_level = style_params.get("technical_level", "non_technical")

        # Map combinations to visual styles
        if domain == "technology" and tech_level == "highly_technical":
            return "clean technical diagrams, minimalist, monochrome with accent colors"
        if domain == "technology":
            return "modern tech illustration, flat design, bold colors"
        if domain == "business":
            return "professional business graphics, corporate colors, clean lines"
        if tone == "humorous":
            return "playful illustrations, bright colors, cartoon style"
        if tone == "academic":
            return "scholarly diagrams, muted colors, precise details"
        return "clean modern illustration, balanced colors, semi-abstract"
