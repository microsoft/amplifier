#!/usr/bin/env python3
"""
Knowledge Assistant - Main interface for AI to use the knowledge mining system.
Clean, practical API for extracting and applying knowledge from articles.
"""

import json
import logging
from pathlib import Path
from typing import Any

from amplifier.config.paths import paths

from .config import get_config
from .insight_generator import Insight
from .insight_generator import InsightGenerator
from .knowledge_extractor import KnowledgeExtractor
from .knowledge_store import KnowledgeStore
from .pattern_finder import Pattern
from .pattern_finder import PatternFinder

logger = logging.getLogger(__name__)


class KnowledgeAssistant:
    """Main interface for knowledge mining and application"""

    def __init__(self, storage_dir: Path | None = None):
        """Initialize the knowledge assistant"""
        # Use configured directory for all storage
        config = get_config()
        self.storage_dir = storage_dir or config.knowledge_mining_storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.extractor = KnowledgeExtractor()
        self.store = KnowledgeStore(paths.data_dir / "knowledge" / "store.json")
        self.pattern_finder = PatternFinder()
        self.insight_generator = InsightGenerator(self.store)

        # Load existing extractions into pattern finder
        self._sync_pattern_finder()

    def process_article(
        self, content: str, title: str = "Unknown", source: str = "Unknown", document_type: str = "general"
    ) -> dict[str, Any]:
        """Process an article and extract knowledge

        Args:
            content: The text content to process
            title: Title of the document
            source: Source identifier/path
            document_type: Type of document (see config for valid types)
        """

        # Check if source has already been processed
        if source != "Unknown" and self.store.is_source_processed(source):
            logger.info(f"Skipping already processed source: {source}")
            return {
                "title": title,
                "source": source,
                "status": "skipped",
                "reason": "already_processed",
                "concepts_extracted": 0,
                "relationships_found": 0,
                "insights_captured": 0,
                "code_patterns": 0,
                "nodes_created": 0,
            }

        # Extract knowledge with document type
        logger.info(f"Starting extraction for: {title} (type: {document_type})")
        try:
            extraction = self.extractor.extract(content, title=title, source=source, document_type=document_type)
        except RuntimeError as e:
            if "timeout" in str(e).lower():
                logger.error(f"Extraction timed out for {source} - stopping all extraction")
                raise  # Re-raise to stop processing
            raise
        logger.info(
            f"Extraction complete: {len(extraction.concepts)} concepts, {len(extraction.key_insights)} insights"
        )

        # Store in knowledge base
        node_ids = self.store.add_extraction(extraction)

        # Add to pattern finder
        self.pattern_finder.add_extraction(extraction)

        # Save store
        self.store.save()

        return {
            "title": title,
            "source": source,
            "status": "processed",
            "concepts_extracted": len(extraction.concepts),
            "relationships_found": len(extraction.relationships),
            "insights_captured": len(extraction.key_insights),
            "code_patterns": len(extraction.code_patterns),
            "nodes_created": len(node_ids),
        }

    def process_directory(
        self, directory: Path, pattern: str = "*.md", document_type: str = "general"
    ) -> list[dict[str, Any]]:
        """Process all articles in a directory

        Args:
            directory: Directory containing documents
            pattern: File pattern to match
            document_type: Type of documents in directory
        """
        results = []

        for file_path in directory.glob(pattern):
            try:
                content = file_path.read_text()
                title = file_path.stem.replace("_", " ").title()

                # Use intelligent classification if document type is general
                file_type = document_type
                if document_type == "general":
                    # Use Claude Haiku for intelligent classification
                    file_type = self.extractor.classify_document(content, title)
                    logger.info(f"Classified {file_path.name} as: {file_type}")

                # Convert to relative path for consistent storage
                try:
                    relative_path = file_path.relative_to(Path.cwd())
                    source_path = str(relative_path)
                except ValueError:
                    # If not relative to cwd, use absolute path
                    source_path = str(file_path)

                result = self.process_article(content, title=title, source=source_path, document_type=file_type)
                results.append(result)
                if result["status"] == "skipped":
                    print(f"Skipped (already processed): {title}")
                else:
                    print(f"Processed: {title} (type: {file_type})")
            except RuntimeError as e:
                if "timeout" in str(e).lower():
                    print("\nTimeout occurred - stopping all extraction")
                    print(
                        f"Successfully processed {len([r for r in results if r.get('status') == 'processed'])} files before timeout"
                    )
                    break  # Stop processing more files
                print(f"Error processing {file_path}: {e}")
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

        return results

    def find_patterns(self, min_occurrences: int = 2) -> list[Pattern]:
        """Find patterns across all processed articles"""
        return self.pattern_finder.find_patterns(min_occurrences)

    def generate_insights(self, context: str | None = None) -> list[Insight]:
        """Generate insights from discovered patterns"""
        patterns = self.find_patterns()
        return self.insight_generator.generate_insights(patterns, context or "")

    def solve_problem(self, problem_description: str) -> dict[str, Any]:
        """Find relevant knowledge and insights for a specific problem"""

        # Extract key terms from problem
        key_terms = self._extract_problem_terms(problem_description)

        # Find relevant concepts
        relevant_concepts = []
        for term in key_terms:
            nodes = self.store.query(concept=term)
            relevant_concepts.extend(nodes)

        # Find related patterns
        relevant_patterns = []
        patterns = self.find_patterns(min_occurrences=1)
        for pattern in patterns:
            if any(term in " ".join(pattern.concepts_involved).lower() for term in key_terms):
                relevant_patterns.append(pattern)

        # Generate problem-specific insights
        problem_insights = self.insight_generator.generate_problem_insights(problem_description)

        # Generate pattern-based insights
        pattern_insights = self.insight_generator.generate_insights(relevant_patterns, problem_description)

        # Combine and sort all insights
        all_insights = problem_insights + pattern_insights
        all_insights.sort(key=lambda i: i.confidence, reverse=True)

        return {
            "problem": problem_description,
            "key_terms": key_terms,
            "relevant_concepts": [
                {
                    "name": c.content.get("name", "unknown"),
                    "description": c.content.get("description", "")[:100],
                    "sources": c.sources,  # Return all sources
                }
                for c in relevant_concepts  # Return all relevant concepts
            ],
            "patterns_found": [
                {
                    "type": p.pattern_type,
                    "description": p.description,
                    "strength": p.strength,
                }
                for p in relevant_patterns  # Return all patterns
            ],
            "insights": [
                {
                    "type": i.type,
                    "title": i.title,
                    "description": i.description,
                    "confidence": i.confidence,
                    "actions": i.action_items,
                }
                for i in all_insights  # Return all insights
            ],
            "recommended_actions": self._compile_action_plan(all_insights[:5]),
        }

    def query_knowledge(self, query: str) -> dict[str, Any]:
        """Query the knowledge base with natural language"""

        # Simple query parsing
        query_lower = query.lower()

        results = {
            "query": query,
            "concepts": [],
            "insights": [],
            "patterns": [],
            "code_examples": [],
        }

        # Extract concepts mentioned in query
        words = query_lower.split()
        for word in words:
            if len(word) > 3:  # Simple filter
                nodes = self.store.query(concept=word)
                if nodes:
                    for node in nodes[:3]:
                        if node.type == "concept":
                            results["concepts"].append(
                                {
                                    "name": node.content.get("name"),
                                    "description": node.content.get("description", "")[:100],
                                }
                            )
                        elif node.type == "code":
                            results["code_examples"].append(
                                {
                                    "language": node.metadata.get("language"),
                                    "description": node.content.get("description"),
                                    "snippet": node.content.get("pattern", "")[:200],
                                }
                            )

        # Find relevant patterns
        patterns = self.find_patterns(min_occurrences=1)
        for pattern in patterns[:5]:
            if any(word in pattern.description.lower() for word in words if len(word) > 3):
                results["patterns"].append(
                    {
                        "type": pattern.pattern_type,
                        "description": pattern.description,
                        "strength": pattern.strength,
                    }
                )

        # Generate contextual insights
        insights = self.generate_insights(context=query)
        results["insights"] = [
            {
                "type": i.type,
                "title": i.title,
                "confidence": i.confidence,
            }
            for i in insights[:5]
        ]

        return results

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about the knowledge base"""
        stats = self.store.get_statistics()
        patterns = self.find_patterns(min_occurrences=1)

        stats["patterns_discovered"] = len(patterns)
        stats["pattern_types"] = {}
        for pattern in patterns:
            stats["pattern_types"][pattern.pattern_type] = stats["pattern_types"].get(pattern.pattern_type, 0) + 1

        return stats

    def export_knowledge(self, output_path: Path) -> None:
        """Export all knowledge to a JSON file"""
        export_data = {
            "statistics": self.get_statistics(),
            "patterns": [
                {
                    "type": p.pattern_type,
                    "description": p.description,
                    "strength": p.strength,
                    "concepts": p.concepts_involved,
                }
                for p in self.find_patterns(min_occurrences=1)
            ],
            "insights": [
                {
                    "type": i.type,
                    "title": i.title,
                    "description": i.description,
                    "confidence": i.confidence,
                }
                for i in self.generate_insights()
            ],
        }

        output_path.write_text(json.dumps(export_data, indent=2))

    def _sync_pattern_finder(self):
        """Sync pattern finder with stored extractions"""
        # This would need to reconstruct extractions from store
        # For now, pattern finder starts fresh each session

    def _extract_problem_terms(self, problem: str) -> list[str]:
        """Extract key terms from a problem description"""
        # Simple term extraction
        terms = []
        words = problem.lower().split()

        # Technical terms
        tech_words = [
            "api",
            "service",
            "data",
            "system",
            "design",
            "pattern",
            "architecture",
            "database",
            "cache",
            "async",
            "test",
            "deploy",
            "scale",
            "performance",
            "security",
        ]

        for word in words:
            if word in tech_words or (len(word) > 5 and word.isalpha()):
                terms.append(word)

        return list(set(terms))[:10]

    def _compile_action_plan(self, insights: list[Insight]) -> list[str]:
        """Compile a prioritized action plan from insights"""
        action_plan = []
        seen_actions = set()

        for insight in insights:
            for action in insight.action_items:
                if action not in seen_actions:
                    seen_actions.add(action)
                    action_plan.append(f"[{insight.type}] {action}")

        return action_plan[:10]  # Top 10 actions

    def _detect_document_type(self, file_path: Path, content: str) -> str:
        """Simple heuristic to detect document type from filename and content

        Args:
            file_path: Path to the file
            content: Content of the file

        Returns:
            Detected document type
        """
        config = get_config()
        filename_lower = file_path.name.lower()
        content_lower = content.lower()[: config.knowledge_mining_classification_chars]  # Check configured chars

        # Check filename patterns
        if "api" in filename_lower or "endpoint" in filename_lower or "swagger" in filename_lower:
            return "api_docs"
        if "meeting" in filename_lower or "transcript" in filename_lower or "notes" in filename_lower:
            return "meeting"
        if "blog" in filename_lower or "post" in filename_lower:
            return "blog"
        if "tutorial" in filename_lower or "guide" in filename_lower or "howto" in filename_lower:
            return "tutorial"
        if "research" in filename_lower or "paper" in filename_lower or "study" in filename_lower:
            return "research"
        if "changelog" in filename_lower or "release" in filename_lower or "version" in filename_lower:
            return "changelog"
        if "readme" in filename_lower:
            return "readme"
        if "spec" in filename_lower or "rfc" in filename_lower:
            return "specification"
        if "review" in filename_lower or "pr_" in filename_lower:
            return "code_review"
        if "postmortem" in filename_lower or "incident" in filename_lower:
            return "post_mortem"

        # Check content patterns
        if any(term in content_lower for term in ["endpoint", "request", "response", "api key", "authentication"]) and (
            content_lower.count("endpoint") > 2 or content_lower.count("request") > 3
        ):
            return "api_docs"

        if any(term in content_lower for term in ["action items", "decided", "meeting", "attendees", "agenda"]):
            return "meeting"

        if any(term in content_lower for term in ["in this post", "i've been", "let me share", "my experience"]):
            return "blog"

        if any(term in content_lower for term in ["step 1", "step 2", "first, you", "next, we", "installation"]):
            return "tutorial"

        if any(term in content_lower for term in ["hypothesis", "methodology", "results show", "findings indicate"]):
            return "research"

        if any(term in content_lower for term in ["## [0-9]", "### added", "### fixed", "breaking changes"]):
            return "changelog"

        if any(term in content_lower for term in ["## installation", "## usage", "## contributing", "## license"]):
            return "readme"

        if any(term in content_lower for term in ["must", "shall", "requirement", "specification"]):
            return "specification"

        if any(term in content_lower for term in ["root cause", "timeline", "impact", "lessons learned"]):
            return "post_mortem"

        # Default to article for formal writing
        if any(term in content_lower for term in ["abstract", "introduction", "conclusion", "methodology"]):
            return "article"

        # Default to general
        return config.knowledge_mining_default_doc_type


def create_assistant(storage_dir: Path | None = None) -> KnowledgeAssistant:
    """Factory function to create a knowledge assistant"""
    return KnowledgeAssistant(storage_dir)


if __name__ == "__main__":
    # Example usage
    assistant = create_assistant()

    # Process a sample article
    sample_article = """
    # Building Scalable APIs with Microservices

    The principle of single responsibility is crucial for microservices. Each service should
    handle one business capability. Use the repository pattern for data access abstraction.

    Key techniques for scalability:
    - Implement caching at multiple levels
    - Use async communication between services
    - Apply the circuit breaker pattern for resilience

    ```python
    class APIGateway:
        async def route_request(self, request):
            service = self.service_registry.find(request.path)
            return await service.handle(request)
    ```

    Remember that monitoring and observability are essential. The main point is to build
    services that can scale independently.
    """

    result = assistant.process_article(sample_article, title="Scalable APIs", source="sample.md")
    print(f"Processed article: {json.dumps(result, indent=2)}")

    # Find patterns
    patterns = assistant.find_patterns(min_occurrences=1)
    print(f"\nFound {len(patterns)} patterns")

    # Solve a problem
    problem = "How do I make my API more scalable and handle high traffic?"
    solution = assistant.solve_problem(problem)
    print(f"\nProblem solution: {json.dumps(solution, indent=2)}")

    # Get statistics
    stats = assistant.get_statistics()
    print(f"\nKnowledge base stats: {json.dumps(stats, indent=2)}")
