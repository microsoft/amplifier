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
        # Create test data directory
        self.test_data_dir.mkdir(exist_ok=True)

        # Create sample data files
        sample_article = self.test_data_dir / "test_article.md"
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
        sample_code.write_text("""# Test Python file
def hello_world():
    \"\"\"Sample function for testing.\"\"\"
    return "Hello, World!"

if __name__ == "__main__":
    print(hello_world())
""")

    def cleanup_test_environment(self) -> None:
        """Clean up test environment after tests."""
        import shutil

        if self.test_data_dir.exists():
            shutil.rmtree(self.test_data_dir)

    def get_test_env(self) -> dict:
        """Get environment variables for test execution."""
        env = os.environ.copy()
        # Override data directories to use test data
        env["AMPLIFIER_DATA_DIR"] = str(self.test_data_dir / "data")
        env["AMPLIFIER_CONTENT_DIRS"] = str(self.test_data_dir)
        env["PYTHONPATH"] = str(Path.cwd())
        return env


# Global instance
config = SmokeTestConfig()
