#!/usr/bin/env python3
"""
Usage examples for the path configuration module.

These examples demonstrate how to use the path configuration
in various scenarios.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def example_basic_usage():
    """Basic usage of the path configuration."""
    from amplifier.config import paths

    print("Basic Path Usage:")
    print("-" * 40)

    # Access pre-configured paths
    print(f"Data directory: {paths.data_dir}")
    print(f"Content directories: {paths.content_dirs}")

    # Create file paths
    knowledge_file = paths.data_dir / "knowledge" / "graph.json"
    print(f"\nKnowledge file would be at: {knowledge_file}")

    # Work with content directories
    print("\nScanning content directories:")
    for content_dir in paths.get_all_content_paths():
        print(f"  - {content_dir}")


def example_save_data():
    """Example of saving data using configured paths."""
    import json

    from amplifier.config import paths

    print("\nSaving Data Example:")
    print("-" * 40)

    # Ensure directories exist
    paths.ensure_data_dirs()

    # Save to knowledge directory
    knowledge_path = paths.data_dir / "knowledge" / "example.json"
    data = {"type": "example", "content": "This is test data"}

    with open(knowledge_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved data to: {knowledge_path}")

    # Save to cache
    cache_path = paths.data_dir / "cache" / "temp.txt"
    cache_path.write_text("Temporary cache data")
    print(f"Saved cache to: {cache_path}")


def example_scan_content():
    """Example of scanning content directories."""
    from amplifier.config import paths

    print("\nContent Scanning Example:")
    print("-" * 40)

    # Get all content directories that exist
    content_dirs = paths.get_all_content_paths()

    if not content_dirs:
        print("No content directories found")
        return

    # Scan for markdown files
    for content_dir in content_dirs:
        md_files = list(content_dir.glob("**/*.md"))[:5]  # Limit to 5 for example

        if md_files:
            print(f"\nMarkdown files in {content_dir}:")
            for md_file in md_files:
                relative = md_file.relative_to(content_dir)
                print(f"  - {relative}")


def example_resolve_paths():
    """Example of resolving different path types."""
    from amplifier.config import paths

    print("\nPath Resolution Example:")
    print("-" * 40)

    # Examples of different path types
    test_paths = {
        "relative/path": "Relative path from repo root",
        "~/documents": "Home directory path",
        "/tmp/absolute": "Absolute path",
        ".": "Current directory",
        "..": "Parent directory",
    }

    for path_str, description in test_paths.items():
        resolved = paths.resolve_path(path_str)
        print(f"\n{description}:")
        print(f"  Input:    {path_str}")
        print(f"  Resolved: {resolved}")


def example_custom_environment():
    """Example of using custom environment variables."""
    import os

    from amplifier.config import PathConfig

    print("\nCustom Environment Example:")
    print("-" * 40)

    # Save original environment
    original_data_dir = os.environ.get("AMPLIFIER_DATA_DIR")

    try:
        # Set custom data directory
        os.environ["AMPLIFIER_DATA_DIR"] = "/tmp/custom-amplifier-data"

        # Create new config with custom environment
        custom_paths = PathConfig()

        print(f"Custom data directory: {custom_paths.data_dir}")

        # Create structure in custom location
        custom_paths.ensure_data_dirs()

        # List created directories
        print("\nCreated directories:")
        for subdir in ["knowledge", "indexes", "state", "memories", "cache"]:
            dir_path = custom_paths.data_dir / subdir
            if dir_path.exists():
                print(f"  ✓ {dir_path}")

    finally:
        # Restore original environment
        if original_data_dir is None:
            os.environ.pop("AMPLIFIER_DATA_DIR", None)
        else:
            os.environ["AMPLIFIER_DATA_DIR"] = original_data_dir


def main():
    """Run all examples."""
    examples = [
        example_basic_usage,
        example_save_data,
        example_scan_content,
        example_resolve_paths,
        example_custom_environment,
    ]

    for example in examples:
        example()
        print()


if __name__ == "__main__":
    main()
