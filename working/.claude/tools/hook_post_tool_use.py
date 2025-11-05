#!/usr/bin/env python3
"""
Claude Code hook for PostToolUse events - minimal wrapper for claim validation.
Reads JSON from stdin, calls amplifier modules, writes JSON to stdout.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add amplifier to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import logger from the same directory
sys.path.insert(0, str(Path(__file__).parent))
from hook_logger import HookLogger

logger = HookLogger("post_tool_use")

try:
    from amplifier.memory import MemoryStore
    from amplifier.validation import ClaimValidator
except ImportError as e:
    logger.error(f"Failed to import amplifier modules: {e}")
    # Exit gracefully to not break hook chain
    json.dump({}, sys.stdout)
    sys.exit(0)


async def main():
    """Read input, validate claims, return warnings if contradictions found"""
    try:
        # Check if memory system is enabled
        import os

        memory_enabled = os.getenv("MEMORY_SYSTEM_ENABLED", "false").lower() in ["true", "1", "yes"]
        if not memory_enabled:
            logger.info("Memory system disabled via MEMORY_SYSTEM_ENABLED env var")
            # Return empty response and exit gracefully
            json.dump({}, sys.stdout)
            return

        logger.info("Starting claim validation")
        logger.cleanup_old_logs()  # Clean up old logs on each run

        # Read JSON input
        raw_input = sys.stdin.read()
        logger.info(f"Received input length: {len(raw_input)}")

        input_data = json.loads(raw_input)

        # Extract message
        message = input_data.get("message", {})
        role = message.get("role", "")
        content = message.get("content", "")

        logger.debug(f"Message role: {role}")
        logger.debug(f"Content length: {len(content)}")

        # Skip if not assistant message or too short
        if role != "assistant" or not content or len(content) < 50:
            logger.info(f"Skipping: role={role}, content_len={len(content)}")
            json.dump({}, sys.stdout)
            return

        # Initialize modules
        logger.info("Initializing store and validator")
        store = MemoryStore()
        validator = ClaimValidator()

        # Get all memories for validation
        memories = store.get_all()
        logger.info(f"Total memories for validation: {len(memories)}")

        # Validate text for claims
        logger.info("Validating text for claims")
        validation_result = validator.validate_text(content, memories)
        logger.info(f"Has contradictions: {validation_result.has_contradictions}")
        logger.info(f"Claims found: {len(validation_result.claims)}")

        # Build response if contradictions found
        output = {}
        if validation_result.has_contradictions:
            warnings = []
            for claim_validation in validation_result.claims:
                if claim_validation.contradicts and claim_validation.confidence > 0.6:
                    claim_text = claim_validation.claim[:100]
                    warnings.append(f"⚠️ Claim may be incorrect: '{claim_text}...'")

                    if claim_validation.evidence:
                        evidence = claim_validation.evidence[0][:150]
                        warnings.append(f"   Memory says: {evidence}")

            if warnings:
                output = {
                    "warning": "\n".join(warnings),
                    "metadata": {
                        "contradictionsFound": sum(1 for c in validation_result.claims if c.contradicts),
                        "claimsChecked": len(validation_result.claims),
                        "source": "amplifier_validation",
                    },
                }

        json.dump(output, sys.stdout)

        if output:
            logger.info(f"Returned {len(warnings) if 'warnings' in locals() else 0} warnings")
        else:
            logger.info("No contradictions found")

    except Exception as e:
        logger.exception("Error during claim validation", e)
        json.dump({}, sys.stdout)


if __name__ == "__main__":
    asyncio.run(main())
