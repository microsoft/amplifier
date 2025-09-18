"""Post-generation verification helpers."""

from __future__ import annotations

from ..plan_models import PlanBrick


def verify_brick(brick: PlanBrick) -> None:
    target_dir = brick.target_dir
    if not target_dir.exists():
        raise FileNotFoundError(f"Expected brick directory missing: {target_dir}")
    if not any(target_dir.iterdir()):
        raise FileNotFoundError(f"Brick directory is empty: {target_dir}")


def verify_plan_outputs(bricks: list[PlanBrick]) -> None:
    for brick in bricks:
        verify_brick(brick)
