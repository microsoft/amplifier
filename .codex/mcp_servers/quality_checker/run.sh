#!/bin/bash
# Wrapper script for Quality Checker MCP Server
# Ensures correct working directory and environment for server execution

# Navigate to project root (3 levels up from .codex/mcp_servers/quality_checker/)
cd "$(dirname "$0")/../../.." || exit 1

# Set required environment variables
export AMPLIFIER_ROOT="$(pwd)"
export PYTHONPATH="$(pwd)"

# Execute the server, replacing this shell process
exec uv run python .codex/mcp_servers/quality_checker/server.py
