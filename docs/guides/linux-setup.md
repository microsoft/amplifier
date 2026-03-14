# Amplifier Linux Setup Guide

## Machine: 172.31.250.2 (mcp, Ubuntu)

### Projects in /opt/

| Project | Purpose |
|---------|---------|
| `/opt/amplifier` | Amplifier platform (this repo) |
| `/opt/autocontext` | AutoContext MCP server (global, all projects) |
| `/opt/genetics-platform` | Genetics analysis platform |
| `/opt/universal-siem-*` | Universal SIEM components |
| `/opt/monitoring` | Infrastructure monitoring |
| `/opt/obsidian` | Obsidian vault (MCP served via SSE) |

### MCP Server Architecture

**Global servers** (available to ALL Claude Code projects, registered via `claude mcp add -s user`):

| Server | Command | Notes |
|--------|---------|-------|
| autocontext | `/home/claude/.local/bin/uv run --directory /opt/autocontext/autocontext autoctx mcp-serve` | Requires uv absolute path |
| gitea | `/usr/local/bin/gitea-mcp` | Gitea MCP binary |
| chrome-devtools | `npx chrome-devtools-mcp@latest` | Requires DISPLAY=:2 |
| obsidian | `npx mcp-remote http://localhost:22360/sse` | Requires Obsidian running |
| cipher | `~/.npm-global/bin/cipher --mode mcp` | Encryption utility |

**Project-level servers** (Amplifier only, in `/opt/amplifier/.mcp.json`):

| Server | Command |
|--------|---------|
| playwright | `npx @playwright/mcp@latest` |
| context7 | `npx -y @upstash/context7-mcp` |
| deepwiki | HTTP: `https://mcp.deepwiki.com/mcp` |
| repomix | `npx -y repomix --mcp` |
| autocontext | Same as global (in template, may duplicate) |

**Dedup rule:** If a server is in global config, don't add to project config. Global = gitea, chrome-devtools, autocontext, obsidian, cipher. Project = only what's unique to this repo.

### Dependencies

```bash
# uv (Python package manager — required for Amplifier and AutoContext)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env

# Verify
uv --version           # installed at ~/.local/bin/uv
node --version          # v22.22.1
python3 --version       # 3.12.3
gitea-mcp --version     # v1.0
tea --version           # v0.12.0
```

### Setup After Cloning

```bash
cd /opt/amplifier
git pull origin main
source ~/.local/bin/env
uv sync
bash scripts/setup-platform-config.sh --force
```

### Adding Global MCP Servers

```bash
# Correct way (writes to ~/.claude.json):
claude mcp add <name> -s user -- <command> <args...>

# WRONG way (writes to ~/.claude/mcp.json — Claude Code doesn't read this for global):
# Editing ~/.claude/mcp.json directly
```

### AutoContext Installation

```bash
cd /opt
git clone https://github.com/greyhaven-ai/autocontext.git
cd autocontext/autocontext
source ~/.local/bin/env
uv sync --extra mcp
uv add 'mcp>=1.9.0,<1.16.0'  # Pin to avoid outputSchema issue

# Register globally
claude mcp add autocontext -s user -- /home/claude/.local/bin/uv run --directory /opt/autocontext/autocontext autoctx mcp-serve

# Add env var
python3 -c '
import json
f = "/home/claude/.claude.json"
d = json.load(open(f))
d["mcpServers"]["autocontext"]["env"] = {"AUTOCONTEXT_AGENT_PROVIDER": "anthropic"}
json.dump(d, open(f, "w"), indent=2)
'
```

### FuseCP-Specific Commands

`/fix-bugs` and `/test-verified` are Amplifier commands but they execute against the FuseCP project at `C:\claude\fusecp-enterprise` (Windows). They are NOT meant to run from the Linux machine — FuseCP runs on Windows Server with IIS, Exchange, AD, DNS, HyperV.

### Troubleshooting

| Issue | Fix |
|-------|-----|
| `uv: command not found` | `source ~/.local/bin/env` or use absolute path `/home/claude/.local/bin/uv` |
| AutoContext not showing in `claude mcp list` | Use `claude mcp add -s user`, not manual `~/.claude/mcp.json` edit |
| chrome-devtools needs display | Xvfb must be running on DISPLAY=:2 |
| episodic-memory fails to connect | Plugin may need reinstall: `claude /plugin install episodic-memory@superpowers-marketplace` |
| obsidian MCP fails | Obsidian SSE server must be running on port 22360 |
