# Design Checklist

**Systematic validation for all design and development work**

This checklist ensures we follow the methodology defined in [FRAMEWORK.md](../FRAMEWORK.md) and [PRINCIPLES.md](../PRINCIPLES.md) for every component, feature, and design decision.

---

## Quick Reference

Before shipping ANY design work, verify:

- [ ] **Layer 1: Purpose & Intent** - Why does this exist?
- [ ] **Layer 2: Expression & Manifestation** - How should it work?
- [ ] **Layer 3: Context & Appropriateness** - For whom?
- [ ] **Layer 4: Contextual Adaptation** - How does context shape it?
- [ ] **Design System Validation** - Are all tokens defined?
- [ ] **Five Pillars Verification** - Does it embody our principles?

---

## Layer 1: Purpose & Intent (What and Why)

**Before any aesthetic choice, answer:**

- [ ] **Should this exist?** (Necessity)
  - What problem does this solve?
  - Is this the simplest solution?
  - What happens if we don't build this?

- [ ] **What problem does this solve?** (Function)
  - What user goal does this serve?
  - How does this improve the experience?
  - What pain point does this address?

- [ ] **For whom?** (Audience)
  - Who will use this?
  - What are their needs and expectations?
  - What context are they in when using this?

- [ ] **Why now?** (Timing and context)
  - Why is this the right moment?
  - What dependencies or prerequisites exist?
  - Is this the right phase of the project?

- [ ] **What values does this embody?** (Ethics and positioning)
  - How does this align with our Five Pillars?
  - What message does this send to users?
  - Does this respect user agency and privacy?

**Documentation**: Write a 2-3 sentence purpose statement explaining the "why" before proceeding to implementation.

---

## Layer 2: Expression & Manifestation (How)

### Functional Requirements

- [ ] **Capabilities**
  - What must this do?
  - What edge cases exist?
  - What error states need handling?

- [ ] **Constraints**
  - What technical limitations apply?
  - What performance requirements exist?
  - What browser/device support is needed?

- [ ] **Accessibility Standards**
  - Does it pass WCAG 2.1 Level AA?
  - Is it keyboard navigable?
  - Does it work with screen readers?
  - Are touch targets at least 44x44px (Apple) or 48x48dp (Android)?

### Experiential Requirements

- [ ] **How should it feel to use?**
  - What emotional response should it evoke?
  - Is the interaction intuitive?
  - Does it provide appropriate feedback?

- [ ] **What behavior should it encourage?**
  - Does it guide users toward their goals?
  - Does it prevent errors proactively?
  - Does it make the right action obvious?

- [ ] **What mental model should it build?**
  - Is the interaction pattern familiar?
  - Does it match user expectations?
  - Is the system status visible?

### Aesthetic Requirements (Nine Dimensions)

#### 1. Style
- [ ] Visual language communicates personality and values
- [ ] All elements work together cohesively
- [ ] Approach is appropriate for context (B2B vs consumer, etc.)
- [ ] Style documented with examples

#### 2. Motion
- [ ] Timing is appropriate for context
  - <100ms for instant feedback (hover states)
  - 100-300ms for responsive actions (button presses)
  - 300-1000ms for deliberate transitions (modals)
  - >1000ms includes progress indication
- [ ] Easing curve matches intent
  - `ease-out` for smooth, polished
  - `cubic-bezier(0.34, 1.56, 0.64, 1)` for spring physics
- [ ] Motion respects `prefers-reduced-motion`
- [ ] All animations documented (duration, easing, purpose)

#### 3. Voice
- [ ] Language matches personality (voice)
- [ ] Tone adapts to context
- [ ] Copy is clear and concise
- [ ] No jargon or unnecessary complexity
- [ ] Error messages are helpful, not blaming

#### 4. Space
- [ ] White space creates hierarchy
- [ ] Proximity shows relationships (Gestalt principles)
- [ ] Layout guides attention through flow
- [ ] Space signals appropriately (generous = premium, tight = utilitarian)
- [ ] Can remove 20% of elements without losing function?

#### 5. Color
- [ ] Color choices have documented rationale
- [ ] Contrast ratios meet WCAG standards
  - 4.5:1 minimum for normal text
  - 7:1 for maximum accessibility
  - 3:1 minimum for UI components
- [ ] Color blind simulation tested
- [ ] Cultural context considered
- [ ] Color system documented

#### 6. Typography
- [ ] Hierarchy is clear (size, weight, color, space)
- [ ] Line height is 1.125-1.5× font size
- [ ] Line length is 45-75 characters optimal
- [ ] Maximum 2-3 typefaces used
- [ ] Type scale documented

#### 7. Proportion
- [ ] Scale relationships feel balanced
- [ ] Mathematical system applied (golden ratio, Fibonacci, rule of thirds)
- [ ] Visual adjustment applied where needed
- [ ] Proportions documented

#### 8. Texture
- [ ] Texture serves purpose (not decoration)
- [ ] Materiality is appropriate for context
- [ ] Doesn't reduce readability
- [ ] Texture choices documented

#### 9. Body (Ergonomics)
- [ ] Touch targets are appropriately sized
  - 44×44px minimum (Apple)
  - 48×48dp minimum (Android)
- [ ] Thumb zones considered for mobile
- [ ] Keyboard navigation works
- [ ] Physical interaction tested on real devices

---

## Layer 3: Context & Appropriateness (For Whom)

- [ ] **Cultural Context**
  - What meanings do these choices carry?
  - Are symbols/colors culturally appropriate?
  - Is language inclusive?

- [ ] **Audience Expectations**
  - What conventions does this audience expect?
  - Should we follow or break conventions? (documented rationale)
  - Does this match their mental model?

- [ ] **Industry Context**
  - What standards exist in this industry?
  - What competitors do (not to copy, but to understand)
  - What differentiates us appropriately?

- [ ] **Temporal Context**
  - Is this timeless or trend-responsive?
  - Will this age well?
  - How will we maintain this?

---

## Layer 4: Contextual Adaptation (How Context Shapes Expression)

### Physical Context

- [ ] **Desktop** (if applicable)
  - Precision interactions work?
  - Information density appropriate?
  - Hover states provide feedback?

- [ ] **Mobile** (if applicable)
  - Thumb zones optimized?
  - Touch targets large enough?
  - Works one-handed?
  - Simplified hierarchy for smaller screen?

- [ ] **Tablet** (if applicable)
  - Hybrid interactions considered?
  - Orientation handled?

- [ ] **Voice** (if applicable)
  - Conversational (not command-like)?
  - Confirmatory feedback provided?
  - Hands-free, eyes-free?

### Attention Context

- [ ] **Focused** (primary task)
  - Rich information available?
  - Details accessible?

- [ ] **Divided** (multitasking)
  - Cognitive load reduced?
  - Critical info prominent?

- [ ] **Interrupted** (notifications)
  - Progressive disclosure used?
  - Context respected?

### Environmental Context

- [ ] **Bright sunlight**
  - High contrast?
  - Dark mode optional?

- [ ] **Noisy environment**
  - Visual primary?
  - Haptic feedback?

- [ ] **Quiet space**
  - Audio appropriate?

- [ ] **Public space**
  - Privacy respected?
  - Discreet visuals?

---

## Design System Validation

### CSS Variables & Tokens

- [ ] **All CSS variables used are defined**
  - Check `globals.css` for undefined variables
  - Document new variables before use
  - Follow naming conventions

- [ ] **Color System Complete**
  - [ ] Base palette defined
  - [ ] Semantic mapping complete (`--bg-primary`, `--text-primary`, etc.)
  - [ ] Contrast ratios validated
  - [ ] Dark mode variants (if applicable)

- [ ] **Typography System Complete**
  - [ ] Font families defined
  - [ ] Type scale defined
  - [ ] Line heights defined
  - [ ] Font weights defined

- [ ] **Spacing System Complete**
  - [ ] Base unit defined (usually 4px or 8px)
  - [ ] Scale consistent (4, 8, 12, 16, 24, 32, 48, 64, 96, 128...)
  - [ ] All spacing uses system values

- [ ] **Shadow System Complete**
  - [ ] Shadow levels defined
  - [ ] Appropriate for context
  - [ ] Consistent across components

- [ ] **Border Radius System Complete**
  - [ ] Radius scale defined
  - [ ] Consistent application
  - [ ] Appropriate for brand

- [ ] **Animation System Complete**
  - [ ] Duration scale defined
  - [ ] Easing curves defined
  - [ ] Keyframes documented
  - [ ] Respects reduced motion

### Component Classes

- [ ] **All utility classes are defined**
  - `.studio-*` classes documented
  - Hover states defined
  - Focus states defined
  - Active states defined

- [ ] **No undefined classes in browser console**
  - Test in browser dev tools
  - Check for undefined CSS warnings

---

## Five Pillars Verification

### 1. Purpose Drives Execution

- [ ] Clear "why" documented
- [ ] Purpose statement written
- [ ] User need identified
- [ ] Alternatives considered

**Questions**:
- Why does this need to exist?
- Who will use this and what do they need?
- What problem does this solve?

### 2. Craft Embeds Care

- [ ] Tested on real devices
- [ ] Accessibility validated
- [ ] Edge cases handled
- [ ] Error states designed
- [ ] Loading states designed
- [ ] Empty states designed
- [ ] Details refined (timing, spacing, contrast)
- [ ] **No emojis as UI elements** (unless explicitly requested)
- [ ] **No Unicode characters or text as icons** (use proper icon system)

**Question**: Would I be proud to show this to an expert?

### 3. Constraints Enable Creativity

- [ ] Works within design system
- [ ] Locked properties respected
- [ ] Creativity found within constraints
- [ ] Novel combinations explored

**Question**: What CAN I change vs what should stay locked?

### 4. Intentional Incompleteness

- [ ] Room for user expression
- [ ] Content customizable
- [ ] Context adaptable
- [ ] No over-engineering

**Question**: Does this leave room for users to make it their own?

### 5. Design for Humans

- [ ] Keyboard navigable
- [ ] Screen reader compatible
- [ ] Color contrast validated
- [ ] Reduced motion respected
- [ ] Touch targets sized for real fingers
- [ ] Tested with diverse users
- [ ] Real content used (not Lorem Ipsum)

**Question**: Can someone with low vision, motor impairment, or screen reader use this?

---

## Pre-Ship Final Checklist

**Before committing or deploying, verify ALL are checked:**

### Code Quality
- [ ] No console errors
- [ ] No console warnings about undefined CSS
- [ ] TypeScript passes with no errors
- [ ] Build completes successfully
- [ ] Tests pass (if applicable)

### Design Quality
- [ ] All design tokens defined
- [ ] All interactions tested
- [ ] All states designed (hover, focus, active, disabled, loading, error, empty)
- [ ] Responsive behavior verified
- [ ] Cross-browser tested (Chrome, Safari, Firefox minimum)

### Documentation
- [ ] Purpose documented
- [ ] Rationale for key decisions documented
- [ ] Usage examples provided
- [ ] Known limitations noted

### Accessibility
- [ ] Automated accessibility tests pass
- [ ] Manual keyboard testing done
- [ ] Screen reader testing done
- [ ] Color contrast verified
- [ ] Touch target sizes verified

### User Testing
- [ ] Tested with real users (or plan to)
- [ ] Feedback incorporated
- [ ] Edge cases validated

---

## How to Use This Checklist

### For New Components

1. **Start with Layer 1** - Don't code until purpose is clear
2. **Define Expression** (Layer 2) - How will it manifest?
3. **Consider Context** (Layer 3-4) - Who and where?
4. **Validate Design System** - Are all tokens defined?
5. **Verify Five Pillars** - Does it embody our values?
6. **Pre-Ship Check** - Final validation before commit

### For Existing Components

1. **Audit against checklist** - What's missing?
2. **Prioritize gaps** - What's critical vs nice-to-have?
3. **Document findings** - What needs fixing?
4. **Create tasks** - Break into actionable items
5. **Fix and re-validate** - Use checklist to verify fixes

### For Design Reviews

1. **Use as review guide** - Walk through each section
2. **Document gaps** - What doesn't pass?
3. **Prioritize fixes** - What's blocking vs enhancement?
4. **Re-review** - Verify fixes pass checklist

---

## Automation Opportunities

**Future improvements to automate this checklist:**

1. **CSS Variable Validator**
   - Script to scan codebase for undefined CSS variables
   - Compare against `globals.css` definitions
   - Output report of missing variables

2. **Accessibility Auditor**
   - Automated contrast checking
   - Touch target size validation
   - Keyboard navigation testing
   - Screen reader compatibility checks

3. **Design Token Completeness**
   - Validate all design system components exist
   - Check for gaps in token definitions
   - Ensure consistency across files

4. **Pre-commit Hooks**
   - Run validators before allowing commits
   - Block commits with undefined CSS variables
   - Warn on accessibility issues

---

## Remember

**This checklist exists to ensure quality, not to slow you down.**

- Use it as a thinking tool, not just a checkbox exercise
- Skip irrelevant sections (e.g., voice for visual-only components)
- Add project-specific items as needed
- Review and update this checklist as we learn

**The goal**: Ship work we're proud of, that serves users well, and embodies our values.

---

## Resources

- [FRAMEWORK.md](../FRAMEWORK.md) - Full design sensibility framework
- [PRINCIPLES.md](../PRINCIPLES.md) - Quick reference for daily practice
- [PHILOSOPHY.md](../PHILOSOPHY.md) - Five Pillars detailed explanation
- [knowledge-base/](../knowledge-base/) - Deep dives on specific topics
