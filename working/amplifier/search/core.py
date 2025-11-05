"""Semantic search for memories"""

import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from memory.models import StoredMemory

from .models import SearchResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import sentence transformers
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer

    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    SentenceTransformer = None  # type: ignore
    np = None  # type: ignore


class MemorySearcher:
    """Search memories using semantic similarity or keywords"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", data_dir: Path | None = None):
        """Initialize searcher

        Args:
            model_name: Sentence transformer model to use
            data_dir: Directory for embedding storage
        """
        self.model_name = model_name
        self.model = None
        self.data_dir = data_dir or Path(".data")
        self.embeddings_file = self.data_dir / "embeddings.json"
        self.embeddings = self._load_embeddings()

        if EMBEDDINGS_AVAILABLE:
            try:
                self.model = SentenceTransformer(model_name)  # type: ignore
                logger.info(f"Loaded embedding model: {model_name}")
            except Exception as e:
                logger.warning(f"Failed to load embedding model: {e}")

    def search(self, query: str, memories: list[StoredMemory], limit: int = 10) -> list[SearchResult]:
        """Search memories by query

        Args:
            query: Search query
            memories: List of memories to search
            limit: Maximum results to return

        Returns:
            Sorted list of search results
        """
        if not memories:
            return []

        # Try semantic search first
        if self.model is not None and EMBEDDINGS_AVAILABLE:
            results = self._semantic_search(query, memories, limit)
            if results:
                return results

        # Fallback to keyword search
        return self._keyword_search(query, memories, limit)

    def _semantic_search(self, query: str, memories: list[StoredMemory], limit: int) -> list[SearchResult]:
        """Search using semantic similarity"""
        try:
            # Encode query
            query_embedding = self.model.encode(query, convert_to_numpy=True)  # type: ignore

            # Encode all memory contents
            memory_texts = [m.content for m in memories]
            memory_embeddings = self.model.encode(memory_texts, convert_to_numpy=True)  # type: ignore

            # Calculate cosine similarities
            similarities = np.dot(memory_embeddings, query_embedding) / (  # type: ignore
                np.linalg.norm(memory_embeddings, axis=1) * np.linalg.norm(query_embedding)  # type: ignore
            )

            # Create results with scores
            results = []
            for memory, score in zip(memories, similarities, strict=False):
                results.append(SearchResult(memory=memory, score=float(score), match_type="semantic"))

            # Sort by score and return top results
            results.sort(key=lambda r: r.score, reverse=True)
            return results[:limit]

        except Exception as e:
            print(f"Semantic search failed: {e}")
            return []

    def _keyword_search(self, query: str, memories: list[StoredMemory], limit: int) -> list[SearchResult]:
        """Fallback keyword search"""
        query_lower = query.lower()
        query_words = set(query_lower.split())

        results = []
        for memory in memories:
            content_lower = memory.content.lower()
            content_words = set(content_lower.split())

            # Calculate simple overlap score
            overlap = query_words.intersection(content_words)
            if overlap:
                score = len(overlap) / max(len(query_words), 1)
                results.append(SearchResult(memory=memory, score=score, match_type="keyword"))

        # Sort by score and return top results
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def generate_embedding(self, text: str) -> list[float] | None:
        """Generate embedding for text

        Args:
            text: Text to embed

        Returns:
            Embedding vector or None if not available
        """
        if self.model is None or not EMBEDDINGS_AVAILABLE:
            return None

        try:
            embedding = self.model.encode(text, convert_to_numpy=True)  # type: ignore
            return embedding.tolist()  # type: ignore
        except Exception as e:
            logger.warning(f"Failed to generate embedding: {e}")
            return None

    def store_embedding(self, memory_id: str, embedding: list[float]):
        """Store an embedding for a memory

        Args:
            memory_id: ID of the memory
            embedding: Embedding vector
        """
        self.embeddings[memory_id] = embedding
        self._save_embeddings()

    def get_embedding(self, memory_id: str) -> list[float] | None:
        """Get stored embedding for a memory

        Args:
            memory_id: ID of the memory

        Returns:
            Embedding vector or None if not found
        """
        return self.embeddings.get(memory_id)

    def _load_embeddings(self) -> dict[str, list[float]]:
        """Load embeddings from storage"""
        if not self.embeddings_file.exists():
            return {}

        try:
            import json

            with open(self.embeddings_file) as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load embeddings: {e}")
            return {}

    def _save_embeddings(self):
        """Save embeddings to storage"""
        try:
            import json

            self.data_dir.mkdir(parents=True, exist_ok=True)
            with open(self.embeddings_file, "w") as f:
                json.dump(self.embeddings, f)
        except Exception as e:
            logger.error(f"Failed to save embeddings: {e}")

    def rerank(self, query: str, results: list[SearchResult]) -> list[SearchResult]:
        """Rerank existing results for better relevance

        Args:
            query: Original search query
            results: Previous search results

        Returns:
            Reranked results
        """
        # For now, just return as-is
        # Could add more sophisticated reranking later
        return results
