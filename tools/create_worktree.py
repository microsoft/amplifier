#!/usr/bin/env python3
"""
Create a git worktree for parallel development with efficient data copying and proper venv setup.

Usage:
    python tools/create_worktree.py <branch-name>

This will:
1. Create a worktree in ../repo-name-branch-name/
2. Copy .data/ directory contents efficiently using rsync
3. Set up a local .venv for the worktree using uv
4. Output instructions to navigate and activate the venv
"""

import os
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
            print("❌ Error: Cannot create worktrees from within a worktree.")
            print("\nPlease run this command from the main repository:")
            print(f"  cd {main_repo}")
            print(f"  make worktree {sys.argv[1] if len(sys.argv) > 1 else '<branch-name>'}")
            sys.exit(1)
    except subprocess.CalledProcessError:
        # Not in a git repository at all
        print("❌ Error: Not in a git repository.")
        sys.exit(1)


def run_command(cmd, cwd=None, capture_output=False, env=None):
    """Run a command and handle errors gracefully."""
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=capture_output, text=True, check=True, env=env)
        return result
    except subprocess.CalledProcessError as e:
        if capture_output:
            print(f"Command failed: {' '.join(cmd)}")
            if e.stderr:
                print(f"Error: {e.stderr}")
        raise


def setup_worktree_venv(worktree_path):
    """Set up a local virtual environment for the worktree using uv."""
    print("\n🐍 Setting up virtual environment for worktree...")

    # Check if uv is available
    try:
        subprocess.run(["uv", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Warning: 'uv' not found. Please install dependencies manually:")
        print(f"   cd {worktree_path}")
        print("   make install")
        return False

    # Create .venv in the worktree
    print("Creating .venv in worktree...")
    try:
        # Use uv to create venv and sync dependencies
        run_command(["uv", "venv"], cwd=worktree_path)
        print("Installing dependencies...")

        # Clean environment to avoid VIRTUAL_ENV warning from parent shell
        env = os.environ.copy()
        env.pop("VIRTUAL_ENV", None)  # Remove if exists

        # Run with clean environment and reduced verbosity (--quiet suppresses package list)
        run_command(["uv", "sync", "--group", "dev", "--quiet"], cwd=worktree_path, env=env)
        print("✅ Virtual environment created and dependencies installed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Warning: Failed to set up venv automatically: {e}")
        print("   You can set it up manually with: make install")
        return False


def main():
    # Ensure we're not running from within a worktree
    ensure_not_in_worktree()

    # Get branch name from arguments
    if len(sys.argv) != 2:
        print("Usage: python tools/create_worktree.py <branch-name>")
        sys.exit(1)

    branch_name = sys.argv[1]

    # Get current repo path and name
    current_path = Path.cwd()
    repo_name = current_path.name

    # Build worktree path
    worktree_name = f"{repo_name}-{branch_name}"
    worktree_path = current_path.parent / worktree_name

    # Create the worktree
    print(f"Creating worktree at {worktree_path}...")
    try:
        # Check if branch exists locally
        result = subprocess.run(["git", "rev-parse", "--verify", branch_name], capture_output=True, text=True)

        if result.returncode == 0:
            # Branch exists, use it
            subprocess.run(["git", "worktree", "add", str(worktree_path), branch_name], check=True)
        else:
            # Branch doesn't exist, create it
            subprocess.run(["git", "worktree", "add", "-b", branch_name, str(worktree_path)], check=True)
            print(f"Created new branch: {branch_name}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to create worktree: {e}")
        sys.exit(1)

    # Copy .data directory if it exists
    data_dir = current_path / ".data"
    if data_dir.exists() and data_dir.is_dir():
        print("\nCopying .data directory (this may take a moment)...")
        target_data_dir = worktree_path / ".data"

        try:
            # Use rsync for efficient copying with progress
            subprocess.run(
                [
                    "rsync",
                    "-av",  # archive mode with verbose
                    "--progress",  # show progress
                    f"{data_dir}/",  # trailing slash to copy contents
                    f"{target_data_dir}/",
                ],
                check=True,
            )
            print("Data copy complete!")
        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to copy .data directory: {e}")
            print("You may need to copy it manually or use cp instead of rsync")
        except FileNotFoundError:
            # rsync not available, fallback to cp
            print("rsync not found, using cp instead...")
            try:
                subprocess.run(["cp", "-r", str(data_dir), str(worktree_path)], check=True)
                print("Data copy complete!")
            except subprocess.CalledProcessError as e:
                print(f"Warning: Failed to copy .data directory: {e}")

    # Set up virtual environment for the worktree
    venv_created = setup_worktree_venv(worktree_path)

    # Output instructions
    print("\n✓ Worktree created successfully!")
    print("\nTo use your new worktree:")
    print(f"cd {worktree_path}")

    if venv_created:
        print("\n# The virtual environment is already set up!")
        print("# To activate it (if needed):")
        print("source .venv/bin/activate")
    else:
        print("\n# Set up the virtual environment:")
        print("make install")


if __name__ == "__main__":
    main()
