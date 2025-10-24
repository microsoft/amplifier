# Studio-Interface Agents

These agents are **customized specifically for the Studio-Interface project** and embed Studio's dual aesthetic approach.

## Studio's Dual Aesthetic

Studio-Interface uses two distinct aesthetics for different contexts:

### Homepage/Marketing
**Swedish Design Studio aesthetic** - Playful, creative, inviting
- Goal: "Come in and explore!"
- Characteristics: Warm colors, playful interactions, inviting curiosity

### Workspace/Canvas
**German Car Facility aesthetic** - Clean, focused, precise
- Goal: "Here's your focused space to create"
- Characteristics: Restrained, purposeful, quality through subtle refinement

This dual approach demonstrates **"context shapes expression"** (Layer 4 of the Nine Dimensions framework).

---

## Agents in This Directory

### ux-wireframe-designer.md
Studio-specific UX design agent that understands and applies Studio's dual aesthetic based on context. Overrides the framework's generic `ux-wireframe-designer.md` with Studio-specific guidance.

### requirements-architect.md
Studio-specific requirements agent that frames requirements with Studio's aesthetic context in mind. Overrides the framework's generic `requirements-architect.md`.

---

## How This Works

**Agent Override Pattern:**

1. **Framework provides base agents** → `/agents/ux-wireframe-designer.md` (generic, aesthetic-agnostic)
2. **Project customizes via override** → `studio-interface/.claude/agents/ux-wireframe-designer.md` (Studio-specific)
3. **Same filename = clear relationship** - The project version extends/overrides the framework version

When working in Studio-Interface, Claude Code will discover and use these Studio-specific agents that understand the dual aesthetic approach.

---

## For Other Projects

If you're creating a new project using Amplified Design:

1. Create `your-project/.claude/agents/`
2. Copy framework agents from `/agents/` as starting templates
3. Customize with your project's aesthetic
4. Same filename = override relationship is clear

**Example:**
```
/agents/
└── ux-wireframe-designer.md          ← Framework generic

/healthcare-app/.claude/agents/
└── ux-wireframe-designer.md          ← Healthcare-specific

/fintech-app/.claude/agents/
└── ux-wireframe-designer.md          ← Fintech-specific
```

---

## Philosophy

This structure follows Amplified Design's core principles:

- **Ruthless Simplicity**: Clear rule: Framework → `/agents/`, Project → `project/.claude/agents/`
- **Modular Design**: Framework provides base, projects customize via override
- **Bricks & Studs**: Same filename = clear contract between framework and project

---

**Remember:** These agents are Studio-specific. They're not prescriptions for all projects—they're examples of how to customize the framework for your project's needs.
