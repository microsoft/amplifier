"""
Claude Code SDK client wrapper (no fallbacks).

Contract:
- `class LLM`: `.complete(prompt: str, system: str | None = None, model: str | None = None, timeout_s: int = 60) -> str`

Behavior:
- Requires `claude-code-sdk` and runnable Claude CLI.
- If unavailable or errors occur, raises a clear `MicrotaskError` with guidance.
"""

from __future__ import annotations

from dataclasses import dataclass

try:
    # Python SDK (pip install claude-code-sdk)
    from claude_code_sdk import ClaudeCodeOptions
    from claude_code_sdk import ClaudeSDKClient
    from claude_code_sdk import query as sdk_query
except Exception:  # pragma: no cover - unavailable
    ClaudeSDKClient = None  # type: ignore
    ClaudeCodeOptions = None  # type: ignore
    sdk_query = None  # type: ignore

from .models import MicrotaskError


@dataclass
class LLMConfig:
    model_default: str = "claude-3-5-sonnet-20241022"
    timeout_s: int = 60


def is_sdk_available() -> bool:
    """Return True if the Python SDK is importable and Claude CLI is runnable."""
    import shutil as _shutil
    import subprocess as _subprocess

    if ClaudeSDKClient is None or ClaudeCodeOptions is None or sdk_query is None:
        return False
    cli = _shutil.which("claude") or _shutil.which("@anthropic-ai/claude-code")
    if not cli:
        return False
    try:
        proc = _subprocess.run([cli, "--help"], capture_output=True, text=True, timeout=3)
        return proc.returncode == 0
    except Exception:
        return False


class LLM:
    def __init__(self, cfg: LLMConfig | None = None) -> None:
        self.cfg = cfg or LLMConfig()
        self._available = is_sdk_available()

    def _ensure_available(self) -> None:
        if not self._available:
            raise MicrotaskError(
                "Claude Code SDK/CLI not available. Install and configure first: "
                "pip install claude-code-sdk && npm i -g @anthropic-ai/claude-code; then retry."
            )

    def complete(
        self, prompt: str, system: str | None = None, model: str | None = None, timeout_s: int | None = None
    ) -> str:
        self._ensure_available()

        # Map to SDK options; keep it minimal and synchronous
        assert ClaudeCodeOptions is not None and sdk_query is not None
        opts = ClaudeCodeOptions(
            system_prompt=system,
            model=model or self.cfg.model_default,
            max_turns=1,
        )

        try:
            return self._run_query_sync(prompt, opts)
        except Exception as e:
            raise MicrotaskError(f"Claude Code query failed: {e}") from e

    def _run_query_sync(self, prompt: str, opts) -> str:
        import asyncio

        async def _go() -> str:
            chunks: list[str] = []
            final: str | None = None
            async for message in sdk_query(prompt=prompt, options=opts):  # type: ignore[misc]
                tname = type(message).__name__
                if tname == "ResultMessage":
                    final = getattr(message, "result", None)
                elif hasattr(message, "content"):
                    for block in getattr(message, "content", []) or []:
                        txt = getattr(block, "text", None)
                        if txt:
                            chunks.append(str(txt))
            return final or "".join(chunks)

        return asyncio.run(_go())

    # No fallbacks by design.
