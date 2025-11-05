"""
Session Manager Brick - Tracks conversion progress and enables resume.

Contract:
  Purpose: Save progress after every file for interruption recovery
  Persistence: JSON file with processed files and results
  Resume: Skip already processed files on restart
"""

from .manager import SessionManager

__all__ = ["SessionManager"]
