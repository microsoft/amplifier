"""
LLM response parsing with defensive handling.

Extracts JSON from any LLM response format without raising exceptions.
"""

import json
import logging
import re
from typing import Union

logger = logging.getLogger(__name__)


def parse_llm_json(response: str) -> Union[dict, list] | None:
    """
    Extract JSON from any LLM response format.

    Handles:
    - Plain JSON
    - Markdown-wrapped JSON (```json blocks)
    - JSON with text preambles
    - Common formatting issues

    Returns None on failure (doesn't raise exceptions).

    Args:
        response: Raw LLM response text

    Returns:
        Parsed JSON as dict/list, or None if parsing fails
    """
    if not response or not isinstance(response, str):
        return None

    # Try 1: Direct JSON parsing
    try:
        return json.loads(response)
    except (json.JSONDecodeError, TypeError):
        pass

    # Try 2: Extract from markdown code blocks
    # Match ```json ... ``` or ``` ... ```
    markdown_patterns = [r"```json\s*\n?(.*?)```", r"```\s*\n?(.*?)```"]

    for pattern in markdown_patterns:
        matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
        for match in matches:
            try:
                return json.loads(match)
            except (json.JSONDecodeError, TypeError):
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
                    return result
            except (json.JSONDecodeError, TypeError):
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
                return json.loads(cleaned)
            except (json.JSONDecodeError, TypeError):
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
            return json.loads(cleaned)
        except (json.JSONDecodeError, TypeError):
            pass

    # All attempts failed
    logger.debug(f"Failed to parse JSON from response (first 500 chars): {response[:500]}")
    return None
