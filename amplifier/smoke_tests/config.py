"""
Smoke Test Configuration Module

Configuration for isolated test environments.
"""

import os
from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class SmokeTestConfig(BaseSettings):
    """Configuration for smoke test execution."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SMOKE_TEST_",
        case_sensitive=False,
        extra="ignore",
    )

    # Model selection (default to fast for smoke tests)
    model_category: str = "fast"

    # Test data directory
    test_data_dir: Path = Path(".smoke_test_data")

    # Skip tests when AI unavailable
    skip_on_ai_unavailable: bool = True

    # AI evaluation timeout
    ai_timeout: int = 30

    # Maximum output to send to AI
    max_output_chars: int = 5000

    def setup_test_environment(self) -> None:
        """Setup isolated test environment."""
        import json
        import time

        # Create test data directory
        self.test_data_dir.mkdir(exist_ok=True)

        # Create data subdirectory for amplifier data
        data_dir = self.test_data_dir / "data"
        data_dir.mkdir(exist_ok=True)

        # Create knowledge directory for test extractions
        knowledge_dir = data_dir / "knowledge"
        knowledge_dir.mkdir(exist_ok=True)

        # Create a dummy Makefile for workspace discovery
        test_makefile = self.test_data_dir / "Makefile"
        if not test_makefile.exists():
            test_makefile.write_text("""# Test project Makefile
.DEFAULT_GOAL := help

help:
	@echo "Test project for smoke testing"

test:
	@echo "Running tests..."
""")

        # Create sample knowledge extractions
        extractions_file = knowledge_dir / "extractions.jsonl"
        if not extractions_file.exists():
            # Create sample extraction data
            sample_extraction = {
                "source_id": "test_article_001",
                "title": "Test Article",
                "concepts": [
                    {"name": "Testing", "description": "The process of validating software functionality"},
                    {"name": "Smoke Testing", "description": "Basic tests to ensure core functionality works"},
                    {"name": "Amplifier", "description": "A knowledge synthesis and amplification system"},
                ],
                "relationships": [
                    {"subject": "Smoke Testing", "predicate": "validates", "object": "Core Functionality"},
                    {"subject": "Amplifier", "predicate": "uses", "object": "Knowledge Synthesis"},
                ],
                "insights": [
                    "Smoke tests provide quick validation of basic functionality",
                    "Amplifier helps synthesize knowledge from various sources",
                ],
                "timestamp": time.time(),
            }

            # Write the extraction to JSONL file
            with open(extractions_file, "w", encoding="utf-8") as f:
                f.write(json.dumps(sample_extraction, ensure_ascii=False) + "\n")

        # Create sample events file for knowledge pipeline
        events_file = knowledge_dir / "events.jsonl"
        if not events_file.exists():
            # Create sample event data
            events = [
                {
                    "event": "sync_started",
                    "stage": "sync",
                    "timestamp": time.time() - 100,
                    "data": {"total": 1, "max": None},
                },
                {
                    "event": "extraction_started",
                    "stage": "extract",
                    "source_id": "test_article_001",
                    "timestamp": time.time() - 90,
                    "data": {"title": "Test Article"},
                },
                {
                    "event": "extraction_succeeded",
                    "stage": "extract",
                    "source_id": "test_article_001",
                    "timestamp": time.time() - 80,
                    "data": {"title": "Test Article", "concepts": 3, "relationships": 2, "insights": 2},
                },
                {
                    "event": "sync_finished",
                    "stage": "sync",
                    "timestamp": time.time() - 70,
                    "data": {"processed": 1, "skipped": 0, "total": 1},
                },
            ]

            # Write events to JSONL file
            with open(events_file, "w", encoding="utf-8") as f:
                for event in events:
                    f.write(json.dumps(event, ensure_ascii=False) + "\n")

        # Only create sample data files if they don't exist
        sample_article = self.test_data_dir / "test_article.md"
        if not sample_article.exists():
            sample_article.write_text("""# Test Article

This is a test article for smoke testing.

## Key Points
- First important point
- Second important point
- Third important point

## Conclusion
This is the conclusion of the test article.
""")

        sample_code = self.test_data_dir / "test_code.py"
        if not sample_code.exists():
            sample_code.write_text("""# Test Python file
def hello_world():
    \"\"\"Sample function for testing.\"\"\"
    return "Hello, World!"

if __name__ == "__main__":
    print(hello_world())
""")

    def cleanup_test_environment(self) -> None:
        """Clean up test environment after tests."""
        # Don't delete the test data directory - we want to preserve test data
        # Clean up any temporary files created during tests
        import shutil

        # Clean up any __pycache__ directories that might have been created
        for cache_dir in self.test_data_dir.rglob("__pycache__"):
            if cache_dir.is_dir():
                shutil.rmtree(cache_dir)

        # Clean up any .pyc files
        for pyc_file in self.test_data_dir.rglob("*.pyc"):
            if pyc_file.is_file():
                pyc_file.unlink()

    def get_test_env(self) -> dict:
        """Get environment variables for test execution."""
        env = os.environ.copy()
        # Override data directories to use test data
        env["AMPLIFIER_DATA_DIR"] = str(self.test_data_dir / "data")
        env["AMPLIFIER_CONTENT_DIRS"] = str(self.test_data_dir)
        env["PYTHONPATH"] = str(Path.cwd())

        # Set model to use fast model for testing
        env["AMPLIFIER_MODEL_CATEGORY"] = "fast"

        # Ensure test data directory is absolute
        env["SMOKE_TEST_TEST_DATA_DIR"] = str(self.test_data_dir.absolute())

        # Skip AI evaluation if SDK not available
        env["SMOKE_TEST_SKIP_ON_AI_UNAVAILABLE"] = "true"

        return env


# Global instance
config = SmokeTestConfig()
