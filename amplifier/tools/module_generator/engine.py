from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .parsers import derive_module_name_from_path
from .parsers import parse_contract
from .parsers import parse_impl_spec
from .sdk_client import generate_from_specs
from .sdk_client import generate_with_continuation
from .sdk_client import plan_from_specs


@dataclass
class GenContext:
    repo_root: Path
    tool_dir: Path
    contract_path: Path
    spec_path: Path
    module_name: str
    target_rel: str  # e.g., "amplifier/idea_synthesizer"
    force: bool = False


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


async def generate_phase(ctx: GenContext, use_continuation: bool = True) -> str:
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

    # Use continuation function by default for more reliable generation
    if use_continuation:
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
