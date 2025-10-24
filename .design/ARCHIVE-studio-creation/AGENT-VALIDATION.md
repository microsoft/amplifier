# Agent Validation Framework

**How to verify design agents are working correctly**

---

## Overview

This framework ensures `/designer` agents (design-system-architect, component-designer, animation-choreographer) are functioning properly and following protocols.

---

## Validation Levels

### Level 1: Basic Functionality (MUST PASS)
**Can the agent complete its core mission?**

### Level 2: Protocol Adherence (SHOULD PASS)
**Does the agent follow our design protocols?**

### Level 3: Quality Output (EXCELLENCE)
**Does the output meet 9.5/10 baseline?**

---

## Testing Matrix

### Design-System-Architect Agent

#### Test Case 1: Token Definition
**Command:**
```bash
/designer system Create a new semantic color token for warning states
```

**Expected Behavior:**
- [ ] Asks WHY this token is needed (Purpose validation)
- [ ] Checks if existing tokens could serve this purpose (Constraint)
- [ ] Defines token for BOTH light and dark modes
- [ ] Updates `studio-interface/app/globals.css`
- [ ] Documents token usage with examples
- [ ] Runs `npm run validate:tokens`

**Success Criteria:**
- ✅ Token follows naming convention (`--color-[semantic-name]`)
- ✅ Light AND dark mode definitions present
- ✅ WCAG AA contrast validated (if text color)
- ✅ Documentation includes use cases
- ✅ Validation script passes

**Failure Indicators:**
- ❌ Token only defined for light mode
- ❌ Arbitrary naming (`--warning-yellow` vs `--color-warning`)
- ❌ No documentation
- ❌ Validation not run

#### Test Case 2: System Review
**Command:**
```bash
/designer Review current design system for inconsistencies
```

**Expected Behavior:**
- [ ] Reads `studio-interface/app/globals.css`
- [ ] Checks for undefined variables in components
- [ ] Evaluates Nine Dimensions coverage
- [ ] Validates Five Pillars alignment
- [ ] Provides structured report with priorities

**Success Criteria:**
- ✅ Identifies hardcoded values (if present)
- ✅ Flags missing semantic tokens
- ✅ Evaluates against WCAG AA standards
- ✅ Prioritizes issues (High/Medium/Low)
- ✅ Provides actionable recommendations

#### Test Case 3: System Architecture
**Command:**
```bash
/designer system Design spacing scale for our 8px system
```

**Expected Behavior:**
- [ ] References existing spacing system
- [ ] Proposes scale based on 8px base (4, 8, 12, 16, 24, 32, 48, 64, 96, 128)
- [ ] Explains rationale for each step
- [ ] Defines CSS variables (`--space-1` through `--space-32`)
- [ ] Documents usage examples

**Success Criteria:**
- ✅ Follows 8px base unit system
- ✅ Clear semantic naming
- ✅ Usage examples for each token
- ✅ Integration guidance provided

---

### Component-Designer Agent

#### Test Case 1: New Component
**Command:**
```bash
/designer component Create a notification toast component
```

**Expected Behavior:**
- [ ] Asks for PURPOSE (why does this need to exist?)
- [ ] Runs through Nine Dimensions evaluation
- [ ] Validates Five Pillars alignment
- [ ] Defines all states (loading, error, empty, success)
- [ ] Specifies accessibility requirements
- [ ] Creates props API specification
- [ ] Provides implementation guidance

**Success Criteria:**
- ✅ Purpose articulated in 1-2 sentences
- ✅ All states documented
- ✅ Touch targets meet 44x44px minimum
- ✅ WCAG AA contrast validated
- ✅ Keyboard navigation specified
- ✅ Screen reader compatibility addressed
- ✅ Uses design system tokens (no hardcoded values)
- ✅ Animation timing follows protocol (<100ms, 100-300ms, 300-1000ms)

**Failure Indicators:**
- ❌ Purpose unclear ("make a toast")
- ❌ Missing states (no error state)
- ❌ Hardcoded colors or spacing
- ❌ No accessibility considerations
- ❌ Arbitrary animation timing

#### Test Case 2: Component Refinement
**Command:**
```bash
/designer component Improve the button hover state to feel more premium
```

**Expected Behavior:**
- [ ] Reviews current implementation
- [ ] References "German car facility" aesthetic
- [ ] Suggests specific improvements (transform, shadow, timing)
- [ ] Validates against motion protocol
- [ ] Ensures reduced-motion support
- [ ] Tests in BOTH light and dark modes

**Success Criteria:**
- ✅ Specific technical recommendations (translateY, scale, etc.)
- ✅ Timing rationale provided (why 150ms not 300ms)
- ✅ Easing curve justified
- ✅ Aesthetic alignment explained
- ✅ Works in light and dark modes

#### Test Case 3: Component Review
**Command:**
```bash
/designer component Review this button for Nine Dimensions compliance
[provide code]
```

**Expected Behavior:**
- [ ] Evaluates ALL nine dimensions
- [ ] Checks protocol compliance (COMPONENT-CREATION-PROTOCOL.md)
- [ ] Validates token usage (no hardcoded values)
- [ ] Checks accessibility
- [ ] Provides specific improvement recommendations

**Success Criteria:**
- ✅ Structured review against Nine Dimensions
- ✅ Identifies hardcoded values
- ✅ Flags accessibility issues
- ✅ Prioritizes improvements (Critical/High/Medium/Low)
- ✅ Provides code examples for fixes

---

### Animation-Choreographer Agent

#### Test Case 1: Motion Design
**Command:**
```bash
/designer animate Create a modal open animation
```

**Expected Behavior:**
- [ ] Asks about emotional goal (what should this feel like?)
- [ ] References motion timing protocol
- [ ] Specifies easing curves with rationale
- [ ] Includes reduced-motion alternative
- [ ] Validates GPU-accelerated properties
- [ ] Ensures 60fps performance

**Success Criteria:**
- ✅ Timing follows protocol (300-1000ms for modal = deliberate)
- ✅ Easing curve justified (ease-out for smooth)
- ✅ Transform properties used (not width/height)
- ✅ Reduced-motion query included
- ✅ Stagger/choreography if multiple elements

**Failure Indicators:**
- ❌ Arbitrary timing (347ms)
- ❌ No reduced-motion support
- ❌ Layout-thrashing properties (width, height, top, left)
- ❌ No performance considerations

#### Test Case 2: Micro-interaction
**Command:**
```bash
/designer animate Design a button press animation
```

**Expected Behavior:**
- [ ] Timing: 100-300ms (responsive)
- [ ] Defines hover, active, focus states
- [ ] Specifies transform values (scale, translateY)
- [ ] Includes transition timing
- [ ] Validates touch-friendly (not too subtle)

**Success Criteria:**
- ✅ Hover: <100ms instant feedback
- ✅ Active: 100-300ms responsive
- ✅ Transform-based (scale 0.98, translateY 1px)
- ✅ Timing matches perceived action
- ✅ Works on touch devices

---

## Automated Validation Tests

### Script 1: Token Usage Audit
```bash
# Check for hardcoded values in components
npm run validate:tokens

# Expected: 0 violations
# If violations found, agent should fix them
```

### Script 2: TypeScript Compilation
```bash
# Check for type errors
npx tsc --noEmit

# Expected: No errors
# Validates proper prop types, imports
```

### Script 3: Build Validation
```bash
# Production build must succeed
npm run build

# Expected: Successful build
# Validates all tokens defined, no runtime errors
```

### Script 4: Hardcoded Color Detection
```bash
# Manual audit for hardcoded colors
grep -r "rgba\|#[0-9A-Fa-f]" studio-interface/components/ | grep -v "var(--"

# Expected: Only in comments or CSS variable definitions
# Agent should eliminate all hardcoded values
```

---

## Manual Testing Checklist

### After Design Work
Run through this checklist after `/designer` completes work:

#### 1. Philosophy Check
- [ ] Can articulate PURPOSE in one sentence
- [ ] Nine Dimensions addressed
- [ ] Five Pillars embodied
- [ ] Quality meets 9.5/10 baseline

#### 2. Technical Check
- [ ] All CSS variables defined in `globals.css`
- [ ] `npm run validate:tokens` passes
- [ ] `npx tsc --noEmit` passes
- [ ] `npm run build` succeeds
- [ ] No hardcoded colors, spacing, timing

#### 3. Accessibility Check
- [ ] WCAG AA contrast (4.5:1 text, 3:1 UI)
- [ ] Touch targets 44x44px minimum
- [ ] Keyboard navigation works
- [ ] Screen reader compatible
- [ ] Reduced motion support

#### 4. Mode Testing
- [ ] Works in light mode
- [ ] Works in dark mode
- [ ] Transitions smoothly between modes
- [ ] All tokens adapt correctly

#### 5. State Testing
- [ ] Loading state present
- [ ] Error state present
- [ ] Empty state present
- [ ] Success state present
- [ ] All states visually distinct

---

## Agent Self-Validation

### Design-System-Architect
Before completion, agent should verify:
```markdown
Self-Check:
- [ ] Read FRAMEWORK.md and PHILOSOPHY.md
- [ ] Applied Nine Dimensions framework
- [ ] Validated Five Pillars alignment
- [ ] Updated globals.css (if tokens added)
- [ ] Ran npm run validate:tokens
- [ ] Documented rationale
- [ ] Provided usage examples
```

### Component-Designer
Before completion, agent should verify:
```markdown
Self-Check:
- [ ] Purpose clear in 1-2 sentences
- [ ] All states specified
- [ ] Accessibility requirements met
- [ ] No hardcoded values
- [ ] Motion timing follows protocol
- [ ] Works in light AND dark modes
- [ ] Ran validation scripts
- [ ] Documentation complete
```

### Animation-Choreographer
Before completion, agent should verify:
```markdown
Self-Check:
- [ ] Timing follows protocol
- [ ] Easing curve justified
- [ ] Reduced-motion alternative
- [ ] GPU-accelerated properties
- [ ] 60fps performance validated
- [ ] Emotional goal achieved
- [ ] Works across devices
```

---

## Success Metrics

### Agent Performance Indicators

**Design-System-Architect Success:**
- ✅ 0 undefined CSS variables in production
- ✅ All tokens have clear semantic purpose
- ✅ WCAG AA standards met universally
- ✅ Developers use tokens without asking which
- ✅ System scales without breaking

**Component-Designer Success:**
- ✅ Purpose clear in one sentence
- ✅ All states handled gracefully
- ✅ Accessibility standards achieved
- ✅ Developers use correctly without help
- ✅ Users accomplish tasks without friction

**Animation-Choreographer Success:**
- ✅ Animations feel smooth and intentional
- ✅ Timing matches perceived action
- ✅ 60fps performance maintained
- ✅ Reduced motion respected
- ✅ Motion communicates meaning, not decoration

---

## Red Flags (Agent Malfunction)

### Critical Issues
Stop and investigate if agent:
- ❌ Produces hardcoded color values
- ❌ Skips purpose validation
- ❌ Ignores accessibility requirements
- ❌ Doesn't run validation scripts
- ❌ Missing states (loading, error, empty)
- ❌ Arbitrary timing (347ms, 129px)
- ❌ No rationale provided
- ❌ Skips Nine Dimensions evaluation

### Warning Signs
Review agent configuration if:
- ⚠️ Suggestions frequently rejected by user
- ⚠️ Output requires multiple revisions
- ⚠️ Missing key files (FRAMEWORK.md, PHILOSOPHY.md)
- ⚠️ Validation scripts fail
- ⚠️ Dark mode broken after changes
- ⚠️ Documentation incomplete

---

## Testing Workflow

### 1. Quick Smoke Test (5 minutes)
```bash
# Test basic routing
/designer system Create a test token
/designer component Create a test button
/designer animate Create a test transition

# Verify agents respond appropriately
```

### 2. Protocol Compliance Test (15 minutes)
```bash
# Test that agents follow protocols
/designer component Create notification toast

# Check for:
- Purpose validation question
- Nine Dimensions evaluation
- State coverage (loading, error, empty, success)
- Accessibility specifications
- Token usage (no hardcoded values)
```

### 3. Quality Validation Test (30 minutes)
```bash
# Test output quality
/designer Review entire design system

# Manually verify:
- Hardcoded color audit passes
- All validation scripts pass
- Light and dark modes work
- Accessibility standards met
- Documentation complete
```

### 4. Integration Test (60 minutes)
```bash
# End-to-end workflow
/designer system Create semantic color system
/designer component Use new colors in button component
/designer animate Add button hover animation

# Verify:
- All agents coordinate
- Tokens defined before use
- Validation passes at each step
- Final output meets 9.5/10 baseline
```

---

## Continuous Monitoring

### Weekly Audit
```bash
# Run automated checks
npm run validate:tokens
npx tsc --noEmit
npm run build

# Manual spot checks
grep -r "rgba\|#[0-9A-Fa-f]" studio-interface/components/ | grep -v "var(--"

# Review recent agent output
# - Was purpose always validated?
# - Were protocols followed?
# - Did validation scripts run?
```

### Monthly Review
- Review agent success metrics
- Analyze failure patterns
- Update protocols if needed
- Refine agent instructions
- Document learnings

---

## Debugging Agents

### If Agent Produces Hardcoded Values
1. Check: Did agent read DESIGN-SYSTEM-ENFORCEMENT.md?
2. Fix: Add explicit token enforcement to agent instructions
3. Test: Run token validation before accepting output

### If Agent Skips Validation
1. Check: Does agent have TodoWrite access?
2. Fix: Update agent workflow to include validation step
3. Test: Verify validation scripts run

### If Agent Ignores Accessibility
1. Check: Did agent read COMPONENT-CREATION-PROTOCOL.md?
2. Fix: Add accessibility checklist to agent instructions
3. Test: Verify WCAG standards met

### If Output Quality <9.5/10
1. Check: Did agent evaluate Nine Dimensions?
2. Fix: Strengthen protocol adherence
3. Test: Manual quality review

---

## Documentation

After each validation session, document:

```markdown
## Validation Session: [Date]

### Tests Run
- [ ] Smoke tests
- [ ] Protocol compliance
- [ ] Quality validation
- [ ] Integration tests

### Results
- Passed: X/Y tests
- Issues found: [list]
- Agent performance: [rating]

### Actions Taken
- Fixed: [specific fixes]
- Updated: [protocols/agents]
- Documented: [learnings]

### Follow-up
- [Next steps]
- [Schedule next validation]
```

---

## Success Criteria

### Overall Agent Health
The `/designer` system is healthy when:
- ✅ 95%+ protocol compliance rate
- ✅ All validation scripts pass
- ✅ Zero hardcoded values in production
- ✅ WCAG AA standards met universally
- ✅ User satisfaction with output quality
- ✅ Minimal revision cycles needed
- ✅ Output quality consistently 9.5/10

### Ready for Production
Agents are production-ready when:
- ✅ Pass all test cases above
- ✅ 2+ weeks of stable operation
- ✅ User trust established
- ✅ Documentation complete
- ✅ Validation automated
- ✅ Clear escalation path for issues

---

## Remember

**Validation isn't overhead—it's how we ensure agents embody our philosophy.**

The automated scripts catch technical issues. The manual checklists ensure philosophy adherence. Together they guarantee `/designer` produces work that's not just technically correct, but meaningfully excellent.

**Quality at creation beats debugging later.**

---

Last updated: 2025-01-19
Created alongside agent system to ensure continuous quality validation
