"""
Pydantic models for microtask orchestration.

This brick defines the data contracts (studs) for:
- Microtask definitions and results
- Job state persistence

Inputs/Outputs are JSON-serializable and stable for other bricks.
"""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel
from pydantic import Field


class StepStatus(str, Enum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class StepResult(BaseModel):
    name: str
    status: StepStatus
    started_at: str | None = None
    finished_at: str | None = None
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class JobState(BaseModel):
    job_id: str
    recipe: str
    created_at: str
    updated_at: str
    steps: list[StepResult] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)

    def mark_running(self, step_name: str, inp: dict[str, Any] | None = None) -> None:
        now = datetime.now(UTC).isoformat()
        result = StepResult(name=step_name, status=StepStatus.running, started_at=now, input=inp or {})
        self.steps.append(result)
        self.updated_at = now

    def mark_succeeded(self, output: dict[str, Any] | None = None) -> None:
        if not self.steps:
            raise RuntimeError("No step to mark succeeded")
        now = datetime.now(UTC).isoformat()
        self.steps[-1].status = StepStatus.succeeded
        self.steps[-1].finished_at = now
        if output is not None:
            self.steps[-1].output = output
        self.updated_at = now

    def mark_failed(self, error: str, partial_output: dict[str, Any] | None = None) -> None:
        if not self.steps:
            raise RuntimeError("No step to mark failed")
        now = datetime.now(UTC).isoformat()
        self.steps[-1].status = StepStatus.failed
        self.steps[-1].finished_at = now
        self.steps[-1].error = error
        if partial_output:
            self.steps[-1].output = partial_output
        self.updated_at = now


class RunSummary(BaseModel):
    job_id: str
    recipe: str
    success: bool
    steps: list[dict[str, Any]]
    artifacts_dir: str


class MicrotaskError(Exception):
    """Raised for unrecoverable microtask failures."""


def iso_now() -> str:
    return datetime.now(UTC).isoformat()
