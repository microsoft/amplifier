"""
Session Manager MCP Server for Codex.
Provides memory system integration at session boundaries.
Replaces Claude Code SessionStart and Stop hooks with explicit MCP tools.
"""

import asyncio
import json

# Add parent directory to path for absolute imports
import sys
from pathlib import Path
from typing import Any

# Import FastMCP for server framework
from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).parent.parent))

# Import base utilities using absolute imports
from base import MCPLogger
from base import check_memory_system_enabled
from base import error_response
from base import get_project_root
from base import metadata_response
from base import setup_amplifier_path
from base import success_response

# Initialize FastMCP server
mcp = FastMCP("amplifier-session")

# Initialize logger
logger = MCPLogger("session_manager")


@mcp.tool()
async def initialize_session(prompt: str, context: str | None = None) -> dict[str, Any]:
    """
    Load relevant memories at session start to provide context.

    Args:
        prompt: The initial prompt or query for the session
        context: Optional additional context about the session

    Returns:
        Dictionary containing formatted memory context and metadata
    """
    try:
        logger.info("Initializing session with memory retrieval")
        logger.debug(f"Prompt length: {len(prompt)}")
        if context:
            logger.debug(f"Context length: {len(context)}")

        # Check if memory system is enabled
        memory_enabled = check_memory_system_enabled()
        if not memory_enabled:
            logger.info("Memory system disabled via MEMORY_SYSTEM_ENABLED env var")
            return metadata_response({"memories_loaded": 0, "source": "amplifier_memory", "disabled": True})

        # Set up amplifier path
        project_root = get_project_root()
        if not setup_amplifier_path(project_root):
            logger.warning("Failed to set up amplifier path")
            return error_response("Amplifier modules not available")

        # Import amplifier modules safely
        try:
            from amplifier.memory import MemoryStore
            from amplifier.search import MemorySearcher
        except ImportError as e:
            logger.error(f"Failed to import amplifier modules: {e}")
            return error_response("Memory modules not available", {"import_error": str(e)})

        # Initialize modules
        logger.info("Initializing memory store and searcher")
        store = MemoryStore()
        searcher = MemorySearcher()

        # Check data directory
        logger.debug(f"Data directory: {store.data_dir}")
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
        context_str = "\n".join(context_parts) if context_parts else ""

        # Calculate memories loaded
        memories_loaded = len(search_results)
        if search_results:
            seen_ids = {r.memory.id for r in search_results}
            unique_recent_count = len([m for m in recent if m.id not in seen_ids])
            memories_loaded += unique_recent_count
        else:
            memories_loaded += len(recent)

        output = {
            "additionalContext": context_str,
            "metadata": {
                "memoriesLoaded": memories_loaded,
                "source": "amplifier_memory",
            },
        }

        logger.info(f"Session initialized with {memories_loaded} memories loaded")
        return success_response(output)

    except Exception as e:
        logger.exception("Error during session initialization", e)
        return error_response("Session initialization failed", {"error": str(e)})


@mcp.tool()
async def finalize_session(messages: list[dict[str, Any]], context: str | None = None) -> dict[str, Any]:
    """
    Extract and store memories from conversation at session end.

    Args:
        messages: List of conversation messages with role and content
        context: Optional context about the session

    Returns:
        Dictionary containing extraction results and metadata
    """
    try:
        logger.info("Finalizing session with memory extraction")
        logger.info(f"Processing {len(messages)} messages")

        # Check if memory system is enabled
        memory_enabled = check_memory_system_enabled()
        if not memory_enabled:
            logger.info("Memory system disabled via MEMORY_SYSTEM_ENABLED env var")
            return metadata_response({"memories_extracted": 0, "source": "amplifier_extraction", "disabled": True})

        # Set up amplifier path
        project_root = get_project_root()
        if not setup_amplifier_path(project_root):
            logger.warning("Failed to set up amplifier path")
            return error_response("Amplifier modules not available")

        # Import amplifier modules safely
        try:
            from amplifier.extraction import MemoryExtractor
            from amplifier.memory import MemoryStore
        except ImportError as e:
            logger.error(f"Failed to import amplifier modules: {e}")
            return error_response("Extraction modules not available", {"import_error": str(e)})

        # Set timeout for the entire operation
        async with asyncio.timeout(60):  # 60 second timeout
            # Get context from first user message if not provided
            if not context:
                for msg in messages:
                    if msg.get("role") == "user":
                        context = msg.get("content", "")[:200]
                        logger.debug(f"Extracted context from first user message: {context[:50]}...")
                        break

            # Initialize modules
            logger.info("Initializing extractor and store")
            extractor = MemoryExtractor()
            store = MemoryStore()

            # Check data directory
            logger.debug(f"Data directory: {store.data_dir}")
            logger.debug(f"Data file exists: {store.data_file.exists()}")

            # Extract memories from messages
            logger.info("Starting extraction from messages")
            extracted = await extractor.extract_from_messages(messages, context)
            logger.debug(f"Extraction result: {json.dumps(extracted, default=str)[:500]}...")

            # Store extracted memories
            memories_count = 0
            if extracted and "memories" in extracted:
                memories_list = extracted.get("memories", [])
                logger.info(f"Found {len(memories_list)} memories to store")

                store.add_memories_batch(extracted)
                memories_count = len(memories_list)

                logger.info(f"Stored {memories_count} memories")
                logger.info(f"Total memories in store: {len(store.get_all())}")
            else:
                logger.warning("No memories extracted")

            # Build response
            output = {
                "metadata": {
                    "memoriesExtracted": memories_count,
                    "source": "amplifier_extraction",
                }
            }

            logger.info(f"Session finalized with {memories_count} memories extracted")
            return success_response(output)

    except TimeoutError:
        logger.error("Memory extraction timed out after 60 seconds")
        return error_response("Memory extraction timed out", {"timeout": True})
    except Exception as e:
        logger.exception("Error during session finalization", e)
        return error_response("Session finalization failed", {"error": str(e)})


@mcp.tool()
async def health_check() -> dict[str, Any]:
    """
    Verify server is running and amplifier modules are accessible.

    Returns:
        Dictionary containing server status and module availability
    """
    try:
        logger.info("Running health check")

        # Basic server info
        project_root = get_project_root()
        amplifier_available = setup_amplifier_path(project_root)
        memory_enabled = check_memory_system_enabled()

        status = {
            "server": "session_manager",
            "project_root": str(project_root) if project_root else None,
            "amplifier_available": amplifier_available,
            "memory_enabled": memory_enabled,
        }

        # Test memory module imports if amplifier is available
        if amplifier_available:
            try:
                from amplifier.memory import MemoryStore  # noqa: F401

                status["memory_store_import"] = True
            except ImportError:
                status["memory_store_import"] = False

            try:
                from amplifier.search import MemorySearcher  # noqa: F401

                status["memory_searcher_import"] = True
            except ImportError:
                status["memory_searcher_import"] = False

            try:
                from amplifier.extraction import MemoryExtractor  # noqa: F401

                status["memory_extractor_import"] = True
            except ImportError:
                status["memory_extractor_import"] = False

        logger.info("Health check completed successfully")
        return success_response(status, {"checked_at": "now"})

    except Exception as e:
        logger.exception("Health check failed", e)
        return error_response("Health check failed", {"error": str(e)})


if __name__ == "__main__":
    logger.info("Starting Session Manager MCP Server")
    mcp.run()
