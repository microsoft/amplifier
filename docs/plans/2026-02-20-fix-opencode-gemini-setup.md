# Fix OpenCode/Gemini Agent Setup Implementation Plan

> **For Claude:** REQUIRED: Use /subagent-dev (if subagents available) or /execute-plan to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the broken OpenCode agent architecture so Gemini can actually use agents and execute the handoff workflow.

**Architecture:** Replace the non-functional 34-agent mirror with a focused setup that works within OpenCode's actual constraints: custom commands for structured workflows, proper built-in agent config, and acknowledgment that OpenCode subagents are read-only.

**Tech Stack:** OpenCode JSON config, Markdown custom commands, Bash (sync script).

---

## Root Cause Analysis

Investigation revealed **5 critical problems** explaining why "agents do nothing":

### Problem 1: `~/.config/opencode/agents/` Is Not Loaded by OpenCode

OpenCode has NO concept of an `agents/` directory. The 34 markdown files sitting in `~/.config/opencode/agents/` are **completely orphaned** — OpenCode never reads them. Agent configurations in OpenCode go in `opencode.json` under the `"agents"` key, which only supports 4 built-in agent types: `coder`, `task`, `title`, `summarizer`.

### Problem 2: OpenCode Subagents (TaskAgent) Are READ-ONLY

When Gemini dispatches a subagent via the `agent` tool (displayed as "Task" in UI), that subagent only gets: **Glob, Grep, LS, View**. No Write. No Edit. No Bash. So when OPENCODE.md tells Gemini to "dispatch modular-builder as a subagent", modular-builder literally cannot write code because it has no file editing tools.

### Problem 3: OPENCODE.md Instructs Broken Workflow

OPENCODE.md lines 98-120 say "you MUST delegate implementation work to your specialized agents." This is impossible because those subagents can't write files. Gemini tries, agents can only search/read, and nothing gets implemented.

### Problem 4: Tool Name Mismatch

Agent prompts reference Claude Code tool names (`Read`, `Write`, `Edit`) but OpenCode uses different names (`view`, `write`, `edit`). The capitalization and API differ.

### Problem 5: Agent Frontmatter Is Ignored

The `mode: subagent`, `model: google/gemini-3-flash-preview` frontmatter in agent files is a format our sync script generates, but OpenCode doesn't parse frontmatter from agent files at all. These fields have no effect.

### Correct Architecture for OpenCode

| Feature | Claude Code | OpenCode |
|---------|------------|----------|
| Agent definitions | `.claude/agents/*.md` with frontmatter | `opencode.json` `"agents"` key (4 types only) |
| Subagent tools | Full access (configurable) | **Read-only**: Glob, Grep, LS, View |
| Custom workflows | `.claude/commands/*.md` (slash commands) | `~/.config/opencode/commands/*.md` or `.opencode/commands/*.md` |
| Model selection | `model` param on Task tool | Not per-dispatch; set in `opencode.json` per agent type |
| Context files | CLAUDE.md (@imports) | `"instructions"` array in opencode.json |

**Key design decision:** Implementation work MUST happen in the main coder agent context (which has full tools), NOT in subagents. Subagents are only useful for research/search tasks.

---

## Task 0: Confirm Findings on Live System

**Agent:** agentic-search

**Question:** Verify the 5 root causes by checking the live OpenCode installation. Confirm: (1) Are the 34 agent files in `~/.config/opencode/agents/` actually loaded? (2) Does the `agent` tool really give only read-only tools? (3) Is the `instructions` array the only way to inject context? (4) Does OpenCode recognize `opencode.json` or `.opencode.json`? (5) What's the current OpenCode version?

**Files:**
- Read: `C:\Users\Administrator.ERGOLAB\.config\opencode\opencode.json`
- Read: `C:\Users\Administrator.ERGOLAB\.config\opencode\agents\modular-builder.md`
- Read: `C:\Przemek\OPENCODE.md`

- [ ] **Step 1: Check what OpenCode actually loads**

Run OpenCode with debug logging if possible, or check the `.opencode/` project directory for session data that shows what context was loaded.

```bash
ls -la /c/claude/amplifier/.opencode/ 2>/dev/null
ls -la /c/Przemek/.opencode/ 2>/dev/null
```

- [ ] **Step 2: Verify agent file count vs what's referenced**

```bash
# Count orphaned agent files
ls ~/.config/opencode/agents/*.md | wc -l
# Check if opencode.json references agents/ directory anywhere
grep -i "agent" ~/.config/opencode/opencode.json
```

- [ ] **Step 3: Document findings**

Report: Which root causes are confirmed, any new findings, recommended priority order for fixes.

---

## Task 1: Fix opencode.json Configuration

**Agent:** modular-builder

**Files:**
- Modify: `C:\Users\Administrator.ERGOLAB\.config\opencode\opencode.json`

The current config is missing the `"agents"` section entirely. OpenCode supports configuring the 4 built-in agent types: `coder` (main), `task` (subagent), `title` (title generation), `summarizer`.

- [ ] **Step 1: Add agents section to opencode.json**

Replace the entire `opencode.json` with this corrected version:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "google/gemini-2.5-pro",
  "small_model": "google/gemini-2.5-flash",
  "theme": "opencode",
  "autoupdate": true,
  "tui": { "scroll_speed": 3 },
  "tools": { "write": true, "edit": true, "bash": true },
  "agents": {
    "coder": {
      "model": "google/gemini-2.5-pro",
      "maxTokens": 16000,
      "reasoningEffort": "high"
    },
    "task": {
      "model": "google/gemini-2.5-flash",
      "maxTokens": 8000
    }
  },
  "permission": {
    "doom_loop": "deny",
    "external_directory": "allow",
    "read": "allow",
    "edit": "allow",
    "glob": "allow",
    "grep": "allow",
    "list": "allow",
    "lsp": "allow",
    "todoread": "allow",
    "todowrite": "allow",
    "task": "allow",
    "skill": "allow",
    "webfetch": "deny",
    "websearch": "deny",
    "codesearch": "deny",
    "bash": "allow"
  },
  "instructions": [
    "C:/Przemek/OPENCODE.md",
    "AGENTS.md",
    "COWORK.md"
  ],
  "provider": {
    "google": {
      "options": {
        "timeout": 600000
      }
    }
  },
  "mcp": {
    "chrome-devtools": {
      "type": "local",
      "command": [
        "node",
        "C:/Przemek/chrome-devtools-mcp/node_modules/chrome-devtools-mcp/build/src/index.js"
      ],
      "enabled": true
    }
  }
}
```

**Key changes:**
- Added `"agents"` section with `coder` (Pro, high reasoning) and `task` (Flash, for search subagents)
- Model names: verify current Gemini model IDs available to the user (may be `gemini-2.5-pro`, `gemini-2.5-flash`, `gemini-3-pro-preview`, or `gemini-3-flash-preview` — check what's currently working)
- `maxTokens`: 16K for coder (plenty for implementation), 8K for task (search results)

- [ ] **Step 2: Verify the config is valid**

```bash
# Check JSON syntax
python3 -c "import json; json.load(open('C:/Users/Administrator.ERGOLAB/.config/opencode/opencode.json'))" && echo "Valid JSON"
```

- [ ] **Step 3: Commit**

```bash
# This file is outside the repo, no git commit needed
# But document the change
echo "opencode.json updated $(date +%Y-%m-%d): added agents section, verified model IDs" >> C:/Przemek/CHANGELOG.md
```

---

## Task 2: Create Custom Commands for Key Workflows

**Agent:** modular-builder

**Files:**
- Create: `C:\Users\Administrator.ERGOLAB\.config\opencode\commands\handoff.md`
- Create: `C:\Users\Administrator.ERGOLAB\.config\opencode\commands\search.md`
- Create: `C:\Users\Administrator.ERGOLAB\.config\opencode\commands\review-pr.md`

OpenCode custom commands go in `~/.config/opencode/commands/*.md`. They appear as slash commands in the UI with `user:` prefix. These replace the non-functional agent dispatch model.

- [ ] **Step 1: Create the handoff command**

Create `C:\Users\Administrator.ERGOLAB\.config\opencode\commands\handoff.md`:

```markdown
# Handoff Workflow

Execute the full Claude → Gemini handoff workflow from HANDOFF.md.

## Steps

1. Read HANDOFF.md from the repo root
2. Check the `## Dispatch Status:` line
3. If status is `WAITING_FOR_GEMINI` or `IN_PROGRESS`, proceed with the task
4. If status is anything else, stop and report

## When status is WAITING_FOR_GEMINI:

1. Extract: Objective, Branch, Repository, Working Directory, PR Target, Requirements, File whitelist/blacklist, Acceptance Criteria, Build commands
2. Navigate to the Repository directory
3. Create the feature branch: `git checkout main && git pull && git checkout -b <branch>`
4. Update HANDOFF.md status to IN_PROGRESS, commit on feature branch
5. Read all Context Loading files listed in HANDOFF.md
6. Implement the requirements — write code, tests, commit frequently
7. Run Build & Verify commands — if build fails, fix and retry
8. Audit diff: `git diff main..HEAD --stat` — only allowed files should be changed
9. Push and create PR: `git push -u origin <branch> && gh pr create ...`
10. Update HANDOFF.md to PR_READY on main

## CRITICAL RULES:
- NEVER use `git add .` or `git add -A` — always stage files by name
- NEVER modify files in `.claude/`, `CLAUDE.md`, or `C:\FuseCP\`
- NEVER create PR if build fails
- Run `git diff --cached --stat` before every commit
- Include build output and acceptance criteria checklist in PR description
```

- [ ] **Step 2: Create the search command**

Create `C:\Users\Administrator.ERGOLAB\.config\opencode\commands\search.md`:

```markdown
# Codebase Search

Systematically search the codebase to answer a question. Use a three-phase approach:

## Phase 1: Reconnaissance
- Use glob to find candidate files by name patterns
- Use grep with files_with_matches mode to find content patterns
- Check the `tags` file at repo root for symbol definitions: `grep -i "pattern" tags | head -20`
- Goal: Identify 3-8 candidate files

## Phase 2: Targeted Reading
- Read the most relevant files (max 8)
- Follow imports and dependencies
- Check tests for expected behavior

## Phase 3: Synthesis
- Produce a structured answer with file:line references
- Include a Key Files table
- List any gaps or unknowns

## Rules:
- Evidence before claims — cite file:line for every assertion
- Breadth before depth — Phase 1 before Phase 2
- Max 8 file reads total
- If stuck after 6 reads, return what you have with gaps listed
```

- [ ] **Step 3: Create the review-pr command**

Create `C:\Users\Administrator.ERGOLAB\.config\opencode\commands\review-pr.md`:

```markdown
# Review PR Checklist

Review the current branch's changes against main before creating a PR.

## Steps:

1. Run `git diff main..HEAD --stat` to see all changed files
2. For each changed file:
   - Is it in the allowed file list from HANDOFF.md?
   - Does it contain only intended changes?
   - Remove unexpected files: `git checkout main -- <file>`
3. Check acceptance criteria from HANDOFF.md — verify each item
4. Run build commands from HANDOFF.md
5. Report: files changed count, criteria met, build status

## Red Flags:
- Files not in the whitelist
- Changes to `.claude/`, `CLAUDE.md`, `C:\FuseCP\`
- Build failures
- Uncommitted changes
```

- [ ] **Step 4: Verify commands are loadable**

```bash
ls -la ~/.config/opencode/commands/
# Should show: handoff.md, search.md, review-pr.md
```

- [ ] **Step 5: Commit the changes**

```bash
# Commands are outside repo, but let's track them in Przemek's workspace
cp -r ~/.config/opencode/commands/ /c/Przemek/opencode-commands-backup/
```

---

## Task 3: Rewrite OPENCODE.md

**Agent:** modular-builder

**Files:**
- Modify: `C:\Przemek\OPENCODE.md`

The current OPENCODE.md tells Gemini to dispatch implementation agents as subagents — which is impossible because OpenCode subagents only have read-only tools. This is the #1 cause of "agents do nothing."

- [ ] **Step 1: Replace the Agent Skills section**

Replace lines 87-120 (the "Agent Skills" section) with a corrected version that reflects OpenCode's actual capabilities:

```markdown
## Tool Capabilities

### Your main session (coder agent) has FULL access:
- **view** — Read files (OpenCode calls it 'view', not 'Read')
- **write** — Create/overwrite files
- **edit** — Replace specific strings in files
- **bash** — Execute shell commands
- **glob** — Find files by pattern
- **grep** — Search file contents
- **agent** — Dispatch a search subagent (READ-ONLY — see below)

### Subagents (via the "agent" / "Task" tool) are READ-ONLY:
Subagents can ONLY use: glob, grep, ls, view. They CANNOT write, edit, or run bash.
- Use subagents ONLY for research/search tasks
- NEVER dispatch a subagent expecting it to write code
- All implementation work MUST happen in your main session

### Custom Commands (Slash Commands)
You have custom commands available:
- `/user:handoff` — Execute the full HANDOFF.md workflow
- `/user:search` — Structured codebase search
- `/user:review-pr` — PR review checklist

## Workflow Protocol

### Starting a Session

1. `git checkout main && git pull` — get latest
2. Read `HANDOFF.md` — check current dispatch status
3. If status is `WAITING_FOR_GEMINI`:
   - Run `/user:handoff` to start the full workflow
   - The command guides you through: branch → implement → build → PR
4. If no handoff task, work on whatever the user asks

### Doing Implementation Work

**CRITICAL: Do ALL implementation in your main session.** Do not dispatch subagents for code writing — they can only search.

For research before implementing:
- Use the `agent` tool (Task) to search the codebase for patterns
- Or use `/user:search` for structured codebase exploration
- These subagents CAN read files and search — use them for reconnaissance

For writing code:
- Write files directly using `write` tool
- Edit files using `edit` tool
- Run commands using `bash` tool
- Commit frequently with `git add <specific-files> && git commit -m "..."`
```

- [ ] **Step 2: Remove the agent dispatch table**

Remove the "Key agents for implementation tasks" table (old lines 109-119) since subagents can't implement. Replace with a note that implementation happens in main context.

- [ ] **Step 3: Fix tool references throughout**

Search and replace any remaining references to Claude Code tool names:
- `Read` → `view` (when referring to the OpenCode tool)
- Keep `Read` when it appears in human-readable instructions (like "Read HANDOFF.md")

- [ ] **Step 4: Verify the file is coherent**

Read the full updated OPENCODE.md and verify it doesn't contain contradictions.

- [ ] **Step 5: Commit**

```bash
cd /c/Przemek
git add OPENCODE.md 2>/dev/null || true
# OPENCODE.md might not be in a git repo — that's fine
```

---

## Task 4: Clean Up Orphaned Agent Files

**Agent:** post-task-cleanup

**Files:**
- Delete: `C:\Users\Administrator.ERGOLAB\.config\opencode\agents\` (entire directory — 34 files, all orphaned)
- Modify: `C:\Przemek\scripts\sync-agents.sh` (update to only sync SKILL.md format, not OpenCode agents)

- [ ] **Step 1: Back up then remove orphaned agents directory**

```bash
# Back up first
cp -r ~/.config/opencode/agents/ /c/Przemek/opencode-agents-backup-$(date +%Y%m%d)/

# Remove the orphaned directory
rm -rf ~/.config/opencode/agents/
```

- [ ] **Step 2: Update sync-agents.sh**

Edit `C:\Przemek\scripts\sync-agents.sh` to:
1. Remove the OpenCode agents output section (lines 189-226) — this generates files OpenCode doesn't read
2. Keep the SKILL.md output section (lines 145-186) — this format is still used by Przemek's agents
3. Update the summary to not mention OpenCode agents

Specifically, remove these lines:
- Lines 12-13: `OPENCODE_AGENTS_DIR=...` variable
- Lines 121: `mkdir -p "$OPENCODE_AGENTS_DIR"`
- Lines 124, 228: `oc_count` variable
- Lines 189-226: The entire "OUTPUT 2: OpenCode native flat .md" block
- Lines 233-234: Summary lines referencing OpenCode

- [ ] **Step 3: Verify cleanup**

```bash
# Confirm agents dir is gone
ls ~/.config/opencode/agents/ 2>/dev/null && echo "STILL EXISTS" || echo "Cleaned up"

# Confirm commands dir exists
ls ~/.config/opencode/commands/
```

- [ ] **Step 4: Commit sync script changes**

```bash
cd /c/claude/amplifier
# sync-agents.sh lives in C:\Przemek\scripts, not in the repo
```

---

## Task 5: Update HANDOFF.md Template

**Agent:** modular-builder

**Files:**
- Modify: `C:\claude\amplifier\HANDOFF.md`

The HANDOFF.md template currently references "Agent Assignments" which implies subagent dispatch. Update it to reflect that Gemini does implementation in main context, using subagents only for research.

- [ ] **Step 1: Update the HANDOFF.md with correct workflow**

Replace the current content with a fresh template that reflects the actual working architecture:

```markdown
# Amplifier Project - Handoff Log

## Dispatch Status: IDLE

Use this file to dispatch tasks from Claude Code (Senior) to Gemini/OpenCode (Junior).

---

## How This Works

1. **Claude** writes a task below and sets status to `WAITING_FOR_GEMINI`
2. **Gemini** reads this file, runs `/user:handoff`, implements on a feature branch
3. **Gemini** creates PR and sets status to `PR_READY`
4. **Claude** reviews PR, merges, deploys, sets status to `IDLE`

---

## Current Task

<!-- Claude fills this section when dispatching -->

**Objective:** (none)

**Branch:** feature/...

**Repository:** C:\claude\amplifier

**Working Directory:** C:\claude\amplifier

**PR Target:** psklarkins/amplifier main

**Requirements:**
- (none)

**Context Loading:**
- Read: (list files Gemini should read before starting)

**Files YOU May Modify:**
- (explicit whitelist)

**Files You Must NOT Modify:**
- `.claude/*`
- `CLAUDE.md`
- `C:\FuseCP\*`

**Acceptance Criteria:**
- [ ] (criterion 1)
- [ ] (criterion 2)

**Build & Verify:**
```bash
# (exact build commands to run before PR)
```

---

## Last Completed Task

(Previous task summary moves here after completion)
```

- [ ] **Step 2: Commit**

```bash
cd /c/claude/amplifier
git add HANDOFF.md
git commit -m "docs: update HANDOFF.md template for OpenCode-compatible workflow"
```

---

## Task 6: Verify End-to-End

**Agent:** post-task-cleanup

- [ ] **Step 1: Verify opencode.json is valid**

```bash
python3 -c "import json; json.load(open('C:/Users/Administrator.ERGOLAB/.config/opencode/opencode.json'))" && echo "Valid"
```

- [ ] **Step 2: Verify custom commands exist**

```bash
ls -la ~/.config/opencode/commands/
# Expected: handoff.md, search.md, review-pr.md
```

- [ ] **Step 3: Verify orphaned agents are gone**

```bash
ls ~/.config/opencode/agents/ 2>/dev/null && echo "FAIL: agents dir still exists" || echo "OK: agents dir removed"
```

- [ ] **Step 4: Verify OPENCODE.md is coherent**

Read `C:\Przemek\OPENCODE.md` and verify:
- No references to "dispatch implementation agents as subagents"
- Tool names are correct (view not Read)
- Custom commands are referenced
- Subagent limitations are documented

- [ ] **Step 5: Verify HANDOFF.md template**

Read `HANDOFF.md` and verify it has the updated template.

- [ ] **Step 6: Check for model ID validity**

```bash
# Verify current model IDs work — user should test in OpenCode
echo "Model IDs to verify in OpenCode:"
echo "  google/gemini-2.5-pro (or google/gemini-3-pro-preview)"
echo "  google/gemini-2.5-flash (or google/gemini-3-flash-preview)"
echo "User: start OpenCode and verify models load"
```

- [ ] **Step 7: Summary for user**

Present summary:
- What was broken (5 root causes)
- What was fixed (6 tasks)
- What user needs to test (start OpenCode, run /user:handoff on a test task)
- What's still needed (model ID verification, first real handoff test)

---

## Notes

### What OpenCode Subagents CAN Do (Use for These)
- Search codebase with grep/glob
- Read files to understand architecture
- List directory contents
- Research before implementation

### What OpenCode Subagents CANNOT Do (Never Expect These)
- Write files
- Edit files
- Run bash commands
- Create branches
- Make commits
- Create PRs

### Future Improvements (Not in This Plan)
- Add episodic memory MCP to OpenCode (if MCP server is compatible)
- Add context7 MCP for documentation lookup
- Create more custom commands as workflows emerge
- Consider OpenCode plugins for enhanced tool access in subagents (if future versions support it)
