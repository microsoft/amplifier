"""Lightweight wrapper around Claude Code SDK."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from claude_code_sdk import AssistantMessage
    from claude_code_sdk import ClaudeCodeOptions
    from claude_code_sdk import ClaudeSDKClient
    from claude_code_sdk import PermissionMode as _PermissionMode
    from claude_code_sdk import ResultMessage
    from claude_code_sdk import TextBlock
except Exception:  # pragma: no cover - import error handled at runtime
    AssistantMessage = None  # type: ignore[assignment]
    ClaudeCodeOptions = None  # type: ignore[assignment]
    ClaudeSDKClient = None  # type: ignore[assignment]
    _PermissionMode = str  # type: ignore[assignment]
    ResultMessage = None  # type: ignore[assignment]
    TextBlock = None  # type: ignore[assignment]

PermissionModeType = _PermissionMode


@dataclass
class ClaudeRunResult:
    text: str
    session_id: str | None
    total_cost: float
    duration_ms: int


def _ensure_sdk() -> None:
    if ClaudeSDKClient is None or ClaudeCodeOptions is None:
        raise RuntimeError("claude_code_sdk is not available. Install dependencies via `make install`.")


async def _collect_messages(client: Any) -> ClaudeRunResult:
    collected: list[str] = []
    session_id: str | None = None
    total_cost = 0.0
    duration_ms = 0
    async for message in client.receive_response():
        if AssistantMessage is not None and isinstance(message, AssistantMessage):
            for block in getattr(message, "content", []) or []:
                if TextBlock is not None and isinstance(block, TextBlock):
                    text = getattr(block, "text", "")
                    if text:
                        print(text, end="", flush=True)
                        collected.append(text)
        if ResultMessage is not None and isinstance(message, ResultMessage):
            total_cost = getattr(message, "total_cost_usd", 0.0) or 0.0
            duration_ms = getattr(message, "duration_ms", 0) or 0
            session_id = getattr(message, "session_id", None)
    print("", flush=True)
    return ClaudeRunResult("".join(collected), session_id, total_cost, duration_ms)


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
    _ensure_sdk()
    client_cls = ClaudeSDKClient
    options_cls = ClaudeCodeOptions
    if client_cls is None or options_cls is None:
        raise RuntimeError("Claude SDK not initialised")

    options = options_cls(
        system_prompt=system_prompt or "You are the Amplifier code-generation assistant.",
        cwd=str(cwd),
        add_dirs=list(add_dirs or []),
        allowed_tools=list(allowed_tools),
        permission_mode=permission_mode,  # type: ignore[arg-type]
        max_turns=max_turns,
    )

    async with client_cls(options=options) as client:  # type: ignore[misc]
        await client.query(prompt)
        result = await _collect_messages(client)

    return result
