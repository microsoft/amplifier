"""Planner service that talks to Claude and returns structured plans."""

from __future__ import annotations

import json

from ..plan_models import GenContext
from ..plan_models import PlanBrick
from ..plan_models import PlanDocument
from ..sdk.claude import run_claude
from .template import build_plan_prompt


async def generate_plan(ctx: GenContext, contract_text: str, spec_text: str) -> PlanDocument:
    prompt = build_plan_prompt(ctx, contract_text, spec_text)
    result = await run_claude(
        prompt,
        cwd=ctx.repo_root,
        add_dirs=[ctx.repo_root / "ai_context", ctx.repo_root / "amplifier"],
        allowed_tools=["Read", "Grep"],
        permission_mode="default",
        max_turns=4,
        system_prompt=(
            "You design modular plans for the Amplifier project. Respond with strict JSON; no prose outside the JSON."
        ),
    )
    payload = result.text.strip()
    if payload.startswith("```json"):
        payload = payload[7:]
    if payload.startswith("```"):
        payload = payload[3:]
    if payload.endswith("```"):
        payload = payload[:-3]

    try:
        data = json.loads(payload.strip())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Planner returned non-JSON response: {result.text!r}") from exc

    plan = PlanDocument.from_dict(data)
    plan.claude_session = result.session_id
    plan.ensure_minimum()

    # Normalise paths relative to repo root
    bricks: list[PlanBrick] = []
    for brick in plan.bricks:
        bricks.append(
            PlanBrick(
                name=brick.name,
                description=brick.description,
                contract_path=(ctx.repo_root / brick.contract_path).resolve(),
                spec_path=(ctx.repo_root / brick.spec_path).resolve(),
                target_dir=(ctx.repo_root / brick.target_dir).resolve(),
                type=brick.type,
            )
        )
    plan.bricks = bricks
    return plan
