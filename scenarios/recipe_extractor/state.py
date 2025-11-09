"""State management for resumable recipe extraction."""

import json
from datetime import datetime
from pathlib import Path


class RecipeExtractorState:
    """Manage state for resumable recipe extraction."""

    def __init__(self, state_file: Path):
        """Initialize state manager with file path.

        Args:
            state_file: Path to state JSON file
        """
        self.state_file = state_file
        self.processed_urls: dict[str, bool] = {}
        self.failed_urls: dict[str, str] = {}
        self.session_timestamp: str = datetime.now().isoformat()
        self.load()

    def load(self):
        """Load state from JSON file if exists."""
        if self.state_file.exists():
            try:
                with open(self.state_file, encoding="utf-8") as f:
                    data = json.load(f)
                    self.processed_urls = data.get("processed_urls", {})
                    self.failed_urls = data.get("failed_urls", {})
                    self.session_timestamp = data.get("session_timestamp", self.session_timestamp)
            except (json.JSONDecodeError, OSError):
                # If file is corrupted, start fresh
                pass

    def save(self):
        """Save state to JSON file."""
        # Create parent directories if needed
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "session_timestamp": self.session_timestamp,
            "processed_urls": self.processed_urls,
            "failed_urls": self.failed_urls,
        }

        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def is_processed(self, url: str) -> bool:
        """Check if URL already processed successfully.

        Args:
            url: Recipe URL

        Returns:
            True if URL was successfully processed, False otherwise
        """
        return url in self.processed_urls

    def mark_processed(self, url: str):
        """Mark URL as successfully processed.

        Args:
            url: Recipe URL
        """
        self.processed_urls[url] = True
        # Remove from failed if it was there
        self.failed_urls.pop(url, None)
        self.save()

    def mark_failed(self, url: str, error: str):
        """Mark URL as failed with error message.

        Args:
            url: Recipe URL
            error: Error message describing failure
        """
        self.failed_urls[url] = error
        self.save()
