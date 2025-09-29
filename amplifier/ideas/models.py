"""
Pydantic models for the shared ideas management system.

Defines the data structures for ideas, goals, and the overall document format.
Following the single YAML file storage approach with clean validation.
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel
from pydantic import Field


class Goal(BaseModel):
    """Natural language goal for guiding idea prioritization"""

    id: str = Field(default_factory=lambda: f"goal_{uuid.uuid4().hex[:8]}")
    description: str = Field(..., min_length=10, max_length=500)
    priority: int = Field(default=1, ge=1)
    created: datetime = Field(default_factory=datetime.now)
    active: bool = True


class Idea(BaseModel):
    """Individual idea with metadata and assignment information"""

    id: str = Field(default_factory=lambda: f"idea_{uuid.uuid4().hex[:8]}")
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(default="", max_length=2000)
    assignee: str | None = None  # None means unassigned
    rank: int | None = None  # Position in assignee's queue
    themes: list[str] = Field(default_factory=list)
    priority: Literal["high", "medium", "low"] = "medium"
    created: datetime = Field(default_factory=datetime.now)
    modified: datetime = Field(default_factory=datetime.now)
    notes: str | None = None

    def is_assigned(self) -> bool:
        """Check if idea is assigned to someone"""
        return self.assignee is not None

    def update_modified(self) -> None:
        """Update the modified timestamp"""
        self.modified = datetime.now()


class HistoryEntry(BaseModel):
    """Audit trail entry for tracking changes"""

    timestamp: datetime = Field(default_factory=datetime.now)
    action: Literal["create", "update", "assign", "unassign", "reorder", "delete"]
    user: str = Field(default="system")
    details: str


class Metadata(BaseModel):
    """File metadata for tracking document state"""

    last_modified: datetime = Field(default_factory=datetime.now)
    last_modified_by: str = Field(default="system")
    total_ideas: int = Field(default=0, ge=0)
    total_goals: int = Field(default=0, ge=0)


class IdeasDocument(BaseModel):
    """Complete ideas document structure - the root data model"""

    version: str = Field(default="1.0", pattern=r"^\d+\.\d+$")
    metadata: Metadata = Field(default_factory=Metadata)
    goals: list[Goal] = Field(default_factory=list)
    ideas: list[Idea] = Field(default_factory=list)
    history: list[HistoryEntry] = Field(default_factory=list, max_length=1000)

    def get_user_queue(self, user: str) -> list[Idea]:
        """Get ideas assigned to a specific user, sorted by rank"""
        user_ideas = [i for i in self.ideas if i.assignee == user]
        return sorted(user_ideas, key=lambda x: x.rank or float("inf"))

    def get_unassigned(self) -> list[Idea]:
        """Get all unassigned ideas"""
        return [i for i in self.ideas if i.assignee is None]

    def get_by_theme(self, theme: str) -> list[Idea]:
        """Get ideas containing a specific theme"""
        return [i for i in self.ideas if theme.lower() in [t.lower() for t in i.themes]]

    def get_by_priority(self, priority: Literal["high", "medium", "low"]) -> list[Idea]:
        """Get ideas by priority level"""
        return [i for i in self.ideas if i.priority == priority]

    def find_idea(self, idea_id: str) -> Idea | None:
        """Find an idea by ID"""
        return next((i for i in self.ideas if i.id == idea_id), None)

    def add_idea(self, idea: Idea, user: str = "system") -> None:
        """Add a new idea and update metadata"""
        self.ideas.append(idea)
        self.metadata.total_ideas = len(self.ideas)
        self.metadata.last_modified = datetime.now()
        self.metadata.last_modified_by = user

        # Add history entry
        self.history.append(HistoryEntry(action="create", user=user, details=f"Created idea: {idea.title}"))

    def remove_idea(self, idea_id: str, user: str = "system") -> bool:
        """Remove an idea by ID"""
        idea = self.find_idea(idea_id)
        if not idea:
            return False

        self.ideas = [i for i in self.ideas if i.id != idea_id]
        self.metadata.total_ideas = len(self.ideas)
        self.metadata.last_modified = datetime.now()
        self.metadata.last_modified_by = user

        # Add history entry
        self.history.append(HistoryEntry(action="delete", user=user, details=f"Deleted idea: {idea.title}"))
        return True

    def assign_idea(self, idea_id: str, assignee: str, user: str = "system") -> bool:
        """Assign an idea to a user"""
        idea = self.find_idea(idea_id)
        if not idea:
            return False

        old_assignee = idea.assignee
        idea.assignee = assignee
        idea.update_modified()

        # Set rank to end of user's queue
        user_queue = self.get_user_queue(assignee)
        idea.rank = len(user_queue)

        self.metadata.last_modified = datetime.now()
        self.metadata.last_modified_by = user

        # Add history entry
        action = "assign" if old_assignee is None else "update"
        details = f"Assigned idea '{idea.title}' to {assignee}"
        if old_assignee:
            details += f" (was: {old_assignee})"

        self.history.append(HistoryEntry(action=action, user=user, details=details))
        return True

    def add_goal(self, goal: Goal, user: str = "system") -> None:
        """Add a new goal"""
        self.goals.append(goal)
        self.metadata.total_goals = len(self.goals)
        self.metadata.last_modified = datetime.now()
        self.metadata.last_modified_by = user

        # Add history entry
        self.history.append(HistoryEntry(action="create", user=user, details=f"Added goal: {goal.description[:50]}..."))

    def get_active_goals(self) -> list[Goal]:
        """Get all active goals, sorted by priority"""
        active = [g for g in self.goals if g.active]
        return sorted(active, key=lambda g: g.priority)

    def update_metadata(self, user: str = "system") -> None:
        """Update document metadata"""
        self.metadata.total_ideas = len(self.ideas)
        self.metadata.total_goals = len(self.goals)
        self.metadata.last_modified = datetime.now()
        self.metadata.last_modified_by = user
