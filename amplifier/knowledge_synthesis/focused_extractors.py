"""
Focused Knowledge Extractors

Purpose: Provide specialized extractors for each type of knowledge
Contract: Each extractor focuses on ONE specific extraction type for better quality
Philosophy: "More focused asks are generally better than asking for more in single larger one"
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Any

try:
    from claude_code_sdk import ClaudeCodeOptions
    from claude_code_sdk import ClaudeSDKClient

    CLAUDE_SDK_AVAILABLE = True
except ImportError:
    CLAUDE_SDK_AVAILABLE = False
    ClaudeCodeOptions = None
    ClaudeSDKClient = None

logger = logging.getLogger(__name__)


@dataclass
class FocusedExtractionResult:
    """Result from a focused extraction"""

    extraction_type: str  # concepts, relationships, insights, patterns
    data: list[Any]
    extraction_time: float
    error: str | None = None


class ConceptExtractor:
    """Focused extractor for concepts only"""

    async def extract(self, text: str, title: str = "", document_type: str = "general") -> FocusedExtractionResult:
        """Extract ONLY concepts from text"""
        if not CLAUDE_SDK_AVAILABLE:
            return FocusedExtractionResult(
                extraction_type="concepts", data=[], extraction_time=0.0, error="Claude SDK not available"
            )

        start_time = time.time()
        prompt = f"""Analyze this text and extract ONLY the key concepts.

Title: {title}

Content:
{text}

Extract concepts in this JSON format:
{{
  "concepts": [
    {{
      "name": "concept name",
      "description": "one sentence description",
      "category": "pattern|technique|principle|tool|concept",
      "importance": 0.0-1.0
    }}
  ]
}}

Focus ONLY on identifying and describing concepts. Ignore relationships, insights, and patterns.
Look for:
- Technical concepts and terms
- Design patterns and architectures
- Principles and methodologies
- Tools and technologies
- Frameworks and libraries
- Algorithms and data structures

Return ONLY valid JSON, no other text."""

        try:
            response = ""
            async with asyncio.timeout(120):  # 2 minutes timeout
                if ClaudeSDKClient is None or ClaudeCodeOptions is None:
                    raise RuntimeError("Claude SDK not available")
                async with ClaudeSDKClient(
                    options=ClaudeCodeOptions(
                        system_prompt="You are a concept extraction specialist. Extract ONLY concepts from text. Return ONLY valid JSON.",
                        max_turns=1,
                    )
                ) as client:
                    await client.query(prompt)

                    async for message in client.receive_response():
                        if hasattr(message, "content"):
                            content = getattr(message, "content", [])
                            if isinstance(content, list):
                                for block in content:
                                    if hasattr(block, "text"):
                                        response += getattr(block, "text", "")

            # Parse response
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            elif cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            data = json.loads(cleaned_response)
            concepts = data.get("concepts", [])

            elapsed = time.time() - start_time
            logger.debug(f"Concept extraction completed in {elapsed:.1f}s: {len(concepts)} concepts found")

            return FocusedExtractionResult(extraction_type="concepts", data=concepts, extraction_time=elapsed)

        except TimeoutError:
            elapsed = time.time() - start_time
            error_msg = f"Concept extraction timed out after {elapsed:.1f} seconds - SDK may be unavailable or content too complex"
            logger.error(error_msg)
            return FocusedExtractionResult(
                extraction_type="concepts", data=[], extraction_time=elapsed, error=error_msg
            )
        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = f"Concept extraction failed: {str(e) or 'Unknown error occurred'}"
            logger.error(f"Concept extraction failed after {elapsed:.1f}s: {e}")
            return FocusedExtractionResult(
                extraction_type="concepts", data=[], extraction_time=elapsed, error=error_msg
            )


class RelationshipExtractor:
    """Focused extractor for relationships only"""

    async def extract(self, text: str, title: str = "", document_type: str = "general") -> FocusedExtractionResult:
        """Extract ONLY relationships from text"""
        if not CLAUDE_SDK_AVAILABLE:
            return FocusedExtractionResult(
                extraction_type="relationships", data=[], extraction_time=0.0, error="Claude SDK not available"
            )

        start_time = time.time()
        prompt = f"""Analyze this text and extract ONLY the relationships between entities.

Title: {title}

Content:
{text}

Extract relationships in this JSON format:
{{
  "relationships": [
    {{
      "subject": "entity1",
      "predicate": "relationship_type",
      "object": "entity2",
      "confidence": 0.0-1.0,
      "context": "brief context or explanation"
    }}
  ]
}}

Focus ONLY on identifying relationships. Ignore concepts, insights, and patterns.
Look for:
- Dependencies between components
- Causal relationships
- Hierarchical structures
- Interactions between systems
- Comparisons and alternatives
- Temporal relationships
- Logical connections

Common predicates: depends_on, contains, uses, implements, extends, replaces, causes, enables, prevents, similar_to

Return ONLY valid JSON, no other text."""

        try:
            response = ""
            async with asyncio.timeout(120):  # 2 minutes timeout
                if ClaudeSDKClient is None or ClaudeCodeOptions is None:
                    raise RuntimeError("Claude SDK not available")
                async with ClaudeSDKClient(
                    options=ClaudeCodeOptions(
                        system_prompt="You are a relationship extraction specialist. Extract ONLY relationships from text. Return ONLY valid JSON.",
                        max_turns=1,
                    )
                ) as client:
                    await client.query(prompt)

                    async for message in client.receive_response():
                        if hasattr(message, "content"):
                            content = getattr(message, "content", [])
                            if isinstance(content, list):
                                for block in content:
                                    if hasattr(block, "text"):
                                        response += getattr(block, "text", "")

            # Parse response
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            elif cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            data = json.loads(cleaned_response)
            relationships = data.get("relationships", [])

            elapsed = time.time() - start_time
            logger.debug(
                f"Relationship extraction completed in {elapsed:.1f}s: {len(relationships)} relationships found"
            )

            return FocusedExtractionResult(extraction_type="relationships", data=relationships, extraction_time=elapsed)

        except TimeoutError:
            elapsed = time.time() - start_time
            error_msg = f"Relationship extraction timed out after {elapsed:.1f} seconds - SDK may be unavailable or content too complex"
            logger.error(error_msg)
            return FocusedExtractionResult(
                extraction_type="relationships", data=[], extraction_time=elapsed, error=error_msg
            )
        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = f"Relationship extraction failed: {str(e) or 'Unknown error occurred'}"
            logger.error(f"Relationship extraction failed after {elapsed:.1f}s: {e}")
            return FocusedExtractionResult(
                extraction_type="relationships", data=[], extraction_time=elapsed, error=error_msg
            )


class InsightExtractor:
    """Focused extractor for insights only"""

    async def extract(self, text: str, title: str = "", document_type: str = "general") -> FocusedExtractionResult:
        """Extract ONLY insights from text"""
        if not CLAUDE_SDK_AVAILABLE:
            return FocusedExtractionResult(
                extraction_type="insights", data=[], extraction_time=0.0, error="Claude SDK not available"
            )

        start_time = time.time()
        prompt = f"""Analyze this text and extract ONLY actionable insights and learnings.

Title: {title}

Content:
{text}

Extract insights in this JSON format:
{{
  "insights": [
    "actionable insight or best practice",
    "warning or pitfall to avoid",
    "performance tip or optimization",
    "lesson learned",
    "recommendation or advice"
  ]
}}

Focus ONLY on extracting insights. Ignore concepts, relationships, and code patterns.
Look for:
- Best practices and recommendations
- Warnings and pitfalls to avoid
- Performance tips and optimizations
- Lessons learned from experience
- Actionable advice and guidance
- Trade-offs and considerations
- Common mistakes and how to avoid them
- Success factors and key takeaways

Each insight should be a complete, actionable statement.
Extract ALL meaningful insights - don't limit yourself.

Return ONLY valid JSON, no other text."""

        try:
            response = ""
            async with asyncio.timeout(120):  # 2 minutes timeout
                if ClaudeSDKClient is None or ClaudeCodeOptions is None:
                    raise RuntimeError("Claude SDK not available")
                async with ClaudeSDKClient(
                    options=ClaudeCodeOptions(
                        system_prompt="You are an insight extraction specialist. Extract ONLY actionable insights from text. Return ONLY valid JSON.",
                        max_turns=1,
                    )
                ) as client:
                    await client.query(prompt)

                    async for message in client.receive_response():
                        if hasattr(message, "content"):
                            content = getattr(message, "content", [])
                            if isinstance(content, list):
                                for block in content:
                                    if hasattr(block, "text"):
                                        response += getattr(block, "text", "")

            # Parse response
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            elif cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            data = json.loads(cleaned_response)
            insights = data.get("insights", [])

            elapsed = time.time() - start_time
            logger.debug(f"Insight extraction completed in {elapsed:.1f}s: {len(insights)} insights found")

            return FocusedExtractionResult(extraction_type="insights", data=insights, extraction_time=elapsed)

        except TimeoutError:
            elapsed = time.time() - start_time
            error_msg = f"Insight extraction timed out after {elapsed:.1f} seconds - SDK may be unavailable or content too complex"
            logger.error(error_msg)
            return FocusedExtractionResult(
                extraction_type="insights", data=[], extraction_time=elapsed, error=error_msg
            )
        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = f"Insight extraction failed: {str(e) or 'Unknown error occurred'}"
            logger.error(f"Insight extraction failed after {elapsed:.1f}s: {e}")
            return FocusedExtractionResult(
                extraction_type="insights", data=[], extraction_time=elapsed, error=error_msg
            )


class PatternExtractor:
    """Focused extractor for code patterns only"""

    async def extract(self, text: str, title: str = "", document_type: str = "general") -> FocusedExtractionResult:
        """Extract ONLY code patterns from text"""
        if not CLAUDE_SDK_AVAILABLE:
            return FocusedExtractionResult(
                extraction_type="patterns", data=[], extraction_time=0.0, error="Claude SDK not available"
            )

        start_time = time.time()
        prompt = f"""Analyze this text and extract ONLY code patterns and technical implementations.

Title: {title}

Content:
{text}

Extract patterns in this JSON format:
{{
  "patterns": [
    {{
      "name": "pattern name",
      "code": "code snippet or pseudo-code",
      "language": "python|javascript|etc",
      "purpose": "what problem it solves",
      "context": "when to use this pattern"
    }}
  ]
}}

Focus ONLY on extracting code patterns. Ignore concepts, relationships, and general insights.
Look for:
- Code examples and snippets
- Design patterns implementations
- Algorithm implementations
- Configuration examples
- Command sequences
- API usage patterns
- Testing patterns
- Error handling patterns
- Performance optimization patterns

Return ONLY valid JSON, no other text."""

        try:
            response = ""
            async with asyncio.timeout(120):  # 2 minutes timeout
                if ClaudeSDKClient is None or ClaudeCodeOptions is None:
                    raise RuntimeError("Claude SDK not available")
                async with ClaudeSDKClient(
                    options=ClaudeCodeOptions(
                        system_prompt="You are a code pattern extraction specialist. Extract ONLY code patterns from text. Return ONLY valid JSON.",
                        max_turns=1,
                    )
                ) as client:
                    await client.query(prompt)

                    async for message in client.receive_response():
                        if hasattr(message, "content"):
                            content = getattr(message, "content", [])
                            if isinstance(content, list):
                                for block in content:
                                    if hasattr(block, "text"):
                                        response += getattr(block, "text", "")

            # Parse response
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            elif cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            data = json.loads(cleaned_response)
            patterns = data.get("patterns", [])

            elapsed = time.time() - start_time
            logger.debug(f"Pattern extraction completed in {elapsed:.1f}s: {len(patterns)} patterns found")

            return FocusedExtractionResult(extraction_type="patterns", data=patterns, extraction_time=elapsed)

        except TimeoutError:
            elapsed = time.time() - start_time
            error_msg = f"Pattern extraction timed out after {elapsed:.1f} seconds - SDK may be unavailable or content too complex"
            logger.error(error_msg)
            return FocusedExtractionResult(
                extraction_type="patterns", data=[], extraction_time=elapsed, error=error_msg
            )
        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = f"Pattern extraction failed: {str(e) or 'Unknown error occurred'}"
            # Don't log here - let the caller handle error display
            return FocusedExtractionResult(
                extraction_type="patterns", data=[], extraction_time=elapsed, error=error_msg
            )


class FocusedKnowledgeExtractor:
    """Orchestrates focused extractions for better quality results"""

    def __init__(self):
        """Initialize all focused extractors"""
        self.concept_extractor = ConceptExtractor()
        self.relationship_extractor = RelationshipExtractor()
        self.insight_extractor = InsightExtractor()
        self.pattern_extractor = PatternExtractor()

    async def extract_all(
        self, text: str, title: str = "", document_type: str = "general"
    ) -> dict[str, FocusedExtractionResult]:
        """Run all focused extractors in parallel

        Returns dict with keys: concepts, relationships, insights, patterns
        """
        # Run all extractors in parallel for efficiency
        tasks = [
            self.concept_extractor.extract(text, title, document_type),
            self.relationship_extractor.extract(text, title, document_type),
            self.insight_extractor.extract(text, title, document_type),
            self.pattern_extractor.extract(text, title, document_type),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        extraction_results = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Extraction {i} failed: {result}")
                # Create empty result for failed extraction
                extraction_type = ["concepts", "relationships", "insights", "patterns"][i]
                extraction_results[extraction_type] = FocusedExtractionResult(
                    extraction_type=extraction_type, data=[], extraction_time=0.0, error=str(result)
                )
            elif isinstance(result, FocusedExtractionResult):
                extraction_results[result.extraction_type] = result

        return extraction_results

    async def extract_sequential(self, text: str, title: str = "") -> dict[str, FocusedExtractionResult]:
        """Run focused extractors sequentially (for debugging or when parallel isn't desired)

        Returns dict with keys: concepts, relationships, insights, patterns
        """
        extraction_results = {}

        # Extract concepts
        extraction_results["concepts"] = await self.concept_extractor.extract(text, title)

        # Extract relationships
        extraction_results["relationships"] = await self.relationship_extractor.extract(text, title)

        # Extract insights
        extraction_results["insights"] = await self.insight_extractor.extract(text, title)

        # Extract patterns
        extraction_results["patterns"] = await self.pattern_extractor.extract(text, title)

        return extraction_results
