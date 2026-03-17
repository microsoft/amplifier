---
description: "Generate multiple radically different interface designs using parallel agents, then compare. Based on 'Design It Twice' from A Philosophy of Software Design."
---

# /design-interface — Parallel Interface Design

Spawn 3+ parallel subagents, each with a different design constraint, to produce radically different interface designs for a module. Then compare and synthesize.

## Arguments

Parse `$ARGUMENTS` as the module/interface description. If empty, ask the user what they want to design.

## Step 1: Gather Requirements (inline)

Before spawning agents, understand:
- What problem does this module solve?
- Who are the callers? (other modules, external users, tests)
- What are the key operations?
- Any constraints? (performance, compatibility, existing patterns)
- What should be hidden inside vs exposed?

Ask ONE clarifying question if the description is ambiguous. If clear enough, proceed immediately.

## Step 2: Explore Existing Code (conditional)

If the target is an existing module, dispatch an agentic-search subagent (haiku, read-only, 8 turns) to understand current interfaces, callers, and patterns:

```
Task(subagent_type="general-purpose", model="haiku", max_turns=8, description="Scout existing interfaces for [module]", prompt="
  **READ-ONLY MODE: Use ONLY Read, Glob, Grep, LS, and search tools. Do NOT use Edit, Write, Bash, or any tool that modifies files.**

  Find the current interface for [module]. Return:
  1. Current public API (function signatures, class methods, exports)
  2. All callers (grep for imports/usages across the codebase)
  3. Pain points visible from usage patterns (verbose calls, repeated boilerplate, error-prone sequences)

  MAX 400 words.")
```

Skip this step for greenfield modules.

## Step 3: Generate Designs (3 parallel agents)

Dispatch 3 zen-architect subagents in parallel (sonnet, 15 turns each). All receive the same requirements but a DIFFERENT constraint:

**Agent A — Minimal:**
> "Design the smallest possible interface. Aim for 1-3 methods/functions max. Hide everything else. Optimize for the common case. If a caller needs something rare, they can work around it."

**Agent B — Flexible:**
> "Design for maximum flexibility and extensibility. Support diverse use cases. Think about what callers might need in 6 months. Composition over configuration."

**Agent C — Ergonomic:**
> "Design for the best developer experience. Optimize for readability, discoverability, and making the wrong thing hard to do. Pit-of-success design."

Each agent prompt includes the requirements from Step 1, any scout findings from Step 2, and must output:

1. **Interface signature** — types, methods, params (actual code)
2. **Usage example** — how callers actually use it (2-3 snippets)
3. **What this design hides** — internal complexity invisible to callers
4. **Trade-offs** — what you gain and what you sacrifice
5. **Where this shines vs struggles** — best-fit and worst-fit scenarios

Optional 4th agent — dispatch when the domain warrants a paradigm shift (user requests it, or the problem is clearly suited to functional/event-driven/declarative/builder style):

**Agent D — Paradigm Shift:**
> "Take inspiration from a completely different paradigm. If the others are OOP, go functional. If procedural, go declarative. Challenge the assumed shape of the solution."

## Step 4: Present Designs

Show each design sequentially. For each:
- Give it a short name (e.g., "Minimal API", "Flexible Builder", "Ergonomic DSL")
- Show the interface signature as a code block
- Show 2-3 usage examples
- State what complexity is hidden inside
- State the key trade-off in one sentence

## Step 5: Compare

After presenting all designs, compare in prose (not tables) on these dimensions:

- **Interface simplicity** — fewer methods, simpler params = easier to learn
- **Depth** — small interface hiding significant complexity = deep module (good per Ousterhout). Large interface with thin implementation = shallow module (avoid)
- **General-purpose vs specialized** — flexibility vs focus
- **Ease of correct use vs ease of misuse** — pit of success
- **Implementation efficiency** — does the interface shape allow efficient internals?

State a recommendation with reasoning. Highlight where designs diverge most — that's where the real decision lies.

## Step 6: Synthesize

Often the best design combines insights from multiple options. Ask:
- "Which design best fits your primary use case?"
- "Any elements from other designs worth incorporating?"

Produce the final synthesized interface with the same 5-point structure the agents used.

## Anti-Patterns

- Don't let agents produce similar designs — the constraints must force radical divergence
- Don't skip comparison — the value is in contrast, not in any single design
- Don't implement anything — this command is purely about interface shape
- Don't evaluate based on implementation effort — focus on caller experience
- Don't default to the "middle ground" — bold choices beat safe compromises

## When to Use

- Before implementing any new module with a public API
- When refactoring a module that feels awkward to use
- When developers disagree on interface design
- When an interface has grown unwieldy over time
- After `/brainstorm` identifies a module that needs careful design
