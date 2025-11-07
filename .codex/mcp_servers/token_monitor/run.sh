#!/bin/bash
cd "$(dirname "$0")" || exit 1
exec python -m mcp.server.stdio server:mcp