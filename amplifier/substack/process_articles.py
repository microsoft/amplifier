#!/usr/bin/env python3
"""
Process Substack articles through Amplifier's knowledge mining system
"""

import json
import logging
import sys
import time
from pathlib import Path

# Add the amplifier module to path
sys.path.insert(0, str(Path(__file__).parent))

from amplifier.knowledge_mining.knowledge_assistant import KnowledgeAssistant

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


def process_articles():
    """Process all Substack articles"""
    articles_dir = Path("data/articles/raw")

    if not articles_dir.exists():
        logger.error(f"Directory {articles_dir} does not exist")
        return None

    # Initialize the knowledge assistant
    assistant = KnowledgeAssistant()
    # store = KnowledgeStore()  # Not used currently

    # Find all markdown files
    articles = list(articles_dir.glob("*.md"))
    logger.info(f"Found {len(articles)} articles to process")

    if not articles:
        logger.warning("No articles found")
        return None

    print("=" * 60)
    print("PROCESSING SUBSTACK ARTICLES")
    print("=" * 60)

    all_concepts = []
    all_insights = []
    all_relationships = []

    for i, article_path in enumerate(articles, 1):
        print(f"\n[{i}/{len(articles)}] Processing: {article_path.name}")

        try:
            # Read the article
            content = article_path.read_text()
            title = article_path.stem.replace("michaeljjabbour_", "").replace("-", " ").replace("_", " ")

            print(f"  📖 Title: {title}")
            print(f"  📝 Size: {len(content):,} characters")

            # Process with knowledge assistant (this does the actual extraction)
            start = time.time()
            result = assistant.process_article(
                content,
                title=title,
                source=article_path.name,
                document_type="blog",  # Specify as blog post
            )
            elapsed = time.time() - start

            if result:
                print(f"  ✅ Extracted in {elapsed:.1f}s:")
                print(f"     - {len(result.get('concepts', []))} concepts")
                print(f"     - {len(result.get('insights', []))} insights")
                print(f"     - {len(result.get('relationships', []))} relationships")

                # Collect results
                all_concepts.extend(result.get("concepts", []))
                all_insights.extend(result.get("insights", []))
                all_relationships.extend(result.get("relationships", []))
            else:
                print("  ❌ Extraction failed")

        except Exception as e:
            print(f"  ❌ Error: {e}")
            logger.error(f"Failed to process {article_path.name}: {e}")
            continue

    # Save the complete knowledge graph
    print("\n" + "=" * 60)
    print("BUILDING KNOWLEDGE GRAPH")
    print("=" * 60)

    knowledge_graph = {
        "articles": [a.name for a in articles],
        "concepts": all_concepts,
        "insights": all_insights,
        "relationships": all_relationships,
        "statistics": {
            "total_articles": len(articles),
            "total_concepts": len(all_concepts),
            "unique_concepts": len({c["name"] for c in all_concepts if "name" in c}),
            "total_insights": len(all_insights),
            "total_relationships": len(all_relationships),
        },
    }

    # Save to file
    output_path = Path("data/substack_knowledge_graph.json")
    output_path.write_text(json.dumps(knowledge_graph, indent=2))

    print(f"\n✅ Knowledge graph saved to: {output_path}")
    print(f"   - {knowledge_graph['statistics']['total_concepts']} concepts")
    print(f"   - {knowledge_graph['statistics']['unique_concepts']} unique concepts")
    print(f"   - {knowledge_graph['statistics']['total_insights']} insights")
    print(f"   - {knowledge_graph['statistics']['total_relationships']} relationships")

    # Note: Pattern discovery would go here if store had discover_patterns method
    # patterns = store.discover_patterns()  # Method doesn't exist yet
    # if patterns:
    #     print(f"\n🔍 Discovered {len(patterns)} patterns:")
    #     for pattern in patterns[:5]:  # Show first 5
    #         print(f"   - {pattern['type']}: {pattern['name']}")

    return knowledge_graph


if __name__ == "__main__":
    try:
        knowledge_graph = process_articles()
        print("\n✨ Knowledge extraction complete!")
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logger.exception("Fatal error during processing")
        sys.exit(1)
