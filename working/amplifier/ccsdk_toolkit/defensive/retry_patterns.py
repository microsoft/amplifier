"""
Retry patterns for AI operations with error feedback.

Implements intelligent retry mechanisms that learn from failures.
"""

import asyncio
import logging
import random
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


async def retry_with_feedback(
    func: Callable,
    prompt: str,
    max_retries: int = 2,
    base_delay: float = 1.0,
    provide_feedback: bool = True,
) -> Any:
    """
    Retry AI operations with error correction feedback.

    On failure, provides specific feedback about what went wrong
    and what format is expected.

    Args:
        func: Async function to retry (typically session.query)
        prompt: Original prompt to send
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
        provide_feedback: Whether to append error feedback on retry

    Returns:
        Result from successful function call, or None if all retries fail
    """
    last_error = None
    current_prompt = prompt

    for attempt in range(max_retries + 1):
        try:
            # Add delay with exponential backoff and jitter (except first attempt)
            if attempt > 0:
                delay = base_delay * (2 ** (attempt - 1))
                # Add jitter to prevent thundering herd
                jitter = random.uniform(0, delay * 0.1)
                await asyncio.sleep(delay + jitter)

                if provide_feedback and last_error:
                    # Enhance prompt with error feedback
                    feedback = _create_error_feedback(last_error, attempt)
                    current_prompt = f"{prompt}\n\n{feedback}"

            # Try the operation
            result = await func(current_prompt)

            # If we got a result, return it
            if result is not None:
                return result

            # Result was None, treat as failure
            last_error = "Empty or null response received"

        except TimeoutError as e:
            last_error = f"Operation timed out: {e}"
            logger.warning(f"Attempt {attempt + 1}/{max_retries + 1} failed: {last_error}")

        except Exception as e:
            last_error = str(e)
            logger.warning(f"Attempt {attempt + 1}/{max_retries + 1} failed: {last_error}")

    # All retries exhausted
    logger.error(f"All {max_retries + 1} attempts failed. Last error: {last_error}")
    return None


def _create_error_feedback(error: str, attempt: int) -> str:
    """
    Create helpful feedback for the AI based on the error.

    Args:
        error: Error message from previous attempt
        attempt: Current attempt number

    Returns:
        Feedback message to append to prompt
    """
    feedback_parts = [
        f"IMPORTANT: Attempt {attempt} failed with error: {error}",
        "Please ensure your response follows the exact format requested.",
    ]

    # Add specific guidance based on error type
    error_lower = error.lower()

    if "json" in error_lower or "parse" in error_lower:
        feedback_parts.extend(
            [
                "Your response MUST be valid JSON only.",
                "Do NOT include any explanatory text, markdown formatting, or preambles.",
                "Start directly with [ or { and end with ] or }.",
            ]
        )

    elif "timeout" in error_lower:
        feedback_parts.extend(
            [
                "Please provide a more concise response.",
                "Focus only on the essential information requested.",
            ]
        )

    elif "empty" in error_lower or "null" in error_lower or "none" in error_lower:
        feedback_parts.extend(
            [
                "Your previous response was empty or could not be processed.",
                "Please provide the actual content requested.",
            ]
        )

    return "\n".join(feedback_parts)
