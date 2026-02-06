---
description: Show current DDD progress and next steps (project:ddd)
allowed-tools: Read, Bash(ls:*), Bash(cat:*), Bash(git status:*), Bash(git log:*)
---

# DDD Workflow Status

Checking current Document-Driven Development progress...

---

## DDD Working Directory

!`ls -la ai_working/ddd/ 2>/dev/null || echo "❌ No active DDD session (no ai_working/ddd/ directory)"`

---

## Phase Detection

Checking which artifacts exist to determine current phase:

**Phase 1 (Plan)**: !`test -f ai_working/ddd/plan.md && echo "✅ Plan created" || echo "❌ No plan yet"`

**Phase 2 (Docs)**: !`test -f ai_working/ddd/docs_status.md && echo "✅ Docs updated" || echo "❌ Docs not updated"`

**Phase 3 (Code Plan)**: !`test -f ai_working/ddd/code_plan.md && echo "✅ Code planned" || echo "❌ Code not planned"`

**Phase 4 (Code)**: !`test -f ai_working/ddd/impl_status.md && echo "✅ Code implemented" || echo "❌ Code not implemented"`

**Phase 5 (Finish)**: !`test -d ai_working/ddd/ && echo "⏳ Not finished yet" || echo "✅ Workflow complete (no artifacts remain)"`

---

## Git Status

Current working tree state:

!`git status --short || git status`

---

## Recent DDD-Related Commits

!`git log --oneline --all --grep="docs:\|feat:\|fix:" -10 2>/dev/null || git log --oneline -10`

---

## Current Branch

!`git branch --show-current`

---

## Unpushed Commits

!`git log --oneline @{u}..HEAD 2>/dev/null || echo "No unpushed commits or remote tracking branch"`

---

## Status Analysis

Based on the artifacts detected above, here's your current status:

### Current Phase

**Determining phase...**

If `ai_working/ddd/` doesn't exist:

- **Status**: No active DDD session
- **Recommendation**: Start new feature with `/ddd:1-plan [feature]`

If `plan.md` exists but not `docs_status.md`:

- **Status**: Phase 1 complete (Planning done)
- **Next**: Update documentation with `/ddd:2-docs`

If `docs_status.md` exists but not `code_plan.md`:

- **Status**: Phase 2 in progress or awaiting commit
- **Next**:
  - If docs not committed yet: Review and commit them
  - If docs committed: Plan code with `/ddd:3-code-plan`

If `code_plan.md` exists but not `impl_status.md`:

- **Status**: Phase 3 complete (Code planned)
- **Next**: Implement code with `/ddd:4-code`

If `impl_status.md` exists:

- **Status**: Phase 4 in progress (Implementation)
- **Next**: Continue `/ddd:4-code` or finalize with `/ddd:5-finish`

If no `ai_working/ddd/` but recent DDD commits:

- **Status**: DDD workflow previously completed
- **Next**: Start new feature with `/ddd:1-plan [feature]`

---

## Artifact Details

### Quick Access to Current Artifacts

If artifacts exist, you can read them:

**Plan** (Phase 1 output):

```bash
Read ai_working/ddd/plan.md
```

**Docs Status** (Phase 2 output):

```bash
Read ai_working/ddd/docs_status.md
```

**Code Plan** (Phase 3 output):

```bash
Read ai_working/ddd/code_plan.md
```

**Implementation Status** (Phase 4 tracking):

```bash
Read ai_working/ddd/impl_status.md
```

**Test Report** (Phase 4 output):

```bash
Read ai_working/ddd/test_report.md
```

---

## Recommended Next Command

Based on current phase:

**If no active session**:

```bash
/ddd:1-plan [describe your feature]
```

**If plan exists, docs not updated**:

```bash
/ddd:2-docs
```

**If docs updated but not committed**:

```bash
# Review changes:
git diff

# When satisfied, commit:
git commit -m "docs: [your description]"

# Then:
/ddd:3-code-plan
```

**If docs committed, code not planned**:

```bash
/ddd:3-code-plan
```

**If code planned but not implemented**:

```bash
/ddd:4-code
```

**If code implemented but not finalized**:

```bash
/ddd:5-finish
```

**If workflow complete**:

```bash
# Start next feature:
/ddd:1-plan [next feature]
```

---

## Workflow Progress Summary

**Complete DDD Workflow**:

```
Phase 1: Planning ━━━━━━━━━┓
                         ↓
Phase 2: Docs ━━━━━━━━━━┫  ← Where are you?
                         ↓
Phase 3: Code Plan ━━━━━┫
                         ↓
Phase 4: Code ━━━━━━━━━━┫
                         ↓
Phase 5: Finish ━━━━━━━━┛
```

**Your Progress**: [Based on phase detection above]

---

## Git Summary

**Current Branch:**
!`git branch --show-current`

**Uncommitted Changes:**
!`git status --short | wc -l | xargs -I {} echo "{} files"`

**Unpushed Commits:**
!`git log --oneline @{u}..HEAD 2>/dev/null | wc -l | xargs -I {} echo "{} commits" || echo "0 commits (no remote tracking)"`

---

## Process

- Ultrathink step-by-step, laying out assumptions and unknowns, use the TodoWrite tool to capture all tasks and subtasks.
  - VERY IMPORTANT: Make sure to use the actual TodoWrite tool for todo lists, don't do your own task tracking, there is code behind use of the TodoWrite tool that is invisible to you that ensures that all tasks are completed fully.
  - Adhere to the @ai_context/IMPLEMENTATION_PHILOSOPHY.md and @ai_context/MODULAR_DESIGN_PHILOSOPHY.md files.
- For each sub-agent, clearly delegate its task, capture its output, and summarise insights.
- Perform an "ultrathink" reflection phase where you combine all insights to form a cohesive solution.
- If gaps remain, iterate (spawn sub-agents again) until confident.
- Where possible, spawn sub-agents in parallel to expedite the process.

---

## Need Help?

**For complete DDD guide**:

```bash
/ddd:0-help
```

**To load all DDD context**:

```bash
/ddd:prime
```

**For phase-specific help**:
Run the command for that phase - each has detailed instructions.

---

## Troubleshooting

**"I'm lost, not sure where I am"**

- Review the Phase Detection section above
- Check which artifacts exist
- Follow Recommended Next Command

**"I made a mistake in [phase]"**

- **Planning**: Edit `ai_working/ddd/plan.md` or re-run `/ddd:1-plan`
- **Docs**: Re-run `/ddd:2-docs` with feedback
- **Code Planning**: Edit `ai_working/ddd/code_plan.md` or re-run `/ddd:3-code-plan`
- **Code**: Provide feedback to `/ddd:4-code`

**"I want to start over"**

```bash
# Delete DDD artifacts
rm -rf ai_working/ddd/

# Start fresh
/ddd:1-plan [feature]
```

**"I want to abandon this feature"**

```bash
# Delete DDD artifacts
rm -rf ai_working/ddd/

# Reset git changes (if needed)
git reset --hard HEAD
# or
git stash
```

---

**Status check complete.**

Ready to continue? Run the recommended next command above!
