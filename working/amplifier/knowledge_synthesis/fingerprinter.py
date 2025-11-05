"""
Semantic Fingerprinter - Creates 12-char hashes for concept resolution.
A self-contained brick that generates semantic fingerprints for entity resolution.
"""

import hashlib
import re


class SemanticFingerprinter:
    """Creates semantic fingerprints for concepts to enable entity resolution."""

    def __init__(self):
        """Initialize with common variations and stop words."""
        self.stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "up",
            "about",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "under",
            "again",
            "further",
            "then",
            "once",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
        }

    def fingerprint(self, text: str) -> str:
        """
        Generate a 12-character semantic fingerprint for text.

        Contract: text -> 12-char hash

        Args:
            text: Input text to fingerprint

        Returns:
            12-character hash representing the semantic fingerprint
        """
        # Normalize text
        normalized = self._normalize(text)

        # Create semantic features
        features = self._extract_features(normalized)

        # Generate hash from features
        feature_string = "|".join(sorted(features))
        hash_obj = hashlib.md5(feature_string.encode())

        # Return first 12 chars of hex digest
        return hash_obj.hexdigest()[:12]

    def similarity_score(self, fp1: str, fp2: str) -> float:
        """
        Calculate similarity between two fingerprints.

        Args:
            fp1: First fingerprint
            fp2: Second fingerprint

        Returns:
            Similarity score between 0 and 1
        """
        if fp1 == fp2:
            return 1.0

        # Count matching characters at same positions
        matches = sum(1 for i in range(min(len(fp1), len(fp2))) if fp1[i] == fp2[i])
        return matches / 12.0

    def find_collisions(self, fingerprints: list[tuple[str, str]]) -> list[list[str]]:
        """
        Find concept collisions (likely same entities).

        Args:
            fingerprints: List of (concept, fingerprint) tuples

        Returns:
            List of collision groups (concepts with same fingerprint)
        """
        collision_map = {}

        for concept, fp in fingerprints:
            if fp not in collision_map:
                collision_map[fp] = []
            collision_map[fp].append(concept)

        # Return only groups with collisions (2+ concepts)
        return [concepts for concepts in collision_map.values() if len(concepts) > 1]

    def _normalize(self, text: str) -> str:
        """Normalize text for fingerprinting."""
        # Lowercase and remove special chars
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s-]", "", text)

        # Handle common variations
        text = text.replace("-", " ")
        text = text.replace("_", " ")

        # Remove extra spaces
        text = " ".join(text.split())

        return text

    def _extract_features(self, text: str) -> list[str]:
        """Extract semantic features from normalized text."""
        features = []

        # Word-level features
        words = text.split()

        # Core words (non-stop words)
        core_words = [w for w in words if w not in self.stop_words]
        features.extend(core_words[:3])  # First 3 core words

        # Character trigrams from start and end
        if len(text) >= 3:
            features.append(text[:3])  # First trigram
            features.append(text[-3:])  # Last trigram

        # Word count feature
        features.append(f"wc_{len(words)}")

        # Length feature (bucketed)
        length_bucket = len(text) // 10
        features.append(f"len_{length_bucket}")

        # First letter of each word (acronym)
        if core_words:
            acronym = "".join(w[0] for w in core_words if w)[:4]
            if acronym:
                features.append(f"acr_{acronym}")

        return features
