"""Simple network utilities for Amplifier CLI v3."""

import asyncio
import hashlib
from dataclasses import dataclass
from typing import Any

import httpx


class NetworkError(Exception):
    """Network operation failed."""


class MaxRetriesExceededError(NetworkError):
    """Maximum retries exceeded for network operation."""


class HashVerificationError(NetworkError):
    """Hash verification failed for downloaded content."""


@dataclass
class NetworkConfig:
    """Configuration for network operations."""

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    jitter_factor: float = 0.1
    timeout: float = 30.0


async def fetch_with_retry(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
    **kwargs: Any,
) -> bytes:
    """Download content with simple retry logic.

    Args:
        url: URL to download from
        headers: Additional headers to include in request
        timeout: Timeout in seconds for each request (default: 30.0)
        **kwargs: Additional arguments to pass to httpx.get

    Returns:
        Downloaded content as bytes

    Raises:
        NetworkError: If download fails after retries
    """
    last_error: Exception | None = None

    for attempt in range(3):  # Simple 3 retries
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, headers=headers or {}, **kwargs)
                response.raise_for_status()
                return response.content

        except httpx.TimeoutException as e:
            last_error = e
        except httpx.ConnectError as e:
            last_error = e
        except httpx.HTTPStatusError as e:
            if e.response.status_code >= 500:
                # Server errors are retryable
                last_error = e
            else:
                # Client errors are not retryable
                raise NetworkError(f"HTTP {e.response.status_code} error for {url}")
        except Exception as e:
            last_error = e

        # Simple sleep between retries (no jitter, no exponential backoff)
        if attempt < 2:
            await asyncio.sleep(1.0)

    # All retries exhausted
    raise NetworkError(f"Failed to download {url} after 3 attempts: {str(last_error)}")


async def download_to_file(
    url: str,
    filepath: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
    **kwargs: Any,
) -> None:
    """Download content to file.

    Args:
        url: URL to download from
        filepath: Path to save downloaded content
        headers: Additional headers to include in request
        timeout: Timeout in seconds for each request
        **kwargs: Additional arguments to pass to httpx.get

    Raises:
        NetworkError: If download fails
    """
    from pathlib import Path

    # Download content
    content = await fetch_with_retry(url, headers=headers, timeout=timeout, **kwargs)

    # Write to file
    file_path = Path(filepath)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(content)


async def check_connectivity(url: str = "https://www.google.com", timeout: float = 5.0) -> bool:
    """Check internet connectivity.

    Args:
        url: URL to check connectivity against
        timeout: Timeout in seconds

    Returns:
        True if connectivity check succeeds, False otherwise
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.head(url)
            return response.status_code < 500
    except Exception:
        return False


def calculate_hash(content: bytes, algorithm: str = "sha256") -> str:
    """Calculate hash of content.

    Args:
        content: Content to hash
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        Hex digest of the hash
    """
    hasher = hashlib.new(algorithm)
    hasher.update(content)
    return hasher.hexdigest()


def verify_hash(content: bytes, expected_hash: str, algorithm: str = "sha256") -> bool:
    """Verify content matches expected hash.

    Args:
        content: Content to verify
        expected_hash: Expected hash value
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        True if hash matches, False otherwise
    """
    actual_hash = calculate_hash(content, algorithm)
    return actual_hash == expected_hash


async def download_with_retry(
    url: str,
    *,
    config: NetworkConfig | None = None,
    headers: dict[str, str] | None = None,
    **kwargs: Any,
) -> bytes:
    """Download content with retry logic based on NetworkConfig.

    Args:
        url: URL to download from
        config: Network configuration for retry behavior
        headers: Additional headers to include in request
        **kwargs: Additional arguments to pass to httpx

    Returns:
        Downloaded content as bytes

    Raises:
        MaxRetriesExceededError: If all retries are exhausted
    """
    config = config or NetworkConfig()
    last_error: Exception | None = None

    for attempt in range(config.max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=config.timeout) as client:
                response = await client.get(url, headers=headers or {}, **kwargs)
                response.raise_for_status()
                return response.content

        except httpx.TimeoutException as e:
            last_error = e
        except httpx.ConnectError as e:
            last_error = e
        except httpx.HTTPStatusError as e:
            if e.response.status_code >= 500:
                # Server errors are retryable
                last_error = e
            else:
                # Client errors are not retryable
                raise NetworkError(f"HTTP {e.response.status_code} error for {url}")
        except Exception as e:
            last_error = e

        # Calculate backoff delay
        if attempt < config.max_retries:
            import random

            delay = min(config.base_delay * (2**attempt), config.max_delay)
            if config.jitter_factor > 0:
                jitter_amount = delay * config.jitter_factor * (2 * random.random() - 1)
                delay = max(0.1, delay + jitter_amount)

            await asyncio.sleep(delay)

    # All retries exhausted
    raise MaxRetriesExceededError(
        f"Failed to download {url} after {config.max_retries + 1} attempts: {str(last_error)}"
    )


# Export public interface
__all__ = [
    "NetworkError",
    "MaxRetriesExceededError",
    "HashVerificationError",
    "NetworkConfig",
    "fetch_with_retry",
    "download_to_file",
    "check_connectivity",
    "calculate_hash",
    "verify_hash",
    "download_with_retry",
]
