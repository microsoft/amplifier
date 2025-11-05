"""
Entity Resolver Module - Canonicalizes and resolves entity variations.

Simple fuzzy matching for entity resolution. No LLM fallbacks.
"""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from rapidfuzz import fuzz
from rapidfuzz import process

logger = logging.getLogger(__name__)


class MatchType(Enum):
    """Types of entity matches."""

    EXACT = "exact"
    FUZZY = "fuzzy"
    PLURAL = "plural"
    ABBREVIATION = "abbreviation"
    NONE = "none"


@dataclass
class EntityMatch:
    """Result of entity resolution."""

    original: str
    canonical: str
    confidence: float
    match_type: MatchType


class EntityResolver:
    """
    Simple entity resolver with fuzzy matching and caching.

    Follows the resolution hierarchy:
    1. Exact match (100% confidence)
    2. Plural/singular variations (95% confidence)
    3. Fuzzy match (threshold-based confidence)
    4. No match (create new canonical form)
    """

    def __init__(
        self,
        cache_path: Path | None = None,
        fuzzy_threshold: float = 80.0,
        use_intelligent_matching: bool = True,
    ):
        """
        Initialize the entity resolver.

        Args:
            cache_path: Path to cache file for resolved entities
            fuzzy_threshold: Minimum score for fuzzy matching (0-100)
            use_intelligent_matching: Use Claude Code SDK for intelligent entity matching
        """
        self.cache_path = cache_path or Path(".data/knowledge/entity_cache.json")
        self.fuzzy_threshold = fuzzy_threshold
        self.use_intelligent_matching = use_intelligent_matching

        # Canonical entity registry
        self.canonical_entities: set[str] = set()

        # Resolution cache: original -> (canonical, confidence, match_type)
        self.resolution_cache: dict[str, tuple[str, float, str]] = {}

        # Common abbreviations and synonyms (expanded)
        self.abbreviations: dict[str, str] = {
            "AI": "Artificial Intelligence",
            "ML": "Machine Learning",
            "LLM": "Large Language Model",
            "LLMs": "Large Language Models",
            "API": "Application Programming Interface",
            "APIs": "Application Programming Interfaces",
            "UI": "User Interface",
            "UX": "User Experience",
            "DB": "Database",
            "OS": "Operating System",
            "IDE": "Integrated Development Environment",
            "CI/CD": "Continuous Integration/Continuous Deployment",
            "GPT": "Generative Pre-trained Transformer",
            "NLP": "Natural Language Processing",
            "SDK": "Software Development Kit",
            "REST": "Representational State Transfer",
            "HTTP": "HyperText Transfer Protocol",
            "JSON": "JavaScript Object Notation",
            "XML": "eXtensible Markup Language",
            "SQL": "Structured Query Language",
            "NoSQL": "Not Only SQL",
            "CRUD": "Create Read Update Delete",
            "MVC": "Model-View-Controller",
            "MVP": "Model-View-Presenter",
            "MVVM": "Model-View-ViewModel",
            "TDD": "Test-Driven Development",
            "BDD": "Behavior-Driven Development",
            "DDD": "Domain-Driven Design",
            "OOP": "Object-Oriented Programming",
            "FP": "Functional Programming",
            "IoC": "Inversion of Control",
            "DI": "Dependency Injection",
            "DTO": "Data Transfer Object",
            "DAO": "Data Access Object",
            "ORM": "Object-Relational Mapping",
        }

        # Known entity variations (lowercase keys for case-insensitive matching)
        self.known_variations: dict[str, str] = {
            # ChatGPT variations
            "chatgpt": "ChatGPT",
            "chat gpt": "ChatGPT",
            "chat-gpt": "ChatGPT",
            "gpt chat": "ChatGPT",
            "openai chatgpt": "ChatGPT",
            "chatgpt-3": "ChatGPT",
            "chatgpt-3.5": "ChatGPT",
            "chatgpt-4": "ChatGPT-4",
            "gpt-4": "GPT-4",
            "gpt4": "GPT-4",
            "gpt-3": "GPT-3",
            "gpt3": "GPT-3",
            # Claude variations
            "claude": "Claude",
            "claude ai": "Claude",
            "claude-ai": "Claude",
            "anthropic claude": "Claude",
            "claude 2": "Claude 2",
            "claude 3": "Claude 3",
            "claude-2": "Claude 2",
            "claude-3": "Claude 3",
            "claude opus": "Claude 3 Opus",
            "claude sonnet": "Claude 3 Sonnet",
            "claude haiku": "Claude 3 Haiku",
            # Other AI models
            "gemini": "Gemini",
            "google gemini": "Gemini",
            "bard": "Bard",
            "google bard": "Bard",
            "llama": "LLaMA",
            "llama 2": "LLaMA 2",
            "llama2": "LLaMA 2",
            "mistral": "Mistral",
            "mixtral": "Mixtral",
            # Companies
            "openai": "OpenAI",
            "open ai": "OpenAI",
            "anthropic": "Anthropic",
            "google": "Google",
            "microsoft": "Microsoft",
            "meta": "Meta",
            "facebook": "Meta",
            # Technologies
            "python": "Python",
            "javascript": "JavaScript",
            "java script": "JavaScript",
            "js": "JavaScript",
            "typescript": "TypeScript",
            "type script": "TypeScript",
            "ts": "TypeScript",
            "react": "React",
            "reactjs": "React",
            "react.js": "React",
            "nodejs": "Node.js",
            "node.js": "Node.js",
            "node": "Node.js",
        }

        # Load cache if it exists
        if self.cache_path.exists():
            self.load_cache()

    def resolve(self, entity_name: str) -> EntityMatch:
        """
        Resolve an entity name to its canonical form.

        Args:
            entity_name: The entity name to resolve

        Returns:
            EntityMatch with canonical form and confidence
        """
        # Clean the input
        entity_name = entity_name.strip()

        # Check cache first
        if entity_name in self.resolution_cache:
            canonical, confidence, match_type = self.resolution_cache[entity_name]
            return EntityMatch(
                original=entity_name,
                canonical=canonical,
                confidence=confidence,
                match_type=MatchType(match_type),
            )

        # 1. Check for exact match
        if entity_name in self.canonical_entities:
            match = EntityMatch(
                original=entity_name,
                canonical=entity_name,
                confidence=1.0,
                match_type=MatchType.EXACT,
            )
            self._cache_resolution(match)
            return match

        # 2. Check known variations (case-insensitive)
        entity_lower = entity_name.lower()
        if entity_lower in self.known_variations:
            canonical = self.known_variations[entity_lower]
            match = EntityMatch(
                original=entity_name,
                canonical=canonical,
                confidence=0.98,
                match_type=MatchType.EXACT,  # Known variations are treated as exact matches
            )
            self._cache_resolution(match)
            self.canonical_entities.add(canonical)
            return match

        # 3. Check for abbreviation
        if entity_name.upper() in self.abbreviations:
            canonical = self.abbreviations[entity_name.upper()]
            match = EntityMatch(
                original=entity_name,
                canonical=canonical,
                confidence=0.95,
                match_type=MatchType.ABBREVIATION,
            )
            self._cache_resolution(match)
            self.canonical_entities.add(canonical)
            return match

        # 4. Check for plural/singular variations
        plural_match = self._check_plural_variations(entity_name)
        if plural_match:
            self._cache_resolution(plural_match)
            return plural_match

        # 5. Fuzzy matching with both canonical entities and known variation values
        if self.canonical_entities:
            # Create a combined set for fuzzy matching
            matching_pool = self.canonical_entities.copy()
            matching_pool.update(self.known_variations.values())

            best_match, score, _ = process.extractOne(
                entity_name,
                matching_pool,
                scorer=fuzz.ratio,
            )

            if score >= self.fuzzy_threshold:
                match = EntityMatch(
                    original=entity_name,
                    canonical=best_match,
                    confidence=score / 100.0,
                    match_type=MatchType.FUZZY,
                )
                self._cache_resolution(match)
                self.canonical_entities.add(best_match)
                return match

        # 6. No match - create new canonical form
        self.canonical_entities.add(entity_name)
        match = EntityMatch(
            original=entity_name,
            canonical=entity_name,
            confidence=1.0,
            match_type=MatchType.NONE,
        )
        self._cache_resolution(match)
        return match

    def _check_plural_variations(self, entity_name: str) -> EntityMatch | None:
        """
        Check for plural/singular variations of the entity.

        Args:
            entity_name: The entity name to check

        Returns:
            EntityMatch if a variation is found, None otherwise
        """
        # Simple plural/singular rules
        variations = []

        # Check if it ends with 's' and the singular exists
        if entity_name.endswith("s") and len(entity_name) > 1:
            singular = entity_name[:-1]
            if singular in self.canonical_entities:
                return EntityMatch(
                    original=entity_name,
                    canonical=singular,
                    confidence=0.95,
                    match_type=MatchType.PLURAL,
                )
            variations.append(singular)

        # Check if adding 's' gives us a match
        plural = entity_name + "s"
        if plural in self.canonical_entities:
            return EntityMatch(
                original=entity_name,
                canonical=plural,
                confidence=0.95,
                match_type=MatchType.PLURAL,
            )

        # Check for 'ies' plural (e.g., "entity" -> "entities")
        if entity_name.endswith("y") and len(entity_name) > 1:
            plural_ies = entity_name[:-1] + "ies"
            if plural_ies in self.canonical_entities:
                return EntityMatch(
                    original=entity_name,
                    canonical=plural_ies,
                    confidence=0.95,
                    match_type=MatchType.PLURAL,
                )

        # Check if it ends with 'ies' and the singular exists
        if entity_name.endswith("ies") and len(entity_name) > 3:
            singular_y = entity_name[:-3] + "y"
            if singular_y in self.canonical_entities:
                return EntityMatch(
                    original=entity_name,
                    canonical=singular_y,
                    confidence=0.95,
                    match_type=MatchType.PLURAL,
                )

        return None

    def _cache_resolution(self, match: EntityMatch) -> None:
        """Cache a resolution for future use."""
        self.resolution_cache[match.original] = (
            match.canonical,
            match.confidence,
            match.match_type.value,
        )

    def save_cache(self) -> None:
        """Save the resolution cache to disk."""
        cache_data = {
            "canonical_entities": list(self.canonical_entities),
            "resolution_cache": self.resolution_cache,
            "abbreviations": self.abbreviations,
        }

        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, "w") as f:
            json.dump(cache_data, f, indent=2)

        logger.info(f"Saved entity cache to {self.cache_path}")

    def load_cache(self) -> None:
        """Load the resolution cache from disk."""
        with open(self.cache_path) as f:
            cache_data = json.load(f)

        self.canonical_entities = set(cache_data.get("canonical_entities", []))
        self.resolution_cache = cache_data.get("resolution_cache", {})

        # Update abbreviations if provided
        saved_abbreviations = cache_data.get("abbreviations", {})
        self.abbreviations.update(saved_abbreviations)

        logger.info(
            f"Loaded {len(self.canonical_entities)} canonical entities "
            f"and {len(self.resolution_cache)} cached resolutions"
        )

    def batch_resolve(self, entity_names: list[str]) -> list[EntityMatch]:
        """
        Resolve multiple entity names.

        Args:
            entity_names: List of entity names to resolve

        Returns:
            List of EntityMatch results
        """
        results = []
        for name in entity_names:
            results.append(self.resolve(name))

        # Save cache after batch processing
        self.save_cache()

        return results

    def get_statistics(self) -> dict[str, int]:
        """Get statistics about the resolver."""
        match_type_counts = {}
        for _, _, match_type in self.resolution_cache.values():
            match_type_counts[match_type] = match_type_counts.get(match_type, 0) + 1

        return {
            "canonical_entities": len(self.canonical_entities),
            "cached_resolutions": len(self.resolution_cache),
            "abbreviations": len(self.abbreviations),
            **match_type_counts,
        }
