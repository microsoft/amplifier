"""
DOT Parser Brick - Extracts structure from DOT files.

Contract:
  Input: DOT file path or content string
  Output: DotGraph object with parsed structure
  Failures: Returns DotGraph with raw_source only if parsing fails
"""

from .dot_parser import parse_dot_file
from .dot_parser import parse_dot_string

__all__ = ["parse_dot_file", "parse_dot_string"]
