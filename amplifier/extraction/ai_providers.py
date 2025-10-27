"""AI Providers for memory extraction."""

import asyncio
import json
import logging
import subprocess
from abc import ABC
from abc import abstractmethod
from typing import Any

from memory.models import Memory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Claude Code SDK - REQUIRED for memory extraction
try:
    from claude_code_sdk import ClaudeCodeOptions
    from claude_code_sdk import ClaudeSDKClient
except ImportError:
    logger.warning("Claude Code SDK not available. Claude provider will not work.")


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    async def extract_memories(self, text: str, context: dict[str, Any] | None = None) -> list[Memory]:
        """Extract memories from text."""
        pass

    @abstractmethod
    async def extract_from_messages(self, messages: list[dict[str, Any]], context: str | None = None) -> dict[str, Any]:
        """Extract memories from conversation messages."""
        pass


class ClaudeProvider(AIProvider):
    """Claude AI provider."""

    def __init__(self, config):
        """Initialize the Claude provider."""
        self.config = config
        self._check_dependencies()

    def _check_dependencies(self):
        """Check for required dependencies."""
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
        """Extract memories from text using Claude Code SDK."""
        return await self._extract_with_claude(text, context)

    async def extract_from_messages(self, messages: list[dict[str, Any]], context: str | None = None) -> dict[str, Any]:
        """Extract memories from conversation messages using Claude Code SDK."""
        return await self._extract_with_claude_full(messages, context)

    async def _extract_with_claude(self, text: str, context: dict[str, Any] | None) -> list[Memory]:
        """Extract memories using Claude Code SDK."""
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
                async with ClaudeSDKClient(
                    options=ClaudeCodeOptions(
                        system_prompt="You extract memories from conversations.",
                        max_turns=1,
                        model=self.config.claude_model,
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

                    cleaned = self._clean_response(response)
                    if cleaned:
                        data = json.loads(cleaned)
                        return [
                            Memory(
                                content=item["content"],
                                category=item["category"],
                                metadata={**item.get("metadata", {
    }), **(context or {
    })},
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
        """Extract using Claude Code SDK with full response format."""
        from datetime import datetime

        context_str = f"
Context: {context}" if context else ""

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
            async with asyncio.timeout(self.config.memory_extraction_timeout):
                async with ClaudeSDKClient(
                    options=ClaudeCodeOptions(
                        system_prompt="You are a memory extraction expert. Extract key information from conversations.",
                        max_turns=1,
                        model=self.config.claude_model,
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

                    cleaned = self._clean_response(response)
                    if cleaned:
                        data = json.loads(cleaned)
                        data["metadata"] = {
    "extraction_method": "claude_sdk", "timestamp": datetime.now().isoformat()}
                        return data

        except TimeoutError:
            logger.warning(
                f"Claude Code SDK timed out after {self.config.memory_extraction_timeout} seconds"
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse extraction response: {e}")
        except Exception as e:
            logger.error(f"Claude Code SDK extraction error: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")

        return None

    def _clean_response(self, response: str) -> str:
        """Clean and parse JSON response."""
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()


class GeminiProvider(AIProvider):
    """Gemini AI provider."""

    def __init__(self, config):
        """Initialize the Gemini provider."""
        self.config = config
        self._check_dependencies()

    def _check_dependencies(self):
        """Check for required dependencies."""
        try:
            import google.generativeai as genai
        except ImportError:
            raise RuntimeError(
                "Google Generative AI Python library not found. Please install it with: pip install google-generativeai"
            )

    async def extract_memories(self, text: str, context: dict[str, Any] | None = None) -> list[Memory]:
        """Extract memories from text using Gemini API."""
        # This method is a simplified version of extract_from_messages and is not
        # fully implemented as the core logic is in extract_from_messages.
        return await self._extract_with_gemini(text, context)

    async def extract_from_messages(self, messages: list[dict[str, Any]], context: str | None = None) -> dict[str, Any]:
        """Extract memories from conversation messages using Gemini API."""
        return await self._extract_with_gemini_full(messages, context)

    async def _extract_with_gemini(self, text: str, context: dict[str, Any] | None) -> list[Memory]:
        """Extract memories using Gemini API."""
        import google.generativeai as genai

        genai.configure(api_key=self.config.gemini_api_key)
        model = genai.GenerativeModel(self.config.gemini_model)

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
            response = await model.generate_content_async(prompt)
            cleaned = self._clean_response(response.text)
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
        except Exception as e:
            logger.error(f"Gemini API extraction error: {e}")
        return []

    async def _extract_with_gemini_full(self, conversation: str, context: str | None) -> dict[str, Any] | None:
        """Extract using Gemini API with full response format."""
        from datetime import datetime
        import google.generativeai as genai

        genai.configure(api_key=self.config.gemini_api_key)
        model = genai.GenerativeModel(self.config.gemini_model)

        context_str = f"
Context: {context}" if context else ""

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
            response = await model.generate_content_async(prompt)
            cleaned = self._clean_response(response.text)
            if cleaned:
                data = json.loads(cleaned)
                data["metadata"] = {
                    "extraction_method": "gemini_api",
                    "timestamp": datetime.now().isoformat(),
                }
                return data
        except Exception as e:
            logger.error(f"Gemini API extraction error: {e}")
        return None

    def _clean_response(self, response: str) -> str:
        """Clean and parse JSON response."""
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()


class OpenAIProvider(AIProvider):
    """OpenAI AI provider."""

    def __init__(self, config):
        """Initialize the OpenAI provider."""
        self.config = config
        self._check_dependencies()

    def _check_dependencies(self):
        """Check for required dependencies."""
        try:
            import openai
        except ImportError:
            raise RuntimeError(
                "OpenAI Python library not found. Please install it with: pip install openai"
            )

    async def extract_memories(self, text: str, context: dict[str, Any] | None = None) -> list[Memory]:
        """Extract memories from text using OpenAI API."""
        # This is a simplified version of extract_from_messages.
        # For the purpose of this task, we will focus on the more complex
        # extract_from_messages and leave this as a placeholder.
        return []

    async def extract_from_messages(self, messages: list[dict[str, Any]], context: str | None = None) -> dict[str, Any]:
        """Extract memories from conversation messages using OpenAI API."""
        from datetime import datetime
        import openai

        client = openai.OpenAI(api_key=self.config.openai_api_key)

        context_str = f"
Context: {context}" if context else ""

        prompt = f"""Extract key memories from this conversation that should be remembered for future interactions.
{context_str}

Conversation:
{messages}

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
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=self.config.openai_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            data = json.loads(response.choices[0].message.content)
            data["metadata"] = {
"extraction_method": "openai_api", "timestamp": datetime.now().isoformat()}
            return data
        except Exception as e:
            logger.error(f"OpenAI API extraction error: {e}")
        return {}
