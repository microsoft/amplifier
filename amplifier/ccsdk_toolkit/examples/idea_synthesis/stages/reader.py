"""Reader stage - loads markdown files from disk."""

from collections.abc import Generator
from pathlib import Path

from rich.console import Console
from rich.progress import Progress
from rich.progress import SpinnerColumn
from rich.progress import TextColumn

from ..models import SourceFile


class ReaderStage:
    """Reads markdown files from a directory."""

    def __init__(self, console: Console | None = None):
        """Initialize the reader stage.

        Args:
            console: Rich console for output
        """
        self.console = console or Console()

    def read_files(
        self, directory: Path, pattern: str = "*.md", recursive: bool = True, limit: int | None = None, skip: int = 0
    ) -> Generator[SourceFile, None, None]:
        """Read markdown files from directory.

        Args:
            directory: Directory to read from
            pattern: Glob pattern for files
            recursive: Whether to search recursively
            limit: Maximum files to read
            skip: Number of files to skip (for resume)

        Yields:
            SourceFile objects
        """
        # Find all matching files
        if recursive:
            files = sorted(directory.rglob(pattern))
        else:
            files = sorted(directory.glob(pattern))

        # Apply skip and limit
        if skip > 0:
            files = files[skip:]
        if limit:
            files = files[:limit]

        total = len(files)

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=self.console
        ) as progress:
            task = progress.add_task(f"Reading {total} files...", total=total)

            for file_path in files:
                try:
                    content = file_path.read_text(encoding="utf-8")

                    # Extract basic metadata
                    metadata = {"size": len(content), "lines": content.count("\n"), "name": file_path.name}

                    yield SourceFile(path=file_path, content=content, metadata=metadata)

                    progress.update(task, description=f"Read {file_path.name}")

                except Exception as e:
                    self.console.print(f"[red]Error reading {file_path}: {e}[/red]")
                    continue

    def count_files(self, directory: Path, pattern: str = "*.md", recursive: bool = True) -> int:
        """Count matching files without reading them.

        Args:
            directory: Directory to search
            pattern: Glob pattern
            recursive: Whether to search recursively

        Returns:
            Number of matching files
        """
        if recursive:
            return len(list(directory.rglob(pattern)))
        return len(list(directory.glob(pattern)))
