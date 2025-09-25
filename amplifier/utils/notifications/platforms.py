"""
Platform-specific notification implementations.
"""

import logging
import platform
import shutil
import subprocess

from .models import Platform

logger = logging.getLogger(__name__)


def detect_platform() -> Platform:
    """Detect the current platform."""
    system = platform.system()

    if system == "Darwin":
        return Platform.MACOS
    if system == "Linux":
        # Check if running in WSL
        try:
            with open("/proc/version") as f:
                if "microsoft" in f.read().lower():
                    return Platform.WSL
        except Exception:
            pass
        return Platform.LINUX
    if system == "Windows":
        return Platform.WINDOWS
    return Platform.UNKNOWN


def send_macos_notification(
    message: str, title: str = "Claude Code", subtitle: str | None = None
) -> tuple[bool, str | None]:
    """Send notification on macOS using osascript."""
    try:
        if subtitle:
            script = f'display notification "{message}" with title "{title}" subtitle "{subtitle}"'
        else:
            script = f'display notification "{message}" with title "{title}"'

        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0, result.stderr if result.returncode != 0 else None
    except Exception as e:
        return False, str(e)


def send_linux_notification(
    message: str, title: str = "Claude Code", subtitle: str | None = None
) -> tuple[bool, str | None]:
    """Send notification on Linux using notify-send."""
    if not shutil.which("notify-send"):
        return False, "notify-send not found"

    try:
        if subtitle:
            # Use HTML formatting for subtitle
            formatted_title = f"<b>{subtitle}</b>"
        else:
            formatted_title = title

        result = subprocess.run(
            ["notify-send", formatted_title, message],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0, result.stderr if result.returncode != 0 else None
    except Exception as e:
        return False, str(e)


def send_wsl_notification(
    message: str, title: str = "Claude Code", subtitle: str | None = None
) -> tuple[bool, str | None]:
    """Send notification on WSL using Windows PowerShell."""
    try:
        if subtitle:
            # Use ToastText02 template with two text fields
            ps_script = f"""
                [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
                [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
                [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

                $APP_ID = '{title}'
                $template = @"
<toast><visual><binding template='ToastText02'>
    <text id='1'>{subtitle}</text>
    <text id='2'>{message}</text>
</binding></visual></toast>
"@
                $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
                $xml.LoadXml($template)
                $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
                [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($APP_ID).Show($toast)
            """
        else:
            # Use ToastText01 template with single text field
            ps_script = f"""
                [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
                [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
                [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

                $APP_ID = '{title}'
                $template = @"
<toast><visual><binding template='ToastText01'>
    <text id='1'>{message}</text>
</binding></visual></toast>
"@
                $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
                $xml.LoadXml($template)
                $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
                [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($APP_ID).Show($toast)
            """

        result = subprocess.run(
            ["powershell.exe", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0, result.stderr if result.returncode != 0 else None
    except Exception as e:
        return False, str(e)


def send_windows_notification(
    message: str, title: str = "Claude Code", subtitle: str | None = None
) -> tuple[bool, str | None]:
    """Send notification on Windows using PowerShell."""
    # Same implementation as WSL
    return send_wsl_notification(message, title, subtitle)
