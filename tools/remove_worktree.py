#!/usr/bin/env python3
"""
Remove a git worktree and optionally delete the associated branch.

Usage:
    python tools/remove_worktree.py feature-branch
    python tools/remove_worktree.py feature-branch --force
"""

import argparse
import subprocess
import sys
from pathlib import Path


def ensure_not_in_worktree():
    """Ensure we're not running from within a worktree."""
    try:
        # Get the main git directory
        result = subprocess.run(["git", "rev-parse", "--git-common-dir"], capture_output=True, text=True, check=True)
        git_common_dir = Path(result.stdout.strip()).resolve()

        # Get the current git directory
        result = subprocess.run(["git", "rev-parse", "--git-dir"], capture_output=True, text=True, check=True)
        git_dir = Path(result.stdout.strip()).resolve()

        # If they differ, we're in a worktree
        if git_common_dir != git_dir:
            # Get the main repo path
            main_repo = git_common_dir.parent
            print("❌ Error: Cannot remove worktrees from within a worktree.")
            print("\nPlease run this command from the main repository:")
            print(f"  cd {main_repo}")
            print(f"  make worktree-rm {sys.argv[1] if len(sys.argv) > 1 else '<branch-name>'}")
            sys.exit(1)
    except subprocess.CalledProcessError:
        # Not in a git repository at all
        print("❌ Error: Not in a git repository.")
        sys.exit(1)


def run_git_command(cmd: list[str]) -> tuple[int, str, str]:
    """Run a git command and return exit code, stdout, stderr."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def main():
    # Ensure we're not running from within a worktree
    ensure_not_in_worktree()

    parser = argparse.ArgumentParser(description="Remove a git worktree and optionally delete its branch")
    parser.add_argument("branch", help="Name of the branch/worktree to remove")
    parser.add_argument("--force", action="store_true", help="Force removal even with uncommitted changes")
    args = parser.parse_args()

    # Get the base repository name
    current_dir = Path.cwd()
    repo_name = current_dir.name

    # Construct worktree path (same pattern as create_worktree.py)
    worktree_path = current_dir.parent / f"{repo_name}-{args.branch}"

    print(f"Looking for worktree at: {worktree_path}")

    # Check if worktree exists
    returncode, stdout, _ = run_git_command(["git", "worktree", "list"])
    if returncode != 0:
        print("Error: Failed to list worktrees")
        sys.exit(1)

    worktree_exists = str(worktree_path) in stdout
    if not worktree_exists:
        print(f"Error: Worktree for branch '{args.branch}' not found at {worktree_path}")
        sys.exit(1)

    # Remove the worktree
    remove_cmd = ["git", "worktree", "remove", str(worktree_path)]
    if args.force:
        remove_cmd.append("--force")

    print(f"Removing worktree at {worktree_path}...")
    returncode, stdout, stderr = run_git_command(remove_cmd)

    if returncode != 0:
        if "contains modified or untracked files" in stderr:
            print("Error: Worktree contains uncommitted changes. Use --force to override.")
        else:
            print(f"Error removing worktree: {stderr}")
        sys.exit(1)

    print(f"Successfully removed worktree at {worktree_path}")

    # Try to delete the branch
    print(f"Attempting to delete branch '{args.branch}'...")

    # Check current branch
    returncode, current_branch, _ = run_git_command(["git", "branch", "--show-current"])
    if returncode == 0 and current_branch == args.branch:
        print(f"Cannot delete branch '{args.branch}' - it is currently checked out")
        return

    # Try to delete the branch
    returncode, stdout, stderr = run_git_command(["git", "branch", "-d", args.branch])

    if returncode == 0:
        print(f"Successfully deleted branch '{args.branch}'")
    elif "not fully merged" in stderr:
        # Try force delete if regular delete fails due to unmerged changes
        print("Branch has unmerged changes, force deleting...")
        returncode, stdout, stderr = run_git_command(["git", "branch", "-D", args.branch])
        if returncode == 0:
            print(f"Successfully force-deleted branch '{args.branch}'")
        else:
            print(f"Warning: Could not delete branch: {stderr}")
    else:
        print(f"Warning: Could not delete branch: {stderr}")


if __name__ == "__main__":
    main()
