"""Multi-turn Claude SDK wrapper for conversation support.

This module provides a wrapper around the Claude SDK that supports
multi-turn conversations with message history management.
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any

from claude_code_sdk import ClaudeCodeOptions
from claude_code_sdk import ClaudeSDKClient


@dataclass
class MultiTurnOptions:
    """Options for multi-turn Claude SDK."""

    system_prompt: str = ""
    max_turns: int = 10
    temperature: float = 0.7
    max_tokens: int | None = None
    checkpoint_dir: Path | None = None
    auto_checkpoint: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


class MultiTurnClaudeSDK:
    """Multi-turn wrapper for Claude SDK with conversation management."""

    def __init__(self, options: MultiTurnOptions | None = None):
        """Initialize multi-turn Claude SDK.

        Args:
            options: Multi-turn conversation options
        """
        self.options = options or MultiTurnOptions()
        self.client: ClaudeSDKClient | None = None
        self.message_history: list[dict[str, str]] = []
        self.turn_count = 0
        self.is_active = False

    async def start_session(self, initial_system_prompt: str | None = None) -> None:
        """Start a new conversation session.

        Args:
            initial_system_prompt: Override system prompt for this session
        """
        system_prompt = initial_system_prompt or self.options.system_prompt

        # Create Claude SDK options
        claude_options = ClaudeCodeOptions(
            system_prompt=system_prompt, max_turns=self.options.max_turns, temperature=self.options.temperature
        )

        # Initialize client
        self.client = ClaudeSDKClient(options=claude_options)
        await self.client.__aenter__()

        self.is_active = True
        self.turn_count = 0
        self.message_history = []

        # Add system prompt to history
        if system_prompt:
            self.message_history.append({"role": "system", "content": system_prompt})

    async def query(self, prompt: str, max_turns: int | None = None) -> str:
        """Send a query and get complete response.

        Args:
            prompt: User prompt
            max_turns: Override max turns for this query

        Returns:
            Complete response text
        """
        if not self.is_active:
            await self.start_session()

        # Add user message to history
        self.message_history.append({"role": "user", "content": prompt})

        # Send query
        await self.client.query(prompt)

        # Collect response
        response = ""
        async for chunk in self.receive_stream():
            response += chunk

        # Add assistant response to history
        self.message_history.append({"role": "assistant", "content": response})

        self.turn_count += 1

        # Auto checkpoint if enabled
        if self.options.auto_checkpoint and self.options.checkpoint_dir:
            await self._save_checkpoint()

        return response

    async def send_message(self, message: str) -> str:
        """Send a follow-up message in the conversation.

        Args:
            message: Follow-up message

        Returns:
            Response text
        """
        return await self.query(message)

    async def receive_stream(self) -> AsyncIterator[str]:
        """Receive response as a stream.

        Yields:
            Response chunks
        """
        if not self.client:
            raise RuntimeError("Session not started")

        async for message in self.client.receive_response():
            if hasattr(message, "content"):
                content = getattr(message, "content", [])
                if isinstance(content, list):
                    for block in content:
                        if hasattr(block, "text"):
                            text = getattr(block, "text", "")
                            if text:
                                yield text

    async def receive_message(self) -> str:
        """Receive a complete message.

        Returns:
            Complete message text
        """
        response = ""
        async for chunk in self.receive_stream():
            response += chunk
        return response

    def has_more(self) -> bool:
        """Check if more responses are expected.

        Returns:
            True if more responses expected
        """
        return self.is_active and self.turn_count < self.options.max_turns

    async def end_session(self) -> None:
        """End the conversation session."""
        if self.client:
            await self.client.__aexit__(None, None, None)
            self.client = None

        self.is_active = False

    def get_history(self) -> list[dict[str, str]]:
        """Get conversation history.

        Returns:
            List of messages
        """
        return self.message_history.copy()

    def get_context(self) -> str:
        """Get formatted conversation context.

        Returns:
            Formatted conversation history
        """
        context = []
        for msg in self.message_history:
            role = msg["role"].upper()
            content = msg["content"]
            context.append(f"{role}: {content}")

        return "\n\n".join(context)

    async def reset(self) -> None:
        """Reset the conversation state."""
        await self.end_session()
        self.message_history = []
        self.turn_count = 0

    async def _save_checkpoint(self) -> None:
        """Save conversation checkpoint."""
        if not self.options.checkpoint_dir:
            return

        import json
        from datetime import datetime

        checkpoint_file = self.options.checkpoint_dir / f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        checkpoint_data = {
            "turn_count": self.turn_count,
            "message_history": self.message_history,
            "options": {
                "system_prompt": self.options.system_prompt,
                "max_turns": self.options.max_turns,
                "temperature": self.options.temperature,
            },
            "metadata": self.options.metadata,
        }

        with open(checkpoint_file, "w") as f:
            json.dump(checkpoint_data, f, indent=2)

    async def load_checkpoint(self, checkpoint_file: Path) -> None:
        """Load conversation from checkpoint.

        Args:
            checkpoint_file: Path to checkpoint file
        """
        import json

        with open(checkpoint_file) as f:
            data = json.load(f)

        self.turn_count = data["turn_count"]
        self.message_history = data["message_history"]

        # Update options
        if "options" in data:
            self.options.system_prompt = data["options"].get("system_prompt", "")
            self.options.max_turns = data["options"].get("max_turns", 10)
            self.options.temperature = data["options"].get("temperature", 0.7)

        # Restart session with loaded state
        await self.start_session(self.options.system_prompt)

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.end_session()


class SimplifiedMultiTurnSDK:
    """Simplified multi-turn SDK for backward compatibility."""

    def __init__(self, system_prompt: str = "", max_turns: int = 10):
        """Initialize simplified SDK.

        Args:
            system_prompt: System prompt
            max_turns: Maximum turns
        """
        self.sdk = MultiTurnClaudeSDK(MultiTurnOptions(system_prompt=system_prompt, max_turns=max_turns))

    async def query(self, prompt: str) -> str:
        """Send query and get response.

        Args:
            prompt: User prompt

        Returns:
            Response text
        """
        return await self.sdk.query(prompt)

    async def send_message(self, message: str) -> str:
        """Send follow-up message.

        Args:
            message: Follow-up message

        Returns:
            Response text
        """
        return await self.sdk.send_message(message)

    def has_more(self) -> bool:
        """Check if more responses expected.

        Returns:
            True if more responses expected
        """
        return self.sdk.has_more()

    async def __aenter__(self):
        """Context manager entry."""
        await self.sdk.start_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.sdk.end_session()
