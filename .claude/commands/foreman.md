---
description: "Manage persistent sub-assistant fleet. Sub-assistants maintain context across dispatches for multi-phase feature work."
---

# Foreman — Persistent Sub-Assistant Fleet

## Overview

Foreman manages a fleet of sub-assistants that maintain state across multiple dispatches. Unlike `/parallel-agents` (one-shot), Foreman sub-assistants accumulate context — completed work, decisions, and in-progress state — between turns.

**Announce at start:** "Foreman: <subcommand> on <project>."

## Usage

```
/foreman start <spec-path>    — Create fleet from spec's agent allocation
/foreman status               — Show fleet state
/foreman dispatch <name>      — Dispatch one sub-assistant with accumulated context
/foreman dispatch all         — Dispatch all idle sub-assistants in parallel
/foreman stop                 — Archive fleet, clean up session files
```

## Arguments

$ARGUMENTS

## The Process

### Parse Subcommand

Extract subcommand and arguments from `$ARGUMENTS`:
- First word = subcommand (`start`, `status`, `dispatch`, `stop`)
- Remaining = arguments (spec path, agent name, or "all")

---

### Subcommand: `start <spec-path>`

**1. Read the spec:**
```bash
cat <spec-path>
```

Extract the Agent Allocation table from the spec.

**2. Read the routing matrix for model resolution:**
```bash
cat config/routing-matrix.yaml
```

**3. Create fleet directory:**
```bash
mkdir -p .foreman/sessions
```

**4. Generate fleet manifest (`.foreman/fleet.yaml`):**

For each agent in the allocation table, create an entry:

```yaml
project: "<branch-name or spec topic>"
created: "<ISO timestamp>"
spec: "<spec-path>"

assistants:
  <task-name>:
    role: <role from routing-matrix>
    scope: "<files or area from spec>"
    agent_type: <agent from allocation table>
    model: <resolved from routing-matrix via role>
    status: idle
    last_dispatch: null
    context_file: sessions/<task-name>.md
```

**5. Initialize session files:**

For each assistant, create `sessions/<task-name>.md`:

```markdown
# <task-name> session context

## Assignment
<responsibility from agent allocation table>

## Scope
<files from spec>

## Completed
(none yet)

## In Progress
(none yet)

## Key Decisions
(none yet)
```

**6. Report:**
```
Fleet created with N sub-assistants:
- <name>: <agent_type> (model: <model>) — <scope>
...
Ready. Use `/foreman dispatch <name>` or `/foreman dispatch all`.
```

---

### Subcommand: `status`

**1. Read fleet state:**
```bash
cat .foreman/fleet.yaml
```

**2. For each assistant, read session context:**
```bash
cat .foreman/sessions/<name>.md
```

**3. Report:**
```
Fleet: <project> (created <date>)

| Assistant | Agent | Model | Status | Completed | In Progress |
|-----------|-------|-------|--------|-----------|-------------|
| <name>    | <type>| <model>| <status>| N items  | N items     |
...
```

---

### Subcommand: `dispatch <name>` or `dispatch all`

**For each assistant to dispatch:**

**1. Read fleet.yaml and session context:**
```bash
cat .foreman/fleet.yaml
cat .foreman/sessions/<name>.md
```

**2. Update status to `working`** in fleet.yaml.

**3. Resolve effort and turns** from routing matrix:
- Look up agent's role in `config/routing-matrix.yaml` → get model, effort, turns range
- Score task complexity: count files in scope, check for security/migration keywords, check retry state
- Map score to effort: ≤0 → low (min turns) | 1-2 → medium (default turns) | ≥3 → high (max turns)
- Cap by session `/effort` setting

**4. Dispatch agent via Task tool:**

```
Task(
  subagent_type="<agent_type>",
  model="<model>",
  max_turns=<resolved from effort + turns range>,
  description="Foreman: <name> — <assignment>",
  prompt="
    You are a Foreman sub-assistant. You maintain persistent context across dispatches.

    ## Your Assignment
    <from session context file>

    ## Your Accumulated Context
    <full contents of sessions/<name>.md>

    ## Spec Reference
    <relevant section from the spec>

    ## Instructions
    1. Review your accumulated context — pick up where you left off
    2. Work on the next incomplete item
    3. When done, output a structured update:

    ### FOREMAN_UPDATE
    #### Completed This Turn
    - [items completed]

    #### Still In Progress
    - [items still pending]

    #### Key Decisions Made
    - [any decisions worth preserving]

    #### Blockers
    - [anything blocking progress, or 'none']
  "
)
```

**For `dispatch all`:** Send ALL dispatch Task calls in a single message (parallel execution).

**4. Process agent response:**

Parse the `FOREMAN_UPDATE` section from the agent's response.

**5. Update session context file** (`sessions/<name>.md`):
- Move completed items to `## Completed` with checkmarks
- Update `## In Progress` with remaining items
- Append new decisions to `## Key Decisions`

**6. Update fleet.yaml:**
- Set status back to `idle` (or `blocked` if blockers reported)
- Update `last_dispatch` timestamp

**7. Report results:**
```
Dispatched: <name> (<agent_type>, model: <model>)
Completed: N items
Remaining: N items
Blockers: <any or none>
```

---

### Subcommand: `stop`

**1. Read fleet state:**
```bash
cat .foreman/fleet.yaml
```

**2. Archive fleet** (move to timestamped directory):
```bash
mv .foreman .foreman-archive-$(date +%Y%m%d-%H%M%S)
```

**3. Report:**
```
Fleet archived. Sub-assistant sessions preserved in .foreman-archive-<timestamp>/.
```

---

## Integration

**Pairs with:**
- `/create-plan` — Plan's agent allocation seeds the fleet manifest
- `/finish-branch` — Run after foreman fleet completes all work
- `config/routing-matrix.yaml` — Model resolution for sub-assistants

**Uses:**
- Task tool for all agent dispatches
- File-based state (`.foreman/`) — no external dependencies

## Common Mistakes

**Dispatching without reading context**
- Fix: Always inject full session context into agent prompt

**Not updating session files after dispatch**
- Fix: Parse FOREMAN_UPDATE and update session files immediately

**Dispatching a `blocked` assistant**
- Fix: Check status before dispatch, resolve blockers first

## Red Flags

**Never:**
- Dispatch all agents without checking for blockers first
- Delete `.foreman/` without archiving — use `stop` subcommand
- Modify session files manually while an agent is `working`

**Always:**
- Read session context before every dispatch
- Update session files after every dispatch
- Use routing-matrix for model resolution
