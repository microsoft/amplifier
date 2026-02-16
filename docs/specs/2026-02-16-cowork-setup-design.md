# Design Spec: Claude Code + OpenCode/Gemini Cowork Setup

**Date:** 2026-02-16
**Status:** Approved
**Author:** Claude Code (Senior) + Gemini (Junior) brainstorm

## Problem

Claude Code (Opus 4.6) and OpenCode (Gemini 3 Flash) are now both installed on the same Windows Server 2025 machine. They need to collaborate on the same codebase without destroying each other's work, with clear role boundaries (Claude = senior/architect, Gemini = junior/implementer).

Previous setup had them on separate machines. The move to one machine introduces collision risks: concurrent file edits, deployment conflicts, config overlap, and memory pollution.

## Goal

Establish a safe, productive cowork environment where:
1. Claude creates plans and specs, reviews PRs, deploys and tests
2. Gemini executes plans on feature branches, creates PRs
3. Neither can damage the other's configuration or work
4. Knowledge flows between them via git-tracked shared files
5. Agent skills are available to both in their native format

## Architecture

### File System Layout

```
C:\claude\amplifier\                    # Shared git repo
├── .claude\                            # Claude ONLY (agents, commands, tools, skills)
├── ai_context\                         # Shared design philosophy (both read)
├── docs\                               # Shared specs & plans
├── COWORK.md                           # Collaboration protocol
├── HANDOFF.md                          # Task dispatch + state machine
├── DISCOVERIES.md                      # Shared learnings
└── AGENTS.md                           # Project guidelines

C:\Przemek\                             # Gemini/OpenCode workspace
├── OPENCODE.md                         # Gemini's identity + rules + boundaries
├── agents\                             # Agents in OpenCode SKILL.md format
│   ├── bug-hunter\SKILL.md
│   ├── agentic-search\SKILL.md
│   └── ... (all 30 agents)
├── memory\                             # Gemini's private session memory
└── scripts\                            # Gemini utilities
```

### Workflow State Machine

```
IDLE → WAITING_FOR_GEMINI → IN_PROGRESS → PR_READY → REVIEWING → DEPLOYING → IDLE
```

- Claude acts on: IDLE, PR_READY, REVIEWING, DEPLOYING
- Gemini acts on: WAITING_FOR_GEMINI (transitions to IN_PROGRESS)

### Branch Ownership

| Branch pattern | Owner | Purpose |
|----------------|-------|---------|
| main | Claude | Stable, deployed code |
| feature/* | Gemini | Implementation work |
| gemini/* | Gemini | Experimental/research |
| review/* | Claude | Review fixes before merge |
| hotfix/* | Claude | Emergency production fixes |

### Memory Layers

1. **Private**: Claude at `~/.claude/projects/*/memory/`, Gemini at `C:\Przemek\memory\`
2. **Shared Knowledge**: DISCOVERIES.md, HANDOFF.md, docs/decisions/ (git-tracked)
3. **Project Context**: AGENTS.md, COWORK.md, ai_context/ (Claude maintains, both read)

### Agent Tier System

All 30 agents synced with tier markings:

**Primary (Gemini uses freely):**
- agentic-search, bug-hunter, modular-builder, test-coverage, content-researcher, analysis-engine, post-task-cleanup, performance-optimizer

**Senior-Review (Gemini uses only when Claude assigns):**
- zen-architect, api-contract-designer, database-architect, security-guardian, contract-spec-author, subagent-architect, integration-specialist, module-intent-architect

**Design Specialists (typically Claude-only, available if assigned):**
- art-director, component-designer, design-system-architect, layout-architect, animation-choreographer, responsive-strategist, voice-strategist

**Knowledge/Analysis (Gemini uses freely for research):**
- amplifier-expert, concept-extractor, graph-builder, insight-synthesizer, knowledge-archaeologist, pattern-emergence, visualization-architect, ambiguity-guardian, amplifier-cli-architect

## Changes Required

### Deliverable 1: Create C:\Przemek\ structure + OPENCODE.md
- Create directory structure: agents/, memory/, scripts/
- Write OPENCODE.md with Gemini identity, rules, boundaries, workflow instructions
- Include cowork protocol, branch rules, safety boundaries

### Deliverable 2: Sync agents (.claude/agents/ → C:\Przemek\agents/)
- Read each of the 30 agents from .claude/agents/
- Convert to OpenCode SKILL.md format (directory per agent)
- Add YAML frontmatter: name, description, recommended_model, tools, tier
- Map Claude tiers to Gemini: haiku→flash, sonnet→flash, opus→pro
- Add tier marking: primary | senior-review | design-specialist | knowledge
- Add junior-dev boundary reminders to each agent

### Deliverable 3: Clean up repo
- Remove agents/ directory from repo root (was Gemini's first attempt)
- Remove skills/ directory from repo root (incorrect location)
- Ensure .gitignore excludes C:\Przemek\ artifacts if any leak in

### Deliverable 4: Update CLAUDE.md with cowork identity
- Add "Cowork Identity" section defining senior role
- Add boundary: never touch C:\Przemek\
- Add reference to HANDOFF.md state machine

### Deliverable 5: Update HANDOFF.md with structured format
- Replace current content with state machine format
- Add Dispatch Status field
- Add structured task template with file ownership lists
- Add Context Loading section for Gemini's 1M window

### Deliverable 6: Update COWORK.md with full protocol
- Expand with all rules from this design
- Add state machine diagram
- Add branch ownership table
- Add memory layer definitions
- Add agent tier system reference

### Deliverable 7: Create sync script
- PowerShell or bash script to re-sync agents when they change
- Reads .claude/agents/, converts format, writes to C:\Przemek\agents/
- Idempotent (safe to re-run)

### Deliverable 8: Gemini verification prompt
- A prompt the user pastes into OpenCode
- Gemini reads OPENCODE.md, tests agent loading, confirms boundaries
- Reports any issues back

## Impact

- **Files created**: OPENCODE.md, 30 agent SKILL.md files, sync script, memory dir
- **Files modified**: CLAUDE.md, HANDOFF.md, COWORK.md
- **Files deleted**: agents/ (repo root), skills/ (repo root)
- **No code changes** — this is infrastructure/configuration only

## Agent Allocation

| Phase | Agent | Responsibility |
|-------|-------|---------------|
| Research | agentic-search | Verify agent formats, find cleanup targets |
| Architecture review | zen-architect | Validate design before implementation |
| Implementation | modular-builder | Create files, sync agents, build scripts |
| Cleanup | post-task-cleanup | Remove stale files, verify repo hygiene |

## Test Plan

1. Verify C:\Przemek\ structure exists with all 30 agents in SKILL.md format
2. Verify agents/ and skills/ removed from repo root
3. Verify CLAUDE.md has cowork identity section
4. Verify HANDOFF.md has state machine format
5. Verify COWORK.md has full protocol
6. Verify sync script runs idempotently
7. User runs Gemini verification prompt — Gemini confirms config works
8. Do a test handoff: Claude writes task → Gemini picks up → creates branch → PR
