#!/usr/bin/env python3

import json
import re
from collections import defaultdict
from pathlib import Path


class ConceptExtractor:
    """Extract concepts and relationships from articles"""

    def __init__(self):
        self.concepts = {}  # concept_id -> concept details
        self.relationships = []  # list of relationships
        self.articles = {}  # article_id -> article metadata
        self.concept_articles = defaultdict(list)  # concept_id -> [article_ids]
        self.themes = defaultdict(set)  # theme -> set of concept_ids

    def extract_from_article(self, filepath: Path) -> dict:
        """Extract concepts from a single article"""

        content = filepath.read_text(encoding="utf-8")
        article_id = filepath.stem

        # Extract metadata
        metadata = self._extract_metadata(content, article_id)
        self.articles[article_id] = metadata

        # Extract key concepts
        concepts = self._extract_concepts(content, article_id)

        # Extract relationships
        relationships = self._extract_relationships(content, concepts)

        return {"article_id": article_id, "metadata": metadata, "concepts": concepts, "relationships": relationships}

    def _extract_metadata(self, content: str, article_id: str) -> dict:
        """Extract article metadata"""
        lines = content.split("\n")
        metadata = {
            "id": article_id,
            "title": "",
            "author": "michaeljjabbour",
            "date": "",
            "source": "",
            "word_count": len(content.split()),
        }

        # Parse front matter
        if lines[0] == "---":
            for _i, line in enumerate(lines[1:], 1):
                if line == "---":
                    break
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip().lower()
                    value = value.strip()
                    if key in metadata:
                        metadata[key] = value
                    elif key == "publication":
                        metadata["author"] = value

        # Clean title
        if metadata["title"]:
            metadata["title"] = metadata["title"].replace("-", " ")
        elif "# " in content[:200]:
            for line in lines[:10]:
                if line.startswith("# "):
                    metadata["title"] = line[2:].strip()
                    break

        return metadata

    def _extract_concepts(self, content: str, article_id: str) -> list[dict]:
        """Extract key concepts from article text"""
        concepts = []

        # Core AI/Technology concepts
        ai_patterns = [
            (
                r"\b(AI|artificial intelligence|machine learning|LLM|large language model)s?\b",
                "AI & Machine Learning",
                "technology",
            ),
            (r"\b(algorithm|computation|processing|automation)s?\b", "Computational Systems", "technology"),
            (r"\b(neural|network|brain|cognition|metacognition)s?\b", "Neural & Cognitive", "cognition"),
            (r"\b(agency|autonomy|control|authorship)s?\b", "Agency & Control", "philosophy"),
            (r"\b(consciousness|awareness|sentience|experience)s?\b", "Consciousness", "philosophy"),
            (r"\b(pattern|recognition|matching|emergence)s?\b", "Pattern & Emergence", "systems"),
            (r"\b(warp|woof|weaving|tapestry|loom|thread)s?\b", "Weaving Metaphor", "metaphor"),
            (r"\b(human|machine|boundary|interface|symbiosis)s?\b", "Human-Machine Interface", "interaction"),
            (r"\b(trust|transparency|explainability|reasoning)s?\b", "Trust & Transparency", "ethics"),
            (r"\b(evolution|adaptation|fitness|survival)s?\b", "Evolution & Adaptation", "biology"),
            (r"\b(perception|reality|truth|illusion)s?\b", "Perception & Reality", "philosophy"),
            (r"\b(memory|forgetting|retention|recall)s?\b", "Memory Systems", "cognition"),
            (r"\b(creativity|generation|synthesis|creation)s?\b", "Creativity & Generation", "creation"),
            (r"\b(meaning|purpose|value|significance)s?\b", "Meaning & Purpose", "philosophy"),
            (r"\b(time|rhythm|tempo|synchronization|acceleration)s?\b", "Time & Rhythm", "temporal"),
            (r"\b(complexity|simplicity|emergence|chaos)s?\b", "Complexity Theory", "systems"),
            (r"\b(learning|growth|development|education)s?\b", "Learning & Development", "education"),
            (r"\b(emotion|feeling|affect|experience)s?\b", "Emotion & Experience", "psychology"),
            (r"\b(work|productivity|efficiency|output)s?\b", "Work & Productivity", "productivity"),
            (r"\b(tool|augmentation|extension|replacement)s?\b", "Tools & Augmentation", "technology"),
        ]

        # Process each pattern
        for pattern, concept_name, theme in ai_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                concept_id = self._get_concept_id(concept_name)

                # Create or update concept
                if concept_id not in self.concepts:
                    self.concepts[concept_id] = {
                        "id": concept_id,
                        "name": concept_name,
                        "theme": theme,
                        "count": 0,
                        "articles": [],
                        "examples": [],
                        "importance": 0,
                    }

                # Update concept data
                self.concepts[concept_id]["count"] += len(matches)
                if article_id not in self.concepts[concept_id]["articles"]:
                    self.concepts[concept_id]["articles"].append(article_id)

                # Extract example quotes
                for match in matches[:3]:  # Keep top 3 examples
                    quote = self._extract_context(content, match)
                    if quote and quote not in self.concepts[concept_id]["examples"]:
                        self.concepts[concept_id]["examples"].append(quote)

                # Add to theme
                self.themes[theme].add(concept_id)

                concepts.append({"id": concept_id, "name": concept_name, "theme": theme, "frequency": len(matches)})

        return concepts

    def _extract_relationships(self, content: str, concepts: list[dict]) -> list[dict]:
        """Extract relationships between concepts"""
        relationships = []
        # concept_ids = [c["id"] for c in concepts]  # Not needed currently

        # Look for concepts that appear near each other
        sentences = re.split(r"[.!?]+", content)

        for sentence in sentences:
            mentioned_concepts = []
            for concept in concepts:
                if self._concept_in_text(concept["name"], sentence):
                    mentioned_concepts.append(concept["id"])

            # Create relationships for concepts in same sentence
            for i, concept1 in enumerate(mentioned_concepts):
                for concept2 in mentioned_concepts[i + 1 :]:
                    # rel_id = f"{concept1}_{concept2}"  # Not used
                    relationships.append(
                        {
                            "source": concept1,
                            "target": concept2,
                            "type": "co-occurrence",
                            "strength": 1,
                            "context": sentence[:200],
                        }
                    )

        return relationships

    def _concept_in_text(self, concept_name: str, text: str) -> bool:
        """Check if concept appears in text"""
        # Simple keyword matching, could be enhanced
        keywords = concept_name.lower().split(" & ")
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in keywords)

    def _extract_context(self, content: str, term: str, window: int = 100) -> str:
        """Extract context around a term"""
        try:
            idx = content.lower().find(term.lower())
            if idx == -1:
                return ""
            start = max(0, idx - window)
            end = min(len(content), idx + len(term) + window)
            context = content[start:end].strip()
            # Clean up the context
            if start > 0:
                context = "..." + context
            if end < len(content):
                context = context + "..."
            return context.replace("\n", " ").replace("  ", " ")
        except Exception:
            return ""

    def _get_concept_id(self, name: str) -> str:
        """Generate consistent ID for concept"""
        return name.lower().replace(" & ", "_").replace(" ", "_").replace("-", "_")

    def process_all_articles(self, directory: Path) -> dict:
        """Process all articles and build knowledge graph"""

        article_files = sorted(directory.glob("*.md"))

        for filepath in article_files:
            print(f"Processing: {filepath.name}")
            self.extract_from_article(filepath)

        # Calculate importance scores
        self._calculate_importance()

        # Build final graph structure
        return self.build_knowledge_graph()

    def _calculate_importance(self):
        """Calculate importance scores for concepts"""
        for _concept_id, concept in self.concepts.items():
            # Importance based on frequency and article spread
            concept["importance"] = (
                concept["count"] * 0.3  # Raw frequency
                + len(concept["articles"]) * 10  # Article spread weighted more
            )

    def build_knowledge_graph(self) -> dict:
        """Build the final knowledge graph structure"""

        # Aggregate relationships
        relationship_map = defaultdict(lambda: {"count": 0, "contexts": []})

        for rel in self.relationships:
            key = f"{rel['source']}_{rel['target']}"
            relationship_map[key]["count"] += rel["strength"]
            if rel.get("context"):
                contexts = relationship_map[key]["contexts"]
                if isinstance(contexts, list):
                    contexts.append(rel["context"])

        # Build final relationships
        final_relationships = []
        for key, data in relationship_map.items():
            source, target = key.split("_", 1)
            if source in self.concepts and target in self.concepts:
                final_relationships.append(
                    {
                        "source": source,
                        "target": target,
                        "strength": min(10, data["count"]),  # Cap strength at 10
                        "type": "related",
                    }
                )

        return {
            "concepts": list(self.concepts.values()),
            "relationships": final_relationships,
            "articles": list(self.articles.values()),
            "themes": {theme: list(concepts) for theme, concepts in self.themes.items()},
            "stats": {
                "total_concepts": len(self.concepts),
                "total_relationships": len(final_relationships),
                "total_articles": len(self.articles),
                "themes": list(self.themes.keys()),
            },
        }


def main():
    """Main extraction process"""

    # Initialize extractor
    extractor = ConceptExtractor()

    # Process all articles
    articles_dir = Path("data/articles/raw")
    knowledge_graph = extractor.process_all_articles(articles_dir)

    # Save knowledge graph
    output_file = Path("data/knowledge_graph.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(knowledge_graph, f, indent=2, ensure_ascii=False)

    print(f"\nKnowledge graph saved to {output_file}")
    print(f"Total concepts: {knowledge_graph['stats']['total_concepts']}")
    print(f"Total relationships: {knowledge_graph['stats']['total_relationships']}")
    print(f"Total articles: {knowledge_graph['stats']['total_articles']}")
    print(f"Themes: {', '.join(knowledge_graph['stats']['themes'])}")

    # Show top concepts
    top_concepts = sorted(knowledge_graph["concepts"], key=lambda x: x["importance"], reverse=True)[:10]

    print("\nTop 10 Concepts by Importance:")
    for concept in top_concepts:
        print(f"  - {concept['name']}: {concept['importance']:.1f} (in {len(concept['articles'])} articles)")


if __name__ == "__main__":
    main()
