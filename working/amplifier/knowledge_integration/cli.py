#!/usr/bin/env python
"""
Command-line interface for Knowledge Integration system.

Simple, direct CLI following ruthless simplicity principle.
Only works with real input files - no demo data.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports when run as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def extract_file(file_path: str) -> None:
    """
    Extract knowledge from a single file.

    Args:
        file_path: Path to the file to extract from
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"Error: File not found: {file_path}")
        sys.exit(1)

    try:
        import asyncio

        from knowledge_store import UnifiedKnowledgeStore
        from unified_extractor import UnifiedKnowledgeExtractor

        # Read file content
        text = path.read_text(encoding="utf-8")

        # Extract knowledge
        extractor = UnifiedKnowledgeExtractor()
        extraction = asyncio.run(extractor.extract_from_text(text=text, title=path.stem, source=str(path)))

        # Check if extraction has any content
        has_content = (
            extraction.concepts or extraction.relationships or extraction.key_insights or extraction.code_patterns
        )

        if not has_content:
            logger.warning(f"No content extracted from {path.name} - not saving")
            return

        # Store results
        store = UnifiedKnowledgeStore()
        summary = store.add_extraction(extraction)  # Note: add_extraction() saves automatically

        logger.info(f"✓ Extracted from {path.name}")
        logger.info(f"  Added {summary['nodes_added']} nodes")
        logger.info(f"  Added {summary['relationships_added']} relationships")
        logger.info(f"  Total nodes: {summary.get('total_nodes', 0)}")

    except Exception as e:
        logger.error(f"Error extracting from {file_path}: {e}")
        sys.exit(1)


def extract_directory(dir_path: str, pattern: str = "*.md") -> None:
    """
    Extract knowledge from all files in a directory.

    Args:
        dir_path: Path to the directory
        pattern: File pattern to match (default: *.md)
    """
    directory = Path(dir_path)
    if not directory.exists():
        logger.error(f"Error: Directory not found: {dir_path}")
        sys.exit(1)

    if not directory.is_dir():
        logger.error(f"Error: Not a directory: {dir_path}")
        sys.exit(1)

    # Find all matching files
    files = list(directory.glob(pattern))
    if not files:
        logger.warning(f"No files matching '{pattern}' found in {dir_path}")
        return

    logger.info(f"Processing {len(files)} files from {directory.name}/")

    # Initialize once
    import asyncio

    from knowledge_store import UnifiedKnowledgeStore
    from unified_extractor import UnifiedKnowledgeExtractor

    extractor = UnifiedKnowledgeExtractor()
    store = UnifiedKnowledgeStore()

    total_nodes = 0
    total_relationships = 0
    files_processed = 0

    try:
        # Process each file
        for i, file_path in enumerate(files, 1):
            logger.info(f"[{i}/{len(files)}] Processing {file_path.name}...")

            # Check if already processed
            if store.is_source_processed(str(file_path)):
                logger.info("  → Already processed, skipping")
                files_processed += 1
                continue

            try:
                text = file_path.read_text(encoding="utf-8")
                extraction = asyncio.run(
                    extractor.extract_from_text(text=text, title=file_path.stem, source=str(file_path))
                )

                # Check if extraction has any content
                has_content = (
                    extraction.concepts
                    or extraction.relationships
                    or extraction.key_insights
                    or extraction.code_patterns
                )

                if not has_content:
                    logger.warning("  → No content extracted, skipping save")
                    continue

                summary = store.add_extraction(extraction)
                total_nodes += summary["nodes_added"]
                total_relationships += summary["relationships_added"]
                files_processed += 1

                logger.info(f"  → Added {summary['nodes_added']} nodes, {summary['relationships_added']} relationships")

            except RuntimeError as e:
                error_msg = str(e).lower()
                # Handle known SDK issues directly
                if "timed out" in error_msg:
                    logger.error(f"\n⚠ {e}")
                    logger.info(f"Successfully processed {files_processed} files before timeout")
                    logger.info(
                        "Please ensure Claude CLI is installed globally: npm install -g @anthropic-ai/claude-code"
                    )
                    break
                # Empty response from interrupted SDK
                if "interrupted" in error_msg or "no response" in error_msg:
                    logger.info("\n⚠ Extraction interrupted")
                    break
                # Unknown runtime error - log and continue
                logger.error(f"  → Error processing file: {e}")
                continue

    except KeyboardInterrupt:
        # Simple, direct interrupt handling
        logger.info("\n⚠ Interrupted - saving progress...")

    # Always show final summary
    logger.info(f"\n✓ Processed {files_processed}/{len(files)} files")
    logger.info(f"  Total nodes added: {total_nodes}")
    logger.info(f"  Total relationships added: {total_relationships}")

    # Save happens automatically via add_extraction()
    if files_processed > 0:
        logger.info("  Data saved successfully")


def show_stats() -> None:
    """Show statistics about the knowledge graph."""
    try:
        from knowledge_store import UnifiedKnowledgeStore

        store = UnifiedKnowledgeStore()
        stats = store.get_statistics()

        logger.info("\nKnowledge Graph Statistics")
        logger.info("=" * 40)
        logger.info(f"Total nodes: {stats['total_nodes']}")
        logger.info(f"Total relationships: {stats['total_relationships']}")
        logger.info(f"Processed sources: {stats['total_sources']}")

        if stats.get("node_types"):
            logger.info("\nNode types:")
            for node_type, count in stats["node_types"].items():
                logger.info(f"  {node_type}: {count}")

        if stats.get("relationship_types"):
            logger.info("\nRelationship types:")
            for rel_type, count in stats["relationship_types"].items():
                logger.info(f"  {rel_type}: {count}")

    except FileNotFoundError:
        logger.error("No knowledge graph found. Run extraction first.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error showing statistics: {e}")
        sys.exit(1)


def run_inference(query: str | None = None) -> None:
    """
    Run inference engine on the knowledge graph.

    Args:
        query: Optional query to analyze
    """
    # Inference engine not yet implemented
    logger.error("Inference engine not yet implemented")
    return


def visualize(output_dir: str | None = None, viz_type: str = "full") -> None:
    """
    Generate interactive visualization of the knowledge graph.

    Args:
        output_dir: Directory to save visualizations
        viz_type: Type of visualization (full, concept, filtered, subgraph)
    """
    # Visualizer not yet fully implemented
    logger.error("Visualizer not yet fully implemented")
    return


def resolve_entities() -> None:
    """Run entity resolution to canonicalize the knowledge graph."""
    # Entity resolution not yet implemented
    logger.error("Entity resolution not yet implemented")
    return


def export_graph(output_file: str) -> None:
    """
    Export the knowledge graph to JSON.

    Args:
        output_file: Path to output JSON file
    """
    try:
        from knowledge_store import UnifiedKnowledgeStore

        store = UnifiedKnowledgeStore()

        # Export to dict - use dataclass fields directly
        export_data = {
            "nodes": [
                {
                    "id": node.id,
                    "name": node.name,
                    "type": node.type,
                    "definition": node.definition,
                    "sources": node.sources,
                    "metadata": node.metadata,
                }
                for node in store.nodes.values()
            ],
            "relationships": [
                {
                    "subject": rel.subject,
                    "predicate": rel.predicate,
                    "object": rel.object,
                    "confidence": rel.confidence,
                    "source": rel.source,
                }
                for rel in store.relationships
            ],
            "statistics": store.get_statistics(),
            "export_timestamp": str(Path(output_file).stat().st_mtime if Path(output_file).exists() else "new"),
        }

        # Write to file
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(export_data, indent=2))

        logger.info(f"\n✓ Exported knowledge graph to {output_file}")
        logger.info(f"  {len(export_data['nodes'])} nodes")
        logger.info(f"  {len(export_data['relationships'])} relationships")

    except FileNotFoundError:
        logger.error("No knowledge graph found. Run extraction first.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error exporting graph: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Knowledge Integration CLI - Extract, analyze, and visualize knowledge graphs"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Extract single file
    extract_parser = subparsers.add_parser("extract", help="Extract knowledge from a file")
    extract_parser.add_argument("file", help="Path to file to extract from")

    # Extract directory
    extract_dir_parser = subparsers.add_parser("extract-dir", help="Extract from all files in directory")
    extract_dir_parser.add_argument("directory", help="Path to directory")
    extract_dir_parser.add_argument("--pattern", default="*.md", help="File pattern (default: *.md)")

    # Show statistics
    subparsers.add_parser("stats", help="Show knowledge graph statistics")

    # Run inference
    infer_parser = subparsers.add_parser("infer", help="Run inference engine")
    infer_parser.add_argument("--query", help="Optional query to analyze")

    # Visualize
    viz_parser = subparsers.add_parser("visualize", help="Create interactive visualization")
    viz_parser.add_argument("--output-dir", help="Output directory for visualizations")
    viz_parser.add_argument(
        "--type",
        choices=["full", "concept", "filtered", "subgraph", "suite"],
        default="full",
        help="Visualization type",
    )

    # Resolve entities
    subparsers.add_parser("resolve", help="Run entity resolution")

    # Export
    export_parser = subparsers.add_parser("export", help="Export knowledge graph to JSON")
    export_parser.add_argument("output", help="Output JSON file path")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    if args.command == "extract":
        extract_file(args.file)
    elif args.command == "extract-dir":
        extract_directory(args.directory, args.pattern)
    elif args.command == "stats":
        show_stats()
    elif args.command == "infer":
        run_inference(args.query)
    elif args.command == "visualize":
        visualize(args.output_dir, args.type)
    elif args.command == "resolve":
        resolve_entities()
    elif args.command == "export":
        export_graph(args.output)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
