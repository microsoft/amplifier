"""Philosophy-driven tool generation with evaluation loops."""

import json
from pathlib import Path
from typing import Any

from ..llm import LLM
from .evaluator import evaluate_alignment
from .exemplars import find_similar
from .exemplars import get_exemplar_context
from .generator import adapt_from_feedback
from .generator import generate_tool_code
from .generator import generate_tool_plan


def step_plan_tool_philosophy(llm: LLM, artifacts: Path, name: str, desc: str) -> dict[str, Any]:
    """Plan a tool using philosophy-driven approach with exemplars.

    Args:
        llm: LLM instance for generation
        artifacts: Path to store artifacts
        name: Tool name
        desc: User's tool description/requirements

    Returns:
        Dict with plan results
    """
    # Find relevant exemplars based on description
    exemplars = find_similar(desc)
    exemplar_context = get_exemplar_context(exemplars)

    # Generate plan prompt with philosophy
    plan_prompt = generate_tool_plan(desc, exemplars)
    # Consult the amplifier-cli-architect to bias toward Amplifier patterns and CCSDK Toolkit usage
    advisor_preamble = (
        "Role: amplifier-cli-architect in CONTEXTUALIZE+GUIDE mode.\n"
        "- Apply Amplifier philosophies (ruthless simplicity, resume-friendly incremental saves).\n"
        "- Leverage amplifier.ccsdk_toolkit for sessions, logging, defensive I/O, and JSON parsing.\n"
        "- No fallbacks: fail fast on missing SDK/CLI with clear messages.\n"
        "- Stream progress (job id, per-step ticks), write artifacts/status.json incrementally.\n"
    )

    # Add exemplar context
    full_prompt = f"{advisor_preamble}\n\n{plan_prompt}\n\n{exemplar_context}"

    # Generate plan with evaluation loop
    max_attempts = 3
    for attempt in range(max_attempts):
        # Generate plan
        plan_text = llm.complete(full_prompt, system="You are a tool architect. Create structured plans.")

        # Evaluate plan alignment
        evaluation = evaluate_alignment(plan_text, desc)

        if evaluation["passed"]:
            # Save successful plan
            (artifacts / "tool_plan.txt").write_text(plan_text)

            # Try to extract JSON if present; otherwise write a minimal structured plan
            try:
                # Look for any JSON object in the plan
                import re

                json_match = re.search(r"\{[\s\S]*\}", plan_text)
                if json_match:
                    plan_json = json.loads(json_match.group())
                    (artifacts / "plan.json").write_text(json.dumps(plan_json, indent=2))
                else:
                    # No JSON block found — write a minimal plan to enable composition
                    plan_json = {"purpose": desc, "steps": [], "cli": {"requires": ["--src", "--limit"]}}
                    (artifacts / "plan.json").write_text(json.dumps(plan_json, indent=2))
            except Exception:
                # On parsing errors, still provide a minimal plan
                plan_json = {"purpose": desc, "steps": [], "cli": {"requires": ["--src", "--limit"]}}
                (artifacts / "plan.json").write_text(json.dumps(plan_json, indent=2))

            return {"plan": plan_text, "exemplars_used": len(exemplars), "attempt": attempt + 1}

        # Add feedback for next attempt
        full_prompt = (
            f"{plan_prompt}\n\nPrevious attempt had issues:\n{evaluation['feedback']}\n\nPlease fix these issues."
        )

    # Return best effort after max attempts
    (artifacts / "tool_plan.txt").write_text(plan_text)
    return {
        "plan": plan_text,
        "exemplars_used": len(exemplars),
        "attempt": max_attempts,
        "issues": evaluation.get("issues", []),
    }


def step_generate_tool_philosophy(llm: LLM, artifacts: Path, name: str, desc: str) -> dict[str, Any]:
    """Generate tool code using philosophy-driven approach.

    Args:
        llm: LLM instance for generation
        artifacts: Path to store artifacts
        name: Tool name
        desc: User's tool description/requirements

    Returns:
        Dict with generation results
    """
    # Load the plan
    plan_path = artifacts / "tool_plan.txt"
    if plan_path.exists():
        plan = plan_path.read_text()
    else:
        # Generate plan first if missing
        plan_result = step_plan_tool_philosophy(llm, artifacts, name, desc)
        plan = plan_result["plan"]

    # Find relevant exemplars
    exemplars = find_similar(desc)

    # Generate code with evaluation loop
    max_attempts = 3
    generated_code = ""

    for attempt in range(max_attempts):
        if attempt == 0:
            # Initial generation
            code_prompt = generate_tool_code(plan, exemplars)
            generated_code = llm.complete(
                code_prompt, system="You are an expert Python developer. Generate clean, working code."
            )
        else:
            # Regenerate with feedback
            # Evaluate current code
            evaluation = evaluate_alignment(generated_code, desc)
            adapt_prompt = adapt_from_feedback(generated_code, evaluation["feedback"], desc)
            generated_code = llm.complete(
                adapt_prompt, system="You are an expert Python developer. Fix the code based on feedback."
            )

        # Evaluate generated code
        evaluation = evaluate_alignment(generated_code, desc)

        if evaluation["passed"]:
            # Save successful code
            (artifacts / "generated_recipe.py").write_text(generated_code)
            return {"code": generated_code, "passed": True, "attempt": attempt + 1}

    # Save best effort
    (artifacts / "generated_recipe.py").write_text(generated_code)

    return {"code": generated_code, "passed": False, "attempt": max_attempts, "issues": evaluation.get("issues", [])}
