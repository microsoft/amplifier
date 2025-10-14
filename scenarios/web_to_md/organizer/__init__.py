"""Organizer module - Manages file organization by domain."""

from .core import get_domain_dir
from .core import save_page

__all__ = ["save_page", "get_domain_dir"]
