# Context Poisoning

**Understanding and preventing inconsistent information that misleads AI tools**

---

## What is Context Poisoning?

**Context poisoning** occurs when AI tools load inconsistent or conflicting information from the codebase, leading to wrong decisions and implementations.

**Metaphor**: Imagine a chef following multiple recipes for the same dish that contradict each other on ingredients and temperatures. The dish will fail. Same with code - AI following contradictory "recipes" (documentation) produces broken implementations.

---

## Why It's Critical

When AI tools load context for a task, they may:
- Load stale doc instead of current one
- Load conflicting docs and guess wrong
- Not know which source is authoritative
- Combine information incorrectly
- Make wrong decisions confidently

**Real-world impact**:
- Wasted hours implementing wrong design
- Bugs from mixing incompatible approaches
- Rework when conflicts discovered later
- User confusion when docs contradict
- Loss of trust in documentation

---

## Common Sources

### 1. Duplicate Documentation
Same concept described differently in multiple files

**Example**:
- `docs/USER_GUIDE.md`: "Workflows configure your environment"
- `docs/API.md`: "Profiles define capability sets"

**Impact**: AI doesn't know if "workflow" == "profile" or they're different

### 2. Stale Documentation
Docs don't match current code

**Example**:
- Docs: "Use `amplifier setup` to configure"
- Code: Only `amplifier init` works

**Impact**: AI generates code using removed command

### 3. Inconsistent Terminology
Multiple terms for same concept

**Example**:
- README: "workflow"
- USER_GUIDE: "profile"
- API: "capability set"

**Impact**: AI confused about canonical term

### 4. Partial Updates
Updated some files but not others

**Example**:
- Updated README with new flags (`--model`)
- Forgot to update COMMAND_REFERENCE
- COMMAND_REFERENCE now has wrong syntax

**Impact**: AI uses outdated syntax from COMMAND_REFERENCE

### 5. Historical References
Old approaches mentioned alongside new

**Example**:
```markdown
Previously, use `setup`. Now use `init`.
For now, both work.
```

**Impact**: AI implements BOTH, doesn't know which is current

---

## Real Example from Practice

**Context poisoning caught live during development**:

### What Happened

1. Created `docs/COMMAND_REFERENCE.md` with command syntax
2. Updated `README.md` with new provider-specific flags (`--model`, `--deployment`)
3. `COMMAND_REFERENCE.md` now out of sync - doesn't show new flags
4. Future AI loads outdated syntax from `COMMAND_REFERENCE.md`
5. AI generates code using old syntax without required flags

### The Cost

- Bugs in generated code
- User confusion (docs say one thing, code requires another)
- Rework needed to fix
- Lost trust in documentation

### The Fix

- **Deleted** `COMMAND_REFERENCE.md` entirely
- Moved unique content to `USER_ONBOARDING.md#quick-reference`
- Single source of truth restored

### The Lesson

**Even small duplication causes immediate problems. If file exists, it will drift.**

---

## Types of Context Poisoning

### Type 1: Terminology Conflicts

```markdown
# docs/USER_GUIDE.md
Use workflows to configure environment.
Run: amplifier workflow apply dev

# docs/API.md
Profiles define capability sets.
Run: amplifier profile use dev

# POISON: Are "workflow" and "profile" the same? Different?
```

### Type 2: Behavioral Conflicts

```markdown
# docs/USER_GUIDE.md
The --model flag is optional. Defaults to claude-sonnet-4-5.

# docs/API.md
The --model flag is required. Command fails without it.

# POISON: Is --model required or optional?
```

### Type 3: Example Conflicts

```markdown
# README.md
amplifier provider use anthropic

# docs/USER_GUIDE.md
amplifier provider use anthropic --model claude-opus-4

# POISON: Which example is correct?
```

### Type 4: Historical References

```markdown
# docs/MIGRATION.md
Previously, use `amplifier setup`.
Now, use `amplifier init` instead.
The old `setup` command still works.

# POISON: Should AI implement setup, init, or both?
```

### Type 5: Scope Conflicts

```markdown
# docs/ARCHITECTURE.md
Provider configuration is immutable per session.

# docs/USER_GUIDE.md
Use --local flag to override provider per project.

# POISON: Is provider immutable or overridable?
```

---

## Prevention Strategies

### 1. Maximum DRY (Don't Repeat Yourself)

**Rule**: Each concept lives in exactly ONE place.

**Good organization**:
- ✅ Command syntax → `docs/USER_ONBOARDING.md#quick-reference`
- ✅ Architecture → `docs/ARCHITECTURE.md`
- ✅ API reference → `docs/API.md`

**Cross-reference, don't duplicate**:
```markdown
For command syntax, see [USER_ONBOARDING.md#quick-reference](...)

NOT: Duplicating all command syntax inline
```

### 2. Aggressive Deletion

When you find duplication:
1. Identify which doc is canonical
2. **Delete** the duplicate entirely (don't update it)
3. Update cross-references to canonical source

**Why delete vs. update?**
- Prevents future divergence
- If it exists, it will drift
- Deletion is permanent elimination

**Example**:
```bash
# Found duplication: COMMAND_GUIDE.md duplicates USER_ONBOARDING.md

# Delete duplicate
rm docs/COMMAND_GUIDE.md

# Update cross-references
sed -i 's/COMMAND_GUIDE\.md/USER_ONBOARDING.md#commands/g' docs/*.md

# Verify gone
grep -r "COMMAND_GUIDE" docs/  # Should find nothing
```

### 3. Retcon, Don't Evolve

**BAD** (creates poison):
```markdown
Previously, use `amplifier setup`.
As of version 2.0, use `amplifier init`.
In future, `setup` will be removed.
For now, both work.
```

**GOOD** (clean retcon):
```markdown
## Provider Configuration

Configure your provider:
```bash
amplifier init
```

Historical info belongs in git history and CHANGELOG, not docs.

See [Retcon Writing](retcon_writing.md) for details.

### 4. Systematic Global Updates

When terminology changes:
```bash
# 1. Global replace (first pass only)
find docs/ -name "*.md" -exec sed -i 's/\bworkflow\b/profile/g' {} +

# 2. STILL review each file individually
# Global replace is helper, not solution

# 3. Verify
grep -rn "\bworkflow\b" docs/  # Should be zero or intentional

# 4. Commit together
git commit -am "docs: Standardize terminology: workflow → profile"
```

### 5. Catch During File Processing

When using [file crawling](file_crawling.md), check each file for conflicts.

**If detected**: PAUSE, collect all instances, ask human for resolution.

See [Phase 1: Step 6](../phases/01_documentation_retcon.md#step-6-detecting-and-resolving-conflicts) for details.

---

## Detection and Resolution

### During Documentation Phase

**Watch for**:
- Conflicting definitions
- Duplicate content
- Inconsistent examples
- Historical baggage

**Action**: PAUSE, collect all instances, get human guidance

### During Implementation Phase

**Watch for AI saying**:
- "I see from COMMAND_REFERENCE.md that..." (when that file was deleted)
- "According to the old approach..." (no old approaches should be documented)
- "Both X and Y are valid..." (when only Y should be documented)
- "The docs are inconsistent about..." (PAUSE, fix docs)

**Action**: PAUSE immediately, document conflict, ask user

### Resolution Pattern

```markdown
# CONFLICT DETECTED - User guidance needed

## Issue
[Describe what conflicts]

## Instances
1. file1.md:42: says X
2. file2.md:15: says Y
3. file3.md:8: says Z

## Analysis
[What's most common, what matches code, etc.]

## Suggested Resolutions
Option A: [description]
- Pro: [benefits]
- Con: [drawbacks]

Option B: [description]
- Pro: [benefits]
- Con: [drawbacks]

## Recommendation
[AI's suggestion with reasoning]

Please advise which resolution to apply.
```

**Wait for human decision**, then apply systematically.

---

## Prevention Checklist

Before committing any documentation:

- [ ] No duplicate concepts across files
- [ ] Consistent terminology throughout
- [ ] No historical references (use retcon)
- [ ] All cross-references point to existing content
- [ ] Each doc has clear, non-overlapping scope
- [ ] Examples all work (test them)
- [ ] No "old way" and "new way" both shown
- [ ] Version numbers removed (docs always current)

---

## Measuring Context Poisoning

### Healthy Codebase (No Poisoning)

✅ `grep -r "duplicate-term" docs/` returns single canonical location
✅ AI tools make correct assumptions consistently
✅ New contributors understand system from docs alone
✅ Examples all work when copy-pasted
✅ No "which docs are current?" questions

### Warning Signs (Poisoning Present)

❌ Multiple files define same concept
❌ AI implements wrong approach confidently
❌ Contributors ask "which is right?"
❌ Examples don't work
❌ Frequent questions about terminology

---

## Real-World Examples

### Example 1: Command Reference Duplication

**Setup**:
- Created COMMAND_REFERENCE.md with all command syntax
- README.md also documents commands

**What happened**:
- Updated README with new flags
- Forgot COMMAND_REFERENCE
- Future AI loaded COMMAND_REFERENCE (wrong syntax)

**Fix**: Deleted COMMAND_REFERENCE entirely

### Example 2: Terminology Inconsistency

**Setup**:
- Some docs say "workflow"
- Some docs say "profile"
- Some docs say "capability set"

**What happened**:
- AI confused about canonical term
- Generated code mixing terms
- User confused reading docs

**Fix**: Chose "profile" as canonical, global replace + individual review

### Example 3: Historical References

**Setup**:
- Docs mentioned both old `setup` and new `init` commands
- Said "both work for now"

**What happened**:
- AI implemented both commands
- Maintained old approach unnecessarily
- More code to maintain

**Fix**: Retconned docs to show only `init`, removed historical references

---

## Quick Reference

### Detection

**Ask yourself**:
- Can same information be found in multiple places?
- Are there multiple terms for same concept?
- Do docs reference "old" vs "new" approaches?
- Do examples conflict with each other?

**If yes to any**: Context poisoning present

### Prevention

**Core rules**:
1. Each concept in ONE place only
2. Delete duplicates (don't update)
3. Use retcon (not evolution)
4. Consistent terminology everywhere
5. Test all examples work

### Resolution

**When detected**:
1. PAUSE all work
2. Collect all instances
3. Present to human with options
4. Wait for decision
5. Apply resolution systematically
6. Verify with grep

---

## Integration with DDD

Context poisoning prevention is built into every phase:

- **[Phase 0](../phases/00_planning_and_alignment.md)**: Check docs during reconnaissance
- **[Phase 1](../phases/01_documentation_retcon.md)**: Enforce maximum DRY
- **[Phase 2](../phases/02_approval_gate.md)**: Human catches inconsistencies
- **[Phase 4](../phases/04_code_implementation.md)**: Pause when docs conflict
- **[Phase 5](../phases/05_testing_and_verification.md)**: Examples reveal conflicts

**Result**: Context poisoning prevented by design, not by luck.

---

**Return to**: [Core Concepts](README.md) | [Main Index](../README.md)

**Related**: [File Crawling](file_crawling.md) | [Retcon Writing](retcon_writing.md)

**See Also**: [Phase 1 Step 4](../phases/01_documentation_retcon.md#step-4-maximum-dry-enforcement)
