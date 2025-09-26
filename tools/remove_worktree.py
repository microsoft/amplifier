#!/usr/bin/env python3
"""
Remove a git worktree and optionally delete the associated branch.

Usage:
    python tools/remove_worktree.py feature-branch
    python tools/remove_worktree.py feature-branch --force
    python tools/remove_worktree.py .              # Remove current worktree (from within worktree)
    python tools/remove_worktree.py . --force       # Force remove current worktree
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def is_in_worktree():
    """Check if we're running from within a worktree (not the main repo)."""
    try:
        # Get the main git directory
        result = subprocess.run(["git", "rev-parse", "--git-common-dir"], capture_output=True, text=True, check=True)
        git_common_dir = Path(result.stdout.strip()).resolve()

        # Get the current git directory
        result = subprocess.run(["git", "rev-parse", "--git-dir"], capture_output=True, text=True, check=True)
        git_dir = Path(result.stdout.strip()).resolve()

        # If they differ, we're in a worktree
        return git_common_dir != git_dir
    except subprocess.CalledProcessError:
        return False


def get_worktree_info():
    """Get current worktree branch and main repo path."""
    try:
        # Get current branch
        result = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, check=True)
        current_branch = result.stdout.strip()

        # Get main repo path
        result = subprocess.run(["git", "rev-parse", "--git-common-dir"], capture_output=True, text=True, check=True)
        git_common_dir = Path(result.stdout.strip()).resolve()
        main_repo = git_common_dir.parent

        return current_branch, main_repo
    except subprocess.CalledProcessError:
        return None, None


def run_git_command(cmd: list[str]) -> tuple[int, str, str]:
    """Run a git command and return exit code, stdout, stderr."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def main():
    parser = argparse.ArgumentParser(description="Remove a git worktree and optionally delete its branch")
    parser.add_argument("branch", help="Name of the branch/worktree to remove, or '.' for current worktree")
    parser.add_argument("--force", action="store_true", help="Force removal even with uncommitted changes")
    args = parser.parse_args()

    in_worktree = is_in_worktree()
    current_branch, main_repo = get_worktree_info()

    # Handle special case: removing current worktree
    if args.branch == ".":
        if not in_worktree:
            print("❌ Error: Cannot use '.' from the main repository.")
            print("Please specify a branch name to remove.")
            sys.exit(1)

        if not current_branch or not main_repo:
            print("❌ Error: Could not determine worktree information.")
            sys.exit(1)

        # User wants to remove current worktree
        print(f"⚠️  WARNING: You are about to remove the current worktree '{current_branch}'")
        print("Your current directory will be deleted after this operation.")
        print("You will need to navigate to a valid directory afterwards.\n")

        # Set the branch to the current branch
        args.branch = current_branch

        # Change to main repo to perform the removal
        print(f"Switching to main repository at {main_repo}...")
        os.chdir(main_repo)

    elif args.branch == current_branch and in_worktree:
        # User specified current branch name explicitly
        if not main_repo:
            print("❌ Error: Could not determine main repository path.")
            sys.exit(1)

        print(f"⚠️  WARNING: You are removing the worktree you're currently in '{current_branch}'")
        print("Your current directory will be deleted after this operation.\n")

        # Change to main repo to perform the removal
        print(f"Switching to main repository at {main_repo}...")
        os.chdir(main_repo)

    elif in_worktree:
        # In a worktree but removing a different one - need to go to main repo
        if not main_repo:
            print("❌ Error: Could not determine main repository path.")
            sys.exit(1)

        print(f"Switching to main repository at {main_repo} to perform removal...")
        os.chdir(main_repo)

    # Continue with normal removal process

    # Get the base repository name
    current_dir = Path.cwd()
    repo_name = current_dir.name

    # Extract feature name (part after last '/' if present, otherwise full name)
    feature_name = args.branch.split("/")[-1] if "/" in args.branch else args.branch

    # Construct worktree path (same pattern as create_worktree.py)
    worktree_path = current_dir.parent / f"{repo_name}.{feature_name}"

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
