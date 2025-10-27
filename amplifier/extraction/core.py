"""Memory extraction from conversations"""

import asyncio
import json
import logging
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).parent.parent))
from memory.models import Memory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .ai_providers import ClaudeProvider
from .ai_providers import GeminiProvider
from .ai_providers import OpenAIProvider

# Import extraction configuration


class MemoryExtractor:
    """Extract memories from conversation text"""

    def __init__(self):
        """Initialize the extractor and check for required dependencies"""
        logger.info("[EXTRACTION] Initializing MemoryExtractor")
        # Import and load configuration
        from amplifier.extraction.config import get_config

        self.config = get_config()
        self.provider = self._get_provider()

    def _get_provider(self):
        """Get the AI provider based on the configuration."""
        provider_map = {
            "claude": ClaudeProvider,
            "gemini": GeminiProvider,
            "openai": OpenAIProvider,
        }
        provider_class = provider_map.get(self.config.ai_provider)
        if not provider_class:
            raise ValueError(f"Unsupported AI provider: {self.config.ai_provider}")
        return provider_class(self.config)

    async def extract_memories(self, text: str, context: dict[str, Any] | None = None) -> list[Memory]:
        """Extract memories from text using the configured AI provider.

        Args:
            text: Conversation text to analyze
            context: Additional context for extraction

        Returns:
            List of extracted memories

        Raises:
            RuntimeError: If extraction fails
        """
        memories = await self.provider.extract_memories(text, context)
        if not memories:
            raise RuntimeError("Memory extraction failed - AI provider returned no results")
        return memories

    async def extract_from_messages(self, messages: list[dict[str, Any]], context: str | None = None) -> dict[str, Any]:
        """Extract memories from conversation messages using the configured AI provider.

        Args:
            messages: List of conversation messages
            context: Optional context string

        Returns:
            Dictionary with memories and metadata

        Raises:
            RuntimeError: If no messages provided or extraction fails
        """
        logger.info(f"[EXTRACTION] extract_from_messages called with {len(messages)} messages")

        if not messages:
            raise RuntimeError("No messages provided for memory extraction")

        conversation = self._format_messages(messages)
        if not conversation:
            raise RuntimeError("No valid conversation content found in messages")

        logger.info(f"[EXTRACTION] Using {self.config.ai_provider} for memory extraction")
        result = await self.provider.extract_from_messages(conversation, context)

        if not result:
            raise RuntimeError("Memory extraction failed - AI provider returned no results")

        logger.info(f"[EXTRACTION] Extraction completed: {len(result.get('memories', []))} memories")
        return result

    def _format_messages(self, messages: list[dict[str, Any]]) -> str:
        """Format messages for extraction - optimized for performance"""
        formatted = []
        # Use configured limits
        max_messages = self.config.memory_extraction_max_messages
        max_content_length = self.config.memory_extraction_max_content_length

        # Only process the last N messages to avoid timeout
        messages_to_process = messages[-max_messages:] if len(messages) > max_messages else messages
        logger.info(f"[EXTRACTION] Processing {len(messages_to_process)} of {len(messages)} total messages")

        for msg in messages_to_process:
            role = msg.get("role", "unknown")
            # Skip non-conversation roles early
            if role not in ["user", "assistant"]:
                continue

            content = msg.get("content", "")
            if not content:
                continue

            # Truncate content to configured length
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."

            # Skip system/hook messages
            if self._is_system_message(content):
                continue

            formatted.append(f"{role.upper()}: {content}")

        logger.info(f"[EXTRACTION] Formatted {len(formatted)} messages for extraction")
        return "\n\n".join(formatted)

    def _is_system_message(self, content: str) -> bool:
        """Check if content is a system/hook message that should be filtered"""
        if not content:
            return False

        # Filter out ANSI escape codes first for cleaner checking
        import re

        clean_content = re.sub(r"\x1b\[[0-9;]*m", "", content)

        # Patterns that indicate system/hook messages
        system_patterns = [
            r"^PostToolUse:",
            r"^PreToolUse:",
            r"^\[.*HOOK\]",
            r"^Hook (started|completed|cancelled)",
            r"^Running.*make check",
            r"^Post-hook for \w+ tool",
            r"^Using directory of",
            r"^Skipping.*make check",
            r"^\$CLAUDE_PROJECT_DIR",
            r"^Extract key memories from this conversation",  # System prompts
            r"^Looking at the conversation context",  # Assistant meta-commentary
            r"^UNKNOWN:",  # Empty conversation markers
            r"^Extract and return as JSON:",  # Instruction text
        ]

        return any(re.match(pattern, clean_content, re.IGNORECASE) for pattern in system_patterns)

    def _extract_tags(self, text: str) -> list[str]:
        """Extract relevant tags from text"""
        tags = []

        # Technical terms
        tech_terms = re.findall(
            r"\b(?:Python|JavaScript|TypeScript|API|SDK|async|await|JSON|SQL|Git|Docker|"
            r"React|Vue|Node|Express|FastAPI|Django|CLI|MCP|SSE|LLM|Claude|OpenAI)\b",
            text,
            re.IGNORECASE,
        )
        tags.extend([term.lower() for term in tech_terms])

        # File extensions
        extensions = re.findall(r"\b\w+\.(py|js|ts|jsx|tsx|json|yaml|yml|md|txt)\b", text)
        tags.extend([ext for _, ext in extensions])

        return list(set(tags))[:5]
