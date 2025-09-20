"""File reading module for handling various text formats."""

from pathlib import Path
from typing import Optional


def read_file(path: Path, encoding: str | None = None) -> str:
    """Read a file with automatic encoding detection.

    Args:
        path: Path to the file to read
        encoding: Optional encoding override

    Returns:
        File contents as string

    Raises:
        FileNotFoundError: If file doesn't exist
        UnicodeDecodeError: If file cannot be decoded
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise ValueError(f"Not a file: {path}")

    # Try encodings in order of likelihood
    encodings = [encoding] if encoding else ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

    last_error = None
    for enc in encodings:
        if enc is None:
            continue
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError as e:
            last_error = e
            continue

    # If all encodings failed
    if last_error is not None:
        raise UnicodeDecodeError(
            last_error.encoding,
            last_error.object,
            last_error.start,
            last_error.end,
            f"Could not decode file {path} with any common encoding",
        )
    # This shouldn't happen but handle it for type safety
    raise ValueError(f"Could not decode file {path} with any encoding")


__all__ = ["read_file"]
