"""
Manifest operations module for Amplifier CLI v3.

This module handles all operations related to the manifest.json file,
including creation, loading, saving, and updating.

Contract:
    - create_manifest() → Create new manifest
    - load_manifest() → Load existing or create new
    - save_manifest(manifest) → Save manifest to disk
    - add_resource_to_manifest(resource) → Add resource and save
"""

import json

from amplifier.cli.core.paths import get_manifest_path
from amplifier.cli.models import Manifest
from amplifier.cli.models import Resource


def create_manifest() -> Manifest:
    """Create a new manifest with default structure.

    Returns:
        New Manifest instance

    Example:
        >>> manifest = create_manifest()
        >>> assert manifest.version == "1.0.0"
    """
    return Manifest()


def load_manifest() -> Manifest:
    """Load existing manifest or create new one if not found.

    Returns:
        Loaded or new Manifest instance

    Example:
        >>> manifest = load_manifest()
        >>> assert isinstance(manifest, Manifest)
    """
    manifest_path = get_manifest_path()

    if manifest_path.exists():
        try:
            with open(manifest_path, encoding="utf-8") as f:
                data = json.load(f)
                return Manifest(**data)
        except (json.JSONDecodeError, ValueError) as e:
            # If manifest is corrupted, backup and create new
            backup_path = manifest_path.with_suffix(".json.bak")
            manifest_path.rename(backup_path)
            print(f"Warning: Corrupted manifest backed up to {backup_path}")
            print(f"Error was: {e}")

    # Create new manifest if not found or corrupted
    return create_manifest()


def save_manifest(manifest: Manifest) -> None:
    """Save manifest to disk.

    Args:
        manifest: Manifest to save

    Example:
        >>> manifest = create_manifest()
        >>> save_manifest(manifest)
    """
    manifest_path = get_manifest_path()

    # Ensure directory exists
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to dict and save
    data = manifest.model_dump(mode="json")

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def add_resource_to_manifest(resource: Resource) -> None:
    """Add a resource to the manifest and save.

    This is a convenience function that loads, updates, and saves.

    Args:
        resource: Resource to add

    Example:
        >>> resource = Resource(name="test", type="agents")
        >>> add_resource_to_manifest(resource)
    """
    manifest = load_manifest()
    manifest.add_resource(resource)
    save_manifest(manifest)


def remove_resource_from_manifest(resource_type: str, name: str) -> bool:
    """Remove a resource from the manifest.

    Args:
        resource_type: Type of resource
        name: Resource name

    Returns:
        True if resource was removed, False if not found

    Example:
        >>> removed = remove_resource_from_manifest("agents", "test")
    """
    manifest = load_manifest()

    if resource_type not in manifest.resources:
        return False

    original_count = len(manifest.resources[resource_type])
    manifest.resources[resource_type] = [r for r in manifest.resources[resource_type] if r.name != name]

    if len(manifest.resources[resource_type]) < original_count:
        save_manifest(manifest)
        return True

    return False


def get_installed_resource(resource_type: str, name: str) -> Resource | None:
    """Get an installed resource from the manifest.

    Args:
        resource_type: Type of resource
        name: Resource name

    Returns:
        Resource if found, None otherwise

    Example:
        >>> resource = get_installed_resource("agents", "zen-architect")
    """
    manifest = load_manifest()
    return manifest.get_resource(resource_type, name)


def list_installed_resources(resource_type: str | None = None) -> list[Resource]:
    """List installed resources from the manifest.

    Args:
        resource_type: Optional type filter

    Returns:
        List of installed resources

    Example:
        >>> agents = list_installed_resources("agents")
    """
    manifest = load_manifest()
    return manifest.list_resources(resource_type)


def is_resource_installed(resource_type: str, name: str) -> bool:
    """Check if a resource is installed.

    Args:
        resource_type: Type of resource
        name: Resource name

    Returns:
        True if installed, False otherwise

    Example:
        >>> installed = is_resource_installed("agents", "zen-architect")
    """
    return get_installed_resource(resource_type, name) is not None


def get_resource_version(resource_type: str, name: str) -> str | None:
    """Get the SHA version of an installed resource.

    Args:
        resource_type: Type of resource
        name: Resource name

    Returns:
        SHA hash if available, None otherwise

    Example:
        >>> sha = get_resource_version("agents", "zen-architect")
    """
    resource = get_installed_resource(resource_type, name)
    return resource.sha if resource else None


def needs_update(resource_type: str, name: str, github_sha: str) -> bool:
    """Check if a resource needs update by comparing SHA hashes.

    Args:
        resource_type: Type of resource
        name: Resource name
        github_sha: SHA from GitHub

    Returns:
        True if resource needs update, False otherwise

    Example:
        >>> needs_update = needs_update("agents", "zen-architect", "abc123...")
    """
    current_sha = get_resource_version(resource_type, name)
    if current_sha is None:
        # Resource not installed or no SHA tracked
        return True
    return current_sha != github_sha


def update_resource_sha(resource_type: str, name: str, sha: str, ref: str | None = None) -> bool:
    """Update the SHA hash for an installed resource.

    Args:
        resource_type: Type of resource
        name: Resource name
        sha: New SHA hash
        ref: Optional Git ref

    Returns:
        True if update succeeded, False if resource not found

    Example:
        >>> success = update_resource_sha("agents", "zen-architect", "abc123...", "main")
    """
    manifest = load_manifest()
    resource = manifest.get_resource(resource_type, name)

    if resource is None:
        return False

    # Update the resource's SHA and ref
    resource.sha = sha
    if ref:
        resource.ref = ref

    # Save the manifest
    save_manifest(manifest)
    return True
