"""Planning utilities that prepare Claude for module generation."""

from __future__ import annotations

import json
import logging
import textwrap
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import GenerationOptions
from .models import ModuleSpecBundle
from .sdk import ClaudeSessionManager
from .sdk import SessionCallbacks


@dataclass
class PlanResult:
    """Structured output from the planning stage."""

    text: str
    todos: list[dict]
    usage: dict | None
    session_id: str | None


class ModulePlanner:
    """Run a planning pass through Claude using contract + spec artifacts."""

    def __init__(self, session_manager: ClaudeSessionManager):
        self.session_manager = session_manager

    async def create_plan(self, bundle: ModuleSpecBundle, options: GenerationOptions) -> PlanResult:
        prompt = build_plan_prompt(bundle)
        add_dirs: Iterable[str] = {
            str(bundle.contract_path.parent),
            str(bundle.spec_path.parent),
        }

        captured_messages: list[dict[str, Any]] = []
        message_path = bundle.artifact_dir / "plan.messages.jsonl"

        def on_message(message: dict[str, Any]) -> None:
            captured_messages.append(message)
            with message_path.open("a", encoding="utf-8") as handle:
                json.dump(message, handle, default=str)
                handle.write("\n")

        if message_path.exists():
            message_path.unlink()

        result = await self.session_manager.run(
            prompt=prompt,
            system_prompt=PLAN_SYSTEM_PROMPT,
            permission_mode=options.plan_permission_mode,
            allowed_tools=options.allowed_tools_plan,
            max_turns=options.plan_max_turns,
            add_dirs=add_dirs,
            callbacks=SessionCallbacks(on_message=on_message),
        )

        if not message_path.exists():
            _write_message_log(bundle.artifact_dir, "plan.messages.jsonl", captured_messages)

        _warn_if_max_turns_reached(captured_messages, options.plan_max_turns)

        return PlanResult(text=result.text, todos=result.todos, usage=result.usage, session_id=result.session_id)


PLAN_SYSTEM_PROMPT = textwrap.dedent(
    """
    You are the planning orchestrator for the Amplifier module generator.
    Operate within the project's philosophy (Bricks & Studs, Contract-First, Regenerate-Don't-Patch).
    Use information from the provided contract/spec plus repository context (CLAUDE.md, AGENTS.md, philosophy docs).
    Produce a concise, numbered plan with gated checkpoints, todo structure, and explicit references to subagents/hooks when useful.
    Do not write code or modify files in this phase; focus on analysis, dependencies, risks, and success criteria.
    """
)


def build_plan_prompt(bundle: ModuleSpecBundle) -> str:
    """Construct the planning prompt that feeds contract/spec content to Claude."""

    return textwrap.dedent(
        f"""
        ## Module Overview
        - Name: {bundle.module_name}
        - Slug: {bundle.module_slug}
        - Target output directory: {bundle.output_module_path}

        ## Contract
        ```markdown
        {bundle.contract_text}
        ```

        ## Implementation Spec
        ```markdown
        {bundle.spec_text}
        ```

        ### Expectations
        1. Validate assumptions, highlight dependencies, and outline subagent usage.
        2. Produce TODO entries grouped by phase (validation, scaffolding, code generation, verification).
        3. Identify files to read via Read/Grep tools and hooks to trigger.
        4. Finish with explicit exit criteria to approve code generation.
        """
    ).strip()


def _write_message_log(artifact_dir: Path, filename: str, messages: list[dict[str, Any]]) -> None:
    """Persist captured Claude messages for debugging."""

    if not messages:
        return

    path = artifact_dir / filename
    with path.open("w", encoding="utf-8") as handle:
        for message in messages:
            json.dump(message, handle, default=str)
            handle.write("\n")


def _warn_if_max_turns_reached(messages: list[dict[str, Any]], max_turns: int) -> None:
    """Emit a warning when Claude reports hitting the max turn limit."""

    if not messages:
        return

    last = messages[-1]
    if isinstance(last, dict) and last.get("subtype") == "error_max_turns":
        logging.getLogger(__name__).warning(
            "Claude planning session reached the max turn limit (%s). Consider increasing --plan-max-turns or refining the prompt.",
            max_turns,
        )
