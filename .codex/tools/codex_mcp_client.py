#!/usr/bin/env python3
"""
Codex MCP Client - Thin client for invoking MCP tools via Codex CLI.

This client provides a simple interface to call MCP tools registered with Codex
using the `codex tool` command. It parses JSON responses and handles errors gracefully.
"""

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CodexMCPClient:
    """
    Client for invoking MCP tools via Codex CLI.

    This client uses the `codex tool` command to invoke MCP server tools
    and parses the JSON response.
    """

    def __init__(self, codex_cli_path: str = "codex", profile: str | None = None):
        """
        Initialize the MCP client.

        Args:
            codex_cli_path: Path to Codex CLI executable (default: "codex")
            profile: Codex profile to use (default: None, uses Codex default)
        """
        self.codex_cli = codex_cli_path
        self.profile = profile
        self._verify_codex_available()

    def _verify_codex_available(self):
        """Verify that Codex CLI is available."""
        try:
            result = subprocess.run([self.codex_cli, "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                raise RuntimeError(f"Codex CLI not working: {result.stderr}")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            raise RuntimeError(f"Codex CLI not available: {e}")

    def call_tool(self, server: str, tool_name: str, **kwargs) -> dict[str, Any]:
        """
        Call an MCP tool via Codex CLI.

        Args:
            server: MCP server name (e.g., "amplifier_tasks")
            tool_name: Tool name (e.g., "create_task")
            **kwargs: Tool arguments as keyword arguments

        Returns:
            Parsed JSON response from the tool

        Raises:
            RuntimeError: If tool invocation fails
        """
        try:
            # Build command
            cmd = [self.codex_cli, "tool", f"{server}.{tool_name}"]

            # Add profile if specified
            if self.profile:
                cmd.extend(["--profile", self.profile])

            # Add arguments as JSON
            if kwargs:
                cmd.extend(["--args", json.dumps(kwargs)])

            logger.debug(f"Invoking MCP tool: {' '.join(cmd)}")

            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout for tool calls
                cwd=str(Path.cwd()),
            )

            # Check for errors
            if result.returncode != 0:
                error_msg = result.stderr.strip() or "Unknown error"
                logger.error(f"Tool call failed: {error_msg}")
                return {"success": False, "data": {}, "metadata": {"error": error_msg, "returncode": result.returncode}}

            # Parse JSON response
            try:
                response = json.loads(result.stdout.strip())
                logger.debug(f"Tool response: {response}")
                return response
            except json.JSONDecodeError:
                # If response is not JSON, treat as plain text
                logger.warning(f"Non-JSON response from tool: {result.stdout[:100]}")
                return {
                    "success": True,
                    "data": {"raw_output": result.stdout.strip()},
                    "metadata": {"format": "plain_text"},
                }

        except subprocess.TimeoutExpired:
            logger.error(f"Tool call timed out: {server}.{tool_name}")
            return {"success": False, "data": {}, "metadata": {"error": "Tool call timed out after 30 seconds"}}
        except Exception as e:
            logger.exception(f"Unexpected error calling tool {server}.{tool_name}")
            return {"success": False, "data": {}, "metadata": {"error": str(e), "error_type": type(e).__name__}}


def main():
    """Command-line interface for testing MCP client."""
    import argparse

    parser = argparse.ArgumentParser(description="Codex MCP Client CLI")
    parser.add_argument("server", help="MCP server name")
    parser.add_argument("tool", help="Tool name")
    parser.add_argument("--args", help="Tool arguments as JSON", default="{}")
    parser.add_argument("--profile", help="Codex profile to use")
    parser.add_argument("--codex-cli", help="Path to Codex CLI", default="codex")
    args = parser.parse_args()

    # Parse arguments
    tool_args = json.loads(args.args)

    # Create client
    client = CodexMCPClient(codex_cli_path=args.codex_cli, profile=args.profile)

    # Call tool
    result = client.call_tool(args.server, args.tool, **tool_args)

    # Print result
    print(json.dumps(result, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result.get("success", False) else 1)


if __name__ == "__main__":
    main()
