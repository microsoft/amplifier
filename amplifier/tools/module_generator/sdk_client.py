"""Claude Code SDK integration for module generation

This module handles interaction with the Claude Code SDK to generate
module implementations from specifications.
"""

import asyncio
import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from claude_code_sdk import ClaudeCodeOptions
from claude_code_sdk import ClaudeSDKClient


@dataclass
class ProgressTracker:
    """Track progress during SDK operations"""

    phase: str = "initializing"
    message: str = ""
    last_update: float = 0
    stall_threshold: float = 30.0  # Seconds before considering stalled
    callback: Callable[[str, str], None] | None = None

    def update(self, phase: str, message: str):
        """Update progress"""
        self.phase = phase
        self.message = message
        self.last_update = time.time()
        if self.callback:
            self.callback(phase, message)

    @property
    def is_stalled(self) -> bool:
        """Check if progress has stalled"""
        return (time.time() - self.last_update) > self.stall_threshold

    def check_stall(self) -> str:
        """Get stall warning message if stalled"""
        if self.is_stalled:
            elapsed = int(time.time() - self.last_update)
            return f"Operation may be stalled (no update for {elapsed}s)"
        return ""


@dataclass
class TimeoutConfig:
    """Configuration for different operation timeouts"""

    analysis: int = 120  # 2 minutes for analysis
    file_generation: int = 300  # 5 minutes for file generation
    test_generation: int = 300  # 5 minutes for test generation
    default: int = 120  # Default timeout


class SDKModuleGenerator:
    """Generate module code using Claude Code SDK"""

    def __init__(
        self,
        timeout_config: TimeoutConfig,
        permission_mode: str = "plan",
        philosophy_path: Path | None = None,
    ):
        """Initialize SDK generator

        Args:
            timeout_config: Timeout configuration for different operations
            permission_mode: Either "plan" (dry run) or "acceptEdits" (actual generation)
            philosophy_path: Path to philosophy document to include in prompts
        """
        self.permission_mode = permission_mode
        self.timeout_config = timeout_config
        self.logger = logging.getLogger(__name__)
        self.max_retries = 3
        self.progress_tracker = ProgressTracker()
        self.philosophy_content = self._load_philosophy(philosophy_path) if philosophy_path else ""

    def _load_philosophy(self, philosophy_path: Path) -> str:
        """Load philosophy document content

        Args:
            philosophy_path: Path to philosophy markdown file

        Returns:
            Philosophy content as string
        """
        try:
            if philosophy_path.exists():
                with open(philosophy_path, encoding="utf-8") as f:
                    return f.read()
            else:
                self.logger.warning(f"Philosophy file not found: {philosophy_path}")
        except Exception as e:
            self.logger.error(f"Failed to load philosophy: {e}")
        return ""

    def set_progress_callback(self, callback: Callable[[str, str], None]):
        """Set a callback to receive progress updates.

        Args:
            callback: Function that takes (phase: str, message: str) parameters
        """
        self.progress_tracker.callback = callback

    async def analyze_spec(self, spec_content: str) -> dict[str, Any]:
        """Analyze a specification and return implementation plan

        Args:
            spec_content: Module specification as JSON

        Returns:
            Analysis results including implementation approach

        Raises:
            TimeoutError: If SDK operation times out
        """
        philosophy_section = (
            f"\n\n=== Philosophy ===\n{self.philosophy_content[:1000]}" if self.philosophy_content else ""
        )

        system_prompt = f"""You are a JSON-only module analysis API.
You MUST respond with ONLY valid JSON - no explanations, no markdown, no text before or after.
{philosophy_section}

Required JSON structure:
{{
    "feasibility": "simple|moderate|complex",
    "estimated_files": <number>,
    "implementation_approach": "description of approach",
    "key_challenges": ["challenge1", "challenge2"],
    "suggested_patterns": ["pattern1", "pattern2"]
}}

CRITICAL: Return ONLY the JSON object. No other text."""

        prompt = f"""Analyze this module specification:

{spec_content}

IMPORTANT: Your response must be ONLY a JSON object with the exact structure specified in the system prompt.
Do not include any explanations, markdown formatting, or text outside the JSON.
Start your response with {{ and end with }}."""

        try:
            # Use configured analysis timeout
            self.progress_tracker.update("analysis", "Analyzing specification...")
            response = await self._query_sdk_with_retry(
                system_prompt, prompt, "plan", expect_json=True, timeout_override=self.timeout_config.analysis
            )
            return self._parse_json_response(response)
        except TimeoutError:
            raise TimeoutError(
                f"SDK analysis timed out after {self.timeout_config.analysis} seconds. "
                "This may indicate the SDK is not responding or the spec is too complex."
            )

    async def generate_file(self, file_spec: dict[str, Any], module_context: dict[str, Any]) -> str:
        """Generate implementation for a single file

        Args:
            file_spec: File specification
            module_context: Overall module context

        Returns:
            Generated Python code

        Raises:
            TimeoutError: If SDK operation times out
        """
        philosophy_section = f"\n\n=== Philosophy ===\n{self.philosophy_content}" if self.philosophy_content else ""

        system_prompt = f"""You are a Python module implementation expert following the Amplifier philosophy:
- Ruthless simplicity - no unnecessary abstractions
- Complete, working code - no stubs or placeholders
- Clear contracts via docstrings and type hints
- Each file is self-contained but connects via clear interfaces
{philosophy_section}

Generate complete, working Python code."""

        prompt = f"""Generate the implementation for this file:

File: {file_spec.get("filename", "unknown.py")}
Purpose: {file_spec.get("purpose", "No purpose specified")}
Public Interface: {file_spec.get("public_interface", [])}
Dependencies: {file_spec.get("dependencies", [])}

Module Context:
- Module: {module_context.get("name", "unknown")}
- Purpose: {module_context.get("purpose", "No purpose specified")}

Implementation Notes:
{file_spec.get("implementation_notes", "Follow standard patterns")}

Generate complete, working Python code for this file. Include:
1. Module docstring
2. All necessary imports
3. Complete implementation of all public interfaces
4. Proper error handling
5. Type hints for all functions

Return ONLY the Python code, no explanations."""

        try:
            filename = file_spec.get("filename", "file")
            self.progress_tracker.update("file_generation", f"Generating {filename}...")

            # Use file generation timeout
            response = await self._query_sdk_with_retry(
                system_prompt,
                prompt,
                self.permission_mode,
                expect_json=False,
                timeout_override=self.timeout_config.file_generation,
            )
            return self._clean_code_response(response)
        except TimeoutError:
            filename = file_spec.get("filename", "unknown")
            raise TimeoutError(
                f"SDK file generation for '{filename}' timed out after {self.timeout_config.file_generation} seconds. "
                f"Consider increasing timeout for complex modules or breaking into smaller files."
            )

    async def generate_test(self, test_spec: dict[str, Any], module_context: dict[str, Any]) -> str:
        """Generate test implementation

        Args:
            test_spec: Test specification
            module_context: Overall module context

        Returns:
            Generated test code

        Raises:
            TimeoutError: If SDK operation times out
        """
        system_prompt = """You are a Python test implementation expert.
Generate complete pytest test files that thoroughly validate module behavior.
Follow pytest best practices and include fixtures where appropriate."""

        prompt = f"""Generate tests for this specification:

Test File: {test_spec.get("filename", "test_unknown.py")}
Description: {test_spec.get("description", "Test module functionality")}
Test Cases: {test_spec.get("test_cases", [])}

Module Context:
- Module: {module_context.get("name", "unknown")}
- Files: {[f["filename"] for f in module_context.get("files", [])]}

Generate complete pytest test code. Include:
1. All necessary imports
2. Fixtures if needed
3. Comprehensive test cases
4. Edge case handling
5. Clear test documentation

Return ONLY the Python test code."""

        try:
            filename = test_spec.get("filename", "tests")
            self.progress_tracker.update("test_generation", f"Generating {filename}...")

            # Use test generation timeout
            response = await self._query_sdk_with_retry(
                system_prompt,
                prompt,
                self.permission_mode,
                expect_json=False,
                timeout_override=self.timeout_config.test_generation,
            )
            return self._clean_code_response(response)
        except TimeoutError:
            filename = test_spec.get("filename", "test")
            raise TimeoutError(
                f"SDK test generation for '{filename}' timed out after {self.timeout_config.test_generation} seconds. "
                f"Consider simplifying test cases or increasing timeout."
            )

    async def _query_sdk_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        permission_mode: str,
        expect_json: bool = False,
        timeout_override: int | None = None,
    ) -> str:
        """Query SDK with retry logic for handling empty responses and parse errors.

        Args:
            system_prompt: System prompt for the SDK
            user_prompt: User prompt/query
            permission_mode: SDK permission mode
            expect_json: Whether we expect JSON response (enables parse retry)
            timeout_override: Optional timeout override for this specific query

        Returns:
            SDK response as string

        Raises:
            asyncio.TimeoutError: If operation times out
            ValueError: If all retries fail to get valid response
        """
        last_error = None
        retry_prompt = user_prompt

        # Log the initial request - also to stdout for visibility
        self.logger.info("=" * 80)
        self.logger.info("SDK REQUEST")
        self.logger.info("=" * 80)
        self.logger.info(f"Permission Mode: {permission_mode}")
        self.logger.info(f"Expect JSON: {expect_json}")
        self.logger.info(f"Timeout: {timeout_override or self.timeout_config.default}s")
        self.logger.info("-" * 40 + " SYSTEM PROMPT " + "-" * 40)
        self.logger.info(system_prompt)
        self.logger.info("-" * 40 + " USER PROMPT " + "-" * 40)
        self.logger.info(user_prompt[:1000] + ("..." if len(user_prompt) > 1000 else ""))

        # Also print to stdout for immediate visibility
        print("\n" + "=" * 60)
        print(f"📤 SDK REQUEST - {permission_mode} mode")
        print("=" * 60)
        print(f"System prompt preview: {system_prompt[:100]}...")
        print(f"User prompt preview: {user_prompt[:100]}...")
        print(f"Timeout: {timeout_override or self.timeout_config.default} seconds")
        print("=" * 60)

        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"SDK query attempt {attempt + 1}/{self.max_retries}")

                self.progress_tracker.update("sdk_query", f"Querying SDK (attempt {attempt + 1}/{self.max_retries})...")

                # Query SDK with optional timeout override
                timeout = timeout_override if timeout_override is not None else self.timeout_config.default
                response = await self._query_sdk(system_prompt, retry_prompt, permission_mode, timeout)

                # Log the response
                self.logger.info("=" * 80)
                self.logger.info(f"SDK RESPONSE (Attempt {attempt + 1}/{self.max_retries})")
                self.logger.info("=" * 80)
                self.logger.info(f"Response length: {len(response) if response else 0} chars")
                if not response:
                    self.logger.warning("EMPTY RESPONSE")
                else:
                    # Log first 2000 chars to see what we're getting
                    self.logger.info("-" * 40 + " RESPONSE CONTENT " + "-" * 40)
                    self.logger.info(response[:2000] + ("..." if len(response) > 2000 else ""))
                    self.logger.info("=" * 80)

                # Also print response summary to stdout
                print("\n" + "=" * 60)
                print(f"📥 SDK RESPONSE - Attempt {attempt + 1}/{self.max_retries}")
                print("=" * 60)
                if not response:
                    print("⚠️  Empty response received")
                elif expect_json:
                    print(f"✅ JSON response: {len(response)} chars")
                    try:
                        # Try to show JSON keys
                        import json

                        data = json.loads(self._clean_json_response(response))
                        print(f"   Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    except:
                        print("   (Failed to parse as JSON)")
                else:
                    # Show code response preview
                    print(f"✅ Code response: {len(response)} chars")
                    lines = response.strip().split("\n")
                    print(f"   First line: {lines[0][:80]}..." if lines else "   (empty)")
                    print(f"   Total lines: {len(lines)}")
                print("=" * 60)

                # Validate response
                if not response or response.strip() == "":
                    raise ValueError("SDK returned empty response")

                # If we expect JSON, try to parse it
                if expect_json:
                    try:
                        self._parse_json_response(response)
                    except ValueError as e:
                        if attempt < self.max_retries - 1:
                            # Include error in retry prompt with stronger enforcement
                            retry_prompt = (
                                f"{user_prompt}\n\n"
                                f"ERROR: Previous response was not valid JSON.\n"
                                f"Error: {str(e)}\n\n"
                                f"CRITICAL INSTRUCTION: You MUST respond with ONLY a JSON object.\n"
                                f"- Start with {{\n"
                                f"- End with }}\n"
                                f"- No markdown formatting (no ```)\n"
                                f"- No explanations before or after\n"
                                f"- ONLY the JSON object\n\n"
                                f"Example correct response:\n"
                                f'{{"feasibility": "simple", "estimated_files": 3, ...}}'
                            )
                            self.logger.warning(f"JSON parse error on attempt {attempt + 1}: {str(e)}")
                            last_error = e
                            continue
                        raise

                # Success!
                return response

            except (TimeoutError, ValueError) as e:
                last_error = e

                if attempt < self.max_retries - 1:
                    # Calculate backoff
                    wait_time = 2**attempt  # 1s, 2s, 4s
                    self.logger.info(f"Retry {attempt + 1}/{self.max_retries} after {wait_time}s due to: {str(e)}")
                    await asyncio.sleep(wait_time)

                    # Add error context for next attempt
                    if "empty response" in str(e).lower():
                        retry_prompt = (
                            f"{user_prompt}\n\n"
                            f"IMPORTANT: You must provide a response. "
                            f"Previous attempt returned empty. Please respond."
                        )
                else:
                    # Final attempt failed
                    self.logger.error(f"All {self.max_retries} SDK attempts failed. Last error: {str(e)}")
                    raise

        # Should not reach here, but for safety
        raise ValueError(f"SDK query failed after {self.max_retries} attempts. Last error: {last_error}")

    async def _query_sdk(
        self, system_prompt: str, user_prompt: str, permission_mode: str, timeout: int | None = None
    ) -> str:
        """Query Claude Code SDK with timeout handling and progress tracking

        Args:
            system_prompt: System prompt for the SDK
            user_prompt: User prompt/query
            permission_mode: SDK permission mode
            timeout: Timeout in seconds (uses instance default if None)

        Returns:
            SDK response as string

        Raises:
            asyncio.TimeoutError: If operation times out
        """

        # Convert string permission mode to expected type
        # The SDK expects specific string literals
        valid_modes = ["default", "acceptEdits", "plan", "bypassPermissions"]
        if permission_mode not in valid_modes:
            permission_mode = "plan"  # Default to plan mode

        if timeout is None:
            timeout = self.timeout_config.default

        response = ""
        chunks_received = 0
        last_progress_time = asyncio.get_event_loop().time()
        stall_check_time = time.time()

        async with asyncio.timeout(timeout):
            async with ClaudeSDKClient(
                options=ClaudeCodeOptions(
                    system_prompt=system_prompt,
                    permission_mode=permission_mode,  # type: ignore
                    max_turns=1,
                )
            ) as client:
                await client.query(user_prompt)

                async for message in client.receive_response():
                    if hasattr(message, "content"):
                        content = getattr(message, "content", [])
                        if isinstance(content, list):
                            for block in content:
                                if hasattr(block, "text"):
                                    chunk = getattr(block, "text", "")
                                    response += chunk
                                    chunks_received += 1

                                    # Report progress periodically (every 5 seconds)
                                    current_time = asyncio.get_event_loop().time()
                                    if current_time - last_progress_time > 5:
                                        self.progress_tracker.update(
                                            "streaming",
                                            f"Receiving response... ({len(response)} chars, {chunks_received} chunks)",
                                        )
                                        # Also print to stdout for visibility
                                        print(
                                            f"  📊 Streaming: {len(response)} chars received, {chunks_received} chunks..."
                                        )
                                        last_progress_time = current_time

                                    # Check for stalled operation
                                    if time.time() - stall_check_time > 10:
                                        stall_msg = self.progress_tracker.check_stall()
                                        if stall_msg:
                                            self.logger.warning(stall_msg)
                                        stall_check_time = time.time()

        if chunks_received > 0:
            self.progress_tracker.update(
                "complete", f"Response complete ({len(response)} chars, {chunks_received} chunks)"
            )

        return response

    def _parse_json_response(self, response: str) -> dict[str, Any]:
        """Parse JSON from SDK response with aggressive extraction

        Args:
            response: Raw SDK response

        Returns:
            Parsed JSON object

        Raises:
            ValueError: If response cannot be parsed as JSON
        """
        # Handle empty response
        if not response or response.strip() == "":
            raise ValueError("Cannot parse JSON from empty response")

        # Clean up response
        cleaned = response.strip()

        # Remove markdown code blocks if present
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        # First attempt: direct parse
        try:
            result = json.loads(cleaned)
            self.logger.debug("Successfully parsed JSON response directly")
            return result
        except json.JSONDecodeError:
            pass

        # Second attempt: extract JSON object from text
        import re

        # Try to find a JSON object anywhere in the response
        # Look for patterns that start with { and end with matching }
        json_patterns = [
            r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}",  # Nested JSON objects
            r'\{.*?"feasibility".*?\}',  # Look for our expected field
            r"\{.*\}",  # Any JSON object
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, cleaned, re.DOTALL)
            for match in matches:
                try:
                    result = json.loads(match)
                    # Validate it has expected structure for analysis
                    if "feasibility" in result or "implementation_approach" in result:
                        self.logger.debug(f"Successfully extracted JSON using pattern: {pattern[:30]}...")
                        return result
                except json.JSONDecodeError:
                    continue

        # Third attempt: Try to find JSON after common prefixes
        prefixes_to_strip = [
            "Here is the JSON analysis:",
            "Here's the analysis:",
            "JSON:",
            "Analysis:",
            "Response:",
            "I'll analyze",
        ]

        for prefix in prefixes_to_strip:
            if prefix.lower() in cleaned.lower():
                # Find where this prefix ends and try parsing after it
                idx = cleaned.lower().index(prefix.lower()) + len(prefix)
                potential_json = cleaned[idx:].strip()
                try:
                    result = json.loads(potential_json)
                    self.logger.debug(f"Successfully extracted JSON after stripping prefix: {prefix}")
                    return result
                except json.JSONDecodeError:
                    # Try to find first { after the prefix
                    if "{" in potential_json:
                        start_idx = potential_json.index("{")
                        try:
                            # Find matching closing brace
                            brace_count = 0
                            end_idx = start_idx
                            for i, char in enumerate(potential_json[start_idx:], start_idx):
                                if char == "{":
                                    brace_count += 1
                                elif char == "}":
                                    brace_count -= 1
                                    if brace_count == 0:
                                        end_idx = i + 1
                                        break

                            if end_idx > start_idx:
                                json_str = potential_json[start_idx:end_idx]
                                result = json.loads(json_str)
                                self.logger.debug(f"Successfully extracted JSON from text after prefix: {prefix}")
                                return result
                        except (json.JSONDecodeError, ValueError):
                            continue

        # Log failure details for debugging
        self.logger.error(f"Failed to parse JSON. Response preview: {cleaned[:200]}...")

        # Provide helpful error message
        if "I'll analyze" in cleaned or "Here" in cleaned or "Let me" in cleaned:
            raise ValueError(
                f"SDK returned natural language instead of JSON. "
                f"Response started with: '{cleaned[:100]}...'. "
                f"The SDK is not following JSON-only instructions."
            )

        raise ValueError(f"Failed to extract valid JSON from SDK response. Response: {cleaned[:200]}...")

    def _clean_json_response(self, response: str) -> str:
        """Clean JSON response by removing markdown formatting

        Args:
            response: Raw response that should contain JSON

        Returns:
            Cleaned JSON string
        """
        if not response:
            return ""

        cleaned = response.strip()

        # Remove markdown code blocks
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        return cleaned.strip()

    def _clean_code_response(self, response: str) -> str:
        """Clean code response from SDK

        Args:
            response: Raw SDK response

        Returns:
            Clean Python code
        """
        cleaned = response.strip()

        # First check if response starts with natural language
        # Common patterns we've seen:
        # - "I'll generate..."
        # - "Here's the..."
        # - "Let me create..."
        natural_language_starters = [
            "I'll",
            "I will",
            "Let me",
            "Here's",
            "Here is",
            "This",
            "The following",
            "Below is",
        ]

        for starter in natural_language_starters:
            if cleaned.startswith(starter):
                self.logger.warning(f"SDK response starts with natural language: '{starter}...'")
                # Try to find code block within the response
                if "```python" in cleaned:
                    start_idx = cleaned.index("```python") + 9
                    if "```" in cleaned[start_idx:]:
                        end_idx = cleaned.index("```", start_idx)
                        cleaned = cleaned[start_idx:end_idx].strip()
                        self.logger.info("Extracted Python code from markdown block")
                        return cleaned
                elif "```py" in cleaned:
                    start_idx = cleaned.index("```py") + 5
                    if "```" in cleaned[start_idx:]:
                        end_idx = cleaned.index("```", start_idx)
                        cleaned = cleaned[start_idx:end_idx].strip()
                        self.logger.info("Extracted Python code from markdown block")
                        return cleaned
                elif "```" in cleaned:
                    start_idx = cleaned.index("```") + 3
                    if "```" in cleaned[start_idx:]:
                        end_idx = cleaned.index("```", start_idx)
                        cleaned = cleaned[start_idx:end_idx].strip()
                        self.logger.info("Extracted code from generic markdown block")
                        return cleaned
                break

        # Standard cleanup for code that's just wrapped in markdown
        if cleaned.startswith("```python"):
            cleaned = cleaned[9:]
        elif cleaned.startswith("```py"):
            cleaned = cleaned[5:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        return cleaned.strip()
