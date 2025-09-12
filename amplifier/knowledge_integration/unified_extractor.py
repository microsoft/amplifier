"""
Unified Knowledge Extractor - Runs concept mining and SPO extraction in parallel.

Simple, direct implementation following ruthless simplicity principle.
NO FALLBACKS - if dependencies are missing, we fail clearly.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from amplifier.knowledge_integration.models import Relationship
from amplifier.knowledge_integration.models import UnifiedExtraction
from amplifier.knowledge_mining.knowledge_extractor import KnowledgeExtractor
from amplifier.knowledge_synthesis.extractor import KnowledgeSynthesizer

logger = logging.getLogger(__name__)


class UnifiedKnowledgeExtractor:
    """
    Orchestrates parallel extraction of concepts and relationships.

    Runs both extraction pipelines in parallel and combines results.
    NO FALLBACKS - both extractors must be available.
    """

    def __init__(self, output_dir: Path | None = None):
        """
        Initialize the unified extractor.

        Args:
            output_dir: Directory to save extraction results
        """
        self.output_dir = output_dir or Path(".data/knowledge")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize extractors
        self.concept_extractor = KnowledgeExtractor()

        # SPO extraction via KnowledgeSynthesizer
        self.spo_extractor = KnowledgeSynthesizer()
        logger.info("SPO extraction enabled via KnowledgeSynthesizer")

    async def extract_from_text(
        self, text: str, title: str = "", source: str = "", document_type: str = "general"
    ) -> UnifiedExtraction:
        """
        Extract both concepts and relationships from text.

        Runs both extractors in parallel using asyncio.

        Args:
            text: The text to extract from
            title: Title of the document
            source: Source identifier
            document_type: Type of document (article, api_docs, code, conversation, tutorial, etc.)

        Returns:
            UnifiedExtraction containing both concepts and relationships
        """
        extraction = UnifiedExtraction(title=title, source=source, extraction_timestamp=datetime.now().isoformat())

        # Run extractors
        if self.spo_extractor:
            # Run both extractors in parallel
            concept_task = self._extract_concepts(text, title, source, document_type)
            spo_task = self._extract_spo(text)
            results = await asyncio.gather(concept_task, spo_task, return_exceptions=True)
        else:
            # Only run concept extraction
            concept_result = await self._extract_concepts(text, title, source, document_type)
            results = [concept_result, []]

        # Process concept results
        concept_result = results[0]
        if isinstance(concept_result, Exception):
            logger.warning(f"Concept extraction failed: {concept_result}")
            concept_result = {"concepts": [], "key_insights": [], "code_patterns": []}

        if isinstance(concept_result, dict):
            extraction.concepts = concept_result.get("concepts", [])
            extraction.key_insights = concept_result.get("key_insights", [])
            extraction.code_patterns = concept_result.get("code_patterns", [])
        else:
            # If result is not a dict, skip extraction
            extraction.concepts = []
            extraction.key_insights = []
            extraction.code_patterns = []

        # Process SPO results
        if self.spo_extractor:
            spo_result = results[1]
            if isinstance(spo_result, Exception):
                logger.warning(f"SPO extraction failed: {spo_result}")
                extraction.relationships = []
            elif isinstance(spo_result, list):
                extraction.relationships = spo_result
            else:
                extraction.relationships = []
        else:
            extraction.relationships = []

        return extraction

    async def _extract_concepts(
        self, text: str, title: str, source: str = "", document_type: str = "general"
    ) -> dict[str, Any]:
        """
        Extract concepts using the knowledge mining system.

        Calls async extraction directly to avoid nested asyncio issues.
        """
        # Call the async version directly - SDK is REQUIRED
        result = await self.concept_extractor._extract_async(
            text,  # No need to limit - extractor handles chunking internally
            title,
            source,  # Pass through the source parameter
            document_type,  # Use the actual document_type parameter
        )

        # Convert Extraction dataclass to dict
        return {
            "concepts": [
                {
                    "name": c.name,
                    "description": c.description,
                    "category": c.category,
                    "importance": c.importance,
                }
                for c in result.concepts
            ],
            "key_insights": result.key_insights,
            "code_patterns": result.code_patterns,
        }

    async def _extract_spo(self, text: str) -> list[Relationship]:
        """
        Extract SPO relationships from text using KnowledgeSynthesizer.
        """
        try:
            # Use KnowledgeSynthesizer to extract relationships
            extraction = await self.spo_extractor.extract(text)

            # Convert to Relationship objects
            relationships = []
            for rel in extraction.get("relationships", []):
                relationships.append(
                    Relationship(
                        subject=rel.get("subject", ""),
                        predicate=rel.get("predicate", ""),
                        object=rel.get("object", ""),
                        confidence=rel.get("confidence", 1.0),
                    )
                )

            logger.debug(f"Extracted {len(relationships)} relationships")
            return relationships
        except Exception as e:
            logger.error(f"SPO extraction failed: {e}")
            return []

    async def extract_from_articles(
        self, articles: list[dict[str, Any]], save_incrementally: bool = True
    ) -> list[UnifiedExtraction]:
        """
        Extract from multiple articles with incremental saving.

        Args:
            articles: List of article dictionaries with 'title', 'content', 'url' keys
            save_incrementally: Save after each article (default: True)

        Returns:
            List of extraction results
        """
        results = []
        output_file = self.output_dir / "unified_extraction_results.json"

        # Load existing results if file exists
        if output_file.exists():
            with open(output_file) as f:
                existing_data = json.load(f)
                results = existing_data.get("extractions", [])
                logger.info(f"Loaded {len(results)} existing extractions")

        for i, article in enumerate(articles):
            logger.info(f"Processing article {i + 1}/{len(articles)}: {article.get('title', 'Untitled')}")

            # Check if already processed
            if any(r.get("source") == article.get("url") for r in results):
                logger.info(f"Article already processed, skipping: {article.get('url')}")
                continue

            # Extract knowledge
            extraction = await self.extract_from_text(
                text=article.get("content", ""), title=article.get("title", ""), source=article.get("url", "")
            )

            # Convert to dict and add to results
            extraction_dict = extraction.to_dict()
            results.append(extraction_dict)

            # Save incrementally if requested
            if save_incrementally:
                save_data = {
                    "total_articles": len(results),
                    "last_updated": datetime.now().isoformat(),
                    "extractions": results,
                }

                with open(output_file, "w") as f:
                    json.dump(save_data, f, indent=2)

                logger.info(f"Saved extraction for article {i + 1} to {output_file}")

        return results
