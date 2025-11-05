"""
Prompt isolation to prevent context contamination.

Ensures AI responses are based only on provided content, not system context.
"""


def isolate_prompt(prompt: str, content: str) -> str:
    """
    Create an isolated prompt that prevents AI from using system context.

    Adds explicit boundaries to ensure the AI:
    - Uses ONLY the content provided
    - Does NOT reference any system files
    - Has no access to any files or system context

    Args:
        prompt: The task or question to ask
        content: The specific content to analyze

    Returns:
        Isolated prompt with clear boundaries
    """
    isolation_prefix = """IMPORTANT INSTRUCTIONS:
- Use ONLY the content provided below for your response
- Do NOT reference or use any system files, previous context, or external knowledge
- You have NO access to any files, folders, or system context
- Base your response SOLELY on the content between the START and END markers
- If asked about files or paths, only refer to what's explicitly in the provided content"""

    isolated = f"""{isolation_prefix}

TASK: {prompt}

--- START OF CONTENT ---
{content}
--- END OF CONTENT ---

Remember: Your response must be based ONLY on the content above. Do not reference any external files or system context."""

    return isolated
