"""
LLM response parsing with defensive handling.

Extracts JSON from any LLM response format without raising exceptions.
"""

import json
import logging
import re
from typing import Union

logger = logging.getLogger(__name__)


def parse_llm_json(
    response: str, default: Union[dict, list, None] = None, verbose: bool = False
) -> Union[dict, list, None]:
    """
    Extract JSON from any LLM response format.

    Handles:
    - Plain JSON
    - Markdown-wrapped JSON (```json blocks)
    - JSON with text preambles
    - Common formatting issues

    Returns default value on failure (doesn't raise exceptions).

    Args:
        response: Raw LLM response text
        default: Value to return if parsing fails (default: None)
        verbose: If True, log debugging output for failed parsing attempts

    Returns:
        Parsed JSON as dict/list, or default if parsing fails
    """
    if not response or not isinstance(response, str):
        if verbose:
            logger.debug(f"Empty or invalid response type: {type(response)}")
        return default

    # Try 1: Direct JSON parsing
    try:
        result = json.loads(response)
        if verbose:
            logger.debug("Successfully parsed JSON directly")
        return result
    except (json.JSONDecodeError, TypeError) as e:
        if verbose:
            logger.debug(f"Direct JSON parsing failed: {e}")
        pass

    # Try 2: Extract from markdown code blocks
    # Match ```json ... ``` or ``` ... ```
    markdown_patterns = [r"```json\s*\n?(.*?)```", r"```\s*\n?(.*?)```"]

    for pattern in markdown_patterns:
        matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
        for match in matches:
            try:
                result = json.loads(match)
                if verbose:
                    logger.debug("Successfully extracted JSON from markdown block")
                return result
            except (json.JSONDecodeError, TypeError) as e:
                if verbose:
                    logger.debug(f"Failed to parse markdown-extracted JSON: {e}")
                continue

    # Try 3: Find JSON-like structures in text
    # Look for {...} or [...] patterns
    json_patterns = [
        r"(\{[^{}]*\{[^{}]*\}[^{}]*\})",  # Nested objects
        r"(\[[^\[\]]*\[[^\[\]]*\][^\[\]]*\])",  # Nested arrays
        r"(\{[^{}]+\})",  # Simple objects
        r"(\[[^\[\]]+\])",  # Simple arrays
    ]

    for pattern in json_patterns:
        matches = re.findall(pattern, response, re.DOTALL)
        for match in matches:
            try:
                result = json.loads(match)
                # Prefer arrays over single objects for typical AI responses
                if isinstance(result, dict | list):
                    if verbose:
                        logger.debug("Successfully extracted JSON structure from text")
                    return result
            except (json.JSONDecodeError, TypeError) as e:
                if verbose:
                    logger.debug(f"Failed to parse JSON structure: {e}")
                continue

    # Try 4: Extract after common preambles
    # Remove common AI response prefixes
    preamble_patterns = [
        r"^.*?(?:here\'s|here is|below is|following is).*?:\s*",
        r"^.*?(?:i\'ll|i will|let me).*?:\s*",
        r"^[^{\[]*",  # Remove everything before first { or [
    ]

    for pattern in preamble_patterns:
        cleaned = re.sub(pattern, "", response, flags=re.IGNORECASE | re.DOTALL)
        if cleaned != response:  # Something was removed
            try:
                result = json.loads(cleaned)
                if verbose:
                    logger.debug("Successfully parsed JSON after removing preamble")
                return result
            except (json.JSONDecodeError, TypeError) as e:
                if verbose:
                    logger.debug(f"Failed after preamble removal: {e}")
                continue

    # Try 5: Fix common JSON formatting issues
    # This is a last resort for slightly malformed JSON
    fixes = [
        (r",\s*}", "}"),  # Remove trailing commas before }
        (r",\s*]", "]"),  # Remove trailing commas before ]
        (r"(\w+):", r'"\1":'),  # Add quotes to unquoted keys
        (r":\s*\'([^\']+)\'", r': "\1"'),  # Convert single to double quotes
    ]

    cleaned = response
    for pattern, replacement in fixes:
        cleaned = re.sub(pattern, replacement, cleaned)

    if cleaned != response:
        try:
            result = json.loads(cleaned)
            if verbose:
                logger.debug("Successfully parsed JSON after fixing formatting issues")
            return result
        except (json.JSONDecodeError, TypeError) as e:
            if verbose:
                logger.debug(f"Failed after formatting fixes: {e}")
            pass

    # All attempts failed
    if verbose:
        logger.debug(f"All JSON parsing attempts failed. Response (first 500 chars): {response[:500]}")
    return default
