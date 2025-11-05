# Phase 1: Documentation Retcon

**Update ALL documentation to describe the target state as if it already exists**

---

## Goal

Update every piece of documentation to reflect the target state using [retcon writing](../core_concepts/retcon_writing.md). Write as if the feature already exists and always worked this way.

**Critical**: Do NOT commit documentation yet. Iterate with human feedback until approved in Phase 2.

---

## Why Retcon First?

**Why documentation before code**:
- Design flaws cheaper to fix in docs than code
- Clear specification before implementation complexity
- Human reviews design before expensive coding
- Prevents implementing wrong thing

**Why retcon style**:
- Eliminates ambiguity (single timeline: NOW)
- Prevents [context poisoning](../core_concepts/context_poisoning.md)
- Clear for both AI and humans
- No historical confusion

---

## Overview of Steps

```
Step 1: Generate File Index
    ↓
Step 2: Sequential File Processing (file crawling)
    ↓
Step 3: Apply Retcon Writing Rules
    ↓
Step 4: Enforce Maximum DRY
    ↓
Step 5: Global Replacements (helper only)
    ↓
Step 6: Detect and Resolve Conflicts
    ↓
Step 7: Progressive Organization
    ↓
Step 8: Verification Pass
    ↓
Ready for Phase 2 (Approval)
```

---

## Step 1: Generate File Index

Use [file crawling technique](../core_concepts/file_crawling.md) for systematic processing.

```bash
# Find all non-code files to update
find . -type f \
  \( -name "*.md" -o -name "*.yaml" -o -name "*.toml" \) \
  ! -path "*/.git/*" \
  ! -path "*/.venv/*" \
  ! -path "*/node_modules/*" \
  > /tmp/docs_to_process.txt

# Convert to checklist format
sed 's/^/[ ] /' /tmp/docs_to_process.txt > /tmp/docs_checklist.txt

# Show checklist (once)
cat /tmp/docs_checklist.txt
```

**Why external file**: Tracks files outside AI's limited context. Saves 99.5% tokens.

---

## Step 2: Sequential File Processing

Process files ONE AT A TIME using [file crawling](../core_concepts/file_crawling.md#step-by-step-guide):

```bash
# Processing loop
while [ $(grep -c "^\[ \]" /tmp/docs_checklist.txt) -gt 0 ]; do
  # Get next uncompleted file (minimal tokens)
  NEXT=$(grep -m1 "^\[ \]" /tmp/docs_checklist.txt | sed 's/\[ \] //')

  echo "Processing: $NEXT"

  # AI reads this ONE file COMPLETELY
  # AI reviews ENTIRE file content
  # AI makes ALL needed updates
  # AI verifies changes

  # Mark complete ONLY after full individual review
  sed -i "s|\[ \] $NEXT|[x] $NEXT|" /tmp/docs_checklist.txt

  # Show progress periodically
  if [ $((counter % 10)) -eq 0 ]; then
    DONE=$(grep -c "^\[x\]" /tmp/docs_checklist.txt)
    TOTAL=$(wc -l < /tmp/docs_checklist.txt)
    echo "Progress: $DONE/$TOTAL files"
  fi
  counter=$((counter + 1))
done
```

**For each file**:
1. **Read ENTIRE file** - Full content, no skimming
2. **Review in context** - Understand file's purpose and scope
3. **Decide action**:
   - Update to target state (retcon)
   - Delete if duplicates another doc
   - Move if wrong location
   - Skip if already correct
4. **Apply changes** - Edit, delete, or move
5. **Mark complete** - Only after thorough review

**⚠️ ANTI-PATTERN**: Do NOT mark complete based on global replacements alone. Each file needs individual attention.

---

## Step 3: Apply Retcon Writing Rules

For each file being updated, follow [retcon writing rules](../core_concepts/retcon_writing.md#retcon-writing-rules):

### DO:

✅ Write in **present tense**: "The system does X"
✅ Write as if **always existed**: Current reality only
✅ Show **actual commands**: Examples that work now
✅ Use **canonical terminology**: No invented names
✅ **Document all complexity**: Be honest about requirements

### DON'T:

❌ "This will change to X"
❌ "Coming soon" or "planned"
❌ Migration notes in main docs
❌ Historical references ("used to")
❌ Version numbers in content
❌ Future-proofing

**Why**: See [Why Retcon Writing Matters](../core_concepts/retcon_writing.md#why-retcon-writing-matters)

---

## Step 4: Enforce Maximum DRY

**Rule**: Each concept lives in exactly ONE place. Zero duplication.

**Why critical**: Duplication causes [context poisoning](../core_concepts/context_poisoning.md). When one doc updates and another doesn't, AI loads inconsistent information.

### Finding Duplication

While processing files, ask:
- Does this content exist in another file?
- Is this concept already documented elsewhere?
- Am I duplicating another doc's scope?

### Resolving Duplication

**If found**:
1. Identify which doc is canonical
2. **Delete** the duplicate entirely (don't update it)
3. Update cross-references to canonical source

**Example**:
```bash
# Found: COMMAND_GUIDE.md duplicates USER_ONBOARDING.md

# Delete duplicate
rm docs/COMMAND_GUIDE.md

# Update cross-references
sed -i 's/COMMAND_GUIDE\.md/USER_ONBOARDING.md#commands/g' docs/*.md

# Verify deletion
grep -r "COMMAND_GUIDE" docs/  # Should find nothing
```

**Why delete vs. update**: If it exists, it will drift. Deletion is permanent elimination.

---

## Step 5: Global Replacements (Use with Extreme Caution)

Global replacements can help with terminology changes, but **are NOT a substitute for individual review**.

### How to Use Correctly

```bash
# 1. Run global replacement as FIRST PASS
sed -i 's/profile apply/profile use/g' docs/*.md
sed -i 's/\bworkflow\b/profile/g' docs/*.md

# 2. STILL review each file individually (Step 2)
# Global replace is helper, not solution

# 3. Verify worked correctly
grep -rn "profile apply" docs/  # Should be zero
grep -rn "\bworkflow\b" docs/   # Check each hit for context
```

### ⚠️ CRITICAL WARNING - ANTI-PATTERN

**Global replacements cause context poisoning when used as completion marker.**

**Problems**:
1. **Inconsistent formatting** - Misses variations
2. **Context-inappropriate** - Replaces wrong instances
3. **False confidence** - Files marked done without review

**Example of what goes wrong**:
```markdown
# File 1: "Use `profile apply`"  → Caught by replace
# File 2: "run profile-apply command" → Missed (hyphenated)
# File 3: "applying profiles" → Missed (verb form)

# Developer marks files "done" after global replace
# Files 2 and 3 still have old terminology
# Context poisoning introduced
```

**Correct approach**:
- Use as helper for first pass
- Still review EVERY file individually
- Verify replacement worked in context
- Make additional file-specific changes
- Mark complete only after full review

See [Common Pitfall #3](../reference/common_pitfalls.md#pitfall-3-global-replacements-as-completion) for more.

---

## Step 6: Detect and Resolve Conflicts

**If AI detects drift/inconsistency/conflicts between files**:

### ⚠️ PAUSE IMMEDIATELY

Do NOT continue. Do NOT fix without human guidance.

### Conflict Detection Pattern

```markdown
# AI detects while processing:

File 1 (docs/USER_GUIDE.md): calls it "workflow"
File 2 (docs/API.md): calls it "profile"
File 3 (docs/TUTORIAL.md): calls it "capability set"

# AI SHOULD PAUSE
```

### What AI Should Do

1. **Stop processing** - Don't mark more files complete
2. **Collect all instances** - Document every conflict
3. **Present to human** with analysis and options:

```markdown
# CONFLICT DETECTED - User guidance needed

## Issue
Inconsistent terminology found across documentation

## Instances
1. docs/USER_GUIDE.md:42: "workflow"
2. docs/API.md:15: "profile"
3. docs/TUTORIAL.md:8: "capability set"
4. README.md:25: uses both "workflow" and "profile"

## Analysis
- "profile" appears 47 times across 12 files
- "workflow" appears 23 times across 8 files
- "capability set" appears 3 times across 2 files

## Suggested Resolutions

Option A: Standardize on "profile"
- Pro: Most common, matches code
- Con: May confuse users familiar with "workflow"

Option B: Standardize on "capability set"
- Pro: More descriptive
- Con: More verbose

Option C: Define relationship, keep both
- Pro: Accommodates existing usage
- Con: Maintains ambiguity, risks context poisoning

## Recommendation
Option A - standardize on "profile" as canonical term

Please advise which resolution to apply.
```

4. **Wait for human decision**
5. **Apply resolution systematically** across all files
6. **Resume processing**

**Conflicts include**:
- Terminology (different words for same concept)
- Technical approaches (incompatible methods)
- Scope (unclear boundaries)
- Examples (code that contradicts)

**Why this matters**: Only human has full context to decide correctly. AI guessing introduces new context poisoning.

---

## Step 7: Progressive Documentation Organization

**Principle**: Organize for progressive understanding, not information dump.

### Documentation Hierarchy

```
README.md (Entry Point)
├─ Introduction (what is this?)
├─ Quick Start (working in 90 seconds)
├─ Key Concepts (3-5 ideas, brief)
└─ Next Steps (where to learn more)
   ├─ → User Guide (detailed usage)
   ├─ → Developer Guide (contributing)
   ├─ → API Reference (technical)
   └─ → Architecture (system design)
```

### Top-Level README Principles

✅ **Focus on awareness, not completeness** - "These things exist, find them here"
✅ **Progressive reveal** - Simple → detailed
✅ **Audience-appropriate** - Tailor to primary users
✅ **Action-oriented** - What can I do now?

❌ **Don't duplicate entire guides inline**
❌ **Don't compress to cryptic bullets**
❌ **Don't optimize for AI at expense of humans**
❌ **Don't mix all audience levels together**

### Example: Well-Organized README

```markdown
## Quick Start

### Step 1: Install (30 seconds)
```bash
curl -sSL https://install.sh | sh
```

### Step 2: Run (60 seconds)
```bash
myapp init
myapp run
```

**First time?** The init wizard guides you. [See detailed setup →](docs/USER_GUIDE.md#setup)

---

## Core Concepts

**Profiles** - Capability sets. [Learn more →](docs/PROFILES.md)
**Providers** - Infrastructure backends. [Learn more →](docs/PROVIDERS.md)
**Modules** - Pluggable functionality. [Browse modules →](docs/MODULES.md)

---

## Next Steps

**For users**: [User Guide](docs/USER_GUIDE.md)
**For developers**: [Developer Guide](docs/DEVELOPER_GUIDE.md)
**For architects**: [Architecture](docs/ARCHITECTURE.md)
```

### Audience-Specific Organization

**End-user applications**:
- README focuses on user experience
- Developer docs separate, linked from bottom

**Developer tools/libraries**:
- README focuses on developer quick start
- API reference prominent

**Platform/infrastructure**:
- README introduces capabilities
- Multiple audience paths clearly separated

### Balance Clarity and Conciseness

✅ **GOOD**: "Profiles define capability sets. Use `amplifier profile use dev` to activate the development profile."

❌ **TOO COMPRESSED**: "Profiles=caps. Use: amp prof use dev"

❌ **TOO VERBOSE**: "Profiles are comprehensive modular capability aggregation configurations..."

**Remember**: Documents are for humans first. AI can parse anything. Humans need clarity and flow.

---

## Step 8: Verification Pass

Before considering Phase 1 complete (but still NOT committing):

### Verification Checklist

- [ ] **Broken links check** - All cross-references work
- [ ] **Terminology consistency** - No old terms remain
- [ ] **Zero duplication** - Each concept in ONE place
- [ ] **Examples validity** - Commands use correct syntax
- [ ] **Philosophy compliance** - Follows IMPLEMENTATION_PHILOSOPHY.md and MODULAR_DESIGN_PHILOSOPHY.md
- [ ] **Human readability** - New person can understand

### Verification Commands

```bash
# Check for old terminology
grep -rn "old-term" docs/  # Should return zero

# Check for duplicate concepts
grep -rn "concept definition" docs/  # Single canonical location

# Verify historical references removed
grep -rn "previously\|used to\|old way" docs/  # Should be zero

# Check for future tense
grep -rn "will be\|coming soon" docs/  # Should be zero
```

---

## Common Issues and Fixes

### Issue: Files Missed During Processing

**Symptom**: Some files not in checklist, got skipped

**Fix**:
```bash
# Regenerate checklist with better filters
find . -type f -name "*.md" \
  ! -path "*/.git/*" \
  ! -path "*/.venv/*" \
  ! -path "*/node_modules/*" \
  ! -path "*/__pycache__/*" \
  > /tmp/complete_docs_list.txt

# Compare with what was processed
diff /tmp/docs_to_process.txt /tmp/complete_docs_list.txt

# Process missed files
```

### Issue: Duplicate Content Found Late

**Symptom**: Found duplication after processing many files

**Fix**:
1. Identify canonical source
2. Delete duplicate file
3. Update all cross-references
4. Re-process files that referenced duplicate
5. Verify with grep

### Issue: Inconsistent Terminology After Global Replace

**Symptom**: Some files still have old terms

**Fix**:
1. Find all remaining instances: `grep -rn "old-term" docs/`
2. Review each in context (might be intentional)
3. Fix individually
4. Update checklist for affected files

---

## Integration with Core Concepts

This phase relies heavily on core concepts:

**[File Crawling](../core_concepts/file_crawling.md)**:
- Step 1: Generate index
- Step 2: Sequential processing
- Prevents forgetting files

**[Context Poisoning](../core_concepts/context_poisoning.md)**:
- Step 4: Enforce maximum DRY
- Step 6: Detect and resolve conflicts
- Prevents inconsistent information

**[Retcon Writing](../core_concepts/retcon_writing.md)**:
- Step 3: Apply writing rules
- Step 7: Progressive organization
- Eliminates timeline ambiguity

---

## Output of Phase 1

When complete:
- ✅ All documentation describes target state
- ✅ Retcon writing style used throughout
- ✅ Maximum DRY enforced (no duplication)
- ✅ Progressive organization applied
- ✅ Verification pass complete
- ✅ All files in checklist marked `[x]`
- ⚠️ **NOT committed yet** - awaiting approval
- ⚠️ **NOT pushed** - Phase 2 next

**Ready for**: [Phase 2: Approval Gate](02_approval_gate.md)

---

## Tips for Success

### For AI Assistants

1. **Use file crawling** - Don't try to hold all files in context
2. **Read complete files** - No skimming
3. **Apply retcon rules strictly** - Present tense, as if already exists
4. **PAUSE on conflicts** - Never guess at resolution
5. **Mark complete honestly** - Only after full individual review
6. **Show progress** - Keep human informed

### For Humans

1. **Monitor progress** - Check checklist files periodically
2. **Don't commit yet** - Wait for Phase 2 approval
3. **Review samples** - Spot-check files during processing
4. **Provide clear decisions** - When AI pauses for conflicts

---

## Next Phase

**When Phase 1 complete**: [Phase 2: Approval Gate](02_approval_gate.md)

**Before proceeding**:
- All files processed
- No remaining `[ ]` in checklist
- Verification pass complete
- Ready for human review

---

**Return to**: [Phases](README.md) | [Main Index](../README.md)

**Prerequisites**: [Phase 0: Planning & Alignment](00_planning_and_alignment.md)

**Core Techniques**: [File Crawling](../core_concepts/file_crawling.md) | [Context Poisoning](../core_concepts/context_poisoning.md) | [Retcon Writing](../core_concepts/retcon_writing.md)
