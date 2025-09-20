"""
Microtask orchestrator.

Executes a recipe as a sequence of deterministic steps with
incremental persistence and graceful partial-failure handling.
"""

from __future__ import annotations

import traceback
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from typing import Any

from .llm import LLM
from .models import RunSummary
from .store import JobStore


class MicrotaskOrchestrator:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.store = JobStore(base_dir)
        self.llm = LLM()

    def run(
        self,
        recipe_name: str,
        steps: list[tuple[str, Callable[..., dict[str, Any]]]],
        meta: dict[str, Any] | None = None,
        fail_fast: bool = True,
        on_event: Callable[[str, str, dict[str, Any] | None], None] | None = None,
    ) -> RunSummary:
        state = self.store.create(recipe=recipe_name, meta=meta)
        job_id = state.job_id
        artifacts_dir = self.store.artifacts_dir(job_id)
        if on_event:
            with suppress(Exception):
                on_event("job", recipe_name, {"job_id": job_id, "artifacts_dir": str(artifacts_dir)})

        for step_name, fn in steps:
            if on_event:
                with suppress(Exception):
                    on_event("start", step_name, {"artifacts_dir": str(artifacts_dir)})
            state.mark_running(step_name, inp={"artifacts_dir": str(artifacts_dir)})
            self.store.save(state)

            try:
                out = fn(self.llm, artifacts_dir)
                state.mark_succeeded(out)
                if on_event:
                    with suppress(Exception):
                        on_event("success", step_name, out)
            except Exception as e:
                tb = traceback.format_exc(limit=8)
                state.mark_failed(error=f"{e}\n{tb}")
                if on_event:
                    with suppress(Exception):
                        on_event("fail", step_name, {"error": str(e)})
            finally:
                self.store.save(state)
            if state.steps[-1].status == "failed" and fail_fast:
                break

        success = all(s.status == "succeeded" for s in state.steps)
        return RunSummary(
            job_id=job_id,
            recipe=recipe_name,
            success=success,
            steps=[s.model_dump() for s in state.steps],
            artifacts_dir=str(artifacts_dir),
        )
