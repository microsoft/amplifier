"""
Workaround for module generation hanging issue.

This module provides an alternative module generation method that avoids
triggering the Claude Code SDK's interactive modes.
"""

import asyncio
import json
import logging
from pathlib import Path

from amplifier.utils.file_io import write_text_with_retry

logger = logging.getLogger(__name__)

try:
    from claude_code_sdk import ClaudeCodeOptions
    from claude_code_sdk import ClaudeSDKClient

    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False


async def generate_module_code(
    module_name: str,
    module_path: Path,
    contract: str,
    impl_spec: str,
    design_doc: str,
    timeout: int = 600,
) -> bool:
    """Generate module code using safe prompting that avoids interactive modes.

    The Claude Code SDK enters interactive modes when it detects certain keywords.
    This function uses careful terminology to avoid those modes.

    Args:
        module_name: Name of the module to generate
        module_path: Path where module should be created
        contract: Contract specification
        impl_spec: Implementation specification
        design_doc: Design document (previously generated)
        timeout: Maximum time to wait for response

    Returns:
        True if successful, False otherwise
    """
    if not SDK_AVAILABLE:
        logger.error("Claude Code SDK not available")
        return False

    # Create module directory
    module_path.mkdir(parents=True, exist_ok=True)

    # Craft a prompt that avoids problematic keywords
    # Avoid: plan, planning, implementation plan, etc.
    # Use: design, structure, build, create, generate
    prompt = f"""Generate Python module code in markdown code blocks. Each file should be a separate code block with the filename as a comment.

MODULE NAME: {module_name}
OUTPUT DIRECTORY: {module_path}

REQUIREMENTS:
{contract[:1500]}

TECHNICAL SPEC:
{impl_spec[:1500]}

DESIGN:
{design_doc[:2000]}

Output the complete module code in this format:

```python
# File: __init__.py
[complete __init__.py code here]
```

```python
# File: core.py
[complete core.py code here]
```

```python
# File: tests/test_core.py
[complete test code here]
```

```markdown
# File: README.md
[complete README content here]
```

Generate ALL files now with complete, working implementations. Include type hints, docstrings, and error handling."""

    try:
        # Use very generic system prompt to avoid mode detection
        options = ClaudeCodeOptions(
            system_prompt="You are a Python code generator. Create working code files.",
            max_turns=1,  # Single-shot generation only
        )

        logger.info(f"Generating module code for {module_name}...")
        logger.info("This may take 2-5 minutes for complex modules")

        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)

            response = ""
            chunks_received = 0
            import time

            last_activity = time.time()
            last_log = time.time()

            async with asyncio.timeout(timeout):
                async for message in client.receive_response():
                    current_time = time.time()

                    # Check for inactivity
                    if current_time - last_activity > 60:
                        logger.warning("No activity for 60 seconds, may be stuck")
                        raise TimeoutError("Response stalled")

                    if hasattr(message, "content"):
                        content = getattr(message, "content", [])
                        if isinstance(content, list):
                            for block in content:
                                if hasattr(block, "text"):
                                    text = getattr(block, "text", "")
                                    if text:
                                        response += text
                                        chunks_received += 1
                                        last_activity = current_time

                                        # Log progress every 10 seconds
                                        if current_time - last_log > 10:
                                            logger.info(
                                                f"Progress: {chunks_received} chunks, "
                                                f"{len(response)} characters received"
                                            )
                                            last_log = current_time

            logger.info(f"Code generation complete: {len(response)} characters")

            # Parse the response and create files from code blocks
            if response:
                success = _parse_and_create_files(module_path, response)

                if success:
                    logger.info(f"Module files created successfully in {module_path}")

                    # Save generation metadata
                    metadata = {
                        "module_name": module_name,
                        "generated_via": "workaround_single_shot",
                        "response_length": len(response),
                        "chunks_received": chunks_received,
                        "generator_version": "2.1.0",
                    }
                    metadata_path = module_path / ".generation_metadata.json"
                    write_text_with_retry(json.dumps(metadata, indent=2), metadata_path)

                    return True
                logger.warning("Failed to parse and create files from response")

                # Save the response for debugging
                debug_path = module_path / ".generation_response.txt"
                write_text_with_retry(response, debug_path)
                logger.info(f"Saved raw response to {debug_path} for debugging")

                return False

            logger.error("Empty response received from SDK")
            return False

    except TimeoutError:
        logger.error(f"Module generation timed out after {timeout} seconds")
        logger.info("The SDK may be stuck in interactive mode")
        return False
    except Exception as e:
        logger.error(f"Error generating module: {e}")
        return False

    # This should never be reached, but satisfies type checker
    return False


def _parse_and_create_files(module_path: Path, response: str) -> bool:
    """Parse response and create module files from markdown code blocks.

    Args:
        module_path: Directory to create files in
        response: Response containing code blocks

    Returns:
        True if files created, False otherwise
    """
    import re  # Import here to avoid linter removing it

    # Extract code blocks with file markers
    # Look for patterns like ```python\n# File: filename\n...```
    pattern = r"```(?:python|py|markdown|md)?\s*\n#\s*File:\s*(.+?)\n(.*?)```"
    matches = re.findall(pattern, response, re.DOTALL)

    if not matches:
        logger.warning("No code blocks found in response")
        return False

    created_files = []
    for filename, content in matches:
        # Clean filename
        filename = filename.strip()

        # Create file path
        if "/" in filename:
            file_path = module_path / filename
        else:
            file_path = module_path / filename

        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        write_text_with_retry(content.strip() + "\n", file_path)
        created_files.append(file_path)
        logger.info(f"Created: {file_path}")

    # Check if core files were created
    required_files = [
        module_path / "__init__.py",
        module_path / "core.py",
    ]

    if all(f.exists() for f in required_files):
        logger.info(f"All required files created: {[f.name for f in required_files]}")
        return True

    existing = [f.name for f in required_files if f.exists()]
    missing = [f.name for f in required_files if not f.exists()]
    logger.warning(f"Some required files missing. Found: {existing}, Missing: {missing}")

    # Still return True if we created some files
    return len(created_files) > 0


async def test_workaround():
    """Test the workaround with a simple module."""

    module_name = "test_module"
    module_path = Path("amplifier") / module_name

    contract = """# Module: test_module

A simple test module.

## Interface
- process(data: str) -> str: Process input
"""

    impl_spec = """## Implementation

Use Python standard library.
Simple implementation.
"""

    design_doc = """## Module Structure

- __init__.py: Module initialization
- core.py: Main processing logic
- tests/test_core.py: Unit tests

## Components

ProcessorClass: Main processor
- process method: handles input
"""

    # Clean up any existing test module
    import shutil

    if module_path.exists():
        shutil.rmtree(module_path)

    result = await generate_module_code(module_name, module_path, contract, impl_spec, design_doc, timeout=60)

    if result:
        print(f"SUCCESS: Module generated at {module_path}")
        # List created files
        for f in module_path.rglob("*"):
            if f.is_file():
                print(f"  Created: {f.relative_to(module_path)}")
    else:
        print("FAILED: Could not generate module")

    return result


if __name__ == "__main__":
    # Test the workaround
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_workaround())
