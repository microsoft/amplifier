"""
Code extraction from LLM responses with defensive handling.

Extracts Python code from any LLM response format without raising exceptions.
"""

import ast
import logging
import re

logger = logging.getLogger(__name__)


def parse_llm_code(response: str, validate_python: bool = True, verbose: bool = False) -> str | None:
    """
    Extract Python code from any LLM response format.

    Handles:
    - Plain code
    - Markdown-wrapped code (```python blocks)
    - Code with text preambles
    - Conversational responses containing code

    Returns None if no valid code is found (doesn't raise exceptions).

    Args:
        response: Raw LLM response text
        validate_python: If True, validate that extracted text is valid Python
        verbose: If True, log debugging output for failed parsing attempts

    Returns:
        Extracted Python code as string, or None if extraction fails
    """
    if not response or not isinstance(response, str):
        if verbose:
            logger.debug(f"Empty or invalid response type: {type(response)}")
        return None

    # Try 1: Check if response is already pure Python code
    code = response.strip()
    if _is_valid_python(code):
        if verbose:
            logger.debug("Response is already valid Python code")
        return code

    # Try 2: Extract from markdown code blocks (most common case)
    # Match ```python ... ``` or ```py ... ``` or ``` ... ```
    patterns = [
        (r"```python\s*\n(.*?)```", "python block"),
        (r"```py\s*\n(.*?)```", "py block"),
        (r"```\s*\n(.*?)```", "generic block"),
    ]

    for pattern, desc in patterns:
        matches = re.findall(pattern, response, re.DOTALL)
        for match in matches:
            match = match.strip()
            if match:
                if not validate_python or _is_valid_python(match):
                    if verbose:
                        logger.debug(f"Successfully extracted code from {desc}")
                    return match
                if verbose:
                    logger.debug(f"Found {desc} but not valid Python")

    # Try 3: Remove common preambles and extract code
    # Split into lines and look for code start
    lines = response.split("\n")

    # Find where code likely starts
    code_start_idx = -1
    for i, line in enumerate(lines):
        # Check for import statements or common Python starters
        if re.match(r'^(import |from |#!|""")', line.strip()):
            code_start_idx = i
            break

    if code_start_idx >= 0:
        # Extract from code start to end
        potential_code = "\n".join(lines[code_start_idx:]).strip()

        # Remove any trailing explanatory text
        # Look for double newline followed by prose
        parts = potential_code.split("\n\n")
        code_parts = []
        for part in parts:
            # Stop if we hit explanatory text
            if part and not _looks_like_code_block(part):
                break
            code_parts.append(part)

        if code_parts:
            extracted = "\n\n".join(code_parts).strip()
            if extracted and (not validate_python or _is_valid_python(extracted)):
                if verbose:
                    logger.debug("Successfully extracted code by finding start pattern")
                return extracted

    # Try 4: Look for the largest contiguous block of Python-like lines
    code_blocks = _extract_code_blocks(lines)

    # Try the largest block first
    for block in sorted(code_blocks, key=len, reverse=True):
        if block and (not validate_python or _is_valid_python(block)):
            if verbose:
                logger.debug("Successfully extracted largest Python-like block")
            return block

    # All attempts failed
    if verbose:
        logger.debug(f"All code extraction attempts failed. Response (first 200 chars): {response[:200]}")
    return None


def _is_valid_python(code: str) -> bool:
    """Check if the given string is valid Python code."""
    if not code or not code.strip():
        return False

    try:
        # Try to compile as a module (most common case)
        compile(code, "<string>", "exec")
        return True
    except SyntaxError:
        # Maybe it's an expression or has minor issues
        try:
            ast.parse(code)
            return True
        except:
            return False


def _looks_like_code_block(text: str) -> bool:
    """Check if a text block looks like code rather than prose."""
    lines = text.strip().split("\n")
    if not lines:
        return False

    # Count lines that look like code
    code_lines = 0
    total_lines = len(lines)

    for line in lines:
        if _looks_like_python_line(line):
            code_lines += 1

    # If more than 50% of lines look like code, it's probably code
    return code_lines > total_lines * 0.5


def _looks_like_python_line(line: str) -> bool:
    """Heuristic to check if a line looks like Python code."""
    line = line.strip()

    # Empty lines and comments are valid in Python
    if not line or line.startswith("#"):
        return True

    # Common Python keywords and patterns
    python_indicators = [
        # Keywords
        "import ",
        "from ",
        "def ",
        "class ",
        "if ",
        "elif ",
        "else:",
        "for ",
        "while ",
        "try:",
        "except",
        "finally:",
        "with ",
        "return ",
        "yield ",
        "raise ",
        "assert ",
        "pass",
        "break",
        "continue",
        "async ",
        "await ",
        # Common patterns
        "@",  # Decorators
        "= ",  # Assignment
        "(",  # Function calls
        ".",  # Attribute access
        "[",  # Indexing/lists
        "{",  # Dicts
        '"""',
        "'''",  # Docstrings
    ]

    for indicator in python_indicators:
        if indicator in line:
            return True

    # Check if line is indented (likely inside a block)
    if line != line.lstrip():
        return True

    return False


def _extract_code_blocks(lines: list[str]) -> list[str]:
    """Extract contiguous blocks that look like code."""
    blocks = []
    current_block = []
    in_code = False

    for line in lines:
        if _looks_like_python_line(line):
            if not in_code:
                in_code = True
                current_block = [line]
            else:
                current_block.append(line)
        else:
            # Non-code line
            if in_code and current_block:
                # Save the current block if it has content
                block_text = "\n".join(current_block).strip()
                if block_text:
                    blocks.append(block_text)
                current_block = []
                in_code = False

    # Don't forget the last block
    if current_block:
        block_text = "\n".join(current_block).strip()
        if block_text:
            blocks.append(block_text)

    return blocks


def extract_code_with_validation(response: str, max_retries: int = 3, verbose: bool = False) -> tuple[str | None, str]:
    """
    Extract and validate Python code from LLM response.

    Returns a tuple of (code, status_message).
    If code is None, status_message explains why.

    Args:
        response: Raw LLM response text
        max_retries: Maximum validation attempts
        verbose: If True, log debugging output

    Returns:
        Tuple of (extracted_code, status_message)
    """
    # First try to extract code
    code = parse_llm_code(response, validate_python=True, verbose=verbose)

    if code:
        return code, "Successfully extracted valid Python code"

    # Try without validation
    code = parse_llm_code(response, validate_python=False, verbose=verbose)

    if code:
        # We found something that looks like code but isn't valid Python
        # Try to fix common issues
        fixed_code = _attempt_code_fixes(code)
        if fixed_code and _is_valid_python(fixed_code):
            return fixed_code, "Extracted and fixed Python code"
        return None, "Found code-like content but it's not valid Python"

    # Check if response is conversational
    if _is_conversational_response(response):
        return None, "Response is conversational text instead of code"

    return None, "No code found in response"


def _attempt_code_fixes(code: str) -> str | None:
    """Attempt to fix common code issues."""
    # Remove any remaining markdown artifacts
    code = re.sub(r"^```.*?\n?", "", code)
    code = re.sub(r"\n?```$", "", code)

    # Trim any obvious non-code at the beginning
    lines = code.split("\n")
    while lines and not _looks_like_python_line(lines[0]):
        lines.pop(0)

    # Trim any obvious non-code at the end
    while lines and not _looks_like_python_line(lines[-1]):
        lines.pop()

    return "\n".join(lines) if lines else None


def _is_conversational_response(response: str) -> bool:
    """Check if response is conversational rather than code."""
    # Check first few lines for conversational patterns
    first_lines = response.strip().split("\n")[:3]
    first_text = " ".join(first_lines).lower()

    conversational_patterns = [
        r"^i'(ll|m going to|ve)",
        r"^let me",
        r"^i can help",
        r"^i'll create",
        r"^here's (how|what)",
        r"^to (create|implement|build)",
        r"^this (will|code|implementation)",
        r"^sure,? i",
    ]

    for pattern in conversational_patterns:
        if re.match(pattern, first_text):
            return True

    return False
