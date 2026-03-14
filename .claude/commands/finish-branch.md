---
description: "Complete development branch with cleanup, verification, and merge/PR workflow. Use when implementation is complete and all tests pass."
---

# Finishing a Development Branch

## Overview

Guide completion of development work by presenting clear options and handling chosen workflow.

**Core principle:** Verify tests → Quality gate → Create PR (default) → Clean up.

**Announce at start:** "I'm using the finish-branch command to complete this work."

## The Process

**Session Naming:** First, rename this session to indicate the completion phase:

/rename finish: <branch-name>

Get branch from `git branch --show-current`. Example: `/rename finish: feature/auth`

If `/rename` is unavailable, skip this step.

### Step 1: Pre-Merge Verification

**Dispatch `test-coverage` agent** to run the project's test suite and verify all tests pass before presenting options.

```bash
# Run project's test suite
npm test / cargo test / pytest / go test ./...
```

**If tests fail:**
```
Tests failing (<N> failures). Must fix before completing:

[Show failures]

Cannot proceed with merge/PR until tests pass.
```

Stop. Don't proceed to Step 2.

**If tests pass:** Continue to Step 2.

### Step 2: Quality Gate

After tests pass, dispatch **2 agents in parallel** (single message, two Task calls) to review all files changed on this branch:

```bash
# Get list of changed files for agent prompts
git diff --name-only main...HEAD
```

#### Agent 1: Code Quality Review

```
Task(subagent_type="code-quality-reviewer", model="sonnet", max_turns=10)

Review these changed files for code quality issues:
[changed file list from git diff]

Check: type annotations, code style, dead code, stubs/placeholders, unused imports.
Focus on the diff only — do not flag pre-existing issues.
Return VERDICT: PASS or FAIL with specific findings.
```

#### Agent 2: Cleanup Review

```
Task(subagent_type="post-task-cleanup", model="sonnet", max_turns=10)

Review git status and these changed files for cleanup issues:
[changed file list from git diff]

Check: temp files, debug statements, commented-out code, artifacts, philosophy violations.
Return Status: CLEAN or NEEDS_ATTENTION with specific findings.
```

#### Gate Logic

**If code-quality-reviewer returns FAIL with BLOCKING findings:**
```
Quality gate failed. Fix these before PR:

[Show BLOCKING findings with file:line references]

Cannot proceed until issues are resolved.
```
Stop. Don't proceed to Step 3.

**If code-quality-reviewer returns FAIL with only SUGGESTION/NITPICK:**
```
Quality review warnings (non-blocking):
[Show findings]

Proceeding to PR creation. Consider addressing these in a follow-up.
```
Continue to Step 3.

**If post-task-cleanup returns NEEDS_ATTENTION:**
```
Cleanup suggestions found:
[Show findings]

Fix these first, or proceed to PR? (fix/proceed)
```
Wait for user choice. If "fix", stop and let user address. If "proceed", continue to Step 3.

**If both pass:** Continue silently to Step 3.

### Step 3: Determine Base Branch

```bash
# Try common base branches
git merge-base HEAD main 2>/dev/null || git merge-base HEAD master 2>/dev/null
```

Or ask: "This branch split from main - is that correct?"

### Step 4: Default Action — Create PR

**The default completion action is always to create a Pull Request.** Do not present a menu of options. Instead:

```
Implementation complete. Tests pass. Creating PR against <base-branch>.
```

Then proceed directly to Option 2 (Push and Create PR) below.

**Only offer alternatives if the user explicitly asks** (e.g., "just merge locally", "discard this"). The 4 options still exist but PR is the default — don't ask, just do it.

**If on main/master (should not happen if Branch Gate was followed):**
```
WARNING: You're on main. Cannot create a PR from main to main.
Creating feature branch from current HEAD, then resetting main.
```
Then: create branch, reset main, push branch, create PR. This is the recovery path — it works but is messy. The Branch Gate in /subagent-dev should prevent this.

### Step 5: Execute Choice

#### Option 1: Merge Locally

```bash
# Switch to base branch
git checkout <base-branch>

# Pull latest
git pull

# Merge feature branch
git merge <feature-branch>

# Verify tests on merged result
<test command>

# If tests pass
git branch -d <feature-branch>
```

Then: Cleanup worktree (Step 6)

#### Option 2: Push and Create PR (Gitea-First)

```bash
# Push branch to Gitea (primary remote)
git push -u origin <feature-branch>
```

Create PR using Gitea MCP (preferred):
```
mcp__gitea__create_pull_request(owner="admin", repo="<repo>", title="<title>", head="<feature-branch>", base="main", body="<summary>")
```

Fallback (tea CLI): `tea pr create --repo admin/<repo> --title "<title>" --head "<feature-branch>" --base main --description "<summary>"`

Present the PR URL to the user.

**Note:** PR lives on Gitea. GitHub mirror syncs automatically via push mirror. CI runs on GitHub Actions when the mirror triggers.

Then: Cleanup worktree (Step 6)

#### Option 3: Keep As-Is

Report: "Keeping branch <name>. Worktree preserved at <path>."

**Don't cleanup worktree.**

#### Option 4: Discard

**Confirm first:**
```
This will permanently delete:
- Branch <name>
- All commits: <commit-list>
- Worktree at <path>

Type 'discard' to confirm.
```

Wait for exact confirmation.

If confirmed:
```bash
git checkout <base-branch>
git branch -D <feature-branch>
```

Then: Cleanup worktree (Step 6)

### Step 6: Cleanup Worktree and Final Hygiene

**For Options 1, 2, 4:**

Check if in worktree:
```bash
git worktree list | grep $(git branch --show-current)
```

If yes:
```bash
git worktree remove <worktree-path>
```

**For Option 3:** Keep worktree.

**Note:** `post-task-cleanup` already ran in Step 2 (Quality Gate). This step only handles worktree/branch cleanup. If Step 2 was skipped (e.g., user chose Option 4: Discard), dispatch `post-task-cleanup` here as a fallback to prune stale branches and worktrees.

## Quick Reference

| Option | Merge | Push | Keep Worktree | Cleanup Branch |
|--------|-------|------|---------------|----------------|
| 1. Merge locally | yes | - | - | yes |
| 2. Create PR | - | yes | yes | - |
| 3. Keep as-is | - | - | yes | - |
| 4. Discard | - | - | - | yes (force) |

## Common Mistakes

**Skipping test verification**
- **Problem:** Merge broken code, create failing PR
- **Fix:** Always verify tests before offering options

**Open-ended questions**
- **Problem:** "What should I do next?" leads to ambiguity
- **Fix:** Present exactly 4 structured options

**Automatic worktree cleanup**
- **Problem:** Remove worktree when might need it (Option 2, 3)
- **Fix:** Only cleanup for Options 1 and 4

**No confirmation for discard**
- **Problem:** Accidentally delete work
- **Fix:** Require typed "discard" confirmation

## Red Flags

**Never:**
- Proceed with failing tests
- Merge without verifying tests on result
- Delete work without confirmation
- Force-push without explicit request

**Always:**
- Verify tests before offering options
- Present exactly 4 options
- Get typed confirmation for Option 4
- Clean up worktree for Options 1 & 4 only

## Integration

**Called by:**
- **subagent-driven-development** (Step 7) - After all tasks complete
- **executing-plans** (Step 5) - After all batches complete

**Pairs with:**
- `/worktree` - Cleans up worktree created by that command
- `/verify` - Pre-merge verification
- `/request-review` - Code review workflow
- `/self-eval finish-branch` - Evaluate this branch completion quality
- `/self-eval all` - Evaluate all command outputs from this session
- `/techdebt` - Run before finishing to catch accumulated debt
