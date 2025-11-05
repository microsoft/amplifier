"""Data models for content loader module"""

from dataclasses import dataclass
from dataclasses import field
from typing import Any


@dataclass
class ContentItem:
    """Represents a loaded content item.

    This is the primary data structure returned by ContentLoader.
    All fields are immutable after creation.

    Attributes:
        content_id: Unique identifier (SHA256 hash of source_path)
        title: Extracted title or filename-based fallback
        content: The actual text content
        source_path: Absolute path to source file
        format: File format ('md', 'txt', 'json')
        metadata: Optional metadata (e.g., from JSON files)
    """

    content_id: str
    title: str
    content: str
    source_path: str
    format: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate content item after initialization"""
        if not self.content_id:
            raise ValueError("content_id cannot be empty")
        if not self.source_path:
            raise ValueError("source_path cannot be empty")
        if self.format not in ("md", "txt", "json"):
            raise ValueError(f"Invalid format: {self.format}")
