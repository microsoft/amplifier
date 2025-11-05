"""
Style extraction core functionality.

Analyzes writings to identify author's unique style patterns.
"""

from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic import Field

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit.defensive import parse_llm_json
from amplifier.ccsdk_toolkit.defensive import retry_with_feedback
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class StyleProfile(BaseModel):
    """Author style profile extracted from writings."""

    tone: str = Field(description="Overall tone (formal, conversational, technical, etc.)")
    vocabulary_level: str = Field(description="Vocabulary complexity (simple, moderate, advanced)")
    sentence_structure: str = Field(description="Typical sentence patterns")
    paragraph_length: str = Field(description="Typical paragraph length preference")
    common_phrases: list[str] = Field(default_factory=list, description="Frequently used phrases")
    writing_patterns: list[str] = Field(default_factory=list, description="Common structural patterns")
    voice: str = Field(description="Active vs passive voice preference")
    examples: list[str] = Field(default_factory=list, description="Example sentences that capture style")


class StyleExtractor:
    """Extracts author style from writing samples."""

    def __init__(self):
        """Initialize style extractor."""
        self.profile: StyleProfile | None = None

    async def extract_style(self, writings_dir: Path) -> dict[str, Any]:
        """Extract style profile from writings directory.

        Args:
            writings_dir: Directory containing author's writings

        Returns:
            Style profile as dictionary
        """
        # Find all markdown files
        files = list(writings_dir.glob("**/*.md"))
        if not files:
            logger.warning(f"No markdown files found in {writings_dir}")
            return self._default_profile()

        logger.info(f"Analyzing {len(files)} writing samples:")
        for f in files[:3]:  # Show first 3
            logger.info(f"  • {f.name}")
        if len(files) > 3:
            logger.info(f"  ... and {len(files) - 3} more")

        # Read samples (limit to prevent context overflow)
        samples = []
        max_samples = 5
        max_chars_per_sample = 3000

        for file in files[:max_samples]:
            try:
                content = file.read_text()[:max_chars_per_sample]
                samples.append(f"=== {file.name} ===\n{content}")
            except Exception as e:
                logger.warning(f"Could not read {file}: {e}")

        if not samples:
            logger.warning("Could not read any writing samples")
            return self._default_profile()

        # Extract style with AI
        combined_samples = "\n\n".join(samples)
        profile = await self._analyze_with_ai(combined_samples)

        # Store profile
        self.profile = profile
        return profile.model_dump()

    async def _analyze_with_ai(self, samples: str) -> StyleProfile:
        """Analyze samples with AI to extract style.

        Args:
            samples: Combined writing samples

        Returns:
            Extracted style profile
        """
        prompt = f"""Analyze these writing samples to extract the author's style:

{samples}

Extract:
1. Overall tone (formal/casual/technical/conversational)
2. Vocabulary complexity level
3. Typical sentence structure patterns
4. Paragraph length preference
5. Common phrases or expressions
6. Recurring writing patterns
7. Voice preference (active/passive)
8. 3-5 example sentences that best capture the style

Return as JSON with keys: tone, vocabulary_level, sentence_structure, paragraph_length,
common_phrases (list), writing_patterns (list), voice, examples (list)"""

        options = SessionOptions(
            system_prompt="You are an expert writing style analyst.",
            retry_attempts=2,
        )

        try:
            async with ClaudeSession(options) as session:
                # Use retry_with_feedback for robust JSON extraction
                async def query_with_parsing(enhanced_prompt: str):
                    response = await session.query(enhanced_prompt)
                    if response and response.content:
                        parsed = parse_llm_json(response.content)
                        if parsed:
                            return parsed
                    return None

                # Retry with feedback if parsing fails
                parsed = await retry_with_feedback(
                    func=query_with_parsing, prompt=prompt, max_retries=3, provide_feedback=True
                )

                if parsed is None:
                    logger.warning("Could not extract style after retries, using defaults")
                    return StyleProfile(**self._default_profile())

                # Handle both dict and list responses from LLM
                # If LLM returns an array like [{...}], extract first element
                if isinstance(parsed, list):
                    if len(parsed) > 0 and isinstance(parsed[0], dict):
                        parsed = parsed[0]
                        logger.debug("Extracted style data from array response")
                    else:
                        logger.warning("LLM returned empty or invalid array, using defaults")
                        return StyleProfile(**self._default_profile())
                elif not isinstance(parsed, dict):
                    logger.warning(f"Unexpected response type: {type(parsed)}, using defaults")
                    return StyleProfile(**self._default_profile())

                # Log what we extracted
                logger.info("Successfully extracted style profile:")
                logger.info(f"  - Tone: {parsed.get('tone', 'N/A')}")
                logger.info(f"  - Voice: {parsed.get('voice', 'N/A')}")
                logger.info(f"  - Vocabulary: {parsed.get('vocabulary_level', 'N/A')}")

                # Ensure we have all required fields
                profile_data = {
                    "tone": parsed.get("tone", "conversational"),
                    "vocabulary_level": parsed.get("vocabulary_level", "moderate"),
                    "sentence_structure": parsed.get("sentence_structure", "varied"),
                    "paragraph_length": parsed.get("paragraph_length", "medium"),
                    "common_phrases": parsed.get("common_phrases", []),
                    "writing_patterns": parsed.get("writing_patterns", []),
                    "voice": parsed.get("voice", "active"),
                    "examples": parsed.get("examples", []),
                }

                return StyleProfile(**profile_data)

        except Exception as e:
            logger.error(f"Style extraction failed: {e}")
            return StyleProfile(**self._default_profile())

    def _default_profile(self) -> dict[str, Any]:
        """Return default style profile when extraction fails."""
        logger.info("Using default style profile")
        default = StyleProfile(
            tone="conversational",
            vocabulary_level="moderate",
            sentence_structure="varied",
            paragraph_length="medium",
            common_phrases=[],
            writing_patterns=["introduction-body-conclusion", "problem-solution"],
            voice="active",
            examples=["Clear and direct communication.", "Focus on practical value."],
        )
        return default.model_dump()
