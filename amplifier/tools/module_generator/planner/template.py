"""Prompt template for the structured planner."""

from __future__ import annotations

from textwrap import dedent

from ..plan_models import GenContext


def build_plan_prompt(ctx: GenContext, contract_text: str, spec_text: str) -> str:
    """Return a deterministic prompt instructing Claude to emit JSON plan."""
    module = ctx.module_name
    target_dir = ctx.target_rel.as_posix()
    try:
        contract_ref = ctx.contract_path.relative_to(ctx.repo_root)
    except ValueError:
        contract_ref = ctx.contract_path
    try:
        spec_ref = ctx.spec_path.relative_to(ctx.repo_root)
    except ValueError:
        spec_ref = ctx.spec_path
    return dedent(
        f"""
        You are the Module Planner for the Amplifier repository. Review the guidance in
        ai_context/MODULAR_DESIGN_PHILOSOPHY.md and ai_context/module_generator/CONTRACT_SPEC_AUTHORING_GUIDE.md. Break the module into focused bricks that can be
        generated independently using recursive invocations of the module generator.

        Output **only** JSON with the schema:
        {{
          "module": "{module}",
          "bricks": [
            {{
              "name": "short_identifier",
              "description": "summary of responsibilities",
              "contract_path": "ai_working/{module}/<brick>.contract.md",
              "spec_path": "ai_working/{module}/<brick>.impl_spec.md",
              "target_dir": "{target_dir}/<brick>",
              "type": "python_module"
            }}
          ]
        }}

        Rules:
        - Use snake_case for brick names.
        - Only include responsibilities that align with the contract/spec below.
        - Honour dependency boundaries: bricks must communicate via contracts only.
        - Prefer 4-8 bricks: loader, partitioning, persistence, orchestrator, cli, documentation, tests, plus a sample_runner brick when the spec mentions a demo script.
        - Ensure each brick has a dedicated contract/spec path under ai_working/{module}/.
        - Do not include generated code, only the plan JSON.
        - RESPOND WITH RAW JSON ONLY. No commentary, explanations, or markdown fences.

        # Module Contract (@{contract_ref})
        @{contract_ref}
        {contract_text}

        # Implementation Spec (@{spec_ref})
        @{spec_ref}
        {spec_text}
        """
    ).strip()
