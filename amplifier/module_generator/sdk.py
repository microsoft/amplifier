"""Claude Code SDK integration helpers for the module generator."""

from __future__ import annotations

import logging
from collections.abc import Callable
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import ClaudeSessionResult
from .models import PermissionMode

logger = logging.getLogger(__name__)

try:  # pragma: no cover - import guard exercised in tests
    from claude_code_sdk import ClaudeCodeOptions
    from claude_code_sdk import ClaudeSDKClient

    CLAUDE_SDK_AVAILABLE = True
except Exception:  # pragma: no cover - ensures graceful fallback when SDK missing
    ClaudeCodeOptions = None  # type: ignore
    ClaudeSDKClient = None  # type: ignore
    CLAUDE_SDK_AVAILABLE = False


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

        if not CLAUDE_SDK_AVAILABLE or ClaudeSDKClient is None or ClaudeCodeOptions is None:
            raise ClaudeUnavailableError(
                "Claude Code SDK is required for module generation. Install `claude-code-sdk` and the `@anthropic-ai/claude-code` CLI."
            )

        callbacks = callbacks or SessionCallbacks()
        context_dirs = set(add_dirs or [])
        context_dirs.add(self.repo_root)
        settings_path = Path(self.repo_root) / ".claude" / "settings.json"

        options = ClaudeCodeOptions(
            system_prompt=system_prompt,
            permission_mode=permission_mode,
            allowed_tools=list(allowed_tools),
            cwd=self.repo_root,
            add_dirs=list(context_dirs),
            settings=str(settings_path) if settings_path.exists() else None,
            max_turns=max_turns,
        )

        logger.debug("Starting Claude session with permission_mode=%s", permission_mode)
        logger.debug("System prompt (first 200 chars): %s", _preview(system_prompt))
        logger.debug("User prompt (first 200 chars): %s", _preview(prompt))

        async with ClaudeSDKClient(options=options) as client:  # type: ignore[arg-type]
            session_id = getattr(client, "session_id", None)
            await client.query(prompt)

            logger.debug("Claude session %s awaiting response", session_id)
            text_parts: list[str] = []
            todos: list[dict] = []
            usage: dict | None = None

            async for message in client.receive_response():
                normalized = _normalize_message(message)
                logger.debug("%s", _describe_message(normalized))
                if callbacks.on_message:
                    callbacks.on_message(normalized)

                if normalized.get("type") == "tool_use" and normalized.get("name") == "TodoWrite":
                    todos = normalized.get("input", {}).get("todos", [])
                    if callbacks.on_todo:
                        callbacks.on_todo(todos)

                for segment in _extract_text(normalized):
                    if segment:
                        text_parts.append(segment)

                if "usage" in normalized and normalized["usage"]:
                    usage = normalized["usage"]

            output_lines = [segment for segment in text_parts if segment]
            output_text = "\n".join(output_lines).strip()

            if not output_lines and not todos and usage is None:
                raise RuntimeError("Claude session ended without producing output")

            logger.debug("Claude session %s completed with %s characters", session_id, len(output_text))

            return ClaudeSessionResult(text=output_text, todos=todos, usage=usage, session_id=session_id)


def _normalize_message(message: Any) -> dict[str, Any]:
    """Convert SDK message objects into plain dictionaries for easier handling."""

    if isinstance(message, dict):
        return message

    normalized: dict[str, Any] = {}

    for attribute in ["type", "content", "name", "input", "usage", "id", "result", "text"]:
        if hasattr(message, attribute):
            normalized[attribute] = getattr(message, attribute)

    if hasattr(message, "__dict__"):
        for key, value in vars(message).items():
            normalized.setdefault(key, value)

    if hasattr(message, "to_dict"):
        try:
            normalized = {**message.to_dict(), **normalized}
        except Exception:  # pragma: no cover - defensive; if to_dict fails we keep current data
            logger.debug("Failed to coerce message via to_dict()", exc_info=True)

    content = normalized.get("content")
    if isinstance(content, list):
        normalized["content"] = [_coerce_block(block) for block in content]
    else:
        normalized["content"] = []

    return normalized


def _coerce_block(block: Any) -> dict[str, Any]:
    """Convert Claude SDK content blocks to plain dictionaries."""

    if isinstance(block, dict):
        return block

    block_dict: dict[str, Any] = {}

    for attr in ("type", "text", "id", "language", "data", "name"):
        if hasattr(block, attr):
            value = getattr(block, attr)
            if value is not None:
                block_dict[attr] = value

    if not block_dict and hasattr(block, "__dict__"):
        block_dict = dict(vars(block))

    return block_dict


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
                    texts.append(text_value.strip())
            elif isinstance(block, str):
                texts.append(block.strip())

    result = normalized.get("result")
    if isinstance(result, dict):
        for key in ("text", "output_text"):
            value = result.get(key)
            if isinstance(value, str):
                texts.append(value.strip())

    inline_text = normalized.get("text")
    if isinstance(inline_text, str):
        texts.append(inline_text.strip())

    return [segment for segment in texts if segment]
