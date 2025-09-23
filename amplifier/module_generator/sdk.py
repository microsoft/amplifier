"""Claude Code SDK integration helpers for the module generator."""

from __future__ import annotations

import logging
from collections.abc import Callable
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionError
from amplifier.ccsdk_toolkit import SessionOptions

from .models import ClaudeSessionResult
from .models import PermissionMode

logger = logging.getLogger(__name__)


def _preview(value: str | None, limit: int = 200) -> str:
    """Return a trimmed preview of large prompt strings for logging."""

    if not value:
        return "(empty)"

    cleaned = value.replace("\n", " ").strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + "..."


def _describe_message(message: dict[str, Any]) -> str:
    """Produce a readable description of Claude SDK messages for logging."""

    message_type = message.get("type") or message.get("subtype")

    if not message_type:
        blocks = message.get("content")
        if isinstance(blocks, list):
            if any(isinstance(block, dict) and block.get("text") for block in blocks):
                message_type = "assistant"
            elif any(isinstance(block, dict) and block.get("tool_use_id") for block in blocks):
                message_type = "tool_result"
        if not message_type and message.get("name"):
            message_type = "tool_use"
        if not message_type:
            message_type = "unknown"

    summary = f"Claude message type={message_type}"

    if message_type == "assistant":
        extracted = _extract_text(message)
        if extracted:
            snippet = " ".join(extracted)
            summary += f" text={snippet[:200]!r}"
        else:
            summary += " text=<empty>"
    elif message_type == "tool_use":
        name = message.get("name") or "unknown"
        summary += f" tool={name}"
    elif message_type == "tool_result":
        blocks = message.get("content") or []
        for block in blocks:
            if isinstance(block, dict):
                content = block.get("content")
                if isinstance(content, str):
                    summary += f" result={content.strip()[:200]!r}"
                    break
    elif message_type == "error_max_turns":
        summary += " (max turns reached)"

    return summary


class ClaudeUnavailableError(RuntimeError):
    """Raised when the Claude Code SDK is unavailable or misconfigured."""


@dataclass
class SessionCallbacks:
    """Optional callbacks invoked during session streaming."""

    on_todo: Callable[[list[dict]], None] | None = None
    on_message: Callable[[dict[str, Any]], None] | None = None


class ClaudeSessionManager:
    """Wrapper responsible for running prompts through the Claude SDK."""

    def __init__(self, *, repo_root: str):
        self.repo_root = repo_root

    async def run(
        self,
        *,
        prompt: str,
        system_prompt: str,
        permission_mode: PermissionMode,
        allowed_tools: Iterable[str],
        max_turns: int,
        add_dirs: Iterable[str] | None = None,
        callbacks: SessionCallbacks | None = None,
    ) -> ClaudeSessionResult:
        """Execute a single-turn conversation and collect structured output."""

        callbacks = callbacks or SessionCallbacks()
        context_dirs = {str(Path(self.repo_root).resolve())}
        for extra in add_dirs or []:
            context_dirs.add(str(Path(extra).resolve()))

        settings_path = Path(self.repo_root) / ".claude" / "settings.json"

        options = SessionOptions(
            system_prompt=system_prompt,
            permission_mode=permission_mode,
            allowed_tools=list(allowed_tools),
            cwd=Path(self.repo_root),
            add_dirs=[Path(path) for path in context_dirs],
            settings_path=settings_path if settings_path.exists() else None,
            max_turns=max_turns,
        )

        logger.debug("Starting Claude session with permission_mode=%s", permission_mode)
        logger.debug("System prompt (first 200 chars): %s", _preview(system_prompt))
        logger.debug("User prompt (first 200 chars): %s", _preview(prompt))

        collected_messages: list[dict[str, Any]] = []
        todos_holder: list[dict[str, Any]] = []

        def handle_message(message: dict[str, Any]) -> None:
            collected_messages.append(message)
            logger.debug("%s", _describe_message(message))
            if callbacks.on_message:
                callbacks.on_message(message)

        def handle_todos(todos: list[dict[str, Any]]) -> None:
            todos_holder.clear()
            todos_holder.extend(todos)
            if callbacks.on_todo:
                callbacks.on_todo(todos)

        try:
            async with ClaudeSession(options) as session:
                response = await session.query(
                    prompt,
                    message_callback=handle_message,
                    todo_callback=handle_todos,
                )
        except SessionError as exc:  # pragma: no cover - depends on external CLI availability
            raise ClaudeUnavailableError(
                "Claude Code SDK is required for module generation. Install `claude-code-sdk` and the `@anthropic-ai/claude-code` CLI."
            ) from exc

        if not response.success:
            raise RuntimeError(response.error or "Claude session returned no output")

        logger.debug(
            "Claude session %s completed with %s characters",
            response.session_id,
            len(response.content),
        )

        todos = response.todos or todos_holder

        return ClaudeSessionResult(
            text=response.content.strip(),
            todos=todos,
            usage=response.usage,
            session_id=response.session_id,
        )


def _extract_text(normalized: dict[str, Any]) -> list[str]:
    """Extract plaintext segments from normalized Claude messages."""

    texts: list[str] = []

    content = normalized.get("content")
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                if block.get("tool_use_id"):
                    continue
                text_value = block.get("text")
                if isinstance(text_value, str):
                    stripped = text_value.strip()
                    if stripped:
                        texts.append(stripped)
            elif isinstance(block, str):
                stripped = block.strip()
                if stripped:
                    texts.append(stripped)

    result = normalized.get("result")
    if isinstance(result, dict):
        for key in ("text", "output_text"):
            value = result.get(key)
            if isinstance(value, str):
                stripped = value.strip()
                if stripped:
                    texts.append(stripped)

    inline_text = normalized.get("text")
    if isinstance(inline_text, str):
        stripped = inline_text.strip()
        if stripped:
            texts.append(stripped)

    return [segment for segment in texts if segment]
