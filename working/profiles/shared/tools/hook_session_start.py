#!/usr/bin/env python3
"""
Claude Code hook for session start - minimal wrapper for memory retrieval.
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

logger = HookLogger("session_start")

try:
    from amplifier.memory import MemoryStore
    from amplifier.search import MemorySearcher
except ImportError as e:
    logger.error(f"Failed to import amplifier modules: {e}")
    # Exit gracefully to not break hook chain
    json.dump({}, sys.stdout)
    sys.exit(0)


async def main():
    """Read input, search memories, return context"""
    try:
        # Check if memory system is enabled
        import os

        memory_enabled = os.getenv("MEMORY_SYSTEM_ENABLED", "false").lower() in ["true", "1", "yes"]
        if not memory_enabled:
            logger.info("Memory system disabled via MEMORY_SYSTEM_ENABLED env var")
            # Return empty response and exit gracefully
            json.dump({}, sys.stdout)
            return

        logger.info("Starting memory retrieval")
        logger.cleanup_old_logs()  # Clean up old logs on each run

        # Read JSON input
        raw_input = sys.stdin.read()
        logger.info(f"Received input length: {len(raw_input)}")

        input_data = json.loads(raw_input)
        prompt = input_data.get("prompt", "")
        logger.info(f"Prompt length: {len(prompt)}")

        if prompt:
            logger.debug(f"Prompt preview: {prompt[:100]}...")

        if not prompt:
            logger.warning("No prompt provided, exiting")
            json.dump({}, sys.stdout)
            return

        # Initialize modules
        logger.info("Initializing store and searcher")
        store = MemoryStore()
        searcher = MemorySearcher()

        # Check data directory
        logger.debug(f"Data directory: {store.data_dir}")
        logger.debug(f"Data file: {store.data_file}")
        logger.debug(f"Data file exists: {store.data_file.exists()}")

        # Get all memories
        all_memories = store.get_all()
        logger.info(f"Total memories in store: {len(all_memories)}")

        # Search for relevant memories
        logger.info("Searching for relevant memories")
        search_results = searcher.search(prompt, all_memories, limit=5)
        logger.info(f"Found {len(search_results)} relevant memories")

        # Get recent memories too
        recent = store.search_recent(limit=3)
        logger.info(f"Found {len(recent)} recent memories")

        # Format context
        context_parts = []
        if search_results or recent:
            context_parts.append("## Relevant Context from Memory System\n")

            # Add relevant memories
            if search_results:
                context_parts.append("### Relevant Memories")
                for result in search_results[:3]:
                    content = result.memory.content
                    category = result.memory.category
                    score = result.score
                    context_parts.append(f"- **{category}** (relevance: {score:.2f}): {content}")

            # Add recent memories not already shown
            seen_ids = {r.memory.id for r in search_results}
            unique_recent = [m for m in recent if m.id not in seen_ids]
            if unique_recent:
                context_parts.append("\n### Recent Context")
                for mem in unique_recent[:2]:
                    context_parts.append(f"- {mem.category}: {mem.content}")

        # Build response
        context = "\n".join(context_parts) if context_parts else ""

        output = {}
        if context:
            # Calculate memories loaded - unique_recent is always defined after the conditional above
            memories_loaded = len(search_results)
            if search_results:
                # unique_recent is defined when we have search_results
                seen_ids = {r.memory.id for r in search_results}
                unique_recent_count = len([m for m in recent if m.id not in seen_ids])
                memories_loaded += unique_recent_count
            else:
                # No search results, so all recent memories are unique
                memories_loaded += len(recent)

            output = {
                "additionalContext": context,
                "metadata": {
                    "memoriesLoaded": memories_loaded,
                    "source": "amplifier_memory",
                },
            }

        json.dump(output, sys.stdout)
        logger.info(f"Returned {len(context_parts) if context_parts else 0} memory contexts")

    except Exception as e:
        logger.exception("Error during memory retrieval", e)
        json.dump({}, sys.stdout)


if __name__ == "__main__":
    asyncio.run(main())
