# Gemini/OpenCode Optimization Implementation Plan

> **For Claude:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement critical context caching and TPM optimization for Gemini 3 on the OpenCode platform.

**Architecture:**
- **Gold Prefix Optimization:** Restructure `hook_session_start.py` to separate static (frozen) and dynamic (churn) content, enabling stable prefix caching.
- **Subagent Cache Inheritance:** Update `sync-agents-to-opencode.py` to prepend the stable "Frozen Zone" to all generated subagent skills, ensuring they share the main session's cache.
- **TPM Protection:** Force `model: flash` for implementation subagents in `sync-agents-to-opencode.py` to prevent "Pro" model rate limit exhaustion.

**Tech Stack:** Python 3.11+, Amplifier Hooks, Jinja2 (optional/implied for templating), Gemini 3 API patterns.

---

## Chunk 1: Gold Prefix Architecture

### Task 1: Create Frozen Zone Header Source
**Agent:** `zen-architect`

**Files:**
- Create: `./.claude/context/frozen_header.md`

**Goal:** Establish the single source of truth for the stable "Frozen Zone" content.

- [ ] **Step 1: Create context directory**
  Run: `mkdir -p ./.claude/context`

- [ ] **Step 2: Write frozen_header.md**
  Write content containing:
  - Identity & Core Mandates
  - Project Constitution (CLAUDE.md reference)
  - Agent Manifest (AMPLIFIER-AGENTS.md reference)
  - Crucially: **NO dynamic data** (no dates, no paths, no search results)

- [ ] **Step 3: Verify content stability**
  Check that the file contains zero dynamic placeholders.

### Task 2: Refactor Session Start Hook
**Agent:** `amplifier-cli-architect`

**Files:**
- Modify: `./.claude/tools/hook_session_start.py`

**Goal:** Split the hook output into strictly static (read from frozen_header) and dynamic sections.

- [ ] **Step 1: Read frozen_header.md in hook**
  Update `main()` to read `../context/frozen_header.md` as the very first output block.

- [ ] **Step 2: Move dynamic content to Churn Zone**
  Move:
  - Date/Time
  - Platform/OS info
  - Working Directory
  - Memory Search Results
  ...to the *end* of the output, labeled `## [CHURN ZONE: DYNAMIC SESSION CONTEXT]`.

- [ ] **Step 3: Verify Output Structure**
  Run: `uv run .claude/tools/hook_session_start.py`
  Expected Output starts with: `## [FROZEN ZONE: STABLE CONTEXT]`
  Expected Output ends with: `## [CHURN ZONE: DYNAMIC SESSION CONTEXT]` containing date/memory.

---

## Chunk 2: Subagent Optimization

### Task 3: Update Agent Sync Script (Cache Inheritance)
**Agent:** `modular-builder`

**Files:**
- Modify: `./scripts/sync-agents-to-opencode.py`

**Goal:** Bake the Frozen Zone into subagent skills so they share the cache.

- [ ] **Step 1: Read frozen_header.md in script**
  Update script to read `./.claude/context/frozen_header.md`.

- [ ] **Step 2: Prepend to generated SKILL.md**
  In `generate_skill_md`:
  - After frontmatter (`--- ... ---`)
  - Insert: `\n\n<!-- FROZEN ZONE START -->\n{frozen_header_content}\n<!-- FROZEN ZONE END -->\n\n`
  - Before the agent's specific description/instructions.

- [ ] **Step 3: Verify Generation**
  Run: `python scripts/sync-agents-to-opencode.py --dry-run`
  Check output for one agent to ensure Frozen Zone is present.

### Task 4: Force Flash Model for Implementation Agents
**Agent:** `performance-optimizer`

**Files:**
- Modify: `./scripts/sync-agents-to-opencode.py`

**Goal:** Prevent TPM exhaustion by using Flash for non-reasoning tasks.

- [ ] **Step 1: Update MODEL_MAP**
  Change `inherit` or `pro` to `flash` for:
  - `modular-builder`
  - `test-coverage`
  - `post-task-cleanup`
  - `bug-hunter`
  - `integration-specialist`

- [ ] **Step 2: Verify Mapping**
  Run: `python scripts/sync-agents-to-opencode.py --dry-run`
  Verify `modular-builder/SKILL.md` frontmatter shows `model: flash` (or equivalent OpenCode mapping).

---

## Chunk 3: Deployment & Verification

### Task 5: Deploy and Verify
**Agent:** `integration-specialist`

**Files:**
- Run: `python scripts/sync-agents-to-opencode.py`
- Verify: `${OPENCODE_SKILLS_DIR}/amplifier/modular-builder/SKILL.md`

**Goal:** Apply changes and verify the fix works in the real environment.

- [ ] **Step 1: Run Sync**
  Execute the sync script to update all 30 agents.

- [ ] **Step 2: Check Installed Skill**
  Read `${OPENCODE_SKILLS_DIR}/amplifier/modular-builder/SKILL.md`.
  - Confirm Frozen Zone is present.
  - Confirm `recommended_model: flash`.

- [ ] **Step 3: Run Session Start Hook**
  Run: `uv run .claude/tools/hook_session_start.py`
  - Confirm output structure matches Task 2.

- [ ] **Step 4: Commit**
  `git add . && git commit -m "feat(gemini): optimize context caching and TPM usage"`
