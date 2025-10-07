"""Source Reviewer Module

Verifies factual accuracy and source attribution in blog posts.
"""

from .core import SourceReview
from .core import SourceReviewer

__all__ = ["SourceReviewer", "SourceReview"]
