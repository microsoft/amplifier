---
description: "Show current platform config and regenerate if needed. Use after cloning on a new machine or switching between Windows and Linux."
---

# Platform — Configuration Management

## Overview

Shows the current platform (Windows/Linux), validates configs, and regenerates platform-specific files when needed. Run this after cloning the repo on a new machine or when switching platforms.

## Arguments

$ARGUMENTS

## The Process

### Step 1: Detect Platform

```bash
AMPLIFIER_HOME="${AMPLIFIER_HOME:-$([ -d /opt/amplifier ] && echo /opt/amplifier || echo /c/claude/amplifier)}"
if [[ "$(uname -o 2>/dev/null)" == "Msys" ]] || [[ "$OSTYPE" == "msys" ]]; then
    PLATFORM="windows"
else
    PLATFORM="linux"
fi
echo "Platform: $PLATFORM"
echo "AMPLIFIER_HOME: $AMPLIFIER_HOME"
```

### Step 2: Check Config Status

Verify both runtime configs exist and match the platform:

```bash
echo "=== Config Status ==="
[ -f .mcp.json ] && echo ".mcp.json: EXISTS" || echo ".mcp.json: MISSING — run: bash scripts/setup-platform-config.sh --force"
[ -f .claude/settings.json ] && echo "settings.json: EXISTS" || echo "settings.json: MISSING — run: bash scripts/setup-platform-config.sh --force"
```

### Step 3: Handle Arguments

- **No arguments:** Show status only (Step 1 + Step 2)
- **`setup`:** Regenerate configs for current platform:
  ```bash
  bash scripts/setup-platform-config.sh --force
  ```
- **`switch`:** Regenerate and show what changed:
  ```bash
  bash scripts/setup-platform-config.sh --force
  echo "Restart Claude Code to pick up new MCP configs."
  ```

### Step 4: Validate After Setup

```bash
bash scripts/validate-amplifier.sh 2>&1 | tail -3
```

Report the health check result.

## Platform Differences

| Aspect | Windows | Linux |
|--------|---------|-------|
| Workspace | `C:\claude\amplifier` | `/opt/amplifier` |
| MCP commands | `cmd /c npx ...` | `npx ...` directly |
| Gitea MCP | `.exe` binary | `gitea-mcp` on PATH |
| AutoContext | `uv.exe` absolute path | `uv` on PATH |
| Path style in hooks | `/c/claude/amplifier` (Git Bash) | `/opt/amplifier` |

## Files Involved

| File | Role |
|------|------|
| `config/platform/mcp.windows.json` | Windows MCP server config (source) |
| `config/platform/mcp.linux.json` | Linux MCP server config (source) |
| `config/platform/settings.json.template` | Hooks template with `{{AMPLIFIER_HOME}}` |
| `scripts/setup-platform-config.sh` | Generator script |
| `scripts/lib/platform.sh` | Platform detection library |
| `.mcp.json` | Generated — gitignored, platform-specific |
| `.claude/settings.json` | Generated — gitignored, platform-specific |
