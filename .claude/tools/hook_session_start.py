#!/usr/bin/env python3
"""
Claude Code hook for session start - minimal wrapper for memory retrieval.
Reads JSON from stdin, calls amplifier modules, writes JSON to stdout.
"""

import asyncio
import json
import os
import platform
import sys
from datetime import datetime
from pathlib import Path

# Add amplifier to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import logger from the same directory
sys.path.insert(0, str(Path(__file__).parent))
from hook_logger import HookLogger
from platform_detect import IS_OPENCODE

logger = HookLogger("session_start")

try:
    from amplifier.memory import MemoryStore
    from amplifier.search import MemorySearcher
except ImportError as e:
    logger.error(f"Failed to import amplifier modules: {e}")
    # Exit gracefully to not break hook chain
    json.dump({}, sys.stdout)
    sys.exit(0)


def format_session_env():
    """Format session environment details."""
    return [
        f"- **Today's Date:** {datetime.now().strftime('%A, %B %d, %Y')}",
        f"- **Platform:** {platform.system()} ({platform.release()})",
        f"- **Working Directory:** {os.getcwd()}",
    ]


def format_memories(search_results, unique_recent, base_heading_level=2):
    """Format memory search results and recent memories."""
    parts = []

    if not (search_results or unique_recent):
        return parts

    h_base = "#" * base_heading_level
    h_sub = "#" * (base_heading_level + 1)

    parts.append(f"\n{h_base} Relevant Context from Memory System")

    if search_results:
        parts.append(f"{h_sub} Relevant Memories")
        for result in search_results[:3]:
            content = result.memory.content
            category = result.memory.category
            score = result.score
            parts.append(f"- **{category}** (relevance: {score:.2f}): {content}")

    if unique_recent:
        parts.append(f"\n{h_sub} Recent Context")
        for mem in unique_recent[:2]:
            parts.append(f"- {mem.category}: {mem.content}")

    return parts


async def main():
    """Read input, search memories, return context"""
    try:
        # Check if memory system is enabled
        # We check this env var first to allow quick disable
        memory_enabled = os.getenv("MEMORY_SYSTEM_ENABLED", "false").lower() in [
            "true",
            "1",
            "yes",
        ]
        if not memory_enabled:
            logger.info("Memory system disabled via MEMORY_SYSTEM_ENABLED env var")
            # Return empty response and exit gracefully
            json.dump({}, sys.stdout)
            return

        logger.info("Starting memory retrieval")
        logger.cleanup_old_logs()  # Clean up old logs on each run

        # Read JSON input
        try:
            raw_input = sys.stdin.read()
        except Exception as e:
            logger.error(f"Failed to read stdin: {e}")
            json.dump({}, sys.stdout)
            return

        logger.info(f"Received input length: {len(raw_input)}")

        if not raw_input:
            logger.warning("Empty input received")
            json.dump({}, sys.stdout)
            return

        try:
            input_data = json.loads(raw_input)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON input: {e}")
            json.dump({}, sys.stdout)
            return

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

        # Check data directory (debug info)
        logger.debug(f"Data directory: {store.data_dir}")
        logger.debug(f"Data file: {store.data_file}")

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

        # Prepare context parts
        context_parts = []

        # Calculate unique recent memories
        seen_ids = {r.memory.id for r in search_results}
        unique_recent = [m for m in recent if m.id not in seen_ids]

        if IS_OPENCODE:
            # --- GEMINI OPTIMIZED STRUCTURE ---
            # 1. Frozen Zone: Stable project header
            context_parts.append("## [FROZEN ZONE: STABLE CONTEXT]")

            # Read frozen header
            frozen_path = Path(__file__).parent.parent / "context" / "frozen_header.md"
            if frozen_path.exists():
                try:
                    frozen_content = frozen_path.read_text(encoding="utf-8").strip()
                    context_parts.append(frozen_content)
                except Exception as e:
                    logger.error(f"Failed to read frozen header: {e}")
            else:
                logger.warning(f"Frozen header not found at {frozen_path}")

            # 2. Churn Zone: Dynamic Session Context
            context_parts.append("\n## [CHURN ZONE: DYNAMIC SESSION CONTEXT]")

            # Session Environment (Dynamic)
            context_parts.extend(format_session_env())

            # Memory Search Results (Dynamic because depends on prompt)
            context_parts.extend(
                format_memories(search_results, unique_recent, base_heading_level=3)
            )

        else:
            # --- STANDARD CLAUDE CODE STRUCTURE ---
            # Keep existing behavior roughly: Memories first, then session info

            context_parts.extend(
                format_memories(search_results, unique_recent, base_heading_level=2)
            )

            context_parts.append("\n## Session Environment")
            context_parts.extend(format_session_env())

        # Build response
        context = "\n".join(context_parts)

        output = {}
        if context:
            # Calculate memories loaded
            memories_loaded = len(search_results) + len(unique_recent)

            output = {
                "additionalContext": context,
                "metadata": {
                    "memoriesLoaded": memories_loaded,
                    "source": "amplifier_memory",
                },
            }

        json.dump(output, sys.stdout)
        logger.info(
            f"Returned {len(context_parts) if context_parts else 0} context parts"
        )

    except Exception as e:
        logger.exception("Error during memory retrieval", e)
        json.dump({}, sys.stdout)


if __name__ == "__main__":
    asyncio.run(main())
