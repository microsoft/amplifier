"""Revision state management for FMA."""

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from pathlib import Path


@dataclass
class RevisionState:
    """State for a PRD revision/worktree.

    This represents the state of a PRD implementation in both:
    - The worktree (.xfma/state.json)
    - The central database ($LAMP_DB_HOME/database/{id}/state.json)
    """

    id: str  # Unique identifier (e.g., "basic-functions_a1b2c3d4")
    prd_name: str  # PRD name (e.g., "001_basic_functions")
    worktree_path: str  # Full path to worktree
    worktree_name: str  # Worktree directory name
    created_at: str  # ISO format timestamp
    state: str = "building"  # Current state
    current_agent: str = "builder"  # Current agent working on this
    history: list[dict] = field(default_factory=list)  # State change history

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "prd_name": self.prd_name,
            "worktree_path": self.worktree_path,
            "worktree_name": self.worktree_name,
            "created_at": self.created_at,
            "state": self.state,
            "current_agent": self.current_agent,
            "history": self.history,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RevisionState":
        """Create RevisionState from dictionary."""
        return cls(
            id=data["id"],
            prd_name=data["prd_name"],
            worktree_path=data["worktree_path"],
            worktree_name=data["worktree_name"],
            created_at=data["created_at"],
            state=data.get("state", "building"),
            current_agent=data.get("current_agent", "builder"),
            history=data.get("history", []),
        )

    def add_history_entry(self, message: str) -> None:
        """Add entry to history with current state and agent.

        Args:
            message: Description of the state change
        """
        self.history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "state": self.state,
                "agent": self.current_agent,
                "message": message,
            }
        )

    def transition_to(self, new_state: str, new_agent: str, message: str) -> None:
        """Transition to a new state with a new agent.

        Args:
            new_state: New state to transition to
            new_agent: Agent that will handle this state
            message: Description of the transition
        """
        self.state = new_state
        self.current_agent = new_agent
        self.add_history_entry(message)

    @classmethod
    def create_initial(
        cls,
        unique_id: str,
        prd_name: str,
        worktree_path: Path,
    ) -> "RevisionState":
        """Create initial RevisionState for a new PRD worktree.

        Args:
            unique_id: Unique identifier
            prd_name: PRD name
            worktree_path: Path to the worktree

        Returns:
            New RevisionState instance
        """
        now = datetime.now().isoformat()
        state = cls(
            id=unique_id,
            prd_name=prd_name,
            worktree_path=str(worktree_path),
            worktree_name=worktree_path.name,
            created_at=now,
            state="building",
            current_agent="builder",
            history=[
                {
                    "timestamp": now,
                    "state": "building",
                    "agent": "builder",
                    "message": "Worktree created and builder agent started",
                }
            ],
        )
        return state


# Valid state transitions
STATE_TRANSITIONS = {
    "building": ["review_pending", "failed"],
    "review_pending": ["in_review"],
    "in_review": ["approved", "rejected", "building"],
    "approved": ["merged"],
    "rejected": ["building"],
    "failed": ["building"],
    "merged": [],  # Terminal state
}

# Agent assignments for each state
STATE_AGENTS = {
    "building": "builder",
    "review_pending": "orchestrator",
    "in_review": "reviewer",
    "approved": "orchestrator",
    "rejected": "orchestrator",
    "failed": "orchestrator",
    "merged": None,
}
