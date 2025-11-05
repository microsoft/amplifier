"""Token counting and truncation utilities using tiktoken.

This module provides utilities for accurately counting tokens and truncating text
to fit within token limits for LLM processing.
"""

import tiktoken


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """Count the number of tokens in text.

    Args:
        text: The text to count tokens for
        model: The tiktoken encoding model to use (default: cl100k_base for GPT-4/Claude)

    Returns:
        Number of tokens in the text
    """
    try:
        encoding = tiktoken.get_encoding(model)
    except KeyError:
        # Fallback to cl100k_base if model not found
        encoding = tiktoken.get_encoding("cl100k_base")

    return len(encoding.encode(text))


def truncate_to_tokens(text: str, max_tokens: int = 80000, model: str = "cl100k_base") -> tuple[str, int, int]:
    """Truncate text to fit within a token limit.

    Args:
        text: The text to potentially truncate
        max_tokens: Maximum number of tokens allowed (default: 80000)
        model: The tiktoken encoding model to use

    Returns:
        Tuple of (truncated_text, original_token_count, final_token_count)
    """
    try:
        encoding = tiktoken.get_encoding(model)
    except KeyError:
        # Fallback to cl100k_base if model not found
        encoding = tiktoken.get_encoding("cl100k_base")

    # Encode the text to tokens
    tokens = encoding.encode(text)
    original_count = len(tokens)

    # If within limit, return as-is
    if original_count <= max_tokens:
        return text, original_count, original_count

    # Truncate tokens and decode back to text
    truncated_tokens = tokens[:max_tokens]
    truncated_text = encoding.decode(truncated_tokens)
    final_count = len(truncated_tokens)

    return truncated_text, original_count, final_count
