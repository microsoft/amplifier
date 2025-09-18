"""Enumerations for module generator pipeline."""

from __future__ import annotations

from enum import Enum


class PipelineStage(Enum):
    """Stages of the module generation pipeline."""

    PARSE = "parse"
    PLAN = "plan"
    EVALUATE_PLAN = "evaluate_plan"
    GENERATE = "generate"
    VERIFY_CONTRACT = "verify_contract"
    TEST = "test"
    COMPLETE = "complete"

    def next_stage(self) -> PipelineStage | None:
        """Get the next stage in the pipeline."""
        stages = list(PipelineStage)
        current_idx = stages.index(self)
        if current_idx < len(stages) - 1:
            return stages[current_idx + 1]
        return None
