"""
Pydantic models for the slides tool.

This module defines the data structures used throughout the slides tool,
serving as the contract between components (the "studs" in our brick architecture).
"""

from datetime import datetime
from typing import Any
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_serializer


class Slide(BaseModel):
    """Individual slide data structure."""

    title: str = Field(description="Slide title")
    content: str = Field(description="Slide content in Markdown format")
    notes: str | None = Field(None, description="Speaker notes")
    fragments: list[str] = Field(default_factory=list, description="Fragment animations")
    transition: str | None = Field("slide", description="Transition type")
    background: str | None = Field(None, description="Background color or image")
    layout: Literal["title", "content", "two-column", "image"] = Field("content", description="Slide layout type")


class Presentation(BaseModel):
    """Complete presentation data structure."""

    model_config = ConfigDict()

    title: str = Field(description="Presentation title")
    subtitle: str | None = Field(None, description="Presentation subtitle")
    author: str | None = Field(None, description="Author name")
    date: datetime | None = Field(default_factory=datetime.now, description="Creation date")
    theme: str = Field("black", description="Reveal.js theme")
    slides: list[Slide] = Field(default_factory=list, description="List of slides")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    version: int = Field(1, description="Version number for tracking revisions")

    @field_serializer("date")
    def serialize_date(self, date: datetime | None, _info):
        """Serialize datetime to ISO format."""
        return date.isoformat() if date else None


class GenerationRequest(BaseModel):
    """Request structure for slide generation."""

    prompt: str = Field(description="User's generation prompt")
    context: str | None = Field(None, description="Additional context for generation")
    context_file: str | None = Field(None, description="Path to context file")
    num_slides: int | None = Field(None, description="Desired number of slides")
    style: Literal["professional", "academic", "creative", "minimal"] = Field(
        "professional", description="Presentation style"
    )
    include_images: bool = Field(False, description="Whether to include image placeholders")


class RevisionRequest(BaseModel):
    """Request structure for slide revision."""

    presentation_file: str = Field(description="Path to existing presentation")
    feedback: str = Field(description="Revision feedback")
    specific_slides: list[int] | None = Field(None, description="Specific slide indices to revise")


class ExportRequest(BaseModel):
    """Request structure for presentation export."""

    presentation_file: str = Field(description="Path to presentation file")
    format: Literal["html", "png", "gif"] = Field(description="Export format")
    output_path: str | None = Field(None, description="Custom output path")
    options: dict[str, Any] = Field(default_factory=dict, description="Format-specific options")


class GenerationResult(BaseModel):
    """Result of slide generation."""

    success: bool = Field(description="Whether generation succeeded")
    presentation: Presentation | None = Field(None, description="Generated presentation")
    markdown: str | None = Field(None, description="Markdown representation")
    html_path: str | None = Field(None, description="Path to saved HTML file")
    error: str | None = Field(None, description="Error message if failed")
    generation_time: float = Field(description="Time taken in seconds")


class ExportResult(BaseModel):
    """Result of presentation export."""

    success: bool = Field(description="Whether export succeeded")
    output_path: str | None = Field(None, description="Path to exported file")
    format: str = Field(description="Export format used")
    error: str | None = Field(None, description="Error message if failed")
    export_time: float = Field(description="Time taken in seconds")
