# Framework Agents

**Generic, aesthetic-agnostic agents for the Amplified Design framework**

---

## Overview

These agents provide intelligent guidance while remaining **aesthetic-agnostic**—they work with ANY project using the Amplified Design framework.

**How it works**: Share agent definition files with your AI assistant (Claude, ChatGPT, etc.) to get expert guidance that respects quality guardrails.

**Project-Specific Agents**: For customized agents that embed specific project aesthetics:
- **Studio-Interface**: `studio-interface/.claude/agents/` (Swedish + German dual aesthetic)
- **Amplifier**: `amplifier/.claude/agents/` (AI-amplified workflows)

---

## Framework Agents

### [Customization Guide](./customization-guide.md)
**Role**: Help users safely customize components

**Provides**:
- Variant recommendations based on use case
- Color suggestions with contrast validation
- Size and layout guidance
- Icon and content advice
- Context-appropriate customizations

**Example**:
```
User: "I need a button for my B2B SaaS checkout"

Agent: "For B2B checkout, I recommend:
- Variant: 'ripple' (tactile confirmation for high-stakes action)
- Size: 'md' (standard, not overwhelming)
- Color: Professional blue gradient (contrast validated at 6.2:1)
Here's the implementation..."
```

**[View full definition →](./customization-guide.md)**

---

### [Quality Guardian](./quality-guardian.md)
**Role**: Validate all changes maintain 9.5/10 quality

**Validates**:
- Color contrast (4.5:1 minimum, WCAG AA)
- Accessibility compliance (keyboard, screen reader, touch targets)
- Performance (60fps maintained)
- Locked properties unchanged
- Visual consistency

**Authority**: Has final approval, can reject changes

**Example**:
```
User: "Use light yellow background with white text"

Agent: "❌ Rejected
- Contrast ratio: 1.8:1 (below 4.5:1 minimum)
- WCAG AA: Failed

✅ Alternative: Darker yellow (#F59E0B) with white text
- Contrast ratio: 5.1:1 (WCAG AA compliant)
```

**[View full definition →](./quality-guardian.md)**

---

### [Orchestrator](./orchestrator.md)
**Role**: Coordinate multi-agent workflow

**Manages**:
- Request parsing and intent understanding
- Routing to appropriate agents
- Response synthesis
- Error handling
- Parallel processing when possible
- Multi-turn conversations

**Example workflow**:
```
User request → Parse intent →
    ↓
Route to Customization Guide (recommend) →
    ↓
Route to Quality Guardian (validate) →
    ↓
Synthesize final response → Return to user
```

**[View full definition →](./orchestrator.md)**

---

## Agent Workflow

### Simple Customization
```
User: "Make this button red"
    ↓
Orchestrator (routes to Customization Guide)
    ↓
Customization Guide (suggests validated red options)
    ↓
Quality Guardian (auto-validates contrast)
    ↓
Orchestrator (returns validated options)
```

### Complex Customization
```
User: "I need buttons for an e-commerce product page"
    ↓
Orchestrator (understands context: e-commerce)
    ↓
Customization Guide (recommends variants for different CTAs)
    ↓
Quality Guardian (validates all suggestions)
    ↓
Orchestrator (synthesizes complete solution)
```

---

## How to Use

### Step 1: Share Definitions
Provide your AI assistant with agent definition files:
- customization-guide.md
- quality-guardian.md
- orchestrator.md

### Step 2: Request Customization
Ask naturally:
- "I need a button for my SaaS landing page"
- "Make this match my brand (blue)"
- "What variant works for a form submit?"

### Step 3: Receive Guidance
Agents work together to:
1. Understand your context
2. Recommend appropriate options
3. Validate all suggestions
4. Provide implementation code

### Step 4: Implement
Use the validated, quality-assured component code.

---

## Integration with AI Assistants

### Compatible With
- **Claude** (Anthropic) - Excellent context handling
- **ChatGPT** (OpenAI) - Strong reasoning
- **Other AI assistants** - Any that can follow structured prompts

### How Agents Access Information
Agents reference:
- **Quality Guardrails**: JSON schemas defining constraints
- **Knowledge Base**: Design principles (color, animation, accessibility)
- **Component Docs**: Implementation details
- **Philosophy**: Quality standards and reasoning

---

## Agent Permissions

Defined in [quality-guardrails](../quality-guardrails/):

**Customization Guide** can:
- ✅ Recommend colors, sizes, variants
- ✅ Suggest content and icons
- ❌ Cannot modify locked properties
- ⚠️ Must validate with Quality Guardian

**Quality Guardian** can:
- ✅ Validate all changes
- ✅ Approve or reject
- ✅ Suggest alternatives
- ✅ Has final authority

**Orchestrator** can:
- ✅ Route requests
- ✅ Synthesize responses
- ❌ Cannot override Quality Guardian
- ⚠️ Must respect agent permissions

---

## Example Interactions

### Brand Color Customization
```
User: "Match my brand color #3B82F6"

Customization Guide:
"That blue works well! Contrast ratio: 6.8:1 with white text (WCAG AAA).
I recommend pairing with a darker shade for gradient depth:
linear-gradient(135deg, #3B82F6 0%, #1E40AF 100%)"

Quality Guardian:
"✅ Approved
- Contrast: 6.8:1 (WCAG AAA)
- Gradient maintains accessibility
- Touch targets adequate
- All checks passed"
```

### Use Case Recommendation
```
User: "What button for a gaming interface?"

Customization Guide:
"For gaming, I recommend 'neon-pulse' variant:
- Energetic, cyberpunk aesthetic
- Glowing animation matches gaming vibe
- Bold and attention-grabbing
Size: 'lg' for primary actions"

Quality Guardian:
"✅ Validated
- Neon glow maintains 4.9:1 contrast
- Animation respects reduced-motion
- Keyboard accessible"
```

---

## Contributing to Agents

Want to improve agent definitions?

**Consider adding**:
- More example scenarios
- Better decision trees
- Additional validation rules
- Refined recommendation logic

**Guidelines**:
1. Maintain agent role clarity
2. Add examples showing edge cases
3. Reference quality guardrails
4. Test with real AI assistants

**[Read contribution guide →](../CONTRIBUTING.md)**

---

## Creating Project-Specific Agents

Want to customize agents for your project? Follow this pattern:

### 1. Create Project Agent Directory
```bash
mkdir -p your-project/.claude/agents
```

### 2. Override Framework Agents
Copy framework agents as templates and customize:
```bash
cp agents/ux-wireframe-designer.md your-project/.claude/agents/
cp agents/requirements-architect.md your-project/.claude/agents/
```

### 3. Embed Your Aesthetic
Edit the copied agents to include your project's specific:
- Emotional tone and personality
- Color palettes and visual approach
- Interaction principles and timing
- Typography choices

### 4. Same Filename = Clear Override
Use the **same filename** as the framework agent to make the override relationship clear:
- Framework: `/agents/ux-wireframe-designer.md` (generic)
- Project: `your-project/.claude/agents/ux-wireframe-designer.md` (customized)

### Examples
- **Studio-Interface**: See `studio-interface/.claude/agents/` for dual aesthetic approach
- **Amplifier**: See `amplifier/.claude/agents/` for AI workflow customization

**Pattern**: Framework provides the base, projects customize via override with same filename.

---

## Questions?

- **Agent-specific**: Check individual agent definition files
- **Quality rules**: See [quality-guardrails](../quality-guardrails/)
- **Philosophy**: See [PHILOSOPHY.md](../PHILOSOPHY.md)
- **Implementation**: See [components](../components/)
- **Project agents**: See `studio-interface/.claude/agents/README.md` for customization examples
