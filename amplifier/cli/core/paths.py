"""
Path management module for Amplifier CLI v3.

This is the CRITICAL module that ensures resources ALWAYS go to .claude/,
NEVER to .amplifier/resources/. The .amplifier/ directory is reserved
for metadata only (manifest, state, etc).

Contract:
    - get_claude_dir() → Path to .claude/ in current working directory
    - get_amplifier_dir() → Path to .amplifier/ (metadata only)
    - get_resource_target_dir(resource_type) → ALWAYS under .claude/
    - All paths include assertions to verify correctness
"""

from pathlib import Path


def get_claude_dir() -> Path:
    """Get the .claude directory path in the current working directory.

    Returns:
        Path to .claude/ directory

    Example:
        >>> claude_dir = get_claude_dir()
        >>> assert ".claude" in str(claude_dir)
    """
    return Path.cwd() / ".claude"


def get_amplifier_dir() -> Path:
    """Get the .amplifier directory path for metadata storage.

    Returns:
        Path to .amplifier/ directory (for manifest and metadata only)

    Example:
        >>> amp_dir = get_amplifier_dir()
        >>> assert ".amplifier" in str(amp_dir)
    """
    return Path.cwd() / ".amplifier"


def get_resource_target_dir(resource_type: str) -> Path:
    """Get the target directory for a specific resource type.

    CRITICAL: This ALWAYS returns a path under .claude/, NEVER under .amplifier/

    Args:
        resource_type: Type of resource (agents, tools, commands, mcp-servers)

    Returns:
        Path to resource directory under .claude/

    Raises:
        ValueError: If resource_type is invalid
        AssertionError: If path doesn't contain .claude (safety check)

    Example:
        >>> agents_dir = get_resource_target_dir("agents")
        >>> assert ".claude/agents" in str(agents_dir)
    """
    valid_types = {"agents", "tools", "commands", "mcp-servers"}
    if resource_type not in valid_types:
        raise ValueError(f"Invalid resource type: {resource_type}. Must be one of {valid_types}")

    target_dir = get_claude_dir() / resource_type

    # CRITICAL ASSERTION: Ensure path contains .claude
    assert ".claude" in str(target_dir), f"Resource path {target_dir} does not contain .claude!"
    assert ".amplifier" not in str(target_dir), f"Resource path {target_dir} incorrectly contains .amplifier!"

    return target_dir


def get_manifest_path() -> Path:
    """Get the path to the manifest.json file.

    Returns:
        Path to .amplifier/manifest.json

    Example:
        >>> manifest = get_manifest_path()
        >>> assert str(manifest).endswith("manifest.json")
    """
    return get_amplifier_dir() / "manifest.json"


def get_settings_path() -> Path:
    """Get the path to the Claude settings.json file.

    Returns:
        Path to .claude/settings.json

    Example:
        >>> settings = get_settings_path()
        >>> assert ".claude" in str(settings)
    """
    return get_claude_dir() / "settings.json"


def ensure_directories() -> None:
    """Ensure all required directories exist.

    Creates:
        - .claude/ with subdirectories (agents, tools, commands, mcp-servers)
        - .amplifier/ for metadata
    """
    # Create .claude directory structure
    claude_dir = get_claude_dir()
    claude_dir.mkdir(exist_ok=True)

    # Create resource subdirectories
    for resource_type in ["agents", "tools", "commands", "mcp-servers"]:
        resource_dir = get_resource_target_dir(resource_type)
        resource_dir.mkdir(parents=True, exist_ok=True)

    # Create .amplifier metadata directory
    amplifier_dir = get_amplifier_dir()
    amplifier_dir.mkdir(exist_ok=True)


def validate_paths() -> bool:
    """Validate that paths are configured correctly.

    Returns:
        True if all paths are valid

    Raises:
        AssertionError: If any path validation fails
    """
    # Verify .claude paths
    claude_dir = get_claude_dir()
    assert ".claude" in str(claude_dir)
    assert ".amplifier" not in str(claude_dir)

    # Verify .amplifier paths
    amp_dir = get_amplifier_dir()
    assert ".amplifier" in str(amp_dir)
    assert "resources" not in str(amp_dir)  # Should never have resources subdirectory

    # Verify resource paths ALL go to .claude
    for resource_type in ["agents", "tools", "commands", "mcp-servers"]:
        resource_dir = get_resource_target_dir(resource_type)
        assert ".claude" in str(resource_dir)
        assert ".amplifier" not in str(resource_dir)

    return True
