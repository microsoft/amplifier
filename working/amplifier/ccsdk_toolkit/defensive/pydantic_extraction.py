"""
Extraction utilities for pydantic_ai responses.

Handles various response formats from pydantic_ai agents.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def extract_agent_output(result: Any) -> str:
    """
    Extract clean text from pydantic_ai AgentRunResult or similar response objects.

    Handles various response formats including:
    - AgentRunResult with .data attribute
    - Direct string responses
    - Objects with str() representations containing "output="

    Args:
        result: The response from pydantic_ai Agent.run()

    Returns:
        Clean text output without wrapper objects
    """
    if result is None:
        return ""

    # If it's already a string, check for wrapper patterns
    if isinstance(result, str):
        # Check if it looks like "AgentRunResult(output='...')"
        if result.startswith("AgentRunResult(output="):
            try:
                # Extract the actual output from the string representation
                # Find the content between output=' and the last ')
                start = result.find("output='") + 8
                if start > 7:  # Found the pattern
                    end = result.rfind("')")
                    if end > start:
                        return result[start:end]
            except Exception as e:
                logger.debug(f"Failed to extract from AgentRunResult string: {e}")
        return result

    # Try to access .data attribute (common in pydantic_ai responses)
    if hasattr(result, "data"):
        data = result.data
        # Recursively extract in case data is also wrapped
        return extract_agent_output(data)

    # Try to access .output attribute directly
    if hasattr(result, "output"):
        return str(result.output)

    # Convert to string and check for wrapper patterns
    str_result = str(result)

    # If the string representation contains the AgentRunResult wrapper
    if "AgentRunResult(output=" in str_result:
        return extract_agent_output(str_result)

    return str_result
