"""Format stage: Convert analysis into audience-specific reports.

Stage 3 of the competitive analysis pipeline. Takes structured analysis results
and formats them into readable reports tailored for specific audiences.
"""

import json
from pathlib import Path

from claude_code_sdk import query

from ..models import AnalysisResult

# Audience-specific formatting instructions
AUDIENCE_INSTRUCTIONS = {
    "executive": """Format this competitive analysis for C-level executives:
- Lead with 3-5 strategic insights and key takeaways
- Focus on business implications and strategic positioning
- Keep it concise (2-3 pages max)
- Use clear headers and bullet points
- Highlight competitive advantages and threats
- Include actionable recommendations""",
    "pm": """Format this competitive analysis for product managers:
- Lead with product and feature comparisons
- Include detailed competitive positioning
- Focus on capabilities, gaps, and opportunities
- Provide specific product recommendations
- Use clear sections for different frameworks
- Include tactical next steps and priorities""",
}


async def run_format_async(
    analysis_result: AnalysisResult,
    audience: str,
    output_dir: Path,
    entity1: str,
    entity2: str,
) -> str:
    """Format analysis results for specific audience.

    Args:
        analysis_result: Analysis results from Stage 2
        audience: Target audience ("executive" or "pm")
        output_dir: Directory to save formatted report
        entity1: First company/product name
        entity2: Second company/product name

    Returns:
        Formatted markdown report as string

    Side effects:
        Writes {audience}_report.md to output_dir

    Raises:
        ValueError: If unknown audience requested
    """
    # Validate audience
    if audience not in AUDIENCE_INSTRUCTIONS:
        available = ", ".join(AUDIENCE_INSTRUCTIONS.keys())
        raise ValueError(f"Unknown audience '{audience}'. Available: {available}")

    # Get audience-specific instructions
    format_instructions = AUDIENCE_INSTRUCTIONS[audience]

    # Convert analysis result to JSON for context
    analysis_json = json.loads(analysis_result.model_dump_json())

    # Build prompt for formatting
    prompt = f"""You are formatting a competitive analysis of {entity1} vs {entity2}.

{format_instructions}

## Analysis Data

{json.dumps(analysis_json, indent=2)}

## Task

Create a well-structured markdown report following the audience guidelines above.
Use proper markdown formatting (headers, lists, bold, etc.).
Focus on insights and actionable information, not just data presentation.

Return ONLY the markdown report, no preamble or explanation."""

    # Query Claude SDK
    response_text = ""
    async for message in query(prompt=prompt):
        if hasattr(message, "content"):
            for block in message.content:
                if hasattr(block, "text"):
                    response_text += block.text

    # Clean up response (remove any wrapper text)
    report = response_text.strip()

    # Remove markdown code blocks if present
    if report.startswith("```markdown"):
        lines = report.split("\n")
        # Remove first line (```markdown) and last line (```)
        if len(lines) > 2 and lines[-1].strip() == "```":
            report = "\n".join(lines[1:-1])
    elif report.startswith("```"):
        lines = report.split("\n")
        if len(lines) > 2 and lines[-1].strip() == "```":
            report = "\n".join(lines[1:-1])

    # Save formatted report
    output_path = output_dir / f"{audience}_report.md"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    return report
