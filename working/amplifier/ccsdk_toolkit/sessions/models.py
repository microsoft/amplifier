"""Session state models for CCSDK toolkit."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel
from pydantic import Field


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
    """

    metadata: SessionMetadata
    messages: list[dict[str, Any]] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    config: dict[str, Any] = Field(default_factory=dict)

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
