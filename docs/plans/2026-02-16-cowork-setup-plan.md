# Cowork Setup Implementation Plan

> **For Claude:** REQUIRED: Use /subagent-dev (if subagents available) or /execute-plan to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish safe Claude Code + OpenCode/Gemini cowork on the same Windows Server 2025 machine with shared memory, role boundaries, and agent skills in both native formats.

**Architecture:** Sequential handoff workflow — Claude (senior) creates plans/reviews/deploys, Gemini (junior) implements on feature branches. Git branches as isolation. HANDOFF.md as state machine. Agent skills duplicated to each platform's native format with tier markings.

**Tech Stack:** Bash scripts, Markdown configuration files, YAML frontmatter, Git

**Spec:** `docs/specs/2026-02-16-cowork-setup-design.md`

---

## Chunk 1: Safety and Infrastructure

### Task 1: Emergency Safety Cleanup

**Agent:** post-task-cleanup

**Files:**
- Delete: `NUL` (repo root — Windows reserved name, CRITICAL)
- Delete: `pr8-diff.txt` (stale PR artifact, 6059 lines)
- Delete: `2026-02-11-read-this-file-cclaudeamplifier2026-02-11-this.txt`
- Delete: `2026-02-11-this-session-is-being-continued-from-a-previous-co.txt`
- Delete: `2026-02-13-this-session-is-being-continued-from-a-previous.txt`
- Delete: `docs/memory/SNAPSHOT.md` (Gemini artifact)

- [ ] **Step 1: Delete NUL file (CRITICAL — Windows reserved name)**

```bash
rm -f /c/claude/amplifier/NUL
```

Verify it's gone:
```bash
ls -la /c/claude/amplifier/NUL 2>&1 | grep "No such file"
```
Expected: "No such file or directory"

- [ ] **Step 2: Delete stale session artifacts**

```bash
rm -f "/c/claude/amplifier/2026-02-11-read-this-file-cclaudeamplifier2026-02-11-this.txt"
rm -f "/c/claude/amplifier/2026-02-11-this-session-is-being-continued-from-a-previous-co.txt"
rm -f "/c/claude/amplifier/2026-02-13-this-session-is-being-continued-from-a-previous.txt"
rm -f /c/claude/amplifier/pr8-diff.txt
rm -f /c/claude/amplifier/docs/memory/SNAPSHOT.md
```

- [ ] **Step 3: Verify cleanup**

```bash
ls /c/claude/amplifier/*.txt 2>/dev/null | wc -l
```
Expected: 0

- [ ] **Step 4: Commit safety cleanup**

```bash
cd /c/claude/amplifier
git add -A NUL pr8-diff.txt "2026-02-11-*" "2026-02-13-*" docs/memory/
git commit -m "fix: remove NUL reserved name file and stale artifacts

- Delete NUL (Windows reserved name — NTFS corruption risk)
- Delete stale session continuation artifacts
- Delete pr8-diff.txt (stale PR diff)
- Delete docs/memory/SNAPSHOT.md (Gemini artifact)"
```

---

### Task 2: Create Gemini Workspace Structure

**Agent:** modular-builder

**Files:**
- Create: `C:\Przemek\OPENCODE.md`
- Create: `C:\Przemek\agents\` (directory)
- Create: `C:\Przemek\memory\` (directory)
- Create: `C:\Przemek\scripts\` (directory)
- Create: `C:\Przemek\memory\.gitkeep`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p /c/Przemek/agents
mkdir -p /c/Przemek/memory
mkdir -p /c/Przemek/scripts
touch /c/Przemek/memory/.gitkeep
```

Verify:
```bash
ls -la /c/Przemek/
```
Expected: agents/, memory/, scripts/, OPENCODE_CONFIG_PLAN.md (existing)

- [ ] **Step 2: Write OPENCODE.md**

Create `C:\Przemek\OPENCODE.md` with complete Gemini identity, rules, and workflow protocol:

```markdown
# OPENCODE.md — Gemini/OpenCode Configuration

This file is your identity and rules. Read it at the start of every session.

## Your Identity

You are the **JUNIOR DEVELOPER** in a two-model cowork setup:
- **You (Gemini 3 Flash via OpenCode):** Implementation, testing, research, documentation
- **Claude Code (Opus 4.6):** Senior developer — architecture, planning, review, deployment

## Your Advantages

You have a 1M token context window. Use it deliberately:
- Load entire large files instead of chunking
- Hold spec + implementation + tests simultaneously
- Review full PR diffs with surrounding context
- Cross-reference multiple files at once

## Workspace Layout

```
C:\claude\amplifier\    # Shared git repo (you work here)
C:\Przemek\             # Your private workspace (config, memory, agents)
```

## Critical Rules (NEVER VIOLATE)

1. **NEVER modify `.claude/` directory** — that is Claude Code's territory
2. **NEVER deploy to IIS** — no `dotnet publish`, no `Stop-WebAppPool`, no `Start-WebAppPool`
3. **NEVER merge to main** — always create PRs, Claude reviews and merges
4. **NEVER modify CLAUDE.md** — propose changes via PR if needed
5. **NEVER run destructive git commands on main** — no `reset --hard`, no `push --force`
6. **NEVER touch `C:\FuseCP\`** — that's the production deployment directory

## Branch Rules

| Branch | Who | Purpose |
|--------|-----|---------|
| `main` | Claude ONLY | Stable, deployed |
| `feature/*` | YOU | Implementation work |
| `gemini/*` | YOU | Experimental/research |
| `review/*` | Claude | Review fixes |
| `hotfix/*` | Claude | Emergency fixes |

**Always start work with:**
```bash
git checkout main && git pull
git checkout -b feature/descriptive-name
```

## Workflow Protocol

### Starting a Session

1. `git checkout main && git pull` — get latest
2. Read `HANDOFF.md` — check current dispatch status
3. If status is `WAITING_FOR_GEMINI` — pick up the task
4. Read the task spec carefully, load all referenced files
5. Change status to `IN_PROGRESS`, commit to your feature branch

### Doing Work

1. Create feature branch from main
2. Implement according to the spec in HANDOFF.md
3. Write tests alongside implementation
4. Commit frequently with clear messages
5. Update DISCOVERIES.md if you find anything non-obvious

### Completing Work

1. Push your feature branch
2. Create a PR with clear description
3. Update HANDOFF.md: set status to `PR_READY`, add PR link
4. Commit HANDOFF.md change to main (this is the ONE exception — status updates only)
5. Stop working — Claude will review

### If You're Stuck

- Document what you tried in DISCOVERIES.md
- Update HANDOFF.md with status and blockers
- Do NOT try to fix architectural issues — flag them for Claude

## Agent Skills

Your agents are at `C:\Przemek\agents\`. Each has a SKILL.md with a tier marking:

| Tier | Meaning |
|------|---------|
| `primary` | Use freely for any task |
| `knowledge` | Use freely for research/analysis |
| `senior-review` | Use ONLY when Claude assigns it in HANDOFF.md |
| `design-specialist` | Use ONLY when Claude assigns it in HANDOFF.md |

## Shared Files (Read/Write via Git)

| File | Purpose | Your access |
|------|---------|-------------|
| `HANDOFF.md` | Task dispatch + status | Read + write status only |
| `DISCOVERIES.md` | Non-obvious findings | Read + write |
| `AGENTS.md` | Project guidelines | Read only |
| `COWORK.md` | Collaboration protocol | Read only |
| `ai_context/` | Design philosophy | Read only |
| `docs/` | Specs and plans | Read only (write via PR) |

## Commit Message Format

```
type: short description

Body explaining what and why.

🤖 Generated with OpenCode + Gemini 3 Flash
```

Types: feat, fix, test, docs, refactor, chore
```

- [ ] **Step 3: Verify OPENCODE.md is readable**

```bash
wc -l /c/Przemek/OPENCODE.md
```
Expected: ~120 lines

---

## Chunk 2: Agent Sync System

### Task 3: Create Agent Sync Script

**Agent:** modular-builder

**Files:**
- Create: `C:\Przemek\scripts\sync-agents.sh`

This script reads Claude Code agents from `.claude/agents/`, converts to OpenCode SKILL.md format, and writes to `C:\Przemek\agents\`. It is idempotent.

- [ ] **Step 1: Write the sync script**

Create `C:\Przemek\scripts\sync-agents.sh`:

```bash
#!/bin/bash
# sync-agents.sh — Sync Claude Code agents to OpenCode SKILL.md format
# Source: C:\claude\amplifier\.claude\agents\*.md
# Target: C:\Przemek\agents\<name>\SKILL.md
#
# Usage: bash /c/Przemek/scripts/sync-agents.sh
# Idempotent — safe to re-run.

set -euo pipefail

SOURCE_DIR="/c/claude/amplifier/.claude/agents"
TARGET_DIR="/c/Przemek/agents"

# Agent tier assignments (from design spec)
declare -A TIERS=(
  # Primary — Gemini uses freely
  ["agentic-search"]="primary"
  ["bug-hunter"]="primary"
  ["modular-builder"]="primary"
  ["test-coverage"]="primary"
  ["content-researcher"]="primary"
  ["analysis-engine"]="primary"
  ["post-task-cleanup"]="primary"
  ["performance-optimizer"]="primary"

  # Senior-Review — only when Claude assigns
  ["zen-architect"]="senior-review"
  ["api-contract-designer"]="senior-review"
  ["database-architect"]="senior-review"
  ["security-guardian"]="senior-review"
  ["contract-spec-author"]="senior-review"
  ["subagent-architect"]="senior-review"
  ["integration-specialist"]="senior-review"
  ["module-intent-architect"]="senior-review"

  # Design Specialist — typically Claude-only
  ["art-director"]="design-specialist"
  ["component-designer"]="design-specialist"
  ["design-system-architect"]="design-specialist"
  ["layout-architect"]="design-specialist"
  ["animation-choreographer"]="design-specialist"
  ["responsive-strategist"]="design-specialist"
  ["voice-strategist"]="design-specialist"

  # Knowledge — Gemini uses freely for research
  ["amplifier-expert"]="knowledge"
  ["amplifier-cli-architect"]="knowledge"
  ["concept-extractor"]="knowledge"
  ["graph-builder"]="knowledge"
  ["insight-synthesizer"]="knowledge"
  ["knowledge-archaeologist"]="knowledge"
  ["pattern-emergence"]="knowledge"
  ["visualization-architect"]="knowledge"
  ["ambiguity-guardian"]="knowledge"
)

# Model mapping: tier → recommended_model for Gemini
declare -A MODEL_MAP=(
  ["primary"]="flash"
  ["senior-review"]="pro"
  ["design-specialist"]="pro"
  ["knowledge"]="flash"
)

# Boundary reminder for junior dev agents
JUNIOR_REMINDER='

## Cowork Boundaries (ALWAYS ENFORCE)

You are operating as a JUNIOR DEVELOPER agent under Gemini/OpenCode.
- NEVER suggest modifying `.claude/` directory
- NEVER suggest deploying to IIS or touching `C:\FuseCP\`
- NEVER suggest merging to main or force-pushing
- If a task requires senior-level decisions, flag it and stop
- Always work on feature/* or gemini/* branches'

SYNCED=0
SKIPPED=0

echo "=== Agent Sync: .claude/agents/ → C:\\Przemek\\agents/ ==="
echo ""

for agent_file in "$SOURCE_DIR"/*.md; do
  [ -f "$agent_file" ] || continue

  filename=$(basename "$agent_file" .md)
  agent_dir="$TARGET_DIR/$filename"
  skill_file="$agent_dir/SKILL.md"

  # Get tier (default to knowledge if not mapped)
  tier="${TIERS[$filename]:-knowledge}"
  model="${MODEL_MAP[$tier]:-flash}"

  # Read the source agent file
  content=$(cat "$agent_file")

  # Check if file has YAML frontmatter (starts with ---)
  if [[ "$content" == ---* ]]; then
    # Extract frontmatter and body
    frontmatter=$(echo "$content" | sed -n '1,/^---$/p' | tail -n +2 | head -n -1)
    body=$(echo "$content" | sed '1,/^---$/{ /^---$/!d; /^---$/d; }' | sed '1,/^---$/d')

    # Check if recommended_model already exists in frontmatter
    if echo "$frontmatter" | grep -q "^recommended_model:"; then
      new_frontmatter="$frontmatter"
    else
      new_frontmatter="recommended_model: $model
$frontmatter"
    fi

    # Add tier field if not present
    if ! echo "$new_frontmatter" | grep -q "^tier:"; then
      new_frontmatter="$new_frontmatter
tier: $tier"
    fi
  else
    # No frontmatter — create one
    new_frontmatter="recommended_model: $model
name: $filename
description: Agent $filename (imported from Claude Code)
tier: $tier"
    body="$content"
  fi

  # Assemble the SKILL.md
  mkdir -p "$agent_dir"
  {
    echo "---"
    echo "$new_frontmatter"
    echo "---"
    echo "$body"
    echo "$JUNIOR_REMINDER"
  } > "$skill_file"

  echo "  [OK] $filename (tier: $tier, model: $model)"
  ((SYNCED++))
done

echo ""
echo "=== Sync complete: $SYNCED agents synced ==="
echo "=== Target: $TARGET_DIR ==="
```

- [ ] **Step 2: Make script executable and test**

```bash
chmod +x /c/Przemek/scripts/sync-agents.sh
bash /c/Przemek/scripts/sync-agents.sh
```

Expected: ~30 lines of `[OK] agent-name (tier: ..., model: ...)` and final count.

- [ ] **Step 3: Verify output**

```bash
ls /c/Przemek/agents/ | wc -l
```
Expected: 30+ directories

```bash
head -20 /c/Przemek/agents/bug-hunter/SKILL.md
```
Expected: YAML frontmatter with `recommended_model: flash`, `tier: primary`, then prompt body.

```bash
tail -10 /c/Przemek/agents/bug-hunter/SKILL.md
```
Expected: Ends with the "Cowork Boundaries" junior dev reminder section.

- [ ] **Step 4: Verify tier distribution**

```bash
grep -r "^tier:" /c/Przemek/agents/*/SKILL.md | sed 's/.*tier: //' | sort | uniq -c | sort -rn
```
Expected:
```
  9 knowledge
  8 primary
  8 senior-review
  7 design-specialist
```
(Approximate — totals should be ~30-32)

---

### Task 4: Execute Agent Sync and Validate

**Agent:** modular-builder

**Files:**
- Create: 30+ files at `C:\Przemek\agents\<name>\SKILL.md`

- [ ] **Step 1: Run the sync script**

```bash
bash /c/Przemek/scripts/sync-agents.sh
```

- [ ] **Step 2: Spot-check 3 agents across different tiers**

Check a primary agent:
```bash
head -8 /c/Przemek/agents/agentic-search/SKILL.md
```
Expected: `recommended_model: flash`, `tier: primary`

Check a senior-review agent:
```bash
head -8 /c/Przemek/agents/zen-architect/SKILL.md
```
Expected: `recommended_model: pro`, `tier: senior-review`

Check a knowledge agent:
```bash
head -8 /c/Przemek/agents/amplifier-expert/SKILL.md
```
Expected: `recommended_model: flash`, `tier: knowledge`

- [ ] **Step 3: Verify junior boundary reminder is appended**

```bash
grep -l "Cowork Boundaries" /c/Przemek/agents/*/SKILL.md | wc -l
```
Expected: Same count as total agents (every agent has the reminder)

---

## Chunk 3: Repo Configuration Updates

### Task 5: Update CLAUDE.md with Cowork Identity

**Agent:** modular-builder

**Files:**
- Modify: `C:\claude\amplifier\CLAUDE.md` (append after line ~172, the "Amplifier Commands" section)

- [ ] **Step 1: Read current end of CLAUDE.md to find insertion point**

Read `CLAUDE.md` and locate the "Amplifier Commands" section (near the end). The cowork identity section goes immediately after it.

- [ ] **Step 2: Append cowork identity section**

Add the following after the Amplifier Commands section at the end of CLAUDE.md:

```markdown

## Cowork Identity — Senior Developer

You are the **SENIOR DEVELOPER** in a two-model cowork setup on this Windows Server 2025 machine.

### Your Partner
- **Gemini 3 Flash** via OpenCode — junior developer with 1M context window
- Gemini's config: `C:\Przemek\OPENCODE.md`
- Gemini's agents: `C:\Przemek\agents\`

### Your Responsibilities
- Create plans and write specs
- Dispatch tasks via HANDOFF.md
- Review Gemini's PRs (feature/* branches)
- Deploy to local server and run tests
- Maintain COWORK.md, AGENTS.md, ai_context/

### Boundaries
- **NEVER touch `C:\Przemek\`** — that is Gemini's workspace
- **NEVER modify Gemini's agents** directly — use the sync script at `C:\Przemek\scripts\sync-agents.sh`

### Task Dispatch Protocol
See `HANDOFF.md` for the state machine. You write tasks when status is IDLE, review when PR_READY.

### Agent Sync
When you update agents in `.claude/agents/`, re-sync to Gemini format:
```bash
bash /c/Przemek/scripts/sync-agents.sh
```
```

- [ ] **Step 3: Verify the addition**

```bash
grep -c "Cowork Identity" /c/claude/amplifier/CLAUDE.md
```
Expected: 1

- [ ] **Step 4: Commit**

```bash
cd /c/claude/amplifier
git add CLAUDE.md
git commit -m "docs: add cowork identity section to CLAUDE.md

Defines senior developer role, boundaries with Gemini workspace,
and task dispatch protocol reference."
```

---

### Task 6: Update HANDOFF.md with State Machine Format

**Agent:** modular-builder

**Files:**
- Modify: `C:\claude\amplifier\HANDOFF.md` (full rewrite)

- [ ] **Step 1: Rewrite HANDOFF.md with structured format**

Replace entire contents of `HANDOFF.md` with:

```markdown
# Amplifier Cowork — Task Handoff

## Dispatch Status: IDLE

> **Protocol:** Only the designated receiver should act.
> - Claude acts on: `IDLE`, `PR_READY`, `REVIEWING`, `DEPLOYING`
> - Gemini acts on: `WAITING_FOR_GEMINI`

## State Transitions

```
IDLE ──(Claude writes task)──→ WAITING_FOR_GEMINI
WAITING_FOR_GEMINI ──(Gemini starts)──→ IN_PROGRESS
IN_PROGRESS ──(Gemini pushes PR)──→ PR_READY
PR_READY ──(Claude reviews)──→ REVIEWING
REVIEWING ──(Claude merges/deploys)──→ DEPLOYING
DEPLOYING ──(Claude tests pass)──→ IDLE
```

---

## Current Task

_No active task. Claude: write a task below and set status to WAITING_FOR_GEMINI._

### Task Template (copy when dispatching)

```markdown
## Current Task

**From:** Claude → Gemini
**Branch:** feature/<name>
**Priority:** normal | urgent

### Objective
[One sentence: what to build/fix/change]

### Spec
[Inline spec or link to docs/specs/...]

### Context Loading (use your full 1M context)
Load these files completely before starting:
- [file1 — full file]
- [file2 — full file]
- [file3 — lines X-Y]

### Files YOU May Modify
- [exact/path/to/file1.ext]
- [exact/path/to/file2.ext]

### Files You Must NOT Modify
- .claude/* (always)
- CLAUDE.md (always)
- [any other protected files]

### Acceptance Criteria
- [ ] [testable criterion 1]
- [ ] [testable criterion 2]

### Agent Tier Unlocks
[List any senior-review or design-specialist agents Gemini may use for this task, or "primary + knowledge only"]
```

---

## History

| Date | Direction | Task | PR | Result |
|------|-----------|------|-----|--------|
| 2026-02-16 | Gemini → Claude | Initial cowork setup | — | Agents synced, protocol established |
```

- [ ] **Step 2: Verify structure**

```bash
head -5 /c/claude/amplifier/HANDOFF.md
```
Expected: Title + `## Dispatch Status: IDLE`

- [ ] **Step 3: Commit**

```bash
cd /c/claude/amplifier
git add HANDOFF.md
git commit -m "docs: restructure HANDOFF.md with state machine protocol

Replaces simple log with structured dispatch format:
- Status field (IDLE/WAITING_FOR_GEMINI/IN_PROGRESS/PR_READY/REVIEWING/DEPLOYING)
- Task template with file ownership, context loading hints, acceptance criteria
- History table for audit trail"
```

---

### Task 7: Update COWORK.md with Full Protocol

**Agent:** modular-builder

**Files:**
- Modify: `C:\claude\amplifier\COWORK.md` (full rewrite)

- [ ] **Step 1: Rewrite COWORK.md with complete protocol**

Replace entire contents of `COWORK.md` with:

```markdown
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
```

- [ ] **Step 2: Verify**

```bash
wc -l /c/claude/amplifier/COWORK.md
```
Expected: ~130 lines

- [ ] **Step 3: Commit**

```bash
cd /c/claude/amplifier
git add COWORK.md
git commit -m "docs: rewrite COWORK.md with full cowork protocol

Complete protocol covering: roles, workspace separation, branch ownership,
workflow state machine, communication channels, memory architecture,
agent tier system, safety boundaries, and agent sync process."
```

---

## Chunk 4: Cleanup and Verification

### Task 8: Clean Up Repo Root

**Agent:** post-task-cleanup

**Files:**
- Delete: `agents/` directory at repo root (32 subdirectories — Gemini's first attempt, now at C:\Przemek)
- Delete: `skills/` directory at repo root (incorrect location)
- Modify: `.gitignore` (ensure cleanup)

- [ ] **Step 1: Remove agents/ from repo root**

```bash
rm -rf /c/claude/amplifier/agents
```

Verify:
```bash
ls /c/claude/amplifier/agents 2>&1
```
Expected: "No such file or directory"

- [ ] **Step 2: Remove skills/ from repo root**

```bash
rm -rf /c/claude/amplifier/skills
```

- [ ] **Step 3: Update .gitignore if needed**

Check current .gitignore and ensure these patterns are not tracked:
```bash
cat /c/claude/amplifier/.gitignore
```

If `agents/` or `skills/` are not already ignored, no action needed — they're just being deleted, not ignored (they shouldn't come back since Gemini won't create them in the repo anymore).

- [ ] **Step 4: Commit cleanup**

```bash
cd /c/claude/amplifier
git add -A agents/ skills/
git commit -m "chore: remove agents/ and skills/ from repo root

These were Gemini's first attempt at OpenCode agent storage.
Agents now live at C:\Przemek\agents\ (outside the repo).
Source of truth remains .claude/agents/ (Claude Code format)."
```

---

### Task 9: Update TODO.md

**Agent:** modular-builder

**Files:**
- Modify: `C:\claude\amplifier\TODO.md`

- [ ] **Step 1: Rewrite TODO.md to reflect completed setup**

Replace contents with current state:

```markdown
# Amplifier Project — Master TODO

## Cowork Setup (2026-02-16)
- [x] Install OpenCode + Gemini 3 Flash on same machine
- [x] Establish cowork protocol (COWORK.md)
- [x] Setup handoff mechanism (HANDOFF.md with state machine)
- [x] Create Gemini workspace (C:\Przemek\)
- [x] Write OPENCODE.md (Gemini identity + boundaries)
- [x] Sync agents to OpenCode format with tier system
- [x] Create agent sync script
- [x] Update CLAUDE.md with senior dev identity
- [x] Clean up repo root (remove stale agents/, skills/, NUL)
- [ ] Run Gemini verification prompt
- [ ] Execute first test handoff (Claude → Gemini → PR → Claude review)

## Infrastructure
- [ ] Migrate remaining superpowers skills to native Amplifier commands
- [ ] Optimize context window management strategies per model
- [ ] Benchmark Gemini vs Claude on specific task types

## Ongoing
- [ ] Keep DISCOVERIES.md updated with cross-model learnings
- [ ] Refine agent tier assignments based on actual performance
- [ ] Tune HANDOFF.md template based on real usage
```

- [ ] **Step 2: Commit**

```bash
cd /c/claude/amplifier
git add TODO.md
git commit -m "docs: update TODO.md with cowork setup progress"
```

---

### Task 10: Create Gemini Verification Prompt

**Agent:** modular-builder

**Files:**
- Create: `C:\Przemek\VERIFY.md` (verification prompt for user to paste into OpenCode)

- [ ] **Step 1: Write the verification prompt**

Create `C:\Przemek\VERIFY.md`:

```markdown
# Gemini Verification Prompt

Paste the following into OpenCode to verify the cowork setup.

---

## Prompt (copy everything below this line)

You are Gemini, the junior developer in a cowork setup with Claude Code (senior).
Your configuration has just been set up by Claude. Please verify everything works.

### Step 1: Read Your Identity
Read `C:\Przemek\OPENCODE.md` completely. Confirm:
- [ ] You understand your role as junior developer
- [ ] You understand the 6 critical rules (what you must NEVER do)
- [ ] You understand the branch rules
- [ ] You understand the workflow protocol

### Step 2: Check Your Agents
List all directories in `C:\Przemek\agents\`. For each, read the first 8 lines of SKILL.md.
Report:
- Total agent count
- Count by tier (primary, senior-review, design-specialist, knowledge)
- Any agents missing frontmatter or with format issues

### Step 3: Read Shared Protocol
Read these files from `C:\claude\amplifier\`:
- `COWORK.md` — confirm you understand the protocol
- `HANDOFF.md` — confirm you see IDLE status and the task template
- `AGENTS.md` — confirm you can read project guidelines

### Step 4: Verify Boundaries
Confirm you understand these boundaries by listing them:
- Which directories you must NEVER modify
- Which branches you may use
- What deployment actions are forbidden

### Step 5: Test Branch Workflow
```bash
cd C:\claude\amplifier
git checkout main
git pull
git checkout -b gemini/verification-test
echo "# Gemini verification test - $(date)" > /tmp/gemini-verify.txt
git checkout main
git branch -D gemini/verification-test
```
Confirm: branch created and deleted cleanly.

### Step 6: Report
Provide a summary:
```
VERIFICATION REPORT
==================
Identity loaded:     [YES/NO]
Agents found:        [count] ([count by tier])
Shared files read:   [YES/NO]
Boundaries understood: [YES/NO]
Branch workflow:     [PASS/FAIL]
Issues found:        [list or NONE]

Ready for first task: [YES/NO]
```
```

- [ ] **Step 2: Verify file exists**

```bash
wc -l /c/Przemek/VERIFY.md
```
Expected: ~65 lines

---

### Task 11: Final Verification

**Agent:** test-coverage

**Files:**
- Read-only verification of all deliverables

- [ ] **Step 1: Verify C:\Przemek\ structure**

```bash
find /c/Przemek -type f | sort
```
Expected: OPENCODE.md, OPENCODE_CONFIG_PLAN.md, VERIFY.md, memory/.gitkeep, scripts/sync-agents.sh, agents/*/SKILL.md (30+ files)

- [ ] **Step 2: Verify repo root is clean**

```bash
ls /c/claude/amplifier/agents 2>&1 | grep -c "No such"
ls /c/claude/amplifier/skills 2>&1 | grep -c "No such"
ls /c/claude/amplifier/NUL 2>&1 | grep -c "No such"
```
Expected: 1 for each (all deleted)

- [ ] **Step 3: Verify CLAUDE.md has cowork section**

```bash
grep "Cowork Identity" /c/claude/amplifier/CLAUDE.md
```
Expected: "## Cowork Identity — Senior Developer"

- [ ] **Step 4: Verify HANDOFF.md has state machine**

```bash
grep "Dispatch Status" /c/claude/amplifier/HANDOFF.md
```
Expected: "## Dispatch Status: IDLE"

- [ ] **Step 5: Verify COWORK.md has full protocol**

```bash
grep -c "##" /c/claude/amplifier/COWORK.md
```
Expected: 10+ section headers

- [ ] **Step 6: Verify agent tier coverage**

```bash
grep -r "^tier:" /c/Przemek/agents/*/SKILL.md | wc -l
```
Expected: 30+ (every agent has a tier)

- [ ] **Step 7: Verify sync script is idempotent — run it again**

```bash
bash /c/Przemek/scripts/sync-agents.sh
```
Expected: Same output, no errors, same file count

- [ ] **Step 8: Git status check — everything committed**

```bash
cd /c/claude/amplifier && git status --short
```
Expected: Only untracked files that are intentionally not tracked (docs/specs, docs/plans). No modified tracked files.

- [ ] **Step 9: Final commit for spec + plan docs**

```bash
cd /c/claude/amplifier
git add docs/specs/2026-02-16-cowork-setup-design.md docs/plans/2026-02-16-cowork-setup-plan.md
git commit -m "docs: add cowork setup design spec and implementation plan"
```
