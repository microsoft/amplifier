#!/usr/bin/env bash
# enforce-brainstorm.sh — PreToolUse hook for EnterPlanMode
# Blocks Plan Mode entry unless /brainstorm or /create-plan has been completed
# in this session (indicated by marker file /tmp/amplifier-brainstorm-done).

MARKER="/tmp/amplifier-brainstorm-done"

if [ ! -f "$MARKER" ]; then
  echo "Brainstorm required before entering Plan Mode." >&2
  echo "Run /brainstorm to validate the design, then try again." >&2
  echo "The marker file /tmp/amplifier-brainstorm-done will be set automatically." >&2
  exit 2
fi

exit 0
