#!/usr/bin/env python3
"""
Configuration for Knowledge Mining system.
Supports environment variables and .env files with sensible defaults.
"""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

from amplifier.config.paths import paths

# Document type definitions
DocumentType = Literal[
    "article",  # Formal article, research paper, or technical documentation
    "api_docs",  # API documentation, endpoint descriptions, integration guides
    "meeting",  # Meeting notes, transcripts, discussion summaries
    "blog",  # Blog post, personal narrative, informal writing
    "tutorial",  # Step-by-step guides, how-to documentation
    "research",  # Academic papers, studies, white papers
    "changelog",  # Release notes, version updates, migration guides
    "readme",  # Project documentation, setup guides
    "specification",  # RFCs, technical specifications, standards
    "conversation",  # Chat logs, interviews, Q&A sessions
    "code_review",  # PR reviews, code feedback, architecture discussions
    "post_mortem",  # Incident analysis, lessons learned
    "general",  # Doesn't clearly fit other categories
]

VALID_DOCUMENT_TYPES = [
    "article",
    "api_docs",
    "meeting",
    "blog",
    "tutorial",
    "research",
    "changelog",
    "readme",
    "specification",
    "conversation",
    "code_review",
    "post_mortem",
    "general",
]


class KnowledgeMiningConfig(BaseSettings):
    """Configuration for Knowledge Mining system with environment variable support"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")

    # Model configuration
    knowledge_mining_model: str = Field(
        default="claude-3-5-haiku-20241022", description="Model for document classification (fast, efficient)"
    )

    knowledge_mining_extraction_model: str = Field(
        default="claude-sonnet-4-20250514", description="Model for knowledge extraction (powerful, thorough)"
    )

    # Content limits
    knowledge_mining_max_chars: int = Field(
        default=50000, description="Maximum characters to process from a document (~8000 words)"
    )

    knowledge_mining_classification_chars: int = Field(
        default=1500, description="Characters to use for document classification"
    )

    # Storage configuration
    knowledge_mining_storage_dir: Path = Field(
        default_factory=lambda: paths.data_dir / "knowledge_mining",
        description="Directory for storing knowledge mining data",
    )

    # Defaults
    knowledge_mining_default_doc_type: DocumentType = Field(
        default="general", description="Default document type when classification fails"
    )

    # API Keys (optional - SDK may provide these)
    anthropic_api_key: str | None = Field(
        default=None, description="Anthropic API key (optional, Claude Code SDK may provide)"
    )

    def ensure_storage_dir(self) -> Path:
        """Ensure storage directory exists and return it"""
        self.knowledge_mining_storage_dir.mkdir(parents=True, exist_ok=True)
        return self.knowledge_mining_storage_dir

    def get_valid_document_types(self) -> list[str]:
        """Return list of valid document types"""
        return VALID_DOCUMENT_TYPES.copy()


# Singleton instance
_config: KnowledgeMiningConfig | None = None


def get_config() -> KnowledgeMiningConfig:
    """Get or create the configuration singleton"""
    global _config
    if _config is None:
        _config = KnowledgeMiningConfig()
    return _config


def reset_config() -> None:
    """Reset configuration (useful for testing)"""
    global _config
    _config = None
