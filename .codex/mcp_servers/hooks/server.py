#!/usr/bin/env python3
"""
Hooks Orchestration MCP Server

Provides automatic triggers for file changes, session events, periodic tasks.
Replicates Claude Code's automatic hook behavior through MCP tools.
"""

import asyncio
import json
import os
import threading
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastmcp import FastMCP
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from ..base import AmplifierMCPServer
from ..base import MCPLogger
from ..tools.codex_mcp_client import CodexMCPClient


class HookConfig:
    """Configuration for a hook."""

    def __init__(
        self,
        hook_id: str,
        event_type: str,
        action: str,
        matcher: str | None = None,
        tool_name: str | None = None,
        tool_args: dict[str, Any] | None = None,
    ):
        self.hook_id = hook_id
        self.event_type = event_type
        self.action = action
        self.matcher = matcher
        self.tool_name = tool_name
        self.tool_args = tool_args or {}


class FileWatchHandler(FileSystemEventHandler):
    """File system event handler for hooks."""

    def __init__(self, hooks_server):
        self.hooks_server = hooks_server

    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory:
            self.hooks_server._trigger_file_hooks("file_change", event.src_path)

    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory:
            self.hooks_server._trigger_file_hooks("file_change", event.src_path)

    def on_deleted(self, event):
        """Handle file deletion events."""
        if not event.is_directory:
            self.hooks_server._trigger_file_hooks("file_change", event.src_path)


class HooksServer(AmplifierMCPServer):
    """MCP server for orchestrating automatic hooks."""

    def __init__(self, mcp_instance):
        super().__init__("amplifier_hooks", mcp_instance)
        self.hooks: dict[str, HookConfig] = {}
        self.hook_history: list[dict[str, Any]] = []
        self.file_observer = None
        self.watch_handler: FileWatchHandler | None = None
        self.watch_thread: threading.Thread | None = None
        self.watch_enabled = False
        self.logger = MCPLogger("hooks")

        # Load server configuration
        self.server_config = self.get_server_config()
        self.auto_enable_file_watch = self.server_config.get("auto_enable_file_watch", False)
        self.check_interval_seconds = self.server_config.get("check_interval_seconds", 5)

        # Load existing hooks
        self._load_hooks()

        # Auto-enable file watching if configured
        if self.auto_enable_file_watch:
            self.logger.info("Auto-enabling file watching based on config")
            self._start_file_watching(["*.py", "*.js", "*.ts", "*.md"], self.check_interval_seconds)

    def _load_hooks(self):
        """Load hooks from storage."""
        hooks_file = Path(".codex/hooks/hooks.json")
        if hooks_file.exists():
            try:
                with open(hooks_file) as f:
                    data = json.load(f)
                    for hook_data in data.get("hooks", []):
                        hook = HookConfig(**hook_data)
                        self.hooks[hook.hook_id] = hook
            except Exception as e:
                self.logger.error(f"Failed to load hooks: {e}")

    def _save_hooks(self):
        """Save hooks to storage."""
        hooks_file = Path(".codex/hooks/hooks.json")
        hooks_file.parent.mkdir(exist_ok=True)

        hooks_data = {
            "hooks": [
                {
                    "hook_id": hook.hook_id,
                    "event_type": hook.event_type,
                    "action": hook.action,
                    "matcher": hook.matcher,
                    "tool_name": hook.tool_name,
                    "tool_args": hook.tool_args,
                }
                for hook in self.hooks.values()
            ]
        }

        with open(hooks_file, "w") as f:
            json.dump(hooks_data, f, indent=2)

    def _trigger_file_hooks(self, event_type: str, file_path: str):
        """Trigger hooks for file events."""
        for hook in self.hooks.values():
            if hook.event_type == event_type:
                if hook.matcher and not self._matches_pattern(file_path, hook.matcher):
                    continue

                self._execute_hook(hook, {"file_path": file_path})

    def _matches_pattern(self, file_path: str, pattern: str) -> bool:
        """Check if file path matches pattern."""
        # Simple glob-style matching
        import fnmatch

        return fnmatch.fnmatch(file_path, pattern)

    def _execute_hook(self, hook: HookConfig, context: dict[str, Any]):
        """Execute a hook asynchronously."""

        async def execute():
            try:
                self.logger.info(f"Executing hook {hook.hook_id} for {hook.event_type}")

                # Record execution
                execution = {
                    "hook_id": hook.hook_id,
                    "timestamp": time.time(),
                    "event_type": hook.event_type,
                    "action": hook.action,
                    "context": context,
                    "success": False,
                }

                # Get Codex profile from environment
                codex_profile = os.environ.get("CODEX_PROFILE")

                # Execute action based on hook configuration
                if hook.action == "run_tool" and hook.tool_name:
                    try:
                        # Split tool_name into server.tool format
                        if "." not in hook.tool_name:
                            raise ValueError(f"Invalid tool_name format: {hook.tool_name}. Expected 'server.tool'")

                        server_name, tool_name = hook.tool_name.split(".", 1)

                        # Create MCP client
                        client = CodexMCPClient(profile=codex_profile)

                        # Call the tool
                        self.logger.info(f"Invoking MCP tool {server_name}.{tool_name} with args {hook.tool_args}")
                        result = await asyncio.to_thread(client.call_tool, server_name, tool_name, **hook.tool_args)

                        execution["tool_invoked"] = hook.tool_name
                        execution["tool_args"] = hook.tool_args
                        execution["tool_response"] = result
                        execution["success"] = result.get("success", False)
                        if not execution["success"]:
                            execution["error"] = result.get("metadata", {}).get("error", "Unknown error")

                    except Exception as tool_error:
                        self.logger.error(f"Tool invocation failed: {tool_error}")
                        execution["error"] = str(tool_error)
                        execution["success"] = False

                elif hook.action == "quality_check":
                    try:
                        # Create MCP client
                        client = CodexMCPClient(profile=codex_profile)

                        # Determine file paths to check
                        file_paths = []
                        if context.get("file_path"):
                            file_paths = [context["file_path"]]

                        # Call quality check tool
                        tool_name = "check_code_quality"
                        tool_args = {"file_paths": file_paths} if file_paths else {}

                        self.logger.info(f"Invoking quality check tool with args {tool_args}")
                        result = await asyncio.to_thread(client.call_tool, "amplifier_quality", tool_name, **tool_args)

                        execution["tool_invoked"] = f"amplifier_quality.{tool_name}"
                        execution["tool_args"] = tool_args
                        execution["tool_response"] = result
                        execution["success"] = result.get("success", False)
                        if not execution["success"]:
                            execution["error"] = result.get("metadata", {}).get("error", "Unknown error")

                    except Exception as e:
                        self.logger.error(f"Quality check failed: {e}")
                        execution["error"] = str(e)

                elif hook.action == "memory_operation":
                    try:
                        # Create MCP client
                        client = CodexMCPClient(profile=codex_profile)

                        # Use sensible defaults for memory operation
                        # Could be enhanced to parse hook.tool_args for specific operations
                        tool_name = "get_memory_insights"  # Default memory operation
                        tool_args = {}

                        # If context has messages, use finalize_session instead
                        if context.get("messages"):
                            tool_name = "finalize_session"
                            tool_args = {"messages": context["messages"]}

                        self.logger.info(f"Invoking memory tool {tool_name} with args {tool_args}")
                        result = await asyncio.to_thread(client.call_tool, "amplifier_session", tool_name, **tool_args)

                        execution["tool_invoked"] = f"amplifier_session.{tool_name}"
                        execution["tool_args"] = tool_args
                        execution["tool_response"] = result
                        execution["success"] = result.get("success", False)
                        if not execution["success"]:
                            execution["error"] = result.get("metadata", {}).get("error", "Unknown error")

                    except Exception as e:
                        self.logger.error(f"Memory operation failed: {e}")
                        execution["error"] = str(e)

                self.hook_history.append(execution)
                self._save_hook_history()

            except Exception as e:
                self.logger.error(f"Hook execution failed: {e}")

        # Run in background
        asyncio.create_task(execute())

    def _save_hook_history(self):
        """Save hook execution history."""
        history_file = Path(".codex/hooks/history.json")
        history_file.parent.mkdir(exist_ok=True)

        with open(history_file, "w") as f:
            json.dump(self.hook_history[-100:], f, indent=2)  # Keep last 100 executions

    def _start_file_watching(self, file_patterns: list[str], check_interval: int):
        """Start file watching for the specified patterns."""
        if self.file_observer:
            self.file_observer.stop()

        self.file_observer = Observer()
        self.watch_handler = FileWatchHandler(self)

        # Watch current directory and subdirectories
        self.file_observer.schedule(self.watch_handler, ".", recursive=True)
        self.file_observer.start()

        self.watch_enabled = True
        self.logger.info(f"Started file watching with patterns: {file_patterns}")

    def _stop_file_watching(self):
        """Stop file watching."""
        if self.file_observer:
            self.file_observer.stop()
            self.file_observer = None
            self.watch_handler = None

        self.watch_enabled = False
        self.logger.info("Stopped file watching")

    async def register_hook(
        self,
        event_type: str,
        action: str,
        matcher: str | None = None,
        tool_name: str | None = None,
        tool_args: dict[str, Any] | None = None,
    ) -> str:
        """Register a new hook.

        Args:
            event_type: Type of event ("file_change", "session_start", "session_end", "tool_use", "periodic")
            action: Action to take ("run_tool", "quality_check", "memory_operation")
            matcher: Pattern to match for file events
            tool_name: Name of tool to run
            tool_args: Arguments for tool execution

        Returns:
            Hook ID
        """
        hook_id = str(uuid4())
        hook = HookConfig(hook_id, event_type, action, matcher, tool_name, tool_args)
        self.hooks[hook_id] = hook
        self._save_hooks()

        self.logger.info(f"Registered hook {hook_id} for {event_type}")
        return hook_id

    async def list_active_hooks(self) -> list[dict[str, Any]]:
        """Return list of all active hooks with metadata."""
        return [
            {
                "hook_id": hook.hook_id,
                "event_type": hook.event_type,
                "action": hook.action,
                "matcher": hook.matcher,
                "tool_name": hook.tool_name,
                "tool_args": hook.tool_args,
            }
            for hook in self.hooks.values()
        ]

    async def trigger_hook_manually(self, hook_id: str) -> bool:
        """Manually trigger a hook for testing.

        Args:
            hook_id: ID of hook to trigger

        Returns:
            True if hook was found and triggered
        """
        if hook_id not in self.hooks:
            return False

        hook = self.hooks[hook_id]
        self._execute_hook(hook, {"manual_trigger": True, "timestamp": time.time()})
        return True

    async def enable_watch_mode(
        self, file_patterns: list[str] | None = None, check_interval: int | None = None
    ) -> bool:
        """Start file watching mode.

        Args:
            file_patterns: List of file patterns to watch (uses config default if None)
            check_interval: Interval between checks in seconds (uses config default if None)

        Returns:
            True if watching was started
        """
        # Use config defaults if not specified
        if file_patterns is None:
            file_patterns = ["*.py", "*.js", "*.ts", "*.md"]  # Default patterns
        if check_interval is None:
            check_interval = self.check_interval_seconds

        try:
            self._start_file_watching(file_patterns, check_interval)
            return True
        except Exception as e:
            self.logger.error(f"Failed to start file watching: {e}")
            return False

    async def disable_watch_mode(self) -> bool:
        """Stop file watching mode.

        Returns:
            True if watching was stopped
        """
        try:
            self._stop_file_watching()
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop file watching: {e}")
            return False

    async def get_hook_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """Return recent hook execution history.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of recent hook executions
        """
        return self.hook_history[-limit:]


def main():
    """Main entry point for the hooks MCP server."""
    mcp = FastMCP("amplifier_hooks")
    server = HooksServer(mcp)

    # Register tools with error handling
    @mcp.tool()
    async def register_hook(
        event_type: str,
        action: str,
        matcher: str | None = None,
        tool_name: str | None = None,
        tool_args: dict[str, Any] | None = None,
    ) -> str:
        """Register a new automatic hook."""
        return await server.tool_error_handler(server.register_hook)(event_type, action, matcher, tool_name, tool_args)

    @mcp.tool()
    async def list_active_hooks() -> list[dict[str, Any]]:
        """List all active hooks."""
        return await server.tool_error_handler(server.list_active_hooks)()

    @mcp.tool()
    async def trigger_hook_manually(hook_id: str) -> bool:
        """Manually trigger a hook for testing."""
        return await server.tool_error_handler(server.trigger_hook_manually)(hook_id)

    @mcp.tool()
    async def enable_watch_mode(file_patterns: list[str] | None = None, check_interval: int = 5) -> bool:
        """Enable file watching mode."""
        return await server.tool_error_handler(server.enable_watch_mode)(file_patterns, check_interval)

    @mcp.tool()
    async def disable_watch_mode() -> bool:
        """Disable file watching mode."""
        return await server.tool_error_handler(server.disable_watch_mode)()

    @mcp.tool()
    async def get_hook_history(limit: int = 10) -> list[dict[str, Any]]:
        """Get recent hook execution history."""
        return await server.tool_error_handler(server.get_hook_history)(limit)

    # Run the server
    mcp.run()


if __name__ == "__main__":
    main()
