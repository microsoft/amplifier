# Amplifier Plugin Migration — Design Spec

## Problem

Amplifier is a monolith (36 agents, 35 commands, platform configs, project-specific content) in a single `.claude/` directory. This causes:
- No modularity — can't enable/disable subsets per project
- Not aligned with Claude Code plugin ecosystem (`/reload-plugins` doesn't work)
- Platform-specific content mixed with universal content
- Project-specific commands (fix-bugs, test-siem) loaded in all contexts

## Goal

Split Amplifier into a plugin-based architecture:
- `amplifier-core` — always loaded (agents, commands, routing matrix)
- `amplifier-windows` / `amplifier-linux` — auto-enabled by OS detection
- `amplifier-fusecp`, `amplifier-siem`, `amplifier-genetics` — enabled by `.amplifier-project` marker file
- All plugins in a single Gitea monorepo (`claude/amplifier-plugins`)
- Hot-reload via `/reload-plugins`

## Architecture

### Plugin Marketplace Repo
```
claude/amplifier-plugins/
├── install.sh / install.ps1
├── amplifier-core/
│   ├── .claude-plugin/plugin.json
│   ├── agents/ (36 agents)
│   ├── commands/ (35 commands minus project-specific)
│   ├── config/routing-matrix.yaml
│   ├── hooks/session-start.sh
│   ├── CLAUDE.md
│   └── AGENTS.md
├── amplifier-windows/
│   ├── .claude-plugin/plugin.json
│   ├── scripts/guard-paths.sh
│   └── CLAUDE.md (Windows paths, IIS, PowerShell)
├── amplifier-linux/
│   ├── .claude-plugin/plugin.json
│   ├── scripts/setup-platform-config.sh
│   └── CLAUDE.md (Linux paths, uv, chrome headless)
├── amplifier-fusecp/
│   ├── .claude-plugin/plugin.json
│   ├── agents/ (csharp-developer, dotnet-core-expert)
│   ├── commands/ (fix-bugs, test-verified)
│   ├── routing-overlay.yaml
│   └── CLAUDE.md (3 principles, deployment, Exchange)
├── amplifier-siem/
│   ├── .claude-plugin/plugin.json
│   ├── commands/ (test-siem)
│   └── CLAUDE.md
└── amplifier-genetics/
    ├── .claude-plugin/plugin.json
    └── CLAUDE.md
```

### Plugin Manifests
Each plugin has `.claude-plugin/plugin.json` declaring agents, commands, mcpServers, hooks. Version: date-based (YYYY.MM.DD).

### Session-Start Hook (amplifier-core)
1. Detect OS → enable amplifier-windows or amplifier-linux
2. Walk up from cwd (max 3 levels) looking for `.amplifier-project` file
3. If found, enable the named project plugin
4. Collect routing-overlay.yaml from all active plugins, merge into base routing-matrix.yaml
5. Write merged matrix to temp location for runtime use

### Routing Overlay System
Base routing-matrix.yaml in core defines 7 roles and default agent mappings. Project plugins provide routing-overlay.yaml:
```yaml
agents:
  csharp-developer: implement
  dotnet-core-expert: implement
```
Merge rules: new agents added, existing agents overridden, roles never removed.

### Project Marker File
Each project repo has `.amplifier-project` containing the plugin name:
```
amplifier-fusecp
```

### Installation
```bash
git clone https://gitea.ergonet.pl:3001/claude/amplifier-plugins.git \
    ~/.claude/plugins/cache/amplifier-marketplace/
# Register in ~/.claude/settings.json
```
Update: `git pull` + `/reload-plugins`

## Files Changed

| File | Action |
|------|--------|
| claude/amplifier-plugins (new repo) | Create — entire plugin marketplace |
| amplifier-core/.claude-plugin/plugin.json | Create — core manifest |
| amplifier-core/agents/*.md | Move from .claude/agents/ |
| amplifier-core/commands/*.md | Move from .claude/commands/ |
| amplifier-core/config/routing-matrix.yaml | Move from config/ |
| amplifier-core/CLAUDE.md | Extract platform-independent content |
| amplifier-core/AGENTS.md | Move as-is |
| amplifier-core/hooks/session-start.sh | Create — orchestrator |
| amplifier-windows/.claude-plugin/plugin.json | Create |
| amplifier-windows/CLAUDE.md | Extract Windows content |
| amplifier-linux/.claude-plugin/plugin.json | Create |
| amplifier-linux/CLAUDE.md | Extract Linux content |
| amplifier-fusecp/* | Create — project plugin |
| amplifier-siem/* | Create — project plugin |
| amplifier-genetics/* | Create — project plugin |
| install.sh, install.ps1 | Create — installers |
| .amplifier-project files | Create in each project repo |

## Agent Allocation

| Phase | Agent |
|-------|-------|
| Codebase Research | agentic-search |
| Plugin Scaffolding | modular-builder |
| Core Migration | modular-builder |
| Platform Split | modular-builder |
| Project Plugins | modular-builder |
| Session-Start Hook | modular-builder |
| Install Scripts | modular-builder |
| Verification | test-coverage |
| Cleanup | post-task-cleanup |

## Execution Waves

- Wave 1: Scaffold 6 plugin directories + plugin.json manifests
- Wave 2: Migrate core (agents, commands, config, CLAUDE.md, AGENTS.md)
- Wave 3 (parallel): Platform plugins + project plugins
- Wave 4: Session-start hook + overlay merge
- Wave 5: Install scripts + .amplifier-project markers
- Wave 6: Verification + cleanup

## Test Plan

- [ ] amplifier-core plugin.json is valid JSON with all agents/commands listed
- [ ] All 36 agents exist in amplifier-core/agents/
- [ ] All core commands exist in amplifier-core/commands/
- [ ] amplifier-windows/CLAUDE.md contains Windows-specific content only
- [ ] amplifier-linux/CLAUDE.md contains Linux-specific content only
- [ ] amplifier-fusecp has fix-bugs.md, test-verified.md, routing-overlay.yaml
- [ ] Session-start hook detects OS correctly
- [ ] Session-start hook reads .amplifier-project file
- [ ] Routing overlay merges new agents into base matrix
- [ ] install.sh clones repo to correct location
- [ ] /reload-plugins re-runs detection and merge
- [ ] No duplicate files between plugins
