from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

from amplifier.module_generator.generator import ModuleGenerator
from amplifier.module_generator.models import ClaudeSessionResult
from amplifier.module_generator.models import GenerationOptions
from amplifier.module_generator.spec_loader import load_spec_bundle


class FakeSessionManager:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def run(self, **kwargs: Any) -> ClaudeSessionResult:
        self.calls.append(kwargs)
        return ClaudeSessionResult(
            text="1. Draft plan\n2. Do work",
            todos=[{"status": "completed", "content": "draft"}],
            usage={"total_cost_usd": 0.01},
            session_id="session-test",
        )


def _workspace_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _make_bundle() -> tuple[Path, Path]:
    workspace = _workspace_root() / "tmp" / "module_generator_tests" / str(uuid4())
    workspace.mkdir(parents=True, exist_ok=True)
    contract = workspace / "contract.md"
    spec = workspace / "spec.md"
    contract.write_text("# Module Contract: Test Module\n\nBody", encoding="utf-8")
    spec.write_text("# Implementation Spec\n\nMore", encoding="utf-8")
    return contract, spec


@pytest.mark.asyncio
async def test_module_generator_plan_only(tmp_path: Path) -> None:
    contract, spec = _make_bundle()
    bundle = load_spec_bundle(contract, spec)
    manager = FakeSessionManager()
    generator = ModuleGenerator(manager)  # type: ignore[arg-type]

    options = GenerationOptions(
        plan_only=True,
        plan_permission_mode="acceptEdits",
        generate_permission_mode="acceptEdits",
        plan_max_turns=40,
        generate_max_turns=60,
    )
    result = await generator.run(bundle, options)

    assert result.generation is None
    assert (bundle.artifact_dir / "plan.md").exists()
    assert manager.calls  # ensure planner invoked
    assert manager.calls[0]["max_turns"] == options.plan_max_turns
