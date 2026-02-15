# Context Caching Optimization (Gold Prefix) Implementation Plan

> **For Claude:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Maximize Gemini 3 context caching by implementing a stable "Gold Prefix" strategy, refactoring compaction hooks, and implementing subagent context mirroring.

**Architecture:** Frozen Zone (static) followed by Churn Zone (dynamic). Refactor `hook_precompact.py` for stable history summarization. Update `subagent-driven-development` templates for mirroring.

**Tech Stack:** Python (hooks), Markdown (templates), OpenCode CLI.

---

## Chunk 1: Hook Refactoring for Stable Prefix

### Task 1: Refactor `hook_precompact.py`

**Agent:** amplifier-cli-architect

**Files:**
- Modify: `.claude/tools/hook_precompact.py`

- [ ] **Step 1: Read current implementation**
Read: `.claude/tools/hook_precompact.py`

- [ ] **Step 2: Implement Frozen Zone protection**
Update the script to identify the start of the prompt and ensure it is NEVER summarized. Define the "Frozen Zone" as the first 100k-200k tokens containing core instructions and agent definitions.

- [ ] **Step 3: Implement stable history summarization**
Modify the summarization logic to target only the "Middle History" (turns 3 to N-5). Ensure the summarized block is appended *after* the Frozen Zone and stays stable until the next compaction event.

- [ ] **Step 4: Verify syntax and logic**
Run: `python -m py_compile .claude/tools/hook_precompact.py`

- [ ] **Step 5: Commit**
```bash
git add .claude/tools/hook_precompact.py
git commit -m "feat(cache): refactor precompact hook for stable Gold Prefix"
```

### Task 2: Refactor `hook_session_start.py` for Prefix Stability

**Agent:** amplifier-cli-architect

**Files:**
- Modify: `.claude/tools/hook_session_start.py`

- [ ] **Step 1: Identify and move dynamic variables**
Check if `hook_session_start.py` or associated prompts inject "Today's Date" or "CWD" at the top. Move them to a "Churn Zone" that follows the static system instructions.

- [ ] **Step 2: Commit**
```bash
git add .claude/tools/hook_session_start.py
git commit -m "feat(cache): isolate churn zone in session start hook"
```

---

## Chunk 2: Subagent Mirroring & Prompt Standardization

### Task 3: Update Subagent Prompt Templates

**Agent:** modular-builder

**Files:**
- Modify: `C:/Przemek/superpowers/skills/subagent-driven-development/implementer-prompt.md`
- Modify: `C:/Przemek/superpowers/skills/subagent-driven-development/spec-reviewer-prompt.md`
- Modify: `C:/Przemek/superpowers/skills/subagent-driven-development/code-quality-reviewer-prompt.md`

- [ ] **Step 1: Standardize Subagent Prefix**
Modify the prompt templates to include a directive for the controller to inject the Frozen Zone (Gold Prefix) before the agent-specific instructions. 

- [ ] **Step 2: Commit**
```bash
git add C:/Przemek/superpowers/skills/subagent-driven-development/*.md
git commit -m "feat(cache): implement Gold Prefix mirroring in subagent templates"
```

---

## Chunk 3: Verification & Profiling

### Task 4: Profile Cache Hits

**Agent:** performance-optimizer

- [ ] **Step 1: Perform 5-10 turns of interaction**
Trigger tool use and subagent dispatches to build context.

- [ ] **Step 2: Verify hits via `opencode stats`**
Run: `opencode stats`
Expected: "Cache Read" tokens should grow significantly per turn, while "Input" tokens stay low.

- [ ] **Step 3: Report findings**
Analyze the ratio of Cache Read vs Input.

### Task 4: Final Cleanup

**Agent:** post-task-cleanup

- [ ] **Step 1: Ensure no debug artifacts remain**
- [ ] **Step 2: Commit**
```bash
git commit --allow-empty -m "chore: final verification of context caching optimization"
```
