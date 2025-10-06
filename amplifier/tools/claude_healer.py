"""Direct Claude Code SDK healing implementation - replacement for Aider."""

import asyncio
import logging
from pathlib import Path

from amplifier.ccsdk_toolkit.core.models import SessionOptions
from amplifier.ccsdk_toolkit.core.session import ClaudeSession

logger = logging.getLogger(__name__)


async def heal_with_claude(module_path: Path, healing_prompt: str) -> bool:
    """Apply healing to a module using Claude Code SDK directly.

    Args:
        module_path: Path to the module file to heal
        healing_prompt: The healing prompt/instructions

    Returns:
        True if healing was successful, False otherwise
    """
    try:
        # Read the current module code
        with open(module_path, encoding="utf-8") as f:
            original_code = f.read()

        # Create a prompt that includes the code and healing instructions
        full_prompt = f"""Here is the code that needs improvement:

```python
{original_code}
```

{healing_prompt}

Please provide the complete improved version of this code. Output only the improved Python code without any explanations or markdown formatting."""

        # Configure session for code healing
        options = SessionOptions(
            system_prompt="You are a code improvement assistant. Focus on simplicity, readability, and reducing complexity.",
            max_turns=1,
            stream_output=False,
            retry_attempts=2,
        )

        # Run the healing session
        async with ClaudeSession(options) as session:
            response = await session.query(full_prompt)

            if response.error:
                logger.error(f"Claude session error: {response.error}")
                return False

            if not response.content:
                logger.error("Empty response from Claude")
                return False

            # Extract the improved code from the response
            improved_code = extract_code(response.content)

            if not improved_code:
                logger.error("Could not extract improved code from response")
                return False

            # Write the improved code atomically to avoid corruption
            _atomic_write(module_path, improved_code)

            logger.info(f"Successfully healed {module_path}")
            return True

    except Exception as e:
        logger.error(f"Healing failed for {module_path}: {e}")
        return False


def _atomic_write(file_path: Path, content: str) -> None:
    """Write file atomically to avoid corruption on failure.

    Args:
        file_path: Target file path
        content: Content to write
    """
    # Write to a temporary file first
    temp_path = file_path.with_suffix(file_path.suffix + ".tmp")
    try:
        temp_path.write_text(content, encoding="utf-8")
        # Atomic rename (POSIX systems)
        temp_path.replace(file_path)
    except Exception:
        # Clean up temp file on failure
        if temp_path.exists():
            temp_path.unlink()
        raise


def extract_code(response: str) -> str:
    """Extract Python code from Claude's response.

    Claude might wrap the code in markdown blocks or include explanations.
    This function extracts just the code portion.
    """
    # Remove leading/trailing whitespace
    response = response.strip()

    # Check if response is wrapped in code blocks
    if response.startswith("```python"):
        # Extract content between ```python and ```
        start = response.find("```python") + len("```python")
        end = response.find("```", start)
        if end > start:
            return response[start:end].strip()
    elif response.startswith("```"):
        # Extract content between ``` and ```
        start = response.find("```") + len("```")
        end = response.find("```", start)
        if end > start:
            return response[start:end].strip()

    # If no code blocks, check if the entire response looks like Python code
    # (starts with common Python keywords/patterns)
    python_starters = ["import ", "from ", "def ", "class ", "#", '"""', "'''", "@"]
    if any(response.startswith(starter) for starter in python_starters):
        return response

    # Last resort: look for code blocks anywhere in the response
    if "```python" in response:
        parts = response.split("```python")
        if len(parts) > 1:
            code_part = parts[1].split("```")[0]
            return code_part.strip()
    elif "```" in response:
        parts = response.split("```")
        if len(parts) >= 3:
            # Take the second part (first code block)
            return parts[1].strip()

    # If all else fails, return the original response
    # (it might already be clean code)
    return response


def run_claude_healing(module_path: Path, prompt_file: Path | str) -> bool:
    """Synchronous wrapper for healing - drop-in replacement for _run_healing_tool.

    Args:
        module_path: Path to the module to heal
        prompt_file: Path to file containing the healing prompt

    Returns:
        True if healing succeeded, False otherwise
    """
    try:
        prompt_path = Path(prompt_file)
        if not prompt_path.exists():
            logger.error(f"Healing prompt not found: {prompt_path}")
            return False

        # Read the healing prompt from file
        with open(prompt_path, encoding="utf-8") as f:
            healing_prompt = f.read()

        # Run the async healing function
        return asyncio.run(heal_with_claude(module_path, healing_prompt))

    except Exception as e:
        logger.error(f"Failed to run Claude healing: {e}")
        return False
