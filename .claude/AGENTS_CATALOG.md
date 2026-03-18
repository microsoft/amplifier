# Amplifier Agents Catalog

Complete reference for all 36 specialized agents. Each agent is defined in the `amplifier-core plugin`.

## Core Development Agents

| Agent | Purpose | Dispatch Keywords |
|-------|---------|-------------------|
| `amplifier-core:agentic-search` | Search codebases, find files, locate symbols, trace dependencies, explore unfamiliar code | search, find, where, how does, understand, explore |
| `amplifier-core:zen-architect` | Review architecture, evaluate trade-offs, simplify complexity, conduct code reviews | plan, design, architect, structure, review |
| `amplifier-core:modular-builder` | Implement features, build modules, write code from specifications, execute implementation tasks | implement, build, create, write code |
| `amplifier-core:bug-hunter` | Debug errors, fix bugs, investigate failures, troubleshoot crashes, trace root causes | fix, debug, error, failure, broken |
| `amplifier-core:test-coverage` | Analyze test coverage, identify gaps, review spec compliance, verify implementations | test, coverage, verify, validate |
| `amplifier-core:security-guardian` | Review security, audit auth flows, identify OWASP vulnerabilities, assess secrets exposure | security, auth, secrets, vulnerability |
| `amplifier-core:post-task-cleanup` | Clean up after tasks, remove dead code, fix lint errors, restore codebase tidiness | cleanup, hygiene, lint, unused, dead code |
| `amplifier-core:performance-optimizer` | Optimize performance, profile bottlenecks, measure latency, resolve throughput issues | performance, slow, optimize, bottleneck |
| `amplifier-core:integration-specialist` | Integrate external services, wire APIs, connect MCP servers, debug integration failures | API, MCP, external, dependency, integration |
| `amplifier-core:spec-reviewer` | Review spec compliance, verify implementations match requirements, detect missing or extra work | spec review, compliance, verify spec |
| `amplifier-core:code-quality-reviewer` | Review code quality, check type safety, enforce style consistency, verify test coverage | quality review, code review, style, types |

## API & Data Agents

| Agent | Purpose | Dispatch Keywords |
|-------|---------|-------------------|
| `amplifier-core:api-contract-designer` | Design REST APIs, define GraphQL schemas, write OpenAPI specs, specify contracts | endpoint, contract, REST, GraphQL, route |
| `amplifier-core:database-architect` | Design schemas, write migrations, optimize queries, define indexes, resolve N+1 problems | schema, migration, query, index, database |
| `amplifier-core:contract-spec-author` | Write formal specifications, author interface contracts, define acceptance criteria | spec, contract, interface, protocol |
| `amplifier-core:module-intent-architect` | Translate requirements into module specs, define module boundaries, clarify interfaces | module boundary, interface, requirements |

## Design Agents

| Agent | Purpose | Dispatch Keywords |
|-------|---------|-------------------|
| `amplifier-core:component-designer` | Design UI components, implement frontend widgets, create React/Vue/Svelte components | component, UI, frontend, visual, widget |
| `amplifier-core:art-director` | Direct visual aesthetics, define brand identity, set color palettes, evaluate consistency | aesthetic, brand, visual identity, style |
| `amplifier-core:animation-choreographer` | Design animations, choreograph transitions, specify motion curves, create micro-interactions | animation, transition, motion, easing |
| `amplifier-core:layout-architect` | Design page layouts, define information architecture, plan grid systems | layout, grid, page structure, navigation |
| `amplifier-core:responsive-strategist` | Design responsive layouts, define breakpoints, adapt UI for mobile/tablet/desktop | responsive, breakpoint, mobile, viewport |
| `amplifier-core:design-system-architect` | Build design systems, define design tokens, architect theme infrastructure | design tokens, theme, design system |
| `amplifier-core:voice-strategist` | Write UX copy, craft microcopy, define voice and tone, improve error messages | copy, microcopy, tone, error message |

## Knowledge & Analysis Agents

| Agent | Purpose | Dispatch Keywords |
|-------|---------|-------------------|
| `amplifier-core:content-researcher` | Research topics, investigate content, compare sources, extract actionable insights | research, investigate, compare, evaluate |
| `amplifier-core:analysis-engine` | Analyze systems, audit codebases, assess technical debt, produce structured reports | analyze, assess, audit, measure, report |
| `amplifier-core:concept-extractor` | Extract key concepts, distill articles, summarize papers, surface actionable takeaways | extract, summarize, distill, key ideas |
| `amplifier-core:insight-synthesizer` | Synthesize cross-domain insights, identify meta-patterns, combine findings from multiple sources | synthesize, combine, cross-reference |
| `amplifier-core:knowledge-archaeologist` | Trace knowledge evolution, recover abandoned approaches, investigate legacy decisions | history, evolution, legacy, original intent |
| `amplifier-core:pattern-emergence` | Detect emergent patterns, identify recurring structures, surface trends across diverse inputs | pattern, recurring, trend, structural |
| `amplifier-core:visualization-architect` | Design data visualizations, create charts and diagrams, specify rendering approaches | diagram, chart, graph, visualize |
| `amplifier-core:graph-builder` | Build knowledge graphs, map entity relationships, construct multi-perspective networks | graph, relationship, entity, network |

## Infrastructure Agents

| Agent | Purpose | Dispatch Keywords |
|-------|---------|-------------------|
| `amplifier-core:vmware-infrastructure` | Diagnose VMware issues, analyze ESXi/VCSA/NSX logs, generate PowerCLI commands | vmware, vcsa, esxi, nsx, vsphere, powercli, vcenter, vmkernel, log analysis |

## Meta Agents

| Agent | Purpose | Dispatch Keywords |
|-------|---------|-------------------|
| `amplifier-core:subagent-architect` | Create new agents, design agent prompts, define agent roles, review agent effectiveness | new agent, specialized agent, create agent |
| `amplifier-core:amplifier-cli-architect` | Design CLI tools, architect hybrid code-AI workflows, structure amplifier scenarios | CLI tool, command, scenario, amplifier tool |
| `amplifier-core:ambiguity-guardian` | Preserve contradictions, flag ambiguous requirements, surface hidden assumptions | ambiguous, unclear, conflicting, assumption |
| `amplifier-core:amplifier-expert` | Answer Amplifier questions, explain agent selection, troubleshoot command failures | amplifier, how to, expert, help, explain |
| `amplifier-core:handoff-gemini` | Prepare Gemini handoffs, write HANDOFF.md dispatches, coordinate cross-model work | handoff, gemini, dispatch, cross-model |

## Review Agent Mapping

Used by superpowers skills for two-stage review:

| Review Type | Agent | When |
|-------------|-------|------|
| Spec Compliance | `amplifier-core:spec-reviewer` | After every implementation task |
| Code Quality | `amplifier-core:code-quality-reviewer` | After spec compliance passes |
| Security | `amplifier-core:security-guardian` | Security-sensitive tasks or final review |
| Post-completion | `amplifier-core:post-task-cleanup` | After all tasks pass, before finishing branch |

## Model Tier Mapping

| Agent | Tier | Claude | Gemini |
|-------|------|--------|--------|
| `amplifier-core:agentic-search` (scouting) | Fast | `haiku` | Flash |
| `amplifier-core:agentic-search` (deep investigation) | Balanced | `sonnet` | Pro |
| `amplifier-core:modular-builder` (simple, 1-2 files) | Fast | `haiku` | Flash |
| `amplifier-core:modular-builder` (multi-file) | Balanced | `sonnet` | Pro |
| `amplifier-core:bug-hunter` | Balanced | `sonnet` | Pro |
| `amplifier-core:database-architect` | Balanced | `sonnet` | Pro |
| `amplifier-core:api-contract-designer` | Balanced | `sonnet` | Pro |
| `amplifier-core:contract-spec-author` | Balanced | `sonnet` | Pro |
| `amplifier-core:module-intent-architect` | Balanced | `sonnet` | Pro |
| `amplifier-core:integration-specialist` | Balanced | `sonnet` | Pro |
| `amplifier-core:performance-optimizer` | Balanced | `sonnet` | Pro |
| `amplifier-core:component-designer` | Balanced | `sonnet` | Pro |
| `amplifier-core:art-director` | Balanced | `sonnet` | Pro |
| `amplifier-core:animation-choreographer` | Balanced | `sonnet` | Pro |
| `amplifier-core:layout-architect` | Balanced | `sonnet` | Pro |
| `amplifier-core:responsive-strategist` | Balanced | `sonnet` | Pro |
| `amplifier-core:design-system-architect` | Balanced | `sonnet` | Pro |
| `amplifier-core:voice-strategist` | Fast | `haiku` | Flash |
| `amplifier-core:content-researcher` | Balanced | `sonnet` | Pro |
| `amplifier-core:analysis-engine` | Balanced | `sonnet` | Pro |
| `amplifier-core:concept-extractor` | Fast | `haiku` | Flash |
| `amplifier-core:insight-synthesizer` | Balanced | `sonnet` | Pro |
| `amplifier-core:knowledge-archaeologist` | Balanced | `sonnet` | Pro |
| `amplifier-core:pattern-emergence` | Balanced | `sonnet` | Pro |
| `amplifier-core:visualization-architect` | Balanced | `sonnet` | Pro |
| `amplifier-core:graph-builder` | Balanced | `sonnet` | Pro |
| `amplifier-core:vmware-infrastructure` | Balanced | `sonnet` | Pro |
| `amplifier-core:spec-reviewer` | Balanced | `sonnet` | Pro |
| `amplifier-core:code-quality-reviewer` | Balanced | `sonnet` | Pro |
| `amplifier-core:test-coverage` (review) | Balanced | `sonnet` | Pro |
| `amplifier-core:zen-architect` (review/architecture) | Deep | `opus` | Pro |
| `amplifier-core:security-guardian` | Deep | `opus` | Pro |
| `amplifier-core:post-task-cleanup` | Fast | `haiku` | Flash |
| `amplifier-core:subagent-architect` | Balanced | `sonnet` | Pro |
| `amplifier-core:amplifier-cli-architect` | Balanced | `sonnet` | Pro |
| `amplifier-core:ambiguity-guardian` | Balanced | `sonnet` | Pro |
| `amplifier-core:amplifier-expert` | Fast | `haiku` | Flash |
| `amplifier-core:handoff-gemini` | Fast | `haiku` | Flash |

## Key Commands (dispatch agents)

These slash commands orchestrate agent dispatch. Listed here for discoverability.

| Command | Purpose | Agents Used |
|---------|---------|-------------|
| `/frontend-design` | 14-mode frontend design with anti-slop detection | amplifier-core:component-designer, amplifier-core:art-director, amplifier-core:animation-choreographer, amplifier-core:layout-architect |
| `/design-interface` | Parallel "Design It Twice" — 3+ radically different proposals | amplifier-core:zen-architect (3 parallel) |
| `/retro` | Development retrospective — velocity, churn, quality metrics | general-purpose (haiku scout) |
| `/create-plan` | Structured plans with scope challenge + vertical slices | amplifier-core:zen-architect, amplifier-core:agentic-search |
| `/techdebt` | Technical debt scan including module depth analysis | amplifier-core:agentic-search (3 parallel) |
| `/test-verified` | E2E auto-fix with Exchange EWS verification | amplifier-core:bug-hunter, exchange-ews MCP |

## Selection Rules

1. Match task keywords against Dispatch Keywords column
2. If multiple agents match, pick the one whose Purpose best describes the primary goal
3. Implementation tasks default to `amplifier-core:modular-builder`
4. Review tasks always use the Review Agent Mapping
5. When unsure: `amplifier-core:modular-builder` for building, `amplifier-core:bug-hunter` for fixing
6. Design agents are for UI/frontend work only
7. Knowledge agents are for research/analysis tasks
