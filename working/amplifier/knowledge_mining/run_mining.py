#!/usr/bin/env python3
"""
Command-line interface for the Knowledge Mining System.
"""

import logging
import sys
import time
from pathlib import Path

from amplifier.config.paths import paths

from .knowledge_assistant import KnowledgeAssistant

# Set up logging with INFO level to see progress
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
)


def process_articles(directory: Path, limit: int | None = None, document_type: str = "general"):
    """Process articles from a directory.

    Args:
        directory: Directory containing articles
        limit: Maximum number of articles to process
        document_type: Type of documents ('article', 'api_docs', 'meeting', 'blog', 'general')
    """
    assistant = KnowledgeAssistant()

    # Find all markdown files
    articles = list(directory.glob("*.md"))
    if limit:
        articles = articles[:limit]

    print(f"Found {len(articles)} articles to process")
    print("-" * 60)

    for i, article_path in enumerate(articles, 1):
        print(f"\nProcessing {i}/{len(articles)}: {article_path.name}")
        print("  📖 Reading article...")

        start_time = time.time()
        try:
            content = article_path.read_text()
            title = article_path.stem.replace("-", " ").replace("_", " ").title()

            # Auto-detect document type if general
            article_type = document_type
            if document_type == "general":
                article_type = assistant._detect_document_type(article_path, content)

            print(f"  🔍 Extracting knowledge from {len(content)} characters (type: {article_type})...")
            sys.stdout.flush()  # Force output immediately

            # Convert to relative path for consistent storage
            try:
                relative_path = article_path.relative_to(Path.cwd())
                source_path = str(relative_path)
            except ValueError:
                # If not relative to cwd, use absolute path
                source_path = str(article_path)

            result = assistant.process_article(content, title, source=source_path, document_type=article_type)
            elapsed = time.time() - start_time

            if result.get("status") == "skipped":
                print(f"  ⏭️  Skipped (already processed) [{elapsed:.1f}s]")
            else:
                print(f"  ✓ Extracted {result['concepts_extracted']} concepts [{elapsed:.1f}s]")
                print(f"  ✓ Found {result['relationships_found']} relationships")
                print(f"  ✓ Generated {result['insights_captured']} insights")
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"  ❌ FAILED after {elapsed:.1f}s: {e}")
            logging.error(f"Failed to process {article_path.name}", exc_info=True)
            # Continue with next article instead of crashing
            continue

    # Find patterns across all articles
    print("\n" + "=" * 60)
    print("DISCOVERING PATTERNS")
    print("=" * 60)

    patterns = assistant.find_patterns()
    print(f"\nFound {len(patterns)} patterns across articles:")

    for pattern in patterns[:10]:  # Show top 10
        print(f"  • {pattern.pattern_type}: {pattern.description[:80]}...")

    # Export knowledge base
    stats = assistant.get_statistics()
    print("\n" + "=" * 60)
    print("KNOWLEDGE BASE STATISTICS")
    print("=" * 60)
    print(f"  Total concepts: {stats['concepts']}")
    print(f"  Total insights: {stats['insights']}")
    print(f"  Total patterns: {len(patterns)}")
    print(f"  Sources processed: {stats['sources']}")

    return assistant


def solve_problem(assistant: KnowledgeAssistant, problem: str):
    """Apply knowledge to solve a problem."""
    print("\n" + "=" * 60)
    print("PROBLEM SOLVING")
    print("=" * 60)
    print(f"Problem: {problem}")
    print("-" * 60)

    solution = assistant.solve_problem(problem)

    print("\nRelevant Concepts:")
    for concept in solution["concepts"][:5]:
        print(f"  • {concept}")

    print("\nApplicable Patterns:")
    for pattern in solution["patterns"][:5]:
        print(f"  • {pattern.pattern_type}: {pattern.description[:60]}...")

    print("\nRecommendations:")
    for rec in solution["recommendations"][:5]:
        print(f"  • {rec}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Knowledge Mining System")
    parser.add_argument(
        "--articles",
        type=Path,
        default=paths.content_dirs[0] if paths.content_dirs else Path("."),
        help="Directory containing articles to process",
    )
    parser.add_argument("--limit", type=int, help="Limit number of articles to process")
    parser.add_argument(
        "--type",
        type=str,
        default="general",
        choices=["article", "api_docs", "meeting", "blog", "general"],
        help="Type of documents to process",
    )
    parser.add_argument("--problem", type=str, help="Problem to solve using mined knowledge")
    parser.add_argument("--export", type=Path, help="Export knowledge base to JSON file")

    args = parser.parse_args()

    # Process articles
    assistant = process_articles(args.articles, args.limit, args.type)

    # Solve problem if specified
    if args.problem:
        solve_problem(assistant, args.problem)

    # Export if requested
    if args.export:
        assistant.export_knowledge(args.export)
        print(f"\n✓ Knowledge exported to {args.export}")


if __name__ == "__main__":
    main()
