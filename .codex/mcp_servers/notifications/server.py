import asyncio
import json
import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).parent.parent))

from base import AmplifierMCPServer
from base import error_response
from base import success_response


class NotificationsServer(AmplifierMCPServer):
    """MCP server for cross-platform desktop notifications"""

    def __init__(self):
        # Initialize FastMCP
        mcp = FastMCP("amplifier-notifications")

        # Initialize base server
        super().__init__("notifications", mcp)

        # Setup notification history storage
        project_root = self.project_root if self.project_root else Path.cwd()
        self.history_file = project_root / ".codex" / "notifications" / "history.json"
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

        # Register tools
        self._register_tools()

    def _register_tools(self):
        """Register all MCP tools"""

        @self.mcp.tool()
        async def notify(title: str, message: str, urgency: str = "normal") -> dict[str, Any]:
            """Send desktop notification using platform-specific commands

            Args:
                title: Notification title
                message: Notification message
                urgency: Urgency level (low/normal/critical)

            Returns:
                Success status and metadata
            """
            try:
                self.logger.info(f"Sending notification: {title} - {urgency}")
                self.logger.debug(f"Message: {message}")

                success = await self._send_notification(title, message, urgency)

                if success:
                    await self._save_notification(title, message, urgency)
                    return success_response({"sent": True}, {"urgency": urgency})
                return error_response("Failed to send notification")

            except Exception as e:
                self.logger.exception("notify failed", e)
                return error_response(f"Notification failed: {str(e)}")

        @self.mcp.tool()
        async def notify_on_completion(task_description: str) -> dict[str, Any]:
            """Alert when long-running tasks finish

            Args:
                task_description: Description of the completed task

            Returns:
                Success status
            """
            try:
                self.logger.info(f"Task completion notification: {task_description}")
                title = "Task Completed"
                message = f"Completed: {task_description}"
                return await notify(title, message, "normal")

            except Exception as e:
                self.logger.exception("notify_on_completion failed", e)
                return error_response(f"Completion notification failed: {str(e)}")

        @self.mcp.tool()
        async def notify_on_error(error_details: str) -> dict[str, Any]:
            """Alert on failures

            Args:
                error_details: Details of the error

            Returns:
                Success status
            """
            try:
                self.logger.info(f"Error notification: {error_details}")
                title = "Error Occurred"
                message = f"Error: {error_details}"
                return await notify(title, message, "critical")

            except Exception as e:
                self.logger.exception("notify_on_error failed", e)
                return error_response(f"Error notification failed: {str(e)}")

        @self.mcp.tool()
        async def get_notification_history(limit: int = 50) -> dict[str, Any]:
            """View recent notifications

            Args:
                limit: Maximum number of notifications to return

            Returns:
                List of recent notifications with metadata
            """
            try:
                self.logger.info(f"Retrieving notification history (limit: {limit})")

                history = await self._load_history()

                # Sort by timestamp descending (most recent first)
                history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

                limited = history[:limit]

                self.logger.info(f"Returning {len(limited)} notifications from {len(history)} total")

                return success_response(
                    {"notifications": limited, "total": len(history)}, {"limit": limit, "returned": len(limited)}
                )

            except Exception as e:
                self.logger.exception("get_notification_history failed", e)
                return error_response(f"Failed to get history: {str(e)}")

    async def _send_notification(self, title: str, message: str, urgency: str) -> bool:
        """Send notification using platform-specific commands"""
        system = platform.system()

        try:
            if system == "Linux":
                # Use notify-send with urgency
                cmd = ["notify-send", "--urgency", urgency, title, message]

            elif system == "Darwin":
                # Use osascript for macOS notifications
                script = f'display notification "{message}" with title "{title}"'
                if urgency == "critical":
                    script += ' sound name "Basso"'
                cmd = ["osascript", "-e", script]

            elif system == "Windows":
                # Use PowerShell message box for Windows
                cmd = ["powershell", "-Command", f"[System.Windows.Forms.MessageBox]::Show('{message}', '{title}')"]

            else:
                self.logger.error(f"Unsupported platform: {system}")
                return False

            self.logger.debug(f"Running command: {' '.join(cmd)}")

            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                stderr_output = stderr.decode().strip()
                self.logger.warning(f"Notification command failed: {stderr_output}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Failed to send notification on {system}: {e}")
            return False

    async def _save_notification(self, title: str, message: str, urgency: str):
        """Save notification to history file"""
        try:
            history = await self._load_history()

            entry = {"timestamp": datetime.now().isoformat(), "title": title, "message": message, "urgency": urgency}

            history.append(entry)

            # Keep only last 1000 entries to prevent file from growing too large
            if len(history) > 1000:
                history = history[-1000:]

            with open(self.history_file, "w") as f:
                json.dump(history, f, indent=2)

            self.logger.debug(f"Saved notification to history: {title}")

        except Exception as e:
            self.logger.error(f"Failed to save notification: {e}")

    async def _load_history(self) -> list[dict]:
        """Load notification history from file"""
        try:
            if self.history_file.exists():
                with open(self.history_file) as f:
                    data = json.load(f)
                    # Ensure it's a list
                    return data if isinstance(data, list) else []
            return []
        except Exception as e:
            self.logger.error(f"Failed to load history: {e}")
            return []


# Create and run server
if __name__ == "__main__":
    server = NotificationsServer()
    server.run()
