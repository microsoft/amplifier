#!/usr/bin/env python3
"""
Clean up WSL-related files that accidentally get created in the repository.

This tool removes Windows Subsystem for Linux (WSL) metadata files that can
clutter the repository, including Zone.Identifier and endpoint DLP files.
"""

import sys
from pathlib import Path


def find_wsl_files(root_dir: Path) -> list[Path]:
    """
    Find all WSL-related files in the directory tree.

    Args:
        root_dir: Root directory to search from

    Returns:
        List of paths to WSL-related files
    """
    patterns = ["*:Zone.Identifier", "*:sec.endpointdlp"]

    wsl_files = []
    for pattern in patterns:
        wsl_files.extend(root_dir.rglob(pattern))

    return wsl_files


def clean_wsl_files(root_dir: Path, dry_run: bool = False) -> int:
    """
    Remove WSL-related files from the directory tree.

    Args:
        root_dir: Root directory to clean
        dry_run: If True, only show what would be deleted without actually deleting

    Returns:
        Number of files cleaned
    """
    wsl_files = find_wsl_files(root_dir)

    if not wsl_files:
        print("No WSL-related files found.")
        return 0

    print(f"Found {len(wsl_files)} WSL-related file(s):")

    for file_path in wsl_files:
        rel_path = file_path.relative_to(root_dir)
        if dry_run:
            print(f"  [DRY RUN] Would remove: {rel_path}")
        else:
            try:
                file_path.unlink()
                print(f"  Removed: {rel_path}")
            except Exception as e:
                print(f"  ERROR removing {rel_path}: {e}", file=sys.stderr)

    if dry_run:
        print(f"\nDry run complete. Would have removed {len(wsl_files)} file(s).")
    else:
        print(f"\nCleaned {len(wsl_files)} WSL-related file(s).")

    return len(wsl_files)


def main():
    """Main entry point for the script."""
    import argparse
    import subprocess

    parser = argparse.ArgumentParser(description="Clean up WSL-related files from the repository")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without actually deleting")
    parser.add_argument("--path", type=Path, default=Path.cwd(), help="Path to clean (defaults to current directory)")

    args = parser.parse_args()

    if not args.path.exists():
        print(f"Error: Path {args.path} does not exist", file=sys.stderr)
        sys.exit(1)

    if not args.path.is_dir():
        print(f"Error: Path {args.path} is not a directory", file=sys.stderr)
        sys.exit(1)

    # Find git root if we're in a git repository
    try:
        git_root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=args.path, text=True).strip()
        root_dir = Path(git_root)
        print(f"Cleaning WSL files from git repository: {root_dir}")
    except subprocess.CalledProcessError:
        root_dir = args.path
        print(f"Cleaning WSL files from directory: {root_dir}")

    print()

    clean_wsl_files(root_dir, dry_run=args.dry_run)

    # Always exit with status 0 (success) - finding no files is not an error
    sys.exit(0)


if __name__ == "__main__":
    main()
