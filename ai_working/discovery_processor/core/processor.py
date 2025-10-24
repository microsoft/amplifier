"""Base processor protocol for Discovery content understanding."""

from abc import ABC, abstractmethod
from typing import Protocol, Optional, List

from ..models import ContentItem, ProcessingResult, ProcessorConfig


class ContentProcessor(Protocol):
    """Protocol for content processors.

    Each processor implements this protocol to handle a specific
    content type (image, document, URL, canvas drawing).
    """

    @abstractmethod
    async def can_process(self, item: ContentItem) -> bool:
        """Check if this processor can handle the content item.

        Args:
            item: Content item to check

        Returns:
            True if this processor can handle the item
        """
        ...

    @abstractmethod
    async def process(self, item: ContentItem, config: ProcessorConfig) -> ProcessingResult:
        """Process the content item and extract insights.

        Args:
            item: Content item to process
            config: Processor configuration

        Returns:
            Processing result with analysis and insights
        """
        ...

    @abstractmethod
    def get_supported_types(self) -> List[str]:
        """Get list of MIME types or content types this processor supports.

        Returns:
            List of supported MIME types or content type strings
        """
        ...


class BaseProcessor(ABC):
    """Abstract base class for content processors.

    Provides common functionality for all processors.
    """

    def __init__(self, config: Optional[ProcessorConfig] = None):
        """Initialize processor with configuration.

        Args:
            config: Processor configuration (uses defaults if not provided)
        """
        self.config = config or ProcessorConfig()

    @abstractmethod
    async def can_process(self, item: ContentItem) -> bool:
        """Check if this processor can handle the content item."""
        pass

    @abstractmethod
    async def process(self, item: ContentItem, config: Optional[ProcessorConfig] = None) -> ProcessingResult:
        """Process the content item."""
        pass

    @abstractmethod
    def get_supported_types(self) -> List[str]:
        """Get supported content/MIME types."""
        pass

    def _validate_file_size(self, item: ContentItem) -> bool:
        """Validate that file size is within limits.

        Args:
            item: Content item to validate

        Returns:
            True if file size is acceptable
        """
        if item.size_bytes is None:
            return True

        max_bytes = self.config.max_file_size_mb * 1024 * 1024
        return item.size_bytes <= max_bytes

    def _is_image(self, item: ContentItem) -> bool:
        """Check if content item is an image.

        Args:
            item: Content item to check

        Returns:
            True if item is an image
        """
        if not item.mime_type:
            return False

        return item.mime_type.startswith("image/")

    def _is_document(self, item: ContentItem) -> bool:
        """Check if content item is a document.

        Args:
            item: Content item to check

        Returns:
            True if item is a document (PDF, Office, etc.)
        """
        if not item.mime_type:
            return False

        document_types = [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument",
            "application/msword",
            "application/vnd.ms-excel",
            "application/vnd.ms-powerpoint",
        ]

        return any(item.mime_type.startswith(doc_type) for doc_type in document_types)

    def _is_url(self, item: ContentItem) -> bool:
        """Check if content item is a URL.

        Args:
            item: Content item to check

        Returns:
            True if item is a URL
        """
        return item.source_path.startswith("http://") or item.source_path.startswith("https://")
