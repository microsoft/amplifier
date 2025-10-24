# .design Directory

**Design system protocols, validation frameworks, and active design work for Amplified Design**

---

## Two Types of Content

### 1. Protocols & Standards (Always Active)
Design system rules and agent validation frameworks:

- **`COMPONENT-CREATION-PROTOCOL.md`** - Component creation checklist
- **`PROACTIVE-DESIGN-PROTOCOL.md`** - Aesthetic-first approach
- **`DESIGN-SYSTEM-ENFORCEMENT.md`** - Token system rules (no hardcoding)
- **`AGENT-VALIDATION.md`** - How to verify agents work properly
- **`AGENT-TEST-SCENARIOS.md`** - Concrete test cases for agents
- **`test-agents.sh`** - Automated health check script

### 2. Design Work (State Prefixes)
Active design specs and documentation:

- **`ACTIVE-*`** - Currently being worked on
- **`DONE-*`** - Completed work, kept for reference
- **`TODO-*`** - Queued work, not yet started
- **`ARCHIVE-*`** - Historical work, no longer active

---

## Quick Start

### For Humans (Designers/Developers)
Read these to understand the design philosophy and protocols:
- **Start here:** `COMPONENT-CREATION-PROTOCOL.md`
- **Design thinking:** `PROACTIVE-DESIGN-PROTOCOL.md`
- **Token system:** `DESIGN-SYSTEM-ENFORCEMENT.md`

### For AI Agents
Use `/designer` command which references protocols and routes to:
- **System design:** `.claude/agents/design-system-architect.md`
- **Component design:** `.claude/agents/component-designer.md`
- **Motion design:** `.claude/agents/animation-choreographer.md`

### Testing & Validation
```bash
# Quick automated health check
./design/test-agents.sh

# Manual validation
npm run validate:tokens
npx tsc --noEmit
npm run build
```

For detailed testing: See `AGENT-VALIDATION.md` and `AGENT-TEST-SCENARIOS.md`

---

## How It All Fits Together

### The Philosophy (Root Directory)
```
FRAMEWORK.md      → Nine Dimensions + Four Layers methodology
PHILOSOPHY.md     → Five Pillars deep dive
PRINCIPLES.md     → Quick reference guide
VISION.md         → Beyond the artifact philosophy
CLAUDE.md         → Implementation standards for AI
```

### The Protocols (.design/)
```
COMPONENT-CREATION-PROTOCOL.md   → Implements FRAMEWORK + PHILOSOPHY
PROACTIVE-DESIGN-PROTOCOL.md     → Aesthetic-first workflow
DESIGN-SYSTEM-ENFORCEMENT.md     → Token enforcement rules
```

### The Agents (.claude/agents/)
```
design-system-architect.md   → Executes system-level protocols
component-designer.md        → Executes component protocols
animation-choreographer.md   → Executes motion protocols
```

### The Command (.claude/commands/)
```
designer.md   → Routes user requests to appropriate agent
```

### The Validation (.design/)
```
AGENT-VALIDATION.md      → Validation framework
AGENT-TEST-SCENARIOS.md  → Test cases
test-agents.sh           → Automated testing
```

---

## Common Workflows

### Create New Component
```bash
/designer component [description]
```
Agent executes `COMPONENT-CREATION-PROTOCOL.md` → validates all dimensions → outputs specification

### Add Design Tokens
```bash
/designer system [description]
```
Agent designs tokens for light AND dark modes → updates `globals.css` → validates

### Refine Aesthetics
```bash
/designer [refinement request]
```
Agent applies `PROACTIVE-DESIGN-PROTOCOL.md` → implements with polish built-in

### Validate Agent Health
```bash
./design/test-agents.sh
```
Runs automated health check → reports score and issues

---

## Key Principles

1. **Purpose-First** - Articulate WHY in one sentence before coding
2. **Nine Dimensions** - Evaluate Style, Motion, Voice, Space, Color, Typography, Proportion, Texture, Body
3. **Five Pillars** - Purpose, Craft, Constraints, Incompleteness, Humans
4. **9.5/10 Quality** - Refined and purposeful, not generic or over-engineered
5. **No Hardcoded Values** - Always use `var(--tokens)`, never `#FFFFFF` or `17px`
---

## Success Metrics

### Agent Health
- 95%+ protocol compliance
- Zero hardcoded values in production
- All validation scripts pass
- WCAG AA standards met
- Output quality consistently 9.5/10

### System Health
- Tokens cover all use cases
- Components follow patterns
- Light + dark modes work perfectly
- Developers confident without review
- Users accomplish tasks without friction

---

## File Organization

### Protocols (Always Active)
```
.design/
├── README.md (this file)
├── COMPONENT-CREATION-PROTOCOL.md
├── PROACTIVE-DESIGN-PROTOCOL.md
├── DESIGN-SYSTEM-ENFORCEMENT.md
├── AGENT-VALIDATION.md
├── AGENT-TEST-SCENARIOS.md
└── test-agents.sh
```

### Design Work (State Prefixed)
```
.design/
├── ACTIVE-*.md (work in progress)
├── DONE-*.md (completed work)
├── TODO-*.md (planned work)
└── ARCHIVE-*.md (historical reference)
```

### Quick Reference
```bash
# Find active work
ls .design/ACTIVE-*

# Find completed work
ls .design/DONE-*

# Find queued work
ls .design/TODO-*

# Run agent tests
./.design/test-agents.sh
```

---

## Troubleshooting

**Agent produces hardcoded values?**
→ Check `DESIGN-SYSTEM-ENFORCEMENT.md` in agent instructions

**Agent skips validation?**
→ Add validation step to agent workflow, verify TodoWrite access

**Agent ignores accessibility?**
→ Add accessibility checklist from `COMPONENT-CREATION-PROTOCOL.md`

**Output quality <9.5/10?**
→ Verify agent evaluates Nine Dimensions and Five Pillars

For detailed troubleshooting: See `AGENT-VALIDATION.md`

---

**Quality at creation beats debugging later.**

---

Last updated: 2025-01-19
