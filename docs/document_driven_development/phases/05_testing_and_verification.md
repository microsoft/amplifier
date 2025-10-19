# Phase 5: Testing & Verification

**Verify code matches documentation specification and works as users will use it**

---

## Goal

Verify that code matches documentation specification through two critical layers:
1. **Test documented behaviors** - Does code do what docs promise?
2. **Test as actual user** - Does it work the way users will use it?

**Philosophy**: Test what docs promise. If docs say it works, it must work. AI is the QA entity before human review.

---

## Why Two Testing Layers?

### Code-Based Tests (Traditional)

**What they verify**:
- Implementation details
- Unit logic correctness
- Integration points
- Edge cases

**What they miss**:
- Confusing UX
- Broken end-to-end workflows
- Unclear output messages
- Real-world usage patterns

### User Testing (Critical Addition)

**What it verifies**:
- Actual user experience
- End-to-end workflows
- Output clarity
- Integration with real environment
- Behavior matches documentation

**What it catches**:
- Commands that technically work but are confusing
- Output that's correct but unclear
- Workflows broken end-to-end
- Integration issues between components
- Real scenarios not covered by unit tests

**Together**: Comprehensive verification of both implementation AND experience.

---

## Overview of Steps

```
Step 1: Test Against Specification
    ↓
Step 2: Systematic Testing (file crawling)
    ↓
Step 3: Test As User Would (CRITICAL)
    ↓
Step 4: Create User Testing Report
    ↓
Step 5: Handle Mismatches
    ↓
Step 6: Code-Based Test Verification
    ↓
Ready for Phase 6 (Cleanup & Push)
```

---

## Step 1: Test Against Specification

For each documented behavior, verify it works:

1. **Find the doc** - Where is this behavior described?
2. **Extract the example** - What command/code does doc show?
3. **Run the example** - Does it actually work?
4. **Verify output** - Does it match what docs say?
5. **Test edge cases** - Error handling, invalid inputs

**Example**:
```bash
# From docs/USER_ONBOARDING.md:45
amplifier provider use anthropic --model claude-opus-4 --local

# Run it
$ amplifier provider use anthropic --model claude-opus-4 --local

# Verify output matches docs
Expected: "✓ Provider configured: anthropic (claude-opus-4)"
Actual: [must match]

# Verify behavior
$ amplifier provider current
Expected: Shows anthropic with claude-opus-4
Actual: [must match]
```

---

## Step 2: Systematic Testing with File Crawling

Use [file crawling](../core_concepts/file_crawling.md) for comprehensive testing:

```bash
# Generate test checklist from documentation
cat > /tmp/test_checklist.txt << 'EOF'
[ ] Test: README.md Quick Start flow
[ ] Test: USER_ONBOARDING.md provider use command
[ ] Test: USER_ONBOARDING.md provider list command
[ ] Test: USER_ONBOARDING.md profile use with --local
[ ] Test: API.md provider configuration examples
[ ] Test: Error handling for missing API key
[ ] Test: Error handling for invalid provider
EOF

# Process each test
while [ $(grep -c "^\[ \]" /tmp/test_checklist.txt) -gt 0 ]; do
  NEXT=$(grep -m1 "^\[ \]" /tmp/test_checklist.txt | sed 's/\[ \] Test: //')

  echo "Testing: $NEXT"

  # AI runs this test:
  # 1. Extract example from doc
  # 2. Run it
  # 3. Verify output
  # 4. Pass/fail

  sed -i "s|\[ \] Test: $NEXT|[x] Test: $NEXT|" /tmp/test_checklist.txt
done
```

---

## Step 3: Test As User Would (CRITICAL)

**This is AI's QA role** - Before handing to human, AI must test as actual user.

### Why This Matters

**Code-based tests verify**: Implementation details
**User testing verifies**: Actual experience

**What user testing catches**:
- Commands that work but are confusing
- Output that's correct but unclear
- Workflows broken end-to-end
- Integration issues
- Real-world scenarios not in unit tests

### Testing Approach

**Identify user scenarios from documentation**:
- What are the main use cases?
- What does Quick Start promise?
- What workflows are documented?

**Actually run the tool as user would**:
- Not just unit tests
- Not mocked environment
- Real CLI commands
- Real user workflows

**Observe everything**:
- Command output (clear? correct?)
- Logs generated (any errors/warnings?)
- State changes (files created/modified correctly?)
- Artifacts produced (as expected?)
- System behavior (performance? responsiveness?)

**Verify expectations**:
- Does behavior match documentation?
- Would a user be confused?
- Are error messages helpful?
- Does workflow feel smooth?

### Example User Testing Session

```markdown
# User Testing Session - Provider Management Feature

## Test Environment
- OS: Ubuntu 22.04
- Python: 3.11.5
- Fresh install: Yes

## Scenario 1: First-time setup with Anthropic

**Documentation reference**: README.md Quick Start

**Steps (as user would do)**:
1. Install: `uvx --from git+https://...@next amplifier`
2. Run: `amplifier`
3. Follow init wizard prompts

**Observations**:
- ✅ Init wizard appeared automatically
- ✅ Provider selection clear (1-4 options)
- ✅ API key prompt clear with link
- ✅ Model selection presented options
- ✅ Profile selection clear
- ✅ Success message displayed
- ✅ Chat started immediately after

**Output examined**:
```
Welcome to Amplifier!

First time? Let's get you set up.

Provider? [1] Anthropic [2] OpenAI [3] Azure OpenAI [4] Ollama: 1
API key: ••••••••
  Get one: https://console.anthropic.com/settings/keys
✓ Saved to ~/.amplifier/keys.env

Model? [1] claude-sonnet-4-5 [2] claude-opus-4 [3] custom: 1
✓ Using claude-sonnet-4-5

Profile? [1] dev [2] base [3] full: 1
✓ Activated profile: dev

Ready! Starting chat...
```

**Artifacts checked**:
- ✅ `~/.amplifier/keys.env` created with ANTHROPIC_API_KEY
- ✅ `.amplifier/settings.local.yaml` created with provider config
- ✅ Profile 'dev' activated correctly

**Behavior assessment**:
- ✅ Matches documentation exactly
- ✅ User experience smooth, no confusion
- ✅ Error handling clear (tested with invalid input)

## Scenario 2: Switching providers mid-project

**Documentation reference**: USER_ONBOARDING.md Provider Management

**Steps (as user would do)**:
1. Check current: `amplifier provider current`
2. Switch: `amplifier provider use openai --model gpt-4o --local`
3. Verify: `amplifier provider current`
4. Test: `amplifier run "test message"`

**Observations**:
- ✅ Current command shows provider clearly
- ✅ Switch command accepted
- ⚠️ Warning shown: OpenAI key not found
- ✅ Helpful error message with next steps
- ❌ **BUG FOUND**: Chat tried to use OpenAI without key, crashed

**Output examined**:
```
$ amplifier provider current
Current provider: anthropic (claude-sonnet-4-5)
Scope: local

$ amplifier provider use openai --model gpt-4o --local
⚠️  OpenAI API key not found
   Run: amplifier init
   Or set: OPENAI_API_KEY in ~/.amplifier/keys.env
✓ Provider configured: openai (gpt-4o)

$ amplifier run "test"
Error: OpenAI API key not found
  Set OPENAI_API_KEY environment variable
```

**Behavior assessment**:
- ✅ Warning appropriate
- ❌ **CRITICAL**: Crash is bad UX
- 📝 **RECOMMENDATION**: Add validation before allowing provider switch

## Scenario 3: Smoke tests (integration points)

**Areas not directly changed but should still work**:

Profile management:
- ✅ `amplifier profile list` works
- ✅ `amplifier profile current` shows active
- ✅ `amplifier profile use base` switches correctly

Module management:
- ✅ `amplifier module list` works
- ✅ `amplifier module show tool-bash` shows details

Chat functionality:
- ✅ `amplifier` starts chat with configured provider
- ✅ Sending message works, gets response
- ✅ `/status` command shows provider info

**Assessment**: Integration points intact, no regressions detected
```

### What to Test

**Changed areas** (thorough):
- All new commands
- All modified workflows
- All updated behaviors
- Provider-specific paths
- Scope variations

**Integration points** (smoke test):
- Related features still work
- No regressions introduced
- Cross-cutting scenarios function
- Existing workflows intact

**Edge cases**:
- Invalid inputs
- Missing configuration
- Error scenarios
- Boundary conditions

---

## Step 4: Create User Testing Report

### Report Template

Save detailed findings to `ai_working/user_testing_report.md`:

```markdown
# User Testing Report - [Feature Name]

## Test Environment
- OS: [operating system]
- Python: [version]
- Fresh install: [yes/no]

## Scenarios Tested

### Scenario 1: [Name]
**Documentation reference**: [file:section]

**Steps (as user would do)**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Observations**:
- ✅ [What worked]
- ⚠️ [Warnings/concerns]
- ❌ [What failed]

**Output examined**:
```
[Actual command output]
```

**Artifacts checked**:
- ✅ [Files created correctly]
- ✅ [State persisted correctly]

**Behavior assessment**:
- ✅ Matches documentation: [yes/no]
- ✅ User experience smooth: [yes/no]
- 📝 Recommendations: [any improvements]

[... additional scenarios ...]

## Issues Found

### Critical
1. **[Issue name]**
   - Severity: High
   - Impact: [description]
   - Recommendation: [fix or workaround]

### Minor
[List minor issues]

### Improvements
[Suggested improvements not blocking]

## Test Coverage Assessment

### Thoroughly tested
- ✅ [Main feature areas]
- ✅ [All providers/variations]

### Smoke tested
- ✅ [Integration points]
- ✅ [Existing features]

### Not tested
- ℹ️ [Out of scope items]
```

### Present Summary to Human

```markdown
# User Testing Complete

## Summary
- Tested 3 main scenarios + smoke tests
- Found 1 critical issue (provider switch validation)
- 0 minor issues
- All documented behaviors work correctly

## Issues Requiring Action

### Critical: Provider switch without API key crashes
When user switches provider but doesn't have API key configured,
chat attempts to use provider anyway and crashes.

**Recommendation**: Add validation to prevent switch until key
configured, or gracefully degrade with clear error.

## Detailed Report
See: ai_working/user_testing_report.md

## Recommended Smoke Tests for You (~12 minutes)

As actual user of the tool, try these scenarios:

1. **Fresh setup flow** (5 minutes)
   - Delete `~/.amplifier/` and `.amplifier/`
   - Run `amplifier` and go through init wizard
   - Verify it feels smooth and clear

2. **Provider switching** (2 minutes)
   - Try switching between providers you have keys for
   - Check that chat actually uses new provider
   - Verify `amplifier provider current` is accurate

3. **Azure OpenAI** (if available) (3 minutes)
   - Run init with Azure OpenAI option
   - Verify endpoint/deployment flow makes sense
   - Test Azure CLI auth if available

4. **Error scenarios** (2 minutes)
   - Try provider without API key (should fail gracefully)
   - Try invalid provider name (should show helpful error)
   - Try malformed endpoint (should validate)

These test main flows and integration points without requiring
deep technical knowledge. Run as you would naturally use the tool.
```

**Key points**:
- High-level summary for quick understanding
- Critical issues highlighted
- Link to detailed report for depth
- Recommended smoke tests described as user would run them
- NOT code snippets, actual tool usage

---

## Step 5: Handle Mismatches

### When Tests Reveal Problems

**Option A: Code is wrong**
```markdown
# Test failed: provider use command

Expected (from docs): "✓ Provider configured: anthropic"
Actual: "Error: model is required"

Analysis: Code requires --model but docs say it's optional

Resolution: Fix code to match docs (model should be optional
with sensible default)
```

**Action**: Fix code to match documentation

**Option B: Docs are wrong**
```markdown
# Test failed: provider list command

Expected (from docs): Shows 4 providers
Actual: Shows 3 providers (missing Ollama)

Analysis: Docs mention Ollama but it's not implemented

Resolution: Either implement Ollama OR update docs to remove it
This requires returning to Phase 1 to fix documentation.
```

**Action**: PAUSE, propose doc fix to user, get approval, return to Phase 1

**Option C: Design was wrong**
```markdown
# Test failed: profile use command

Expected (from docs): amplifier profile use dev --local
Actual: Command doesn't accept --local flag

Analysis: Realized during implementation that --local doesn't
make sense for profiles (profiles are session-level)

Resolution: Design discussion needed with human
```

**Action**: PAUSE, document issue, get human guidance

### Critical Rule

**Documentation remains source of truth**:
- If docs are wrong, fix docs first
- Get approval on doc changes
- Then update code to match
- Never let them diverge

### Updating Documentation When Needed

**If implementation reveals documentation was wrong**:

1. **Stop testing**
2. **Document what's wrong and why**
3. **Propose fix to user**
4. **Get approval**
5. **Return to Phase 1** - Fix documentation
6. **Update implementation to match corrected docs**
7. **Resume testing**

---

## Step 6: Code-Based Test Verification

**In addition to user testing**, verify code-based tests pass:

```bash
# Run all tests
make test

# Run all checks (lint, format, type check)
make check

# Both must pass before proceeding
```

**What code tests verify**:
- Unit tests: Logic correctness
- Integration tests: Component interaction
- Type checking: Type safety
- Linting: Code quality
- Formatting: Style consistency

**Philosophy compliance** (from [IMPLEMENTATION_PHILOSOPHY.md](../../ai_context/IMPLEMENTATION_PHILOSOPHY.md)):
- Test real bugs, not code inspection
- Test runtime invariants
- Test edge cases
- Don't test obvious things

---

## Completion Checklist

Before considering Phase 5 complete:

- [ ] All documented examples tested and working
- [ ] **User testing complete** (AI tested as actual user)
- [ ] **User testing report created** (detailed in ai_working/)
- [ ] **Recommended smoke tests provided** (for human to run)
- [ ] Error handling tested (invalid inputs, edge cases)
- [ ] Output matches documentation descriptions
- [ ] Cross-cutting scenarios tested
- [ ] Performance acceptable (no obvious bottlenecks)
- [ ] All code-based tests passing: `make test`
- [ ] All checks passing: `make check`
- [ ] **Critical issues resolved** or documented for user
- [ ] Documentation updated if mismatches found

---

## Output of Phase 5

When complete:
- ✅ All documented behaviors verified working
- ✅ Tested as user would use it
- ✅ Comprehensive user testing report created
- ✅ Recommendations for human smoke tests provided
- ✅ All code-based tests passing
- ✅ Critical issues resolved or documented
- ✅ Docs updated if needed (with approval)

**Ready for**: [Phase 6: Cleanup & Push](06_cleanup_and_push.md)

---

## Real-World Example: Detailed User Testing

This example shows what thorough user testing looks like:

### Scenario: Provider Configuration Feature

**Test environment setup**:
```bash
# Fresh environment
rm -rf ~/.amplifier .amplifier

# Verify clean state
ls ~/.amplifier  # Should not exist
```

**Test execution**:
```bash
# Run as user would
$ amplifier

# Follow wizard
Provider? [1] Anthropic [2] OpenAI [3] Azure OpenAI [4] Ollama: 1
[... following prompts ...]

# Test provider switching
$ amplifier provider use openai --model gpt-4o --local
$ amplifier provider current

# Test error scenarios
$ amplifier provider use invalid-provider
$ amplifier provider use anthropic  # Missing required flag
```

**Observations documented**:
- What output appeared
- What files were created/modified
- What warnings/errors shown
- How behavior matched docs
- What felt confusing
- What worked well

**Issues found**:
- Critical: Provider switch without key crashes
- Minor: Warning message could be clearer
- Improvement: Consider `amplifier provider test` command

**Assessment**:
- 90% matches documentation
- 1 critical bug found and documented
- User experience mostly smooth
- Recommendations provided

**Result**: Detailed report in `ai_working/user_testing_report.md` with summary for human.

---

## Tips for Success

### For AI Assistants

1. **Actually run the tool** - Don't just read code
2. **Test as real user** - Follow documented workflows
3. **Observe everything** - Output, logs, state, artifacts
4. **Document thoroughly** - What worked, what didn't
5. **Be honest about issues** - Don't hide problems
6. **Provide recommendations** - Suggest fixes or improvements
7. **Guide human testing** - Recommend scenarios to verify

### For Humans

1. **Review user testing report** - AI's findings are valuable
2. **Run recommended smoke tests** - Quick verification
3. **Test edge cases AI might miss** - Domain expertise
4. **Verify on different environment** - AI tested on one environment
5. **Trust but verify** - AI is good QA, but not perfect

---

## Common Issues

### Issue: AI only runs unit tests

**Problem**: AI runs `make test` and considers testing done

**Fix**: Explicitly ask AI to "test as user would use it" - actual CLI commands, real workflows

### Issue: Mocked testing instead of real

**Problem**: AI creates mock environment instead of testing real tool

**Fix**: Specify "real environment, not mocked" - actual installation, actual commands

### Issue: No user testing report

**Problem**: AI tests but doesn't document findings

**Fix**: Require detailed report in ai_working/ with summary and recommendations

---

## Next Phase

**When Phase 5 complete**: [Phase 6: Cleanup & Push](06_cleanup_and_push.md)

**Before proceeding**:
- All tests passing (code and user)
- User testing report created
- Critical issues resolved
- Ready for final cleanup

---

**Return to**: [Phases](README.md) | [Main Index](../README.md)

**Prerequisites**: [Phase 4: Code Implementation](04_code_implementation.md)

**Core Techniques**: [File Crawling](../core_concepts/file_crawling.md)

**Philosophy**: [IMPLEMENTATION_PHILOSOPHY.md](../../ai_context/IMPLEMENTATION_PHILOSOPHY.md#testing-strategy)
