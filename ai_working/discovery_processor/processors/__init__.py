"""Content processors for Discovery."""

from .canvas import CanvasDrawingProcessor
from .document import DocumentProcessor
from .image import ImageProcessor
from .url import URLProcessor

__all__ = ["ImageProcessor", "URLProcessor", "DocumentProcessor", "CanvasDrawingProcessor"]
