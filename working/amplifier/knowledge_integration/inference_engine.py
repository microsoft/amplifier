"""
Relationship Inference Engine - Discovers implicit relationships through rule-based inference.

Following ruthless simplicity: direct rules, clear tracking, no over-engineering.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import field

from amplifier.knowledge_integration.models import Relationship

logger = logging.getLogger(__name__)


@dataclass
class InferenceRule:
    """A rule for inferring new relationships from existing ones."""

    name: str
    description: str
    apply: Callable[[list[Relationship]], list[Relationship]]
    confidence_factor: float = 0.8  # Inferred relationships have lower confidence


@dataclass
class InferredRelationship(Relationship):
    """A relationship that was inferred rather than directly extracted."""

    inference_chain: list[str] = field(default_factory=list)  # Track how it was inferred
    rule_used: str | None = None


class RelationshipInferenceEngine:
    """
    Infers new relationships from existing ones using rule-based patterns.

    Implements:
    - Transitive relationships (A→B, B→C implies A→C)
    - Symmetric relationships (A↔B implies B↔A)
    - Inverse relationships (parent/child, contains/part-of)
    - Type-based inference (inheritance of properties)
    """

    def __init__(self, confidence_decay: float = 0.8):
        """
        Initialize the inference engine.

        Args:
            confidence_decay: Factor to reduce confidence for each inference step
        """
        self.confidence_decay = confidence_decay
        self.rules = self._initialize_rules()

        # Track what we've already inferred to avoid loops
        self.inferred_cache: set[tuple[str, str, str]] = set()

    def _initialize_rules(self) -> list[InferenceRule]:
        """Initialize the inference rules."""
        return [
            InferenceRule(
                name="transitive",
                description="If A→B and B→C, then A→C",
                apply=self._apply_transitive,
                confidence_factor=self.confidence_decay,
            ),
            InferenceRule(
                name="symmetric",
                description="If A↔B, then B↔A",
                apply=self._apply_symmetric,
                confidence_factor=1.0,  # Symmetric relationships maintain confidence
            ),
            InferenceRule(
                name="inverse",
                description="Inverse relationships like parent/child",
                apply=self._apply_inverse,
                confidence_factor=0.9,
            ),
            InferenceRule(
                name="type_inheritance",
                description="If A is-a B and B has property P, then A has property P",
                apply=self._apply_type_inheritance,
                confidence_factor=self.confidence_decay,
            ),
        ]

    def infer_relationships(
        self, relationships: list[Relationship], max_iterations: int = 3
    ) -> list[InferredRelationship]:
        """
        Infer new relationships from existing ones.

        Args:
            relationships: Existing relationships
            max_iterations: Maximum inference iterations to prevent runaway

        Returns:
            List of newly inferred relationships
        """
        all_relationships = relationships.copy()
        inferred = []

        for iteration in range(max_iterations):
            new_inferred = []

            for rule in self.rules:
                rule_inferred = rule.apply(all_relationships)

                for rel in rule_inferred:
                    # Check if we've already inferred this
                    cache_key = (rel.subject, rel.predicate, rel.object)
                    if cache_key not in self.inferred_cache:
                        self.inferred_cache.add(cache_key)

                        # Create InferredRelationship with metadata
                        inferred_rel = InferredRelationship(
                            subject=rel.subject,
                            predicate=rel.predicate,
                            object=rel.object,
                            confidence=rel.confidence * rule.confidence_factor,
                            source="inference",
                            rule_used=rule.name,
                            inference_chain=[f"iteration_{iteration}", rule.name],
                        )

                        new_inferred.append(inferred_rel)

            if not new_inferred:
                # No new relationships inferred, stop
                break

            all_relationships.extend(new_inferred)
            inferred.extend(new_inferred)

            logger.info(f"Iteration {iteration + 1}: Inferred {len(new_inferred)} new relationships")

        return inferred

    def _apply_transitive(self, relationships: list[Relationship]) -> list[Relationship]:
        """
        Apply transitive rule: If A→B and B→C, then A→C.

        Only applies to specific predicates that are transitive.
        """
        transitive_predicates = {
            "is-a",
            "is_a",
            "type-of",
            "subtype-of",
            "part-of",
            "component-of",
            "member-of",
            "depends-on",
            "requires",
            "uses",
            "extends",
            "implements",
            "inherits-from",
        }

        inferred = []

        # Group relationships by subject and object for efficient lookup
        by_subject = {}
        by_object = {}

        for rel in relationships:
            if rel.predicate in transitive_predicates:
                if rel.subject not in by_subject:
                    by_subject[rel.subject] = []
                by_subject[rel.subject].append(rel)

                if rel.object not in by_object:
                    by_object[rel.object] = []
                by_object[rel.object].append(rel)

        # Find transitive chains
        for rel1 in relationships:
            if rel1.predicate not in transitive_predicates:
                continue

            # Find relationships where rel1.object is the subject
            if rel1.object in by_subject:
                for rel2 in by_subject[rel1.object]:
                    if rel2.predicate == rel1.predicate:
                        # Same predicate, can infer transitive relationship
                        inferred.append(
                            Relationship(
                                subject=rel1.subject,
                                predicate=rel1.predicate,
                                object=rel2.object,
                                confidence=min(rel1.confidence, rel2.confidence),
                            )
                        )

        return inferred

    def _apply_symmetric(self, relationships: list[Relationship]) -> list[Relationship]:
        """
        Apply symmetric rule: If A↔B, then B↔A.

        Only applies to specific predicates that are symmetric.
        """
        symmetric_predicates = {
            "related-to",
            "connected-to",
            "associated-with",
            "similar-to",
            "equivalent-to",
            "same-as",
            "interacts-with",
            "communicates-with",
        }

        inferred = []

        for rel in relationships:
            if rel.predicate in symmetric_predicates:
                # Create the symmetric relationship
                inferred.append(
                    Relationship(
                        subject=rel.object,
                        predicate=rel.predicate,
                        object=rel.subject,
                        confidence=rel.confidence,
                    )
                )

        return inferred

    def _apply_inverse(self, relationships: list[Relationship]) -> list[Relationship]:
        """
        Apply inverse relationships.

        If A has relationship R to B, then B has inverse(R) to A.
        """
        inverse_pairs = {
            "parent-of": "child-of",
            "child-of": "parent-of",
            "contains": "part-of",
            "part-of": "contains",
            "owns": "owned-by",
            "owned-by": "owns",
            "manages": "managed-by",
            "managed-by": "manages",
            "supervises": "supervised-by",
            "supervised-by": "supervises",
            "teaches": "taught-by",
            "taught-by": "teaches",
        }

        inferred = []

        for rel in relationships:
            if rel.predicate in inverse_pairs:
                inverse_predicate = inverse_pairs[rel.predicate]
                inferred.append(
                    Relationship(
                        subject=rel.object,
                        predicate=inverse_predicate,
                        object=rel.subject,
                        confidence=rel.confidence,
                    )
                )

        return inferred

    def _apply_type_inheritance(self, relationships: list[Relationship]) -> list[Relationship]:
        """
        Apply type inheritance rule.

        If A is-a B and B has property P, then A has property P.
        """
        inheritance_predicates = {"is-a", "is_a", "type-of", "subtype-of", "extends", "implements"}

        inferred = []

        # Find all inheritance relationships
        inheritance_chains = {}
        for rel in relationships:
            if rel.predicate in inheritance_predicates:
                if rel.subject not in inheritance_chains:
                    inheritance_chains[rel.subject] = []
                inheritance_chains[rel.subject].append(rel.object)

        # For each entity with inheritance, inherit properties from parent
        for rel in relationships:
            # Skip inheritance relationships themselves
            if rel.predicate in inheritance_predicates:
                continue

            # Find all entities that inherit from rel.subject
            for child, parents in inheritance_chains.items():
                if rel.subject in parents:
                    # Child inherits this property
                    inferred.append(
                        Relationship(
                            subject=child,
                            predicate=rel.predicate,
                            object=rel.object,
                            confidence=rel.confidence * 0.9,  # Slightly lower confidence for inherited
                        )
                    )

        return inferred

    def clear_cache(self) -> None:
        """Clear the inference cache."""
        self.inferred_cache.clear()

    def get_statistics(self) -> dict[str, int]:
        """Get statistics about the inference engine."""
        return {
            "rules_count": len(self.rules),
            "cached_inferences": len(self.inferred_cache),
        }
