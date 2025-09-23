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


def extract_code_from_response(response: str, language: str = "python") -> str:
    """
    Extract code from LLM response, handling various response formats.

    Handles:
    - Plain code
    - Markdown-wrapped code blocks
    - Code with preambles/explanations
    - Multiple code blocks (returns concatenated)

    Args:
        response: Raw LLM response text
        language: Language hint for markdown blocks (default: "python")

    Returns:
        Extracted code without preambles or markdown formatting
    """
    if not response or not isinstance(response, str):
        return ""

    # First check if the entire response is already clean code
    # (starts with typical code patterns without preamble)
    code_start_patterns = [
        r"^(import |from |def |class |@|#!|'''|\"\"\")",
        r"^[a-zA-Z_][a-zA-Z0-9_]*\s*=",  # Variable assignment
    ]

    for pattern in code_start_patterns:
        if re.match(pattern, response.strip(), re.MULTILINE) and "```" not in response:
            # Response starts with code and has no markdown wrappers
            logger.debug("Response appears to be plain code")
            return response.strip()

    # Extract from markdown blocks
    markdown_patterns = [
        rf"```{language}\s*\n(.*?)\n```",
        r"```\w*\s*\n(.*?)\n```",  # Any language marker
        r"```\s*\n(.*?)\n```",  # No language marker
    ]

    extracted_blocks = []
    for pattern in markdown_patterns:
        matches = re.findall(pattern, response, re.DOTALL)
        if matches:
            extracted_blocks.extend(matches)
            logger.debug(f"Extracted {len(matches)} code blocks from markdown")

    if extracted_blocks:
        # Join multiple blocks with double newlines
        return "\n\n".join(block.strip() for block in extracted_blocks)

    # Look for code after common preambles
    # This handles cases like "I'll generate the code...\n\n[actual code]"
    preamble_end_patterns = [
        # Match preambles that end with a period and newline
        r"(?:I'll\s+(?:generate|create|write|implement)|Let\s+me\s+(?:generate|create|write|implement)|Here(?:'s|\s+is)\s+(?:the|a)).*?\.\s*\n+",
        # Match preambles that end with a colon and newline
        r"(?:I'll\s+(?:generate|create|write|implement)|Let\s+me\s+(?:generate|create|write|implement)|Here(?:'s|\s+is)\s+(?:the|a)).*?:\s*\n+",
        # Match preambles without punctuation (just newlines)
        r"(?:I'll\s+(?:generate|create|write|implement)|Let\s+me\s+(?:generate|create|write|implement)|Here(?:'s|\s+is)\s+(?:the|a)).*?\n\n+",
    ]

    for pattern in preamble_end_patterns:
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            # Get everything after the preamble
            code_start = match.end()
            potential_code = response[code_start:].strip()
            if potential_code:
                logger.debug("Extracted code after removing preamble")
                # Recursively process in case there are markdown blocks after preamble
                return extract_code_from_response(potential_code, language)

    # Check if there's code starting after any line (more aggressive)
    lines = response.split("\n")
    code_started = False
    code_lines = []

    for line in lines:
        # Check if this line looks like code
        if not code_started:
            for pattern in code_start_patterns:
                if re.match(pattern, line.strip()):
                    code_started = True
                    break

        if code_started:
            code_lines.append(line)

    if code_lines:
        logger.debug(f"Extracted {len(code_lines)} lines of apparent code")
        return "\n".join(code_lines)

    # Last resort: if nothing else worked, return the original
    # (might be code without typical patterns)
    logger.warning("Could not identify code structure, returning original response")
    return response.strip()
