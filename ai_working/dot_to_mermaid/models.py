"""
Shared data models for DOT to Mermaid conversion.

These models define the contract between modules.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class DotGraph:
    """Parsed DOT graph representation."""

    name: str
    graph_type: str  # "digraph" or "graph"
    nodes: dict[str, dict[str, Any]]  # node_id -> attributes
    edges: list[dict[str, Any]]  # list of edge definitions
    subgraphs: list["DotGraph"]  # nested subgraphs
    attributes: dict[str, Any]  # graph-level attributes
    raw_source: str  # original DOT source (preserved for reference)


@dataclass
class ConversionResult:
    """Result of converting a single DOT file."""

    source_file: Path
    mermaid_content: str
    conversion_method: str  # "deterministic", "failed", or "error"
    warnings: list[str]  # any issues encountered
    success: bool


@dataclass
class SessionState:
    """Progress tracking for conversion session."""

    processed_files: list[str]  # paths already processed
    results: list[ConversionResult]
    failed_files: list[tuple[str, str]]  # (path, error_message)
    total_files: int
    current_file: str | None = None
