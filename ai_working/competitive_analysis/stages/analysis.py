"""Analysis stage: Apply analytical frameworks to research findings.

Stage 2 of the competitive analysis pipeline. Takes research findings and applies
analytical frameworks (Porter's Five Forces, SWOT) to generate structured insights.
"""

import json
from pathlib import Path
from typing import Any

from claude_code_sdk import query

from ..frameworks.porter import get_porter_prompt
from ..frameworks.swot import get_swot_prompt
from ..models import AnalysisResult
from ..models import ResearchResult

# Framework registry mapping names to prompt generators
FRAMEWORK_PROMPTS = {
    "porter": get_porter_prompt,
    "swot": get_swot_prompt,
}


async def run_analysis_async(
    research_result: ResearchResult,
    frameworks: list[str],
    output_dir: Path,
    entity1: str,
    entity2: str,
) -> AnalysisResult:
    """Apply analytical frameworks to research findings.

    Args:
        research_result: Research findings from Stage 1
        frameworks: List of framework names to apply (e.g., ["porter", "swot"])
        output_dir: Directory to save analysis.json
        entity1: First company/product name
        entity2: Second company/product name

    Returns:
        AnalysisResult with all framework analyses

    Side effects:
        Writes analysis.json to output_dir

    Raises:
        ValueError: If unknown framework requested
    """
    # Convert ResearchResult to dict for framework prompts
    research_data = json.loads(research_result.model_dump_json())

    # Store results for each framework
    framework_results: dict[str, dict[str, Any]] = {}

    # Process each framework
    for framework_name in frameworks:
        # Validate framework exists
        if framework_name not in FRAMEWORK_PROMPTS:
            available = ", ".join(FRAMEWORK_PROMPTS.keys())
            raise ValueError(f"Unknown framework '{framework_name}'. Available: {available}")

        # Get framework-specific prompt
        prompt_generator = FRAMEWORK_PROMPTS[framework_name]
        prompt = prompt_generator(entity1, entity2, research_data)

        # Query Claude SDK
        response_text = ""
        async for message in query(prompt=prompt):
            if hasattr(message, "content"):
                for block in message.content:
                    if hasattr(block, "text"):
                        response_text += block.text

        # Parse JSON response (handle markdown code blocks)
        response_text = response_text.strip()
        if response_text.startswith("```"):
            # Remove markdown code blocks
            lines = response_text.split("\n")
            # Find start and end of JSON
            start_idx = 0
            end_idx = len(lines)
            for i, line in enumerate(lines):
                if line.strip().startswith("{"):
                    start_idx = i
                    break
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip().endswith("}"):
                    end_idx = i + 1
                    break
            response_text = "\n".join(lines[start_idx:end_idx])

        # Parse and store framework result
        framework_data = json.loads(response_text)
        framework_results[framework_name] = framework_data

    # Create AnalysisResult with timestamp
    result = AnalysisResult.create(frameworks=framework_results)

    # Save to analysis.json
    output_path = output_dir / "analysis.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")

    return result
