from __future__ import annotations

from pathlib import Path

import pytest

from amplifier.microtasks.llm import is_sdk_available
from amplifier.microtasks.recipes.code import run_code_recipe


def test_run_code_recipe_tmp(tmp_path: Path) -> None:
    if not is_sdk_available():
        pytest.skip("Claude Code SDK/CLI not available; skipping full-path test")
    # Use temp .data to avoid polluting repo
    result = run_code_recipe("add two numbers", out_dir=str(tmp_path / ".data"))
    assert result["recipe"] == "code"
    assert "job_id" in result
    assert Path(result["artifacts_dir"]).exists()

    # Check artifacts
    artifacts = Path(result["artifacts_dir"])  # type: ignore[index]
    assert (artifacts / "impl.py").exists()
    assert (artifacts / "test_output.txt").exists()

    # Validate test pass or fail recorded (allow failure, but file present)
    # The pipeline should not crash; partial failures are allowed
    assert any(s["status"] in ("succeeded", "failed") for s in result["steps"])  # type: ignore[index]
