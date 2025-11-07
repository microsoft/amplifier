# DDD Plan: External Repository Integration into Amplifier

**Version:** 1.0
**Created:** 2025-11-06
**DDD Phase:** 1 - Planning & Alignment
**Status:** Ready for User Review

---

## Problem Statement

### What We're Solving

Amplifier currently works well with its hook system, slash commands, agents, and scenarios. However, external repositories (Superpowers, Claude Code Infrastructure Showcase, Claude Code Kit) contain proven patterns and capabilities that could enhance Amplifier:

- **Superpowers**: 23 skills with auto-activation via skill-rules.json
- **Showcase**: Production-tested infrastructure patterns
- **Kit**: Framework-aware installation and configuration
- **Brand-Composer**: Lessons learned from failures (what NOT to do)

**Current Pain Points:**
1. We don't have auto-activating skills (only manually invoked agents)
2. No systematic skill activation rules
3. Missing proven patterns from production systems
4. Risk of repeating Brand-Composer mistakes

### User Value

**For Amplifier users (developers using the system):**
- ✅ More intelligent context awareness (skills auto-activate when needed)
- ✅ Reduced cognitive load (system knows when to help)
- ✅ Production-proven patterns (not experimental)
- ✅ Better integration support (Kit patterns)

**For Amplifier maintainers:**
- ✅ Learn from external successes and failures
- ✅ Adopt battle-tested patterns
- ✅ Avoid known pitfalls (Brand-Composer anti-patterns)
- ✅ Systematic integration methodology

### Why This Matters

Without this integration, Amplifier misses opportunities to:
- Automatically assist users based on context
- Leverage proven production patterns
- Learn from other teams' experiences
- Evolve beyond manually-triggered workflows

**Critical Constraint:** Amplifier currently works. We must preserve 100% of existing functionality while adding new capabilities.

---

## Proposed Solution

### High-Level Approach

**Methodical 5-Phase Integration with Safety-First Design:**

**Phase 0: Baseline Documentation (Week 0 - 2-3 hours)**
- Document everything that works today
- Create comprehensive inventories (hooks, commands, agents, scenarios)
- Establish test baseline
- Create git checkpoint for rollback

**Phase 1: Discovery & Analysis (Week 1 - 4-6 hours)**
- Launch 7 parallel Explore agents for deep analysis
- Understand external capabilities in detail
- Learn from Brand-Composer failures
- Synthesize integration candidates with value/risk ranking

**Phase 2: Integration Design (Week 2 - 3-4 hours)**
- Design integration architecture
- Create phased implementation plan
- Define testing strategy for each phase
- Document rollback procedures

**Phase 3: Careful Implementation (Weeks 3-4)**
- Implement in small, tested phases
- Checkpoint → Implement → Test → Validate pattern
- Rollback if any issues
- User approval at each phase

**Phase 4+: Iterative Enhancement (Future)**
- Build on successful patterns
- Add more capabilities incrementally
- Continuous learning and refinement

### Key Design Principles

1. **Preservation First**: Never break existing functionality
2. **Incremental Integration**: Small, tested changes
3. **Rollback Ready**: Can undo at any point
4. **Test Everything**: Baseline, regression, integration tests
5. **User Approval Gates**: Major decisions need explicit approval

### Integration Strategy

**Skills System Integration:**
- Add `skill-rules.json` alongside existing agent system
- Skills auto-activate based on context
- Agents remain manually invocable
- Both systems coexist without conflict

**Hooks Enhancement:**
- Add new hooks from external repos
- Preserve all existing hooks
- Ensure no execution conflicts
- Test firing order and dependencies

**Patterns Adoption:**
- Learn from Showcase production patterns
- Adopt Kit framework detection
- Avoid Brand-Composer anti-patterns
- Maintain Amplifier's philosophy

---

## Alternatives Considered

### Alternative 1: Big Bang Integration

**Approach:** Copy all external patterns at once, merge everything together.

**Pros:**
- Fast initial integration
- Gets all features immediately

**Cons:**
- ❌ High risk of breaking existing functionality
- ❌ Hard to debug when things fail
- ❌ No rollback granularity
- ❌ Overwhelming to test
- ❌ Violates "ruthless simplicity" philosophy

**Why Rejected:** Too risky. Brand-Composer tried this and failed (Issue #67).

### Alternative 2: Cherry-Pick Individual Features

**Approach:** Pick one feature at a time, integrate fully, move to next.

**Pros:**
- Very safe (minimal changes per integration)
- Easy to test and rollback
- Clear ownership per feature

**Cons:**
- ❌ Very slow (months for full integration)
- ❌ Miss cross-feature synergies
- ❌ Could integrate incompatible patterns
- ❌ No holistic understanding first

**Why Rejected:** Too slow and risks missing architectural insights that emerge from understanding the whole system.

### Alternative 3: Phased Analysis-Then-Implementation (CHOSEN)

**Approach:** Deep understanding first (Phases 0-2), then careful implementation (Phase 3+).

**Pros:**
- ✅ Comprehensive understanding before changing anything
- ✅ Can design coherent integration architecture
- ✅ Identifies conflicts and dependencies early
- ✅ Rollback available at every phase
- ✅ Balances speed and safety
- ✅ Aligns with DDD methodology

**Cons:**
- Requires upfront analysis time (but prevents expensive rework)
- Need to resist urge to "just try things"

**Why Chosen:** Best balance of safety, speed, and comprehensiveness. Matches both DDD philosophy and Amplifier's implementation principles.

---

## Architecture & Design

### Current Amplifier Architecture

```
Amplifier/
├── .claude/
│   ├── settings.json           # Hook configuration
│   ├── commands/               # Slash commands (11 files)
│   ├── agents/                 # Specialized agents (30 files)
│   └── tools/                  # Hook scripts
├── scenarios/                  # Complete workflows (blog_writer, etc.)
├── ai_context/                 # Philosophy and design docs
└── ai_working/                 # Temporary working files
```

**Current Capabilities:**
- ✅ Hook system (7 lifecycle hooks)
- ✅ Slash commands (manual invocation)
- ✅ Specialized agents (Task tool)
- ✅ Scenarios (complete workflows)
- ✅ DDD workflow commands
- ✅ Transcript management

**Current Limitations:**
- ❌ No auto-activating skills
- ❌ No context-based activation rules
- ❌ No skill-rules.json pattern
- ❌ Manual agent invocation only

### Target Architecture (After Integration)

```
Amplifier/
├── .claude/
│   ├── settings.json           # Hook configuration (enhanced)
│   ├── skill-rules.json        # NEW: Skill activation rules
│   ├── commands/               # Slash commands (11+ files)
│   ├── agents/                 # Specialized agents (30+ files)
│   ├── skills/                 # NEW: Auto-activating skills
│   └── tools/                  # Hook scripts (enhanced)
├── scenarios/                  # Complete workflows
├── ai_context/                 # Philosophy and design docs
└── ai_working/                 # Temporary working files
```

**Enhanced Capabilities:**
- ✅ All current capabilities (preserved)
- ✅ Auto-activating skills (new)
- ✅ Context-aware assistance (new)
- ✅ skill-rules.json pattern (new)
- ✅ Production-proven patterns (new)
- ✅ Framework detection (from Kit)

### Key Interfaces ("Studs")

**1. Hook Interface:**
```json
{
  "SessionStart": "python .claude/tools/hook_session_start.py",
  "PreCompact": "python .claude/tools/hook_precompact.py",
  // ... existing hooks preserved
  // ... new hooks added without conflict
}
```

**2. Skill Activation Interface (NEW):**
```json
// skill-rules.json
{
  "skills": [
    {
      "name": "skill-name",
      "triggers": ["pattern1", "pattern2"],
      "priority": 1,
      "enabled": true
    }
  ]
}
```

**3. Agent Interface (UNCHANGED):**
```
Task tool with:
- subagent_type: "agent-name"
- prompt: "task description"
```

**4. Command Interface (UNCHANGED):**
```markdown
# /command-name
[Command definition]
```

### Module Boundaries

**Preserved Modules (Don't Change):**
- ✅ Core hook system (SessionStart, PreCompact, etc.)
- ✅ Existing commands (/transcripts, /commit, /ddd:*, etc.)
- ✅ Existing agents (all 30)
- ✅ Existing scenarios (blog_writer, etc.)
- ✅ Transcript management
- ✅ Git integration

**New Modules (To Add):**
- 🆕 Skills system (auto-activation layer)
- 🆕 skill-rules.json loader
- 🆕 Context detection (when to activate skills)
- 🆕 Skill/Agent bridge (coordination)

**Enhanced Modules (Careful Extension):**
- 🔧 Hook system (add new hooks, preserve existing)
- 🔧 settings.json (add skill config, preserve hooks)

### Data Models

**skill-rules.json Schema:**
```json
{
  "$schema": "...",
  "version": "1.0",
  "skills": [
    {
      "name": "string",              // Unique identifier
      "description": "string",       // What it does
      "triggers": ["string"],        // Context patterns
      "priority": "number",          // Activation order
      "enabled": "boolean",          // Can disable without deleting
      "agent": "string (optional)",  // Which agent to invoke
      "command": "string (optional)" // Or which command
    }
  ]
}
```

**Baseline Inventory Schema:**
```markdown
## Component Inventory
- Name: [component-name]
- Type: [hook|command|agent|scenario]
- Status: [working|needs-testing]
- Dependencies: [list]
- Tests: [list of tests]
```

---

## Files to Change

### Phase 0: Baseline Documentation (Read-Only, No Changes)

**Create new files for documentation:**
- [ ] `ai_working/integration/baseline/hooks-inventory.md`
- [ ] `ai_working/integration/baseline/commands-inventory.md`
- [ ] `ai_working/integration/baseline/agents-inventory.md`
- [ ] `ai_working/integration/baseline/scenarios-inventory.md`
- [ ] `ai_working/integration/baseline/functionality-test-results.md`
- [ ] `ai_working/integration/baseline/amplifier-baseline-master.md`
- [ ] `ai_working/integration/baseline/git-state.txt`

**No modifications to existing files in Phase 0**

### Phase 1: Discovery & Analysis (Read-Only, Analysis Outputs)

**Create new analysis files:**
- [ ] `ai_working/integration/analysis/superpowers-complete.md`
- [ ] `ai_working/integration/analysis/showcase-complete.md`
- [ ] `ai_working/integration/analysis/kit-complete.md`
- [ ] `ai_working/integration/analysis/brand-composer-anti-patterns.md`
- [ ] `ai_working/integration/analysis/amplifier-patterns.md`
- [ ] `ai_working/integration/analysis/scenario-success-patterns.md`
- [ ] `ai_working/integration/analysis/command-pattern-comparison.md`
- [ ] `ai_working/integration/analysis/synthesis-current-state.md`
- [ ] `ai_working/integration/analysis/synthesis-external-capabilities.md`
- [ ] `ai_working/integration/analysis/synthesis-gap-analysis.md`
- [ ] `ai_working/integration/analysis/synthesis-integration-candidates.md`

**No modifications to existing files in Phase 1**

### Phase 2: Integration Design (Design Outputs)

**Create design files:**
- [ ] `ai_working/integration/design/integration-architecture.md`
- [ ] `ai_working/integration/design/phased-implementation-plan.md`
- [ ] `ai_working/integration/design/testing-strategy.md`
- [ ] `ai_working/integration/design/rollback-procedures.md`

**No modifications to existing files in Phase 2**

### Phase 3+: Implementation (TBD - Design in Phase 2)

**Files likely to change (will be specified in Phase 2 design):**

**Configuration:**
- [ ] `.claude/settings.json` - Add skill configuration
- [ ] `.claude/skill-rules.json` - NEW FILE: Skill activation rules

**Documentation:**
- [ ] `README.md` - Document new capabilities
- [ ] `CLAUDE.md` - Update agent guidance
- [ ] `AGENTS.md` - Document new patterns
- [ ] `docs/` - Add skill system documentation

**New Directories:**
- [ ] `.claude/skills/` - NEW: Skill definitions

**Specific files determined after Phase 2 design**

---

## Philosophy Alignment

### Ruthless Simplicity

**How we embody it:**

1. **Start Minimal:**
   - Phase 0: Just document (zero code changes)
   - Phase 1: Just analyze (zero code changes)
   - Phase 2: Just design (zero code changes)
   - Phase 3+: Small, tested increments

2. **Avoid Future-Proofing:**
   - ❌ NOT building: "Universal skill framework that could support anything"
   - ❌ NOT building: "Complete reimplementation of Amplifier"
   - ❌ NOT building: "All 23 Superpowers skills at once"
   - ✅ Building: Minimal skill system that works
   - ✅ Building: Integration of proven patterns only
   - ✅ Building: What adds clear value now

3. **Question Every Abstraction:**
   - Do we need a separate skills/ directory? (Answer in Phase 2)
   - Do we need skill-rules.json or can we use settings.json? (Design in Phase 2)
   - Can skills just be special agents? (Analyze in Phase 1)
   - Each abstraction must justify existence

4. **Clear Over Clever:**
   - Explicit skill activation rules (not magic heuristics)
   - Documented integration points (not hidden coupling)
   - Simple file structure (not nested hierarchies)
   - Obvious names (skill-rules.json not auto-context-activation-manifest.yaml)

**Simplicity Checkpoints:**
- After Phase 0: Can explain current state simply?
- After Phase 1: Can explain what we're adding simply?
- After Phase 2: Can explain the design simply?
- After Phase 3: Does the implementation feel simple?

### Modular Design (Bricks & Studs)

**Bricks (Self-Contained Modules):**

1. **Existing Bricks (Preserve):**
   - Hook system (clear lifecycle events)
   - Command system (slash command invocation)
   - Agent system (specialized task agents)
   - Scenario system (complete workflows)
   - Transcript system (conversation management)

2. **New Bricks (Add):**
   - Skill system (auto-activation layer)
   - Skill activation engine (rule matching)
   - Context detector (what's happening now)

**Studs (Interfaces):**

1. **Preserved Studs (Don't Change):**
   - Hook interface: `settings.json` → lifecycle scripts
   - Command interface: `/command` → markdown definition
   - Agent interface: `Task(subagent_type)` → agent invocation
   - File interface: `.claude/` structure

2. **New Studs (Add):**
   - Skill activation interface: `skill-rules.json` → activation rules
   - Skill → Agent bridge: How skills invoke agents
   - Context → Skill matcher: How context triggers skills

**Regeneratable:**
- Each baseline inventory can regenerate understanding of that module
- Each analysis document can regenerate understanding of external patterns
- The integration design can regenerate the implementation approach
- From this plan, we can regenerate the entire integration

**Human Architects, AI Builds:**
- **Human (you) decides:** Which features to integrate, philosophy alignment, risk tolerance
- **AI (me) builds:** Inventories, analysis, synthesis, implementation following your decisions
- **Human reviews:** At every approval gate (end of each phase)

**Example of Modularity:**
```
Skill System Brick:
├── Input Stud: Context (what's happening)
├── Logic: Match context to rules
├── Output Stud: Agent invocation OR Command execution
└── Independent: Can be added/removed without breaking agents

Agent System Brick (UNCHANGED):
├── Input Stud: Task(subagent_type, prompt)
├── Logic: Specialized agent execution
├── Output Stud: Agent result
└── Independent: Works with or without skills
```

---

## Test Strategy

### Three-Tier Testing Approach

#### Tier 1: Baseline Tests (Before Any Changes)

**Purpose:** Document what works now so we can verify it later

**Tests to Create in Phase 0:**

```bash
# ai_working/integration/testing/baseline-tests.sh

# Test 1: PreCompact Hook
echo "Testing PreCompact hook..."
# Verify hook script exists
test -f .claude/tools/hook_precompact.py
# Verify it's referenced in settings.json
grep -q "hook_precompact.py" .claude/settings.json

# Test 2: Commands
echo "Testing commands..."
for cmd in transcripts commit ultrathink-task; do
  test -f ".claude/commands/$cmd.md"
done

# Test 3: Agents
echo "Testing agents..."
AGENT_COUNT=$(ls .claude/agents/*.md | wc -l)
test $AGENT_COUNT -eq 30

# Test 4: Scenarios
echo "Testing scenarios..."
test -d scenarios/blog_writer

# Test 5: Git State
echo "Testing git state..."
git status --porcelain
```

**Expected Result:** All tests pass = baseline established

#### Tier 2: Regression Tests (After Changes)

**Purpose:** Ensure nothing broke

**Tests to Run After Each Phase:**

```bash
# ai_working/integration/testing/regression-tests.sh

# Re-run ALL baseline tests
source ai_working/integration/testing/baseline-tests.sh

# Additional regression checks
echo "Checking configuration integrity..."
python -c "import json; json.load(open('.claude/settings.json'))"

echo "Checking hook scripts executable..."
for hook in .claude/tools/hook_*.py; do
  test -x "$hook"
done

echo "Checking no broken file references..."
# (Specific checks defined in Phase 2)
```

**Expected Result:** All baseline tests still pass + no new errors

#### Tier 3: Integration Tests (New Functionality)

**Purpose:** Verify new features work

**Tests to Create After Implementation (Phase 3+):**

```bash
# ai_working/integration/testing/integration-tests.sh

# Test skill-rules.json loads
if [ -f .claude/skill-rules.json ]; then
  echo "Testing skill-rules.json..."
  python -c "import json; json.load(open('.claude/skill-rules.json'))"
fi

# Test skill activation (when implemented)
echo "Testing skill activation..."
# (Specific tests defined in Phase 2)

# Test new hooks (when added)
echo "Testing new hooks..."
# (Specific tests defined in Phase 2)
```

**Expected Result:** All new features work as designed

### Manual Testing Checklist

**After Every Phase:**

```markdown
## Manual Verification

### Existing Functionality
- [ ] `/transcripts` command works
- [ ] `/commit` command works
- [ ] `/ultrathink-task` command works
- [ ] `/ddd:status` command works
- [ ] PreCompact hook triggers on /compact
- [ ] Transcripts exported to .data/transcripts/
- [ ] Agents can be launched via Task tool
- [ ] Scenarios work (test blog_writer)

### New Functionality (Phase-Specific)
- [ ] [New feature 1] works as designed
- [ ] [New feature 2] works as designed

### Integration Points
- [ ] Hooks don't conflict
- [ ] Commands don't conflict
- [ ] Configuration loads correctly
- [ ] No error messages in logs

### Performance
- [ ] No noticeable slowdown
- [ ] Hooks complete in reasonable time
- [ ] No hanging processes
```

### User Testing Strategy

**Phase 0:** User tests baseline (everything should work)
**Phase 1:** No user testing (analysis only)
**Phase 2:** User reviews design (no code yet)
**Phase 3:** User tests after each implementation phase

**User Testing Scenarios (Phase 3+):**
1. "Use Amplifier as normal for a day"
2. "Try the new features"
3. "Report anything that feels broken or different"

---

## Implementation Approach

### Phase 2: Documentation Updates (When We Get There)

**DDD Phase 2 (`/ddd:2-docs`):**

**Non-code files to update after analysis complete:**

1. **Update ai_context/ documentation:**
   - [ ] Document skill system design
   - [ ] Add integration patterns learned
   - [ ] Update with anti-patterns from Brand-Composer

2. **Update project documentation:**
   - [ ] `README.md` - Describe new capabilities
   - [ ] `CLAUDE.md` - Guide AI on skill usage
   - [ ] `AGENTS.md` - Document skill/agent relationship

3. **Create new documentation:**
   - [ ] `docs/SKILLS_SYSTEM.md` - How skills work
   - [ ] `docs/INTEGRATION_LEARNINGS.md` - What we learned

4. **File Crawling Approach:**
   - Use file crawling for systematic doc updates
   - Process one doc at a time
   - Verify each before marking complete

**Approval Gate:** User commits docs when satisfied

### Phase 4: Code Implementation (When We Get There)

**DDD Phase 4 (`/ddd:4-code`):**

**Implementation pattern for each chunk:**

```
1. Create checkpoint (git tag)
2. Run baseline tests (should pass)
3. Implement changes for this chunk
4. Run regression tests (should still pass)
5. Run integration tests (new features should work)
6. Manual verification
7. If tests pass: User approves commit
8. If tests fail: Rollback to checkpoint
9. Repeat for next chunk
```

**Chunks to implement (determined in Phase 2 design):**

**Example Chunk 1: Skill Rules Foundation**
- Add `skill-rules.json` file (empty skeleton)
- Update `settings.json` to reference it
- Test: Configuration loads without errors
- Commit with user approval

**Example Chunk 2: First Simple Skill**
- Add one simple skill definition
- Implement basic activation logic
- Test: Skill activates in expected context
- Commit with user approval

**Chunk details specified in Phase 2 integration design**

### Rollback Procedures

**Quick Rollback (During Active Work):**
```bash
git reset --hard HEAD~1
cp ai_working/integration/checkpoints/[phase]/settings.json .claude/
bash ai_working/integration/testing/baseline-tests.sh
```

**Phase Rollback (After Phase Complete):**
```bash
git checkout [phase-X-start-tag]
git checkout -b rollback-phase-X
bash ai_working/integration/testing/baseline-tests.sh
# If good, update main branch
```

**Complete Rollback (Nuclear Option):**
```bash
git checkout integration-baseline-[date]
cp -r ai_working/integration/baseline/backups/.claude .
bash ai_working/integration/testing/baseline-tests.sh
```

---

## Value/Risk Evaluation (Critical Decision Point)

### Overview

**After Phase 1 (Discovery & Analysis), we MUST evaluate whether integration is worth it.**

This is NOT a rubber-stamp approval - it's a real Go/No-Go decision based on:
1. **Actual Value** discovered (not assumed)
2. **Real Risks** identified (not theoretical)
3. **Cost/Benefit** analysis (effort vs. gain)

**Possible Outcomes:**
- ✅ **GO**: Clear value exceeds risk → Proceed to Phase 2
- ⚠️ **PARTIAL GO**: Some features worth it, others not → Cherry-pick
- ❌ **NO-GO**: Risk > Value or Amplifier already optimal → Stop gracefully

### Value Assessment Framework

**For each discovered capability, answer:**

#### 1. Clear User Benefit
- **Q:** What specific problem does this solve for Amplifier users?
- **Q:** Is this problem real or hypothetical?
- **Q:** How often does this problem occur?
- **Q:** How painful is the problem? (Rate 1-10)
- **Score:** Problem Frequency × Pain Level = Value Score

**Example:**
- Feature: Auto-activating skills
- Problem: User must manually invoke agents even when context is obvious
- Frequency: Every session (10/10)
- Pain: Mild annoyance (3/10)
- Value Score: 10 × 3 = 30

#### 2. Unique Capability
- **Q:** Can Amplifier already do this?
- **Q:** Can users work around this easily?
- **Q:** Is there a simpler way to achieve the same benefit?

**Scoring:**
- Already exists: 0 points (no value)
- Easy workaround: +5 points (nice to have)
- No workaround: +20 points (real need)

#### 3. Philosophy Alignment
- **Q:** Does this align with ruthless simplicity?
- **Q:** Does this add essential complexity or accidental complexity?
- **Q:** Would this make Amplifier better or just bigger?

**Scoring:**
- Violates philosophy: -50 points (deal-breaker)
- Neutral: 0 points
- Enhances philosophy: +20 points (bonus)

#### 4. Implementation Maturity
- **Q:** Is this proven in production (Showcase) or experimental (Kit)?
- **Q:** Do we understand how it works?
- **Q:** Is it well-documented in source repos?

**Scoring:**
- Experimental/unclear: -20 points (risky)
- Working but undocumented: +10 points (medium confidence)
- Production-proven + documented: +30 points (high confidence)

#### 5. Amplifier-Specific Fit
- **Q:** Does this fit Amplifier's use case?
- **Q:** Does this work with Amplifier's architecture?
- **Q:** Would Amplifier users actually use this?

**Scoring:**
- Poor fit: -30 points
- Okay fit: +10 points
- Perfect fit: +40 points

### Risk Assessment Framework

**For each capability, evaluate:**

#### 1. Breaking Risk
- **Q:** How likely is this to break existing functionality?
- **Q:** How many existing components does this touch?
- **Q:** Are there hidden dependencies?

**Scoring:**
- Isolated (no existing code touched): 1 (low risk)
- Touches 1-3 components: 3 (medium risk)
- Touches 5+ components or core systems: 7 (high risk)
- Requires rewrite of core: 10 (critical risk)

#### 2. Complexity Cost
- **Q:** How much code is needed?
- **Q:** How many new concepts must users learn?
- **Q:** How much ongoing maintenance?

**Scoring:**
- <100 LOC, no new concepts: 1 (simple)
- 100-500 LOC, 1-2 new concepts: 3 (moderate)
- 500-1000 LOC, 3-5 new concepts: 6 (complex)
- >1000 LOC, many new concepts: 9 (very complex)

#### 3. Testing Difficulty
- **Q:** Can we test this automatically?
- **Q:** Can we test rollback reliably?
- **Q:** Are failure modes obvious or subtle?

**Scoring:**
- Easy to test, obvious failures: 1 (low risk)
- Manual testing needed: 3 (medium risk)
- Hard to test, subtle failures: 7 (high risk)
- Cannot fully test: 10 (critical risk)

#### 4. Reversibility
- **Q:** Can we easily undo this?
- **Q:** Does this create lock-in?
- **Q:** Will users depend on this?

**Scoring:**
- Fully reversible, no lock-in: 1 (low risk)
- Reversible with effort: 3 (medium risk)
- Hard to reverse: 7 (high risk)
- Irreversible or user lock-in: 10 (critical risk)

### Value/Risk Matrix

**After scoring each capability:**

| Capability | Value Score | Risk Score | Value/Risk Ratio | Decision |
|------------|-------------|------------|------------------|----------|
| Feature A  | 80          | 2          | 40:1             | **Strong GO** |
| Feature B  | 50          | 5          | 10:1             | **GO** |
| Feature C  | 30          | 4          | 7.5:1            | **Maybe** |
| Feature D  | 20          | 7          | 2.8:1            | **Probably No** |
| Feature E  | 10          | 9          | 1.1:1            | **NO-GO** |

**Decision Thresholds:**
- **Ratio > 15:1** → Strong GO (clear win)
- **Ratio 8-15:1** → GO (worth doing)
- **Ratio 4-8:1** → Maybe (needs discussion)
- **Ratio 2-4:1** → Probably No (marginal)
- **Ratio < 2:1** → NO-GO (not worth risk)

### Evaluation Deliverable

**After Phase 1, create:**

`ai_working/integration/evaluation/value-risk-assessment.md`

**Structure:**

```markdown
# Value/Risk Evaluation: External Repository Integration

## Executive Summary

Based on deep analysis of all external repositories, we evaluated N capabilities.

**Recommendation:** [STRONG GO / GO / PARTIAL GO / NO-GO]

**Rationale:** [1-2 paragraphs explaining the decision]

## Detailed Capability Evaluation

### Capability 1: [Name]

**Description:** [What it is]

**Source:** [Superpowers / Showcase / Kit]

**Value Analysis:**
- User Benefit: [Score + explanation]
- Unique Capability: [Score + explanation]
- Philosophy Alignment: [Score + explanation]
- Implementation Maturity: [Score + explanation]
- Amplifier Fit: [Score + explanation]
- **Total Value Score:** X

**Risk Analysis:**
- Breaking Risk: [Score + explanation]
- Complexity Cost: [Score + explanation]
- Testing Difficulty: [Score + explanation]
- Reversibility: [Score + explanation]
- **Total Risk Score:** Y

**Value/Risk Ratio:** X:Y

**Decision:** [STRONG GO / GO / MAYBE / NO]

**Rationale:** [Why this decision]

[Repeat for all capabilities]

## Comparison with Current Amplifier

### What Amplifier Already Does Well
- [Capability] - No need to add external version
- [Capability] - Current approach is simpler
- [Capability] - Already solved differently

### Real Gaps Identified
- [Gap] - External repos solve this, Amplifier doesn't
- [Gap] - Clear user pain point
- [Gap] - No good workaround

### False Gaps (Not Actually Problems)
- [Non-gap] - Looks like gap but users don't need it
- [Non-gap] - Philosophy says we shouldn't add this
- [Non-gap] - Amplifier's approach is intentionally different

## Final Recommendations

### STRONG GO (Must Have)
1. [Capability]: Ratio X:1, because [reason]
2. [Capability]: Ratio Y:1, because [reason]

### GO (Should Have)
1. [Capability]: Ratio X:1, because [reason]

### MAYBE (Discuss)
1. [Capability]: Ratio X:1, [what makes this unclear]

### NO-GO (Not Worth It)
1. [Capability]: Ratio X:1, because [why not]
2. [Capability]: Violates philosophy
3. [Capability]: Amplifier already has better solution

## Alternative Outcomes

### If STRONG GO or GO:
→ Proceed to Phase 2: Integration Design
→ Focus on top-ranked capabilities
→ Phase implementation by value/risk ratio

### If PARTIAL GO:
→ Proceed to Phase 2 for selected capabilities only
→ Document why others were rejected
→ Leaner integration scope

### If NO-GO:
→ STOP GRACEFULLY
→ Document learnings (what we learned even though not integrating)
→ Update Amplifier docs with "why we don't need external patterns"
→ No code changes, no risk, Amplifier stays as-is
→ This is a SUCCESS (informed decision not to proceed)

## User Decision Point

**Questions for User:**

1. Do you agree with the Value/Risk scoring for each capability?
2. Are there capabilities we missed or undervalued?
3. Do you want to proceed with STRONG GO items only, or include GO items?
4. Any capabilities you want included despite lower ratio? (user judgment overrides)
5. Any capabilities you want excluded despite high ratio? (user veto)

**User Approval Required Before Phase 2:**

- [ ] I have reviewed the value/risk assessment
- [ ] I understand which capabilities are recommended
- [ ] I agree with the overall recommendation (or provide changes)
- [ ] I approve proceeding to [Phase 2 / Selective Integration / Stop]

```

### Integration into Workflow

**Updated Phase 1 Deliverables:**

**OLD:** Discovery & Analysis → User Review → Phase 2
**NEW:** Discovery & Analysis → **Value/Risk Evaluation** → User Decision → Phase 2 (or Stop)

**Phase 1 now has TWO outputs:**
1. `synthesis-integration-candidates.md` (what's possible)
2. `value-risk-assessment.md` (what's worth doing) ← **NEW**

**Phase 2 only proceeds if:**
- Value/Risk assessment shows STRONG GO or GO for at least some capabilities
- User explicitly approves proceeding
- Clear scope defined (which capabilities to integrate)

### Why This Matters

**Without this evaluation:**
- ❌ We might integrate things that don't add real value
- ❌ We might take risks that aren't worth the benefit
- ❌ We might make Amplifier more complex without making it better
- ❌ We might waste weeks implementing features users don't need

**With this evaluation:**
- ✅ We make informed, data-driven decisions
- ✅ We only take risks when value clearly exceeds them
- ✅ We can confidently say "no" if integration isn't worthwhile
- ✅ We respect the "if it ain't broke, don't fix it" principle
- ✅ User has clear decision criteria, not gut feeling

**Remember:** The best integration might be NO integration. Amplifier working well today is already a success.

---

## Success Criteria

### Overall Success

**The integration is successful if ALL are true:**

#### 1. Preservation ✅
- [ ] PreCompact hook still works
- [ ] All existing commands still work
- [ ] All existing agents still work
- [ ] All existing scenarios still work
- [ ] No regressions in functionality
- [ ] No performance degradation
- [ ] User workflows unchanged (unless enhanced)

#### 2. Enhancement ✅
- [ ] New capabilities added as designed
- [ ] New features work reliably
- [ ] Integration points are clean
- [ ] Documentation is complete
- [ ] Examples provided for new features

#### 3. Quality ✅
- [ ] All tests passing
- [ ] No error messages in logs
- [ ] No warnings in configuration
- [ ] Code follows Amplifier philosophy
- [ ] Changes are maintainable

#### 4. Safety ✅
- [ ] Rollback procedures tested
- [ ] Checkpoints created
- [ ] Backups available
- [ ] Recovery procedures documented
- [ ] User can revert if needed

#### 5. User Satisfaction ✅
- [ ] User understands what changed
- [ ] User can use new features
- [ ] User confident in system
- [ ] No mysterious failures
- [ ] User approves result

### Phase-Level Success

**Each phase successful if:**
- Pre-phase tests pass
- Implementation completes as designed
- Post-phase tests all pass
- No regressions detected
- New features work
- Rollback tested and works
- Documentation updated
- User review completed

---

## Next Steps

### Immediate Next Steps (After Plan Approval)

**1. User Review of This Plan**
- Read complete plan
- Ask clarifying questions
- Provide feedback
- Approve or request changes

**2. Start Phase 0: Baseline Documentation**
- Run: `/ddd:2-docs` (for Phase 0 documentation)
- Create all baseline inventories
- Establish test baseline
- User reviews baseline

**3. Execute Phase 1: Discovery & Analysis**
- Launch 7 parallel Explore agents
- Deep dive into all external repos
- Synthesize findings into integration candidates
- **NEW:** Create Value/Risk evaluation for each capability
- User reviews evaluation

**4. CRITICAL DECISION POINT: Go/No-Go**
- Review value-risk-assessment.md
- Decide: STRONG GO / GO / PARTIAL GO / NO-GO
- If NO-GO: Stop gracefully (this is success - informed decision)
- If PARTIAL GO: Select which capabilities to pursue
- If GO/STRONG GO: Approve proceeding with selected capabilities

**5. Continue to Phase 2 (Only If GO/STRONG GO)**
- Design integration architecture for approved capabilities only
- Create detailed implementation plan
- Define testing for each phase
- User approves design before any code

### DDD Workflow Integration

**This plan drives all subsequent DDD phases:**

```
✅ Phase 1 (Planning): THIS DOCUMENT
    ↓
Phase 2 (/ddd:2-docs): Update documentation based on this plan
    ↓
Phase 3 (/ddd:3-code-plan): Plan code changes based on this plan
    ↓
Phase 4 (/ddd:4-code): Implement based on this plan
    ↓
Phase 5 (/ddd:5-finish): Cleanup and finalize
```

**All commands can run without arguments - they use this plan as their guide.**

---

## Risk Assessment

### High Risks (Mitigated)

**Risk 1: Breaking Existing Functionality**
- **Mitigation:** Phase 0 baseline, regression tests, rollback procedures
- **Detection:** Automated tests after every change
- **Recovery:** Rollback to last known-good checkpoint

**Risk 2: Incompatible Patterns**
- **Mitigation:** Phase 1 deep analysis before any changes
- **Detection:** Design review in Phase 2
- **Recovery:** Redesign integration before implementation

**Risk 3: Complexity Creep**
- **Mitigation:** Philosophy alignment checks, user review gates
- **Detection:** "Does this feel simple?" check at each phase
- **Recovery:** Simplify or reject addition

### Medium Risks

**Risk 4: Incomplete Analysis**
- **Mitigation:** 7 parallel agents, synthesis phase, user review
- **Detection:** "Do we understand this?" check before proceeding
- **Recovery:** Additional analysis agents if needed

**Risk 5: Time Pressure**
- **Mitigation:** Phased approach, can stop at any phase
- **Detection:** User decides when to proceed
- **Recovery:** Pause at safe checkpoint

### Low Risks

**Risk 6: Documentation Drift**
- **Mitigation:** DDD ensures docs updated before code
- **Detection:** Part of DDD process
- **Recovery:** Built into methodology

---

## Questions for User

Before proceeding, please confirm:

1. **Scope:** Is focusing on Phase 0+1 (baseline + discovery + evaluation) for this planning cycle correct?
2. **Timeline:** Are the time estimates reasonable (Week 0 for baseline, Week 1 for discovery)?
3. **Approach:** Does the phased, safety-first approach align with your expectations?
4. **Risk Tolerance:** Is the preservation-first philosophy acceptable even if it means slower integration?
5. **Agent Usage:** Approve launching 7 parallel Explore agents in Phase 1?
6. **Evaluation Framework:** Do the Value/Risk scoring criteria make sense to you?
7. **NO-GO Acceptance:** Are you comfortable with the possibility that the evaluation might recommend NOT integrating (and that would be a success)?

---

## Approval

**This plan is ready for user review and approval.**

**If approved:**
✅ Run `/ddd:2-docs` to start Phase 0 baseline documentation

**If changes needed:**
🔄 Provide feedback and I'll iterate on the plan

---

**End of DDD Plan**

*This plan follows Document-Driven Development methodology and Amplifier's implementation philosophy. It serves as the specification for all subsequent work.*
