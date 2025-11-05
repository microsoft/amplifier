"""Enhanced claim validation against memories"""

import logging
import re
import sys
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).parent.parent))
from memory.models import StoredMemory
from search import MemorySearcher

from .models import ClaimValidation
from .models import ValidationResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClaimValidator:
    """Validate claims against stored memories with enhanced logic"""

    def __init__(self):
        """Initialize validator"""
        self.searcher = MemorySearcher()
        self.claim_patterns = self._compile_claim_patterns()

    def validate_text(self, text: str, memories: list[StoredMemory]) -> ValidationResult:
        """Validate all claims in text

        Args:
            text: Text containing claims
            memories: Memories to validate against

        Returns:
            Validation result with all claims
        """
        # Extract claims from text
        claims = self.extract_claims_from_text(text)

        # Validate each claim
        validations = []
        has_contradictions = False
        total_confidence = 0.0

        for claim_text in claims:
            validation = self.validate_claim(claim_text, memories)
            validations.append(validation)
            if validation.contradicts:
                has_contradictions = True
            total_confidence += validation.confidence

        # Calculate overall confidence
        overall_confidence = total_confidence / max(len(validations), 1)

        return ValidationResult(
            text=text, claims=validations, has_contradictions=has_contradictions, overall_confidence=overall_confidence
        )

    async def validate_claims(self, claims: list[str], memories: list[StoredMemory]) -> list[dict[str, Any]]:
        """Validate multiple claims (compatibility method)

        Args:
            claims: List of claims to validate
            memories: Memories to validate against

        Returns:
            List of validation results
        """
        results = []
        for claim in claims:
            try:
                validation = self.validate_claim(claim, memories)
                results.append(
                    {
                        "claim": claim,
                        "verdict": validation.verdict,
                        "confidence": validation.confidence,
                        "evidence": validation.evidence,
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to validate claim '{claim}': {e}")
                results.append({"claim": claim, "verdict": "unknown", "confidence": 0.0, "error": str(e)})

        return results

    def validate_claim(self, claim: str, memories: list[StoredMemory]) -> ClaimValidation:
        """Validate a single claim with enhanced logic

        Args:
            claim: The claim to validate
            memories: Memories to check against

        Returns:
            Validation result for the claim
        """
        if not memories:
            return ClaimValidation(claim=claim, confidence=0.0)

        # Check each memory for support or contradiction
        claim_lower = claim.lower()
        claim_words = set(claim_lower.split())

        supporting = []
        contradicting = []

        for memory in memories:
            memory_content = memory.content.lower()
            memory_words = set(memory_content.split())
            overlap = len(claim_words & memory_words)

            # Check for numeric contradictions
            claim_numbers = re.findall(r"\b(\d+(?:\.\d+)?)\b", claim_lower)
            memory_numbers = re.findall(r"\b(\d+(?:\.\d+)?)\b", memory_content)

            if claim_numbers and memory_numbers and overlap > min(3, len(claim_words) // 2):
                # Compare numbers
                claim_num = float(claim_numbers[0])
                memory_num = float(memory_numbers[0])

                if abs(claim_num - memory_num) / max(claim_num, memory_num, 1) > 0.2:
                    contradicting.append(memory)
                    continue

            # Check for negation patterns
            negations = ["not", "never", "don't", "doesn't", "won't", "can't", "isn't"]
            claim_has_negation = any(neg in claim_lower for neg in negations)
            memory_has_negation = any(neg in memory_content for neg in negations)

            if claim_has_negation != memory_has_negation and overlap > 3:
                # One statement negates the other
                contradicting.append(memory)
                continue

            # Check for contradictory database claims
            if (
                "mongodb" in claim_lower
                and "postgresql" in memory_content
                or "postgresql" in claim_lower
                and "mongodb" in memory_content
                or "mysql" in claim_lower
                and ("postgresql" in memory_content or "postgres" in memory_content)
            ) and ("database" in claim_lower or "primary" in claim_lower):
                contradicting.append(memory)
                continue

            # Check for contradictory framework claims
            if (
                "django" in claim_lower
                and "fastapi" in memory_content
                or "fastapi" in claim_lower
                and "django" in memory_content
            ) and ("framework" in claim_lower or "api" in claim_lower or "endpoints" in claim_lower):
                contradicting.append(memory)
                continue

            # Check for JavaScript vs TypeScript contradictions
            if (
                "javascript" in claim_lower
                and "typescript" in memory_content
                and "prefer" in memory_content
                and ("frontend" in claim_lower or "frontend" in memory_content)
                and any(word in claim_lower for word in ["should", "stick", "use", "better", "simpler"])
            ):
                # Claim is advocating for JavaScript over TypeScript
                contradicting.append(memory)
                continue

            # Check for support
            if overlap > min(4, len(claim_words) // 2):
                supporting.append(memory)

        # Determine verdict
        if contradicting:
            validation = ClaimValidation(
                claim=claim,
                verdict="contradicted",
                confidence=0.8,
                evidence=[m.content for m in contradicting[:2]],
                contradicts=True,
                conflicting_memory=contradicting[0],
            )
        elif supporting:
            validation = ClaimValidation(
                claim=claim,
                verdict="supported",
                confidence=0.7,
                evidence=[m.content for m in supporting[:2]],
                supports=True,
                supporting_memory=supporting[0],
            )
        else:
            validation = ClaimValidation(claim=claim, verdict="unknown", confidence=0.3, evidence=[])

        return validation

    def extract_claims_from_text(self, text: str) -> list[str]:
        """Extract factual claims from text - enhanced version

        Args:
            text: Text to extract claims from

        Returns:
            List of extracted claims
        """
        claims = []

        # Better sentence splitting that handles abbreviations
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)

        for sentence in sentences:
            sentence = sentence.strip()

            # Skip empty, questions, commands, greetings
            if not sentence or sentence.endswith("?"):
                continue

            # Skip imperative/command sentences
            if sentence.startswith(("Please", "Try", "Run", "Check", "Make", "Let's", "Let me")):
                continue

            # Skip conversational phrases
            if any(phrase in sentence.lower() for phrase in ["i think", "i believe", "maybe", "probably", "might be"]):
                continue

            sentence_lower = sentence.lower()

            # Look for strong factual indicators
            strong_indicators = [
                r"\b(is|are|was|were)\s+\w+",  # State of being
                r"\b(will|shall)\s+\w+",  # Future facts
                r"\b(has|have|had)\s+\w+",  # Possession/completion
                r"\b(uses?|requires?|needs?|supports?|provides?)\b",  # Technical specifications
                r"\b(always|never|must|cannot|can't)\b",  # Absolutes
                r"\b\d+\s*(?:seconds?|minutes?|hours?|days?|MB|GB|KB|%)\b",  # Quantitative claims
                r"\b(?:version|v\d+\.\d+)",  # Version numbers
                r"(?:framework|database|library|api|sdk|cli)\s+(?:is|was|will)",  # Technical decisions
            ]

            # Check if sentence contains factual patterns
            has_factual_pattern = any(re.search(pattern, sentence_lower) for pattern in strong_indicators)

            # Also check for specific technical claims
            technical_terms = [
                "postgresql",
                "mongodb",
                "mysql",
                "django",
                "fastapi",
                "express",
                "react",
                "vue",
                "typescript",
                "javascript",
                "python",
                "redis",
                "docker",
                "kubernetes",
                "api",
                "sdk",
            ]
            has_technical_claim = any(term in sentence_lower for term in technical_terms)

            # Include if it has factual patterns or makes technical claims with verbs
            if has_factual_pattern or (
                has_technical_claim
                and any(
                    verb in sentence_lower.split() for verb in ["is", "are", "was", "were", "will", "uses", "using"]
                )
            ):
                # Clean up the sentence
                clean_sentence = re.sub(r"\s+", " ", sentence).strip()
                if len(clean_sentence) > 10:  # Skip very short sentences
                    claims.append(clean_sentence)

        # Remove duplicates while preserving order
        seen = set()
        unique_claims = []
        for claim in claims:
            if claim.lower() not in seen:
                seen.add(claim.lower())
                unique_claims.append(claim)

        return unique_claims[:10]  # Return up to 10 claims for thoroughness

    def _compile_claim_patterns(self) -> list[re.Pattern]:
        """Compile patterns that indicate claims"""
        return [
            re.compile(r"\b(i|we|user|they)\s+(always|never|prefer|like|want|need|use|avoid)"),
            re.compile(r"\b(should|must|will|would|could)\s+\w+"),
            re.compile(r"\b(is|are|was|were)\s+\w+"),
            re.compile(r"\b(my|our|their)\s+\w+\s+(is|are)"),
        ]
