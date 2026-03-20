#!/usr/bin/env bash
# hooks/mcp-channel-handler.sh — Handle incoming MCP channel messages
# Currently NOT ACTIVE — waiting for CC --channels flag and AutoContext push support.
# See ai_context/AUTOCONTEXT-CHANNELS-RESEARCH.md for status.
#
# When activated, stdin receives: {"channel": "...", "payload": {...}}

PLUGIN_DATA="${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugin-data/amplifier-core}"
mkdir -p "$PLUGIN_DATA"

INPUT=$(cat)

if command -v jq >/dev/null 2>&1; then
    CHANNEL=$(echo "$INPUT" | jq -r '.channel // "unknown"' 2>/dev/null)
else
    CHANNEL=$(echo "$INPUT" | grep -oP '"channel"\s*:\s*"\K[^"]+' 2>/dev/null || echo "unknown")
fi

case "$CHANNEL" in
    eval.score)
        echo "$INPUT" >> "$PLUGIN_DATA/eval-history.jsonl"
        ;;
    monitor.alert)
        echo "$INPUT" >> "$PLUGIN_DATA/monitor-alerts.jsonl"
        ;;
    improvement.suggestion)
        echo "$INPUT" >> "$PLUGIN_DATA/improvement-queue.jsonl"
        ;;
    *)
        echo "$INPUT" >> "$PLUGIN_DATA/channel-unknown.jsonl"
        ;;
esac

exit 0
