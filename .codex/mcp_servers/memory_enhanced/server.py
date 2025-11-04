"""
Enhanced memory MCP server for mid-session memory operations.
Provides tools for searching, saving, and extracting memories during active sessions.
"""

import asyncio
import sys
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import FastMCP
try:
    from fastmcp import FastMCP
except ImportError:
    raise RuntimeError("FastMCP not available. Install with: pip install fastmcp")

# Import base utilities  # noqa: E402
from base import AmplifierMCPServer  # noqa: E402
from base import error_response  # noqa: E402
from base import success_response  # noqa: E402

# Import amplifier modules (with fallbacks)
try:
    from amplifier.extraction.core import MemoryExtractor
    from amplifier.memory.core import MemoryStore
    from amplifier.search.core import MemorySearcher

    AMPLIFIER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Amplifier modules not available: {e}", file=sys.stderr)
    MemoryStore = None
    MemorySearcher = None
    MemoryExtractor = None
    AMPLIFIER_AVAILABLE = False


class MemoryEnhancedServer(AmplifierMCPServer):
    """MCP server for enhanced memory operations during active sessions"""

    def __init__(self):
        # Initialize FastMCP
        mcp = FastMCP("amplifier-memory-enhanced")

        # Call parent constructor
        super().__init__("memory_enhanced", mcp)

        # Initialize memory components if available
        self.memory_store = None
        self.memory_searcher = None
        self.memory_extractor = None

        if AMPLIFIER_AVAILABLE and self.amplifier_available:
            try:
                # Initialize memory store
                data_dir = self.project_root / ".data" if self.project_root else Path(".data")
                self.memory_store = MemoryStore(data_dir=data_dir)

                # Initialize memory searcher
                self.memory_searcher = MemorySearcher(data_dir=data_dir)

                # Initialize memory extractor (only if Claude SDK available)
                try:
                    self.memory_extractor = MemoryExtractor()
                except RuntimeError as e:
                    self.logger.warning(f"Memory extractor not available: {e}")

                self.logger.info("Memory components initialized successfully")

            except Exception as e:
                self.logger.error(f"Failed to initialize memory components: {e}")
                self.memory_store = None
                self.memory_searcher = None
                self.memory_extractor = None
        else:
            self.logger.warning("Amplifier modules not available, memory operations disabled")

        # Register tools
        self._register_memory_tools()

    def _register_memory_tools(self):
        """Register all memory-related tools"""

        @self.mcp.tool()
        @self.tool_error_handler
        async def search_memories(query: str, limit: int = 5, category: str | None = None) -> dict[str, Any]:
            """Search memories mid-session using semantic or keyword search

            Args:
                query: Search query string
                limit: Maximum number of results to return (default: 5)
                category: Optional category filter (learning, decision, issue_solved, pattern, preference)

            Returns:
                Dictionary with search results and metadata
            """
            if not self._check_memory_components():
                return error_response("Memory system not available")

            try:
                # Validate inputs
                if not query or not query.strip():
                    return error_response("Query cannot be empty")

                if limit < 1 or limit > 50:
                    return error_response("Limit must be between 1 and 50")

                # Get all memories
                all_memories = self.memory_store.get_all()

                # Filter by category if specified
                if category:
                    valid_categories = ["learning", "decision", "issue_solved", "pattern", "preference"]
                    if category not in valid_categories:
                        return error_response(f"Invalid category. Must be one of: {', '.join(valid_categories)}")
                    all_memories = [m for m in all_memories if m.category == category]

                if not all_memories:
                    return success_response([], {"query": query, "total_found": 0})

                # Perform search
                search_results = self.memory_searcher.search(query, all_memories, limit)

                # Format results
                results = []
                for result in search_results:
                    results.append(
                        {
                            "id": result.memory.id,
                            "content": result.memory.content,
                            "category": result.memory.category,
                            "score": result.score,
                            "match_type": result.match_type,
                            "timestamp": result.memory.timestamp.isoformat(),
                            "accessed_count": result.memory.accessed_count,
                        }
                    )

                metadata = {
                    "query": query,
                    "category_filter": category,
                    "total_searched": len(all_memories),
                    "results_returned": len(results),
                    "search_timestamp": datetime.now().isoformat(),
                }

                return success_response(results, metadata)

            except Exception as e:
                self.logger.exception("Search memories failed", e)
                return error_response(f"Search failed: {str(e)}")

        @self.mcp.tool()
        @self.tool_error_handler
        async def save_memory(
            content: str, category: str, tags: list[str] | None = None, importance: float = 0.5
        ) -> dict[str, Any]:
            """Capture insight immediately as a memory

            Args:
                content: The memory content to save
                category: Category (learning, decision, issue_solved, pattern, preference)
                tags: Optional list of tags
                importance: Importance score 0.0-1.0 (default: 0.5)

            Returns:
                Dictionary with saved memory info and metadata
            """
            if not self._check_memory_components():
                return error_response("Memory system not available")

            try:
                # Validate inputs
                validation_error = self._validate_memory_input(content, category, importance)
                if validation_error:
                    return validation_error

                # Prepare tags
                if tags is None:
                    tags = []

                # Create memory object
                from amplifier.memory.models import Memory

                memory = Memory(
                    content=content.strip(),
                    category=category,
                    metadata={
                        "importance": importance,
                        "tags": tags,
                        "source": "mid_session_capture",
                        "created_via": "memory_enhanced_mcp",
                    },
                )

                # Save memory
                stored_memory = self.memory_store.add_memory(memory)

                result = {
                    "id": stored_memory.id,
                    "content": stored_memory.content,
                    "category": stored_memory.category,
                    "importance": stored_memory.metadata.get("importance", 0.5),
                    "tags": stored_memory.metadata.get("tags", []),
                    "timestamp": stored_memory.timestamp.isoformat(),
                }

                metadata = {
                    "operation": "save_memory",
                    "saved_at": datetime.now().isoformat(),
                    "total_memories": len(self.memory_store.get_all()),
                }

                self.logger.info(f"Saved memory: {stored_memory.id} - {stored_memory.category}")
                return success_response(result, metadata)

            except Exception as e:
                self.logger.exception("Save memory failed", e)
                return error_response(f"Save failed: {str(e)}")

        @self.mcp.tool()
        @self.tool_error_handler
        async def extract_discoveries(transcript_snippet: str) -> dict[str, Any]:
            """Extract learnings and discoveries from recent conversation

            Args:
                transcript_snippet: Recent conversation text to analyze

            Returns:
                Dictionary with extracted discoveries and metadata
            """
            if not self._check_memory_components() or not self.memory_extractor:
                return error_response("Memory extraction system not available")

            try:
                if not transcript_snippet or not transcript_snippet.strip():
                    return error_response("Transcript snippet cannot be empty")

                # Extract memories from transcript
                memories = await asyncio.wait_for(
                    self.memory_extractor.extract_memories(transcript_snippet),
                    timeout=60.0,  # 60 second timeout
                )

                # Save extracted memories
                saved_memories = []
                for memory in memories:
                    stored = self.memory_store.add_memory(memory)
                    saved_memories.append(
                        {
                            "id": stored.id,
                            "content": stored.content,
                            "category": stored.category,
                            "importance": stored.metadata.get("importance", 0.5),
                            "timestamp": stored.timestamp.isoformat(),
                        }
                    )

                metadata = {
                    "operation": "extract_discoveries",
                    "transcript_length": len(transcript_snippet),
                    "memories_extracted": len(saved_memories),
                    "extraction_timestamp": datetime.now().isoformat(),
                }

                self.logger.info(f"Extracted {len(saved_memories)} discoveries from transcript")
                return success_response(saved_memories, metadata)

            except TimeoutError:
                return error_response("Discovery extraction timed out after 60 seconds")
            except Exception as e:
                self.logger.exception("Extract discoveries failed", e)
                return error_response(f"Extraction failed: {str(e)}")

        @self.mcp.tool()
        @self.tool_error_handler
        async def get_recent_context(days: int = 7) -> dict[str, Any]:
            """Get recent work summary and context

            Args:
                days: Number of days to look back (default: 7)

            Returns:
                Dictionary with recent memories and summary statistics
            """
            if not self._check_memory_components():
                return error_response("Memory system not available")

            try:
                if days < 1 or days > 365:
                    return error_response("Days must be between 1 and 365")

                # Calculate cutoff date
                cutoff_date = datetime.now() - timedelta(days=days)

                # Get all memories and filter by date
                all_memories = self.memory_store.get_all()
                recent_memories = [m for m in all_memories if m.timestamp >= cutoff_date]

                # Sort by timestamp (newest first)
                recent_memories.sort(key=lambda m: m.timestamp, reverse=True)

                # Generate summary statistics
                categories = {}
                total_importance = 0

                for memory in recent_memories:
                    cat = memory.category
                    categories[cat] = categories.get(cat, 0) + 1
                    total_importance += memory.metadata.get("importance", 0.5)

                summary = {
                    "total_memories": len(recent_memories),
                    "categories": categories,
                    "average_importance": total_importance / len(recent_memories) if recent_memories else 0,
                    "date_range": {"from": cutoff_date.isoformat(), "to": datetime.now().isoformat()},
                }

                # Format recent memories (limit to 20 most recent)
                formatted_memories = []
                for memory in recent_memories[:20]:
                    formatted_memories.append(
                        {
                            "id": memory.id,
                            "content": memory.content,
                            "category": memory.category,
                            "importance": memory.metadata.get("importance", 0.5),
                            "timestamp": memory.timestamp.isoformat(),
                            "tags": memory.metadata.get("tags", []),
                        }
                    )

                result = {"summary": summary, "recent_memories": formatted_memories}

                metadata = {
                    "operation": "get_recent_context",
                    "days_requested": days,
                    "memories_returned": len(formatted_memories),
                    "generated_at": datetime.now().isoformat(),
                }

                return success_response(result, metadata)

            except Exception as e:
                self.logger.exception("Get recent context failed", e)
                return error_response(f"Context retrieval failed: {str(e)}")

        @self.mcp.tool()
        @self.tool_error_handler
        async def update_discoveries_file(discovery_text: str) -> dict[str, Any]:
            """Append new discovery to DISCOVERIES.md file

            Args:
                discovery_text: The discovery text to append

            Returns:
                Dictionary with update status and metadata
            """
            try:
                if not discovery_text or not discovery_text.strip():
                    return error_response("Discovery text cannot be empty")

                # Find DISCOVERIES.md file
                discoveries_file = None
                if self.project_root:
                    discoveries_file = self.project_root / "DISCOVERIES.md"

                if not discoveries_file or not discoveries_file.exists():
                    return error_response("DISCOVERIES.md file not found in project root")

                # Prepare discovery entry
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                entry = f"\n## {timestamp}\n\n{discovery_text.strip()}\n"

                # Append to file
                with open(discoveries_file, "a") as f:
                    f.write(entry)

                # Get file stats
                stat = discoveries_file.stat()

                result = {
                    "file_path": str(discoveries_file),
                    "discovery_added": discovery_text.strip(),
                    "timestamp": timestamp,
                    "file_size_bytes": stat.st_size,
                }

                metadata = {"operation": "update_discoveries_file", "appended_at": datetime.now().isoformat()}

                self.logger.info(f"Added discovery to DISCOVERIES.md: {len(discovery_text)} chars")
                return success_response(result, metadata)

            except Exception as e:
                self.logger.exception("Update discoveries file failed", e)
                return error_response(f"File update failed: {str(e)}")

    def _check_memory_components(self) -> bool:
        """Check if memory components are available"""
        return self.memory_store is not None and self.memory_searcher is not None and AMPLIFIER_AVAILABLE

    def _validate_memory_input(self, content: str, category: str, importance: float) -> dict[str, Any] | None:
        """Validate memory input parameters"""
        if not content or not content.strip():
            return error_response("Content cannot be empty")

        if len(content.strip()) < 10:
            return error_response("Content must be at least 10 characters long")

        if len(content.strip()) > 2000:
            return error_response("Content must be less than 2000 characters long")

        valid_categories = ["learning", "decision", "issue_solved", "pattern", "preference"]
        if category not in valid_categories:
            return error_response(f"Invalid category. Must be one of: {', '.join(valid_categories)}")

        if not isinstance(importance, int | float) or importance < 0.0 or importance > 1.0:
            return error_response("Importance must be a number between 0.0 and 1.0")

        return None


def main():
    """Main entry point for the memory enhanced MCP server"""
    server = MemoryEnhancedServer()
    server.run()


if __name__ == "__main__":
    main()
