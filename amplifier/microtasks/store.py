"""
File-based persistence for microtask runs (incremental writes).

Implements Incremental Processing Pattern:
- Writes results after each step to fixed filenames
- Allows interruption/resume without losing progress
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any

from .models import JobState
from .models import iso_now

DEFAULT_BASE = Path(".data/microtasks")


class JobStore:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base = Path(base_dir) if base_dir else DEFAULT_BASE
        self.base.mkdir(parents=True, exist_ok=True)

    def create(self, recipe: str, meta: dict[str, Any] | None = None) -> JobState:
        job_id = str(uuid.uuid4())
        run_dir = self.run_dir(job_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        state = JobState(job_id=job_id, recipe=recipe, created_at=iso_now(), updated_at=iso_now(), meta=meta or {})
        self._write_state(job_id, state)
        return state

    def run_dir(self, job_id: str) -> Path:
        return self.base / job_id

    def artifacts_dir(self, job_id: str) -> Path:
        d = self.run_dir(job_id) / "artifacts"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def state_path(self, job_id: str) -> Path:
        return self.run_dir(job_id) / "results.json"

    def load(self, job_id: str) -> JobState:
        data = json.loads(self.state_path(job_id).read_text())
        return JobState.model_validate(data)

    def save(self, state: JobState) -> None:
        self._write_state(state.job_id, state)

    def _write_state(self, job_id: str, state: JobState) -> None:
        path = self.state_path(job_id)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(state.model_dump_json(indent=2))
        os.replace(tmp, path)
