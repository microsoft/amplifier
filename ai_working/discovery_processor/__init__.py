"""Discovery Content Processor - AI-powered content understanding for Discovery canvas."""

from .core import BaseProcessor, ContentProcessor
from .models import ContentItem, ContentType, ProcessingResult, ProcessingStatus, ProcessorConfig, SessionState
from .processors import CanvasDrawingProcessor, DocumentProcessor, ImageProcessor, URLProcessor
from .session import SessionManager

__version__ = "0.1.0"

__all__ = [
    # Core
    "ContentProcessor",
    "BaseProcessor",
    # Models
    "ContentItem",
    "ContentType",
    "ProcessingResult",
    "ProcessingStatus",
    "ProcessorConfig",
    "SessionState",
    # Processors
    "ImageProcessor",
    "URLProcessor",
    "DocumentProcessor",
    "CanvasDrawingProcessor",
    # Session
    "SessionManager",
]
