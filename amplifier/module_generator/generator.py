"""High-level orchestration for planning and generating modules via Claude."""

from __future__ import annotations

import json
import logging
import shutil
import textwrap
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import GenerationOptions
from .models import ModuleSpecBundle
from .planner import ModulePlanner
from .planner import PlanResult
from .planner import _warn_if_max_turns_reached
from .planner import _write_message_log
from .sdk import ClaudeSessionManager
from .sdk import SessionCallbacks

logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    """Structured output from the generation phase."""

    text: str
    todos: list[dict]
    usage: dict | None
    session_id: str | None
    target_dir: Path


@dataclass
class ModuleGenerationOutput:
    """Aggregate of planning and generation results."""

    plan: PlanResult
    generation: GenerationResult | None


class ModuleGenerator:
    """Public orchestrator combining planning + generation workflow."""

    def __init__(self, session_manager: ClaudeSessionManager):
        self.session_manager = session_manager
        self.planner = ModulePlanner(session_manager)

    async def run(self, bundle: ModuleSpecBundle, options: GenerationOptions) -> ModuleGenerationOutput:
        artifact_dir = bundle.artifact_dir
        artifact_dir.mkdir(parents=True, exist_ok=True)

        plan_result = await self.planner.create_plan(bundle, options)
        _persist_plan(artifact_dir, plan_result)

        if options.plan_only:
            logger.info("Plan-only mode enabled; skipping generation")
            return ModuleGenerationOutput(plan=plan_result, generation=None)

        target_dir = bundle.output_module_path
        _prepare_target_dir(target_dir, force=options.force)

        generation_prompt = build_generation_prompt(bundle, plan_result.text)
        add_dirs: Iterable[str] = {
            str(bundle.contract_path.parent),
            str(bundle.spec_path.parent),
            str(target_dir.parent),
        }

        generation_messages: list[dict] = []
        generation_log_path = artifact_dir / "generation.messages.jsonl"

        def on_generation_message(message: dict[str, Any]) -> None:
            generation_messages.append(message)
            with generation_log_path.open("a", encoding="utf-8") as handle:
                json.dump(message, handle, default=str)
                handle.write("\n")

        if generation_log_path.exists():
            generation_log_path.unlink()

        result = await self.session_manager.run(
            prompt=generation_prompt,
            system_prompt=GENERATION_SYSTEM_PROMPT,
            permission_mode=options.generate_permission_mode,
            allowed_tools=options.allowed_tools_generate,
            max_turns=options.generate_max_turns,
            add_dirs=add_dirs,
            callbacks=SessionCallbacks(on_message=on_generation_message),
        )

        if not generation_log_path.exists():
            _write_message_log(artifact_dir, "generation.messages.jsonl", generation_messages)

        _warn_if_max_turns_reached(generation_messages, options.generate_max_turns)
        _persist_generation_summary(artifact_dir, result, target_dir)

        generation = GenerationResult(
            text=result.text,
            todos=result.todos,
            usage=result.usage,
            session_id=result.session_id,
            target_dir=target_dir,
        )
        return ModuleGenerationOutput(plan=plan_result, generation=generation)


def _prepare_target_dir(target_dir: Path, *, force: bool) -> None:
    """Ensure the module output directory is ready for Claude to populate."""

    if target_dir.exists():
        if not force:
            raise FileExistsError(
                f"Output directory {target_dir} already exists. Re-run with --force to overwrite (directory will be removed)."
            )
        logger.info("--force supplied; removing existing %s", target_dir)
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)


def _persist_plan(artifact_dir: Path, plan: PlanResult) -> None:
    """Write plan outputs to disk for auditing and reuse."""

    plan_path = artifact_dir / "plan.md"
    with plan_path.open("w", encoding="utf-8") as handle:
        handle.write("# Generation Plan\n\n")
        handle.write(plan.text)
        handle.write("\n")

    if plan.todos:
        todo_path = artifact_dir / "plan.todos.json"
        import json

        with todo_path.open("w", encoding="utf-8") as handle:
            json.dump(plan.todos, handle, indent=2)

    if plan.usage:
        import json

        usage_path = artifact_dir / "plan.usage.json"
        with usage_path.open("w", encoding="utf-8") as handle:
            json.dump(plan.usage, handle, indent=2)


def _persist_generation_summary(artifact_dir: Path, result, target_dir: Path) -> None:
    """Write summary metadata from the generation session."""

    summary_path = artifact_dir / "generation_summary.md"
    with summary_path.open("w", encoding="utf-8") as handle:
        handle.write("# Generation Summary\n\n")
        handle.write(f"Target directory: {target_dir}\n\n")
        handle.write(result.text)
        handle.write("\n")

    if result.todos:
        import json

        todo_path = artifact_dir / "generation.todos.json"
        with todo_path.open("w", encoding="utf-8") as handle:
            json.dump(result.todos, handle, indent=2)

    if result.usage:
        import json

        usage_path = artifact_dir / "generation.usage.json"
        with usage_path.open("w", encoding="utf-8") as handle:
            json.dump(result.usage, handle, indent=2)


GENERATION_SYSTEM_PROMPT = textwrap.dedent(
    """
    You are the module builder for Amplifier. Use the approved plan to implement the module end-to-end.
    Honour the project's development philosophy: keep solutions simple, respect bricks & studs boundaries,
    regenerate instead of patching, and use subagents/hooks defined in .claude/ when helpful.
    Prefer using Write/Edit tools to create files; run slash commands and hooks as needed; track progress via TodoWrite.
    Ensure generated code passes linting (ruff), formatting, and includes tests per the spec.
    """
)


def build_generation_prompt(bundle: ModuleSpecBundle, plan_text: str) -> str:
    """Construct the generation prompt referencing the approved plan."""

    return textwrap.dedent(
        f"""
        ## Module Overview
        - Name: {bundle.module_name}
        - Slug: {bundle.module_slug}
        - Target output directory: {bundle.output_module_path}
        - Artifact run directory: {bundle.artifact_dir}

        ## Approved Plan
        {plan_text}

        ## Contract
        ```markdown
        {bundle.contract_text}
        ```

        ## Implementation Spec
        ```markdown
        {bundle.spec_text}
        ```

        ### Requirements for this session
        - Use Claude Code Write/Edit tools to scaffold the module inside `{bundle.output_module_path}`.
        - Generate code, tests, documentation, and prompts described in the spec.
        - Update todos as work progresses and complete them before finishing.
        - Trigger project hooks (lint/test) when appropriate and record any failures.
        - Summarize deliverables at the end with a checklist of generated files.
        """
    ).strip()
