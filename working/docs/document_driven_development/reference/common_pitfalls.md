# Common Pitfalls

**What goes wrong, how to recognize it, and how to fix it**

---

## Overview

These are the most common mistakes made when using Document-Driven Development, along with practical guidance for recognizing and recovering from them.

---

## Pitfall 1: Skipping Planning Phase

### The Problem

Diving straight into documentation without achieving shared understanding first.

### What Happens

- AI implements different design than you envisioned
- Wasted effort on wrong approach
- Major rework needed after approval
- Frustration on both sides

### Warning Signs

- User says "that's not what I meant" after doc retcon
- AI's explanation doesn't match your mental model
- Proposals seem off-base or missing key points

### How to Recover

```markdown
# If caught after documentation started:

1. STOP immediately
2. Return to [Phase 0](../phases/00_planning_and_alignment.md)
3. Re-establish shared understanding
4. Get clear approval on correct design
5. Start Phase 1 over with correct design
```

### Prevention

- Be patient in Phase 0
- Iterate on proposals until aligned
- Ask AI to articulate plan back
- Approve explicitly when aligned

**Better 2 hours in Phase 0 than 2 days of rework.**

---

## Pitfall 2: Trying to Hold Everything in Context

### The Problem

AI tries to process all files at once without [file crawling](../core_concepts/file_crawling.md).

### What Happens

- Attention degradation - misses files in large lists
- Token waste - loading unnecessary content
- False confidence - AI thinks it processed all
- Incomplete work - many files actually skipped
- [Context poisoning](../core_concepts/context_poisoning.md) from missing updates

### Warning Signs

- AI says "processed all 100 files" but shows work on only 20
- Files marked complete without individual review
- Global replacements used as completion marker
- User finds untouched files after "completion"

### How to Recover

```bash
# Check what was actually done
grep "^\[x\]" /tmp/checklist.txt  # What AI marked complete
git diff --name-only  # What actually changed

# Reset incomplete items
sed -i 's/^\[x\] \(.*\.md\)$/[ ] \1/' /tmp/checklist.txt

# Manually mark only verified-complete files
# Resume with file crawling
```

### Prevention

- Use [file crawling](../core_concepts/file_crawling.md) for 10+ files
- Process one file at a time
- Verify checklist shows all `[x]` before proceeding

---

## Pitfall 3: Global Replacements as Completion

### The Problem

Run global find/replace, mark all files "done" without individual review.

### What Happens

- Replacements miss inconsistently-formatted instances
- Replacements change wrong instances (context-inappropriate)
- File-specific changes never made
- [Context poisoning](../core_concepts/context_poisoning.md) from inconsistent updates
- False confidence - files marked complete but incomplete

### Warning Signs

- AI runs `sed -i 's/old/new/g'` then marks files done
- No individual file review performed
- Files "completed" in seconds (too fast)
- Specific changes from plan not visible in diffs

### How to Recover

```bash
# Verify what global replace caught
grep -rn "old-term" docs/  # Should be zero if replace worked

# If results remain, understand why:
# - Different formatting?
# - Context-appropriate use?
# - Pattern wrong?

# Unmark all files
sed -i 's/^\[x\]/[ ]/' /tmp/checklist.txt

# Resume with individual review
# Read each file completely
# Verify replace worked correctly
# Make additional changes needed
# Mark complete only after full review
```

### Prevention

- Global replace is HELPER only, not solution
- Always review every file individually
- Mark complete only after full review
- Use verification grep to check results

**See**: [Phase 1 Step 5](../phases/01_documentation_retcon.md#step-5-global-replacements-use-with-extreme-caution)

---

## Pitfall 4: Implementation Before Approval

### The Problem

Starting code while docs still under review.

### What Happens

- Code implements wrong or incomplete spec
- Rework when docs corrected
- Wasted implementation effort
- Confusion about what's authoritative

### Warning Signs

- AI working on code during Phase 1 or 2
- Implementation happening while user commenting on docs
- "I'll just start the easy parts" mentality

### How to Recover

```markdown
# If code started too early:

1. STOP all implementation
2. Return to Phase 2
3. Fix documentation per user feedback
4. Get explicit approval
5. Review code against corrected docs
6. Update or rewrite code to match
7. Resume only after alignment
```

### Prevention

- Hard gate at Phase 2 approval
- No code until explicit approval
- User says "approved, proceed to implementation"
- [Phase 2](../phases/02_approval_gate.md) checklist complete

---

## Pitfall 5: Not Loading Full Context for Subtasks

### The Problem

Implement feature without reading related code, patterns, or tests.

### What Happens

- Breaks existing patterns
- Inconsistent code style
- Misses edge cases already handled
- Reinvents existing solutions
- [Context poisoning](../core_concepts/context_poisoning.md) when new code conflicts with old

### Warning Signs

- AI implements without reading related files
- New code doesn't match existing patterns
- Edge cases not handled
- Duplicates existing functionality

### How to Recover

```markdown
# If caught after implementation:

1. Read SettingsManager and ProfileManager
2. Read tests to understand patterns
3. Identify where new code diverges
4. Refactor to match established patterns
5. Update tests to match existing style
```

### Prevention

- Always load full context before implementation
- Read: spec from docs, related code, existing tests
- Check for conflicts before coding
- Follow [Phase 4](../phases/04_code_implementation.md#loading-full-context-critical) guidance

---

## Pitfall 6: Documentation Drifts During Implementation

### The Problem

Discover implementation needs to differ, change code but not docs.

### What Happens

- Docs and code out of sync immediately
- [Context poisoning](../core_concepts/context_poisoning.md) - future AI reads wrong spec
- Users follow docs, get unexpected behavior
- Lost benefit of documentation-driven approach

### Warning Signs

- Implementation doesn't match docs
- AI says "docs were wrong, fixed code"
- Examples in docs don't work with implementation
- User says "docs say X but it does Y"

### How to Recover

```markdown
# If drift detected:

## Situation
Implemented provider use. Testing revealed --model should be
optional with defaults, but docs say it's required.

## Action - DO NOT just change code!

1. PAUSE implementation
2. Document the mismatch
3. Propose doc fix to user
4. Get approval
5. Return to Phase 1 - fix documentation
6. Update code to match corrected docs
7. Resume testing
```

### Prevention

- Documentation remains source of truth always
- If code needs to differ, update docs first (with approval)
- Never Code → "close enough to docs"
- Test against docs to catch drift early

---

## Pitfall 7: Ignoring Conflict Detection

### The Problem

AI detects conflicts but continues anyway, guessing at resolution.

### What Happens

- Wrong resolution applied
- Conflict spreads to more files
- User discovers conflict later (expensive)
- More [context poisoning](../core_concepts/context_poisoning.md) introduced

### Warning Signs

- AI says "found conflict, choosing option A"
- AI continues despite detecting inconsistency
- No user consultation when sources conflict

### How to Recover

```markdown
# If AI continued past conflict:

1. Identify all files AI changed
2. Undo: git reset --hard HEAD~N
3. Return to conflict point
4. Present conflict properly to user
5. Get user decision
6. Apply correct resolution systematically
7. Resume work
```

### Prevention

- Hard rule: PAUSE on ANY conflict
- Only human decides resolution
- AI detects and proposes, never decides
- See [conflict resolution pattern](../core_concepts/context_poisoning.md#detection-and-resolution)

---

## Pitfall 8: Skipping User Testing

### The Problem

AI runs unit tests but doesn't test as actual user would.

### What Happens

- Misses UX issues
- Misses workflow problems
- Misses integration issues
- Issues discovered only during human review

### Warning Signs

- AI only runs `make test`
- No user testing report created
- No recommended smoke tests for human
- Testing section mentions only unit tests

### How to Recover

```markdown
# Before proceeding to Phase 6:

1. Return to Phase 5 Step 3
2. Actually run the tool as user would
3. Test main scenarios from documentation
4. Create detailed user testing report
5. Provide recommended smoke tests
6. Fix any issues found
```

### Prevention

- Explicitly require user testing
- Ask for detailed report in ai_working/
- Expect recommendations for human testing
- See [Phase 5 Step 3](../phases/05_testing_and_verification.md#step-3-test-as-user-would-critical)

---

## Pitfall 9: Committing Before Approval

### The Problem

Committing documentation changes during iteration before human approval.

### What Happens

- Git log thrashed with wrong versions
- Multiple "oops, undo that" commits
- Harder to track what was actually decided
- Git history is context poisoning source

### Warning Signs

- Multiple commits during Phase 1
- Commit messages like "fix docs again"
- Git log shows iteration history

### How to Recover

```bash
# If already committed wrong versions:

# Soft reset to before documentation commits
git reset --soft HEAD~N

# All changes now unstaged
# Fix documentation with user feedback
# Get approval
# Make SINGLE commit with approved docs
```

### Prevention

- Do NOT commit during Phase 1
- Iterate until approved in Phase 2
- THEN commit once with approval
- See [Phase 2](../phases/02_approval_gate.md)

---

## Quick Reference: Recovery Patterns

### Conflict Detected

1. STOP all work
2. Collect all instances
3. Present to human with options
4. Wait for decision
5. Apply systematically
6. Resume

### Files Missed

1. Regenerate checklist
2. Compare with original
3. Process missed files
4. Verify all complete

### Implementation Doesn't Match Docs

1. PAUSE
2. Propose doc update to human
3. Get approval
4. Fix docs (Phase 1)
5. Update code to match
6. Resume

---

**Return to**: [Reference](README.md) | [Main Index](../README.md)

**See Also**: [Tips for Success](tips_for_success.md) | [FAQ](faq.md) | [Checklists](checklists.md)
