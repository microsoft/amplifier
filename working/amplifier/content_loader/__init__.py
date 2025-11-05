"""
Content Loader Module

A self-contained module for loading content from configured directories.
See README.md for full contract specification.

Basic Usage:
    >>> from amplifier.content_loader import ContentLoader, ContentItem
    >>> loader = ContentLoader()
    >>> for item in loader.load_all():
    ...     print(f"{item.title}: {item.content_id}")
"""

from .loader import ContentLoader
from .models import ContentItem

__all__ = ["ContentLoader", "ContentItem"]
