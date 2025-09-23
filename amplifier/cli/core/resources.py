"""
Basic resource operations for Amplifier CLI v3.

This module handles resource installation, removal, and discovery.
Supports both local test resources and GitHub fetching.

Contract:
    - install_resource(type, name, content, source_path, sha, ref) → Install a resource
    - remove_resource(type, name) → Remove a resource
    - discover_local_resources() → Find local test resources
    - copy_resource_file(source, target) → Copy resource to target
    - fetch_from_github(type, name, ref) → Fetch resource from GitHub
    - list_github_resources(type, ref) → List resources from GitHub
"""

import os
import shutil
import stat
from pathlib import Path

from amplifier.cli.core.github import GitHubClient
from amplifier.cli.core.manifest import add_resource_to_manifest
from amplifier.cli.core.manifest import remove_resource_from_manifest
from amplifier.cli.core.paths import get_resource_target_dir
from amplifier.cli.models import Resource


def install_resource(
    resource_type: str,
    name: str,
    content: str | None = None,
    source_path: Path | None = None,
    sha: str | None = None,
    ref: str | None = None,
    source: str = "local",
) -> bool:
    """Install a resource to the appropriate .claude/ subdirectory.

    Args:
        resource_type: Type of resource (agents, tools, etc)
        name: Resource name (can include extension)
        content: Optional content to write (if provided)
        source_path: Optional source file to copy (if provided)
        sha: Optional GitHub SHA for version tracking
        ref: Optional Git ref (branch/tag) resource was installed from
        source: Source of the resource (local, github, etc)

    Returns:
        True if installation succeeded

    Raises:
        ValueError: If neither content nor source_path provided

    Example:
        >>> success = install_resource("agents", "test", content="# Test Agent")
    """
    if content is None and source_path is None:
        raise ValueError("Must provide either content or source_path")

    # Get target directory (assertions in get_resource_target_dir ensure it's under .claude/)
    target_dir = get_resource_target_dir(resource_type)
    target_dir.mkdir(parents=True, exist_ok=True)

    # If name already has extension, use it directly; otherwise add default extension
    if "." in name:
        target_file = target_dir / name
    else:
        # Determine file extension based on resource type for backward compatibility
        extension = get_resource_extension(resource_type)
        target_file = target_dir / f"{name}{extension}"

    try:
        if content is not None:
            # Write content directly
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(content)
            # Make tools executable (scripts and Python files need execution permissions)
            if resource_type == "tools":
                current_mode = target_file.stat().st_mode
                new_mode = current_mode | stat.S_IXUSR | stat.S_IRUSR | stat.S_IWUSR
                os.chmod(target_file, new_mode)
        elif source_path and source_path.exists():
            # Copy from source with permission preservation
            shutil.copy2(source_path, target_file)
            # Make tools executable if needed
            if resource_type == "tools":
                current_mode = target_file.stat().st_mode
                new_mode = current_mode | stat.S_IXUSR | stat.S_IRUSR | stat.S_IWUSR
                os.chmod(target_file, new_mode)
        else:
            return False

        # Update manifest
        resource = Resource(
            name=name,
            type=resource_type,
            path=str(target_file),
            source=source,
            sha=sha,
            ref=ref,
        )
        add_resource_to_manifest(resource)

        return True

    except Exception as e:
        print(f"Error installing {resource_type}/{name}: {e}")
        return False


def remove_resource(resource_type: str, name: str) -> bool:
    """Remove an installed resource.

    Args:
        resource_type: Type of resource
        name: Resource name (can include extension)

    Returns:
        True if removal succeeded

    Example:
        >>> success = remove_resource("agents", "test")
    """
    target_dir = get_resource_target_dir(resource_type)

    # If name already has extension, use it directly; otherwise add default extension
    if "." in name:
        target_file = target_dir / name
    else:
        extension = get_resource_extension(resource_type)
        target_file = target_dir / f"{name}{extension}"

    try:
        if target_file.exists():
            target_file.unlink()

        # Update manifest
        remove_resource_from_manifest(resource_type, name)
        return True

    except Exception as e:
        print(f"Error removing {resource_type}/{name}: {e}")
        return False


def get_resource_extension(resource_type: str) -> str:
    """Get the file extension for a resource type.

    Args:
        resource_type: Type of resource

    Returns:
        File extension including dot

    Example:
        >>> ext = get_resource_extension("agents")
        >>> assert ext == ".md"
    """
    extensions = {
        "agents": ".md",
        "tools": ".py",
        "commands": ".md",
        "mcp-servers": ".json",
    }
    return extensions.get(resource_type, ".txt")


def discover_local_resources() -> dict[str, list[Path]]:
    """Discover local test resources for Phase 1.

    Returns:
        Dictionary of resource type to list of file paths

    Example:
        >>> resources = discover_local_resources()
    """
    resources = {}
    test_dir = Path(__file__).parent.parent / "test_resources"

    if not test_dir.exists():
        return resources

    for resource_type in ["agents", "tools", "commands", "mcp-servers"]:
        type_dir = test_dir / resource_type
        if type_dir.exists():
            # Find all files in the directory
            files = list(type_dir.glob("*"))
            if files:
                resources[resource_type] = files

    return resources


def copy_resource_file(source: Path, target: Path) -> bool:
    """Copy a resource file to target location.

    Args:
        source: Source file path
        target: Target file path

    Returns:
        True if copy succeeded

    Example:
        >>> success = copy_resource_file(Path("test.md"), Path(".claude/agents/test.md"))
    """
    try:
        # Ensure target directory exists
        target.parent.mkdir(parents=True, exist_ok=True)

        # Copy file
        shutil.copy2(source, target)
        return True

    except Exception as e:
        print(f"Error copying {source} to {target}: {e}")
        return False


def list_available_resources(resource_type: str | None = None) -> dict[str, list[str]]:
    """List available resources from test_resources directory.

    Args:
        resource_type: Optional filter by type

    Returns:
        Dictionary of type to list of resource names

    Example:
        >>> available = list_available_resources()
    """
    discovered = discover_local_resources()
    available = {}

    for rtype, paths in discovered.items():
        if resource_type and rtype != resource_type:
            continue

        names = []
        for path in paths:
            # Remove extension to get name
            name = path.stem
            names.append(name)

        if names:
            available[rtype] = names

    return available


async def list_available_github_resources(resource_type: str | None = None, ref: str = "main") -> dict[str, list[str]]:
    """List available resources from GitHub.

    Args:
        resource_type: Optional filter by type
        ref: Git ref (branch, tag, or SHA)

    Returns:
        Dictionary of type to list of resource names

    Example:
        >>> available = asyncio.run(list_available_github_resources())
    """

    # Get GitHub token from environment for better rate limits
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    github = GitHubClient(token=token)
    available = {}

    resource_types = ["agents", "tools", "commands", "mcp-servers"]
    if resource_type:
        resource_types = [resource_type] if resource_type in resource_types else []

    for rtype in resource_types:
        names = await github.list_resources(rtype, ref)
        if names:
            available[rtype] = names

    return available


async def fetch_from_github(resource_type: str, name: str, ref: str = "main") -> tuple[str | None, str | None]:
    """Fetch a resource from GitHub.

    Args:
        resource_type: Type of resource
        name: Resource name
        ref: Git ref (branch, tag, or SHA)

    Returns:
        Tuple of (content, sha) or (None, None) if not found

    Example:
        >>> content, sha = asyncio.run(fetch_from_github("agents", "zen-architect"))
    """

    # Get token from environment for better rate limits
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    github = GitHubClient(token=token)
    content, sha, _ = await github.fetch_resource(resource_type, name, ref)
    return content, sha


async def list_github_resources(resource_type: str, ref: str = "main") -> list[str]:
    """List available resources from GitHub.

    Args:
        resource_type: Type of resource
        ref: Git ref (branch, tag, or SHA)

    Returns:
        List of resource names

    Example:
        >>> resources = asyncio.run(list_github_resources("agents"))
    """

    # Get token from environment for better rate limits
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    github = GitHubClient(token=token)
    return await github.list_resources(resource_type, ref)
