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

# Import Claude Code SDK - REQUIRED for memory extraction
try:
    from claude_code_sdk import ClaudeCodeOptions
    from claude_code_sdk import ClaudeSDKClient
except ImportError:
    raise RuntimeError(
        "Claude Code SDK not available. Memory extraction requires Claude Code SDK. "
        "Install with: pip install claude-code-sdk"
    )

# Import extraction configuration

# Configuration (deprecated - use config module)
CLAUDE_SDK_TIMEOUT = 120  # seconds


class MemoryExtractor:
    """Extract memories from conversation text"""

    def __init__(self):
        """Initialize the extractor and check for required dependencies"""
        logger.info("[EXTRACTION] Initializing MemoryExtractor")
        # Import and load configuration
        from amplifier.extraction.config import get_config

        self.config = get_config()

        # Check if Claude CLI is installed and available
        try:
            result = subprocess.run(["which", "claude"], capture_output=True, text=True, timeout=2)
            if result.returncode != 0:
                raise RuntimeError(
                    "Claude CLI not found. Memory extraction requires Claude CLI. "
                    "Install with: npm install -g @anthropic-ai/claude-code"
                )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            raise RuntimeError(
                "Claude CLI not found. Memory extraction requires Claude CLI. "
                "Install with: npm install -g @anthropic-ai/claude-code"
            )

        logger.info("[EXTRACTION] Claude Code SDK and CLI verified - ready for extraction")

    async def extract_memories(self, text: str, context: dict[str, Any] | None = None) -> list[Memory]:
        """Extract memories from text using Claude Code SDK

        Args:
            text: Conversation text to analyze
            context: Additional context for extraction

        Returns:
            List of extracted memories

        Raises:
            RuntimeError: If Claude Code SDK extraction fails
        """
        memories = await self._extract_with_claude(text, context)
        if not memories:
            raise RuntimeError("Memory extraction failed - Claude Code SDK returned no results")
        return memories

    async def extract_from_messages(self, messages: list[dict[str, Any]], context: str | None = None) -> dict[str, Any]:
        """Extract memories from conversation messages using Claude Code SDK

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

        # Format messages for Claude Code SDK extraction
        conversation = self._format_messages(messages)
        if not conversation:
            raise RuntimeError("No valid conversation content found in messages")

        logger.info("[EXTRACTION] Using Claude Code SDK for memory extraction")
        result = await self._extract_with_claude_full(conversation, context)

        if not result:
            raise RuntimeError("Memory extraction failed - Claude Code SDK returned no results")

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

    async def _extract_with_claude(self, text: str, context: dict[str, Any] | None) -> list[Memory]:
        """Extract memories using Claude Code SDK"""
        prompt = f"""Extract important memories from this conversation.

Categories: learning, decision, issue_solved, preference, pattern

Return ONLY a JSON array of memories:
[
    {{
        "content": "The specific memory",
        "category": "one of the categories above",
        "metadata": {{}}
    }}
]

Conversation:
{text}

Context: {json.dumps(context or {})}
"""

        try:
            async with asyncio.timeout(self.config.memory_extraction_timeout):
                async with ClaudeSDKClient(  # type: ignore
                    options=ClaudeCodeOptions(  # type: ignore
                        system_prompt="You extract memories from conversations.",
                        max_turns=1,
                        model=self.config.memory_extraction_model,
                    )
                ) as client:
                    await client.query(prompt)

                    response = ""
                    async for message in client.receive_response():
                        if hasattr(message, "content"):
                            content = getattr(message, "content", [])
                            if isinstance(content, list):
                                for block in content:
                                    if hasattr(block, "text"):
                                        response += getattr(block, "text", "")

                    # Clean and parse response
                    cleaned = response.strip()
                    if cleaned.startswith("```json"):
                        cleaned = cleaned[7:]
                    elif cleaned.startswith("```"):
                        cleaned = cleaned[3:]
                    if cleaned.endswith("```"):
                        cleaned = cleaned[:-3]
                    cleaned = cleaned.strip()

                    if cleaned:
                        data = json.loads(cleaned)
                        return [
                            Memory(
                                content=item["content"],
                                category=item["category"],
                                metadata={**item.get("metadata", {}), **(context or {})},
                            )
                            for item in data
                        ]
        except TimeoutError:
            logger.warning(f"Claude Code SDK timed out after {self.config.memory_extraction_timeout} seconds")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse extraction response: {e}")
        except Exception as e:
            logger.error(f"Claude Code SDK extraction error: {e}")

        return []

    async def _extract_with_claude_full(self, conversation: str, context: str | None) -> dict[str, Any] | None:
        """Extract using Claude Code SDK with full response format"""
        from datetime import datetime

        logger.info("[EXTRACTION] Starting Claude Code SDK full extraction")

        context_str = f"\nContext: {context}" if context else ""

        prompt = f"""Extract key memories from this conversation that should be remembered for future interactions.
{context_str}

Conversation:
{conversation}

Extract and return as JSON:
{{
  "memories": [
    {{
      "type": "learning|decision|issue_solved|pattern|preference",
      "content": "concise memory content",
      "importance": 0.0-1.0,
      "tags": ["tag1", "tag2"]
    }}
  ],
  "key_learnings": ["what was learned"],
  "decisions_made": ["decisions"],
  "issues_solved": ["problems resolved"]
}}

Focus on technical decisions, problems solved, user preferences, and important patterns.
Return ONLY valid JSON."""

        try:
            logger.info(f"[EXTRACTION] Setting timeout to {self.config.memory_extraction_timeout} seconds")
            async with asyncio.timeout(self.config.memory_extraction_timeout):
                logger.info(
                    f"[EXTRACTION] Creating Claude Code SDK client with model: {self.config.memory_extraction_model}"
                )
                async with ClaudeSDKClient(  # type: ignore
                    options=ClaudeCodeOptions(  # type: ignore
                        system_prompt="You are a memory extraction expert. Extract key information from conversations.",
                        max_turns=1,
                        model=self.config.memory_extraction_model,
                    )
                ) as client:
                    logger.info("[EXTRACTION] Querying Claude Code SDK")
                    await client.query(prompt)

                    logger.info("[EXTRACTION] Receiving response from Claude Code SDK")
                    response = ""
                    async for message in client.receive_response():
                        if hasattr(message, "content"):
                            content = getattr(message, "content", [])
                            if isinstance(content, list):
                                for block in content:
                                    if hasattr(block, "text"):
                                        response += getattr(block, "text", "")

                    logger.info(f"[EXTRACTION] Received response length: {len(response)}")

                    if not response:
                        logger.warning("[EXTRACTION] Empty response from Claude Code SDK")
                        return None

                    # Clean and parse JSON
                    cleaned = response.strip()
                    if cleaned.startswith("```json"):
                        cleaned = cleaned[7:]
                    elif cleaned.startswith("```"):
                        cleaned = cleaned[3:]
                    if cleaned.endswith("```"):
                        cleaned = cleaned[:-3]
                    cleaned = cleaned.strip()

                    logger.info("[EXTRACTION] Parsing JSON response")
                    data = json.loads(cleaned)
                    data["metadata"] = {"extraction_method": "claude_sdk", "timestamp": datetime.now().isoformat()}

                    logger.info(f"[EXTRACTION] Successfully extracted: {len(data.get('memories', []))} memories")
                    return data

        except TimeoutError:
            logger.warning(
                f"[EXTRACTION] Claude Code SDK timed out after {self.config.memory_extraction_timeout} seconds"
            )
        except json.JSONDecodeError as e:
            logger.error(f"[EXTRACTION] Failed to parse extraction response: {e}")
        except Exception as e:
            logger.error(f"[EXTRACTION] Claude Code SDK extraction error: {e}")
            import traceback

            logger.error(f"[EXTRACTION] Traceback: {traceback.format_exc()}")

        return None

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
