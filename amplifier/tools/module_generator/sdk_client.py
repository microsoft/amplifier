from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

try:
    # Claude Code SDK (declared in project pyproject)
    from claude_code_sdk import AssistantMessage
    from claude_code_sdk import ClaudeCodeOptions
    from claude_code_sdk import ClaudeSDKClient
    from claude_code_sdk import ClaudeSDKError
    from claude_code_sdk import CLINotFoundError
    from claude_code_sdk import ProcessError
    from claude_code_sdk import ResultMessage
    from claude_code_sdk import TextBlock
except Exception:  # pragma: no cover - handled via _ensure_sdk_available
    AssistantMessage = None  # type: ignore[assignment]
    ClaudeCodeOptions = None  # type: ignore[assignment]
    ClaudeSDKClient = None  # type: ignore[assignment]
    ClaudeSDKError = Exception  # type: ignore[assignment]
    CLINotFoundError = Exception  # type: ignore[assignment]
    ProcessError = Exception  # type: ignore[assignment]
    ResultMessage = None  # type: ignore[assignment]
    TextBlock = None  # type: ignore[assignment]


def _ensure_sdk_available() -> None:
    if ClaudeSDKClient is None or ClaudeCodeOptions is None:
        raise RuntimeError(
            "claude_code_sdk is not available. Ensure it's installed and importable in this environment.\n"
            "Dependency is declared in the repo's pyproject; install via `make install`."
        )


async def _stream_all_messages(client: Any) -> tuple[str, str | None, float, int]:
    """Collect streamed assistant text and return (text, session_id, total_cost_usd, duration_ms)."""
    collected: list[str] = []
    session_id: str | None = None
    total_cost = 0.0
    duration_ms = 0
    async for msg in client.receive_response():
        # Print any textual content while collecting
        if AssistantMessage is not None and isinstance(msg, AssistantMessage):
            for block in getattr(msg, "content", []) or []:
                if TextBlock is not None and isinstance(block, TextBlock):
                    text = getattr(block, "text", "")
                    if text:
                        print(text, end="", flush=True)
                        collected.append(text)
        if ResultMessage is not None and isinstance(msg, ResultMessage):
            # Final stats
            total_cost = getattr(msg, "total_cost_usd", 0.0) or 0.0
            duration_ms = getattr(msg, "duration_ms", 0) or 0
            session_id = getattr(msg, "session_id", None)
    print("", flush=True)
    return ("".join(collected), session_id, total_cost, duration_ms)


def _default_system_prompt() -> str:
    return (
        "You are the Modular Builder for the Amplifier repo.\n"
        "Follow contract-first, 'bricks & studs', and regeneration over patching.\n"
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
    _ensure_sdk_available()
    assert ClaudeSDKClient is not None  # pyright: ignore[reportUnnecessaryComparison]
    assert ClaudeCodeOptions is not None  # pyright: ignore[reportUnnecessaryComparison]
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
    async with ClaudeSDKClient(
        options=ClaudeCodeOptions(
            system_prompt=_default_system_prompt(),
            cwd=cwd,
            add_dirs=effective_add_dirs,
            settings=settings,
            # Plan mode not supported; emulate read-only by restricting tools.
            allowed_tools=["Read", "Grep"],
            permission_mode="default",
            max_turns=3,
        )
    ) as client:
        await client.query(prompt)
        plan_output = await _stream_all_messages(client)
    return plan_output


async def generate_from_specs(
    contract_text: str,
    impl_text: str,
    module_name: str,
    module_dir_rel: str,
    cwd: str,
    add_dirs: Sequence[str | Path] | None = None,
    settings: str | None = None,
) -> tuple[str | None, float, int]:
    """Ask Claude to IMPLEMENT the module by creating files in the repo (WRITE-ENABLED)."""
    _ensure_sdk_available()
    assert ClaudeSDKClient is not None  # pyright: ignore[reportUnnecessaryComparison]
    assert ClaudeCodeOptions is not None  # pyright: ignore[reportUnnecessaryComparison]
    effective_add_dirs: list[str | Path] = list(add_dirs) if add_dirs is not None else []
    prompt = (
        "IMPLEMENT the module now. Create all necessary files and tests under the provided repository.\n"
        f"Module target directory (relative to repo root): {module_dir_rel}\n"
        "Strict rules:\n"
        " - Follow the contract exactly.\n"
        " - Generate runnable, import-clean Python 3.11 code.\n"
        " - Add a README.md documenting the public interface.\n"
        " - Add tests. Keep them fast.\n"
        " - Use idempotent writes (you may overwrite files in the target dir).\n"
        " - Respect project style (ruff/pyright) and Makefile conventions.\n\n"
        "Inputs follow.\n\n"
        "=== CONTRACT ===\n" + contract_text + "\n\n"
        "=== IMPLEMENTATION SPEC ===\n" + impl_text + "\n\n"
        "End of inputs."
    )
    async with ClaudeSDKClient(
        options=ClaudeCodeOptions(
            system_prompt=_default_system_prompt(),
            cwd=cwd,
            add_dirs=effective_add_dirs,
            settings=settings,
            allowed_tools=["Read", "Write", "Edit", "MultiEdit", "Bash"],
            permission_mode="acceptEdits",  # auto-approve file edits
            max_turns=40,
        )
    ) as client:
        await client.query(prompt)
        _, session_id, total_cost, duration_ms = await _stream_all_messages(client)
    return (session_id, total_cost, duration_ms)
