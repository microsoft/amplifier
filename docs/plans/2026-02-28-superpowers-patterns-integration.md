# Superpowers Patterns Integration — Implementation Plan

> **For Claude:** REQUIRED: Use /subagent-dev to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Incorporate 7 proven patterns from obra/superpowers v4.3.1 into Amplifier's existing skills and agents to strengthen workflow discipline without breaking current functionality.

**Architecture:** Additive changes only. New hook for EnterPlanMode intercept, new sections appended to AGENTS.md, branch gate checks prepended to 4 commands, DOT graphs added to 4 commands, 2 new review agents created, CSO-optimized descriptions for all 34 agents.

**Tech Stack:** Bash (hooks), Markdown (commands/agents), JSON (settings)

---

## Task 1: Pattern 3 — Red Flags Table

**Agent:** modular-builder
**Files:** `AGENTS.md`

### Steps

- [ ] Read `AGENTS.md` to confirm current line count and final section (ends at line 558 with "Modular Design Philosophy" section).
- [ ] Append the following Red Flags section to `AGENTS.md` after line 558 (do NOT modify any existing content):

```markdown

## Red Flags

If you catch yourself thinking any of the following, stop and apply the reality check before proceeding.

| If you're thinking... | Reality check |
|-----------------------|---------------|
| "This is simple, I'll just implement it directly" | Run /brainstorm first. Simplicity is confirmed after analysis, not assumed before it. |
| "I already know the codebase well enough" | Dispatch agentic-search anyway. Memory of past sessions is lossy. |
| "I'll write tests after the implementation" | /tdd exists for a reason. Tests first is not optional for non-trivial features. |
| "I'll skip the worktree, it's a small change" | Branch first always. Main is protected; there is no "small enough to skip". |
| "I can review my own code" | Two-stage review catches category errors that self-review misses. |
| "The user seems in a hurry, I'll skip brainstorming" | Rushing causes design mistakes that cost 10x the time saved. |
| "This refactor is obvious, no plan needed" | /create-plan takes 2 minutes. The blast radius of "obvious" refactors is routinely underestimated. |
| "I'll just fix this one file" | Check blast radius with grep first. Changes propagate in ways that are not always visible from one file. |
| "I tested it mentally, it should work" | /verify requires evidence, not claims. Mental testing has a well-documented failure rate. |
| "I'll clean up later" | Run /post-task-cleanup now. "Later" accumulates and becomes never. |
```

- [ ] Verify: `AGENTS.md` contains `## Red Flags` section with exactly 10 table rows.
- [ ] Verify: All existing AGENTS.md content above line 558 is unchanged.
- [ ] Commit:
  ```bash
  git add AGENTS.md
  git commit -m "feat: add Red Flags rationalization table to AGENTS.md (Pattern 3)

  Appends 10-row self-check table that catches common rationalization
  patterns leading to skipped workflow steps. Pure documentation append;
  no existing content modified.

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

## Task 2: Pattern 5 — Branch Gates

**Agent:** modular-builder
**Files:** `.claude/commands/execute-plan.md`, `.claude/commands/modular-build.md`, `.claude/commands/parallel-agents.md`, `.claude/commands/subagent-dev.md`

### Steps

- [ ] Read all 4 command files to understand their current opening sections.
- [ ] Add the following branch gate block to the **very start** of `execute-plan.md`, before any other command logic (immediately after the frontmatter `---` block if present, otherwise as the first section):

```markdown
## Branch Gate (REQUIRED)

Before doing ANY work, check the current branch and refuse to proceed if on main or master:

```bash
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null)
if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
  echo "ERROR: Cannot run /execute-plan on branch '$CURRENT_BRANCH'."
  echo "Create a feature branch first:"
  echo "  Option 1: /worktree  (recommended — isolated environment)"
  echo "  Option 2: git checkout -b feature/<name>"
  exit 1
fi
```

**If on main/master:** STOP. Do not execute any plan steps. Tell the user to create a feature branch first, then re-run this command.

**If on a feature branch:** Proceed.
```

- [ ] Add the same branch gate block to the **very start** of `modular-build.md` (adjust error message to `/modular-build`).
- [ ] Add the same branch gate block to the **very start** of `parallel-agents.md` (adjust error message to `/parallel-agents`).
- [ ] Read `subagent-dev.md` lines 97–116 (existing gate). The current gate prints "ON_MAIN" and offers to create a branch but does not actually halt execution. Strengthen it by replacing the existing gate block with a **hard block** that STOPs unconditionally:

  Replace the current gate section (lines 97–116) with:

  ```markdown
  ## Branch Gate (REQUIRED)

  Before doing ANY work, check the current branch and REFUSE if on main or master:

  ```bash
  CURRENT_BRANCH=$(git branch --show-current 2>/dev/null)
  if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
    echo "ERROR: Cannot run /subagent-dev on branch '$CURRENT_BRANCH'."
    echo "Create a feature branch first:"
    echo "  Option 1: /worktree  (recommended — isolated environment)"
    echo "  Option 2: git checkout -b feature/<name>"
    exit 1
  fi
  ```

  **HARD BLOCK:** If on main/master, STOP immediately. Do NOT dispatch any agents. Do NOT offer to continue. Tell the user: "Cannot run /subagent-dev on main. Create a feature branch first, then re-run." Offer the two branch creation options above and wait for the user to switch branches before proceeding.

  **If on a feature branch:** Proceed to The Process.
  ```

- [ ] Verify: All 4 command files contain the branch gate block.
- [ ] Verify: `subagent-dev.md` gate is now a hard block (not just a warning).
- [ ] Commit:
  ```bash
  git add .claude/commands/execute-plan.md .claude/commands/modular-build.md .claude/commands/parallel-agents.md .claude/commands/subagent-dev.md
  git commit -m "feat: add mandatory branch gates to 4 implementation commands (Pattern 5)

  Adds hard branch gate to execute-plan, modular-build, parallel-agents.
  Strengthens existing soft gate in subagent-dev to unconditional hard block.
  All 4 commands now refuse to proceed when on main/master.

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

## Task 3: Pattern 1 — EnterPlanMode Hook

**Agent:** modular-builder
**Files:** `.claude/tools/enforce-brainstorm.sh`, `.claude/settings.json`

### Steps

- [ ] Read `.claude/settings.json` to understand existing hook registrations before modifying. Current structure: `hooks.PreToolUse` has one entry (matcher: "Task", command: `uv run .claude/tools/subagent-logger.py`).
- [ ] Create `.claude/tools/enforce-brainstorm.sh` with the following content:

```bash
#!/usr/bin/env bash
# enforce-brainstorm.sh — PreToolUse hook for EnterPlanMode
# Blocks Plan Mode entry unless /brainstorm or /create-plan has been completed
# in this session (indicated by marker file /tmp/amplifier-brainstorm-done).

MARKER="/tmp/amplifier-brainstorm-done"

if [ ! -f "$MARKER" ]; then
  echo "Brainstorm required before entering Plan Mode." >&2
  echo "Run /brainstorm to validate the design, then try again." >&2
  echo "The marker file /tmp/amplifier-brainstorm-done will be set automatically." >&2
  exit 2
fi

exit 0
```

- [ ] Make the script executable:
  ```bash
  chmod +x .claude/tools/enforce-brainstorm.sh
  ```
- [ ] Add the EnterPlanMode hook to `.claude/settings.json`. The `hooks.PreToolUse` array currently has one entry. Add a second entry for EnterPlanMode. The updated `hooks.PreToolUse` section should be:

  ```json
  "PreToolUse": [
    {
      "matcher": "Task",
      "hooks": [
        {
          "type": "command",
          "command": "uv run .claude/tools/subagent-logger.py"
        }
      ]
    },
    {
      "matcher": "EnterPlanMode",
      "hooks": [
        {
          "type": "command",
          "command": "bash .claude/tools/enforce-brainstorm.sh"
        }
      ]
    }
  ]
  ```

  IMPORTANT: Merge this into the existing `settings.json` carefully — preserve all other hook sections (SessionStart, Stop, SubagentStop, PostToolUse, Notification, PreCompact) exactly as they are. Only add the new EnterPlanMode entry to the PreToolUse array.

- [ ] Verify: `.claude/tools/enforce-brainstorm.sh` exists and is executable.
- [ ] Verify: `.claude/settings.json` has the EnterPlanMode entry in PreToolUse.
- [ ] Verify: All other hooks in `settings.json` are unchanged.
- [ ] Commit:
  ```bash
  git add .claude/tools/enforce-brainstorm.sh .claude/settings.json
  git commit -m "feat: add EnterPlanMode brainstorm gate hook (Pattern 1)

  Creates enforce-brainstorm.sh hook that blocks Plan Mode entry unless
  /brainstorm or /create-plan has written the session marker file at
  /tmp/amplifier-brainstorm-done. Registers hook as PreToolUse on
  EnterPlanMode matcher in settings.json.

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

## Task 4: Pattern 1 continued — Marker File in Commands

**Agent:** modular-builder
**Files:** `.claude/commands/brainstorm.md`, `.claude/commands/create-plan.md`

### Steps

- [ ] Read `brainstorm.md` fully to locate the "After the Design" section (or equivalent section that describes what happens after the user validates the design).
- [ ] In `brainstorm.md`, at the end of the section that describes post-design actions (the section where the command routes to execution after user confirmation), add the following instruction block:

  ```markdown
  ### Write Brainstorm Marker

  After the user confirms the design is ready to proceed, write the brainstorm marker file to unlock Plan Mode:

  ```bash
  touch /tmp/amplifier-brainstorm-done
  ```

  This marker file enables EnterPlanMode for this terminal session. It is session-scoped: a new terminal session will require a new /brainstorm run.
  ```

- [ ] Read `create-plan.md` fully to locate the "Execution Handoff" section (lines 254–273 based on prior research). The section ends with `$ARGUMENTS`.
- [ ] In `create-plan.md`, at the end of the "Execution Handoff" section, immediately before `$ARGUMENTS`, add the following instruction block:

  ```markdown
  ### Write Brainstorm Marker

  After saving the plan and before handing off to execution, write the brainstorm marker file to unlock Plan Mode:

  ```bash
  touch /tmp/amplifier-brainstorm-done
  ```

  This covers the case where the user starts with /create-plan directly (skipping /brainstorm). The marker file is session-scoped.
  ```

- [ ] Verify: `brainstorm.md` contains `touch /tmp/amplifier-brainstorm-done`.
- [ ] Verify: `create-plan.md` contains `touch /tmp/amplifier-brainstorm-done`.
- [ ] Commit:
  ```bash
  git add .claude/commands/brainstorm.md .claude/commands/create-plan.md
  git commit -m "feat: add brainstorm marker write to brainstorm and create-plan (Pattern 1)

  Both commands now write /tmp/amplifier-brainstorm-done after design
  validation/plan completion, enabling EnterPlanMode for the session.
  Covers both entry points into the planning workflow.

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

## Task 5: Pattern 7 — CSO Descriptions (Agents 1–17)

**Agent:** modular-builder
**Files:** `.claude/agents/agentic-search.md`, `.claude/agents/ambiguity-guardian.md`, `.claude/agents/amplifier-cli-architect.md`, `.claude/agents/amplifier-expert.md`, `.claude/agents/analysis-engine.md`, `.claude/agents/animation-choreographer.md`, `.claude/agents/api-contract-designer.md`, `.claude/agents/art-director.md`, `.claude/agents/bug-hunter.md`, `.claude/agents/component-designer.md`, `.claude/agents/concept-extractor.md`, `.claude/agents/content-researcher.md`, `.claude/agents/contract-spec-author.md`, `.claude/agents/database-architect.md`, `.claude/agents/design-system-architect.md`, `.claude/agents/graph-builder.md`, `.claude/agents/handoff-gemini.md`

### Steps

- [ ] Read each of the 17 agent files to get the current `description` field value. Do this in parallel (read all 17 in a single message with multiple Read tool calls).
- [ ] Rewrite ONLY the `description` field in the YAML frontmatter of each agent file. Rules:
  - Start with a primary action verb
  - Include 5–10 comma-separated action phrases
  - Include symptom keywords that trigger natural agent selection
  - Remove "specialized", "expert", "designed to", "that", "which", "powerful"
  - Keep all other fields (name, model, isolation, tools, the agent prompt body) completely unchanged
  - Keep the "Deploy for:" bullet list in the description if present; only change the opening narrative lines

- [ ] Apply these rewrites (read each file first to confirm current wording, then apply):

  **`agentic-search.md`**
  ```yaml
  description: Search codebases, find files, locate symbols, trace dependencies, explore unfamiliar code, investigate where functionality lives, understand module boundaries, discover patterns across a repository
  ```

  **`ambiguity-guardian.md`**
  ```yaml
  description: Preserve contradictions, flag ambiguous requirements, surface hidden assumptions, prevent premature closure, challenge oversimplified designs, identify conflicting constraints, protect productive uncertainty
  ```

  **`amplifier-cli-architect.md`**
  ```yaml
  description: Design CLI tools, architect hybrid code-AI workflows, structure amplifier scenarios, define command interfaces, create tool templates, guide progressive maturity from scripts to agents
  ```

  **`amplifier-expert.md`**
  ```yaml
  description: Answer Amplifier questions, explain agent selection, troubleshoot command failures, guide workflow adoption, resolve confusion about skills and agents, advise on Amplifier best practices
  ```

  **`analysis-engine.md`**
  ```yaml
  description: Analyze systems, audit codebases, assess technical debt, measure complexity, triage issues, synthesize findings, produce structured reports, evaluate architecture trade-offs
  ```

  **`animation-choreographer.md`**
  ```yaml
  description: Design animations, choreograph transitions, specify motion curves, create easing sequences, define micro-interactions, implement CSS/JS animation patterns, coordinate multi-element motion
  ```

  **`api-contract-designer.md`**
  ```yaml
  description: Design REST APIs, define GraphQL schemas, write OpenAPI specs, specify request/response contracts, design endpoint hierarchies, document error codes, version API surfaces
  ```

  **`art-director.md`**
  ```yaml
  description: Direct visual aesthetics, define brand identity, set color palettes, establish typographic hierarchy, create mood boards, evaluate visual consistency, guide design decisions
  ```

  **`bug-hunter.md`**
  ```yaml
  description: Debug errors, fix bugs, investigate failures, troubleshoot crashes, diagnose test failures, trace root causes, resolve exceptions, reproduce intermittent issues, identify regression sources
  ```

  **`component-designer.md`**
  ```yaml
  description: Design UI components, implement frontend widgets, create React/Vue/Svelte components, define component APIs, write component documentation, build interactive UI elements
  ```

  **`concept-extractor.md`**
  ```yaml
  description: Extract key concepts, distill articles into atomic ideas, summarize papers, identify core insights, produce concept maps, strip noise from content, surface actionable takeaways
  ```

  **`content-researcher.md`**
  ```yaml
  description: Research topics, investigate content collections, compare sources, evaluate evidence, extract actionable insights, compile research summaries, assess source credibility
  ```

  **`contract-spec-author.md`**
  ```yaml
  description: Write formal specifications, author interface contracts, document protocols, define acceptance criteria, create implementation specs, produce structured requirement documents
  ```

  **`database-architect.md`**
  ```yaml
  description: Design database schemas, write migrations, optimize queries, define indexes, model entity relationships, plan data partitioning, review ORM patterns, resolve N+1 problems
  ```

  **`design-system-architect.md`**
  ```yaml
  description: Build design systems, define design tokens, architect theme infrastructure, create component libraries, establish visual foundations, document design patterns, enforce consistency
  ```

  **`graph-builder.md`**
  ```yaml
  description: Build knowledge graphs, map entity relationships, construct multi-perspective networks, visualize concept connections, model dependency graphs, produce structured graph outputs
  ```

  **`handoff-gemini.md`**
  ```yaml
  description: Prepare Gemini handoffs, write HANDOFF.md task dispatches, format task specs for OpenCode, coordinate cross-model work, track handoff state, review Gemini PRs for integration
  ```

- [ ] Verify: All 17 files have updated `description` fields.
- [ ] Verify: No description contains "specialized", "expert", "designed to", or "that" as narrative phrases.
- [ ] Verify: Every description starts with an action verb.
- [ ] Verify: All other frontmatter fields and agent prompt bodies are unchanged.
- [ ] Commit:
  ```bash
  git add .claude/agents/agentic-search.md .claude/agents/ambiguity-guardian.md .claude/agents/amplifier-cli-architect.md .claude/agents/amplifier-expert.md .claude/agents/analysis-engine.md .claude/agents/animation-choreographer.md .claude/agents/api-contract-designer.md .claude/agents/art-director.md .claude/agents/bug-hunter.md .claude/agents/component-designer.md .claude/agents/concept-extractor.md .claude/agents/content-researcher.md .claude/agents/contract-spec-author.md .claude/agents/database-architect.md .claude/agents/design-system-architect.md .claude/agents/graph-builder.md .claude/agents/handoff-gemini.md
  git commit -m "feat: CSO-optimize agent descriptions for agents 1-17 (Pattern 7)

  Rewrites description fields in 17 agent files to use action-verb-first,
  keyword-dense format for improved Claude Subagent Orchestration (CSO).
  Removes narrative prose; no agent prompts or other fields changed.

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

## Task 6: Pattern 7 — CSO Descriptions (Agents 18–34)

**Agent:** modular-builder
**Files:** `.claude/agents/insight-synthesizer.md`, `.claude/agents/integration-specialist.md`, `.claude/agents/knowledge-archaeologist.md`, `.claude/agents/layout-architect.md`, `.claude/agents/modular-builder.md`, `.claude/agents/module-intent-architect.md`, `.claude/agents/pattern-emergence.md`, `.claude/agents/performance-optimizer.md`, `.claude/agents/post-task-cleanup.md`, `.claude/agents/responsive-strategist.md`, `.claude/agents/security-guardian.md`, `.claude/agents/subagent-architect.md`, `.claude/agents/test-coverage.md`, `.claude/agents/visualization-architect.md`, `.claude/agents/vmware-infrastructure.md`, `.claude/agents/voice-strategist.md`, `.claude/agents/zen-architect.md`

### Steps

- [ ] Read each of the 17 agent files to get the current `description` field value. Do this in parallel (read all 17 in a single message with multiple Read tool calls).
- [ ] Rewrite ONLY the `description` field using the same rules as Task 5.
- [ ] Apply these rewrites:

  **`insight-synthesizer.md`**
  ```yaml
  description: Synthesize cross-domain insights, identify meta-patterns, combine findings from multiple sources, surface non-obvious connections, produce synthesis reports, distill complex inputs into coherent conclusions
  ```

  **`integration-specialist.md`**
  ```yaml
  description: Integrate external services, wire APIs, connect MCP servers, resolve dependency conflicts, debug integration failures, assess third-party library health, document integration patterns
  ```

  **`knowledge-archaeologist.md`**
  ```yaml
  description: Trace knowledge evolution, recover abandoned approaches, investigate legacy decisions, find original intent in old code, excavate architectural history, document why things changed
  ```

  **`layout-architect.md`**
  ```yaml
  description: Design page layouts, define information architecture, plan grid systems, structure navigation hierarchies, create wireframes, specify spatial relationships, architect content flow
  ```

  **`modular-builder.md`**
  ```yaml
  description: Implement features, build modules, write code from specifications, create files, edit existing code, execute implementation tasks, produce working software from plans
  ```

  **`module-intent-architect.md`**
  ```yaml
  description: Translate requirements into module specifications, define module boundaries, clarify natural language into technical interfaces, produce implementation-ready module intent documents
  ```

  **`pattern-emergence.md`**
  ```yaml
  description: Detect emergent patterns, identify recurring structures, surface trends across diverse inputs, recognize structural regularities, map pattern evolution, synthesize multi-perspective pattern reports
  ```

  **`performance-optimizer.md`**
  ```yaml
  description: Optimize performance, profile bottlenecks, measure latency, reduce memory usage, improve query efficiency, benchmark changes, identify slow paths, resolve throughput issues
  ```

  **`post-task-cleanup.md`**
  ```yaml
  description: Clean up after tasks, remove dead code, fix lint errors, delete unused imports, organize files, run hygiene checks, restore codebase tidiness after implementation work
  ```

  **`responsive-strategist.md`**
  ```yaml
  description: Design responsive layouts, define breakpoints, adapt UI for mobile/tablet/desktop, plan viewport strategies, implement fluid grids, test cross-device behavior, resolve layout breakage
  ```

  **`security-guardian.md`**
  ```yaml
  description: Review security, audit authentication flows, identify OWASP vulnerabilities, assess secrets exposure, evaluate authorization logic, find injection risks, assess cryptographic practices
  ```

  **`subagent-architect.md`**
  ```yaml
  description: Create new agents, design agent prompts, define agent roles, write YAML frontmatter, structure agent capabilities, advise on agent specialization, review agent effectiveness
  ```

  **`test-coverage.md`**
  ```yaml
  description: Analyze test coverage, identify gaps, design test cases, review spec compliance, verify implementation against requirements, write missing tests, assess edge case handling
  ```

  **`visualization-architect.md`**
  ```yaml
  description: Design data visualizations, create charts and diagrams, plan knowledge graph layouts, specify rendering approaches, produce structured visualization outputs, select appropriate chart types
  ```

  **`vmware-infrastructure.md`**
  ```yaml
  description: Diagnose VMware issues, analyze ESXi/VCSA/NSX logs, generate PowerCLI commands, troubleshoot vmkernel errors, investigate vSphere failures, produce infrastructure remediation steps
  ```

  **`voice-strategist.md`**
  ```yaml
  description: Write UX copy, craft microcopy, define voice and tone, improve error messages, edit interface text, establish content style guides, review copy for clarity and consistency
  ```

  **`zen-architect.md`**
  ```yaml
  description: Review architecture, analyze system design, evaluate trade-offs, simplify overly complex approaches, identify over-engineering, recommend structural improvements, conduct code reviews
  ```

- [ ] Verify: All 17 files have updated `description` fields.
- [ ] Verify: No description contains "specialized", "expert", "designed to", or "that" as narrative phrases.
- [ ] Verify: Every description starts with an action verb.
- [ ] Commit:
  ```bash
  git add .claude/agents/insight-synthesizer.md .claude/agents/integration-specialist.md .claude/agents/knowledge-archaeologist.md .claude/agents/layout-architect.md .claude/agents/modular-builder.md .claude/agents/module-intent-architect.md .claude/agents/pattern-emergence.md .claude/agents/performance-optimizer.md .claude/agents/post-task-cleanup.md .claude/agents/responsive-strategist.md .claude/agents/security-guardian.md .claude/agents/subagent-architect.md .claude/agents/test-coverage.md .claude/agents/visualization-architect.md .claude/agents/vmware-infrastructure.md .claude/agents/voice-strategist.md .claude/agents/zen-architect.md
  git commit -m "feat: CSO-optimize agent descriptions for agents 18-34 (Pattern 7)

  Rewrites description fields in 17 agent files to use action-verb-first,
  keyword-dense format for improved Claude Subagent Orchestration (CSO).
  Removes narrative prose; no agent prompts or other fields changed.

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

## Task 7: Pattern 7 — Update AGENTS_CATALOG.md

**Agent:** modular-builder
**Files:** `.claude/AGENTS_CATALOG.md`

### Steps

- [ ] Read `.claude/AGENTS_CATALOG.md` to understand the current table structure and all 34 agent entries.
- [ ] Update the "Purpose" column for all 34 agents in the catalog to match the CSO-optimized descriptions from Tasks 5 and 6. Keep the table structure, section headers, and "Dispatch Keywords" column completely unchanged. Only update the Purpose column values.
- [ ] Updated Purpose values (abbreviated for catalog — keep under ~100 chars, preserve the essence of the CSO description):

  | Agent | Updated Purpose |
  |-------|----------------|
  | `agentic-search` | Search codebases, find files, locate symbols, trace dependencies, explore unfamiliar code |
  | `zen-architect` | Review architecture, evaluate trade-offs, simplify complexity, conduct code reviews |
  | `modular-builder` | Implement features, build modules, write code from specifications, execute implementation tasks |
  | `bug-hunter` | Debug errors, fix bugs, investigate failures, troubleshoot crashes, trace root causes |
  | `test-coverage` | Analyze test coverage, identify gaps, review spec compliance, verify implementations |
  | `security-guardian` | Review security, audit auth flows, identify OWASP vulnerabilities, assess secrets exposure |
  | `post-task-cleanup` | Clean up after tasks, remove dead code, fix lint errors, restore codebase tidiness |
  | `performance-optimizer` | Optimize performance, profile bottlenecks, measure latency, resolve throughput issues |
  | `integration-specialist` | Integrate external services, wire APIs, connect MCP servers, debug integration failures |
  | `api-contract-designer` | Design REST APIs, define GraphQL schemas, write OpenAPI specs, specify contracts |
  | `database-architect` | Design schemas, write migrations, optimize queries, define indexes, resolve N+1 problems |
  | `contract-spec-author` | Write formal specifications, author interface contracts, define acceptance criteria |
  | `module-intent-architect` | Translate requirements into module specs, define module boundaries, clarify interfaces |
  | `component-designer` | Design UI components, implement frontend widgets, create React/Vue/Svelte components |
  | `art-director` | Direct visual aesthetics, define brand identity, set color palettes, evaluate consistency |
  | `animation-choreographer` | Design animations, choreograph transitions, specify motion curves, create micro-interactions |
  | `layout-architect` | Design page layouts, define information architecture, plan grid systems |
  | `responsive-strategist` | Design responsive layouts, define breakpoints, adapt UI for mobile/tablet/desktop |
  | `design-system-architect` | Build design systems, define design tokens, architect theme infrastructure |
  | `voice-strategist` | Write UX copy, craft microcopy, define voice and tone, improve error messages |
  | `content-researcher` | Research topics, investigate content, compare sources, extract actionable insights |
  | `analysis-engine` | Analyze systems, audit codebases, assess technical debt, produce structured reports |
  | `concept-extractor` | Extract key concepts, distill articles, summarize papers, surface actionable takeaways |
  | `insight-synthesizer` | Synthesize cross-domain insights, identify meta-patterns, combine findings from multiple sources |
  | `knowledge-archaeologist` | Trace knowledge evolution, recover abandoned approaches, investigate legacy decisions |
  | `pattern-emergence` | Detect emergent patterns, identify recurring structures, surface trends across diverse inputs |
  | `visualization-architect` | Design data visualizations, create charts and diagrams, specify rendering approaches |
  | `graph-builder` | Build knowledge graphs, map entity relationships, construct multi-perspective networks |
  | `vmware-infrastructure` | Diagnose VMware issues, analyze ESXi/VCSA/NSX logs, generate PowerCLI commands |
  | `subagent-architect` | Create new agents, design agent prompts, define agent roles, review agent effectiveness |
  | `amplifier-cli-architect` | Design CLI tools, architect hybrid code-AI workflows, structure amplifier scenarios |
  | `ambiguity-guardian` | Preserve contradictions, flag ambiguous requirements, surface hidden assumptions |
  | `amplifier-expert` | Answer Amplifier questions, explain agent selection, troubleshoot command failures |
  | `handoff-gemini` | Prepare Gemini handoffs, write HANDOFF.md dispatches, coordinate cross-model work |

- [ ] Verify: All 34 agents in the catalog have updated Purpose values.
- [ ] Verify: Table structure, section headers, and Dispatch Keywords column are unchanged.
- [ ] Commit:
  ```bash
  git add .claude/AGENTS_CATALOG.md
  git commit -m "feat: update AGENTS_CATALOG.md to match CSO-optimized descriptions (Pattern 7)

  Syncs the Purpose column for all 34 agents to match the CSO-optimized
  descriptions written to the individual agent files in the previous tasks.

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

## Task 8: Pattern 2 — DOT Flowcharts

**Agent:** modular-builder
**Files:** `.claude/commands/brainstorm.md`, `.claude/commands/fix-bugs.md`, `.claude/commands/subagent-dev.md`, `.claude/commands/execute-plan.md`

### Steps

- [ ] Read each of the 4 command files to understand their current structure and choose the best insertion point for each graph section.
- [ ] Note: `subagent-dev.md` already has a process graph section at lines 120–168. Read it to understand the current graph before enhancing it.
- [ ] Add the following `## Process Graph (Authoritative)` section to `brainstorm.md` (insert after the "Session Start" or early overview section, before the detailed step instructions):

  ````markdown
  ## Process Graph (Authoritative)

  > When this graph conflicts with prose, follow the graph.

  ```dot
  digraph brainstorm {
    rankdir=TB;

    "gather_context" [label="Gather Context\n(dispatch scout subagent)" shape=box];
    "ask_questions" [label="Ask clarifying questions\n(one at a time)" shape=box];
    "propose_approaches" [label="Propose 2-3 approaches" shape=box];
    "present_design" [label="Present design in sections\n(200-300 words each)" shape=box];
    "validate" [label="User validates design?" shape=diamond];
    "revise" [label="Revise based on feedback" shape=box];
    "write_spec" [label="Write spec to docs/specs/" shape=box];
    "write_marker" [label="touch /tmp/amplifier-brainstorm-done" shape=box style=filled fillcolor=lightyellow];
    "route" [label="Route to execution?" shape=diamond];
    "simple" [label="Simple (1-2 tasks)\nUse /execute-plan directly" shape=box style=filled fillcolor=lightgreen];
    "medium" [label="Medium (3-8 tasks)\nUse /create-plan then /subagent-dev" shape=box style=filled fillcolor=lightgreen];
    "complex" [label="Complex (9+ tasks)\nUse /create-plan with parallel batches" shape=box style=filled fillcolor=lightgreen];

    "gather_context" -> "ask_questions";
    "ask_questions" -> "propose_approaches";
    "propose_approaches" -> "present_design";
    "present_design" -> "validate";
    "validate" -> "revise" [label="needs changes"];
    "revise" -> "present_design";
    "validate" -> "write_spec" [label="approved"];
    "write_spec" -> "write_marker";
    "write_marker" -> "route";
    "route" -> "simple" [label="simple"];
    "route" -> "medium" [label="medium"];
    "route" -> "complex" [label="complex"];
  }
  ```
  ````

- [ ] Add the following `## Process Graph (Authoritative)` section to `fix-bugs.md` (insert after any overview section, before detailed phase descriptions):

  ````markdown
  ## Process Graph (Authoritative)

  > When this graph conflicts with prose, follow the graph.

  ```dot
  digraph fix_bugs {
    rankdir=TB;

    "fetch_bugs" [label="Fetch bugs from issue tracker\nor accept from user" shape=box];
    "select" [label="Select bug to investigate" shape=box];
    "investigate" [label="Investigate\n(read logs, code, stack traces)" shape=box];
    "visual_check" [label="Visual check needed?" shape=diamond];
    "playwright" [label="Playwright MCP\nscreenshot / interact" shape=box];
    "analyze" [label="Form hypothesis\nidentify root cause" shape=box];
    "fix" [label="Implement fix\n(on feature branch)" shape=box];
    "build_test" [label="Build + run tests" shape=box];
    "tests_pass" [label="Tests pass?" shape=diamond];
    "iterate" [label="Iterate on fix" shape=box];
    "deploy" [label="Deploy to test environment" shape=box];
    "verify" [label="Verify fix in environment" shape=box];
    "more_bugs" [label="More bugs?" shape=diamond];
    "done" [label="Create PR\n/finish-branch" shape=box style=filled fillcolor=lightgreen];

    "fetch_bugs" -> "select";
    "select" -> "investigate";
    "investigate" -> "visual_check";
    "visual_check" -> "playwright" [label="yes"];
    "playwright" -> "analyze";
    "visual_check" -> "analyze" [label="no"];
    "analyze" -> "fix";
    "fix" -> "build_test";
    "build_test" -> "tests_pass";
    "tests_pass" -> "iterate" [label="no"];
    "iterate" -> "fix";
    "tests_pass" -> "deploy" [label="yes"];
    "deploy" -> "verify";
    "verify" -> "more_bugs";
    "more_bugs" -> "select" [label="yes"];
    "more_bugs" -> "done" [label="no"];
  }
  ```
  ````

- [ ] For `subagent-dev.md`: Read the existing graph at lines 120–168 carefully. The current graph shows the per-task loop with review levels (L1/L2/L3). Enhance it to add the two-stage review loop nodes from Pattern 4. Replace the existing graph content with this enhanced version:

  ````markdown
  ## Process Graph (Authoritative)

  > When this graph conflicts with prose, follow the graph.

  ```dot
  digraph subagent_dev {
    rankdir=TB;

    "branch_gate" [label="Branch Gate\ncheck current branch" shape=diamond];
    "on_main" [label="STOP: on main/master\nCreate feature branch first" shape=box style=filled fillcolor=red fontcolor=white];
    "load_plan" [label="Read plan, extract tasks\nCreate TodoWrite list" shape=box];
    "dispatch_impl" [label="Dispatch implementation agent\n(agent from task Agent field)" shape=box];
    "impl_questions" [label="Agent has questions?" shape=diamond];
    "answer" [label="Answer questions\nprovide context" shape=box];
    "impl_done" [label="Implementation complete\nand committed" shape=box];
    "trivial" [label="Task marked trivial?" shape=diamond];
    "spec_review" [label="Dispatch spec-reviewer\n(verify spec compliance)" shape=box style=filled fillcolor=lightyellow];
    "spec_pass" [label="spec-reviewer PASS?" shape=diamond];
    "spec_fix" [label="Implementer fixes\nspec gaps" shape=box];
    "spec_second_fail" [label="Second spec FAIL?" shape=diamond];
    "spec_escalate" [label="ESCALATE to user\n(do not loop again)" shape=box style=filled fillcolor=orange];
    "quality_review" [label="Dispatch code-quality-reviewer\n(verify code quality)" shape=box style=filled fillcolor=lightyellow];
    "quality_pass" [label="quality-reviewer PASS?" shape=diamond];
    "quality_fix" [label="Implementer fixes\nquality issues" shape=box];
    "quality_second_fail" [label="Second quality FAIL?" shape=diamond];
    "quality_escalate" [label="ESCALATE to user\n(do not loop again)" shape=box style=filled fillcolor=orange];
    "task_complete" [label="Mark task complete\nin TodoWrite" shape=box];
    "more_tasks" [label="More tasks remain?" shape=diamond];
    "cleanup" [label="Dispatch post-task-cleanup" shape=box];
    "finish" [label="/finish-branch" shape=box style=filled fillcolor=lightgreen];

    "branch_gate" -> "on_main" [label="main/master"];
    "branch_gate" -> "load_plan" [label="feature branch"];
    "load_plan" -> "dispatch_impl";
    "dispatch_impl" -> "impl_questions";
    "impl_questions" -> "answer" [label="yes"];
    "answer" -> "dispatch_impl";
    "impl_questions" -> "impl_done" [label="no"];
    "impl_done" -> "trivial";
    "trivial" -> "task_complete" [label="yes (with justification)"];
    "trivial" -> "spec_review" [label="no"];
    "spec_review" -> "spec_pass";
    "spec_pass" -> "quality_review" [label="yes"];
    "spec_pass" -> "spec_fix" [label="no (first fail)"];
    "spec_fix" -> "spec_review" [label="re-review"];
    "spec_review" -> "spec_second_fail" [label="still failing"];
    "spec_second_fail" -> "spec_escalate" [label="yes"];
    "spec_second_fail" -> "quality_review" [label="no (passed)"];
    "quality_review" -> "quality_pass";
    "quality_pass" -> "task_complete" [label="yes"];
    "quality_pass" -> "quality_fix" [label="no (first fail)"];
    "quality_fix" -> "quality_review" [label="re-review"];
    "quality_review" -> "quality_second_fail" [label="still failing"];
    "quality_second_fail" -> "quality_escalate" [label="yes"];
    "quality_second_fail" -> "task_complete" [label="no (passed)"];
    "task_complete" -> "more_tasks";
    "more_tasks" -> "dispatch_impl" [label="yes"];
    "more_tasks" -> "cleanup" [label="no"];
    "cleanup" -> "finish";
  }
  ```
  ````

- [ ] Add the following `## Process Graph (Authoritative)` section to `execute-plan.md` (insert after the branch gate section added in Task 2, before the main execution instructions):

  ````markdown
  ## Process Graph (Authoritative)

  > When this graph conflicts with prose, follow the graph.

  ```dot
  digraph execute_plan {
    rankdir=TB;

    "branch_gate" [label="Branch Gate\ncheck current branch" shape=diamond];
    "on_main" [label="STOP: on main/master\nCreate feature branch first" shape=box style=filled fillcolor=red fontcolor=white];
    "load_plan" [label="Load plan from docs/plans/" shape=box];
    "review_plan" [label="Review plan\n(all tasks and context)" shape=box];
    "batch_tasks" [label="Group tasks into batches\n(3-5 tasks per batch)" shape=box];
    "execute_batch" [label="Execute current batch\n(task by task)" shape=box];
    "checkpoint" [label="Checkpoint: batch complete\nreport to user" shape=box];
    "user_review" [label="User approves batch?" shape=diamond];
    "revise" [label="Revise based on feedback" shape=box];
    "more_batches" [label="More batches remain?" shape=diamond];
    "done" [label="/finish-branch" shape=box style=filled fillcolor=lightgreen];

    "branch_gate" -> "on_main" [label="main/master"];
    "branch_gate" -> "load_plan" [label="feature branch"];
    "load_plan" -> "review_plan";
    "review_plan" -> "batch_tasks";
    "batch_tasks" -> "execute_batch";
    "execute_batch" -> "checkpoint";
    "checkpoint" -> "user_review";
    "user_review" -> "revise" [label="needs changes"];
    "revise" -> "execute_batch";
    "user_review" -> "more_batches" [label="approved"];
    "more_batches" -> "execute_batch" [label="yes"];
    "more_batches" -> "done" [label="no"];
  }
  ```
  ````

- [ ] Verify: All 4 command files contain a `## Process Graph (Authoritative)` section.
- [ ] Verify: Each section contains a fenced DOT block (` ```dot `).
- [ ] Verify: The instruction "When this graph conflicts with prose, follow the graph." appears verbatim in each section.
- [ ] Commit:
  ```bash
  git add .claude/commands/brainstorm.md .claude/commands/fix-bugs.md .claude/commands/subagent-dev.md .claude/commands/execute-plan.md
  git commit -m "feat: add authoritative DOT flowcharts to 4 commands (Pattern 2)

  Adds Process Graph (Authoritative) sections to brainstorm, fix-bugs,
  execute-plan. Enhances existing subagent-dev graph to include two-stage
  review loop nodes from Pattern 4. Graphs take precedence over prose.

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

## Task 9: Pattern 6 — On-Demand MCP Documentation

**Agent:** modular-builder
**Files:** `AGENTS.md`

### Steps

- [ ] Read the end of `AGENTS.md` to find the current last line (after the Red Flags section appended in Task 1).
- [ ] Append the following On-Demand MCP section to `AGENTS.md` after the Red Flags section. Do NOT modify any existing content:

  ````markdown

  ## On-Demand MCP

  The always-loaded MCP servers (Episodic Memory, Chrome, Playwright) are sufficient for most tasks.
  For specialized tasks requiring additional servers, use the `mcp` CLI rather than adding to the
  always-loaded configuration.

  ### Tiered MCP Approach

  | Tier | Servers | Configuration |
  |------|---------|---------------|
  | Always loaded | Episodic Memory, Chrome, Playwright | `~/.claude/settings.json` (unchanged) |
  | On-demand | Additional servers as needed | `mcp` CLI invocation |
  | Project-specific | Servers for a specific repo | Project `.claude/settings.json` |

  ### Pattern

  Start an MCP server on-demand:
  ```bash
  mcp add <server-name> -- <command>
  ```

  Remove it when done:
  ```bash
  mcp remove <server-name>
  ```

  ### Principles

  - **Keep the base lean**: Only servers needed for every session belong in always-loaded config.
  - **On-demand for specialized work**: Add servers for the duration of the task, then remove.
  - **Project-specific servers**: Place in the project's `.claude/settings.json`, not global config.
  - **Never modify global config for temporary needs**: Use `mcp add/remove` instead.
  ````

- [ ] Verify: `AGENTS.md` contains `## On-Demand MCP` section with the tiered table.
- [ ] Verify: The Red Flags section added in Task 1 is still present and unchanged.
- [ ] Verify: All content above the Red Flags section is unchanged.
- [ ] Commit:
  ```bash
  git add AGENTS.md
  git commit -m "feat: add On-Demand MCP documentation to AGENTS.md (Pattern 6)

  Appends tiered MCP approach documentation explaining always-loaded vs
  on-demand vs project-specific server configuration. Documents mcp
  add/remove pattern. No existing content modified.

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

## Task 10: Pattern 4 — Create Review Agents

**Agent:** modular-builder
**Files:** `.claude/agents/spec-reviewer.md`, `.claude/agents/code-quality-reviewer.md`

### Steps

- [ ] Read one existing agent file (e.g., `.claude/agents/test-coverage.md`) to confirm the exact YAML frontmatter format to use as a template.
- [ ] Create `.claude/agents/spec-reviewer.md` with the following content:

  ````markdown
  ---
  name: spec-reviewer
  description: Review spec compliance, verify implementations against requirements, check all specified requirements are addressed, identify missing behaviors, flag spec contradictions
  model: inherit
  ---

  # Spec Reviewer

  You are a spec compliance reviewer. Your role is to verify that an implementation satisfies the task specification requirements. You are independent — you did not write the code and you have no bias toward approving it.

  ## Role

  Given a task specification and the implementation (files changed + diff or summary), determine whether the implementation fully satisfies the spec. Produce a clear PASS or FAIL verdict with specific findings.

  ## Inputs (provided in your task prompt)

  - The original task specification (requirements, acceptance criteria)
  - List of files changed
  - Diff or summary of changes made

  ## Checks to Perform

  1. **All requirements addressed**: Every requirement in the spec has a corresponding implementation.
  2. **No missing requirements**: Nothing specified is absent from the implementation.
  3. **No contradictions**: No implemented behavior contradicts the spec.
  4. **Edge cases handled**: Edge cases explicitly mentioned in the spec are addressed.
  5. **Acceptance criteria met**: Each acceptance criterion from the spec passes.

  ## Output Format

  Always respond with exactly this format:

  ```
  VERDICT: PASS | FAIL
  FINDINGS:
  - [specific finding 1 — cite the spec requirement and what was found]
  - [specific finding 2]
  (list all findings; if PASS, list what was verified)
  ```

  Do not add prose before or after this block. The orchestrator reads this format programmatically.

  ## Rules

  - Be specific: cite the exact spec requirement that is violated or satisfied.
  - Do not approve code that is missing any spec requirement, even if it "looks good."
  - Do not fail code for things not in the spec (style preferences, additional features, etc.).
  - If the spec is ambiguous on a point, note the ambiguity in FINDINGS but do not FAIL on it alone.

  ## Context Budget

  When nearing your turn limit, STOP tool calls and produce your final VERDICT with whatever findings you have. Partial results with clear structure are MORE valuable than exhausting all turns on reading with no summary. Always reserve at least 2 turns for writing your response.
  ````

- [ ] Create `.claude/agents/code-quality-reviewer.md` with the following content:

  ````markdown
  ---
  name: code-quality-reviewer
  description: Review code quality, check type annotations, verify project style compliance, identify dead code, flag stubs and placeholders, assess test coverage for new logic
  model: inherit
  ---

  # Code Quality Reviewer

  You are a code quality reviewer. Your role is to verify that an implementation follows project patterns, type safety, and test requirements. You are independent — you did not write the code and you have no bias toward approving it.

  ## Role

  Given a list of changed files and their diffs (plus project conventions from AGENTS.md), determine whether the implementation meets quality standards. Produce a clear PASS or FAIL verdict with specific findings.

  ## Inputs (provided in your task prompt)

  - List of files changed
  - Diff or summary of changes made
  - Project conventions (from AGENTS.md — code style, line length, type requirements, etc.)

  ## Checks to Perform

  1. **Type annotations**: All functions and methods have type annotations; no unannotated `Any` types introduced.
  2. **Code style**: Line length ≤120 chars, imports organized (stdlib / third-party / local), naming follows project conventions.
  3. **Tests exist**: New logic has corresponding tests, or the orchestrator has explicitly justified the exemption.
  4. **No dead code**: No unused imports, variables, or unreachable code blocks introduced.
  5. **No stubs**: No `NotImplementedError`, bare `TODO` without code, or `pass` as stub in production paths.
  6. **No placeholders**: No `return {}  # stub`, fake implementations, or "coming soon" markers.

  ## Output Format

  Always respond with exactly this format:

  ```
  VERDICT: PASS | FAIL
  FINDINGS:
  - [specific finding 1 — cite the file, line/function, and issue]
  - [specific finding 2]
  (list all findings; if PASS, list what was verified)
  ```

  Do not add prose before or after this block. The orchestrator reads this format programmatically.

  ## Rules

  - Be specific: cite the file and function/line where the issue occurs.
  - Do not fail for spec compliance issues — that is spec-reviewer's job.
  - Do not fail for issues that existed before this change (focus on the diff).
  - If a check is not applicable (e.g., non-Python file), skip it and note the skip.

  ## Context Budget

  When nearing your turn limit, STOP tool calls and produce your final VERDICT with whatever findings you have. Partial results with clear structure are MORE valuable than exhausting all turns on reading with no summary. Always reserve at least 2 turns for writing your response.
  ````

- [ ] Verify: Both agent files exist at the correct paths.
- [ ] Verify: Both files have valid YAML frontmatter with `name`, `description`, and `model` fields.
- [ ] Verify: Both files have the Context Budget section with the synthesis guard.
- [ ] Commit:
  ```bash
  git add .claude/agents/spec-reviewer.md .claude/agents/code-quality-reviewer.md
  git commit -m "feat: create spec-reviewer and code-quality-reviewer agents (Pattern 4)

  Two new review agents for the two-stage automated review loop.
  spec-reviewer checks implementation against task specification.
  code-quality-reviewer checks type safety, style, tests, and no stubs.
  Both produce VERDICT: PASS|FAIL format for programmatic reading.

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

## Task 11: Pattern 4 — Two-Stage Review in subagent-dev

**Agent:** modular-builder
**Files:** `.claude/commands/subagent-dev.md`

### Steps

- [ ] Read `.claude/commands/subagent-dev.md` fully (674 lines) to understand the current task dispatch flow and review levels section.
- [ ] Locate the "Review Levels" section or equivalent section that describes the current review process after an implementer completes a task.
- [ ] Replace or supplement the existing review logic with the following two-stage review loop. Insert it after the section that describes an implementer completing their work (and before the "Mark task complete" step):

  ````markdown
  ## Two-Stage Review Loop (REQUIRED for non-trivial tasks)

  After each implementation agent completes a task, run two sequential review stages before marking the task complete.

  ### Trivial Task Exemption

  A task may skip the review loop ONLY if the orchestrator explicitly marks it as trivial at dispatch time. Trivial means: single-line change or documentation-only update. The orchestrator must include the following in the task dispatch:

  ```
  TRIVIAL EXEMPTION: [specific justification — e.g., "single typo fix in README"]
  ```

  If no TRIVIAL EXEMPTION is logged, both review stages are mandatory.

  ### Stage 1: Spec Compliance Review

  After the implementer completes:

  1. Dispatch `spec-reviewer` with:
     - The original task specification (copy the task's Steps/description from the plan)
     - List of files changed (from the implementer's commit)
     - Summary of changes (from the implementer's report)

  2. Read the `VERDICT` from spec-reviewer:
     - **PASS**: Proceed to Stage 2.
     - **FAIL (first time)**: Share FINDINGS with the implementer. Dispatch implementer again to fix the spec gaps. Then dispatch spec-reviewer again for re-review.
     - **FAIL (second time)**: ESCALATE TO USER. Report both the FINDINGS and the implementer's attempted fixes. Do not loop a third time. Wait for user direction.

  ### Stage 2: Code Quality Review

  After spec-reviewer returns PASS:

  1. Dispatch `code-quality-reviewer` with:
     - List of files changed
     - Summary of changes
     - Reference to AGENTS.md for project conventions

  2. Read the `VERDICT` from code-quality-reviewer:
     - **PASS**: Task is complete. Mark it done in TodoWrite.
     - **FAIL (first time)**: Share FINDINGS with the implementer. Dispatch implementer again to fix the quality issues. Then dispatch code-quality-reviewer again for re-review.
     - **FAIL (second time)**: ESCALATE TO USER. Report both the FINDINGS and the implementer's attempted fixes. Do not loop a third time. Wait for user direction.

  ### Loop Cap Enforcement

  Maximum 2 review cycles per reviewer per task. Track cycle count explicitly. Never dispatch a third review cycle — always escalate after the second consecutive FAIL.

  ### Dispatch Announcements for Reviews

  Use this format for all review dispatches:

  ```
  >> Review [1/2]: spec-reviewer for Task N — spec compliance check
  >> Review [2/2]: code-quality-reviewer for Task N — code quality check
  ```
  ````

- [ ] Verify: The two-stage review loop section is present in `subagent-dev.md`.
- [ ] Verify: The loop cap (max 2 cycles, escalate on second FAIL) is explicit.
- [ ] Verify: The trivial task exemption is described with mandatory justification requirement.
- [ ] Verify: The DOT graph added in Task 8 already includes the review nodes — confirm the graph and this prose section are consistent.
- [ ] Commit:
  ```bash
  git add .claude/commands/subagent-dev.md
  git commit -m "feat: add two-stage automated review loop to subagent-dev (Pattern 4)

  Adds mandatory spec-reviewer then code-quality-reviewer review loop
  after each implementation task. Hard cap of 2 cycles per reviewer;
  escalates to user on second consecutive FAIL. Includes trivial task
  exemption with mandatory justification. Consistent with DOT graph.

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

## Task 12: Final Verification

**Agent:** test-coverage

### Steps

- [ ] Verify Pattern 3 — Red Flags:
  - `AGENTS.md` contains `## Red Flags` section
  - Table has exactly 10 rows
  - Existing content before the section is unchanged

- [ ] Verify Pattern 5 — Branch Gates:
  - `execute-plan.md` contains branch gate block
  - `modular-build.md` contains branch gate block
  - `parallel-agents.md` contains branch gate block
  - `subagent-dev.md` gate is a hard block (not a soft warning)

- [ ] Verify Pattern 1 — EnterPlanMode Hook:
  - `.claude/tools/enforce-brainstorm.sh` exists
  - Script is executable (`ls -la .claude/tools/enforce-brainstorm.sh`)
  - Script checks for `/tmp/amplifier-brainstorm-done` and exits 2 if absent
  - `.claude/settings.json` has EnterPlanMode entry in PreToolUse array
  - All other hooks in `settings.json` are unchanged

- [ ] Verify Pattern 1 — Marker Files:
  - `brainstorm.md` contains `touch /tmp/amplifier-brainstorm-done`
  - `create-plan.md` contains `touch /tmp/amplifier-brainstorm-done`

- [ ] Verify Pattern 7 — CSO Descriptions (all 34 agents):
  - No description field contains "specialized" as a descriptor
  - No description field contains "expert" as a descriptor
  - No description field contains "designed to"
  - Every description starts with an action verb
  - Run: `grep -l "specialized\|designed to" .claude/agents/*.md` — expect zero results

- [ ] Verify AGENTS_CATALOG.md:
  - All 34 agents have updated Purpose values
  - Table structure unchanged

- [ ] Verify Pattern 2 — DOT Flowcharts:
  - `brainstorm.md` contains `## Process Graph (Authoritative)`
  - `fix-bugs.md` contains `## Process Graph (Authoritative)`
  - `subagent-dev.md` graph is enhanced with review loop nodes
  - `execute-plan.md` contains `## Process Graph (Authoritative)`
  - All 4 contain the verbatim instruction: "When this graph conflicts with prose, follow the graph."

- [ ] Verify Pattern 6 — On-Demand MCP:
  - `AGENTS.md` contains `## On-Demand MCP` section
  - Tiered table is present
  - No changes to any `settings.json` MCP server configuration

- [ ] Verify Pattern 4 — Review Agents:
  - `.claude/agents/spec-reviewer.md` exists with valid frontmatter
  - `.claude/agents/code-quality-reviewer.md` exists with valid frontmatter
  - Both have Context Budget / synthesis guard sections
  - `subagent-dev.md` contains "Two-Stage Review Loop" section
  - Loop cap (max 2 cycles) is explicit in the prose

- [ ] Produce a verification report summarizing: total files changed, all 7 patterns confirmed present, any discrepancies found.

---

## Summary

| Task | Pattern | Description | Agent |
|------|---------|-------------|-------|
| 1 | 3 | Red Flags rationalization table → AGENTS.md | modular-builder |
| 2 | 5 | Branch gates → 4 implementation commands | modular-builder |
| 3 | 1 | EnterPlanMode hook + settings.json registration | modular-builder |
| 4 | 1 | Brainstorm marker write → brainstorm.md, create-plan.md | modular-builder |
| 5 | 7 | CSO descriptions → agents 1-17 | modular-builder |
| 6 | 7 | CSO descriptions → agents 18-34 | modular-builder |
| 7 | 7 | Sync AGENTS_CATALOG.md → all 34 agents | modular-builder |
| 8 | 2 | DOT flowcharts → 4 commands | modular-builder |
| 9 | 6 | On-Demand MCP section → AGENTS.md | modular-builder |
| 10 | 4 | Create spec-reviewer + code-quality-reviewer agents | modular-builder |
| 11 | 4 | Two-stage review loop → subagent-dev.md | modular-builder |
| 12 | all | Final verification across all 7 patterns | test-coverage |
