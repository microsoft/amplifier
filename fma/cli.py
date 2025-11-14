"""FMA CLI entry point."""

import argparse
import sys
from pathlib import Path

from fma.src.revisions.revision import setup_prd_worktree


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="FMA - Feature Management Agent CLI tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # fma build command
    build_parser = subparsers.add_parser(
        "build",
        help="Build a PRD by creating a worktree and setting up the environment",
    )
    build_parser.add_argument(
        "prd_number",
        help="PRD number (e.g., 001 for prd/001_basic_functions.md)",
    )
    build_parser.add_argument(
        "--base-branch",
        default="main",
        help="Base branch to create worktree from (default: main)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "build":
        build_command(args.prd_number, args.base_branch)


def build_command(prd_number: str, base_branch: str):
    """Execute the build command for a PRD.

    Args:
        prd_number: PRD number (e.g., "001")
        base_branch: Base branch to create worktree from
    """
    # Find PRD file
    prd_file = find_prd_file(prd_number)
    if not prd_file:
        print(f"❌ Error: Could not find PRD file for number {prd_number}")
        print(f"   Expected: prd/{prd_number}_*.md")
        sys.exit(1)

    print(f"📄 Found PRD: {prd_file}")

    # Extract PRD name from filename
    prd_name = prd_file.stem  # e.g., "001_basic_functions"

    try:
        # Setup worktree
        result = setup_prd_worktree(prd_name, base_branch)

        print("\n" + "=" * 60)
        print("🎉 SUCCESS!")
        print("=" * 60)
        print(f"\nWorktree created at: {result['worktree_path']}")
        print(f"Unique ID: {result['id']}")
        print("\nNext steps:")
        print(f"  cd {result['worktree_path']}")
        print("  # Start working on the PRD!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


def find_prd_file(prd_number: str) -> Path | None:
    """Find PRD file by number.

    Args:
        prd_number: PRD number (e.g., "001")

    Returns:
        Path to PRD file or None if not found
    """
    # Look in prd/ directory
    prd_dir = Path.cwd() / "prd"
    if not prd_dir.exists():
        return None

    # Find file matching pattern: {prd_number}_*.md
    pattern = f"{prd_number}_*.md"
    matches = list(prd_dir.glob(pattern))

    if matches:
        return matches[0]

    return None


if __name__ == "__main__":
    main()
