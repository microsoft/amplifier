#!/usr/bin/env python3
"""
Knowledge Extractor - Real LLM-powered extraction using Claude Code SDK.
Simple, direct implementation that actually extracts semantic knowledge.
"""

import asyncio
import json
import logging
import subprocess
import time
from dataclasses import dataclass
from dataclasses import field
from typing import Any

from .config import get_config

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
class Concept:
    """A concept or idea extracted from text"""

    name: str
    description: str
    category: str  # pattern, technique, principle, tool, concept
    importance: float = 0.5  # 0-1 scale


@dataclass
class Relationship:
    """A relationship between two concepts"""

    source: str
    target: str
    relationship_type: str
    description: str = ""


@dataclass
class Extraction:
    """Complete extraction from a document"""

    title: str
    source: str
    concepts: list[Concept] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    key_insights: list[str] = field(default_factory=list)
    code_patterns: list[dict[str, str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class KnowledgeExtractor:
    """Extract knowledge from text using Claude Code SDK"""

    def __init__(self):
        """Initialize the extractor and REQUIRE Claude Code SDK"""
        # Check if claude CLI is installed - FAIL if not found
        try:
            result = subprocess.run(["which", "claude"], capture_output=True, text=True, timeout=2)
            if result.returncode != 0:
                raise RuntimeError(
                    "\n\n"
                    + "=" * 60
                    + "\n"
                    + "FATAL: Claude CLI not found!\n"
                    + "The Claude Code SDK is REQUIRED for knowledge extraction.\n"
                    + "Install with: npm install -g @anthropic-ai/claude-code\n"
                    + "=" * 60
                    + "\n"
                )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            raise RuntimeError(
                "\n\n"
                + "=" * 60
                + "\n"
                + "FATAL: Could not check for Claude CLI!\n"
                + "Install with: npm install -g @anthropic-ai/claude-code\n"
                + "=" * 60
                + "\n"
            )

        # Also check Python SDK is available
        if not CLAUDE_SDK_AVAILABLE:
            raise RuntimeError(
                "\n\n"
                + "=" * 60
                + "\n"
                + "FATAL: Claude Code SDK Python package not found!\n"
                + "Install with: pip install claude-code-sdk\n"
                + "=" * 60
                + "\n"
            )

        logger.debug("Claude Code SDK verified and ready")

    def classify_document(self, text: str, title: str = "") -> str:
        """Classify document type using Claude Code SDK - REQUIRED

        Args:
            text: The text content to classify (first 1500 chars used)
            title: Optional title to help with classification

        Returns:
            Document type from config's valid types
        """
        # Run async classification synchronously
        try:
            return asyncio.run(self._classify_document_async(text, title))
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            raise RuntimeError(f"FATAL: Document classification failed: {e}") from e

    async def _classify_document_async(self, text: str, title: str = "") -> str:
        """Async document classification using Claude Haiku"""
        config = get_config()
        # Use configured chars for fast classification
        sample_text = text[: config.knowledge_mining_classification_chars]

        classification_prompt = f"""Classify this document into ONE of these categories:
- article: formal article, research paper, or technical documentation
- api_docs: API documentation, endpoint descriptions, or integration guides
- meeting: meeting notes, transcripts, or discussion summaries
- blog: blog post, personal narrative, or informal writing
- tutorial: step-by-step guides, how-to documentation
- research: academic papers, studies, white papers
- changelog: release notes, version updates, migration guides
- readme: project documentation, setup guides
- specification: RFCs, technical specifications, standards
- conversation: chat logs, interviews, Q&A sessions
- code_review: PR reviews, code feedback, architecture discussions
- post_mortem: incident analysis, lessons learned
- general: doesn't clearly fit other categories

Title: {title if title else "(no title)"}

Content sample:
{sample_text}

Respond with ONLY the category name, nothing else."""

        try:
            # Check if SDK is available (should never happen since we check in __init__)
            if not CLAUDE_SDK_AVAILABLE or ClaudeSDKClient is None or ClaudeCodeOptions is None:
                raise RuntimeError("FATAL: Claude Code SDK not available for classification")

            # Use 10-minute timeout for SDK operations (600 seconds)
            async with asyncio.timeout(600):
                # Use configured model for fast classification with minimal turns
                async with ClaudeSDKClient(
                    options=ClaudeCodeOptions(
                        system_prompt="You are a document classifier. Respond with only the category name.",
                        max_turns=1,
                        model=config.knowledge_mining_model,  # Fast, efficient model for classification
                    )
                ) as client:
                    await client.query(classification_prompt)

                    # Collect response
                    response = ""
                    async for message in client.receive_response():
                        if hasattr(message, "content"):
                            content = getattr(message, "content", [])
                            if isinstance(content, list):
                                for block in content:
                                    if hasattr(block, "text"):
                                        response += getattr(block, "text", "")

                    # Clean and validate response
                    doc_type = response.strip().lower()
                    valid_types = config.get_valid_document_types()

                    if doc_type in valid_types:
                        logger.debug(f"Document classified as: {doc_type}")
                        return doc_type
                    logger.warning(f"Invalid classification '{doc_type}', defaulting to 'general'")
                    return "general"

        except TimeoutError:
            logger.error("Claude Code SDK timed out after 600 seconds for classification")
            raise RuntimeError("FATAL: Classification timeout - Claude Code SDK not responding")
        except Exception as e:
            logger.error(f"Error during classification: {e}")
            raise RuntimeError(f"FATAL: Classification failed: {e}") from e

        # This should never be reached due to exceptions, but satisfies type checker
        raise RuntimeError("FATAL: Unexpected classification failure")

    def extract(self, text: str, title: str = "", source: str = "", document_type: str = "general") -> Extraction:
        """Extract knowledge from text - REQUIRES Claude Code SDK

        Args:
            text: The text content to extract from
            title: Title of the document
            source: Source identifier/path
            document_type: Type of document (see config for valid types)
        """
        try:
            # Simple synchronous wrapper - always create new event loop
            return asyncio.run(self._extract_async(text, title, source, document_type))
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            raise RuntimeError(f"FATAL: Knowledge extraction failed: {e}") from e

    async def _extract_async(
        self, text: str, title: str = "", source: str = "", document_type: str = "general"
    ) -> Extraction:
        """Extract knowledge from text using LLM"""
        logger.info(f"Starting extraction for: {title} (source: {source}, type: {document_type})")
        start_time = time.time()

        # Note: Token-based truncation is handled by the caller (resilient_miner.py)
        # We accept the text as-is since it's already been truncated to token limits
        config = get_config()

        try:
            # Build document-type-specific prompt
            prompt = self._build_extraction_prompt(text, title, document_type)

            # Check if SDK is available
            if not CLAUDE_SDK_AVAILABLE or ClaudeSDKClient is None or ClaudeCodeOptions is None:
                logger.error("Claude Code SDK not available - cannot extract knowledge")
                raise RuntimeError("Claude Code SDK is required for knowledge extraction")

            # Use Claude Code SDK to extract knowledge
            logger.info("Initializing Claude Code SDK client...")

            response = ""  # Initialize response before the async with block

            # Use 10-minute timeout for SDK operations (600 seconds)
            async with asyncio.timeout(600):
                async with ClaudeSDKClient(
                    options=ClaudeCodeOptions(
                        system_prompt="You are a knowledge extraction expert. Extract structured knowledge from articles. Return ONLY valid JSON with no other text.",
                        max_turns=1,
                        model=config.knowledge_mining_extraction_model,  # More powerful model for extraction
                    )
                ) as client:
                    # Send query
                    logger.info("Sending query to Claude Code SDK...")
                    await client.query(prompt)

                    # Collect response - trust the SDK to work
                    logger.info("Waiting for Claude Code SDK response...")
                    async for message in client.receive_response():
                        if hasattr(message, "content"):
                            content = getattr(message, "content", [])
                            if isinstance(content, list):
                                for block in content:
                                    if hasattr(block, "text"):
                                        response += getattr(block, "text", "")

            elapsed = time.time() - start_time
            logger.info(f"Received response in {elapsed:.1f} seconds ({len(response)} characters)")

            # Check for empty response (happens when interrupted)
            if not response or not response.strip():
                logger.info("Empty response received - likely interrupted")
                raise RuntimeError("Extraction interrupted - no response received")

            # Parse JSON response
            # Strip markdown code block formatting if present
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]  # Remove ```json
            elif cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]  # Remove ```

            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]  # Remove trailing ```

            # Strip any remaining whitespace
            cleaned_response = cleaned_response.strip()

            try:
                data = json.loads(cleaned_response)

                # Convert to our data structures
                concepts = [
                    Concept(
                        name=c.get("name", ""),
                        description=c.get("description", ""),
                        category=c.get("category", "concept"),
                        importance=float(c.get("importance", 0.5)),
                    )
                    for c in data.get("concepts", [])
                    if c.get("name")
                ]

                relationships = [
                    Relationship(
                        source=r.get("source", ""),
                        target=r.get("target", ""),
                        relationship_type=r.get("type", "related"),
                        description=r.get("description", ""),
                    )
                    for r in data.get("relationships", [])
                    if r.get("source") and r.get("target")
                ]

                # Extract ALL insights and patterns - no artificial limits
                insights = data.get("insights", [])
                code_patterns = data.get("code_patterns", [])

                elapsed = time.time() - start_time
                logger.info(
                    f"Extraction completed in {elapsed:.1f}s: {len(concepts)} concepts, {len(insights)} insights"
                )

                return Extraction(
                    title=title,
                    source=source,
                    concepts=concepts,
                    relationships=relationships,
                    key_insights=insights,
                    code_patterns=code_patterns,
                    metadata={"extraction_method": "llm", "text_length": len(text), "extraction_time": elapsed},
                )

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.error("Original response: %s", response[:500] if response else "(empty)")
                logger.error("Cleaned response: %s", cleaned_response[:500] if cleaned_response else "(empty)")
                raise ValueError(
                    f"LLM did not return valid JSON.\nOriginal length: {len(response)}\nCleaned length: {len(cleaned_response)}\nError: {e}"
                ) from e

        except TimeoutError:
            # Handles both asyncio.TimeoutError and builtin TimeoutError (asyncio.TimeoutError is a subclass in Python 3.11+)
            elapsed = time.time() - start_time
            logger.error(f"Claude Code SDK timed out after 600 seconds for extraction (total time: {elapsed:.1f}s)")
            logger.error("FATAL: Extraction timeout - Claude Code SDK not responding")
            raise RuntimeError("FATAL: Claude Code SDK timeout - extraction cannot continue")
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Error during LLM extraction after {elapsed:.1f}s: {e}")
            raise RuntimeError(f"Failed to extract knowledge after {elapsed:.1f}s: {e}") from e

    def _build_extraction_prompt(self, text: str, title: str, document_type: str) -> str:
        """Build document-type-specific extraction prompt"""

        # Base JSON structure (same for all types)
        json_format = """
{
  "concepts": [
    {
      "name": "concept name",
      "description": "one sentence description",
      "category": "pattern|technique|principle|tool|concept",
      "importance": 0.0-1.0
    }
  ],
  "relationships": [
    {
      "source": "concept1",
      "target": "concept2",
      "type": "depends|contains|alternatives|enhances|uses",
      "description": "brief description"
    }
  ],
  "insights": [
    "actionable insight or best practice",
    "warning or pitfall to avoid",
    "performance tip or optimization"
  ],
  "code_patterns": [
    {
      "name": "pattern name",
      "code": "code snippet or pseudo-code",
      "language": "python|javascript|etc",
      "purpose": "what problem it solves"
    }
  ]
}"""

        # Document-type-specific prompts
        if document_type == "api_docs":
            prompt = f"""Analyze this API documentation and extract structured knowledge.

Title: {title}

Content:
{text}

Extract the following in JSON format:
{json_format}

IMPORTANT: Extract ALL meaningful information. Do not limit yourself.

Focus on extracting:
- API endpoints and their purposes
- Request/response formats and parameters
- Authentication methods and requirements
- Rate limits and constraints
- Error codes and handling
- Usage examples and best practices
- Integration patterns
- SDK/library usage
- Versioning and compatibility notes

For code_patterns, focus on:
- API call examples
- Authentication flows
- Error handling patterns
- Request/response handling
- Pagination patterns

Return ONLY valid JSON, no other text."""

        elif document_type == "meeting":
            prompt = f"""Analyze this meeting transcript and extract structured knowledge.

Title: {title}

Content:
{text}

Extract the following in JSON format:
{json_format}

IMPORTANT: Extract ALL meaningful decisions and discussions. Do not limit yourself.

Focus on extracting:
- Decisions made and rationale
- Action items and owners
- Problems discussed and solutions proposed
- Technical approaches agreed upon
- Risks and concerns raised
- Timeline and milestones mentioned
- Dependencies identified
- Follow-up topics

For insights, focus on:
- Key decisions and their impact
- Action items that need attention
- Blockers or risks to address
- Important consensus points
- Unresolved questions

Return ONLY valid JSON, no other text."""

        elif document_type == "blog":
            prompt = f"""Analyze this blog post and extract structured knowledge.

Title: {title}

Content:
{text}

Extract the following in JSON format:
{json_format}

IMPORTANT: Extract ALL meaningful insights from the article. Do not limit yourself.
For a rich article, there might be 10-20 insights. For a simple article, there might be 2-3.

Focus on extracting:
- Technical patterns and techniques
- Best practices and principles
- Tools and technologies mentioned
- Author's opinions and recommendations
- Lessons learned and experiences
- Tips and tricks
- Common mistakes to avoid
- Code examples and implementations

Return ONLY valid JSON, no other text."""

        elif document_type == "article":
            # Similar to blog but more formal/academic
            prompt = f"""Analyze this article and extract structured knowledge.

Title: {title}

Content:
{text}

Extract the following in JSON format:
{json_format}

IMPORTANT: Extract ALL meaningful knowledge from the article. Do not limit yourself.

Focus on extracting:
- Core concepts and theories
- Methodologies and frameworks
- Research findings and data
- Case studies and examples
- Comparative analyses
- Best practices and standards
- Industry trends
- Technical implementations

Return ONLY valid JSON, no other text."""

        elif document_type == "tutorial":
            prompt = f"""Analyze this tutorial and extract structured knowledge.

Title: {title}

Content:
{text}

Extract the following in JSON format:
{json_format}

IMPORTANT: Extract ALL meaningful steps and instructions. Do not limit yourself.

Focus on extracting:
- Prerequisites and requirements
- Step-by-step instructions
- Configuration settings
- Common pitfalls and troubleshooting
- Expected outcomes and results
- Code snippets and commands
- Best practices for implementation
- Alternative approaches
- Testing and validation steps

For code_patterns, focus on:
- Setup and configuration examples
- Command sequences
- Code templates
- Testing patterns

Return ONLY valid JSON, no other text."""

        elif document_type == "research":
            prompt = f"""Analyze this research document and extract structured knowledge.

Title: {title}

Content:
{text}

Extract the following in JSON format:
{json_format}

IMPORTANT: Extract ALL meaningful findings and methodologies. Do not limit yourself.

Focus on extracting:
- Research questions and hypotheses
- Methodologies and approaches
- Key findings and results
- Statistical data and metrics
- Literature references and comparisons
- Limitations and constraints
- Future research directions
- Practical applications
- Theoretical contributions

For insights, focus on:
- Novel discoveries
- Contradictions to existing knowledge
- Practical implications
- Methodology innovations

Return ONLY valid JSON, no other text."""

        elif document_type == "changelog":
            prompt = f"""Analyze this changelog and extract structured knowledge.

Title: {title}

Content:
{text}

Extract the following in JSON format:
{json_format}

IMPORTANT: Extract ALL meaningful changes and updates. Do not limit yourself.

Focus on extracting:
- New features and capabilities
- Breaking changes and migrations
- Bug fixes and improvements
- Performance optimizations
- API changes
- Deprecations and removals
- Security updates
- Version compatibility notes
- Upgrade instructions

For insights, focus on:
- Migration strategies
- Compatibility concerns
- Performance impacts
- Security implications

Return ONLY valid JSON, no other text."""

        elif document_type == "readme":
            prompt = f"""Analyze this README documentation and extract structured knowledge.

Title: {title}

Content:
{text}

Extract the following in JSON format:
{json_format}

IMPORTANT: Extract ALL meaningful project information. Do not limit yourself.

Focus on extracting:
- Project purpose and goals
- Installation instructions
- Usage examples
- Configuration options
- Dependencies and requirements
- Architecture and design patterns
- Contributing guidelines
- API documentation
- Troubleshooting guides

For code_patterns, focus on:
- Installation commands
- Configuration examples
- Usage patterns
- API examples

Return ONLY valid JSON, no other text."""

        elif document_type == "specification":
            prompt = f"""Analyze this technical specification and extract structured knowledge.

Title: {title}

Content:
{text}

Extract the following in JSON format:
{json_format}

IMPORTANT: Extract ALL technical requirements and standards. Do not limit yourself.

Focus on extracting:
- Technical requirements
- Protocol definitions
- Data formats and schemas
- Interface contracts
- Compliance standards
- Performance requirements
- Security specifications
- Implementation constraints
- Validation rules

For insights, focus on:
- Critical requirements
- Implementation challenges
- Compliance needs
- Integration points

Return ONLY valid JSON, no other text."""

        elif document_type == "conversation":
            prompt = f"""Analyze this conversation/interview and extract structured knowledge.

Title: {title}

Content:
{text}

Extract the following in JSON format:
{json_format}

IMPORTANT: Extract ALL meaningful exchanges and insights. Do not limit yourself.

Focus on extracting:
- Key questions and answers
- Expert opinions and advice
- Problem descriptions and solutions
- Technical explanations
- Experience sharing
- Recommendations and warnings
- Clarifications and corrections
- Follow-up topics

For insights, focus on:
- Expert knowledge shared
- Problem-solving approaches
- Lessons from experience
- Unique perspectives

Return ONLY valid JSON, no other text."""

        elif document_type == "code_review":
            prompt = f"""Analyze this code review and extract structured knowledge.

Title: {title}

Content:
{text}

Extract the following in JSON format:
{json_format}

IMPORTANT: Extract ALL code review feedback and discussions. Do not limit yourself.

Focus on extracting:
- Code quality issues
- Architecture feedback
- Performance suggestions
- Security concerns
- Best practice violations
- Refactoring recommendations
- Testing requirements
- Documentation needs
- Design pattern discussions

For code_patterns, focus on:
- Problem code examples
- Suggested improvements
- Refactoring patterns
- Testing approaches

Return ONLY valid JSON, no other text."""

        elif document_type == "post_mortem":
            prompt = f"""Analyze this post-mortem and extract structured knowledge.

Title: {title}

Content:
{text}

Extract the following in JSON format:
{json_format}

IMPORTANT: Extract ALL incident details and learnings. Do not limit yourself.

Focus on extracting:
- Incident timeline and impact
- Root cause analysis
- Contributing factors
- Detection and response details
- Mitigation steps taken
- Lessons learned
- Action items and improvements
- Prevention strategies
- Process improvements

For insights, focus on:
- Critical failure points
- System weaknesses
- Process improvements
- Prevention measures
- Monitoring gaps

Return ONLY valid JSON, no other text."""

        else:  # "general" or unknown type
            prompt = f"""Analyze this document and extract structured knowledge.

Title: {title}

Content:
{text}

Extract the following in JSON format:
{json_format}

IMPORTANT: Extract ALL meaningful insights. Do not limit yourself.
Adapt your extraction based on the content type you observe.

Focus on extracting:
- Key concepts and ideas
- Relationships between concepts
- Practical insights and learnings
- Patterns and techniques
- Best practices and principles
- Tools and technologies
- Code examples (if present)
- Actionable recommendations

Return ONLY valid JSON, no other text."""

        return prompt


if __name__ == "__main__":
    # Test extraction
    try:
        extractor = KnowledgeExtractor()

        sample_text = """
        # Microservices Best Practices

        The repository pattern provides clean data access.
        Use circuit breaker pattern for resilience.
        Event sourcing helps with audit trails.
        Always implement proper authentication and caching.
        """

        # Test with default document type
        result = extractor.extract(sample_text, "Test Article", "test.md", document_type="blog")

        print(f"Extracted {len(result.concepts)} concepts")
        for concept in result.concepts:
            print(f"  - {concept.name}: {concept.description}")

        print(f"\nFound {len(result.key_insights)} insights")
        for insight in result.key_insights:
            print(f"  - {insight}")

    except RuntimeError as e:
        print(f"Error: {e}")
        print("\nThis tool requires Claude Code SDK to function.")
        print("Install with: pip install claude-code-sdk")
        print("And: npm install -g @anthropic-ai/claude-code")
