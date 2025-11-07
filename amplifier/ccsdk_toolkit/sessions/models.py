"""Session state models for CCSDK toolkit."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel
from pydantic import Field

# Import TokenUsageSnapshot if available (for type hints)
try:
    from amplifier.session_monitor.models import TokenUsageSnapshot
except ImportError:
    TokenUsageSnapshot = Any  # Fallback for type checking


class SessionMetadata(BaseModel):
    """Metadata about a session.

    Attributes:
        session_id: Unique session identifier
        name: Human-readable session name
        created_at: When the session was created
        updated_at: When the session was last updated
        turns: Number of conversation turns
        total_tokens: Total tokens used (if available)
        cost_usd: Estimated cost in USD (if available)
        duration_seconds: Total session duration
        tags: Optional tags for categorization
    """

    session_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(default="unnamed-session")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    turns: int = Field(default=0)
    total_tokens: int = Field(default=0)
    cost_usd: float = Field(default=0.0)
    duration_seconds: float = Field(default=0.0)
    tags: list[str] = Field(default_factory=list)

    def update(self):
        """Update the timestamp."""
        self.updated_at = datetime.now()

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "code-review-session",
                "created_at": "2025-01-01T10:00:00",
                "updated_at": "2025-01-01T10:30:00",
                "turns": 5,
                "total_tokens": 1500,
                "cost_usd": 0.15,
                "duration_seconds": 1800,
                "tags": ["review", "python"],
            }
        }


class SessionState(BaseModel):
    """Complete session state.

    Attributes:
        metadata: Session metadata
        messages: List of conversation messages
        context: Any additional context data
        config: Configuration used for this session
        checkpoint_data: Optional checkpoint data for session resume
        token_usage_history: History of token usage snapshots
        last_checkpoint_at: Timestamp of last checkpoint
    """

    metadata: SessionMetadata
    messages: list[dict[str, Any]] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    config: dict[str, Any] = Field(default_factory=dict)
    checkpoint_data: dict[str, Any] | None = None
    token_usage_history: list[dict] = Field(default_factory=list)
    last_checkpoint_at: datetime | None = None

    def add_message(self, role: str, content: str, metadata: dict | None = None):
        """Add a message to the session.

        Args:
            role: Message role (user/assistant/system)
            content: Message content
            metadata: Optional message metadata
        """
        message: dict[str, Any] = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        if metadata:
            message["metadata"] = metadata
        self.messages.append(message)
        self.metadata.turns += 1
        self.metadata.update()

    def get_conversation(self) -> str:
        """Get formatted conversation history.

        Returns:
            Formatted conversation as string
        """
        lines = []
        for msg in self.messages:
            role = msg["role"].upper()
            content = msg["content"]
            lines.append(f"{role}: {content}\n")
        return "\n".join(lines)

    def create_checkpoint(self, data: dict) -> None:
        """Create a checkpoint with the given data.

        Args:
            data: Checkpoint data to store
        """
        self.checkpoint_data = data
        self.last_checkpoint_at = datetime.now()

    def restore_from_checkpoint(self) -> dict | None:
        """Restore checkpoint data.

        Returns:
            Checkpoint data if available, None otherwise
        """
        return self.checkpoint_data

    def record_token_usage(self, usage) -> None:
        """Record token usage in history.

        Args:
            usage: Token usage snapshot to record
        """
        self.token_usage_history.append(
            {
                "timestamp": usage.timestamp.isoformat(),
                "estimated_tokens": usage.estimated_tokens,
                "usage_pct": usage.usage_pct,
                "source": usage.source,
            }
        )

    class Config:
        json_schema_extra = {
            "example": {
                "metadata": {"session_id": "123e4567-e89b-12d3-a456-426614174000", "name": "example-session"},
                "messages": [
                    {"role": "user", "content": "Review this code"},
                    {"role": "assistant", "content": "Here's my review..."},
                ],
                "context": {"project": "myapp"},
                "config": {"max_turns": 5},
            }
        }
