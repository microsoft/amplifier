"""File organization - saves pages in domain-based directory structure."""

import logging
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

# Add parent directory to path to import amplifier modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from amplifier.utils.file_io import write_text_with_retry  # type: ignore

    def write_file(path: Path, content: str, encoding: str = "utf-8") -> None:
        """Write file using amplifier utilities."""
        write_text_with_retry(content, path)

except ImportError:

    def write_file(path: Path, content: str, encoding: str = "utf-8") -> None:
        """Fallback write function with retry logic."""
        max_retries = 3
        retry_delay = 0.5

        for attempt in range(max_retries):
            try:
                with open(path, "w", encoding=encoding) as f:
                    f.write(content)
                return
            except OSError as e:
                if e.errno == 5 and attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise


logger = logging.getLogger(__name__)


def save_page(url: str, content: str, base_dir: Path) -> Path:
    """Save markdown content to domain-organized directory.

    Args:
        url: Original URL of the page
        content: Markdown content to save
        base_dir: Base directory for saving (e.g., sites/)

    Returns:
        Path to saved file
    """
    # Get domain directory
    domain_dir = get_domain_dir(url, base_dir)

    # Generate filename from URL
    filename = url_to_filename(url)

    # Full path for the file
    file_path = domain_dir / filename

    # Ensure directory exists
    domain_dir.mkdir(parents=True, exist_ok=True)

    # Save the file
    write_file(file_path, content)

    logger.info(f"Saved {url} to {file_path}")
    return file_path


def get_domain_dir(url: str, base_dir: Path) -> Path:
    """Get domain-based directory for a URL.

    Args:
        url: URL to extract domain from
        base_dir: Base directory for sites

    Returns:
        Path to domain directory
    """
    parsed = urlparse(url)
    domain = parsed.netloc or "unknown"

    # Clean domain for filesystem
    # Remove www. prefix if present
    if domain.startswith("www."):
        domain = domain[4:]

    # Replace problematic characters
    domain = domain.replace(":", "_")

    return base_dir / domain


def url_to_filename(url: str) -> str:
    """Convert URL to safe filename.

    Args:
        url: URL to convert

    Returns:
        Safe filename with .md extension
    """
    parsed = urlparse(url)

    # Start with the path
    if parsed.path and parsed.path != "/":
        # Remove leading/trailing slashes
        path = parsed.path.strip("/")
        # Replace slashes with underscores
        filename = path.replace("/", "_")
    else:
        filename = "index"

    # Add query string info if present
    if parsed.query:
        # Take first 20 chars of query to avoid too long filenames
        query_part = parsed.query[:20].replace("&", "_").replace("=", "_")
        filename = f"{filename}_{query_part}"

    # Clean filename for filesystem
    # Remove or replace problematic characters
    filename = re.sub(r'[<>:"|?*]', "_", filename)

    # Remove any file extension and add .md
    if "." in filename:
        filename = filename.rsplit(".", 1)[0]

    # Limit length to avoid filesystem issues
    if len(filename) > 100:
        filename = filename[:100]

    # Ensure we have a valid filename
    if not filename or filename == "_":
        filename = "page"

    return f"{filename}.md"
