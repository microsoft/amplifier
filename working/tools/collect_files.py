#!/usr/bin/env python3
"""
Collect Files Utility

Recursively scans the specified file/directory patterns and outputs a single Markdown
document containing each file's relative path and its content.

This tool helps aggregate source code files for analysis or documentation purposes.

Usage examples:
  # Collect all Python files in the current directory:
  python collect_files.py *.py > my_python_files.md

  # Collect all files in the 'output' directory:
  python collect_files.py output > my_output_dir_files.md

  # Collect specific files, excluding 'utils' and 'logs', but including Markdown files from 'utils':
  python collect_files.py *.py --exclude "utils,logs,__pycache__,*.pyc" --include "utils/*.md" > my_output.md
"""

import argparse
import datetime
import fnmatch
import glob
import os
import pathlib

# Default exclude patterns: common directories and binary files to ignore.
DEFAULT_EXCLUDE = [".venv", "node_modules", "*.lock", ".git", "__pycache__", "*.pyc", "*.ruff_cache", "logs", "output"]


def parse_patterns(pattern_str: str) -> list[str]:
    """Splits a comma-separated string into a list of stripped patterns."""
    return [p.strip() for p in pattern_str.split(",") if p.strip()]


def resolve_pattern(pattern: str) -> str:
    """
    Resolves a pattern that might contain relative path navigation.
    Returns the absolute path of the pattern.
    """
    # Convert the pattern to a Path object
    pattern_path = pathlib.Path(pattern)

    # Check if the pattern is absolute or contains relative navigation
    if os.path.isabs(pattern) or ".." in pattern:
        # Resolve to absolute path
        return str(pattern_path.resolve())

    # For simple patterns without navigation, return as is
    return pattern


def match_pattern(path: str, pattern: str, component_matching=False) -> bool:
    """
    Centralized pattern matching logic.

    Args:
        path: File path to match against
        pattern: Pattern to match
        component_matching: If True, matches individual path components
                           (used primarily for exclude patterns)

    Returns:
        True if path matches the pattern
    """
    # For simple exclude-style component matching
    if component_matching:
        parts = os.path.normpath(path).split(os.sep)
        return any(fnmatch.fnmatch(part, pattern) for part in parts)

    # Convert paths to absolute for consistent comparison
    abs_path = os.path.abspath(path)

    # Handle relative path navigation in the pattern
    if ".." in pattern or "/" in pattern or "\\" in pattern:
        # If pattern contains path navigation, resolve it to an absolute path
        resolved_pattern = resolve_pattern(pattern)

        # Check if this is a directory pattern with a wildcard
        if "*" in resolved_pattern:
            # Get the directory part of the pattern
            pattern_dir = os.path.dirname(resolved_pattern)
            # Get the filename pattern
            pattern_file = os.path.basename(resolved_pattern)

            # Check if the file is in or under the pattern directory
            file_dir = os.path.dirname(abs_path)
            if file_dir.startswith(pattern_dir):
                # Match the filename against the pattern
                return fnmatch.fnmatch(os.path.basename(abs_path), pattern_file)
            return False  # Not under the pattern directory
        # Direct file match
        return abs_path == resolved_pattern or fnmatch.fnmatch(abs_path, resolved_pattern)
    # Regular pattern without navigation, use relative path matching
    return fnmatch.fnmatch(path, pattern)


def should_exclude(path: str, exclude_patterns: list[str]) -> bool:
    """
    Returns True if any component of the path matches an exclude pattern.
    """
    return any(match_pattern(path, pattern, component_matching=True) for pattern in exclude_patterns)


def should_include(path: str, include_patterns: list[str]) -> bool:
    """
    Returns True if the path matches any of the include patterns.
    Handles relative path navigation in include patterns.
    """
    return any(match_pattern(path, pattern) for pattern in include_patterns)


def collect_files(patterns: list[str], exclude_patterns: list[str], include_patterns: list[str]) -> list[str]:
    """
    Collects file paths matching the given patterns, applying exclusion first.
    Files that match an include pattern are added back in.

    Returns a sorted list of absolute file paths.
    """
    collected = set()

    # Process included files with simple filenames or relative paths
    for pattern in include_patterns:
        # Check for files in the current directory first
        direct_matches = glob.glob(pattern, recursive=True)
        for match in direct_matches:
            if os.path.isfile(match):
                collected.add(os.path.abspath(match))

        # Then check for relative paths
        if ".." in pattern or os.path.isabs(pattern):
            resolved_pattern = resolve_pattern(pattern)

            # Direct file inclusion
            if "*" not in resolved_pattern and os.path.isfile(resolved_pattern):
                collected.add(resolved_pattern)
            else:
                # Pattern with wildcards
                directory = os.path.dirname(resolved_pattern)
                if os.path.exists(directory):
                    filename_pattern = os.path.basename(resolved_pattern)
                    for root, _, files in os.walk(directory):
                        for file in files:
                            if fnmatch.fnmatch(file, filename_pattern):
                                full_path = os.path.join(root, file)
                                collected.add(os.path.abspath(full_path))

    # Process the main patterns
    for pattern in patterns:
        matches = glob.glob(pattern, recursive=True)
        for path in matches:
            if os.path.isfile(path):
                process_file(path, collected, exclude_patterns, include_patterns)
            elif os.path.isdir(path):
                process_directory(path, collected, exclude_patterns, include_patterns)

    return sorted(collected)


def process_file(file_path: str, collected: set[str], exclude_patterns: list[str], include_patterns: list[str]) -> None:
    """Process a single file"""
    abs_path = os.path.abspath(file_path)
    rel_path = os.path.relpath(file_path)

    # Skip if excluded and not specifically included
    if should_exclude(rel_path, exclude_patterns) and not should_include(rel_path, include_patterns):
        return

    collected.add(abs_path)


def process_directory(
    dir_path: str, collected: set[str], exclude_patterns: list[str], include_patterns: list[str]
) -> None:
    """Process a directory recursively"""
    for root, dirs, files in os.walk(dir_path):
        # Filter directories based on exclude patterns, but respect include patterns
        dirs[:] = [
            d
            for d in dirs
            if not should_exclude(os.path.join(root, d), exclude_patterns)
            or should_include(os.path.join(root, d), include_patterns)
        ]

        # Process each file in the directory
        for file in files:
            full_path = os.path.join(root, file)
            process_file(full_path, collected, exclude_patterns, include_patterns)


def read_file(file_path: str) -> tuple[str, str | None]:
    """
    Read a file and return its content.

    Returns:
        Tuple of (content, error_message)
    """
    # Check if file is likely binary
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            if b"\0" in chunk:  # Simple binary check
                return "[Binary file not displayed]", None

        # If not binary, read as text
        with open(file_path, encoding="utf-8") as f:
            return f.read(), None
    except UnicodeDecodeError:
        # Handle encoding issues
        return "[File contains non-UTF-8 characters]", None
    except Exception as e:
        return "", f"[ERROR reading file: {e}]"


def format_output(
    file_paths: list[str],
    format_type: str,
    exclude_patterns: list[str],
    include_patterns: list[str],
    patterns: list[str],
) -> str:
    """
    Format the collected files according to the output format.

    Args:
        file_paths: List of absolute file paths to format
        format_type: Output format type ("markdown" or "plain")
        exclude_patterns: List of exclusion patterns (for info)
        include_patterns: List of inclusion patterns (for info)
        patterns: Original input patterns (for info)

    Returns:
        Formatted output string
    """
    output_lines = []

    # Add metadata header
    now = datetime.datetime.now()
    date_str = now.strftime("%-m/%-d/%Y, %-I:%M:%S %p")
    output_lines.append(f"# {patterns}")
    output_lines.append("")
    output_lines.append("[collect-files]")
    output_lines.append("")
    output_lines.append(f"**Search:** {patterns}")
    output_lines.append(f"**Exclude:** {exclude_patterns}")
    output_lines.append(f"**Include:** {include_patterns}")
    output_lines.append(f"**Date:** {date_str}")
    output_lines.append(f"**Files:** {len(file_paths)}\n\n")

    # Process each file
    for file_path in file_paths:
        rel_path = os.path.relpath(file_path)

        # Add file header based on format
        if format_type == "markdown":
            output_lines.append(f"### File: {rel_path}")
            output_lines.append("```")
        else:
            output_lines.append(f"=== File: {rel_path} ===")

        # Read and add file content
        content, error = read_file(file_path)
        if error:
            output_lines.append(error)
        else:
            output_lines.append(content)

        # Add file footer based on format
        if format_type == "markdown":
            output_lines.append("```")

        # Add separator between files
        output_lines.append("\n")

    return "\n".join(output_lines)


def main() -> None:
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Recursively collect files matching the given patterns and output a document with file names and content."
    )
    parser.add_argument("patterns", nargs="+", help="File and/or directory patterns to collect (e.g. *.py or output)")
    parser.add_argument(
        "--exclude",
        type=str,
        default="",
        help="Comma-separated patterns to exclude (will be combined with default excludes: "
        + ",".join(DEFAULT_EXCLUDE)
        + ")",
    )
    parser.add_argument(
        "--include", type=str, default="", help="Comma-separated patterns to include (overrides excludes if matched)"
    )
    parser.add_argument(
        "--format", type=str, choices=["markdown", "plain"], default="plain", help="Output format (default: plain)"
    )
    args = parser.parse_args()

    # Parse pattern arguments and combine with default excludes
    user_exclude_patterns = parse_patterns(args.exclude)
    exclude_patterns = DEFAULT_EXCLUDE + user_exclude_patterns

    include_patterns = parse_patterns(args.include) if args.include else []

    # Collect files
    patterns = args.patterns
    files = collect_files(patterns, exclude_patterns, include_patterns)

    # Format and print output
    output = format_output(files, args.format, exclude_patterns, include_patterns, patterns)
    print(output)


if __name__ == "__main__":
    main()
