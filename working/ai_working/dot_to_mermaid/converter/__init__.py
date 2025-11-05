"""
Converter Brick - Transforms DOT graphs to Mermaid format.

Contract:
  Input: DotGraph object
  Output: Mermaid diagram string
  Method: Deterministic pattern-based conversion
"""

from .deterministic import convert_deterministic

__all__ = ["convert_deterministic"]
