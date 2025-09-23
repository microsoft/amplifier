"""
Data models for Amplifier CLI v3.

This module defines the core data structures used throughout the CLI,
including manifest entries, resource definitions, and operation records.

Contract:
    - Manifest: Complete manifest structure
    - Resource: Individual resource metadata
    - InstallRecord: Record of an installation operation
    - All models use Pydantic for validation
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic import Field


class Resource(BaseModel):
    """Individual resource metadata.

    Attributes:
        name: Resource name (e.g., "zen-architect")
        type: Resource type (agents, tools, commands, mcp-servers)
        version: Version identifier
        source: Where the resource came from
        installed_at: Installation timestamp
        path: Path where resource is installed
        sha: GitHub SHA hash for version tracking
        ref: Git ref (branch/tag) resource was installed from
        metadata: Additional metadata
    """

    name: str = Field(description="Resource name")
    type: str = Field(description="Resource type (agents, tools, etc)")
    version: str = Field(default="1.0.0", description="Version identifier")
    source: str = Field(default="local", description="Resource source")
    installed_at: datetime = Field(default_factory=datetime.now, description="Installation timestamp")
    path: str | None = Field(default=None, description="Installation path")
    sha: str | None = Field(default=None, description="GitHub SHA hash for version tracking")
    ref: str | None = Field(default=None, description="Git ref (branch/tag) resource was installed from")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Path: lambda v: str(v),
        }


class InstallRecord(BaseModel):
    """Record of an installation operation.

    Attributes:
        resource: Resource that was installed
        operation: Type of operation (install, update, remove)
        timestamp: When the operation occurred
        success: Whether the operation succeeded
        error: Error message if operation failed
    """

    resource: Resource = Field(description="Resource involved in operation")
    operation: str = Field(default="install", description="Operation type")
    timestamp: datetime = Field(default_factory=datetime.now, description="Operation timestamp")
    success: bool = Field(default=True, description="Operation success status")
    error: str | None = Field(default=None, description="Error message if failed")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class ManifestMetadata(BaseModel):
    """Metadata about the manifest itself.

    Attributes:
        created_at: When manifest was created
        updated_at: Last update time
        amplifier_version: Version of amplifier that created this
        project_name: Optional project name
    """

    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    amplifier_version: str = Field(default="3.0.0", description="Amplifier version")
    project_name: str | None = Field(default=None, description="Project name")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class Manifest(BaseModel):
    """Complete manifest structure.

    This is the main data structure saved to .amplifier/manifest.json

    Attributes:
        version: Manifest schema version
        resources: Dictionary of installed resources by type
        metadata: Manifest metadata
        history: List of all operations performed
    """

    version: str = Field(default="1.0.0", description="Manifest schema version")
    resources: dict[str, list[Resource]] = Field(
        default_factory=lambda: {
            "agents": [],
            "tools": [],
            "commands": [],
            "mcp-servers": [],
        },
        description="Installed resources by type",
    )
    metadata: ManifestMetadata = Field(default_factory=ManifestMetadata, description="Manifest metadata")
    history: list[InstallRecord] = Field(default_factory=list, description="Operation history")

    def add_resource(self, resource: Resource) -> None:
        """Add a resource to the manifest.

        Args:
            resource: Resource to add
        """
        if resource.type not in self.resources:
            self.resources[resource.type] = []

        # Remove existing resource with same name if present
        self.resources[resource.type] = [r for r in self.resources[resource.type] if r.name != resource.name]

        # Add the new resource
        self.resources[resource.type].append(resource)

        # Update metadata
        self.metadata.updated_at = datetime.now()

        # Add to history
        record = InstallRecord(resource=resource, operation="install")
        self.history.append(record)

    def get_resource(self, resource_type: str, name: str) -> Resource | None:
        """Get a specific resource by type and name.

        Args:
            resource_type: Type of resource
            name: Resource name

        Returns:
            Resource if found, None otherwise
        """
        if resource_type not in self.resources:
            return None

        for resource in self.resources[resource_type]:
            if resource.name == name:
                return resource

        return None

    def list_resources(self, resource_type: str | None = None) -> list[Resource]:
        """List all resources, optionally filtered by type.

        Args:
            resource_type: Optional type filter

        Returns:
            List of resources
        """
        if resource_type:
            return self.resources.get(resource_type, [])

        all_resources = []
        for resources in self.resources.values():
            all_resources.extend(resources)
        return all_resources

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Path: lambda v: str(v),
        }


class Settings(BaseModel):
    """Claude settings structure for .claude/settings.json.

    Attributes:
        version: Settings version
        defaults: Default configuration values
        mcp_servers: MCP server configurations
    """

    version: str = Field(default="1.0.0", description="Settings version")
    defaults: dict[str, Any] = Field(default_factory=dict, description="Default settings")
    mcp_servers: dict[str, Any] = Field(default_factory=dict, description="MCP server configs")
