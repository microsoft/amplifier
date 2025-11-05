"""Core memory storage implementation"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import Memory
from .models import StoredMemory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
MAX_MEMORIES = 1000


class MemoryStore:
    """JSON-based memory storage with rotation and compatibility"""

    def __init__(self, data_dir: Path | None = None, max_memories: int = MAX_MEMORIES):
        """Initialize memory store

        Args:
            data_dir: Directory for data storage, defaults to .data
            max_memories: Maximum number of memories to keep
        """
        self.data_dir = data_dir or Path(".data")
        self.data_file = self.data_dir / "memory.json"
        self.max_memories = max_memories

        logger.info(f"[MEMORY STORE] Initializing with data_dir: {self.data_dir}")
        logger.info(f"[MEMORY STORE] Data file path: {self.data_file}")

        self._ensure_data_dir()
        self._data = self._load_data()
        self._memories = self._extract_memories()

        logger.info(f"[MEMORY STORE] Loaded {len(self._memories)} memories from storage")

    def add_memory(self, memory: Memory) -> StoredMemory:
        """Add a new memory to storage

        Args:
            memory: Memory to store

        Returns:
            StoredMemory with id and timestamp
        """
        stored = StoredMemory(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            content=memory.content,
            category=memory.category,
            metadata=memory.metadata,
            accessed_count=0,
        )

        logger.info(f"[MEMORY STORE] Adding memory: {stored.category} - {stored.content[:50]}...")
        self._memories[stored.id] = stored
        self._save_memories()
        logger.info(f"[MEMORY STORE] Memory added, total now: {len(self._memories)}")
        return stored

    def search_recent(self, limit: int = 10) -> list[StoredMemory]:
        """Get most recent memories

        Args:
            limit: Maximum number of memories to return

        Returns:
            List of memories sorted by timestamp (newest first)
        """
        memories = list(self._memories.values())
        memories.sort(key=lambda m: m.timestamp, reverse=True)

        # Update access count
        for memory in memories[:limit]:
            memory.accessed_count += 1
        self._save_memories()

        return memories[:limit]

    def get_by_id(self, memory_id: str) -> StoredMemory | None:
        """Get a specific memory by ID

        Args:
            memory_id: Unique identifier

        Returns:
            Memory if found, None otherwise
        """
        memory = self._memories.get(memory_id)
        if memory:
            memory.accessed_count += 1
            self._save_memories()
        return memory

    def get_all(self) -> list[StoredMemory]:
        """Get all memories

        Returns:
            All stored memories
        """
        return list(self._memories.values())

    def add_memories_batch(self, extracted: dict[str, Any]):
        """Add memories from extraction result (compatibility method)

        Args:
            extracted: Dictionary with memories and metadata from extraction
        """
        logger.info(f"[MEMORY STORE] add_memories_batch called with: {list(extracted.keys()) if extracted else 'None'}")

        if not extracted or "memories" not in extracted:
            logger.warning("[MEMORY STORE] No memories in extracted data")
            return

        memories_list = extracted.get("memories", [])
        logger.info(f"[MEMORY STORE] Processing {len(memories_list)} memories from batch")

        added_count = 0
        for i, memory_data in enumerate(memories_list):
            logger.info(f"[MEMORY STORE] Processing memory {i + 1}: {memory_data}")

            # Create Memory object
            memory = Memory(
                content=memory_data.get("content", memory_data.get("type", "")),
                category=memory_data.get("type", "pattern"),
                metadata={
                    "importance": memory_data.get("importance", 0.5),
                    "tags": memory_data.get("tags", []),
                    "extraction_method": extracted.get("metadata", {}).get("extraction_method", "unknown"),
                },
            )

            # Add memory
            self.add_memory(memory)
            added_count += 1

        # Store structured extractions
        for key in ["key_learnings", "decisions_made", "issues_solved"]:
            if key in extracted and extracted[key]:
                logger.info(f"[MEMORY STORE] Storing {len(extracted[key])} {key}")
                self._data.setdefault(key, []).extend(extracted[key])
                # Keep only last 50 of each type
                self._data[key] = self._data[key][-50:]

        # Rotate memories if needed
        self._rotate_memories()
        self._save_data()

        logger.info(
            f"[MEMORY STORE] Batch complete: Added {added_count} new memories, total now: {len(self._memories)}"
        )

    def _rotate_memories(self):
        """Rotate old memories if exceeded limit"""
        if len(self._memories) > self.max_memories:
            # Sort by access count and timestamp, keep most accessed/recent
            memories_list = list(self._memories.values())
            memories_list.sort(key=lambda m: (m.accessed_count, m.timestamp.isoformat()))

            # Remove oldest/least accessed
            to_remove = len(memories_list) - self.max_memories
            for memory in memories_list[:to_remove]:
                del self._memories[memory.id]

            logger.info(f"Rotated out {to_remove} old memories")

    # Private methods
    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist"""
        logger.info(f"[MEMORY STORE] Ensuring data directory exists: {self.data_dir}")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"[MEMORY STORE] Data directory ready: {self.data_dir.exists()}")

    def _load_data(self) -> dict[str, Any]:
        """Load full data structure from JSON file"""
        if not self.data_file.exists():
            return {"memories": [], "metadata": {"version": "2.0", "created": datetime.now().isoformat()}}

        try:
            with open(self.data_file) as f:
                data = json.load(f)
                # Migrate old format if needed
                if isinstance(data, dict) and "memories" not in data:
                    # Old format was just {id: memory}
                    return {"memories": [], "metadata": {"version": "2.0"}}
                return data
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to load memories: {e}")
            return {"memories": [], "metadata": {"version": "2.0", "created": datetime.now().isoformat()}}

    def _extract_memories(self) -> dict[str, StoredMemory]:
        """Extract memory objects from data structure"""
        memories = {}

        # Handle new format with memories list
        if "memories" in self._data and isinstance(self._data["memories"], list):
            for mem_data in self._data["memories"]:
                if "id" in mem_data:
                    try:
                        # Convert timestamp if it's a string
                        if isinstance(mem_data.get("timestamp"), str):
                            mem_data["timestamp"] = datetime.fromisoformat(mem_data["timestamp"])
                        # Handle old format with "type" instead of "category"
                        if "type" in mem_data and "category" not in mem_data:
                            mem_data["category"] = mem_data.pop("type")
                        memory = StoredMemory(**mem_data)
                        memories[memory.id] = memory
                    except Exception as e:
                        logger.warning(f"Failed to load memory: {e}")

        # Also check for direct memory storage (compatibility)
        for key, value in self._data.items():
            if key not in ["memories", "metadata", "embeddings", "key_learnings", "decisions_made", "issues_solved"]:
                try:
                    # This might be a memory ID with memory data
                    if isinstance(value, dict) and "content" in value:
                        if isinstance(value.get("timestamp"), str):
                            value["timestamp"] = datetime.fromisoformat(value["timestamp"])
                        memory = StoredMemory(id=key, **value)
                        memories[key] = memory
                except Exception:
                    pass

        return memories

    def _save_data(self):
        """Save full data structure to JSON file"""
        logger.info(f"[MEMORY STORE] Saving data to {self.data_file}")

        # Update memories in data structure
        self._data["memories"] = [memory.model_dump(mode="json") for memory in self._memories.values()]

        # Update metadata
        self._data.setdefault("metadata", {})
        self._data["metadata"]["last_updated"] = datetime.now().isoformat()
        self._data["metadata"]["count"] = len(self._memories)

        try:
            with open(self.data_file, "w") as f:
                json.dump(self._data, f, indent=2, default=str)
            logger.info(f"[MEMORY STORE] Successfully saved {len(self._memories)} memories to disk")
        except Exception as e:
            logger.error(f"[MEMORY STORE] Failed to save data: {e}")

    def _load_memories(self) -> dict:
        """Load memories from JSON file (legacy compatibility)"""
        return self._extract_memories()

    def _save_memories(self):
        """Save memories to JSON file (legacy compatibility)"""
        self._save_data()
