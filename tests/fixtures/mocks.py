"""Mock utilities for testing."""

from typing import Any
from unittest.mock import MagicMock


class MockGitHubClient:
    """Mock GitHub client for testing."""

    def __init__(self, resources: dict[str, dict[str, str]] | None = None):
        """Initialize mock client with test resources.

        Args:
            resources: Dict mapping resource_type -> name -> content
        """
        self.resources = resources or {}
        self.call_count = 0
        self.last_call = None
        self.error_on_next_call = None

    async def fetch_resource(self, resource_type: str, name: str, ref: str = "main") -> tuple[str | None, str | None]:
        """Mock fetch_resource method."""
        self.call_count += 1
        self.last_call = (resource_type, name, ref)

        # Simulate error if configured
        if self.error_on_next_call:
            error = self.error_on_next_call
            self.error_on_next_call = None
            raise error

        # Return resource if available
        if resource_type in self.resources and name in self.resources[resource_type]:
            content = self.resources[resource_type][name]
            sha = f"sha_{name}_{self.call_count}"
            return content, sha

        return None, None

    async def list_resources(self, resource_type: str, ref: str = "main") -> list[str]:
        """Mock list_resources method."""
        if resource_type in self.resources:
            return list(self.resources[resource_type].keys())
        return []

    async def get_latest_release(self) -> str | None:
        """Mock get_latest_release method."""
        return "v3.0.0"

    def simulate_network_error(self):
        """Configure to raise network error on next call."""
        self.error_on_next_call = Exception("Network error")

    def simulate_timeout(self):
        """Configure to raise timeout on next call."""
        self.error_on_next_call = TimeoutError("Request timed out")


class MockFileSystem:
    """Mock file system operations for testing."""

    def __init__(self):
        """Initialize mock filesystem."""
        self.files: dict[str, str] = {}
        self.directories: set[str] = set()
        self.permissions: dict[str, str] = {}  # path -> "read" | "write" | "deny"

    def mkdir(self, path: str | Any, parents: bool = False, exist_ok: bool = False) -> None:
        """Mock directory creation."""
        path = str(path)

        # Check permissions
        if path in self.permissions and self.permissions[path] == "deny":
            raise PermissionError(f"Cannot create directory: {path}")

        # Check if already exists
        if path in self.directories and not exist_ok:
            raise FileExistsError(f"{path} already exists")

        self.directories.add(path)

        # Create parent directories if requested
        if parents:
            parts = path.split("/")
            for i in range(1, len(parts)):
                parent = "/".join(parts[:i])
                if parent:
                    self.directories.add(parent)

    def write_text(self, path: str | Any, content: str) -> None:
        """Mock file write."""
        path = str(path)

        # Check permissions
        if path in self.permissions and self.permissions[path] != "write":
            raise PermissionError(f"Cannot write to: {path}")

        self.files[path] = content

        # Ensure parent directory exists in mock
        parent = "/".join(path.split("/")[:-1])
        if parent:
            self.directories.add(parent)

    def read_text(self, path: str | Any) -> str:
        """Mock file read."""
        path = str(path)

        # Check permissions
        if path in self.permissions and self.permissions[path] == "deny":
            raise PermissionError(f"Cannot read: {path}")

        if path not in self.files:
            raise FileNotFoundError(f"{path} not found")

        return self.files[path]

    def exists(self, path: str | Any) -> bool:
        """Check if path exists."""
        path = str(path)
        return path in self.files or path in self.directories

    def is_dir(self, path: str | Any) -> bool:
        """Check if path is a directory."""
        return str(path) in self.directories

    def is_file(self, path: str | Any) -> bool:
        """Check if path is a file."""
        return str(path) in self.files

    def set_permission(self, path: str, permission: str) -> None:
        """Set permission for a path."""
        self.permissions[str(path)] = permission

    def list_dir(self, path: str | Any) -> list[str]:
        """List directory contents."""
        path = str(path)
        if path not in self.directories:
            raise NotADirectoryError(f"{path} is not a directory")

        # Find all items in this directory
        items = []
        path_with_slash = path + "/" if not path.endswith("/") else path

        for file_path in self.files:
            if file_path.startswith(path_with_slash):
                # Get just the filename, not full path
                relative = file_path[len(path_with_slash) :]
                if "/" not in relative:  # Direct child only
                    items.append(relative)

        for dir_path in self.directories:
            if dir_path.startswith(path_with_slash) and dir_path != path:
                relative = dir_path[len(path_with_slash) :]
                if "/" not in relative:  # Direct child only
                    items.append(relative)

        return sorted(items)


class MockOutputManager:
    """Mock output manager for testing."""

    def __init__(self, capture: bool = True):
        """Initialize mock output manager."""
        self.messages: list[tuple[str, str]] = []  # (method, message) pairs
        self.capture = capture

    def info(self, message: str, detail: str | None = None) -> None:
        """Mock info output."""
        if self.capture:
            self.messages.append(("info", message))
            if detail:
                self.messages.append(("info_detail", detail))

    def success(self, message: str, detail: str | None = None) -> None:
        """Mock success output."""
        if self.capture:
            self.messages.append(("success", message))
            if detail:
                self.messages.append(("success_detail", detail))

    def warning(self, message: str, detail: str | None = None) -> None:
        """Mock warning output."""
        if self.capture:
            self.messages.append(("warning", message))
            if detail:
                self.messages.append(("warning_detail", detail))

    def error(self, message: str, detail: str | None = None) -> None:
        """Mock error output."""
        if self.capture:
            self.messages.append(("error", message))
            if detail:
                self.messages.append(("error_detail", detail))

    def debug(self, message: str) -> None:
        """Mock debug output."""
        if self.capture:
            self.messages.append(("debug", message))

    def section_header(self, title: str) -> None:
        """Mock section header."""
        if self.capture:
            self.messages.append(("section", title))

    def spinner(self, message: str):
        """Mock spinner context manager."""
        return MagicMock(__enter__=lambda self: None, __exit__=lambda self, *args: None)

    def get_messages_by_type(self, msg_type: str) -> list[str]:
        """Get all messages of a specific type."""
        return [msg for method, msg in self.messages if method == msg_type]


class MockManifest:
    """Mock manifest for testing."""

    def __init__(self, resources: list[dict[str, Any]] | None = None):
        """Initialize mock manifest."""
        self.metadata = {
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "amplifier_version": "3.0.0",
        }
        self.resources = resources or []
        self.save_count = 0
        self.last_save_path = None

    def save(self, path: str | Any) -> None:
        """Mock save method."""
        self.save_count += 1
        self.last_save_path = str(path)

    def add_resource(self, resource: dict[str, Any]) -> None:
        """Add a resource to manifest."""
        self.resources.append(resource)

    def remove_resource(self, name: str, resource_type: str) -> bool:
        """Remove a resource from manifest."""
        original_count = len(self.resources)
        self.resources = [r for r in self.resources if not (r["name"] == name and r["type"] == resource_type)]
        return len(self.resources) < original_count

    def find_resource(self, name: str, resource_type: str) -> dict[str, Any] | None:
        """Find a resource in manifest."""
        for resource in self.resources:
            if resource["name"] == name and resource["type"] == resource_type:
                return resource
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {"metadata": self.metadata, "resources": self.resources}
