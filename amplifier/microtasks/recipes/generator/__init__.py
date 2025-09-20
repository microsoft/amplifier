"""Adaptive generator for philosophy-driven tool creation."""

from pathlib import Path
from typing import Any


def inject_philosophy_guidance(prompt: str, stage: str) -> str:
    """Inject philosophy guidance into generation prompts.

    Args:
        prompt: Base prompt for generation
        stage: Current generation stage (plan, code, evaluation)

    Returns:
        Enhanced prompt with philosophy guidance
    """
    philosophy_path = Path(__file__).parent.parent / "TOOL_GENERATION_PHILOSOPHY.md"

    # Load philosophy if available
    philosophy = ""
    if philosophy_path.exists():
        philosophy = philosophy_path.read_text()

    # Stage-specific guidance
    if stage == "plan":
        guidance = """
## Critical Requirements (from Tool Generation Philosophy):

Your plan MUST ensure the generated tool:
1. Uses 120-second timeout for ALL Claude SDK calls (NON-NEGOTIABLE)
2. Saves results incrementally after EVERY processed item
3. Checks for existing results before processing (resume capability)
4. Uses retry-enabled file I/O utilities from amplifier.utils.file_io
5. Shows clear progress indicators to users

Remember: Code provides structure, AI provides intelligence. Keep them separate.
"""
    elif stage == "code":
        guidance = """
## Implementation Requirements:

CRITICAL patterns to follow:
- ALWAYS wrap SDK calls: `async with asyncio.timeout(120):`
- Save immediately after processing each item
- Check existing before processing: `if item_id in existing: continue`
- Use `write_json()` and `read_json()` from amplifier.utils.file_io
- Print progress: `[current/total] Processing item_name...`

The tool should be simple, focused, and regeneratable.
"""
    elif stage == "evaluation":
        guidance = """
## Evaluation Criteria:

Check that the generated code:
- Has >= 120 second timeout on ALL SDK calls
- Saves incrementally (not batch)
- Can resume from interruption
- Uses retry utilities for file I/O
- Shows progress to users
"""
    else:
        guidance = ""

    # Combine prompt with guidance
    enhanced = f"{prompt}\n\n{guidance}"

    # Add full philosophy if loaded and it's plan/code stage
    if philosophy and stage in ["plan", "code"]:
        enhanced += f"\n\n## Full Philosophy Document:\n{philosophy[:5000]}..."  # Truncate for context

    return enhanced


def generate_tool_plan(ask: str, exemplars: list[dict[str, Any]], philosophy: str | None = None) -> str:
    """Generate a tool plan based on user ask and exemplars.

    Args:
        ask: User's tool requirements
        exemplars: Relevant exemplar patterns
        philosophy: Philosophy guidance text

    Returns:
        Generated tool plan as structured text
    """
    prompt = f"""Design a plan for an amplifier CLI tool based on this request:

{ask}

The plan should define:
1. Tool purpose and goals
2. Input/output specifications
3. Processing stages (if multi-stage)
4. Data persistence approach
5. Error handling strategy
6. Progress reporting model

"""

    # Add exemplar context
    if exemplars:
        prompt += "\n## Relevant Patterns:\n"
        for ex in exemplars:
            prompt += f"\n### {ex['name']}\n{ex['description']}\n"

    # Inject philosophy
    prompt = inject_philosophy_guidance(prompt, "plan")

    prompt += """
Return a structured plan that can guide code generation.
Focus on WHAT the tool does, not HOW (that's for implementation).
"""

    return prompt


def generate_tool_code(plan: str, exemplars: list[dict[str, Any]], philosophy: str | None = None) -> str:
    """Generate tool implementation based on plan and exemplars.

    Args:
        plan: Tool plan/specification
        exemplars: Relevant code patterns
        philosophy: Philosophy guidance

    Returns:
        Prompt for generating tool code
    """
    prompt = f"""Implement an amplifier CLI tool based on this plan:

{plan}

Generate complete, working Python code that:
1. Can be run immediately without modifications
2. Follows amplifier tool patterns
3. Handles errors gracefully
4. Provides clear user feedback
"""

    # Add exemplar code
    if exemplars:
        prompt += "\n## Example Patterns to Learn From:\n"
        for ex in exemplars[:3]:  # Limit to avoid context overflow
            prompt += f"\n### {ex['name']}\n"
            prompt += f"```python\n{ex['code'][:1000]}...\n```\n"

    # Inject philosophy
    prompt = inject_philosophy_guidance(prompt, "code")

    prompt += """
Generate ONLY the recipe module code (recipes.py content).
Ensure all critical requirements are met:
- 120-second SDK timeout
- Incremental saves
- Resume capability
- Retry utilities for I/O
- Progress indicators
"""

    return prompt


def adapt_from_feedback(code: str, feedback: str, ask: str) -> str:
    """Adapt generated code based on evaluation feedback.

    Args:
        code: Previously generated code
        feedback: Evaluation feedback with specific issues
        ask: Original user ask

    Returns:
        Prompt for regenerating with fixes
    """
    prompt = f"""Fix the following code based on evaluation feedback:

## Original Request:
{ask}

## Current Code:
```python
{code[:3000]}...
```

## Required Fixes:
{feedback}

Generate a corrected version that addresses ALL listed issues.
Pay special attention to CRITICAL issues - these MUST be fixed.

Key fixes needed:
- Any timeout < 120 must be changed to exactly 120
- Any batch saves must become incremental (save after each item)
- Missing resume checks must be added
- Direct file I/O should use retry utilities

Return the complete corrected code.
"""

    # Inject philosophy for code stage
    prompt = inject_philosophy_guidance(prompt, "code")

    return prompt


def format_for_llm(plan_json: dict[str, Any]) -> str:
    """Format a structured plan for LLM generation.

    Args:
        plan_json: Structured plan dictionary

    Returns:
        Formatted plan text for LLM consumption
    """
    import json

    # Create readable format
    formatted = "Tool Generation Plan:\n\n"

    if "purpose" in plan_json:
        formatted += f"Purpose: {plan_json['purpose']}\n\n"

    if "steps" in plan_json:
        formatted += "Processing Steps:\n"
        for i, step in enumerate(plan_json["steps"], 1):
            formatted += f"{i}. {step.get('name', 'Step ' + str(i))}\n"
            if "description" in step:
                formatted += f"   {step['description']}\n"

    if "inputs" in plan_json:
        formatted += f"\nInputs: {', '.join(plan_json['inputs'])}\n"

    if "outputs" in plan_json:
        formatted += f"Outputs: {', '.join(plan_json['outputs'])}\n"

    # Add raw JSON for completeness
    formatted += f"\n\nRaw Plan:\n{json.dumps(plan_json, indent=2)}"

    return formatted
