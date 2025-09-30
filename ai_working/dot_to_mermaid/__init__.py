"""
DOT to Mermaid Converter Module.

A self-contained tool for converting DOT graph files to Mermaid diagram format
using deterministic pattern matching.
"""

from .converter import convert_deterministic
from .models import ConversionResult
from .models import DotGraph
from .models import SessionState
from .parser import parse_dot_file
from .parser import parse_dot_string
from .session import SessionManager

__version__ = "1.0.0"
__all__ = [
    "parse_dot_file",
    "parse_dot_string",
    "convert_deterministic",
    "SessionManager",
    "DotGraph",
    "ConversionResult",
    "SessionState",
]
