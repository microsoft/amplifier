"""Lightweight wrapper around Claude Code SDK powered by CCSDK toolkit."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SDKNotAvailableError
from amplifier.ccsdk_toolkit import SessionOptions

from ..sdk_client import _prepare_claude_env

PermissionModeType = Literal["default", "acceptEdits", "plan", "bypassPermissions"]


@dataclass
class ClaudeRunResult:
    text: str
    session_id: str | None
    total_cost: float
    duration_ms: int


async def run_claude(
    prompt: str,
    *,
    cwd: Path,
    add_dirs: Sequence[str | Path] | None = None,
    allowed_tools: Sequence[str] = (),
    permission_mode: PermissionModeType = "default",
    max_turns: int = 3,
    system_prompt: str | None = None,
) -> ClaudeRunResult:
    """Execute a Claude Code SDK session and return aggregated output."""
    _prepare_claude_env(cwd)
    default_prompt = (
        "You are the Amplifier code-generation assistant.\n"
        "Consult @ai_context/MODULAR_DESIGN_PHILOSOPHY.md, @ai_context/module_generator/CONTRACT_SPEC_AUTHORING_GUIDE.md, "
        "and @ai_context/AMPLIFIER_CLAUDE_CODE_LEVERAGE.md before responding.\n"
        "Use @amplifier/ccsdk_toolkit/DEVELOPER_GUIDE.md for SDK-specific patterns."
    )

    options = SessionOptions(
        system_prompt=system_prompt or default_prompt,
        max_turns=max_turns,
        timeout_seconds=120,
        cwd=cwd,
        add_dirs=[str(path) for path in (add_dirs or [])],
        allowed_tools=list(allowed_tools),
        permission_mode=permission_mode,
    )

    async with ClaudeSession(options) as session:
        try:
            response = await session.query(prompt)
        except SDKNotAvailableError as exc:  # pragma: no cover - runtime environment guard
            raise RuntimeError(str(exc)) from exc

    if not response.success:
        raise RuntimeError(response.error or "Claude SDK returned no content")

    # Mirror previous behaviour by streaming the response to stdout
    if response.content:
        print(response.content, end="" if response.content.endswith("\n") else "\n", flush=True)

    metadata = response.metadata or {}
    return ClaudeRunResult(
        text=response.content,
        session_id=metadata.get("session_id"),
        total_cost=float(metadata.get("total_cost_usd", 0.0) or 0.0),
        duration_ms=int(metadata.get("duration_ms", 0) or 0),
    )
