"""Data models for Discovery content processor."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Dict, List, Union, Tuple


class ContentType(str, Enum):
    """Types of content that can be processed."""

    IMAGE = "image"  # Images, napkin sketches, diagrams
    DOCUMENT = "document"  # PDF, DOCX, XLSX, PPTX
    URL = "url"  # Web links
    CANVAS_DRAWING = "canvas_drawing"  # User drawings on canvas
    UNKNOWN = "unknown"


class ProcessingStatus(str, Enum):
    """Status of content processing."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ContentItem:
    """Represents a piece of content dropped into Discovery canvas.

    Attributes:
        id: Unique identifier for this content item
        type: Type of content (image, document, url, etc.)
        source_path: Original file path or URL
        file_name: Display name for the content
        mime_type: MIME type if applicable
        size_bytes: File size in bytes
        created_at: Timestamp when item was added
        metadata: Additional metadata (dimensions, page count, etc.)
    """

    id: str
    type: ContentType
    source_path: str
    file_name: str
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingResult:
    """Result of processing a content item.

    Attributes:
        content_id: ID of the content item processed
        status: Processing status
        analysis: AI analysis/understanding of the content
        extracted_text: Text extracted from the content
        insights: Key insights or findings
        design_elements: Identified design elements (colors, layouts, etc.)
        warnings: Any warnings or issues encountered
        error_message: Error message if processing failed
        processing_time_ms: Time taken to process in milliseconds
        processed_at: Timestamp when processing completed
    """

    content_id: str
    status: ProcessingStatus
    analysis: str = ""
    extracted_text: str = ""
    insights: List[str] = field(default_factory=list)
    design_elements: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    processing_time_ms: Optional[int] = None
    processed_at: datetime = field(default_factory=datetime.now)


@dataclass
class SessionState:
    """State of a processing session for resume capability.

    Attributes:
        session_id: Unique session identifier
        processed_items: List of content IDs that have been processed
        results: Processing results for each item
        failed_items: List of (content_id, error_message) tuples
        total_items: Total number of items to process
        current_item: ID of item currently being processed
        started_at: Timestamp when session started
        updated_at: Timestamp of last update
    """

    session_id: str
    processed_items: List[str] = field(default_factory=list)
    results: List[ProcessingResult] = field(default_factory=list)
    failed_items: List[Tuple[str, str]] = field(default_factory=list)
    total_items: int = 0
    current_item: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ProcessorConfig:
    """Configuration for content processors.

    Attributes:
        use_vision_api: Enable Claude Vision API for image analysis
        extract_colors: Extract color palettes from images
        extract_typography: Extract typography information
        extract_layout: Extract layout structure
        max_file_size_mb: Maximum file size to process (in MB)
        timeout_seconds: Processing timeout in seconds
        output_dir: Directory to store processing results
        session_file: Path to session state file
    """

    use_vision_api: bool = True
    extract_colors: bool = True
    extract_typography: bool = True
    extract_layout: bool = True
    max_file_size_mb: int = 50
    timeout_seconds: int = 300
    output_dir: Path = field(default_factory=lambda: Path("discovery_output"))
    session_file: Path = field(default_factory=lambda: Path("discovery_session.json"))
