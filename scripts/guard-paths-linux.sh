#!/bin/bash
# Guard hook: Block file/folder creation outside allowed paths (Linux version).
# Used as PreToolUse hook for Write and Bash tools.
# Registered in ~/.claude/settings.json on Linux machines.

INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // empty')

# --- Allowed paths ---
ALLOWED='^(/opt/|/home/claude/|/tmp/|'"$HOME"'/.claude/)'

case "$TOOL" in
  Write)
    FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

    if echo "$FILE_PATH" | grep -qE "$ALLOWED"; then
      exit 0
    fi
    echo "BLOCKED: Write to '$FILE_PATH' — not in allowed paths. Edit /opt/amplifier/scripts/guard-paths-linux.sh to add exceptions." >&2
    exit 2
    ;;

  Bash)
    CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

    # Check mkdir commands targeting system paths
    if echo "$CMD" | grep -qE 'mkdir.*/(bin|sbin|usr|etc|var|boot|root|srv|mnt|media|proc|sys|dev)/'; then
      echo "BLOCKED: mkdir targeting system directory — not in allowed paths." >&2
      exit 2
    fi

    # Check output redirection outside allowed paths
    if echo "$CMD" | grep -qE '>\s*/[a-z]'; then
      TARGET=$(echo "$CMD" | grep -oE '>\s*/[a-zA-Z][a-zA-Z0-9_/-]*' | sed 's|^>\s*||' | head -1)
      if [ -n "$TARGET" ] && ! echo "$TARGET" | grep -qE "$ALLOWED"; then
        echo "BLOCKED: Redirect to '$TARGET' — not in allowed paths." >&2
        exit 2
      fi
    fi

    exit 0
    ;;

  *)
    exit 0
    ;;
esac
