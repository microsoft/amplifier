"""Data models for memory storage"""

from datetime import datetime
from typing import Any
from typing import Literal

from pydantic import BaseModel
from pydantic import Field

MemoryCategory = Literal["learning", "decision", "issue_solved", "preference", "pattern"]


class Memory(BaseModel):
    """Input memory to be stored"""

    content: str = Field(..., description="The memory content")
    category: MemoryCategory = Field(..., description="Type of memory")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional context")


class StoredMemory(Memory):
    """Memory with storage metadata"""

    id: str = Field(..., description="Unique identifier")
    timestamp: datetime = Field(..., description="When memory was created")
    accessed_count: int = Field(default=0, description="Number of times accessed")
