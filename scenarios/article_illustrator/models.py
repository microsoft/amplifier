"""Data models for article illustrator tool."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from pydantic import Field


class ContentBlock(BaseModel):
    """A block of content from the article."""

    content: str
    line_start: int
    line_end: int
    block_type: Literal["heading", "paragraph", "list", "code", "quote"]


class IllustrationPoint(BaseModel):
    """A point in the article where an illustration could be added."""

    section_title: str
    section_index: int
    line_number: int
    context_before: str
    context_after: str
    importance: Literal["high", "medium", "low"]
    suggested_placement: Literal["before_section", "after_intro", "mid_section"]


class ImagePrompt(BaseModel):
    """An image generation prompt for a specific illustration point."""

    illustration_id: str
    point: IllustrationPoint
    base_prompt: str
    style_modifiers: list[str] = Field(default_factory=list)
    full_prompt: str
    metadata: dict[str, str] = Field(default_factory=dict)


class GeneratedImage(BaseModel):
    """A single generated image from an API."""

    prompt_id: str
    api: Literal["imagen", "dalle", "gptimage"]
    url: str
    local_path: Path
    generation_params: dict = Field(default_factory=dict)
    cost_estimate: float = 0.0


class ImageAlternatives(BaseModel):
    """Primary image with alternatives for an illustration point."""

    illustration_id: str
    primary: GeneratedImage
    alternatives: list[GeneratedImage] = Field(default_factory=list)
    selection_reason: str | None = None


class SessionState(BaseModel):
    """Persistent state for the illustration session."""

    article_path: Path
    output_dir: Path
    style_params: dict[str, str] = Field(default_factory=dict)
    analysis_complete: bool = False
    prompts_complete: bool = False
    images_complete: bool = False
    markdown_complete: bool = False
    illustration_points: list[IllustrationPoint] = Field(default_factory=list)
    prompts: list[ImagePrompt] = Field(default_factory=list)
    images: list[ImageAlternatives] = Field(default_factory=list)
    images_generated: int = 0
    total_cost: float = 0.0
    errors: list[dict[str, str]] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True
