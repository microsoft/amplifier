"""Image processing - downloads images from HTML content."""

import hashlib
import logging
from pathlib import Path
from urllib.parse import urljoin
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def process_images(html: str, base_url: str, output_dir: Path) -> list[tuple[str, Path]]:
    """Extract and download images from HTML.

    Args:
        html: HTML content to parse
        base_url: Base URL for resolving relative image URLs
        output_dir: Directory to save downloaded images

    Returns:
        List of (original_url, local_path) tuples
    """
    soup = BeautifulSoup(html, "html.parser")
    images = soup.find_all("img")

    if not images:
        logger.info("No images found in HTML")
        return []

    # Create images directory
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    downloaded = []

    for img in images:
        src = img.get("src")
        if not src:
            continue

        # Convert to string (BeautifulSoup may return list or other types)
        src_str = str(src) if not isinstance(src, str) else src

        # Resolve relative URLs
        absolute_url = urljoin(base_url, src_str)

        try:
            # Download the image
            local_path = download_image(absolute_url, images_dir)
            if local_path:
                downloaded.append((absolute_url, local_path))
                logger.info(f"Downloaded image: {absolute_url} -> {local_path.name}")
        except Exception as e:
            logger.warning(f"Failed to download image {absolute_url}: {e}")

    logger.info(f"Downloaded {len(downloaded)} of {len(images)} images")
    return downloaded


def download_image(url: str, images_dir: Path, timeout: int = 10) -> Path | None:
    """Download a single image.

    Args:
        url: Image URL to download
        images_dir: Directory to save image
        timeout: Download timeout in seconds

    Returns:
        Path to downloaded image or None if failed
    """
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()

            # Generate filename from URL hash to avoid collisions
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]

            # Try to get extension from URL or content-type
            parsed = urlparse(url)
            path_parts = parsed.path.split("/")
            if path_parts and "." in path_parts[-1]:
                ext = path_parts[-1].split(".")[-1].lower()
                # Validate common image extensions
                if ext not in ["jpg", "jpeg", "png", "gif", "svg", "webp", "bmp"]:
                    ext = "jpg"  # Default to jpg
            else:
                # Try to infer from content-type
                content_type = response.headers.get("content-type", "")
                if "png" in content_type:
                    ext = "png"
                elif "gif" in content_type:
                    ext = "gif"
                elif "svg" in content_type:
                    ext = "svg"
                elif "webp" in content_type:
                    ext = "webp"
                else:
                    ext = "jpg"  # Default

            filename = f"img_{url_hash}.{ext}"
            local_path = images_dir / filename

            # Save the image
            with open(local_path, "wb") as f:
                f.write(response.content)

            return local_path

    except Exception as e:
        logger.error(f"Error downloading image {url}: {e}")
        return None
