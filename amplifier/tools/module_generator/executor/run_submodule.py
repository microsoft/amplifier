"""Execute a single brick generation using the Claude SDK."""

from __future__ import annotations

import shutil

from ..parsers import parse_contract
from ..parsers import parse_impl_spec
from ..plan_models import GenContext
from ..plan_models import PlanBrick
from ..sdk_client import generate_from_specs


async def run_brick(ctx: GenContext, brick: PlanBrick, *, force: bool, extra_context: str | None = None) -> None:
    contract = parse_contract(brick.contract_path)
    impl = parse_impl_spec(brick.spec_path, expected_name=contract.name)

    target_dir = brick.target_dir
    if target_dir.exists():
        if force:
            shutil.rmtree(target_dir)
        else:
            raise FileExistsError(f"Target directory already exists for brick {brick.name}: {target_dir}")
    target_dir.parent.mkdir(parents=True, exist_ok=True)

    dependency_contracts: dict[str, str] = {}
    for dep in contract.depends_on:
        if not isinstance(dep, dict):
            continue
        dep_module = dep.get("module")
        dep_path = dep.get("contract")
        if not dep_module or not dep_path:
            continue
        dep_abs = (ctx.repo_root / dep_path).resolve()
        if not dep_abs.exists():
            continue
        try:
            dep_rel = dep_abs.relative_to(ctx.repo_root)
        except ValueError:
            dep_rel = dep_abs
        dependency_contracts[str(dep_module)] = dep_rel.as_posix()

    try:
        contract_ref = brick.contract_path.relative_to(ctx.repo_root)
    except ValueError:
        contract_ref = brick.contract_path
    try:
        spec_ref = brick.spec_path.relative_to(ctx.repo_root)
    except ValueError:
        spec_ref = brick.spec_path

    _, _, _ = await generate_from_specs(
        contract_text=contract.raw,
        impl_text=impl.raw,
        module_name=brick.name,
        module_dir_rel=target_dir.relative_to(ctx.repo_root).as_posix(),
        cwd=str(ctx.repo_root),
        add_dirs=[ctx.repo_root / "ai_context", ctx.repo_root / "amplifier"],
        settings=None,
        contract_path=contract_ref,
        spec_path=spec_ref,
        dependency_contracts=dependency_contracts or None,
        extra_context=extra_context,
    )
