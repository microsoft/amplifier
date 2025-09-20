"""
GitHub API client for Amplifier CLI v3.

This module handles all interactions with the GitHub API to fetch
resources from the microsoft/amplifier repository.

Contract:
    - fetch_resource(type, name, ref) → Fetch resource content and SHA
    - list_resources(type, ref) → List available resources of a type
    - get_latest_release() → Get latest release tag
    - fetch_resource_metadata(type, name, ref) → Get resource metadata
"""

import base64
from datetime import UTC
from typing import Any

import httpx
from rich.console import Console

from amplifier.cli.core.network import MaxRetriesExceededError
from amplifier.cli.core.network import NetworkConfig
from amplifier.cli.core.network import NetworkError
from amplifier.cli.core.network import calculate_hash
from amplifier.cli.core.network import download_with_retry


class GitHubClient:
    """Client for fetching resources from GitHub repository."""

    BASE_URL = "https://api.github.com/repos/microsoft/amplifier"
    RAW_BASE_URL = "https://raw.githubusercontent.com/microsoft/amplifier"
    TIMEOUT = 30.0  # seconds

    def __init__(self, token: str | None = None, network_config: NetworkConfig | None = None):
        """Initialize GitHub client.

        Args:
            token: Optional GitHub token for higher rate limits
            network_config: Optional network configuration for retry logic
        """
        import os

        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "amplifier-cli-v3",
        }

        # Try to get token from various sources
        if not token:
            token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")

        if token:
            self.headers["Authorization"] = f"Bearer {token}"
            self.authenticated = True
        else:
            self.authenticated = False

        self.network_config = network_config or NetworkConfig()
        self.console = Console()

    async def fetch_resource_raw(
        self, resource_type: str, name: str, ref: str = "main", extensions_to_try: list[str] | None = None
    ) -> tuple[str | None, str | None]:
        """Fetch resource content from raw.githubusercontent.com (no authentication needed).

        Args:
            resource_type: Type of resource (agents, tools, etc)
            name: Resource name (with or without extension)
            ref: Git ref (branch, tag, or SHA)
            extensions_to_try: List of extensions to try if name doesn't have one

        Returns:
            Tuple of (content, content_sha256) or (None, None) if not found
        """
        import asyncio

        # If name already has an extension, use it directly
        if "." in name:
            path = f".claude/{resource_type}/{name}"
            raw_url = f"{self.RAW_BASE_URL}/{ref}/{path}"

            for attempt in range(self.network_config.max_retries + 1):
                try:
                    # Use simple httpx client without auth headers for raw URLs
                    async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                        response = await client.get(raw_url)

                        if response.status_code == 200:
                            content = response.text
                            content_sha256 = calculate_hash(response.content)
                            return content, content_sha256

                        if response.status_code == 404:
                            return None, None

                        # Server error - retry
                        if response.status_code >= 500 and attempt < self.network_config.max_retries:
                            delay = self._calculate_backoff(attempt)
                            await asyncio.sleep(delay)
                            continue

                        # Other errors
                        return None, None

                except httpx.TimeoutException:
                    if attempt < self.network_config.max_retries:
                        delay = self._calculate_backoff(attempt)
                        await asyncio.sleep(delay)
                        continue
                    return None, None

                except Exception:
                    return None, None

            return None, None

        # If no extension, try common ones based on resource type
        if extensions_to_try is None:
            extensions_map = {
                "agents": ["md"],
                "tools": ["py", "sh", "js", "ts", "rb"],
                "commands": ["md"],
                "mcp-servers": ["json"],
            }
            extensions_to_try = extensions_map.get(resource_type, ["md", "json", "yaml", "yml", "txt"])

        # Try each possible extension
        for extension in extensions_to_try:
            path = f".claude/{resource_type}/{name}.{extension}"
            raw_url = f"{self.RAW_BASE_URL}/{ref}/{path}"

            for attempt in range(self.network_config.max_retries + 1):
                try:
                    # Use simple httpx client without auth headers for raw URLs
                    async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                        response = await client.get(raw_url)

                        if response.status_code == 200:
                            content = response.text
                            content_sha256 = calculate_hash(response.content)
                            return content, content_sha256

                        if response.status_code == 404:
                            # Try next extension
                            break

                        # Server error - retry
                        if response.status_code >= 500 and attempt < self.network_config.max_retries:
                            delay = self._calculate_backoff(attempt)
                            await asyncio.sleep(delay)
                            continue

                        # Other errors - try next extension
                        break

                except httpx.TimeoutException:
                    if attempt < self.network_config.max_retries:
                        delay = self._calculate_backoff(attempt)
                        await asyncio.sleep(delay)
                        continue
                    # Max retries exceeded for this extension, try next
                    break

                except Exception:
                    # Try next extension
                    break

        # Tried all extensions without success
        return None, None

    async def fetch_resource(
        self, resource_type: str, name: str, ref: str = "main", show_progress: bool = True
    ) -> tuple[str | None, str | None, str | None]:
        """Fetch single resource content from GitHub with retry logic.

        Tries raw.githubusercontent.com first to avoid rate limits, then falls back
        to GitHub API if SHA is needed.

        Args:
            resource_type: Type of resource (agents, tools, etc)
            name: Resource name (with or without extension)
            ref: Git ref (branch, tag, or SHA)
            show_progress: Whether to show download progress

        Returns:
            Tuple of (content, github_sha, content_sha256) or (None, None, None) if not found
        """
        # First, try fetching from raw.githubusercontent.com (no rate limits)
        content, content_sha256 = await self.fetch_resource_raw(resource_type, name, ref)

        if content is not None:
            # Successfully fetched from raw URL
            # GitHub SHA is not available from raw URLs, so we return None for it
            # This is acceptable as most operations only need the content and content_sha256
            return content, None, content_sha256

        # Fall back to GitHub API if raw fetch failed (e.g., for private repos or if SHA is needed)
        # Note: This path uses authentication and is subject to rate limits
        # If name already has an extension, use it directly
        if "." in name:
            path = f".claude/{resource_type}/{name}"

            # Try fetching directly with the provided filename
            for attempt in range(self.network_config.max_retries + 1):
                try:
                    async with httpx.AsyncClient(headers=self.headers, timeout=self.TIMEOUT) as client:
                        url = f"{self.BASE_URL}/contents/{path}"
                        params = {"ref": ref}
                        response = await client.get(url, params=params)

                        # Check rate limiting
                        if response.status_code == 429:
                            await self._handle_rate_limit(dict(response.headers), attempt)
                            continue

                        if response.status_code == 200:
                            data = response.json()
                            # GitHub API returns base64 encoded content
                            content_bytes = base64.b64decode(data["content"])
                            content = content_bytes.decode("utf-8")
                            content_sha256 = calculate_hash(content_bytes)

                            # Report rate limit status
                            self._report_rate_limit(dict(response.headers))

                            return content, data["sha"], content_sha256

                        if response.status_code == 404:
                            return None, None, None

                        # Server error - retry
                        if response.status_code >= 500 and attempt < self.network_config.max_retries:
                            delay = self._calculate_backoff(attempt)
                            self.console.print(
                                f"[yellow]Server error {response.status_code}, retrying in {delay:.1f}s...[/yellow]"
                            )
                            import asyncio

                            await asyncio.sleep(delay)
                            continue

                        # Other errors
                        self.console.print(f"[red]GitHub API error: {response.status_code} - {response.text}[/red]")
                        return None, None, None

                except httpx.TimeoutException:
                    if attempt < self.network_config.max_retries:
                        delay = self._calculate_backoff(attempt)
                        self.console.print(
                            f"[yellow]Timeout fetching {resource_type}/{name}, retrying in {delay:.1f}s...[/yellow]"
                        )
                        import asyncio

                        await asyncio.sleep(delay)
                        continue
                    self.console.print(
                        f"[red]Timeout fetching {resource_type}/{name} after {attempt + 1} attempts[/red]"
                    )
                    return None, None, None

                except Exception as e:
                    self.console.print(f"[red]Error fetching {resource_type}/{name}: {e}[/red]")
                    return None, None, None

            return None, None, None

        # Otherwise, try different extensions for backward compatibility
        # Map resource types to file extensions
        # For tools, we'll try multiple extensions
        extensions_map = {
            "agents": ["md"],
            "tools": ["py", "sh", "js", "ts", "rb"],  # Try multiple extensions for tools
            "commands": ["md"],
            "mcp-servers": ["json"],
        }

        extensions_to_try = extensions_map.get(resource_type, ["txt"])

        # Try each possible extension
        for extension in extensions_to_try:
            path = f".claude/{resource_type}/{name}.{extension}"

            # Try API endpoint first (has SHA and metadata)
            for attempt in range(self.network_config.max_retries + 1):
                try:
                    async with httpx.AsyncClient(headers=self.headers, timeout=self.TIMEOUT) as client:
                        url = f"{self.BASE_URL}/contents/{path}"
                        params = {"ref": ref}
                        response = await client.get(url, params=params)

                        # Check rate limiting
                        if response.status_code == 429:
                            await self._handle_rate_limit(dict(response.headers), attempt)
                            continue

                        if response.status_code == 200:
                            data = response.json()
                            # GitHub API returns base64 encoded content
                            content_bytes = base64.b64decode(data["content"])
                            content = content_bytes.decode("utf-8")
                            content_sha256 = calculate_hash(content_bytes)

                            # Report rate limit status
                            self._report_rate_limit(dict(response.headers))

                            return content, data["sha"], content_sha256

                        if response.status_code == 404:
                            # For tools, try the next extension
                            if resource_type == "tools" and extension != extensions_to_try[-1]:
                                break  # Try next extension
                            # For non-tools or last extension, return None
                            if extension == extensions_to_try[-1]:
                                return None, None, None
                            break  # Try next extension

                        # Server error - retry
                        if response.status_code >= 500 and attempt < self.network_config.max_retries:
                            delay = self._calculate_backoff(attempt)
                            self.console.print(
                                f"[yellow]Server error {response.status_code}, retrying in {delay:.1f}s...[/yellow]"
                            )
                            import asyncio

                            await asyncio.sleep(delay)
                            continue

                        # Other errors
                        self.console.print(f"[red]GitHub API error: {response.status_code} - {response.text}[/red]")
                        if extension == extensions_to_try[-1]:
                            return None, None, None
                        break  # Try next extension

                except httpx.TimeoutException:
                    if attempt < self.network_config.max_retries:
                        delay = self._calculate_backoff(attempt)
                        self.console.print(
                            f"[yellow]Timeout fetching {resource_type}/{name}, retrying in {delay:.1f}s...[/yellow]"
                        )
                        import asyncio

                        await asyncio.sleep(delay)
                        continue
                    # Max retries exceeded for this extension
                    if extension == extensions_to_try[-1]:
                        self.console.print(
                            f"[red]Timeout fetching {resource_type}/{name} after {attempt + 1} attempts[/red]"
                        )
                        return None, None, None
                    break  # Try next extension

                except Exception as e:
                    if extension == extensions_to_try[-1]:
                        self.console.print(f"[red]Error fetching {resource_type}/{name}: {e}[/red]")
                        return None, None, None
                    break  # Try next extension

        # Tried all extensions without success
        return None, None, None

    async def list_resources(self, resource_type: str, ref: str = "main") -> list[str]:
        """List available resources of a type from GitHub.

        Args:
            resource_type: Type of resource to list
            ref: Git ref (branch, tag, or SHA)

        Returns:
            List of resource names with full filenames (including extensions)
        """
        path = f".claude/{resource_type}"

        for attempt in range(self.network_config.max_retries + 1):
            try:
                async with httpx.AsyncClient(headers=self.headers, timeout=self.TIMEOUT) as client:
                    url = f"{self.BASE_URL}/contents/{path}"
                    params = {"ref": ref}
                    response = await client.get(url, params=params)

                    # Check rate limiting
                    if response.status_code == 429:
                        await self._handle_rate_limit(dict(response.headers), attempt)
                        continue

                    if response.status_code == 200:
                        data = response.json()
                        resources = []

                        for item in data:
                            if item["type"] == "file":
                                # Return full filename including extension
                                resources.append(item["name"])

                        # Report rate limit status
                        self._report_rate_limit(dict(response.headers))
                        return resources

                    if response.status_code == 404:
                        return []

                    # Server error - retry
                    if response.status_code >= 500 and attempt < self.network_config.max_retries:
                        delay = self._calculate_backoff(attempt)
                        self.console.print(
                            f"[yellow]Server error {response.status_code}, retrying in {delay:.1f}s...[/yellow]"
                        )
                        import asyncio

                        await asyncio.sleep(delay)
                        continue

                    self.console.print(f"[red]GitHub API error: {response.status_code} - {response.text}[/red]")
                    return []

            except httpx.TimeoutException:
                if attempt < self.network_config.max_retries:
                    delay = self._calculate_backoff(attempt)
                    self.console.print(f"[yellow]Timeout listing {resource_type}, retrying in {delay:.1f}s...[/yellow]")
                    import asyncio

                    await asyncio.sleep(delay)
                    continue
                self.console.print(f"[red]Timeout listing {resource_type} after {attempt + 1} attempts[/red]")
                return []

            except Exception as e:
                self.console.print(f"[red]Error listing {resource_type}: {e}[/red]")
                return []

        return []

    async def get_latest_release(self) -> str | None:
        """Get latest release tag.

        Returns:
            Latest release tag name or None if error
        """
        for attempt in range(self.network_config.max_retries + 1):
            try:
                async with httpx.AsyncClient(headers=self.headers, timeout=self.TIMEOUT) as client:
                    url = f"{self.BASE_URL}/releases/latest"
                    response = await client.get(url)

                    # Check rate limiting
                    if response.status_code == 429:
                        await self._handle_rate_limit(dict(response.headers), attempt)
                        continue

                    if response.status_code == 200:
                        data = response.json()
                        self._report_rate_limit(dict(response.headers))
                        return data["tag_name"]

                    if response.status_code == 404:
                        # No releases yet, use main
                        return "main"

                    # Server error - retry
                    if response.status_code >= 500 and attempt < self.network_config.max_retries:
                        delay = self._calculate_backoff(attempt)
                        self.console.print(
                            f"[yellow]Server error {response.status_code}, retrying in {delay:.1f}s...[/yellow]"
                        )
                        import asyncio

                        await asyncio.sleep(delay)
                        continue

                    self.console.print(f"[red]GitHub API error: {response.status_code} - {response.text}[/red]")
                    return None

            except httpx.TimeoutException:
                if attempt < self.network_config.max_retries:
                    delay = self._calculate_backoff(attempt)
                    self.console.print(f"[yellow]Timeout fetching latest release, retrying in {delay:.1f}s...[/yellow]")
                    import asyncio

                    await asyncio.sleep(delay)
                    continue
                self.console.print(f"[red]Timeout fetching latest release after {attempt + 1} attempts[/red]")
                return None

            except Exception as e:
                self.console.print(f"[red]Error fetching latest release: {e}[/red]")
                return None

        return None

    async def check_resource_exists_raw(self, resource_type: str, name: str, ref: str = "main") -> bool:
        """Check if a resource exists via raw.githubusercontent.com.

        Args:
            resource_type: Type of resource
            name: Resource name (with or without extension)
            ref: Git ref (branch, tag, or SHA)

        Returns:
            True if resource exists, False otherwise
        """
        # If name already has an extension, check it directly
        if "." in name:
            path = f".claude/{resource_type}/{name}"
            raw_url = f"{self.RAW_BASE_URL}/{ref}/{path}"

            try:
                async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                    response = await client.head(raw_url)
                    return response.status_code == 200
            except Exception:
                return False

        # Otherwise, try common extensions
        extensions_map = {
            "agents": ["md"],
            "tools": ["py", "sh", "js", "ts", "rb"],
            "commands": ["md"],
            "mcp-servers": ["json"],
        }
        extensions_to_try = extensions_map.get(resource_type, ["md", "json", "yaml", "yml", "txt"])

        for extension in extensions_to_try:
            path = f".claude/{resource_type}/{name}.{extension}"
            raw_url = f"{self.RAW_BASE_URL}/{ref}/{path}"

            try:
                async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                    response = await client.head(raw_url)
                    if response.status_code == 200:
                        return True
            except Exception:
                continue

        return False

    async def fetch_resource_metadata(self, resource_type: str, name: str, ref: str = "main") -> dict[str, Any] | None:
        """Get resource metadata (SHA, size, etc.).

        Note: When using raw URLs, only content_sha256 is available.
        For full metadata including GitHub SHA, this falls back to the API.

        Args:
            resource_type: Type of resource
            name: Resource name
            ref: Git ref (branch, tag, or SHA)

        Returns:
            Metadata dictionary or None if not found
        """
        # Map resource types to file extensions
        # For tools, we'll try multiple extensions
        extensions_map = {
            "agents": ["md"],
            "tools": ["py", "sh", "js", "ts", "rb"],  # Try multiple extensions for tools
            "commands": ["md"],
            "mcp-servers": ["json"],
        }

        extensions_to_try = extensions_map.get(resource_type, ["txt"])

        # Try each possible extension
        for extension in extensions_to_try:
            path = f".claude/{resource_type}/{name}.{extension}"

            for attempt in range(self.network_config.max_retries + 1):
                try:
                    async with httpx.AsyncClient(headers=self.headers, timeout=self.TIMEOUT) as client:
                        url = f"{self.BASE_URL}/contents/{path}"
                        params = {"ref": ref}
                        response = await client.get(url, params=params)

                        # Check rate limiting
                        if response.status_code == 429:
                            await self._handle_rate_limit(dict(response.headers), attempt)
                            continue

                        if response.status_code == 200:
                            data = response.json()
                            # Calculate SHA256 of content
                            content_bytes = base64.b64decode(data["content"])
                            content_sha256 = calculate_hash(content_bytes)

                            self._report_rate_limit(dict(response.headers))
                            return {
                                "sha": data["sha"],
                                "sha256": content_sha256,
                                "size": data["size"],
                                "download_url": data["download_url"],
                                "html_url": data["html_url"],
                            }

                        if response.status_code == 404:
                            # For tools, try the next extension
                            if resource_type == "tools" and extension != extensions_to_try[-1]:
                                break  # Try next extension
                            # For non-tools or last extension, return None
                            if extension == extensions_to_try[-1]:
                                return None
                            break  # Try next extension

                        # Server error - retry
                        if response.status_code >= 500 and attempt < self.network_config.max_retries:
                            delay = self._calculate_backoff(attempt)
                            self.console.print(
                                f"[yellow]Server error {response.status_code}, retrying in {delay:.1f}s...[/yellow]"
                            )
                            import asyncio

                            await asyncio.sleep(delay)
                            continue

                        self.console.print(f"[red]GitHub API error: {response.status_code} - {response.text}[/red]")
                        if extension == extensions_to_try[-1]:
                            return None
                        break  # Try next extension

                except httpx.TimeoutException:
                    if attempt < self.network_config.max_retries:
                        delay = self._calculate_backoff(attempt)
                        self.console.print(f"[yellow]Timeout fetching metadata, retrying in {delay:.1f}s...[/yellow]")
                        import asyncio

                        await asyncio.sleep(delay)
                        continue
                    # Max retries exceeded for this extension
                    if extension == extensions_to_try[-1]:
                        self.console.print(f"[red]Timeout fetching metadata after {attempt + 1} attempts[/red]")
                        return None
                    break  # Try next extension

                except Exception as e:
                    if extension == extensions_to_try[-1]:
                        self.console.print(f"[red]Error fetching metadata: {e}[/red]")
                        return None
                    break  # Try next extension

        # Tried all extensions without success
        return None

    async def download_resource_with_progress(
        self, resource_type: str, name: str, ref: str = "main"
    ) -> tuple[bytes | None, str | None]:
        """Download resource content with progress bar.

        Args:
            resource_type: Type of resource
            name: Resource name
            ref: Git ref (branch, tag, or SHA)

        Returns:
            Tuple of (content_bytes, sha256_hash) or (None, None) if not found
        """
        # First try to download directly from raw URL (avoids API rate limits)
        content, sha256 = await self.fetch_resource_raw(resource_type, name, ref)
        if content:
            return content.encode("utf-8"), sha256

        # Fall back to API-based download with metadata
        metadata = await self.fetch_resource_metadata(resource_type, name, ref)
        if not metadata:
            return None, None

        download_url = metadata.get("download_url")
        if not download_url:
            # Fall back to regular fetch
            content, _, sha256 = await self.fetch_resource(resource_type, name, ref, show_progress=False)
            if content:
                return content.encode("utf-8"), sha256
            return None, None

        try:
            # Download with progress and retry logic
            from rich.progress import BarColumn
            from rich.progress import DownloadColumn
            from rich.progress import Progress
            from rich.progress import SpinnerColumn
            from rich.progress import TextColumn

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                console=self.console,
            ) as progress:
                task = progress.add_task(f"Downloading {name}...", total=metadata.get("size", None))

                content_bytes = await download_with_retry(
                    download_url,
                    config=self.network_config,
                    headers=self.headers,
                )

                progress.update(task, completed=len(content_bytes))

            sha256 = calculate_hash(content_bytes)
            return content_bytes, sha256

        except (NetworkError, MaxRetriesExceededError) as e:
            self.console.print(f"[red]Failed to download {resource_type}/{name}: {e}[/red]")
            return None, None

    def _calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff delay.

        Args:
            attempt: Current attempt number (0-based)

        Returns:
            Delay in seconds
        """
        import random

        base_delay = self.network_config.base_delay
        max_delay = self.network_config.max_delay
        jitter = self.network_config.jitter_factor

        delay = min(base_delay * (2**attempt), max_delay)
        if jitter > 0:
            jitter_amount = delay * jitter * (2 * random.random() - 1)
            delay = max(0.1, delay + jitter_amount)

        return delay

    async def _handle_rate_limit(self, headers: dict, attempt: int) -> None:
        """Handle rate limiting with smart wait.

        Args:
            headers: Response headers
            attempt: Current attempt number

        Raises:
            NetworkError: If max retries exceeded
        """
        import asyncio
        import time
        from datetime import datetime

        reset_time = headers.get("X-RateLimit-Reset")
        if reset_time:
            reset_timestamp = int(reset_time)
            wait_time = max(0, reset_timestamp - int(time.time()))

            if wait_time > 0 and attempt < self.network_config.max_retries:
                self.console.print(f"[yellow]Rate limited. Waiting {wait_time} seconds until reset...[/yellow]")
                await asyncio.sleep(wait_time + 1)  # Add 1 second buffer
            else:
                reset_dt = datetime.fromtimestamp(reset_timestamp, tz=UTC)
                raise NetworkError(f"Rate limit exceeded. Resets at {reset_dt}")
        else:
            # No reset time, use exponential backoff
            if attempt < self.network_config.max_retries:
                delay = self._calculate_backoff(attempt)
                self.console.print(f"[yellow]Rate limited. Retrying in {delay:.1f}s...[/yellow]")
                await asyncio.sleep(delay)
            else:
                raise NetworkError("Rate limit exceeded")

    def _report_rate_limit(self, headers: dict) -> None:
        """Report rate limit status if getting low.

        Args:
            headers: Response headers
        """
        remaining = headers.get("X-RateLimit-Remaining")
        limit = headers.get("X-RateLimit-Limit")

        if remaining and limit:
            remaining = int(remaining)
            limit = int(limit)

            if remaining < 10:
                self.console.print(
                    f"[yellow]Warning: GitHub API rate limit low ({remaining}/{limit} remaining)[/yellow]"
                )

                # Provide authentication hint for unauthenticated requests
                if not self.authenticated and limit == 60:
                    self.console.print(
                        "[yellow]💡 Tip: Set GITHUB_TOKEN or GH_TOKEN environment variable "
                        "to increase rate limit from 60 to 5000 requests/hour[/yellow]"
                    )

                if remaining == 0:
                    reset = headers.get("X-RateLimit-Reset")
                    if reset:
                        from datetime import UTC
                        from datetime import datetime

                        reset_time = datetime.fromtimestamp(int(reset), tz=UTC)
                        self.console.print(f"[yellow]Rate limit will reset at: {reset_time}[/yellow]")
