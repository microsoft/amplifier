"""Blog Generator Tool Module

A multi-step content creation workflow that generates polished blog posts
from topics or outlines. Demonstrates workflow orchestration capabilities.
"""

from typing import Any, Dict
from amplifier_core.interfaces.tool import BaseTool


class BlogGeneratorTool(BaseTool):
    """Blog Generator Tool

    Provides a two-step workflow to generate polished blog posts:
    1. Draft generation from topic/outline
    2. Refinement and improvement

    This demonstrates a metacognitive recipe that non-technical users
    can leverage for content creation.
    """

    name = "blog_generator"
    description = "Generate high-quality blog posts using AI based on topics and outlines"

    def __init__(self, kernel):
        """Initialize with kernel reference for accessing model providers."""
        self.kernel = kernel

    async def run(self, input: Dict[str, Any]) -> str:
        """Generate a blog post based on a given topic or outline.

        Args:
            input: Dictionary containing:
                - topic_or_outline: A topic string or outline for the blog post

        Returns:
            str: The refined, polished blog post

        Workflow:
            1. Generate initial draft from topic/outline
            2. Refine draft for clarity and engagement
        """
        # Extract topic_or_outline from input dict
        topic_or_outline = input.get("topic_or_outline", "")

        if not topic_or_outline:
            return "Error: topic_or_outline is required for blog generation"

        # Get model provider (prefer OpenAI if available)
        model = (
            self.kernel.model_providers.get("openai")
            or next(iter(self.kernel.model_providers.values()))
        )

        # Step 1: Draft the blog post
        draft_prompt = (
            f"Write a detailed, well-structured blog post about: "
            f"{topic_or_outline}"
        )
        draft = await model.generate(draft_prompt, max_tokens=1024)

        # Ensure draft is a string (handle dict response if needed)
        if isinstance(draft, dict):
            # If it's a dict, try to extract content
            draft = draft.get('content', str(draft))

        # Optional: Publish progress event
        if hasattr(self.kernel, 'message_bus'):
            from amplifier_core.message_bus import Event
            await self.kernel.message_bus.publish(Event(
                type="tool:blog_generator:draft_complete",
                data={"topic": topic_or_outline},
                source="blog_generator"
            ))

        # Step 2: Refine the draft (improve clarity and add conclusion)
        refine_prompt = (
            f"Improve the following draft to be more clear and engaging, "
            f"ensure it has a strong conclusion:\n\n{draft}"
        )
        refined = await model.generate(refine_prompt, max_tokens=512)

        # Ensure refined is a string (handle dict response if needed)
        if isinstance(refined, dict):
            # If it's a dict, try to extract content
            refined = refined.get('content', str(refined))

        # Optional: Publish completion event
        if hasattr(self.kernel, 'message_bus'):
            from amplifier_core.message_bus import Event
            await self.kernel.message_bus.publish(Event(
                type="tool:blog_generator:complete",
                data={"topic": topic_or_outline},
                source="blog_generator"
            ))

        return refined