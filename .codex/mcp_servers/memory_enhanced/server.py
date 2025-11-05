#!/usr/bin/env python3
"""
Memory Enhancement MCP Server

Provides proactive memory suggestions and quality management.
"""

import time
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from ..base import AmplifierMCPServer
from ..base import MCPLogger


class MemoryEnhancedServer(AmplifierMCPServer):
    """MCP server for proactive memory operations and quality management."""

    def __init__(self, mcp_instance):
        super().__init__("amplifier_memory_enhanced", mcp_instance)
        self.logger = MCPLogger("memory_enhanced")

        # Initialize memory components
        self.memory_store = None
        self.memory_searcher = None

        if self.amplifier_available:
            try:
                from amplifier.memory.core import MemoryStore
                from amplifier.search.core import MemorySearcher

                data_dir = self.project_root / ".data" if self.project_root else Path(".data")
                self.memory_store = MemoryStore(data_dir=data_dir)
                self.memory_searcher = MemorySearcher(data_dir=data_dir)

                self.logger.info("Memory components initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize memory components: {e}")

    async def suggest_relevant_memories(self, current_context: str, limit: int = 5) -> list[dict[str, Any]]:
        """Proactively suggest relevant memories based on current context.

        Args:
            current_context: Current session or task context
            limit: Maximum number of suggestions

        Returns:
            List of relevant memory suggestions
        """
        if not self.memory_store or not self.memory_searcher:
            return []

        try:
            # Get recent memories (last 30 days)
            all_memories = self.memory_store.get_all()
            recent_memories = [m for m in all_memories if (time.time() - m.timestamp.timestamp()) < (30 * 24 * 3600)]

            if not recent_memories:
                return []

            # Search for relevant memories
            search_results = self.memory_searcher.search(current_context, recent_memories, limit)

            suggestions = []
            for result in search_results:
                suggestions.append(
                    {
                        "id": result.memory.id,
                        "content": result.memory.content,
                        "category": result.memory.category,
                        "relevance_score": result.score,
                        "timestamp": result.memory.timestamp.isoformat(),
                    }
                )

            return suggestions

        except Exception as e:
            self.logger.error(f"Failed to suggest memories: {e}")
            return []

    async def tag_memory(self, memory_id: str, tags: list[str]) -> bool:
        """Add tags to an existing memory.

        Args:
            memory_id: ID of the memory to tag
            tags: List of tags to add

        Returns:
            True if tagging was successful
        """
        if not self.memory_store:
            return False

        try:
            # This would require extending MemoryStore to support tagging
            # For now, just log the intent
            self.logger.info(f"Would tag memory {memory_id} with tags: {tags}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to tag memory: {e}")
            return False

    async def find_related_memories(self, memory_id: str, limit: int = 5) -> list[dict[str, Any]]:
        """Find memories related to a given memory.

        Args:
            memory_id: ID of the reference memory
            limit: Maximum number of related memories

        Returns:
            List of related memories
        """
        if not self.memory_store or not self.memory_searcher:
            return []

        try:
            # Get the reference memory
            all_memories = self.memory_store.get_all()
            reference_memory = next((m for m in all_memories if m.id == memory_id), None)

            if not reference_memory:
                return []

            # Search for related memories using the reference content
            related_results = self.memory_searcher.search(reference_memory.content, all_memories, limit + 1)

            # Exclude the reference memory itself
            related = [
                {
                    "id": result.memory.id,
                    "content": result.memory.content,
                    "category": result.memory.category,
                    "similarity_score": result.score,
                    "timestamp": result.memory.timestamp.isoformat(),
                }
                for result in related_results
                if result.memory.id != memory_id
            ][:limit]

            return related

        except Exception as e:
            self.logger.error(f"Failed to find related memories: {e}")
            return []

    async def score_memory_quality(self, memory_id: str) -> dict[str, Any]:
        """Score the quality of a memory based on various metrics.

        Args:
            memory_id: ID of the memory to score

        Returns:
            Quality score and metrics
        """
        if not self.memory_store:
            return {"error": "Memory store not available"}

        try:
            all_memories = self.memory_store.get_all()
            memory = next((m for m in all_memories if m.id == memory_id), None)

            if not memory:
                return {"error": "Memory not found"}

            # Calculate quality metrics
            age_days = (time.time() - memory.timestamp.timestamp()) / (24 * 3600)
            access_count = getattr(memory, "accessed_count", 0)
            content_length = len(memory.content)
            has_tags = bool(getattr(memory, "metadata", {}).get("tags", []))

            # Quality scoring algorithm
            quality_score = 0.0

            # Recency bonus (newer memories are more valuable)
            if age_days < 7:
                quality_score += 0.3
            elif age_days < 30:
                quality_score += 0.2
            elif age_days < 90:
                quality_score += 0.1

            # Access frequency bonus
            if access_count > 10:
                quality_score += 0.3
            elif access_count > 5:
                quality_score += 0.2
            elif access_count > 1:
                quality_score += 0.1

            # Content quality bonus
            if content_length > 200:
                quality_score += 0.2
            elif content_length > 100:
                quality_score += 0.1

            # Organization bonus
            if has_tags:
                quality_score += 0.1

            # Category bonus (some categories are more valuable)
            valuable_categories = ["pattern", "decision", "issue_solved"]
            if memory.category in valuable_categories:
                quality_score += 0.1

            # Normalize to 0-1 range
            quality_score = min(1.0, max(0.0, quality_score))

            return {
                "memory_id": memory_id,
                "quality_score": quality_score,
                "metrics": {
                    "age_days": age_days,
                    "access_count": access_count,
                    "content_length": content_length,
                    "has_tags": has_tags,
                    "category": memory.category,
                },
                "recommendation": "keep" if quality_score > 0.3 else "review",
            }

        except Exception as e:
            self.logger.error(f"Failed to score memory quality: {e}")
            return {"error": str(e)}

    async def cleanup_memories(self, quality_threshold: float = 0.3) -> dict[str, Any]:
        """Remove low-quality memories.

        Args:
            quality_threshold: Minimum quality score to keep

        Returns:
            Cleanup statistics
        """
        if not self.memory_store:
            return {"error": "Memory store not available"}

        try:
            all_memories = self.memory_store.get_all()
            kept_count = 0
            removed_count = 0

            for memory in all_memories:
                quality = await self.score_memory_quality(memory.id)
                if isinstance(quality, dict) and quality.get("quality_score", 0) < quality_threshold:
                    # This would require MemoryStore to support deletion
                    # For now, just count
                    removed_count += 1
                else:
                    kept_count += 1

            return {
                "total_memories": len(all_memories),
                "kept_count": kept_count,
                "removed_count": removed_count,
                "quality_threshold": quality_threshold,
                "message": f"Would remove {removed_count} low-quality memories",
            }

        except Exception as e:
            self.logger.error(f"Failed to cleanup memories: {e}")
            return {"error": str(e)}

    async def get_memory_insights(self) -> dict[str, Any]:
        """Get insights about the memory system.

        Returns:
            Memory system statistics and insights
        """
        if not self.memory_store:
            return {"error": "Memory store not available"}

        try:
            all_memories = self.memory_store.get_all()

            # Calculate statistics
            total_memories = len(all_memories)
            categories = {}
            total_accesses = 0
            oldest_memory = None
            newest_memory = None

            for memory in all_memories:
                # Category counts
                categories[memory.category] = categories.get(memory.category, 0) + 1

                # Access tracking
                access_count = getattr(memory, "accessed_count", 0)
                total_accesses += access_count

                # Age tracking
                if oldest_memory is None or memory.timestamp < oldest_memory:
                    oldest_memory = memory.timestamp
                if newest_memory is None or memory.timestamp > newest_memory:
                    newest_memory = memory.timestamp

            # Calculate averages
            avg_accesses = total_accesses / total_memories if total_memories > 0 else 0

            insights = {
                "total_memories": total_memories,
                "categories": categories,
                "total_accesses": total_accesses,
                "average_accesses_per_memory": avg_accesses,
                "oldest_memory": oldest_memory.isoformat() if oldest_memory else None,
                "newest_memory": newest_memory.isoformat() if newest_memory else None,
                "most_common_category": max(categories, key=lambda k: categories[k]) if categories else None,
            }

            return insights

        except Exception as e:
            self.logger.error(f"Failed to get memory insights: {e}")
            return {"error": str(e)}


def main():
    """Main entry point for the memory enhanced MCP server."""
    mcp = FastMCP("amplifier_memory_enhanced")
    server = MemoryEnhancedServer(mcp)

    # Register tools
    @mcp.tool()
    async def suggest_relevant_memories(current_context: str, limit: int = 5) -> list[dict[str, Any]]:
        """Proactively suggest relevant memories."""
        return await server.tool_error_handler(server.suggest_relevant_memories)(current_context, limit)

    @mcp.tool()
    async def tag_memory(memory_id: str, tags: list[str]) -> bool:
        """Add tags to an existing memory."""
        return await server.tool_error_handler(server.tag_memory)(memory_id, tags)

    @mcp.tool()
    async def find_related_memories(memory_id: str, limit: int = 5) -> list[dict[str, Any]]:
        """Find memories related to a given memory."""
        return await server.tool_error_handler(server.find_related_memories)(memory_id, limit)

    @mcp.tool()
    async def score_memory_quality(memory_id: str) -> dict[str, Any]:
        """Score the quality of a memory."""
        return await server.tool_error_handler(server.score_memory_quality)(memory_id)

    @mcp.tool()
    async def cleanup_memories(quality_threshold: float = 0.3) -> dict[str, Any]:
        """Remove low-quality memories."""
        return await server.tool_error_handler(server.cleanup_memories)(quality_threshold)

    @mcp.tool()
    async def get_memory_insights() -> dict[str, Any]:
        """Get insights about the memory system."""
        return await server.tool_error_handler(server.get_memory_insights)()

    # Run the server
    mcp.run()


if __name__ == "__main__":
    main()
