"""
Blog writer core functionality.

Transforms brain dumps into polished blog posts using style profile.
"""

from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class BlogWriter:
    """Generates blog posts from brain dumps."""

    async def write_blog(
        self,
        brain_dump: str,
        style_profile: dict[str, Any],
        previous_draft: str | None = None,
        feedback: dict[str, Any] | None = None,
        additional_instructions: str | None = None,
    ) -> str:
        """Generate or revise blog post.

        Args:
            brain_dump: Original brain dump/idea content
            style_profile: Author's style profile
            previous_draft: Previous draft if revising
            feedback: Feedback to incorporate
            additional_instructions: Extra guidance (e.g., "remove private info")

        Returns:
            Generated blog post content
        """
        if previous_draft and feedback:
            logger.info("Revising blog based on feedback")
            return await self._revise_blog(previous_draft, feedback, style_profile, brain_dump, additional_instructions)
        logger.info("Writing initial blog draft")
        return await self._write_initial(brain_dump, style_profile, additional_instructions)

    async def _write_initial(
        self, brain_dump: str, style_profile: dict[str, Any], additional_instructions: str | None = None
    ) -> str:
        """Write initial blog post from brain dump.

        Args:
            brain_dump: Raw content to transform
            style_profile: Style to match
            additional_instructions: Extra guidance to follow

        Returns:
            Blog post content
        """
        # Build style description
        style_desc = self._format_style_description(style_profile)

        # Build instructions section if provided
        instructions_section = ""
        if additional_instructions:
            instructions_section = f"""
=== IMPORTANT INSTRUCTIONS ===
{additional_instructions}

YOU MUST follow these instructions carefully when writing the blog post.
"""

        prompt = f"""Transform this idea/brain dump into a polished blog post:

=== IDEA/BRAIN DUMP ===
{brain_dump}

=== STYLE TO MATCH ===
{style_desc}
{instructions_section}
Write a complete blog post that:
1. Captures all key ideas from the brain dump
2. Matches the author's style closely
3. Follows any additional instructions provided above
4. Has a compelling title and introduction
5. Flows logically with clear sections
6. Includes a strong conclusion

Return ONLY the blog post content in markdown format, starting with # Title."""

        options = SessionOptions(
            system_prompt="You are an expert blog writer who can match any writing style.",
            retry_attempts=2,
        )

        try:
            async with ClaudeSession(options) as session:
                response = await session.query(prompt)
                return response.content.strip()
        except Exception as e:
            logger.error(f"Blog generation failed: {e}")
            # Return a basic transformation as fallback
            return self._fallback_transform(brain_dump)

    async def _revise_blog(
        self,
        previous_draft: str,
        feedback: dict[str, Any],
        style_profile: dict[str, Any],
        brain_dump: str,
        additional_instructions: str | None = None,
    ) -> str:
        """Revise blog based on feedback.

        Args:
            previous_draft: Current blog draft
            feedback: Structured feedback to apply
            style_profile: Style to maintain
            brain_dump: Original content for reference
            additional_instructions: Extra guidance to follow

        Returns:
            Revised blog content
        """
        # Format feedback for prompt
        feedback_text = self._format_feedback(feedback)
        style_desc = self._format_style_description(style_profile)

        # Build instructions section if provided
        instructions_section = ""
        if additional_instructions:
            instructions_section = f"""
=== IMPORTANT INSTRUCTIONS (MUST FOLLOW) ===
{additional_instructions}
"""

        prompt = f"""Revise this blog post based on the feedback:

=== ORIGINAL IDEA/BRAIN DUMP (for reference) ===
{brain_dump}

=== CURRENT DRAFT ===
{previous_draft}

=== FEEDBACK TO APPLY ===
{feedback_text}

=== STYLE TO MAINTAIN ===
{style_desc}
{instructions_section}
Revise the blog to:
1. Address all feedback points
2. Maintain the author's style
3. Follow any additional instructions provided above
4. Keep the overall structure unless specifically asked to change
5. Preserve what's working well

Return ONLY the revised blog post content in markdown format."""

        options = SessionOptions(
            system_prompt="You are an expert editor who improves blogs based on feedback.",
            retry_attempts=2,
        )

        try:
            async with ClaudeSession(options) as session:
                response = await session.query(prompt)
                return response.content.strip()
        except Exception as e:
            logger.error(f"Blog revision failed: {e}")
            # Return previous draft if revision fails
            return previous_draft

    def _format_style_description(self, style_profile: dict[str, Any]) -> str:
        """Format style profile for prompt.

        Args:
            style_profile: Style dictionary

        Returns:
            Formatted description
        """
        desc = []
        desc.append(f"Tone: {style_profile.get('tone', 'conversational')}")
        desc.append(f"Vocabulary: {style_profile.get('vocabulary_level', 'moderate')}")
        desc.append(f"Sentences: {style_profile.get('sentence_structure', 'varied')}")
        desc.append(f"Paragraphs: {style_profile.get('paragraph_length', 'medium')} length")
        desc.append(f"Voice: {style_profile.get('voice', 'active')}")

        if style_profile.get("common_phrases"):
            desc.append(f"Common phrases: {', '.join(style_profile['common_phrases'][:3])}")

        if style_profile.get("examples"):
            desc.append("Example sentences:")
            for ex in style_profile["examples"][:2]:
                desc.append(f"  - {ex}")

        return "\n".join(desc)

    def _format_feedback(self, feedback: dict[str, Any]) -> str:
        """Format feedback dictionary for prompt.

        Args:
            feedback: Feedback data

        Returns:
            Formatted feedback text
        """
        lines = []

        if feedback.get("source_issues"):
            lines.append("Source Accuracy Issues:")
            for issue in feedback["source_issues"]:
                lines.append(f"  • {issue}")

        if feedback.get("style_issues"):
            lines.append("\nStyle Consistency Issues:")
            for issue in feedback["style_issues"]:
                lines.append(f"  • {issue}")

        if feedback.get("user_requests"):
            lines.append("\nUser Requests:")
            for req in feedback["user_requests"]:
                lines.append(f"  • {req}")

        return "\n".join(lines) if lines else "General improvements needed"

    def _fallback_transform(self, brain_dump: str) -> str:
        """Basic transformation when AI fails.

        Args:
            brain_dump: Raw content

        Returns:
            Minimally formatted content
        """
        lines = brain_dump.strip().split("\n")
        title = lines[0] if lines else "Blog Post"
        if not title.startswith("#"):
            title = f"# {title}"

        return brain_dump  # Return as-is rather than nothing
