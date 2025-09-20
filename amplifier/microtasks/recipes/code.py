"""
Minimal code recipe: plan → implement → test → refine.

Implements an end-to-end vertical slice that works offline
and upgrades transparently when Claude Code SDK is available.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

from ..llm import LLM


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def step_plan(llm: LLM, artifacts: Path) -> dict[str, Any]:
    prompt = (
        "You are a Planner. Produce a step-by-step plan for implementing the user's code goal. "
        "Use numbered short steps. Keep it concise."
    )
    plan = llm.complete(prompt)
    _write(artifacts / "plan.txt", plan)
    return {"plan": plan}


def step_implement(llm: LLM, artifacts: Path) -> dict[str, Any]:
    prompt = (
        "You are a Coder. Implement code as a single Python function that satisfies the plan. "
        "Respond with a Python fenced code block only."
    )
    code = llm.complete(prompt)
    # Extract code block
    m = re.search(r"```python\n([\s\S]*?)```", code)
    src = m.group(1) if m else code
    _write(artifacts / "impl.py", src)
    return {"file": str(artifacts / "impl.py")}


def step_test(llm: LLM, artifacts: Path) -> dict[str, Any]:
    # Create a tiny test if none exists
    tests_py = artifacts / "test_impl.py"
    if not tests_py.exists():
        test_snippet = (
            "import importlib.util, sys, pathlib\n"
            "p = pathlib.Path(__file__).parent / 'impl.py'\n"
            "spec = importlib.util.spec_from_file_location('impl', p)\n"
            "mod = importlib.util.module_from_spec(spec)\n"
            "sys.modules['impl'] = mod\n"
            "spec.loader.exec_module(mod)\n"
            "\n"
            "def test_exists():\n    assert hasattr(mod, 'generated_function') or hasattr(mod, 'add')\n"
        )
        _write(tests_py, test_snippet)

    # Run pytest for the artifact folder only
    cmd = ["python", "-m", "pytest", str(tests_py), "-q"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    _write(artifacts / "test_output.txt", proc.stdout + "\n" + proc.stderr)
    ok = proc.returncode == 0
    return {"passed": ok, "returncode": proc.returncode}


def step_refine(llm: LLM, artifacts: Path) -> dict[str, Any]:
    # Optional light refinement pass (documented behavior)
    prompt = "You are a Reviewer. Suggest a brief improvement note."
    note = llm.complete(prompt)
    _write(artifacts / "refine.txt", note)
    return {"note": note[:200]}


def run_code_recipe(goal: str, out_dir: str | None = None) -> dict[str, Any]:
    from ..orchestrator import MicrotaskOrchestrator

    orch = MicrotaskOrchestrator(base_dir=Path(out_dir) if out_dir else None)
    steps = [
        ("plan", step_plan),
        ("implement", step_implement),
        ("test", step_test),
        ("refine", step_refine),
    ]
    summary = orch.run("code", steps, meta={"goal": goal}, fail_fast=True)
    return summary.model_dump()
