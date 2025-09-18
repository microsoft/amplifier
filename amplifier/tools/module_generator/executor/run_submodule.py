"""Execute a single brick generation using the Claude SDK."""

from __future__ import annotations

import shutil

from ..parsers import parse_contract
from ..parsers import parse_impl_spec
from ..plan_models import GenContext
from ..plan_models import PlanBrick
from ..sdk_client import generate_from_specs


async def run_brick(ctx: GenContext, brick: PlanBrick, *, force: bool) -> None:
    contract = parse_contract(brick.contract_path)
    impl = parse_impl_spec(brick.spec_path, expected_name=contract.name)

    target_dir = brick.target_dir
    if target_dir.exists():
        if force:
            shutil.rmtree(target_dir)
        else:
            raise FileExistsError(f"Target directory already exists for brick {brick.name}: {target_dir}")
    target_dir.parent.mkdir(parents=True, exist_ok=True)

    _, _, _ = await generate_from_specs(
        contract_text=contract.raw,
        impl_text=impl.raw,
        module_name=brick.name,
        module_dir_rel=target_dir.relative_to(ctx.repo_root).as_posix(),
        cwd=str(ctx.repo_root),
        add_dirs=[ctx.repo_root / "ai_context", ctx.repo_root / "amplifier"],
        settings=None,
    )
