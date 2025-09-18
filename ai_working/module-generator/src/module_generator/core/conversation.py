"""Conversation state management for multi-turn interactions.

This module handles the state tracking and checkpointing of multi-turn
conversations with the Claude SDK.
"""

import json
import uuid
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import Literal


@dataclass
class Message:
    """A single message in the conversation."""

    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationContext:
    """Context that persists across conversation turns."""

    module_spec: dict[str, Any]
    working_directory: Path
    target_directory: Path
    config: dict[str, Any] = field(default_factory=dict)
    state: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationState:
    """Complete state of a multi-turn conversation."""

    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: list[Message] = field(default_factory=list)
    context: ConversationContext | None = None
    status: Literal["active", "completed", "failed", "suspended"] = "active"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    checkpoint_path: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ConversationManager:
    """Manages conversation state and checkpointing."""

    def __init__(self, checkpoint_dir: Path | None = None):
        """Initialize the conversation manager.

        Args:
            checkpoint_dir: Directory for storing conversation checkpoints
        """
        self.checkpoint_dir = checkpoint_dir or Path(".conversation_checkpoints")
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.current_state: ConversationState | None = None

    def start_conversation(
        self,
        module_spec: dict[str, Any],
        working_directory: Path,
        target_directory: Path,
        config: dict[str, Any] | None = None,
    ) -> ConversationState:
        """Start a new conversation.

        Args:
            module_spec: The module specification
            working_directory: Working directory path
            target_directory: Target directory for generated module
            config: Optional configuration

        Returns:
            New conversation state
        """
        context = ConversationContext(
            module_spec=module_spec,
            working_directory=working_directory,
            target_directory=target_directory,
            config=config or {},
        )

        self.current_state = ConversationState(context=context)
        self._save_checkpoint()
        return self.current_state

    def add_message(
        self, role: Literal["user", "assistant", "system"], content: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """Add a message to the current conversation.

        Args:
            role: Message role
            content: Message content
            metadata: Optional message metadata
        """
        if not self.current_state:
            raise RuntimeError("No active conversation")

        message = Message(role=role, content=content, metadata=metadata or {})
        self.current_state.messages.append(message)
        self.current_state.updated_at = datetime.now().isoformat()
        self._save_checkpoint()

    def get_messages(self) -> list[Message]:
        """Get all messages in the current conversation.

        Returns:
            List of messages
        """
        if not self.current_state:
            return []
        return self.current_state.messages

    def get_conversation_history(self) -> str:
        """Get formatted conversation history for context.

        Returns:
            Formatted conversation history
        """
        if not self.current_state:
            return ""

        history = []
        for msg in self.current_state.messages:
            history.append(f"{msg.role.upper()}: {msg.content}")

        return "\n\n".join(history)

    def update_status(self, status: Literal["active", "completed", "failed", "suspended"]) -> None:
        """Update conversation status.

        Args:
            status: New status
        """
        if not self.current_state:
            raise RuntimeError("No active conversation")

        self.current_state.status = status
        self.current_state.updated_at = datetime.now().isoformat()
        self._save_checkpoint()

    def save_checkpoint(self, checkpoint_name: str | None = None) -> Path:
        """Save a conversation checkpoint.

        Args:
            checkpoint_name: Optional custom checkpoint name

        Returns:
            Path to checkpoint file
        """
        if not self.current_state:
            raise RuntimeError("No active conversation")

        checkpoint_name = (
            checkpoint_name or f"{self.current_state.conversation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_name}.json"

        self.current_state.checkpoint_path = checkpoint_path
        self._save_checkpoint()

        return checkpoint_path

    def load_checkpoint(self, checkpoint_path: Path) -> ConversationState:
        """Load a conversation from checkpoint.

        Args:
            checkpoint_path: Path to checkpoint file

        Returns:
            Loaded conversation state
        """
        with open(checkpoint_path) as f:
            data = json.load(f)

        # Reconstruct context
        context = ConversationContext(
            module_spec=data["context"]["module_spec"],
            working_directory=Path(data["context"]["working_directory"]),
            target_directory=Path(data["context"]["target_directory"]),
            config=data["context"]["config"],
            state=data["context"]["state"],
        )

        # Reconstruct messages
        messages = [
            Message(role=msg["role"], content=msg["content"], timestamp=msg["timestamp"], metadata=msg["metadata"])
            for msg in data["messages"]
        ]

        # Reconstruct state
        self.current_state = ConversationState(
            conversation_id=data["conversation_id"],
            messages=messages,
            context=context,
            status=data["status"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            checkpoint_path=Path(data["checkpoint_path"]) if data.get("checkpoint_path") else None,
            metadata=data["metadata"],
        )

        return self.current_state

    def list_checkpoints(self) -> list[dict[str, Any]]:
        """List available checkpoints.

        Returns:
            List of checkpoint info
        """
        checkpoints = []
        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            try:
                with open(checkpoint_file) as f:
                    data = json.load(f)
                checkpoints.append(
                    {
                        "path": checkpoint_file,
                        "conversation_id": data["conversation_id"],
                        "status": data["status"],
                        "created_at": data["created_at"],
                        "updated_at": data["updated_at"],
                        "message_count": len(data["messages"]),
                    }
                )
            except Exception:
                continue

        return sorted(checkpoints, key=lambda x: x["updated_at"], reverse=True)

    def _save_checkpoint(self) -> None:
        """Internal method to save current state to checkpoint."""
        if not self.current_state or not self.current_state.context:
            return

        checkpoint_path = (
            self.current_state.checkpoint_path
            or self.checkpoint_dir / f"{self.current_state.conversation_id}_latest.json"
        )

        # Prepare data for serialization
        data = {
            "conversation_id": self.current_state.conversation_id,
            "messages": [asdict(msg) for msg in self.current_state.messages],
            "context": {
                "module_spec": self.current_state.context.module_spec,
                "working_directory": str(self.current_state.context.working_directory),
                "target_directory": str(self.current_state.context.target_directory),
                "config": self.current_state.context.config,
                "state": self.current_state.context.state,
            },
            "status": self.current_state.status,
            "created_at": self.current_state.created_at,
            "updated_at": self.current_state.updated_at,
            "checkpoint_path": str(checkpoint_path),
            "metadata": self.current_state.metadata,
        }

        with open(checkpoint_path, "w") as f:
            json.dump(data, f, indent=2)

        self.current_state.checkpoint_path = checkpoint_path
