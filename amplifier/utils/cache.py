"""
Artifact cache with content fingerprinting.

Provides deterministic caching for pipeline stages to avoid reprocessing.
"""

import hashlib
import json
import time
from collections.abc import Callable
from pathlib import Path


class ArtifactCache:
    """
    Content-addressable artifact cache for pipeline results.

    Uses fingerprinting to detect when content has already been processed,
    enabling incremental processing and resume capabilities.
    """

    def __init__(self, cache_dir: Path | None = None):
        """Initialize the cache with optional custom directory."""
        self.cache_dir = cache_dir or Path(".data/artifacts")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def compute_fingerprint(
        self, content: str, stage: str, model: str | None = None, params: dict | None = None
    ) -> str:
        """
        Compute a deterministic fingerprint for content + processing parameters.

        Args:
            content: The input content to process
            stage: Pipeline stage name (e.g., "extraction", "synthesis")
            model: Model name/version if applicable
            params: Processing parameters that affect output

        Returns:
            Hex digest fingerprint string
        """
        # Create a deterministic representation
        fingerprint_data = {
            "content_hash": hashlib.sha256(content.encode()).hexdigest(),
            "stage": stage,
            "model": model,
            "params": params or {},
        }

        # Sort params for deterministic ordering
        canonical = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    def get_artifact_path(self, stage: str, fingerprint: str) -> Path:
        """Get the filesystem path for an artifact."""
        stage_dir = self.cache_dir / stage
        stage_dir.mkdir(parents=True, exist_ok=True)
        return stage_dir / f"{fingerprint}.json"

    def exists(self, stage: str, fingerprint: str) -> bool:
        """Check if an artifact exists in the cache."""
        return self.get_artifact_path(stage, fingerprint).exists()

    def load(self, stage: str, fingerprint: str) -> dict | None:
        """
        Load a cached artifact if it exists.

        Returns:
            Cached result dict or None if not found
        """
        artifact_path = self.get_artifact_path(stage, fingerprint)
        if not artifact_path.exists():
            return None

        with open(artifact_path, encoding="utf-8") as f:
            return json.load(f)

    def save(self, stage: str, fingerprint: str, result: dict) -> Path:
        """
        Save a result to the cache.

        Args:
            stage: Pipeline stage name
            fingerprint: Content fingerprint
            result: Processing result to cache

        Returns:
            Path to saved artifact
        """
        artifact_path = self.get_artifact_path(stage, fingerprint)

        # Add metadata
        artifact = {
            "fingerprint": fingerprint,
            "stage": stage,
            "result": result,
            "cached_at": time.time(),
        }

        with open(artifact_path, "w", encoding="utf-8") as f:
            json.dump(artifact, f, indent=2, ensure_ascii=False)

        return artifact_path

    def check_or_process(
        self,
        content: str,
        stage: str,
        processor_func: Callable[[str], dict],
        model: str | None = None,
        params: dict | None = None,
        force: bool = False,
    ) -> tuple[dict, bool]:
        """
        Check cache and process if needed.

        This is the main entry point for cached processing.

        Args:
            content: Input content
            stage: Pipeline stage
            processor_func: Function to call if not cached
            model: Model name for fingerprinting
            params: Processing params for fingerprinting
            force: Force reprocessing even if cached

        Returns:
            Tuple of (result, was_cached)
        """
        # Compute fingerprint
        fingerprint = self.compute_fingerprint(content, stage, model, params)

        # Check cache unless forced
        if not force:
            cached = self.load(stage, fingerprint)
            if cached:
                return cached["result"], True

        # Process and cache
        result = processor_func(content)
        self.save(stage, fingerprint, result)
        return result, False

    def clear_stage(self, stage: str) -> int:
        """
        Clear all cached artifacts for a stage.

        Returns:
            Number of artifacts removed
        """
        stage_dir = self.cache_dir / stage
        if not stage_dir.exists():
            return 0

        count = 0
        for artifact in stage_dir.glob("*.json"):
            artifact.unlink()
            count += 1

        return count

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats by stage
        """
        stats = {}

        for stage_dir in self.cache_dir.iterdir():
            if stage_dir.is_dir():
                artifacts = list(stage_dir.glob("*.json"))
                total_size = sum(a.stat().st_size for a in artifacts)
                stats[stage_dir.name] = {
                    "count": len(artifacts),
                    "size_bytes": total_size,
                    "size_mb": total_size / (1024 * 1024),
                }

        return stats


class IncrementalProcessor:
    """
    Helper for incremental processing with resume support.

    Saves results after each item to enable interruption and resume.
    """

    def __init__(self, output_file: Path, cache: ArtifactCache | None = None):
        """
        Initialize incremental processor.

        Args:
            output_file: Fixed filename for results (will be overwritten)
            cache: Optional artifact cache instance
        """
        self.output_file = output_file
        self.cache = cache or ArtifactCache()
        self.results = self._load_existing()

    def _load_existing(self) -> dict:
        """Load existing results if file exists."""
        if self.output_file.exists():
            with open(self.output_file, encoding="utf-8") as f:
                return json.load(f)
        return {"items": {}, "metadata": {}}

    def _save(self) -> None:
        """Save current results to file."""
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

    def process_item(
        self,
        item_id: str,
        content: str,
        processor_func: Callable[[str], dict],
        stage: str,
        force: bool = False,
        **kwargs,
    ) -> dict:
        """
        Process a single item with caching and incremental save.

        Args:
            item_id: Unique identifier for the item
            content: Item content to process
            processor_func: Function to process content
            stage: Pipeline stage name
            force: Force reprocessing
            **kwargs: Additional params for fingerprinting

        Returns:
            Processing result
        """
        # Check if already processed
        if not force and item_id in self.results["items"]:
            return self.results["items"][item_id]

        # Process with cache
        result, was_cached = self.cache.check_or_process(
            content=content,
            stage=stage,
            processor_func=processor_func,
            params={"item_id": item_id, **kwargs},
            force=force,
        )

        # Save incrementally
        self.results["items"][item_id] = result
        self.results["metadata"]["last_processed"] = item_id
        self._save()

        return result

    def get_pending_items(self, all_items: list[str]) -> list[str]:
        """Get list of items not yet processed."""
        processed = set(self.results["items"].keys())
        return [item for item in all_items if item not in processed]

    def get_progress(self, total: int) -> dict:
        """Get processing progress stats."""
        processed = len(self.results["items"])
        return {
            "processed": processed,
            "total": total,
            "remaining": total - processed,
            "percent": (processed / total * 100) if total > 0 else 0,
        }
