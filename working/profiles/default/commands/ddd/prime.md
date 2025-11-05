---
description: Load complete DDD context for this session (project:ddd)
---

# Priming Document-Driven Development Context

Loading comprehensive DDD methodology documentation...

---

## Core DDD Documentation

@docs/document_driven_development/overview.md

---

## Core Concepts

These techniques are used throughout the workflow:

@docs/document_driven_development/core_concepts/file_crawling.md
@docs/document_driven_development/core_concepts/context_poisoning.md
@docs/document_driven_development/core_concepts/retcon_writing.md

---

## Phase Guides

Complete process documentation:

@docs/document_driven_development/phases/00_planning_and_alignment.md
@docs/document_driven_development/phases/01_documentation_retcon.md
@docs/document_driven_development/phases/02_approval_gate.md
@docs/document_driven_development/phases/03_implementation_planning.md
@docs/document_driven_development/phases/04_code_implementation.md
@docs/document_driven_development/phases/05_testing_and_verification.md
@docs/document_driven_development/phases/06_cleanup_and_push.md

---

## Philosophy Foundation

The principles that guide DDD:

@ai_context/IMPLEMENTATION_PHILOSOPHY.md
@ai_context/MODULAR_DESIGN_PHILOSOPHY.md

---

## Reference Materials

Quick references and troubleshooting:

@docs/document_driven_development/reference/checklists.md
@docs/document_driven_development/reference/tips_for_success.md
@docs/document_driven_development/reference/common_pitfalls.md
@docs/document_driven_development/reference/faq.md

---

## ✅ DDD Context Loaded Successfully

You now have complete understanding of Document-Driven Development:

**Core Principle**: Documentation IS the specification. Code implements what documentation describes.

**Workflow**:

1. `/ddd:1-plan` - Planning & Design
2. `/ddd:2-docs` - Update All Non-Code Files
3. `/ddd:3-code-plan` - Plan Code Changes
4. `/ddd:4-code` - Implement & Verify
5. `/ddd:5-finish` - Wrap-Up & Cleanup

**Utilities**:

- `/ddd:status` - Check current progress
- `/ddd:0-help` - Complete guide and help

---

## Quick Start

**Starting a new feature?**

```bash
/ddd:1-plan [describe your feature]
```

**Resuming existing work?**

```bash
# Check where you are
/ddd:status

# Then run the recommended next command
```

**Need help?**

```bash
/ddd:0-help
```

---

## What You Now Understand

### Why DDD Works

- **Prevents context poisoning**: Single source of truth, no conflicting docs
- **Clear contracts first**: Design reviewed before expensive implementation
- **AI-optimized**: Clear specifications, no guessing
- **No drift**: Docs and code never diverge by design
- **Better decisions**: Human judgment applied at planning phase

### Key Techniques

- **File Crawling**: Process many files systematically (99.5% token reduction)
- **Retcon Writing**: Write as if feature already exists (no "will be")
- **Context Poisoning Prevention**: Maximum DRY, eliminate conflicts
- **Progressive Organization**: Right-sized docs (README → Overview → Details)
- **Test as User**: AI is QA entity, actually uses the feature

### Philosophy Alignment

- **Ruthless Simplicity**: Start minimal, avoid future-proofing, clear over clever
- **Modular Design**: Bricks (modules) and studs (interfaces), regeneratable from specs
- **Human Architects, AI Builds**: Human designs and reviews, AI implements

### Authorization Model

- **User controls all git operations**: No auto-commits, explicit approval required
- **Iteration supported**: Phases 2 and 4 stay active until user satisfied
- **Clear checkpoints**: Approval gates prevent rushing ahead

---

## Context Management

**This loading happens once per session.**

For subsequent work in the same session:

- Context is already loaded
- Just run the commands
- No need to re-prime

**If starting new session:**

- Run `/ddd:prime` again to reload context
- Or just start with `/ddd:1-plan` and it will load relevant context

---

## Next Steps

You're ready to use Document-Driven Development!

**For your first feature:**

```bash
# 1. Plan it
/ddd:1-plan [describe feature]

# 2. Follow the workflow through each phase

# 3. Use /ddd:status to stay oriented
```

**For help anytime:**

```bash
/ddd:0-help     # Complete guide
/ddd:status     # Current progress
```

---

## Process

- Ultrathink step-by-step, laying out assumptions and unknowns, use the TodoWrite tool to capture all tasks and subtasks.
  - VERY IMPORTANT: Make sure to use the actual TodoWrite tool for todo lists, don't do your own task tracking, there is code behind use of the TodoWrite tool that is invisible to you that ensures that all tasks are completed fully.
  - Adhere to the @ai_context/IMPLEMENTATION_PHILOSOPHY.md and @ai_context/MODULAR_DESIGN_PHILOSOPHY.md files.
- For each sub-agent, clearly delegate its task, capture its output, and summarise insights.
- Perform an "ultrathink" reflection phase where you combine all insights to form a cohesive solution.
- If gaps remain, iterate (spawn sub-agents again) until confident.
- Where possible, spawn sub-agents in parallel to expedite the process.

**Context loaded. Ready to build! 🚀**
