from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SDKNotAvailableError
from amplifier.ccsdk_toolkit import SessionOptions


def _prepare_claude_env(cwd: str | Path) -> Path:
    base = Path(cwd) / ".claude_config"
    cache = base / "cache"
    logs = base / "logs"
    base.mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    os.environ["HOME"] = str(Path(cwd))
    os.environ.setdefault("CLAUDE_CODE_CONFIG_DIR", str(base))
    os.environ.setdefault("CLAUDE_CODE_CACHE_DIR", str(cache))
    os.environ.setdefault("CLAUDE_CODE_CACHE_PATH", str(cache))
    os.environ.setdefault("CLAUDE_CODE_LOG_DIR", str(logs))
    return base


def _default_system_prompt() -> str:
    return (
        "You are the Modular Builder for the Amplifier repo.\n"
        "Follow contract-first, 'bricks & studs', and regeneration over patching.\n"
        "Consult @ai_context/MODULAR_DESIGN_PHILOSOPHY.md and @ai_context/module_generator/CONTRACT_SPEC_AUTHORING_GUIDE.md.\n"
        "Leverage @ai_context/AMPLIFIER_CLAUDE_CODE_LEVERAGE.md and @amplifier/ccsdk_toolkit/DEVELOPER_GUIDE.md when using the Claude Code SDK.\n"
        "Use concise, explicit steps. Respect repo conventions and tests."
    )


async def plan_from_specs(
    contract_text: str,
    impl_text: str,
    cwd: str,
    add_dirs: Sequence[str | Path] | None = None,
    settings: str | None = None,
) -> tuple[str, str | None, float, int]:
    """Ask Claude to produce a concrete implementation plan (READ-ONLY)."""
    _prepare_claude_env(cwd)
    effective_add_dirs: list[str | Path] = list(add_dirs) if add_dirs is not None else []
    prompt = (
        "You are in PLANNING phase. Do NOT write or edit files.\n"
        "Given the following module contract and implementation spec, output a precise, actionable plan.\n"
        "Include: file tree to create, key functions/classes, test plan, and acceptance checks.\n"
        "Return clear, stepwise instructions.\n\n"
        "=== CONTRACT ===\n" + contract_text + "\n\n"
        "=== IMPLEMENTATION SPEC ===\n" + impl_text + "\n\n"
        "End of inputs."
    )

    options = SessionOptions(
        system_prompt=_default_system_prompt(),
        max_turns=3,
        timeout_seconds=int(os.environ.get("AMPLIFIER_CLAUDE_PLAN_TIMEOUT", "120")),
        cwd=Path(cwd),
        add_dirs=[str(path) for path in effective_add_dirs],
        allowed_tools=["Read", "Grep"],
        permission_mode="default",
        settings=settings,
    )

    async with ClaudeSession(options) as session:
        try:
            response = await session.query(prompt)
        except SDKNotAvailableError as exc:  # pragma: no cover - runtime guard
            raise RuntimeError(str(exc)) from exc

    if not response.success:
        raise RuntimeError(response.error or "Claude session returned no plan output")

    metadata = response.metadata or {}
    return (
        response.content,
        metadata.get("session_id"),
        float(metadata.get("total_cost_usd", 0.0) or 0.0),
        int(metadata.get("duration_ms", 0) or 0),
    )


async def generate_from_specs(
    contract_text: str,
    impl_text: str,
    module_name: str,
    module_dir_rel: str,
    cwd: str,
    add_dirs: Sequence[str | Path] | None = None,
    settings: str | None = None,
    contract_path: Path | None = None,
    spec_path: Path | None = None,
    dependency_contracts: dict[str, str] | None = None,
    extra_context: str | None = None,
) -> tuple[str | None, float, int]:
    """Ask Claude to IMPLEMENT the module by creating files in the repo (WRITE-ENABLED)."""
    _prepare_claude_env(cwd)
    effective_add_dirs: list[str | Path] = list(add_dirs) if add_dirs is not None else []
    dependency_text = ""
    if dependency_contracts:
        blocks: list[str] = []
        for dep_name, dep_ref in dependency_contracts.items():
            blocks.append(f"### DEPENDENCY CONTRACT: {dep_name}\n@{dep_ref}\n")
        dependency_text = "\n".join(blocks)

    guidance_lines = [
        "IMPLEMENT the module now. Create all necessary files and tests under the provided repository.",
        f"Module target directory (relative to repo root): {module_dir_rel}",
        "Strict rules:",
        " - Follow the contract exactly.",
        " - Generate runnable, import-clean Python 3.11 code.",
        " - Add a README.md documenting the public interface.",
        " - Emit a runnable sample script when the spec requests it (e.g. scripts/run_<module>_sample.py).",
        " - When the spec lists paths outside the module directory, create them exactly at the stated locations.",
        " - Add tests. Keep them fast.",
        " - Use dependency public APIs exactly as defined in their contracts; do not invent wrapper classes if the contract exposes functions.",
        " - Use idempotent writes (you may overwrite files in the target dir).",
        " - Respect project style (ruff/pyright) and Makefile conventions.",
        "Inputs follow.",
    ]
    if extra_context:
        guidance_lines.append("Failure context from the previous attempt: " + extra_context.strip())
    prompt = (
        "\n\n".join(guidance_lines)
        + "\n\n"
        + (f"=== CONTRACT (@{contract_path}) ===\n" if contract_path else "=== CONTRACT ===\n")
        + contract_text
        + "\n\n"
        + (f"=== IMPLEMENTATION SPEC (@{spec_path}) ===\n" if spec_path else "=== IMPLEMENTATION SPEC ===\n")
        + impl_text
        + "\n\n"
        + ("=== DEPENDENCY CONTRACTS ===\n" + dependency_text + "\n\n" if dependency_text else "")
        + "End of inputs."
    )
    options = SessionOptions(
        system_prompt=_default_system_prompt(),
        max_turns=40,
        timeout_seconds=int(os.environ.get("AMPLIFIER_CLAUDE_GENERATE_TIMEOUT", "240")),
        cwd=Path(cwd),
        add_dirs=[str(path) for path in effective_add_dirs],
        allowed_tools=["Read", "Write", "Edit", "MultiEdit", "Bash"],
        permission_mode="acceptEdits",
        settings=settings,
    )

    async with ClaudeSession(options) as session:
        try:
            response = await session.query(prompt)
        except SDKNotAvailableError as exc:  # pragma: no cover - runtime guard
            raise RuntimeError(str(exc)) from exc

    if not response.success:
        raise RuntimeError(response.error or "Claude session returned no implementation output")

    metadata = response.metadata or {}
    return (
        metadata.get("session_id"),
        float(metadata.get("total_cost_usd", 0.0) or 0.0),
        int(metadata.get("duration_ms", 0) or 0),
    )
