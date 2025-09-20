"""
Worktree command for Amplifier CLI v3.

This command manages git worktrees for parallel development branches.
When creating a worktree, it also copies the .data/ directory to preserve local state.

Contract:
    - Creates worktrees in ../.amplifier-worktrees/<name>/
    - Copies .data/ directory when creating worktree
    - Three sub-commands: create, list, remove
    - Uses GitPython for all git operations
"""

import shutil
from pathlib import Path

import click
from git import Repo
from git.exc import GitCommandError

from amplifier.cli.core.decorators import handle_errors
from amplifier.cli.core.decorators import log_command
from amplifier.cli.core.errors import ConfigurationError
from amplifier.cli.core.output import get_output_manager


def get_repo() -> Repo:
    """Get the current git repository.

    Returns:
        Repo: The current git repository

    Raises:
        ConfigurationError: If not in a git repository
    """
    try:
        return Repo(search_parent_directories=True)
    except Exception:
        raise ConfigurationError("Not in a git repository")


def get_worktrees_dir() -> Path:
    """Get the directory where worktrees are stored.

    Returns:
        Path: The worktrees directory path (../.amplifier-worktrees/)
    """
    repo = get_repo()
    repo_path = Path(repo.working_dir)
    return repo_path.parent / ".amplifier-worktrees"


def copy_data_directory(source_repo_path: Path, worktree_path: Path) -> None:
    """Copy .data/ directory from source to worktree.

    Args:
        source_repo_path: Path to the source repository
        worktree_path: Path to the worktree
    """
    source_data = source_repo_path / ".data"
    target_data = worktree_path / ".data"

    if source_data.exists() and source_data.is_dir():
        # Remove target if it exists
        if target_data.exists():
            shutil.rmtree(target_data)
        # Copy the entire directory tree
        shutil.copytree(source_data, target_data)


@click.group()
def cmd() -> None:
    """Manage git worktrees for parallel development."""
    pass


@cmd.command("create")
@click.argument("name")
@click.option("--branch", "-b", help="Branch name (defaults to worktree name)")
@click.option("--no-copy-data", is_flag=True, help="Skip copying .data/ directory")
@handle_errors()
@log_command("worktree.create")
@click.pass_context
def create(ctx: click.Context, name: str, branch: str | None, no_copy_data: bool) -> None:
    """Create a new worktree.

    Creates a worktree in ../.amplifier-worktrees/<name>/ and optionally
    copies the .data/ directory from the current repository.

    Examples:
        amplifier worktree create feature-x
        amplifier worktree create test --branch experiment/test
        amplifier worktree create quick-fix --no-copy-data
    """
    output = ctx.obj.get("output", get_output_manager())

    # Get repository and validate
    repo = get_repo()
    repo_path = Path(repo.working_dir)

    # Check if repository has any commits
    has_commits = True
    try:
        _ = repo.head.commit  # This will fail if no commits
    except (ValueError, TypeError) as e:
        has_commits = False
        output.debug(f"No commits detected: {type(e).__name__}: {e}")
    except Exception as e:
        has_commits = False
        output.debug(f"Unexpected exception checking for commits: {type(e).__name__}: {e}")

    if not has_commits:
        # Repository has no commits yet
        output.warning("Repository has no commits yet. Creating initial commit...")

        try:
            # Create initial commit with --allow-empty flag
            repo.git.commit("--allow-empty", "-m", "Initial commit for worktree support")
            output.success("Created initial commit")
        except Exception as e:
            output.error(f"Failed to create initial commit: {e}")
            raise

    # Determine branch name (use name if not specified)
    branch_name = branch or name

    # Get worktrees directory and create if needed
    worktrees_dir = get_worktrees_dir()
    worktrees_dir.mkdir(parents=True, exist_ok=True)

    # Calculate worktree path
    worktree_path = worktrees_dir / name

    # Check if worktree already exists
    if worktree_path.exists():
        raise ConfigurationError(f"Worktree '{name}' already exists at {worktree_path}")

    # Check if branch already exists
    existing_branches = [ref.name for ref in repo.refs]
    create_new_branch = branch_name not in existing_branches

    output.info(f"Creating worktree '{name}'...")

    try:
        if create_new_branch:
            # Create worktree with new branch
            output.debug(f"Creating new branch '{branch_name}'")
            repo.git.worktree("add", "-b", branch_name, str(worktree_path))
            output.success(f"Created worktree with new branch '{branch_name}'")
        else:
            # Create worktree with existing branch
            output.debug(f"Using existing branch '{branch_name}'")
            repo.git.worktree("add", str(worktree_path), branch_name)
            output.success(f"Created worktree with existing branch '{branch_name}'")

        # Copy .data/ directory unless skipped
        if not no_copy_data:
            output.info("Copying .data/ directory...")
            copy_data_directory(repo_path, worktree_path)
            output.success("Copied .data/ directory")

        output.success(f"✓ Worktree created at: {worktree_path}")
        output.info(f"To enter worktree: cd {worktree_path}")

    except GitCommandError as e:
        raise ConfigurationError(f"Failed to create worktree: {e}")


@cmd.command("list")
@handle_errors()
@log_command("worktree.list")
@click.pass_context
def list_worktrees(ctx: click.Context) -> None:
    """List all worktrees.

    Shows all worktrees with their paths and current branches.
    """
    output = ctx.obj.get("output", get_output_manager())

    # Get repository
    repo = get_repo()

    try:
        # Get worktree list from git
        worktree_output = repo.git.worktree("list", "--porcelain")

        if not worktree_output:
            output.info("No worktrees found")
            return

        # Parse worktree output
        worktrees = []
        current_worktree = {}

        for line in worktree_output.strip().split("\n"):
            if not line:
                if current_worktree:
                    worktrees.append(current_worktree)
                    current_worktree = {}
                continue

            if line.startswith("worktree "):
                current_worktree["path"] = line[9:]
            elif line.startswith("HEAD "):
                current_worktree["head"] = line[5:]
            elif line.startswith("branch "):
                current_worktree["branch"] = line[7:]
            elif line == "bare":
                current_worktree["bare"] = True
            elif line == "detached":
                current_worktree["detached"] = True
            elif line.startswith("locked"):
                if " " in line:
                    current_worktree["locked"] = line.split(" ", 1)[1]
                else:
                    current_worktree["locked"] = True
            elif line.startswith("prunable"):
                if " " in line:
                    current_worktree["prunable"] = line.split(" ", 1)[1]
                else:
                    current_worktree["prunable"] = True

        # Add last worktree if exists
        if current_worktree:
            worktrees.append(current_worktree)

        # Display worktrees
        output.info(f"Found {len(worktrees)} worktree(s):\n")

        for wt in worktrees:
            path = Path(wt["path"])

            # Determine if this is the main worktree
            is_main = path == Path(repo.working_dir)

            # Build status indicators
            status = []
            if is_main:
                status.append("main")
            if wt.get("detached"):
                status.append("detached")
            if wt.get("locked"):
                status.append("locked")
            if wt.get("prunable"):
                status.append("prunable")

            status_str = f" [{', '.join(status)}]" if status else ""

            # Get branch or HEAD info
            branch_info = wt.get("branch", wt.get("head", "unknown")[:8])

            # Format output
            if is_main:
                output.info(f"  * {path.name}/ → {branch_info}{status_str}")
            else:
                # Check if it's in our worktrees directory
                worktrees_dir = get_worktrees_dir()
                if path.parent == worktrees_dir:
                    output.info(f"    {path.name}/ → {branch_info}{status_str}")
                else:
                    output.info(f"    {path}/ → {branch_info}{status_str}")

    except GitCommandError as e:
        raise ConfigurationError(f"Failed to list worktrees: {e}")


@cmd.command("remove")
@click.argument("name")
@click.option("--force", "-f", is_flag=True, help="Force removal even if worktree has changes")
@handle_errors()
@log_command("worktree.remove")
@click.pass_context
def remove(ctx: click.Context, name: str, force: bool) -> None:
    """Remove a worktree.

    Removes the worktree and optionally forces removal even if there are
    uncommitted changes.

    Examples:
        amplifier worktree remove feature-x
        amplifier worktree remove test --force
    """
    output = ctx.obj.get("output", get_output_manager())

    # Get repository
    repo = get_repo()

    # Calculate worktree path
    worktrees_dir = get_worktrees_dir()
    worktree_path = worktrees_dir / name

    # Check if worktree exists
    if not worktree_path.exists():
        # Try to find by path in git worktree list
        try:
            worktree_output = repo.git.worktree("list", "--porcelain")
            found = False

            for line in worktree_output.strip().split("\n"):
                if line.startswith("worktree ") and name in line:
                    worktree_path = Path(line[9:])
                    if worktree_path.name == name:
                        found = True
                        break

            if not found:
                raise ConfigurationError(f"Worktree '{name}' not found")
        except GitCommandError:
            raise ConfigurationError(f"Worktree '{name}' not found")

    output.info(f"Removing worktree '{name}'...")

    try:
        if force:
            repo.git.worktree("remove", str(worktree_path), "--force")
            output.warning(f"Force removed worktree at: {worktree_path}")
        else:
            repo.git.worktree("remove", str(worktree_path))
            output.success(f"Removed worktree at: {worktree_path}")

        # Clean up directory if it still exists
        if worktree_path.exists():
            shutil.rmtree(worktree_path)
            output.debug(f"Cleaned up worktree directory: {worktree_path}")

        output.success(f"✓ Worktree '{name}' removed")

    except GitCommandError as e:
        if "contains modified or untracked files" in str(e):
            output.error(
                "Worktree contains uncommitted changes.\nUse --force to remove anyway, or commit/stash changes first."
            )
        else:
            raise ConfigurationError(f"Failed to remove worktree: {e}")
