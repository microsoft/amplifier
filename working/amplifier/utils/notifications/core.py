"""
Core notification functionality.
"""

import logging
from datetime import datetime
from pathlib import Path

from .models import NotificationRequest
from .models import NotificationResponse
from .models import Platform
from .platforms import detect_platform
from .platforms import send_linux_notification
from .platforms import send_macos_notification
from .platforms import send_windows_notification
from .platforms import send_wsl_notification

logger = logging.getLogger(__name__)


class NotificationSender:
    """Handles sending notifications across different platforms."""

    def __init__(self, debug: bool = False):
        """Initialize notification sender.

        Args:
            debug: Enable debug mode for verbose logging
        """
        self.debug = debug
        self.platform = detect_platform()
        self.debug_log: list[str] = []

    def _debug(self, message: str):
        """Add a debug message."""
        if self.debug:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {message}"
            self.debug_log.append(log_entry)
            logger.debug(log_entry)

    def _get_project_name(self, cwd: str | None) -> str | None:
        """Extract project name from working directory.

        Args:
            cwd: Current working directory path

        Returns:
            Project name or None
        """
        if not cwd:
            self._debug("No working directory provided")
            return None

        cwd_path = Path(cwd)
        if not cwd_path.exists():
            self._debug(f"Working directory does not exist: {cwd}")
            return None

        # Just use directory name
        project_name = cwd_path.name
        self._debug(f"Using directory name as project: {project_name}")
        return project_name

    def _format_subtitle(self, subtitle: str | None, session_id: str | None) -> str | None:
        """Format subtitle.

        Args:
            subtitle: Base subtitle text
            session_id: Optional session ID (ignored)

        Returns:
            Subtitle or None
        """
        return subtitle

    def send(self, request: NotificationRequest) -> NotificationResponse:
        """Send a notification.

        Args:
            request: Notification request with message and optional metadata

        Returns:
            Response indicating success and platform used
        """
        self.debug = request.debug
        self.debug_log = []

        self._debug(f"Platform detected: {self.platform}")
        self._debug(f"Request: message='{request.message}', title='{request.title}'")

        # Format subtitle with session info if provided
        subtitle = self._format_subtitle(request.subtitle, request.session_id)
        self._debug(f"Formatted subtitle: {subtitle}")

        # Send platform-specific notification
        success = False
        error: str | None = None
        fallback_used = False

        if self.platform == Platform.MACOS:
            success, error = send_macos_notification(request.message, request.title, subtitle)
        elif self.platform == Platform.LINUX:
            success, error = send_linux_notification(request.message, request.title, subtitle)
        elif self.platform == Platform.WSL:
            success, error = send_wsl_notification(request.message, request.title, subtitle)
        elif self.platform == Platform.WINDOWS:
            success, error = send_windows_notification(request.message, request.title, subtitle)
        else:
            # Unknown platform - fallback to console
            success = False
            error = f"Unknown platform: {self.platform}"

        # Fallback to console output if notification failed
        if not success:
            fallback_used = True
            if subtitle:
                print(f"[{subtitle}] {request.message}")
            else:
                print(request.message)
            self._debug(f"Fallback to console output due to: {error}")

        return NotificationResponse(
            success=success or fallback_used,
            platform=self.platform,
            fallback_used=fallback_used,
            error=error if not fallback_used else None,
            debug_log="\n".join(self.debug_log) if self.debug else None,
        )


def send_notification(
    message: str,
    title: str = "Amplifier",
    subtitle: str | None = None,
    session_id: str | None = None,
    cwd: str | None = None,
    debug: bool = False,
) -> NotificationResponse:
    """Send a desktop notification.

    This is the main entry point for sending notifications.
    It automatically detects the platform and uses the appropriate method.

    Args:
        message: Main notification message
        title: Notification title (default: "Amplifier")
        subtitle: Optional subtitle (e.g., project name)
        session_id: Optional session ID for tracking (ignored)
        cwd: Current working directory for context
        debug: Enable debug mode

    Returns:
        NotificationResponse with success status and platform info
    """
    # Always add CWD context to subtitle if provided
    if cwd:
        # Extract project name from CWD for context
        from pathlib import Path

        cwd_path = Path(cwd)
        project_name = cwd_path.name
        subtitle = project_name if not subtitle else f"{subtitle} - {project_name}"

    request = NotificationRequest(
        message=message,
        title=title,
        subtitle=subtitle,
        session_id=session_id,
        debug=debug,
    )

    sender = NotificationSender(debug=debug)
    return sender.send(request)
