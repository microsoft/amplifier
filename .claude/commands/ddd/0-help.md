---
description: DDD workflow guide and help (project:ddd)
---

# Document-Driven Development (DDD) - Complete Guide

Loading DDD context for comprehensive help...

@docs/document_driven_development/overview.md
@docs/document_driven_development/reference/tips_for_success.md
@docs/document_driven_development/reference/common_pitfalls.md
@docs/document_driven_development/reference/faq.md
@ai_context/IMPLEMENTATION_PHILOSOPHY.md
@ai_context/MODULAR_DESIGN_PHILOSOPHY.md

---

## What is Document-Driven Development?

**Core Principle**: Documentation IS the specification. Code implements what documentation describes.

**Why it works**:

- Prevents context poisoning (inconsistent docs)
- Clear contracts before complexity
- Reviewable design before expensive implementation
- AI-optimized workflow
- Docs and code never drift

**Philosophy Foundation**:

- Ruthless Simplicity (IMPLEMENTATION_PHILOSOPHY)
- Modular Design / Bricks & Studs (MODULAR_DESIGN_PHILOSOPHY)

---

## Complete Workflow (5 Phases + Utilities)

### Main Workflow Commands (Run in Order)

**1. `/ddd:1-plan`** - Planning & Design

- Design feature before touching files
- Create comprehensive plan
- Get shared understanding
- **Output**: `ai_working/ddd/plan.md`

**2. `/ddd:2-docs`** - Update All Non-Code Files

- Update docs, configs, READMEs
- Apply retcon writing (as if already exists)
- Iterate until approved
- **Requires**: User must commit when satisfied

**3. `/ddd:3-code-plan`** - Plan Code Changes

- Assess current code vs new docs
- Plan all implementation changes
- Break into chunks
- **Requires**: User approval to proceed

**4. `/ddd:4-code`** - Implement & Verify

- Write code matching docs exactly
- Test as user would
- Iterate until working
- **Requires**: User authorization for each commit

**5. `/ddd:5-finish`** - Wrap-Up & Cleanup

- Clean temporary files
- Final verification
- Push/PR with explicit authorization
- **Requires**: User approval for all git operations

### Utility Commands

**`/ddd:prime`** - Load all DDD context

- Loads complete methodology documentation
- Use at session start for full context

**`/ddd:status`** - Check current progress

- Shows current phase
- Lists artifacts created
- Recommends next command

---

## State Management (Artifacts)

All phases use `ai_working/ddd/` directory:

```
ai_working/ddd/
├── plan.md              (Created by 1-plan, used by all)
├── docs_index.txt       (Working file for 2-docs)
├── docs_status.md       (Status from 2-docs)
├── code_plan.md         (Created by 3-code-plan)
├── impl_status.md       (Tracking for 4-code)
└── test_report.md       (Output from 4-code)
```

**Each command reads previous artifacts**, so you can run subsequent commands without arguments if you want to continue from where you left off.

---

## Example Usage

### Starting a New Feature

```bash
# Load context (optional but recommended)
/ddd:prime

# Phase 1: Plan the feature
/ddd:1-plan Add user authentication with JWT tokens

# Phase 2: Update all docs
/ddd:2-docs

# Review the changes, iterate if needed
# When satisfied, commit the docs yourself

# Phase 3: Plan code implementation
/ddd:3-code-plan

# Review the code plan, approve to continue

# Phase 4: Implement and test
/ddd:4-code

# Test, provide feedback, iterate until working

# Phase 5: Finalize
/ddd:5-finish

# Cleanup, push, PR (with your explicit approval at each step)
```

### Checking Progress Mid-Stream

```bash
# See where you are in the workflow
/ddd:status

# It will tell you:
# - Current phase
# - Artifacts created
# - Next recommended command
```

### Resuming After Break

```bash
# Check status
/ddd:status

# Run next phase (artifacts are preserved)
/ddd:3-code-plan
```

---

## Key Design Decisions

### No Auto-Commits

**Every git operation requires explicit user authorization**:

- You review changes before committing
- You control commit messages
- You decide when to push
- You approve PR creation

### Iteration Support

**Phases 2 and 4 are designed for back-and-forth**:

- Provide feedback at any time
- Commands stay active until you're satisfied
- Easy to iterate without restarting

### Artifact-Driven

**Each phase creates artifacts for next phase**:

- Can run without arguments (uses artifacts)
- Can override with arguments if needed
- State preserved across sessions

### Agent Orchestration

**Each phase suggests specialized agents**:

- zen-architect for design
- modular-builder for implementation
- bug-hunter for debugging
- test-coverage for tests
- post-task-cleanup for cleanup

---

## Authorization Checkpoints

### Phase 2 (Docs)

- ⚠️ **YOU must commit docs after review**
- Command stages changes but does NOT commit
- Review diff, iterate if needed, then commit when satisfied

### Phase 4 (Code)

- ⚠️ **Each code chunk requires explicit commit authorization**
- Command asks before each commit
- You control commit messages and timing

### Phase 5 (Finish)

- ⚠️ **Explicit authorization for**: commit remaining, push, create PR
- Clear prompts at each decision point
- You control what happens to your code

---

## Common Workflows

### Feature Development

1-plan → 2-docs → 3-code-plan → 4-code → 5-finish

### Bug Fix with Docs

1-plan → 2-docs → 3-code-plan → 4-code → 5-finish

### Documentation-Only Change

1-plan → 2-docs → 5-finish (skip code phases)

### Refactoring

1-plan → 2-docs → 3-code-plan → 4-code → 5-finish

---

## Troubleshooting

### "I'm lost, where am I?"

```bash
/ddd:status
```

### "I made a mistake in planning"

Edit `ai_working/ddd/plan.md` or re-run `/ddd:1-plan` with corrections

### "Docs aren't right"

Stay in phase 2, provide feedback, command will iterate

### "Code isn't working"

Stay in phase 4, provide feedback, iterate until working

### "I want to start over"

```bash
rm -rf ai_working/ddd/
/ddd:1-plan [your feature]
```

### "I need to understand a concept better"

Check the loaded documentation:

- @docs/document_driven_development/overview.md
- @docs/document_driven_development/core_concepts/file_crawling.md
- @docs/document_driven_development/core_concepts/context_poisoning.md
- @docs/document_driven_development/core_concepts/retcon_writing.md

---

## Tips for Success

### For Humans

- Start with `/ddd:prime` to load full context
- Use `/ddd:status` frequently to stay oriented
- Trust the process - it prevents expensive mistakes
- Review thoroughly at approval gates
- Iterate as much as needed in phases 2 and 4

### For AI Assistants

- Follow the phase strictly
- Use TodoWrite in every phase
- Suggest appropriate agents
- Never commit without explicit authorization
- Iterate based on user feedback
- Exit phases only when user confirms ready

---

## Philosophy Alignment

Every phase checks against:

**Ruthless Simplicity**:

- Start minimal, grow as needed
- Avoid future-proofing
- Question every abstraction
- Clear over clever

**Modular Design**:

- Clear interfaces (studs)
- Self-contained modules (bricks)
- Regeneratable from specs
- Human architects, AI builds

---

## Quick Reference Card

| Command            | Purpose            | Output Artifact                | Next Step                                   |
| ------------------ | ------------------ | ------------------------------ | ------------------------------------------- |
| `/ddd:prime`       | Load context       | -                              | Start workflow                              |
| `/ddd:status`      | Check progress     | -                              | Shows next command                          |
| `/ddd:1-plan`      | Design feature     | plan.md                        | `/ddd:2-docs`                               |
| `/ddd:2-docs`      | Update non-code    | docs_status.md                 | User commits, then `/ddd:3-code-plan`       |
| `/ddd:3-code-plan` | Plan code          | code_plan.md                   | User approves, then `/ddd:4-code`           |
| `/ddd:4-code`      | Implement & test   | impl_status.md, test_report.md | User confirms working, then `/ddd:5-finish` |
| `/ddd:5-finish`    | Cleanup & finalize | -                              | Done!                                       |

---

## Need More Help?

**Loaded Documentation**:

- Overview is now in your context
- Tips and common pitfalls are loaded
- FAQ is available

**Ask Specific Questions**:

- "How do I handle X?"
- "What if Y happens?"
- "Explain Z concept"

**Check Phase-Specific Help**:
Each command has detailed instructions for its phase.

---

Ready to start? Run `/ddd:1-plan [describe your feature]`
