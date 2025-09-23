"""Core utilities for Amplifier CLI v3."""

from amplifier.cli.core.manifest import add_resource_to_manifest
from amplifier.cli.core.manifest import create_manifest
from amplifier.cli.core.manifest import get_installed_resource
from amplifier.cli.core.manifest import get_resource_version
from amplifier.cli.core.manifest import is_resource_installed
from amplifier.cli.core.manifest import list_installed_resources
from amplifier.cli.core.manifest import load_manifest
from amplifier.cli.core.manifest import needs_update
from amplifier.cli.core.manifest import remove_resource_from_manifest
from amplifier.cli.core.manifest import save_manifest
from amplifier.cli.core.manifest import update_resource_sha
from amplifier.cli.core.network import NetworkError
from amplifier.cli.core.network import check_connectivity
from amplifier.cli.core.network import download_to_file
from amplifier.cli.core.network import fetch_with_retry
from amplifier.cli.core.paths import ensure_directories
from amplifier.cli.core.paths import get_amplifier_dir
from amplifier.cli.core.paths import get_claude_dir
from amplifier.cli.core.paths import get_manifest_path
from amplifier.cli.core.paths import get_resource_target_dir
from amplifier.cli.core.paths import get_settings_path
from amplifier.cli.core.paths import validate_paths
from amplifier.cli.core.resources import copy_resource_file
from amplifier.cli.core.resources import discover_local_resources
from amplifier.cli.core.resources import fetch_from_github
from amplifier.cli.core.resources import get_resource_extension
from amplifier.cli.core.resources import install_resource
from amplifier.cli.core.resources import list_available_resources
from amplifier.cli.core.resources import list_github_resources
from amplifier.cli.core.resources import remove_resource

__all__ = [
    # Manifest operations
    "create_manifest",
    "load_manifest",
    "save_manifest",
    "add_resource_to_manifest",
    "remove_resource_from_manifest",
    "get_installed_resource",
    "get_resource_version",
    "list_installed_resources",
    "is_resource_installed",
    "needs_update",
    "update_resource_sha",
    # Network operations
    "NetworkError",
    "fetch_with_retry",
    "download_to_file",
    "check_connectivity",
    # Path operations
    "get_claude_dir",
    "get_amplifier_dir",
    "get_resource_target_dir",
    "get_manifest_path",
    "get_settings_path",
    "ensure_directories",
    "validate_paths",
    # Resource operations
    "install_resource",
    "remove_resource",
    "get_resource_extension",
    "discover_local_resources",
    "copy_resource_file",
    "list_available_resources",
    "fetch_from_github",
    "list_github_resources",
]
