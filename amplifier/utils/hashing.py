"""Hashing utilities for deterministic ID generation.

Provides SHA256 and SHA1 hashing functions for bytes and strings.
"""

import hashlib
from typing import Union


def sha256_digest(data: Union[str, bytes]) -> str:
    """Generate SHA256 hex digest for input data.

    Args:
        data: String or bytes to hash

    Returns:
        Hex digest string
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def sha1_digest(data: Union[str, bytes]) -> str:
    """Generate SHA1 hex digest for input data.

    Args:
        data: String or bytes to hash

    Returns:
        Hex digest string
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha1(data).hexdigest()


def digest_bytes(data: bytes, algorithm: str = "sha256") -> str:
    """Generate hex digest for bytes using specified algorithm.

    Args:
        data: Bytes to hash
        algorithm: Hash algorithm name ('sha256', 'sha1', etc.)

    Returns:
        Hex digest string
    """
    hasher = hashlib.new(algorithm)
    hasher.update(data)
    return hasher.hexdigest()


def deterministic_id(components: list[str], separator: str = "|") -> str:
    """Generate deterministic ID from sorted components.

    Args:
        components: List of string components
        separator: Separator between components

    Returns:
        SHA1 hex digest of joined components
    """
    # Sort components for determinism
    sorted_components = sorted(components)
    combined = separator.join(sorted_components)
    return sha1_digest(combined)
