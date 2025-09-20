"""Data models for idea synthesis."""

from dataclasses import dataclass
from dataclasses import field
from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class SourceFile:
    """Represents a markdown source file."""

    path: Path
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FileSummary:
    """Summary of a single file."""

    file_path: Path
    key_points: list[str]
    main_ideas: list[str]
    important_quotes: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CrossCuttingTheme:
    """A theme that appears across multiple documents."""

    theme: str
    description: str
    supporting_points: list[str]
    source_files: list[Path]
    confidence: float  # 0.0 to 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExpandedIdea:
    """An expanded synthesis combining themes with original context."""

    title: str
    synthesis: str
    themes: list[CrossCuttingTheme]
    supporting_quotes: list[tuple[Path, str]]  # (source_file, quote)
    action_items: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SynthesisState:
    """Tracks the state of the synthesis pipeline."""

    session_id: str
    total_files: int = 0
    processed_files: int = 0
    summaries: list[FileSummary] = field(default_factory=list)
    themes: list[CrossCuttingTheme] = field(default_factory=list)
    expanded_ideas: list[ExpandedIdea] = field(default_factory=list)
    current_stage: str = "reader"
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)
