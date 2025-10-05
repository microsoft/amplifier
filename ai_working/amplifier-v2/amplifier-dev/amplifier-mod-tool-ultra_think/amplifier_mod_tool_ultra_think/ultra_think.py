"""
UltraThink Tool Implementation

Multi-step reasoning workflow that performs deep analysis by:
1. Launching parallel LLM queries with different perspectives
2. Synthesizing results into cohesive insights
"""

import asyncio
from typing import Any, Dict, Optional, List
from amplifier_core.interfaces.tool import BaseTool
from amplifier_core.interfaces.model import BaseModelProvider


class UltraThinkTool(BaseTool):
    """
    UltraThink workflow tool for deep multi-perspective analysis.

    This tool implements a parallel reasoning process that:
    - Generates multiple perspectives on a topic concurrently
    - Synthesizes the results into actionable insights
    - Leverages async-first architecture for efficient LLM calls
    """

    name = "ultra_think"
    description = "Perform deep multi-perspective analysis on any topic"

    def __init__(self, kernel):
        """
        Initialize the UltraThink tool.

        Args:
            kernel: The AmplifierKernel instance for accessing models and services
        """
        self.kernel = kernel
        self._model: Optional[BaseModelProvider] = None

    def _get_model(self) -> BaseModelProvider:
        """Get the model provider, preferring OpenAI if available."""
        if self._model is None:
            # Try to get OpenAI provider first, fallback to any available
            self._model = (
                self.kernel.model_providers.get("openai")
                or next(iter(self.kernel.model_providers.values()))
            )
        return self._model

    async def run(self, input: Dict[str, Any]) -> str:
        """
        Perform ultra-think deep analysis on the given topic.

        This method spawns multiple parallel LLM queries from different perspectives
        and then synthesizes their outputs into a cohesive analysis.

        Args:
            input: Dictionary containing:
                - topic: The topic or question to analyze deeply
                - perspectives: Optional list of custom perspectives to use.
                              If not provided, uses default philosophical, practical, and critical views.

        Returns:
            A synthesized analysis combining multiple perspectives
        """
        # Extract parameters from input dict
        topic = input.get("topic", "")
        perspectives = input.get("perspectives")

        if not topic:
            return "Error: Topic is required for ultra-think analysis"

        model = self._get_model()

        # Use custom perspectives or defaults
        if perspectives is None:
            prompts = [
                f"Think deeply about '{topic}' from a philosophical perspective. "
                "Consider fundamental principles, ethics, and long-term implications.",

                f"Analyze '{topic}' from a practical perspective. "
                "Focus on implementation, feasibility, and real-world applications.",

                f"Critique the concept of '{topic}' and identify potential issues. "
                "Consider risks, unintended consequences, and alternative approaches.",

                f"Explore '{topic}' from a creative and innovative angle. "
                "What unconventional solutions or perspectives might apply?",

                f"Examine '{topic}' from a systems thinking perspective. "
                "How does this connect to larger patterns and interdependencies?"
            ]
        else:
            prompts = [
                f"Analyze '{topic}' from this perspective: {perspective}"
                for perspective in perspectives
            ]

        # Step 1: Launch parallel thoughtful prompts
        # Using asyncio.gather for concurrent execution
        try:
            results = await asyncio.gather(
                *(model.generate(prompt) for prompt in prompts),
                return_exceptions=True
            )
        except Exception as e:
            return f"Error during parallel analysis: {e}"

        # Filter out any errors and collect successful results
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Log the error but continue with other results
                print(f"Warning: Perspective {i+1} failed: {result}")
            else:
                successful_results.append(result)

        if not successful_results:
            return "Unable to generate any perspectives. Please try again."

        # Step 2: Synthesize the results
        perspectives_text = "\n\n=== PERSPECTIVE ===\n".join(successful_results)

        synthesis_prompt = f"""Given these multiple perspectives on '{topic}', provide a comprehensive synthesis that:

1. Identifies key insights and common themes
2. Highlights important tensions or contradictions
3. Proposes actionable recommendations
4. Concludes with the most important takeaway

Perspectives to synthesize:

{perspectives_text}

Please provide a structured, insightful synthesis that adds value beyond the individual perspectives."""

        try:
            summary = await model.generate(synthesis_prompt)
            return f"**Ultra-Think Analysis: {topic}**\n\n{summary}"
        except Exception as e:
            # Fallback to returning the raw perspectives if synthesis fails
            return f"**Ultra-Think Analysis: {topic}**\n\nSynthesis failed, raw perspectives:\n\n{perspectives_text}"

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the ultra-think tool with parameters.

        This method implements the BaseTool interface for tool execution.

        Args:
            **kwargs: Keyword arguments including:
                - topic: The topic to analyze (required)
                - perspectives: Optional list of custom perspectives

        Returns:
            Dictionary with the analysis result
        """
        topic = kwargs.get("topic")
        if not topic:
            return {
                "success": False,
                "error": "Topic is required for ultra-think analysis"
            }

        perspectives = kwargs.get("perspectives")

        try:
            result = await self.run({"topic": topic, "perspectives": perspectives})
            return {
                "success": True,
                "result": result,
                "topic": topic,
                "perspectives_used": len(perspectives) if perspectives else 5
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "topic": topic
            }