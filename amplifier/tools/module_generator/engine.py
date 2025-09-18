from __future__ import annotations

import logging
from pathlib import Path

from .context import GenContext
from .enhanced_sdk_client import generate_from_specs_enhanced
from .parsers import derive_module_name_from_path
from .parsers import parse_contract
from .parsers import parse_impl_spec
from .pipeline_orchestrator import PipelineOrchestrator
from .sdk_client import generate_from_specs
from .sdk_client import generate_with_continuation
from .sdk_client import plan_from_specs

logger = logging.getLogger(__name__)


def find_repo_root(start: Path | None = None) -> Path:
    p = start or Path.cwd()
    for parent in [p, *p.parents]:
        if (parent / ".git").exists() or (parent / "Makefile").exists():
            return parent
    return p  # fallback


def derive_module_name(contract_path: Path) -> str:
    return derive_module_name_from_path(contract_path)


def build_context(contract_path: Path, spec_path: Path, module_name: str | None, force: bool) -> GenContext:
    repo_root = find_repo_root()
    tool_dir = Path(__file__).resolve().parent
    if not module_name:
        module_name = derive_module_name(contract_path)
    # Ensure snake_case name
    safe_name = module_name.lower().replace("-", "_")
    target_rel = f"amplifier/{safe_name}"
    return GenContext(
        repo_root=repo_root,
        tool_dir=tool_dir,
        contract_path=contract_path,
        spec_path=spec_path,
        module_name=safe_name,
        target_rel=target_rel,
        force=force,
    )


async def plan_phase(ctx: GenContext) -> tuple[str, str | None]:
    """Run planning phase using the pipeline orchestrator."""
    orchestrator = PipelineOrchestrator(ctx)
    state = await orchestrator.run_pipeline(resume_from_checkpoint=False)

    # Extract plan from state
    plan_result = state.stage_results.get("plan")
    if plan_result and plan_result.success:
        return plan_result.output, state.session_id
    return "", None


async def plan_phase_legacy(ctx: GenContext) -> tuple[str, str | None]:
    """Legacy planning without pipeline orchestrator."""
    contract = parse_contract(ctx.contract_path)
    impl = parse_impl_spec(ctx.spec_path, expected_name=contract.name)
    if impl.name != contract.name:
        print(f"[warn] Contract/spec name mismatch: {contract.name} vs {impl.name}. Proceeding.")
    # Run planning in read-only mode
    print(f"\n🧭 Planning implementation for module: {ctx.module_name}\n")
    plan_text, session_id, cost, ms = await plan_from_specs(
        contract_text=contract.raw,
        impl_text=impl.raw,
        cwd=str(ctx.repo_root),
        add_dirs=[str(ctx.repo_root / "ai_context"), str(ctx.repo_root / "amplifier")],
        settings=None,
    )
    print(f"\n—— Plan complete (session: {session_id or 'n/a'}, cost=${cost:.4f}, {ms}ms) ——\n")
    return plan_text, session_id


async def generate_phase_with_pipeline(ctx: GenContext) -> str:
    """Run full generation pipeline with checkpoints and evaluation."""
    orchestrator = PipelineOrchestrator(ctx)
    state = await orchestrator.run_pipeline(resume_from_checkpoint=True)

    # Check if generation succeeded
    gen_result = state.stage_results.get("generate")
    if gen_result and gen_result.success:
        return ctx.target_rel

    # Check if we at least got to generation stage
    if state.current_stage.value in ["generate", "verify_contract", "test", "complete"]:
        return ctx.target_rel

    raise RuntimeError(f"Pipeline failed at stage: {state.current_stage.value}")


async def generate_phase(ctx: GenContext, use_continuation: bool = True, use_enhanced: bool = False) -> str:
    contract = parse_contract(ctx.contract_path)
    impl = parse_impl_spec(ctx.spec_path, expected_name=contract.name)
    target_dir = ctx.repo_root / ctx.target_rel
    if target_dir.exists():
        if ctx.force:
            import shutil

            shutil.rmtree(target_dir)
            print(f"[info] Removed existing directory: {target_dir}")
        else:
            print(f"[error] Target exists: {target_dir}. Use --force to overwrite.")
            raise SystemExit(2)
    # Ensure parent exists
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    print(f"\n🛠️  Generating module into: {ctx.target_rel}\n")

    # Use enhanced generation if requested
    if use_enhanced:
        session_id, cost, ms = await generate_from_specs_enhanced(
            contract_text=contract.raw,
            impl_text=impl.raw,
            module_name=ctx.module_name,
            module_dir_rel=ctx.target_rel,
            cwd=str(ctx.repo_root),
            add_dirs=[str(ctx.repo_root / "ai_context"), str(ctx.repo_root / "amplifier")],
            settings=None,
            max_attempts=3,
        )
    # Use continuation function by default for more reliable generation
    elif use_continuation:
        session_id, cost, ms = await generate_with_continuation(
            contract_text=contract.raw,
            impl_text=impl.raw,
            module_name=ctx.module_name,
            module_dir_rel=ctx.target_rel,
            cwd=str(ctx.repo_root),
            add_dirs=[str(ctx.repo_root / "ai_context"), str(ctx.repo_root / "amplifier")],
            settings=None,
            max_attempts=3,
        )
    else:
        session_id, cost, ms = await generate_from_specs(
            contract_text=contract.raw,
            impl_text=impl.raw,
            module_name=ctx.module_name,
            module_dir_rel=ctx.target_rel,
            cwd=str(ctx.repo_root),
            add_dirs=[str(ctx.repo_root / "ai_context"), str(ctx.repo_root / "amplifier")],
            settings=None,
        )

    print(f"\n—— Generation complete (session: {session_id or 'n/a'}, cost=${cost:.4f}, {ms}ms) ——\n")
    return ctx.target_rel
