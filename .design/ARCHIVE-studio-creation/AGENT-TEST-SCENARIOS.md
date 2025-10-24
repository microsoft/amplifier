# Agent Test Scenarios

**Concrete test cases to validate `/designer` agent behavior**

---

## Quick Test Suite (5 minutes)

Run these to verify agents are functioning:

### Test 1: Basic Routing
```bash
/designer Create a primary button component
```

**Expected:** Routes to component-designer
**Pass criteria:** Agent responds with component design process

### Test 2: System Token
```bash
/designer system Add a new shadow token
```

**Expected:** Routes to design-system-architect
**Pass criteria:** Agent asks for purpose and context

### Test 3: Animation
```bash
/designer animate Create a loading spinner
```

**Expected:** Routes to animation-choreographer
**Pass criteria:** Agent asks about emotional goal and timing

---

## Protocol Compliance Suite (15 minutes)

### Scenario A: Component Creation with All Checks

**Command:**
```bash
/designer component Design a notification card with success, warning, and error variants
```

**Step-by-Step Validation:**

1. **Purpose Validation** ✓
   - [ ] Agent asks: "Why does this component need to exist?"
   - [ ] Agent asks: "What specific user need does it solve?"
   - [ ] Agent asks: "Is this the simplest solution?"

2. **Design System Audit** ✓
   - [ ] Agent checks if similar component exists
   - [ ] Agent reviews existing tokens
   - [ ] Agent plans token usage (no hardcoding)

3. **Nine Dimensions Evaluation** ✓
   - [ ] **Style**: Visual language referenced (German car facility)
   - [ ] **Motion**: Timing specified (<100ms, 100-300ms, etc.)
   - [ ] **Voice**: Copy tone defined (clear, non-blaming)
   - [ ] **Space**: Layout follows 8px system
   - [ ] **Color**: Contrast validated (4.5:1 text, 3:1 UI)
   - [ ] **Typography**: Hierarchy clear
   - [ ] **Proportion**: Touch targets sized (44x44px)
   - [ ] **Texture**: Purpose-driven depth
   - [ ] **Body**: Keyboard navigation specified

4. **Five Pillars Check** ✓
   - [ ] **Purpose**: Articulated in 1 sentence
   - [ ] **Craft**: All states defined (loading, error, empty, success)
   - [ ] **Constraints**: Uses design system tokens
   - [ ] **Incompleteness**: Props allow customization
   - [ ] **Humans**: Accessibility requirements met

5. **Output Specification** ✓
   - [ ] Props API defined
   - [ ] All variants documented
   - [ ] All states specified
   - [ ] Accessibility notes included
   - [ ] Usage examples provided
   - [ ] Token references (no hardcoded values)

6. **Validation** ✓
   - [ ] Agent reminds to run `npm run validate:tokens`
   - [ ] Agent reminds to run `npx tsc --noEmit`
   - [ ] Agent confirms light AND dark mode support

**Pass Criteria:**
- All checkboxes ticked
- No hardcoded color/spacing values
- Purpose crystal clear
- Ready for implementation

---

### Scenario B: System Token with Dark Mode

**Command:**
```bash
/designer system Create a semantic color token for info states
```

**Validation Checklist:**

1. **Need Assessment** ✓
   - [ ] Agent asks: "Do we have existing tokens that could serve this?"
   - [ ] Agent reviews current semantic colors
   - [ ] Agent confirms necessity

2. **Token Design** ✓
   - [ ] Semantic naming: `--color-info` (not `--blue`)
   - [ ] Light mode value defined
   - [ ] Dark mode value defined
   - [ ] WCAG AA contrast validated for both modes

3. **Implementation** ✓
   - [ ] Adds to `:root` for light mode
   - [ ] Adds to `@media (prefers-color-scheme: dark)` for dark mode
   - [ ] Adds to `[data-theme="dark"]` for manual toggle
   - [ ] Updates in `studio-interface/app/globals.css`

4. **Documentation** ✓
   - [ ] Usage examples provided
   - [ ] When to use explained
   - [ ] Integration notes included

5. **Validation** ✓
   - [ ] Runs `npm run validate:tokens`
   - [ ] Tests in light mode
   - [ ] Tests in dark mode
   - [ ] Confirms no undefined references

**Pass Criteria:**
- Token defined for BOTH modes
- Semantic naming convention
- Contrast validated
- Validation script passes

---

### Scenario C: Animation with Reduced Motion

**Command:**
```bash
/designer animate Design a page transition animation
```

**Validation Checklist:**

1. **Context Gathering** ✓
   - [ ] Agent asks: "What should this feel like?" (emotional goal)
   - [ ] Agent asks about transition type (modal, page, section)
   - [ ] Agent considers user flow

2. **Motion Design** ✓
   - [ ] Timing: 300-1000ms (deliberate for page transition)
   - [ ] Easing: Justified (ease-out for natural deceleration)
   - [ ] Properties: Transform-based (not width/height)
   - [ ] Choreography: Stagger if multiple elements

3. **Reduced Motion** ✓
   - [ ] `@media (prefers-reduced-motion: reduce)` included
   - [ ] Alternative: Fade or instant (no motion)
   - [ ] Respects user preference

4. **Performance** ✓
   - [ ] GPU-accelerated properties only (transform, opacity)
   - [ ] 60fps target
   - [ ] No layout thrashing
   - [ ] Tested on mobile

5. **Implementation Guidance** ✓
   - [ ] CSS keyframes or transition defined
   - [ ] JavaScript trigger pattern (if needed)
   - [ ] Exit animation specified
   - [ ] Timing constants named

**Pass Criteria:**
- Timing follows protocol
- Reduced motion support
- Performance validated
- Implementation clear

---

## Edge Case Testing (30 minutes)

### Edge Case 1: Conflicting Requirements

**Command:**
```bash
/designer component Create a button that's 24x24px with text label
```

**Expected Behavior:**
- [ ] Agent flags: Touch target too small (44x44px minimum)
- [ ] Agent suggests: Visual size 24x24, clickable area 44x44
- [ ] Agent provides: Code example with padding

**Pass Criteria:**
- Agent catches accessibility violation
- Provides solution maintaining visual design
- Explains rationale (WCAG, Apple HIG)

---

### Edge Case 2: Undefined Token Request

**Command:**
```bash
/designer component Use --color-brand-blue for this button
```

**Expected Behavior:**
- [ ] Agent checks: Is `--color-brand-blue` defined?
- [ ] If not: Agent refuses to use undefined token
- [ ] Agent suggests: Define token first OR use existing semantic token
- [ ] Agent guides: Add to globals.css before use

**Pass Criteria:**
- Agent doesn't use undefined tokens
- Clear guidance provided
- Enforces token-first workflow

---

### Edge Case 3: Hardcoded Value in Request

**Command:**
```bash
/designer component Make the background #F8F9F6
```

**Expected Behavior:**
- [ ] Agent recognizes: Hardcoded color requested
- [ ] Agent suggests: Use `var(--bg-primary)` or define new token
- [ ] Agent explains: Why tokens > hardcoded (dark mode, consistency)
- [ ] Agent implements: Using tokens only

**Pass Criteria:**
- Agent refuses to hardcode values
- Educates user on token system
- Provides token-based solution

---

### Edge Case 4: Missing State Coverage

**Command:**
```bash
/designer component Create a data table component
```

**Expected Behavior:**
- [ ] Agent asks: "What happens when loading?"
- [ ] Agent asks: "What happens when error?"
- [ ] Agent asks: "What happens when empty?"
- [ ] Agent specifies: All states in design

**Pass Criteria:**
- Agent proactively identifies missing states
- Ensures complete state coverage
- Documents all states

---

## Integration Testing (60 minutes)

### End-to-End Workflow

**Scenario: Design and implement a themed notification system**

**Step 1: System Design**
```bash
/designer system Create semantic color tokens for notification types
```

**Validation:**
- [ ] Tokens created: `--color-success`, `--color-warning`, `--color-error`, `--color-info`
- [ ] Light mode values defined
- [ ] Dark mode values defined
- [ ] Contrast validated for both modes
- [ ] Added to `globals.css`
- [ ] `npm run validate:tokens` passes

**Step 2: Component Design**
```bash
/designer component Create notification component using new tokens
```

**Validation:**
- [ ] Uses tokens from Step 1 (no hardcoding)
- [ ] All variants: success, warning, error, info
- [ ] All states: default, with-action, dismissible
- [ ] Accessibility: ARIA roles, keyboard dismiss
- [ ] Motion: Slide-in animation specified

**Step 3: Animation Design**
```bash
/designer animate Design notification slide-in animation
```

**Validation:**
- [ ] Timing: 300ms (deliberate entrance)
- [ ] Easing: ease-out (smooth deceleration)
- [ ] Transform: translateX (from off-screen)
- [ ] Reduced motion: Fade-in alternative
- [ ] Exit animation: Reverse timing

**Step 4: Integration Validation**
```bash
npm run validate:tokens
npx tsc --noEmit
npm run build
```

**Validation:**
- [ ] All scripts pass
- [ ] No undefined tokens
- [ ] No type errors
- [ ] Build succeeds
- [ ] Works in light mode
- [ ] Works in dark mode

**Pass Criteria:**
- All steps completed
- Agents coordinated properly
- Tokens defined before use
- Validation passes throughout
- Final output meets 9.5/10 baseline

---

## Failure Mode Testing

### Test: Agent Skips Validation

**Command:**
```bash
/designer component Create a simple button
```

**Inject Failure:** Observe if agent skips `npm run validate:tokens`

**Expected:**
- [ ] Agent should ALWAYS recommend validation
- [ ] Agent should mention validation scripts
- [ ] Agent should verify token usage

**If Failed:**
1. Check agent instructions include validation step
2. Add explicit validation reminder to agent
3. Test again

---

### Test: Agent Produces Hardcoded Values

**Command:**
```bash
/designer component Create a card with light background
```

**Inject Failure:** Check output for `#FFFFFF` or `rgba(...)`

**Expected:**
- [ ] Agent uses `var(--bg-primary)` or similar
- [ ] NO hardcoded hex codes
- [ ] NO hardcoded rgba values

**If Failed:**
1. Review DESIGN-SYSTEM-ENFORCEMENT.md
2. Strengthen agent token enforcement
3. Add pre-check for hardcoded values
4. Test again

---

### Test: Agent Ignores Accessibility

**Command:**
```bash
/designer component Create an icon button
```

**Inject Failure:** Check if aria-label specified

**Expected:**
- [ ] Agent specifies `aria-label` requirement
- [ ] Touch target 44x44px minimum
- [ ] Keyboard navigation addressed
- [ ] Screen reader compatibility noted

**If Failed:**
1. Review COMPONENT-CREATION-PROTOCOL.md
2. Add accessibility checklist to agent
3. Test again

---

## Regression Testing

**Run monthly to ensure agents maintain quality:**

### Regression Suite
1. Re-run all Quick Tests (5 min)
2. Re-run 3 Protocol Compliance tests (15 min)
3. Re-run 1 Integration test (60 min)
4. Review failure patterns
5. Update agent instructions if needed

**Document:**
```markdown
## Regression Test: [Date]

### Tests Run
- Quick: [Pass/Fail count]
- Protocol: [Pass/Fail count]
- Integration: [Pass/Fail count]

### Changes Since Last Test
- [Agent updates]
- [Protocol changes]
- [New features]

### Issues Found
- [List issues]
- [Root causes]
- [Fixes applied]

### Next Test
- Scheduled: [Date]
- Focus: [Areas to emphasize]
```

---

## Success Metrics

### Agent Health Score

**Calculate after each test session:**

```
Health Score = (Passed Tests / Total Tests) × 100

90-100%: Excellent - Production ready
80-89%: Good - Minor tuning needed
70-79%: Fair - Review agent instructions
<70%: Poor - Major investigation needed
```

**Track over time:**
- Week 1: ___%
- Week 2: ___%
- Week 3: ___%
- Month 1: ___%

**Goal:** Maintain 95%+ health score

---

## Quick Reference

### Daily Smoke Test (1 minute)
```bash
/designer Create a test button
# Verify: Responds appropriately, follows protocol
```

### Weekly Validation (30 minutes)
```bash
# Run Protocol Compliance Suite
# Check: All validation scripts pass
# Review: Any failure patterns
```

### Monthly Deep Dive (2 hours)
```bash
# Run full test suite
# Run regression tests
# Update documentation
# Refine agent instructions
```

---

## Remember

**Testing agents isn't about catching failures—it's about ensuring quality compounds over time.**

Each test validates that agents embody our philosophy. Each validation strengthens the system. Each refinement makes future work better.

**Quality at creation beats debugging later.**

---

Last updated: 2025-01-19
Created to provide concrete test scenarios for agent validation
