"""
Synthesis Engine - Orchestrates the knowledge synthesis pipeline.
Connects all bricks to enable cross-article intelligence.
"""

import json
from pathlib import Path
from typing import Any

from amplifier.config.paths import paths

from .fingerprinter import SemanticFingerprinter
from .stream_reader import StreamReader
from .synthesizer import Synthesizer
from .tension_detector import TensionDetector


class SynthesisEngine:
    """Orchestrates knowledge synthesis across articles."""

    def __init__(self, extractions_path: Path | None = None):
        """
        Initialize synthesis engine with all components.

        Args:
            extractions_path: Path to extractions JSONL file
        """
        self.fingerprinter = SemanticFingerprinter()
        self.stream_reader = StreamReader(path=extractions_path)
        self.tension_detector = TensionDetector()
        self.synthesizer = Synthesizer()

        # Store synthesis results
        self.synthesis_path = paths.data_dir / "knowledge" / "synthesis.json"
        self.synthesis_path.parent.mkdir(parents=True, exist_ok=True)

    def run_synthesis(self) -> dict[str, Any]:
        """
        Run complete synthesis pipeline.

        Returns:
            Dictionary containing all synthesis results
        """
        print("Starting knowledge synthesis...")

        # Process stream and collect fingerprints
        all_concepts = []
        article_count = 0

        for article in self.stream_reader.stream_articles():
            article_count += 1

            # Collect concepts for fingerprinting
            for concept in article.get("concepts", []):
                name = concept.get("name", "")
                if name:
                    fp = self.fingerprinter.fingerprint(name)
                    all_concepts.append((name, fp))

        print(f"Processed {article_count} articles")

        # Find entity collisions (same concepts, different names)
        collisions = self.fingerprinter.find_collisions(all_concepts)

        # Get window context for synthesis
        window_context = self.stream_reader.get_window_context()

        # Find tensions in the window
        tensions = self.tension_detector.find_tensions(list(self.stream_reader.window))

        # Generate synthesis insights
        insights = self.synthesizer.synthesize(window_context)

        # Find emerging concepts
        emerging = self.stream_reader.find_emerging_concepts()

        # Compile results
        results = {
            "statistics": {
                "total_articles": article_count,
                "unique_concepts": len({c for c, _ in all_concepts}),
                "entity_collisions": len(collisions),
                "tensions_found": len(tensions),
                "insights_generated": len(insights),
                "emerging_concepts": len(emerging),
            },
            "entity_resolution": {
                "collision_groups": collisions[:10],  # Top 10 collision groups
                "total_collisions": len(collisions),
            },
            "tensions": tensions[:10],  # Top 10 tensions
            "insights": insights,  # Already limited to top 10
            "emerging_concepts": emerging,
            "window_context": {
                "size": window_context["window_size"],
                "top_concepts": dict(list(window_context["concepts"].items())[:10]),
                "top_relationships": [
                    {"subject": subj, "predicate": pred, "object": obj, "count": count}
                    for (subj, pred, obj), count in list(window_context["relationships"].items())[:5]
                ],
                "top_cooccurrences": [
                    {"concept1": c1, "concept2": c2, "count": count}
                    for (c1, c2), count in list(window_context["cooccurrences"].items())[:5]
                ],
            },
        }

        # Save results
        self._save_results(results)

        return results

    def _save_results(self, results: dict[str, Any]) -> None:
        """Save synthesis results to JSON file."""
        with open(self.synthesis_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Synthesis results saved to {self.synthesis_path}")

    def print_summary(self, results: dict[str, Any]) -> None:
        """Print a human-readable summary of synthesis results."""
        stats = results["statistics"]

        print("\n" + "=" * 60)
        print("KNOWLEDGE SYNTHESIS SUMMARY")
        print("=" * 60)

        print(f"\nProcessed: {stats['total_articles']} articles")
        print(f"Found: {stats['unique_concepts']} unique concepts")
        print(f"Entity collisions: {stats['entity_collisions']} groups")
        print(f"Tensions detected: {stats['tensions_found']}")
        print(f"Insights generated: {stats['insights_generated']}")
        print(f"Emerging concepts: {stats['emerging_concepts']}")

        # Show top insights
        if results["insights"]:
            print("\n" + "-" * 40)
            print("TOP INSIGHTS:")
            print("-" * 40)
            for i, insight in enumerate(results["insights"][:3], 1):
                print(f"\n{i}. [{insight['type'].upper()}] {insight['insight']}")
                print(f"   Evidence: {insight['evidence']}")
                print(f"   Action: {insight['actionable']}")

        # Show tensions
        if results["tensions"]:
            print("\n" + "-" * 40)
            print("KEY TENSIONS:")
            print("-" * 40)
            for i, tension in enumerate(results["tensions"][:3], 1):
                print(f"\n{i}. {tension['type'].replace('_', ' ').title()}")
                if tension["type"] == "relationship_contradiction":
                    print(
                        f"   {tension['subject']} {tension['assertion']} vs {tension['contradiction']} {tension['object']}"
                    )
                elif tension["type"] == "insight_contradiction":
                    print(f"   Insight 1: {tension['insight1'][:60]}...")
                    print(f"   Insight 2: {tension['insight2'][:60]}...")
                print(f"   Sources: {', '.join(tension['sources'][:2])}")

        # Show emerging concepts
        if results["emerging_concepts"]:
            print("\n" + "-" * 40)
            print("EMERGING CONCEPTS:")
            print("-" * 40)
            print(f"  {', '.join(results['emerging_concepts'][:5])}")

        # Show entity resolutions
        if results["entity_resolution"]["collision_groups"]:
            print("\n" + "-" * 40)
            print("ENTITY RESOLUTIONS (same concept, different names):")
            print("-" * 40)
            for group in results["entity_resolution"]["collision_groups"][:3]:
                print(f"  • {' = '.join(group)}")

        print("\n" + "=" * 60)
