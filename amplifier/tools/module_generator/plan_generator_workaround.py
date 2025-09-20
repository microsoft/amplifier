"""
Workaround for SDK plan mode hanging issue.

This module provides an alternative plan generation method that avoids
triggering the Claude Code SDK's interactive plan mode.
"""

import asyncio
import logging

logger = logging.getLogger(__name__)

try:
    from claude_code_sdk import ClaudeCodeOptions
    from claude_code_sdk import ClaudeSDKClient

    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False


async def generate_module_design(contract: str, impl_spec: str, timeout: int = 120) -> str | None:
    """Generate module design using safe prompting that avoids plan mode.

    The Claude Code SDK enters an interactive "plan mode" when it detects
    certain keywords like "plan", "planning", "implementation plan" etc.
    This function uses alternative terminology to avoid that mode.

    Args:
        contract: Contract specification
        impl_spec: Implementation specification
        timeout: Maximum time to wait for response

    Returns:
        Module design document or None if failed
    """
    if not SDK_AVAILABLE:
        logger.error("Claude Code SDK not available")
        return None

    # Use terminology that doesn't trigger plan mode
    prompt = f"""You are creating a technical specification document. Output a complete technical design.

INPUT SPECIFICATIONS:
{contract}

TECHNICAL REQUIREMENTS:
{impl_spec}

Create a comprehensive technical document with these sections:

1. ARCHITECTURE OVERVIEW
Describe the overall module architecture and structure.

2. FILE STRUCTURE
List all files and directories needed:
- Core implementation files
- Test files
- Configuration files

3. COMPONENT DESIGN
Describe each major component:
- Classes and their responsibilities
- Key functions and methods
- Data models

4. CONSTRUCTION SEQUENCE
List the build sequence:
- Step 1: [description]
- Step 2: [description]
(continue for all steps)

5. QUALITY ASSURANCE
Describe testing approach:
- Unit test coverage
- Integration tests
- Test data and fixtures

6. TECHNICAL DEPENDENCIES
List required packages and tools.

Output the complete technical document now."""

    try:
        # Use very generic system prompt to avoid mode detection
        options = ClaudeCodeOptions(
            system_prompt="You are a technical documentation assistant.",
            max_turns=1,
        )

        logger.info("Generating module technical design...")

        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)

            response = ""
            chunks_received = 0
            last_chunk_time = None

            async with asyncio.timeout(timeout):
                async for message in client.receive_response():
                    import time

                    current_time = time.time()

                    # Track first real content chunk
                    if chunks_received == 0 and hasattr(message, "content"):
                        logger.info("Receiving design document...")
                        last_chunk_time = current_time

                    # Check for stalls
                    if last_chunk_time and current_time - last_chunk_time > 30:
                        logger.warning("Response stalled - may be in interactive mode")
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
                                        last_chunk_time = current_time

                                        if chunks_received % 10 == 0:
                                            logger.debug(f"Progress: {chunks_received} chunks, {len(response)} chars")

            if response.strip():
                logger.info(f"Design document generated: {len(response)} characters")
                return response
            logger.warning("Empty response received")
            return None

    except TimeoutError:
        logger.error(f"Design generation timed out after {timeout} seconds")
        logger.info("The SDK may be stuck in interactive mode. Try simpler prompts.")
        return None
    except Exception as e:
        logger.error(f"Error generating design: {e}")
        return None


async def test_workaround():
    """Test the workaround with minimal specifications."""

    contract = """# Module: test_module

A simple test module that processes data.

## Interface
- process(data: str) -> str: Process input data
"""

    impl_spec = """## Implementation

Use Python standard library only.
Simple, direct implementation.
"""

    result = await generate_module_design(contract, impl_spec, timeout=60)

    if result:
        print("SUCCESS: Generated design document")
        print(f"Length: {len(result)} characters")
        print("\nFirst 500 characters:")
        print(result[:500])
    else:
        print("FAILED: Could not generate design")

    return result is not None


if __name__ == "__main__":
    # Test the workaround
    asyncio.run(test_workaround())
