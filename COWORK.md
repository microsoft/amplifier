# Amplifier Cowork Protocol

This document defines how **Claude Code (Senior)** and **Gemini via OpenCode (Junior)** collaborate on the same machine.

## Roles

| Role | Platform | Model | Strengths |
|------|----------|-------|-----------|
| **Senior Developer** | Claude Code | Opus 4.6 | Architecture, planning, review, deployment, complex reasoning |
| **Junior Developer** | OpenCode | Gemini 3 Flash | Implementation, large context (1M tokens), fast iteration, research |

## Workspace Separation

| Path | Owner | Purpose |
|------|-------|---------|
| `C:\claude\amplifier\` | Shared (git repo) | Source of truth for all code |
| `C:\claude\amplifier\.claude\` | Claude ONLY | Agents, commands, tools, skills |
| `C:\Przemek\` | Gemini ONLY | OPENCODE.md, agents (SKILL.md format), private memory |

## Branch Ownership

| Pattern | Owner | Purpose |
|---------|-------|---------|
| `main` | Claude | Stable, deployed code |
| `feature/*` | Gemini | Implementation tasks |
| `gemini/*` | Gemini | Experimental/research |
| `review/*` | Claude | Review fixes before merge |
| `hotfix/*` | Claude | Emergency production fixes |

**Rule:** Neither modifies the other's branch namespace. Gemini NEVER commits to main (except HANDOFF.md status updates).

## Workflow

```
Claude: Plan → HANDOFF.md (WAITING_FOR_GEMINI) → wait
Gemini: Read task → feature branch → implement → PR (PR_READY) → wait
Claude: Review PR → fix issues → merge → deploy → test (IDLE)
```

See `HANDOFF.md` for the full state machine and task template.

## Communication

| Channel | Purpose | Format |
|---------|---------|--------|
| `HANDOFF.md` | Task dispatch + status | State machine with structured template |
| `DISCOVERIES.md` | Non-obvious findings | Dated entries with Issue/Solution/Prevention |
| GitHub PR | Code review | Standard PR review workflow |
| `docs/decisions/` | Architectural decisions | ADR format |

## Memory Architecture

### Layer 1: Private Memory
- **Claude:** `~/.claude/projects/C--claude-amplifier/memory/` (episodic, auto-synced)
- **Gemini:** `C:\Przemek\memory\` (session notes)

Neither reads the other's private memory.

### Layer 2: Shared Knowledge (git-tracked)
- `DISCOVERIES.md` — tool quirks, gotchas, non-obvious findings
- `HANDOFF.md` — active task state + context
- `docs/decisions/` — architectural decision records

Both commit to these via the branch workflow.

### Layer 3: Project Context (Claude maintains, both read)
- `AGENTS.md` — project guidelines
- `COWORK.md` — this file
- `ai_context/` — design philosophy docs
- `.claude/AGENTS_CATALOG.md` — agent reference

## Agent Tier System

All agents are available to both platforms. Gemini's copies include tier markings:

| Tier | Access | Agents |
|------|--------|--------|
| `primary` | Gemini uses freely | agentic-search, bug-hunter, modular-builder, test-coverage, content-researcher, analysis-engine, post-task-cleanup, performance-optimizer |
| `knowledge` | Gemini uses freely | amplifier-expert, concept-extractor, graph-builder, insight-synthesizer, knowledge-archaeologist, pattern-emergence, visualization-architect, ambiguity-guardian, amplifier-cli-architect |
| `senior-review` | Only when Claude assigns | zen-architect, api-contract-designer, database-architect, security-guardian, contract-spec-author, subagent-architect, integration-specialist, module-intent-architect |
| `design-specialist` | Only when Claude assigns | art-director, component-designer, design-system-architect, layout-architect, animation-choreographer, responsive-strategist, voice-strategist |

Claude unlocks senior-review or design-specialist agents per-task in HANDOFF.md under "Agent Tier Unlocks".

## Safety Boundaries

### Gemini Must NEVER:
- Modify `.claude/` directory
- Deploy to IIS (`dotnet publish`, `Stop-WebAppPool`, etc.)
- Merge to main or force-push
- Modify CLAUDE.md directly
- Touch `C:\FuseCP\` (production deployment)

### Claude Must NEVER:
- Modify `C:\Przemek\` directly (use sync script for agents)

### Both Must:
- Read HANDOFF.md before starting work
- Commit frequently with clear messages
- Document non-obvious findings in DISCOVERIES.md
- Use git branches — never edit uncommitted shared files

## Agent Sync Process

Source of truth: `.claude/agents/*.md` (Claude Code format)
Gemini copies: `C:\Przemek\agents\<name>\SKILL.md` (OpenCode format)

When Claude updates agents:
```bash
bash /c/Przemek/scripts/sync-agents.sh
```

This converts format, adds `recommended_model`, `tier` marking, and junior-dev boundary reminders.
