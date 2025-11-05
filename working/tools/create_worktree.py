#!/usr/bin/env python3
"""
Create a git worktree for parallel development with efficient data copying and proper venv setup.

Usage:
    python tools/create_worktree.py <branch-name>

This will:
1. Create a worktree in ../repo-name.branch-name/
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


def run_command(cmd, cwd=None, capture_output=False, env=None, eval_mode=False):
    """Run a command and handle errors gracefully."""
    try:
        # In eval mode, redirect stdout to stderr to avoid interfering with eval
        if eval_mode and not capture_output:
            result = subprocess.run(
                cmd, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True, check=True, env=env
            )
        else:
            result = subprocess.run(cmd, cwd=cwd, capture_output=capture_output, text=True, check=True, env=env)
        return result
    except subprocess.CalledProcessError as e:
        if capture_output:
            print(f"Command failed: {' '.join(cmd)}", file=sys.stderr)
            if e.stderr:
                print(f"Error: {e.stderr}", file=sys.stderr)
        raise


def setup_worktree_venv(worktree_path, eval_mode=False):
    """Set up a local virtual environment for the worktree using uv."""
    if not eval_mode:
        print("\n🐍 Setting up virtual environment for worktree...")

    # Check if uv is available
    try:
        subprocess.run(["uv", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        if not eval_mode:
            print("⚠️  Warning: 'uv' not found. Please install dependencies manually:")
            print(f"   cd {worktree_path}")
            print("   make install")
        return False

    # Create .venv in the worktree
    if not eval_mode:
        print("Creating .venv in worktree...")
    try:
        # Use uv to create venv and sync dependencies
        run_command(["uv", "venv"], cwd=worktree_path, eval_mode=eval_mode)
        if not eval_mode:
            print("Installing dependencies...")

        # Clean environment to avoid VIRTUAL_ENV warning from parent shell
        env = os.environ.copy()
        env.pop("VIRTUAL_ENV", None)  # Remove if exists

        # Run with clean environment and reduced verbosity (--quiet suppresses package list)
        run_command(["uv", "sync", "--group", "dev", "--quiet"], cwd=worktree_path, env=env, eval_mode=eval_mode)
        if not eval_mode:
            print("✅ Virtual environment created and dependencies installed!")
        return True
    except subprocess.CalledProcessError as e:
        if not eval_mode:
            print(f"⚠️  Warning: Failed to set up venv automatically: {e}")
            print("   You can set it up manually with: make install")
        return False


def is_eval_context():
    """Detect if we're being evaluated based on parent process."""
    # Check for explicit eval flag or if output is being captured in a subshell
    # When run as: eval $(make worktree ...), the output is captured
    # When run as: make worktree ..., it's displayed directly
    #
    # A better approach: check if we're in a command substitution
    # by looking for specific environment markers

    # If MAKE_TERMOUT or MAKE_TERMERR are set, we're likely in direct make mode
    # Otherwise, we might be in eval/subshell mode
    # However, this is unreliable. Let's use a simpler approach:
    # Always show instructions unless --eval flag is present
    return "--eval" in sys.argv


def main():
    # Ensure we're not running from within a worktree
    ensure_not_in_worktree()

    # Check for --eval flag
    eval_mode = is_eval_context()
    args = [arg for arg in sys.argv[1:] if arg != "--eval"]

    # Get branch name from arguments
    if len(args) != 1:
        print("Usage: python tools/create_worktree.py [--eval] <branch-name>", file=sys.stderr)
        sys.exit(1)

    branch_name = args[0]

    # Extract feature name (part after last '/' if present, otherwise full name)
    feature_name = branch_name.split("/")[-1] if "/" in branch_name else branch_name

    # Get current repo path and name
    current_path = Path.cwd()
    repo_name = current_path.name

    # Build worktree path using feature name for directory
    worktree_name = f"{repo_name}.{feature_name}"
    worktree_path = current_path.parent / worktree_name

    # Create the worktree
    if not eval_mode:
        print(f"Creating worktree at {worktree_path}...")
    try:
        # Check if branch exists locally
        result = subprocess.run(["git", "rev-parse", "--verify", branch_name], capture_output=True, text=True)

        if result.returncode == 0:
            # Branch exists, use it
            run_command(["git", "worktree", "add", str(worktree_path), branch_name], eval_mode=eval_mode)
        else:
            # Branch doesn't exist, create it
            run_command(["git", "worktree", "add", "-b", branch_name, str(worktree_path)], eval_mode=eval_mode)
            if not eval_mode:
                print(f"Created new branch: {branch_name}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to create worktree: {e}", file=sys.stderr)
        sys.exit(1)

    # Copy .data directory if it exists
    data_dir = current_path / ".data"
    if data_dir.exists() and data_dir.is_dir():
        if not eval_mode:
            print("\nCopying .data directory (this may take a moment)...")
        target_data_dir = worktree_path / ".data"

        try:
            # Use rsync for efficient copying with progress
            if eval_mode:
                # In eval mode, suppress all output
                run_command(
                    [
                        "rsync",
                        "-a",  # archive mode without verbose
                        f"{data_dir}/",  # trailing slash to copy contents
                        f"{target_data_dir}/",
                    ],
                    eval_mode=True,
                )
            else:
                # In normal mode, show progress
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
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to cp, quietly in eval mode
            try:
                run_command(["cp", "-r", str(data_dir), str(worktree_path)], eval_mode=eval_mode)
                if not eval_mode:
                    print("Data copy complete!")
            except subprocess.CalledProcessError as e:
                if not eval_mode:
                    print(f"Warning: Failed to copy .data directory: {e}")

    # Set up virtual environment for the worktree
    venv_created = setup_worktree_venv(worktree_path, eval_mode)

    # Generate output based on mode
    if eval_mode:
        # Being evaluated - output shell commands
        if venv_created:
            # Output commands to change directory and activate venv
            print(f"cd {worktree_path} && source .venv/bin/activate && echo '\n✓ Switched to worktree: {feature_name}'")
        else:
            # Just change directory if venv wasn't created
            print(
                f"cd {worktree_path} && echo '\n✓ Switched to worktree: {feature_name} (run make install to set up environment)'"
            )
    else:
        # Running directly in TTY - show instructions
        print("\n✓ Worktree created successfully!")
        print(f"  📁 Location: {worktree_path}")
        if venv_created:
            print("  🐍 Virtual environment: Ready")
        else:
            print("  ⚠️  Virtual environment: Setup required")

        print("\n" + "─" * 60)
        print("To switch to your new worktree, run these commands:")
        print("─" * 60)
        print(f"\ncd {worktree_path}")
        if venv_created:
            print("source .venv/bin/activate")
        else:
            print("make install  # Set up virtual environment")
            print("source .venv/bin/activate")
        print("\n" + "─" * 60)


if __name__ == "__main__":
    main()
