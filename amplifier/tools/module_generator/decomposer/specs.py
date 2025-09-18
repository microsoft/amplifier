"""Generate or reuse contract/spec documents for plan bricks."""

from __future__ import annotations

import json

from ..plan_models import GenContext
from ..plan_models import PlanBrick
from ..sdk.claude import run_claude

SPEC_PROMPT = """
You are documenting a brick inside an Amplifier module. Produce JSON with two fields:
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

    prompt = (
        SPEC_PROMPT
        + "\n# Module Overview\n"
        + module_contract
        + "\n\n# Module Implementation Spec\n"
        + module_spec
        + "\n\n# Brick Description\n"
        + f"Name: {brick.name}\nTarget dir: {brick.target_dir}\nRole: {brick.description}\n"
    )

    result = await run_claude(
        prompt,
        cwd=ctx.repo_root,
        add_dirs=[ctx.repo_root / "ai_context", ctx.repo_root / "amplifier"],
        allowed_tools=["Read"],
        permission_mode="default",
        max_turns=5,
        system_prompt="You write documentation artefacts for Amplifier bricks. Output strict JSON only.",
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
        raise ValueError(f"Failed to parse spec JSON for brick {brick.name}: {result.text!r}") from exc

    contract_md = data.get("contract_markdown")
    spec_md = data.get("spec_markdown")
    if not contract_md or not spec_md:
        raise ValueError(f"Spec JSON missing fields for brick {brick.name}: {data}")

    contract_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(contract_md.strip() + "\n", encoding="utf-8")
    spec_path.write_text(spec_md.strip() + "\n", encoding="utf-8")
