"""Claude SDK helper with timeout and retry logic."""

import json
from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions


async def query_claude_with_timeout(
    prompt: str,
    system_prompt: str = "You are a helpful AI assistant.",
    timeout_seconds: int = 120,
    parse_json: bool = False,
) -> Any:
    """Query Claude with proper timeout handling.

    Args:
        prompt: The user prompt
        system_prompt: System prompt for context
        timeout_seconds: Timeout in seconds (default 120 as per DISCOVERIES.md)
        parse_json: Whether to parse response as JSON

    Returns:
        SessionResponse or parsed JSON dict
    """
    options = SessionOptions(
        system_prompt=system_prompt, timeout_seconds=timeout_seconds, retry_attempts=2, max_turns=1
    )

    async with ClaudeSession(options) as session:
        response = await session.query(prompt)

        if response.error:
            raise RuntimeError(f"Claude query failed: {response.error}")

        if not response.content:
            raise RuntimeError("Received empty response from Claude")

        if parse_json:
            # Strip markdown code blocks if present
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]

            if content.endswith("```"):
                content = content[:-3]

            content = content.strip()

            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                # Try to extract JSON from content if it's mixed with other text
                import re

                json_match = re.search(r"\[.*\]", content, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except json.JSONDecodeError:
                        pass
                # Return empty list for synthesizer to handle gracefully
                print(f"Warning: Failed to parse JSON response: {e}")
                return []

        return response
