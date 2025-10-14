"""Core fetcher functionality - downloads web pages with retry logic."""

import logging
import time
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)


def fetch_page(url: str, timeout: int = 30, max_retries: int = 3) -> tuple[str, dict[str, Any]]:
    """Fetch a web page and extract metadata.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts

    Returns:
        Tuple of (html_content, metadata_dict)

    Raises:
        httpx.HTTPError: If all fetch attempts fail
    """
    headers = {"User-Agent": "Mozilla/5.0 (compatible; WebToMd/1.0; +https://github.com/amplifier/web_to_md)"}

    retry_delay = 1
    last_error = None

    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching {url} (attempt {attempt + 1}/{max_retries})")

            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()

                # Extract metadata
                final_url = str(response.url)
                parsed = urlparse(final_url)
                metadata = {
                    "url": final_url,
                    "original_url": url,
                    "status_code": response.status_code,
                    "content_type": response.headers.get("content-type", ""),
                    "content_length": response.headers.get("content-length"),
                    "domain": parsed.netloc,
                    "path": parsed.path,
                }

                # Try to extract title from headers if present
                if "content-disposition" in response.headers:
                    metadata["content_disposition"] = response.headers["content-disposition"]

                logger.info(f"Successfully fetched {url} ({len(response.text)} bytes)")
                return response.text, metadata

        except httpx.HTTPError as e:
            last_error = e
            logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")

            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff

    # All retries failed
    error_msg = f"Failed to fetch {url} after {max_retries} attempts: {last_error}"
    logger.error(error_msg)
    raise httpx.HTTPError(error_msg)
