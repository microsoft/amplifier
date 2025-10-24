# Amplified Design - Contributing

**Building together with integrity**

---

## Welcome

We welcome contributions that maintain our commitment to quality, originality, and ethical practice. This guide helps you contribute in ways that align with our values.

---

## Core Principles for Contributors

### 1. Original Work
All contributions should be your own original thinking and implementation.

**Patterns (Do This)**:
- Write your own code implementations
- Create your own examples and scenarios
- Draw on established principles (cite them generically)
- Build on common patterns in the field
- Share your own insights and discoveries

**Anti-Patterns (Avoid This)**:
- Copying code from other projects without proper licensing
- Replicating unique implementations from other systems
- Using proprietary assets without permission
- Claiming others' specific creative work as your own

### 2. Inspiration vs. Replication

When inspired by other work:

**Pattern**: Extract principles, create original expression
```
See something great →
Ask "why does this work?" →
Understand the principle →
Apply principle to your context →
Create something original
```

**Anti-Pattern**: Copy implementation, change names
```
See something great →
Copy the code/design →
Rename variables →
Submit as contribution ❌
```

**Example**:
```
✅ "I studied how design systems handle motion, and here's my
   original implementation of easing curves based on those principles"

❌ "I copied Framer Motion's spring physics and renamed the functions"
```

### 3. Attribution

**Pattern**: Credit the ecosystem
- "Based on established design principles"
- "Inspired by motion design research"
- "Following accessibility standards (WCAG 2.1)"
- "Common pattern in modern design systems"

**Anti-Pattern**: Claim everything or credit nothing
- Don't claim universal principles as your invention
- Don't skip attribution for specific implementations you're building on
- Don't over-attribute (crediting every common pattern)

**Real Example**:
```tsx
// Good attribution
// Using cubic-bezier easing based on motion design research
const easing = 'cubic-bezier(0.34, 1.56, 0.64, 1)';

// Not needed - it's a standard value
// Using cubic-bezier(0.34, 1.56, 0.64, 1) from [specific source]

// Bad - claiming universal pattern
// I invented this cubic-bezier approach ❌
```

---

## Types of Contributions

### Components

**What We're Looking For**:
- 9.5/10 quality baseline
- Clear documentation of locked vs. customizable properties
- Accessibility-first implementation
- Original code and examples

**Pattern**: Thoughtful refinement
1. Identify a real need (not just "cool effect")
2. Research best practices in the field
3. Create your own implementation
4. Test thoroughly for accessibility and performance
5. Document the "why" behind decisions

**Anti-Pattern**: Quick ports
1. Find cool CodePen
2. Copy code
3. Submit without understanding ❌

### Documentation

**What We're Looking For**:
- Clear, actionable guidance
- Original examples and scenarios
- Proper attribution to standards/principles

**Pattern**: Teaching through original examples
```markdown
## Contrast Validation

Our system requires 4.5:1 contrast (WCAG AA standard).

Here's how it works in practice:
[Your own example with your component]
```

**Anti-Pattern**: Copying existing docs
```markdown
## Contrast Validation

[Copy/paste from another design system] ❌
```

### Knowledge Base

**What We're Looking For**:
- Well-researched content
- Clear citations to authoritative sources
- Original explanations and applications

**Pattern**: Research and synthesize
```markdown
# Color Theory

Based on established color theory principles, here's how
we apply them to component design:

[Your original application and examples]

**Further Reading**:
- "Interaction of Color" by Josef Albers
- WCAG 2.1 Color Contrast Guidelines
```

**Anti-Pattern**: Republishing
```markdown
# Color Theory

[Copied content from a book/article] ❌
```

### Bug Fixes

**What We're Looking For**:
- Clear problem statement
- Minimal, focused fix
- Tests to prevent regression

**Pattern**: Fix with understanding
1. Identify the issue
2. Understand root cause
3. Fix specifically
4. Test thoroughly
5. Document why the fix works

---

## Practical Guidelines

### When Studying Other Work

**Do**:
- Study how others solve problems
- Understand the principles they use
- Note patterns across multiple sources
- Create your own implementation

**Don't**:
- Copy their specific implementation
- Replicate their unique approaches
- Use their proprietary code
- Claim their insights

### When Someone Asks: "Make it like [famous example]"

**Pattern**: Understand essence, create original
1. Ask what specifically resonates
2. Identify the underlying principles
3. Understand their context and goals
4. Create original implementation serving their needs

**Anti-Pattern**: Clone the example
1. Copy the design/code
2. Change colors ❌

**Real Contribution Example**:

```markdown
**User Request**: "Can we add a button like Stripe's?"

**Poor Response**: [Copies Stripe's button]

**Good Response**: "Stripe's buttons work well because of:
- High contrast (accessibility)
- Clear hierarchy (visual design)
- Immediate feedback (UX)

Here's an original implementation applying those principles
to our system..."
```

---

## Quality Standards

All contributions must meet:

### Technical Quality
- [ ] Works across supported browsers
- [ ] Accessible (keyboard, screen reader, contrast)
- [ ] Performs at 60fps
- [ ] Responsive and mobile-friendly

### Code Quality
- [ ] Original implementation
- [ ] Clear, documented code
- [ ] Follows project patterns
- [ ] Includes tests where applicable

### Documentation Quality
- [ ] Original writing
- [ ] Clear examples
- [ ] Proper attribution where needed
- [ ] Explains "why" not just "how"

---

## The Contribution Process

### 1. Discuss First (For Large Changes)
Open an issue to discuss:
- What problem you're solving
- Your proposed approach
- How it fits our philosophy

### 2. Create Original Work
Build your contribution:
- Write your own code/documentation
- Test thoroughly
- Document decisions

### 3. Submit Pull Request
Include:
- Clear description of what and why
- Tests/examples demonstrating it works
- Documentation updates
- Attribution if building on specific sources

### 4. Iterate Based on Feedback
Be open to:
- Suggestions for improvement
- Questions about approach
- Requests for clarification

---

## Examples of Good Contributions

### Pattern: Adding a New Variant

```markdown
## Bounce Button Variant

**Purpose**: Celebratory actions (form completion, milestones)

**Implementation**: Original physics-based animation using
spring equations from classical mechanics.

**Research**: Studied how physical springs behave, applied
to digital motion design following established principles
from motion design research.

**Locked Properties**:
- Spring physics constants (k, damping)
- Animation duration curves
- Transform boundaries

**Customizable**:
- Colors (with validation)
- Size (from standard scale)
- Icon placement
```

### Pattern: Improving Documentation

```markdown
## Added Accessibility Testing Guide

Created original guide showing how to test our components
with screen readers and keyboard navigation.

**Content**:
- My own testing workflow
- Original examples using our components
- Links to WCAG standards
- Common issues I found and fixed

**Attribution**: Testing approach based on WCAG 2.1
guidelines and common accessibility practices.
```

---

## What We Don't Accept

### Direct Copies
- Code copied from other libraries
- Documentation republished from other sources
- Examples taken from other projects

### Proprietary Material
- Brand assets used without permission
- Code from closed-source projects
- Trademarked materials

### Poor Quality
- Untested code
- Inaccessible implementations
- Breaking changes without discussion

---

## If You're Unsure

**Ask first!** We'd rather clarify upfront than have work rejected later.

Questions to ask yourself:
- "Is this implementation my own original work?"
- "If inspired by something, did I extract principles and create original?"
- "Have I attributed appropriately?"
- "Does this meet our quality standards?"

If unsure about any of these, open an issue to discuss.

---

## Our Commitment

We commit to:
- **Reviewing contributions fairly** - Judge on merit and fit
- **Providing constructive feedback** - Help you improve
- **Maintaining our standards** - Quality and ethics matter
- **Being responsive** - Reply within reasonable timeframe
- **Appreciating your effort** - Thank you for contributing!

---

## Questions?

- Open an issue for discussion
- Check our [PRINCIPLES.md](./PRINCIPLES.md) for philosophy
- Review [PHILOSOPHY.md](./PHILOSOPHY.md) for deeper context
- Look at existing components for patterns

---

**Thank you for contributing with integrity!**

We build better together when we build with care, originality, and respect for the broader design community.
