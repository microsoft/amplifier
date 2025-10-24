# Quality Guardrails

**JSON schemas defining locked properties, validation rules, and quality standards**

---

## Purpose

Quality guardrails ensure that component customizations maintain the 9.5/10 baseline quality through:

- **Locked Properties**: Preserve refinement (timing, easing, physics)
- **Customizable Constraints**: Safe modification boundaries (colors, sizes)
- **Validation Rules**: Automated quality checks
- **Agent Permissions**: What AI agents can/cannot modify

---

## Current Guardrails

### [Hero Button](./hero-button.json)
Comprehensive guardrails for all 6 button variants.

**Locked Properties** (Never customizable):
- **Timing Functions**: `cubic-bezier` curves tuned for natural motion
- **Animation Durations**: 300ms, 600ms, etc. (optimized for perception)
- **Transform Physics**: 8px magnetic pull, 1.05 scale max
- **Shadow Blur Radii**: Balanced depth without excessive blur
- **Micro-interactions**: Particle counts, ripple physics

**Customizable** (Within constraints):
- **Colors**: 4.5:1 contrast minimum (WCAG AA)
- **Sizes**: sm, md, lg, xl (predefined scale only)
- **Border Radius**: 0-24px range

**Fully Flexible** (No restrictions):
- Content, icons, width, click handlers, ARIA labels

**[View full schema →](./hero-button.json)**

---

## Schema Structure

Each component guardrail file contains:

### 1. Locked Properties
```json
{
  "locked_properties": {
    "timing_functions": {
      "locked": true,
      "reason": "Carefully tuned for natural, premium feel",
      "values": {
        "bounce_spring": "cubic-bezier(0.34, 1.56, 0.64, 1)"
      }
    }
  }
}
```

**Why locked?** These properties create the "refined" feel. Modifying them degrades quality back to generic 5/10.

### 2. Customizable Properties
```json
{
  "customizable_properties": {
    "colors": {
      "customizable": true,
      "guardrails": {
        "contrast_ratio": {
          "normal_text": {
            "min": 4.5,
            "recommended": 7.0
          }
        }
      }
    }
  }
}
```

**Safe to modify** as long as constraints are met.

### 3. Validation Rules
```json
{
  "validation_rules": {
    "pre_deployment": [
      {
        "rule": "contrast_validation",
        "severity": "critical",
        "auto_reject": true
      }
    ]
  }
}
```

**Automated checks** that run before deployment.

### 4. Agent Permissions
```json
{
  "agent_permissions": {
    "customization_guide": {
      "can_recommend": ["colors", "sizes"],
      "cannot_modify": ["timing_functions"]
    },
    "quality_guardian": {
      "final_authority": true
    }
  }
}
```

**Defines** what each AI agent can do.

### 5. Accessibility Requirements
```json
{
  "accessibility_requirements": {
    "keyboard_navigation": {
      "required": true
    },
    "touch_targets": {
      "ios_minimum": "44px"
    }
  }
}
```

**Non-negotiable** accessibility standards.

### 6. Performance Requirements
```json
{
  "performance_requirements": {
    "frame_rate": {
      "target": 60,
      "minimum": 60
    },
    "gpu_acceleration": {
      "allowed_properties": ["transform", "opacity"]
    }
  }
}
```

**Performance** targets and constraints.

---

## How Guardrails Are Used

### By AI Agents

**Customization Guide**:
- References to know what's safe to recommend
- Suggests colors within contrast constraints
- Recommends sizes from predefined scale

**Quality Guardian**:
- Validates all changes against rules
- Auto-rejects violations (contrast, locked properties)
- Suggests alternatives that pass

**Orchestrator**:
- Routes requests based on permissions
- Ensures agents respect constraints

### By Developers

- Understand what can/cannot be customized
- See reasoning behind locked properties
- Reference validation rules
- Check accessibility requirements

### By Contributors

- Know constraints when adding components
- Define guardrails for new components
- Maintain consistent quality standards

---

## Why Lock Properties?

### The Problem
Users (and AI) don't know what they don't know:
- "Make it faster" → breaks natural feel
- "More dramatic" → becomes janky
- "Different curve" → loses refinement

### The Solution
Lock the properties that create quality:
- **Timing** - 300ms isn't arbitrary, it matches perception
- **Easing** - Curves tested extensively for natural feel
- **Physics** - 8px magnetic pull is the "Goldilocks zone"

### The Benefit
- Quality preserved at 9.5/10
- Customization focused on brand (colors, content)
- No accidental quality regression

---

## Validation Flow

```
User/AI proposes change
    ↓
Check locked properties
    ↓
Locked? → Reject
    ↓
Check constraints (contrast, size, etc.)
    ↓
Failed? → Reject with alternatives
    ↓
Check accessibility
    ↓
Failed? → Reject with fix
    ↓
Check performance
    ↓
Failed? → Reject with optimization
    ↓
All passed → Approve ✅
```

---

## Example Validation

### Color Change Request
```
User: "Use #FBBF24 (yellow) background with white text"

Guardrail Check:
- Contrast ratio: 1.8:1
- Minimum required: 4.5:1
- Result: ❌ REJECT

Alternative:
- Use #F59E0B (darker yellow)
- Contrast ratio: 5.1:1
- Result: ✅ APPROVE
```

### Timing Change Request
```
User: "Make animation 150ms instead of 300ms"

Guardrail Check:
- Property: animation_duration
- Status: LOCKED
- Reason: "Optimized for perceived responsiveness"
- Result: ❌ REJECT

Explanation:
"Animation duration is locked at 300ms because it matches
human perception of 'responsive'. Faster feels janky,
slower feels sluggish. This value was tested extensively."
```

---

## Creating Guardrails for New Components

When adding a component:

### 1. Identify Locked Properties
Ask: "What creates the refined feel?"
- Timing and easing
- Physics constants
- Micro-interaction details

### 2. Define Customizable Constraints
Ask: "What's safe to customize with boundaries?"
- Colors (with contrast validation)
- Sizes (from predefined scale)
- Spacing (within range)

### 3. Set Quality Standards
- Accessibility requirements
- Performance targets
- Browser support

### 4. Define Agent Permissions
- What can Customization Guide recommend?
- What must Quality Guardian validate?
- What can't be changed?

### 5. Write Validation Rules
- Critical (auto-reject)
- High (warn)
- Medium (suggest fix)

### 6. Document Reasoning
**Most important**: Explain WHY properties are locked

**[Follow DOCUMENTATION-STRATEGY.md →](../.system/DOCUMENTATION-STRATEGY.md)**

---

## Quality Metrics

Guardrails enforce these standards:

| Metric | Target | Minimum |
|--------|--------|---------|
| **Quality Score** | 9.5/10 | 8.0/10 |
| **Contrast Ratio** | ≥7:1 (AAA) | ≥4.5:1 (AA) |
| **Frame Rate** | 60fps | 60fps |
| **Touch Target** | ≥48px | ≥44px |
| **Accessibility** | 100% | 100% |
| **Locked Properties** | 0 changes | 0 changes |

Components below minimum are rejected.

---

## Contributing Guardrails

Want to improve guardrail definitions?

**Consider**:
- Adding validation rules for edge cases
- Improving constraint definitions
- Better reasoning documentation
- More example valid/invalid values

**Process**:
1. Update JSON schema
2. Test with AI agents
3. Verify validation logic
4. Document changes

**[Read contribution guide →](../CONTRIBUTING.md)**

---

## Questions?

- **Component-specific**: See component guardrails (e.g., hero-button.json)
- **Agent usage**: See [agents](../agents/)
- **Philosophy**: See [PHILOSOPHY.md](../PHILOSOPHY.md)
- **Standards**: See [knowledge-base/accessibility.md](../knowledge-base/accessibility.md)
