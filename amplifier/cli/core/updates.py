"""
Auto-update checking for Amplifier CLI v3.

This module provides functionality to check for new versions on GitHub releases,
compare with the current version, and notify users when updates are available.

Contract:
    - Check for updates from GitHub releases API
    - Compare semantic versions properly
    - Store check timestamp to avoid excessive API calls
    - Respect user configuration for auto-checking
    - Non-intrusive notification when updates available
"""

import json
import urllib.error
import urllib.request
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import Any

from amplifier.cli.core import get_amplifier_dir
from amplifier.cli.core.version import get_version


def get_update_state_path() -> Path:
    """Get the path to the update state file.

    Returns:
        Path to .amplifier/update_state.json
    """
    return get_amplifier_dir() / "update_state.json"


def load_update_state() -> dict[str, Any]:
    """Load the update check state from file.

    Returns:
        Dictionary containing last check time and latest version info
    """
    state_path = get_update_state_path()

    if state_path.exists():
        try:
            with open(state_path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            # If file is corrupted, return empty state
            return {}

    return {}


def save_update_state(state: dict[str, Any]) -> None:
    """Save the update check state to file.

    Args:
        state: Dictionary containing update state information
    """
    state_path = get_update_state_path()

    # Ensure .amplifier directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)

    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def get_last_check_time() -> datetime | None:
    """Get the timestamp of the last update check.

    Returns:
        datetime of last check or None if never checked
    """
    state = load_update_state()
    last_check = state.get("last_check")

    if last_check:
        try:
            return datetime.fromisoformat(last_check)
        except ValueError:
            return None

    return None


def save_last_check_time(check_time: datetime | None = None) -> None:
    """Save the timestamp of an update check.

    Args:
        check_time: datetime to save, defaults to current time
    """
    if check_time is None:
        check_time = datetime.now()

    state = load_update_state()
    state["last_check"] = check_time.isoformat()
    save_update_state(state)


def should_check_updates(force: bool = False, check_frequency_hours: int = 24) -> bool:
    """Determine if an update check should be performed.

    Args:
        force: If True, always check for updates
        check_frequency_hours: Minimum hours between checks (default 24)

    Returns:
        True if update check should be performed
    """
    if force:
        return True

    # Check if auto-update checking is enabled in config
    from amplifier.cli.commands.config import load_config

    config = load_config()

    if not config.get("auto_update_check", True):
        return False

    # Check last update time
    last_check = get_last_check_time()

    if last_check is None:
        # Never checked before
        return True

    # Check if enough time has passed
    time_since_check = datetime.now() - last_check
    min_interval = timedelta(hours=check_frequency_hours)

    return time_since_check >= min_interval


def parse_version(version_str: str) -> tuple[int, int, int]:
    """Parse a semantic version string into components.

    Args:
        version_str: Version string like "1.2.3" or "v1.2.3"

    Returns:
        Tuple of (major, minor, patch) integers
    """
    # Remove 'v' prefix if present
    if version_str.startswith("v"):
        version_str = version_str[1:]

    # Split into parts and handle pre-release versions
    parts = version_str.split("-")[0].split(".")

    # Pad with zeros if necessary
    while len(parts) < 3:
        parts.append("0")

    try:
        return (int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        # If parsing fails, return a minimum version
        return (0, 0, 0)


def is_newer_version(latest: str, current: str) -> bool:
    """Check if the latest version is newer than current.

    Args:
        latest: Latest version string
        current: Current version string

    Returns:
        True if latest is newer than current
    """
    latest_parts = parse_version(latest)
    current_parts = parse_version(current)

    return latest_parts > current_parts


def fetch_latest_version(repo: str = "microsoft/amplifier", timeout: int = 5) -> dict[str, Any] | None:
    """Fetch the latest release information from GitHub.

    Args:
        repo: GitHub repository in format "owner/repo"
        timeout: Request timeout in seconds

    Returns:
        Dictionary with release info or None if fetch fails
    """
    api_url = f"https://api.github.com/repos/{repo}/releases/latest"

    try:
        # Create request with user agent (GitHub API requires it)
        request = urllib.request.Request(
            api_url, headers={"User-Agent": "Amplifier-CLI", "Accept": "application/vnd.github.v3+json"}
        )

        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode())

            return {
                "version": data.get("tag_name", ""),
                "name": data.get("name", ""),
                "html_url": data.get("html_url", ""),
                "published_at": data.get("published_at", ""),
                "body": data.get("body", ""),
            }

    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, KeyError):
        # Silently fail - we don't want to disrupt the user's workflow
        return None


def notify_update_available(
    latest_version: str, current_version: str, release_url: str | None = None, quiet: bool = False
) -> None:
    """Display a notification that an update is available.

    Args:
        latest_version: The latest available version
        current_version: The currently installed version
        release_url: URL to the release page
        quiet: If True, use minimal output
    """
    if quiet:
        # In quiet mode, just a simple one-liner
        print(f"Update available: {current_version} → {latest_version}")
    else:
        # Rich formatted notification
        from rich.console import Console
        from rich.panel import Panel

        console = Console()

        message = (
            f"[bold yellow]📦 Update Available![/bold yellow]\n\n"
            f"Current version: [cyan]{current_version}[/cyan]\n"
            f"Latest version:  [green]{latest_version}[/green]\n"
        )

        if release_url:
            message += f"\n[dim]View release: {release_url}[/dim]\n"

        message += "\nUpdate with: [bold]pip install --upgrade amplifier-cli[/bold]"

        console.print(
            Panel.fit(
                message,
                title="[bold]Amplifier CLI Update[/bold]",
                border_style="yellow",
                padding=(1, 2),
            )
        )


def check_for_updates(force: bool = False, silent: bool = False) -> str | None:
    """Check for available updates and notify if found.

    This is the main entry point for update checking. It respects
    configuration settings and rate limiting.

    Args:
        force: If True, bypass rate limiting and config
        silent: If True, don't display notifications

    Returns:
        Latest version string if update available, None otherwise
    """
    # Check if we should perform the check
    if not should_check_updates(force=force):
        return None

    # Load config for repository
    from amplifier.cli.commands.config import load_config

    config = load_config()
    repo = config.get("github_repo", "microsoft/amplifier")

    # Fetch latest release info
    release_info = fetch_latest_version(repo)

    # Update last check time regardless of success
    save_last_check_time()

    if not release_info:
        # Failed to fetch, silently continue
        return None

    latest_version = release_info.get("version", "")
    if not latest_version:
        return None

    current_version = get_version()

    # Check if update is available
    if is_newer_version(latest_version, current_version):
        # Save the latest version info for future reference
        state = load_update_state()
        state["latest_version"] = latest_version
        state["latest_release_url"] = release_info.get("html_url")
        state["latest_release_date"] = release_info.get("published_at")
        save_update_state(state)

        # Notify user if not silent
        if not silent:
            notify_update_available(latest_version, current_version, release_info.get("html_url"))

        return latest_version

    return None


def check_updates_on_startup(quiet: bool = False, debug: bool = False) -> None:
    """Perform update check on CLI startup.

    This should be called from the main CLI entry point to check
    for updates in a non-intrusive way.

    Args:
        quiet: If True, use minimal output
        debug: If True, show debug information
    """
    try:
        # Only check in normal mode (not quiet, not debug)
        if not quiet and not debug:
            check_for_updates(silent=False)
    except Exception:
        # Never let update checking crash the CLI
        pass
