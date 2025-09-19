from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from click.testing import CliRunner

from amplifier.module_generator.cli import cli
from amplifier.module_generator.generator import ModuleGenerationOutput
from amplifier.module_generator.planner import PlanResult


def _workspace_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _make_inputs() -> tuple[Path, Path]:
    workspace = _workspace_root() / "tmp" / "module_generator_cli" / str(uuid4())
    workspace.mkdir(parents=True, exist_ok=True)
    contract = workspace / "contract.md"
    spec = workspace / "spec.md"
    contract.write_text("# Module Contract: CLI Module\n\nBody", encoding="utf-8")
    spec.write_text("# Implementation Spec\n\nMore", encoding="utf-8")
    return contract, spec


def test_cli_plan_only(monkeypatch) -> None:
    contract, spec = _make_inputs()

    plan = PlanResult(text="Plan step", todos=[], usage=None, session_id="plan-session")

    async def fake_run(self, bundle, options):  # type: ignore[unused-ignore]
        return ModuleGenerationOutput(plan=plan, generation=None)

    monkeypatch.setattr("amplifier.module_generator.generator.ModuleGenerator.run", fake_run)

    runner = CliRunner()
    result = runner.invoke(cli, [str(contract), str(spec), "--plan-only", "--yes"])

    assert result.exit_code == 0
    assert "Plan-only run complete" in result.output
