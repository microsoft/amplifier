"""Content loader implementation"""

import hashlib
import json
import logging
import re
from collections.abc import Iterator
from pathlib import Path

from .models import ContentItem

logger = logging.getLogger(__name__)


class ContentLoader:
    """Loads content from configured directories.

    This class scans directories specified in AMPLIFIER_CONTENT_DIRS
    environment variable and loads content from supported file formats.

    Supported formats:
        - .md (Markdown)
        - .txt (Plain text)
        - .json (JSON with 'content' field)

    Example:
        >>> loader = ContentLoader()
        >>> for item in loader.load_all():
        ...     print(f"{item.title}: {item.content_id}")
    """

    SUPPORTED_EXTENSIONS = {".md", ".txt", ".json"}

    def __init__(self, content_dirs: list[str] | None = None):
        """Initialize content loader.

        Args:
            content_dirs: Optional list of directories to scan.
                         If None, uses PathConfig to get configured directories.
        """
        if content_dirs is None:
            # Use PathConfig which properly loads from .env file
            from amplifier.config.paths import paths

            self.content_dirs = [p for p in paths.content_dirs if p.exists()]
        else:
            self.content_dirs = [Path(d).resolve() for d in content_dirs if Path(d).exists()]

        if not self.content_dirs:
            logger.warning("No valid content directories configured")

    def _generate_content_id(self, file_path: Path) -> str:
        """Generate unique ID from file path.

        Uses SHA256 hash of the absolute path for consistency.
        """
        path_str = str(file_path.resolve())
        return hashlib.sha256(path_str.encode()).hexdigest()[:16]

    def _extract_title(self, content: str, file_path: Path, format: str) -> str:
        """Extract title from content or use filename.

        For markdown, looks for first H1 heading.
        For others, uses filename without extension.
        """
        if format == "md":
            # Look for first H1 heading
            match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            if match:
                return match.group(1).strip()

        # Fallback to filename without extension
        return file_path.stem.replace("_", " ").replace("-", " ").title()

    def _load_file(self, file_path: Path) -> ContentItem | None:
        """Load a single file and return ContentItem.

        Returns None if file cannot be loaded.
        """
        try:
            # Determine format from extension
            ext = file_path.suffix.lower()
            if ext not in self.SUPPORTED_EXTENSIONS:
                return None

            format = ext[1:]  # Remove leading dot

            # Read content based on format
            if format == "json":
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)

                # Extract content from JSON
                if isinstance(data, dict):
                    content = data.get("content", "")
                    title = data.get("title", "")
                    metadata = {k: v for k, v in data.items() if k not in ("content", "title")}
                else:
                    content = json.dumps(data, indent=2)
                    title = ""
                    metadata = {}
            else:
                # Plain text or markdown
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                title = ""
                metadata = {}

            # Generate content ID
            content_id = self._generate_content_id(file_path)

            # Extract or generate title if needed
            if not title:
                title = self._extract_title(content, file_path, format)

            return ContentItem(
                content_id=content_id,
                title=title,
                content=content,
                source_path=str(file_path),
                format=format,
                metadata=metadata,
            )

        except Exception as e:
            logger.warning(f"Failed to load {file_path}: {e}")
            return None

    def load_all(self, quiet: bool = False) -> Iterator[ContentItem]:
        """Load all content from configured directories.

        Args:
            quiet: If True, suppress progress output to stdout.

        Yields ContentItem objects for each successfully loaded file.
        Skips files that cannot be loaded and logs warnings.
        """
        import sys

        total_files_found = 0
        total_files_loaded = 0

        for content_dir in self.content_dirs:
            if not quiet:
                logger.info(f"Scanning directory: {content_dir}")

            # First, count total files to scan for better progress indication
            dir_files_found = 0

            # Walk directory tree
            for file_path in content_dir.rglob("*"):
                if not file_path.is_file():
                    continue

                if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                    continue

                dir_files_found += 1
                total_files_found += 1

                # Update progress during scanning
                if not quiet and dir_files_found % 10 == 0:  # Update every 10 files
                    sys.stdout.write(f"\rScanning: {total_files_found} files found...")
                    sys.stdout.flush()

                item = self._load_file(file_path)
                if item:
                    total_files_loaded += 1
                    yield item

            # Clear the progress line
            if not quiet and dir_files_found > 0:
                sys.stdout.write(
                    f"\rScanned {content_dir}: {dir_files_found} files found, {total_files_loaded} loaded\n"
                )
                sys.stdout.flush()

    def search(self, query: str, case_sensitive: bool = False) -> Iterator[ContentItem]:
        """Search for content containing the query string.

        Args:
            query: Search string to find in content or title
            case_sensitive: Whether search should be case-sensitive

        Yields:
            ContentItem objects matching the search query
        """
        if not case_sensitive:
            query = query.lower()

        for item in self.load_all(quiet=True):
            search_content = item.content if case_sensitive else item.content.lower()
            search_title = item.title if case_sensitive else item.title.lower()

            if query in search_content or query in search_title:
                yield item

    def get_by_id(self, content_id: str) -> ContentItem | None:
        """Get a specific content item by ID.

        Args:
            content_id: The content ID to search for

        Returns:
            ContentItem if found, None otherwise
        """
        for item in self.load_all(quiet=True):
            if item.content_id == content_id:
                return item
        return None
