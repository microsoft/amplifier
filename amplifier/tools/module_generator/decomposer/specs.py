"""Generate or reuse contract/spec documents for plan bricks."""

from __future__ import annotations

import json

from amplifier.ccsdk_toolkit.defensive import parse_llm_json

from ..plan_models import GenContext
from ..plan_models import PlanBrick
from ..sdk.claude import run_claude

SPEC_PROMPT = """
You are documenting a brick inside an Amplifier module. Before responding, review
@ai_context/MODULAR_DESIGN_PHILOSOPHY.md and @ai_context/module_generator/CONTRACT_SPEC_AUTHORING_GUIDE.md.
Produce JSON with two fields:
{
  "contract_markdown": "# ...",
  "spec_markdown": "# ..."
}

Guidelines:
- Contracts describe purpose, inputs, outputs, invariants (Markdown).
- Implementation specs give detailed design, architecture, tests.
- Tailor the content to the named brick and its description.
- Be concise but explicit so future generators can produce code directly from these docs.
- Do not include backticks or commentary outside the JSON.
"""


async def ensure_brick_specs(
    ctx: GenContext,
    brick: PlanBrick,
    *,
    module_contract: str,
    module_spec: str,
) -> None:
    contract_path = brick.contract_path
    spec_path = brick.spec_path
    if contract_path.exists() and spec_path.exists():
        return

    try:
        contract_ref = ctx.contract_path.relative_to(ctx.repo_root)
    except ValueError:
        contract_ref = ctx.contract_path
    try:
        spec_ref = ctx.spec_path.relative_to(ctx.repo_root)
    except ValueError:
        spec_ref = ctx.spec_path

    prompt = (
        SPEC_PROMPT
        + "\n# Module Overview\n"
        + f"@{contract_ref}\n"
        + module_contract
        + "\n\n# Module Implementation Spec\n"
        + f"@{spec_ref}\n"
        + module_spec
        + "\n\n# Brick Description\n"
        + f"Name: {brick.name}\nTarget dir: {brick.target_dir}\nRole: {brick.description}\n"
    )

    extra_guidance = None
    last_error = None
    data = None

    for attempt in range(3):
        augmented_prompt = prompt
        if extra_guidance:
            augmented_prompt += (
                "\n\n# Additional Guidance\n"
                "Your previous response was not valid JSON. Respond with JSON only, "
                "matching the required schema and no commentary."
                f"\n{extra_guidance}\n"
            )

        result = await run_claude(
            augmented_prompt,
            cwd=ctx.repo_root,
            add_dirs=[ctx.repo_root / "ai_context", ctx.repo_root / "amplifier"],
            allowed_tools=["Read"],
            permission_mode="default",
            max_turns=5,
            system_prompt="You write documentation artifacts for Amplifier bricks. Output strict JSON only.",
        )

        text = result.text.strip()
        data = parse_llm_json(text, verbose=True)

        if data is None:
            payload = text
            if payload.startswith("```json"):
                payload = payload[7:]
            if payload.startswith("```"):
                payload = payload[3:]
            if payload.endswith("```"):
                payload = payload[:-3]

            try:
                data = json.loads(payload.strip())
            except json.JSONDecodeError as exc:
                last_error = exc
                extra_guidance = "Respond with valid JSON object containing contract_markdown and spec_markdown only."
                continue

        if not isinstance(data, dict):
            last_error = ValueError("Claude response was not a JSON object")
            extra_guidance = "The response must be a JSON object with contract_markdown and spec_markdown keys."
            data = None
            continue

        if not data.get("contract_markdown") or not data.get("spec_markdown"):
            last_error = ValueError("JSON missing contract_markdown/spec_markdown")
            extra_guidance = "Ensure both contract_markdown and spec_markdown fields are present and non-empty."
            data = None
            continue

        # Successful parse
        break

    if data is None:
        raise ValueError(
            f"Failed to parse spec JSON for brick {brick.name}: {result.text!r}"
        ) from last_error

    contract_md = data.get("contract_markdown")
    spec_md = data.get("spec_markdown")
    if not contract_md or not spec_md:
        raise ValueError(f"Spec JSON missing fields for brick {brick.name}: {data}")

    contract_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(contract_md.strip() + "\n", encoding="utf-8")
    spec_path.write_text(spec_md.strip() + "\n", encoding="utf-8")
