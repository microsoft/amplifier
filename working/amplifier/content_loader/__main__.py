"""
Content Loader CLI Module

Simple command-line interface for content operations.
"""

import argparse
import json
import logging
import sys

from .loader import ContentLoader

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def cmd_scan(args: argparse.Namespace) -> int:
    """List all content files."""
    loader = ContentLoader(content_dirs=args.dirs)

    if not loader.content_dirs:
        logger.error("No content directories configured.")
        logger.info("Set AMPLIFIER_CONTENT_DIRS environment variable or use --dirs option")
        return 1

    logger.info(f"Scanning directories: {', '.join(str(d) for d in loader.content_dirs)}")
    logger.info("")

    count = 0
    for item in loader.load_all():
        print(f"[{item.content_id}] {item.title}")
        print(f"  Path: {item.source_path}")
        print(f"  Format: {item.format}")
        if item.metadata:
            print(f"  Metadata: {json.dumps(item.metadata, indent=2)}")
        print()
        count += 1

    logger.info(f"Total items found: {count}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Show content statistics."""
    loader = ContentLoader(content_dirs=args.dirs)

    if not loader.content_dirs:
        logger.error("No content directories configured.")
        logger.info("Set AMPLIFIER_CONTENT_DIRS environment variable or use --dirs option")
        return 1

    logger.info("Content Statistics")
    logger.info("=" * 40)
    logger.info(f"Configured directories: {len(loader.content_dirs)}")
    for d in loader.content_dirs:
        logger.info(f"  - {d}")

    logger.info("")

    # Collect statistics
    total_count = 0
    format_counts = {"md": 0, "txt": 0, "json": 0}
    total_size = 0

    for item in loader.load_all():
        total_count += 1
        format_counts[item.format] += 1
        total_size += len(item.content)

    logger.info(f"Total items: {total_count}")
    logger.info(f"Total content size: {total_size:,} bytes")
    logger.info("")
    logger.info("By format:")
    for fmt, count in format_counts.items():
        if count > 0:
            logger.info(f"  {fmt:5} : {count:4} items")

    return 0


def cmd_search(args: argparse.Namespace) -> int:
    """Search content for a query string."""
    loader = ContentLoader(content_dirs=args.dirs)

    if not loader.content_dirs:
        logger.error("No content directories configured.")
        logger.info("Set AMPLIFIER_CONTENT_DIRS environment variable or use --dirs option")
        return 1

    logger.info(f"Searching for: '{args.query}'")
    if args.case_sensitive:
        logger.info("(case-sensitive search)")
    logger.info("")

    count = 0
    for item in loader.search(args.query, case_sensitive=args.case_sensitive):
        print(f"[{item.content_id}] {item.title}")
        print(f"  Path: {item.source_path}")

        # Show snippet of matching content
        content_lower = item.content.lower() if not args.case_sensitive else item.content
        query_lower = args.query.lower() if not args.case_sensitive else args.query

        idx = content_lower.find(query_lower)
        if idx >= 0:
            # Show 50 chars before and after match
            start = max(0, idx - 50)
            end = min(len(item.content), idx + len(args.query) + 50)
            snippet = item.content[start:end]
            if start > 0:
                snippet = "..." + snippet
            if end < len(item.content):
                snippet = snippet + "..."
            # Highlight the match
            snippet = snippet.replace(args.query, f"**{args.query}**")
            print(f"  Match: {snippet}")
        print()
        count += 1

    logger.info(f"Found {count} matching items")
    return 0


def main() -> int:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(description="Content Loader CLI - Manage and search content files")
    parser.add_argument(
        "--dirs",
        nargs="+",
        help="Content directories to scan (overrides AMPLIFIER_CONTENT_DIRS)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Scan command
    subparsers.add_parser("scan", help="List all content files")

    # Status command
    subparsers.add_parser("status", help="Show content statistics")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search content")
    search_parser.add_argument("query", help="Search query string")
    search_parser.add_argument("-c", "--case-sensitive", action="store_true", help="Perform case-sensitive search")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Dispatch to command handler
    if args.command == "scan":
        return cmd_scan(args)
    if args.command == "status":
        return cmd_status(args)
    if args.command == "search":
        return cmd_search(args)
    logger.error(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
