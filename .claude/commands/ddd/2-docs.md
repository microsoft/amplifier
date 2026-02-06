---
description: DDD Phase 2 - Update all non-code files (project:ddd)
argument-hint: [optional override instructions]
allowed-tools: TodoWrite, Read, Write, Edit, MultiEdit, Grep, Glob, Task, Bash(git diff:*), Bash(git status:*), Bash(git add:*)
---

# DDD Phase 2: Non-Code Changes

Loading context:

@docs/document_driven_development/phases/01_documentation_retcon.md
@docs/document_driven_development/phases/02_approval_gate.md
@docs/document_driven_development/core_concepts/file_crawling.md
@docs/document_driven_development/core_concepts/retcon_writing.md
@docs/document_driven_development/core_concepts/context_poisoning.md
@ai_working/ddd/plan.md

Override instructions: $ARGUMENTS

---

## Your Task: Update All Non-Code Files

**Goal**: Update docs, configs, READMEs to reflect new feature AS IF IT ALREADY EXISTS

**This phase iterates until user approves - stay in this phase as long as needed**

---

## Phase 2 Steps

### 1. Generate File Index

Create `ai_working/ddd/docs_index.txt`:

```bash
# Read the plan to get list of non-code files
# Create checklist in format:
[ ] docs/file1.md
[ ] README.md
[ ] config/example.toml
...
```

This index is your working checklist - mark files complete as you process them.

### 2. File Crawling - Process One File at a Time

**THIS IS CRITICAL FOR SUCCESS**:

For each file in the index:

1. **Load full context**:

   - Read the file
   - Read relevant parts of plan
   - Load related docs if needed

2. **Update with retcon writing**:

   - Write as if feature ALREADY EXISTS
   - No "will be", "going to", "planned"
   - Present tense: "The system does X"
   - No historical references
   - No migration notes in docs

3. **Apply Maximum DRY**:

   - Each concept in ONE place only
   - No duplicate documentation
   - Use references/links instead of duplication
   - If found elsewhere, consolidate to best location

4. **Check for context poisoning**:

   - Conflicts with other docs?
   - Inconsistent terminology?
   - Contradictory statements?
   - If found: PAUSE, document conflicts, ask user

5. **Mark complete in index**:

   ```bash
   # Change [ ] to [x]
   [x] docs/file1.md
   ```

6. **Move to next file** - REPEAT until all files processed

**Why file crawling?**:

- Token efficiency (99.5% reduction for large batches)
- Prevents missing files
- Clear progress tracking
- Resumable if interrupted
- Avoids context overflow

### 3. Progressive Organization

As you update docs:

**Keep it right-sized**:

- Not over-compressed (missing critical info)
- Not overly detailed (lost in noise)
- Balance clarity vs completeness

**Follow structure**:

- README → Overview → Details
- High-level concepts first
- Specific details later
- Examples that actually work

**Audience-appropriate**:

- User docs: How to use it
- Developer docs: How it works
- Architecture docs: Why designed this way

### 4. Verification Pass

After all files updated:

1. **Read through all changed docs** (use file index)
2. **Check consistency**:
   - Terminology consistent?
   - Examples would work?
   - No contradictions?
3. **Verify DRY**:
   - Each concept in one place?
   - No duplicate explanations?
4. **Check philosophy alignment**:
   - Ruthless simplicity maintained?
   - Clear module boundaries?

### 5. Generate Review Materials

Create `ai_working/ddd/docs_status.md`:

```markdown
# Phase 2: Non-Code Changes Complete

## Summary

[High-level description of what was changed]

## Files Changed

[List from git status]

## Key Changes

### docs/file1.md

- [What changed and why]

### README.md

- [What changed and why]

[... for each file]

## Deviations from Plan

[Any changes from original plan and why]

## Approval Checklist

Please review the changes:

- [ ] All affected docs updated?
- [ ] Retcon writing applied (no "will be")?
- [ ] Maximum DRY enforced (no duplication)?
- [ ] Context poisoning eliminated?
- [ ] Progressive organization maintained?
- [ ] Philosophy principles followed?
- [ ] Examples work (could copy-paste and use)?
- [ ] No implementation details leaked into user docs?

## Git Diff Summary
```

[Insert: git diff --stat]

```

## Review Instructions

1. Review the git diff (shown below)
2. Check above checklist
3. Provide feedback for any changes needed
4. When satisfied, commit with your own message

## Next Steps After Commit

When you've committed the docs, run: `/ddd:3-code-plan`
```

### 6. Show Git Diff

Run these commands to show user the changes:

```bash
git add [changed files]
git status
git diff --cached --stat
git diff --cached
```

**IMPORTANT**: Stage the changes with `git add` but **DO NOT COMMIT**

---

## Iteration Loop

**This phase stays active until user approves**:

If user provides feedback:

1. Note the feedback
2. Make requested changes
3. Update docs_status.md
4. Show new diff
5. Repeat until user says "approved"

**Common feedback examples**:

- "This section needs more detail"
- "Example doesn't match our style"
- "Add documentation for X feature"
- "This contradicts docs/other.md"

**For each feedback**: Address it, then regenerate review materials

---

## Using TodoWrite

Track doc update tasks:

```markdown
- [ ] Generate file index
- [ ] Process file 1 of N
- [ ] Process file 2 of N
      ...
- [ ] Verification pass complete
- [ ] Review materials generated
- [ ] User review in progress
```

---

## Agent Suggestions

**concept-extractor** - For extracting knowledge from complex docs:

```
Task concept-extractor: "Extract key concepts from [source] to include
in [target doc]"
```

**ambiguity-guardian** - If docs have tensions/contradictions:

```
Task ambiguity-guardian: "Analyze apparent contradiction between
[doc1] and [doc2], determine if both views are valid"
```

---

## Retcon Writing Examples

**❌ BAD (Traditional)**:

```markdown
## Authentication (Coming in v2.0)

We will add JWT authentication support. Users will be able to
authenticate with tokens. This feature is planned for next quarter.

Migration: Update your config to add `auth: jwt` section.
```

**✅ GOOD (Retcon)**:

````markdown
## Authentication

The system uses JWT authentication. Users authenticate with tokens
that expire after 24 hours.

Configure authentication in your config file:

```yaml
auth:
  type: jwt
  expiry: 24h
```
````

See [Authentication Guide](auth.md) for details.

```

---

## Context Poisoning Detection

**PAUSE if you find**:
- Same concept explained differently in multiple places
- Contradictory statements about behavior
- Inconsistent terminology for same thing
- Feature described differently in different docs

**Actions when found**:
1. Document the conflicts
2. Note which docs conflict
3. Ask user: "Which version is correct?"
4. After clarification, fix ALL instances

---

## Important Notes

**Maximum DRY is critical**:
- If you copy-paste content between docs: WRONG
- If same concept appears twice: CONSOLIDATE
- Use links/references instead of duplication

**Retcon everywhere**:
- User docs: "The system does X"
- Developer docs: "The module implements Y"
- Config examples: Show the actual config (it works)
- No "TODO", "Coming soon", "Will be added"

**Stage but don't commit**:
- Use `git add` to stage
- Show diff to user
- Let USER commit when satisfied
- USER writes commit message

---

## When User Approves

### Exit Message

```

✅ Phase 2 Complete: Non-Code Changes Approved

All documentation updated and staged.

⚠️ USER ACTION REQUIRED:
Review the changes above and commit when satisfied:

    git commit -m "docs: [your description]"

After committing, proceed to code planning:

    /ddd:3-code-plan

The updated docs are now the specification that code must match.

```

## Process

- Ultrathink step-by-step, laying out assumptions and unknowns, use the TodoWrite tool to capture all tasks and subtasks.
  - VERY IMPORTANT: Make sure to use the actual TodoWrite tool for todo lists, don't do your own task tracking, there is code behind use of the TodoWrite tool that is invisible to you that ensures that all tasks are completed fully.
  - Adhere to the @ai_context/IMPLEMENTATION_PHILOSOPHY.md and @ai_context/MODULAR_DESIGN_PHILOSOPHY.md files.
- For each sub-agent, clearly delegate its task, capture its output, and summarise insights.
- Perform an "ultrathink" reflection phase where you combine all insights to form a cohesive solution.
- If gaps remain, iterate (spawn sub-agents again) until confident.
- Where possible, spawn sub-agents in parallel to expedite the process.

---

## Troubleshooting

**"Too many files to track"**
- That's what file crawling solves
- Use the index file as checklist
- Process one at a time

**"Found conflicts between docs"**
- Document them clearly
- Ask user which is correct
- Fix all instances after clarification

**"Unsure how much detail to include"**
- Follow progressive organization
- Start with high-level in main docs
- Link to detailed docs for specifics
- Ask user if uncertain

**"User feedback requires major rework"**
- That's fine! Better now than after code is written
- This is why we have approval gate before coding
- Iterate as many times as needed

---

Need help? Run `/ddd:0-help` for complete guide
```
