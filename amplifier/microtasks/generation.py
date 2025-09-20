"""
Utilities for generating multi-file outputs from LLM responses.

Protocol: The LLM must emit files as fenced blocks using this exact format:

```file:relative/path.ext
<file contents>
```

Multiple files can be emitted by repeating the fence.
"""

from __future__ import annotations

import re
from pathlib import Path

FILE_FENCE_RE = re.compile(r"```[^\n`]*file:(?P<path>[^\n]+)\n(?P<body>.*?)```", re.DOTALL | re.IGNORECASE)


def parse_file_fences(text: str, base_dir: Path) -> dict[Path, str]:
    """Parse LLM output into a mapping of file path -> contents.

    Args:
        text: The raw LLM output string containing one or more file blocks
        base_dir: The directory to resolve relative paths against

    Returns:
        Dict of absolute Path to file content
    """
    files: dict[Path, str] = {}
    for m in FILE_FENCE_RE.finditer(text):
        rel = m.group("path").strip()
        body = m.group("body")
        # Normalize line endings
        body = body.replace("\r\n", "\n").replace("\r", "\n")
        path = (base_dir / rel).resolve()
        if not str(path).startswith(str(base_dir.resolve())):
            # Prevent path traversal
            raise ValueError(f"Illegal path outside base: {rel}")
        files[path] = body
    return files
