#!/usr/bin/env python3
"""Worktree manager for stashing, unstashing, and adopting git worktrees.

This tool manages git worktrees with three main features:
1. Stash: Hide worktrees from git tracking without deleting directories
2. Unstash: Restore stashed worktrees back to git tracking
3. Adopt: Create local worktree from remote branch
"""

import json
import subprocess
import sys
from pathlib import Path


class WorktreeManager:
    """Manages git worktree stashing and restoration."""

    def __init__(self):
        """Initialize worktree manager."""
        self.git_dir = Path(".git")
        self.stash_file = self.git_dir / "worktree-stash.json"

        if not self.git_dir.exists():
            print("Error: Not in a git repository")
            sys.exit(1)

    def _run_git(self, *args: str) -> tuple[int, str, str]:
        """Run git command and return (returncode, stdout, stderr)."""
        result = subprocess.run(["git"] + list(args), capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr

    def _load_stash_manifest(self) -> dict:
        """Load stash manifest from file."""
        if not self.stash_file.exists():
            return {"stashed": []}

        try:
            with open(self.stash_file) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return {"stashed": []}

    def _save_stash_manifest(self, manifest: dict) -> None:
        """Save stash manifest atomically."""
        temp_file = self.stash_file.with_suffix(".tmp")

        try:
            with open(temp_file, "w") as f:
                json.dump(manifest, f, indent=2)
            temp_file.replace(self.stash_file)
        except OSError as e:
            print(f"Error saving manifest: {e}")
            sys.exit(1)

    def _get_repo_name(self) -> str:
        """Get the repository name from git."""
        code, stdout, _ = self._run_git("rev-parse", "--show-toplevel")
        if code == 0:
            return Path(stdout.strip()).name
        return "repo"

    def resolve_worktree_path(self, feature_name: str) -> Path | None:
        """Resolve worktree path from feature name.

        Args:
            feature_name: The feature name without username prefix
                         (e.g., 'my-feature' not 'username/my-feature')

        Checks for existing worktrees with dot separator first, then hyphen.
        Returns the resolved path or None if not found.
        """
        repo_name = self._get_repo_name()
        main_repo = Path.cwd()

        # Try dot separator first (new format)
        dot_path = main_repo.parent / f"{repo_name}.{feature_name}"
        if dot_path.exists():
            return dot_path

        # Fall back to hyphen separator (old format)
        hyphen_path = main_repo.parent / f"{repo_name}-{feature_name}"
        if hyphen_path.exists():
            return hyphen_path

        return None

    def _get_worktree_info(self, path: str) -> dict | None:
        """Get worktree information for a given path."""
        code, stdout, _ = self._run_git("worktree", "list", "--porcelain")

        if code != 0:
            return None

        # Parse worktree list output
        current_worktree = {}
        for line in stdout.strip().split("\n"):
            if not line:
                if current_worktree.get("worktree") == path:
                    return current_worktree
                current_worktree = {}
            elif line.startswith("worktree "):
                current_worktree["worktree"] = line[9:]
            elif line.startswith("branch "):
                current_worktree["branch"] = line[7:]
            elif line.startswith("HEAD "):
                current_worktree["head"] = line[5:]

        # Check last worktree
        if current_worktree.get("worktree") == path:
            return current_worktree

        return None

    def stash_by_name(self, feature_name: str) -> None:
        """Stash a worktree by feature name or branch name.

        If a branch name with username prefix is provided (e.g., 'username/feature'),
        it will be stripped to just the feature name.
        """
        # Strip username prefix if present (part after last '/')
        feature_name = feature_name.split("/")[-1] if "/" in feature_name else feature_name

        path = self.resolve_worktree_path(feature_name)
        if not path:
            print(f"Error: Worktree not found for feature: {feature_name}")
            print(f"  Looked for: {self._get_repo_name()}.{feature_name}")
            print(f"  And: {self._get_repo_name()}-{feature_name}")
            sys.exit(1)
        self.stash(str(path))

    def unstash_by_name(self, feature_name: str) -> None:
        """Unstash a worktree by feature name or branch name.

        If a branch name with username prefix is provided (e.g., 'username/feature'),
        it will be stripped to just the feature name.
        """
        # Strip username prefix if present (part after last '/')
        feature_name = feature_name.split("/")[-1] if "/" in feature_name else feature_name

        path = self.resolve_worktree_path(feature_name)
        if not path:
            print(f"Error: Worktree not found for feature: {feature_name}")
            print(f"  Looked for: {self._get_repo_name()}.{feature_name}")
            print(f"  And: {self._get_repo_name()}-{feature_name}")
            sys.exit(1)
        self.unstash(str(path))

    def stash(self, worktree_path: str) -> None:
        """Stash a worktree - hide from git but keep directory."""
        # Resolve path
        path = Path(worktree_path).resolve()

        if not path.exists():
            print(f"Error: Worktree path does not exist: {path}")
            sys.exit(1)

        # Get worktree info before removing
        info = self._get_worktree_info(str(path))

        if not info:
            print(f"Error: {path} is not a git worktree")
            sys.exit(1)

        # Find the worktree name in .git/worktrees
        # The name is typically the last component of the path, but we need to find the exact match
        worktrees_dir = self.git_dir / "worktrees"
        if not worktrees_dir.exists():
            print(f"Error: No worktrees directory found in {self.git_dir}")
            sys.exit(1)

        # Find the matching worktree metadata directory
        worktree_meta_dir = None
        for meta_dir in worktrees_dir.iterdir():
            if meta_dir.is_dir():
                gitdir_file = meta_dir / "gitdir"
                if gitdir_file.exists():
                    try:
                        with open(gitdir_file) as f:
                            stored_path = Path(f.read().strip())
                            # gitdir contains path/.git, so compare parent
                            # Compare resolved paths to handle relative vs absolute
                            if stored_path.parent.resolve() == path:
                                worktree_meta_dir = meta_dir
                                break
                    except (OSError, ValueError):
                        continue

        if not worktree_meta_dir:
            print(f"Error: Could not find git metadata for worktree: {path}")
            sys.exit(1)

        # Remove the git metadata directory (this detaches the worktree without deleting it)
        try:
            import shutil

            shutil.rmtree(worktree_meta_dir)
        except OSError as e:
            print(f"Error removing worktree metadata: {e}")
            sys.exit(1)

        # Add to stash manifest
        manifest = self._load_stash_manifest()

        stash_entry = {"path": str(path), "branch": info.get("branch", ""), "head": info.get("head", "")}

        # Avoid duplicates
        if not any(s["path"] == str(path) for s in manifest["stashed"]):
            manifest["stashed"].append(stash_entry)
            self._save_stash_manifest(manifest)

        print(f"✓ Stashed worktree: {path}")
        print(f"  Branch: {info.get('branch', 'unknown')}")

    def unstash(self, worktree_path: str) -> None:
        """Restore a stashed worktree back to git tracking."""
        # Resolve path
        path = Path(worktree_path).resolve()

        if not path.exists():
            print(f"Error: Worktree path does not exist: {path}")
            sys.exit(1)

        # Load manifest and find entry
        manifest = self._load_stash_manifest()

        stash_entry = None
        for entry in manifest["stashed"]:
            if Path(entry["path"]).resolve() == path:
                stash_entry = entry
                break

        if not stash_entry:
            print(f"Error: {path} is not in stash")
            sys.exit(1)

        # Re-add worktree
        branch = stash_entry.get("branch", "")

        # Strip refs/heads/ prefix if present
        if branch.startswith("refs/heads/"):
            branch = branch[11:]

        if not branch:
            print("Error: No branch information in stash")
            sys.exit(1)

        # Git worktree add won't work if directory exists, even with --force
        # So we need to temporarily move it aside, add the worktree, then restore it
        import shutil
        import tempfile

        # Create a temporary directory name
        temp_path = Path(tempfile.mkdtemp(dir=path.parent, prefix=f".{path.name}_temp_"))

        try:
            # Move existing directory to temp location
            shutil.move(str(path), str(temp_path))

            # Add worktree (will create new directory)
            code, _, stderr = self._run_git("worktree", "add", str(path), branch)

            if code != 0:
                # Restore original if failed
                shutil.move(str(temp_path), str(path))
                print(f"Error restoring worktree: {stderr}")
                sys.exit(1)

            # Remove the newly created directory
            shutil.rmtree(str(path))

            # Restore the original directory
            shutil.move(str(temp_path), str(path))

        except Exception as e:
            # Try to restore on any error
            if temp_path.exists() and not path.exists():
                shutil.move(str(temp_path), str(path))
            print(f"Error during unstash: {e}")
            sys.exit(1)

        # Remove from stash manifest
        manifest["stashed"] = [s for s in manifest["stashed"] if Path(s["path"]).resolve() != path]
        self._save_stash_manifest(manifest)

        print(f"✓ Unstashed worktree: {path}")
        print(f"  Branch: {branch}")

    def adopt(self, branch_name: str, worktree_name: str | None = None) -> None:
        """Create local worktree from remote branch."""
        # Parse branch name (could be origin/feature or just feature)
        if "/" in branch_name and not branch_name.startswith("origin/"):
            # Assume it's a remote branch without origin prefix
            remote_branch = f"origin/{branch_name}"
            local_branch = branch_name
        elif branch_name.startswith("origin/"):
            remote_branch = branch_name
            local_branch = branch_name[7:]  # Strip "origin/"
        else:
            remote_branch = f"origin/{branch_name}"
            local_branch = branch_name

        # Determine worktree directory name
        if worktree_name:
            dir_name = worktree_name
        else:
            # Get repo name
            code, stdout, _ = self._run_git("rev-parse", "--show-toplevel")
            if code == 0:
                repo_name = Path(stdout.strip()).name
            else:
                repo_name = "repo"

            # Create directory name with dot separator
            # Extract feature name (part after last '/' if present, otherwise full name)
            feature_name = local_branch.split("/")[-1] if "/" in local_branch else local_branch
            dir_name = f"{repo_name}.{feature_name}"

        # Create worktree path (sibling to main repo)
        main_repo = Path.cwd()
        worktree_path = main_repo.parent / dir_name

        # Fetch latest from remote
        print("Fetching latest from origin...")
        code, _, stderr = self._run_git("fetch", "origin")

        if code != 0:
            print(f"Warning: Could not fetch from origin: {stderr}")

        # Create worktree
        print(f"Creating worktree at {worktree_path}...")
        code, _, stderr = self._run_git("worktree", "add", str(worktree_path), "-b", local_branch, remote_branch)

        if code != 0:
            # Try without creating new branch (if it already exists locally)
            code, _, stderr = self._run_git("worktree", "add", str(worktree_path), local_branch)

            if code != 0:
                print(f"Error creating worktree: {stderr}")
                sys.exit(1)

        # Set upstream tracking
        original_dir = Path.cwd()
        try:
            # Change to worktree directory to set upstream
            import os

            os.chdir(worktree_path)

            code, _, stderr = self._run_git("branch", "--set-upstream-to", remote_branch)

            if code != 0:
                print(f"Warning: Could not set upstream: {stderr}")
        finally:
            os.chdir(original_dir)

        print(f"✓ Created worktree: {worktree_path}")
        print(f"  Local branch: {local_branch}")
        print(f"  Tracking: {remote_branch}")

    def list_stashed(self) -> None:
        """List all stashed worktrees."""
        manifest = self._load_stash_manifest()

        if not manifest["stashed"]:
            print("No stashed worktrees")
            return

        print("Stashed worktrees:")
        for entry in manifest["stashed"]:
            print(f"  {entry['path']}")
            print(f"    Branch: {entry.get('branch', 'unknown')}")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: worktree_manager.py <command> [args]")
        print("\nCommands:")
        print("  stash <path>          Hide worktree from git tracking")
        print("  stash-by-name <name>  Hide worktree by feature name")
        print("  unstash <path>        Restore stashed worktree")
        print("  unstash-by-name <name> Restore worktree by feature name")
        print("  adopt <branch>        Create worktree from remote branch")
        print("  list-stashed          Show all stashed worktrees")
        sys.exit(1)

    manager = WorktreeManager()
    command = sys.argv[1]

    if command == "stash":
        if len(sys.argv) < 3:
            print("Error: stash requires a worktree path")
            sys.exit(1)
        manager.stash(sys.argv[2])

    elif command == "stash-by-name":
        if len(sys.argv) < 3:
            print("Error: stash-by-name requires a feature name")
            sys.exit(1)
        manager.stash_by_name(sys.argv[2])

    elif command == "unstash":
        if len(sys.argv) < 3:
            print("Error: unstash requires a worktree path")
            sys.exit(1)
        manager.unstash(sys.argv[2])

    elif command == "unstash-by-name":
        if len(sys.argv) < 3:
            print("Error: unstash-by-name requires a feature name")
            sys.exit(1)
        manager.unstash_by_name(sys.argv[2])

    elif command == "adopt":
        if len(sys.argv) < 3:
            print("Error: adopt requires a branch name")
            sys.exit(1)

        branch = sys.argv[2]
        worktree_name = sys.argv[3] if len(sys.argv) > 3 else None
        manager.adopt(branch, worktree_name)

    elif command == "list-stashed":
        manager.list_stashed()

    else:
        print(f"Error: Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
