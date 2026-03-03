# Amplifier Agents Catalog

Complete reference for all specialized agents. Each agent is defined in `.claude/agents/<name>.md`.

## Core Development Agents

| Agent | Purpose | Dispatch Keywords |
|-------|---------|-------------------|
| `agentic-search` | Search codebases, find files, locate symbols, trace dependencies, explore unfamiliar code | search, find, where, how does, understand, explore |
| `zen-architect` | Review architecture, evaluate trade-offs, simplify complexity, conduct code reviews | plan, design, architect, structure, review |
| `modular-builder` | Implement features, build modules, write code from specifications, execute implementation tasks | implement, build, create, write code |
| `bug-hunter` | Debug errors, fix bugs, investigate failures, troubleshoot crashes, trace root causes | fix, debug, error, failure, broken |
| `test-coverage` | Analyze test coverage, identify gaps, review spec compliance, verify implementations | test, coverage, verify, validate |
| `security-guardian` | Review security, audit auth flows, identify OWASP vulnerabilities, assess secrets exposure | security, auth, secrets, vulnerability |
| `post-task-cleanup` | Clean up after tasks, remove dead code, fix lint errors, restore codebase tidiness | cleanup, hygiene, lint, unused, dead code |
| `performance-optimizer` | Optimize performance, profile bottlenecks, measure latency, resolve throughput issues | performance, slow, optimize, bottleneck |
| `integration-specialist` | Integrate external services, wire APIs, connect MCP servers, debug integration failures | API, MCP, external, dependency, integration |
| `spec-reviewer` | Review spec compliance, verify implementations match requirements, detect missing or extra work | spec review, compliance, verify spec |
| `code-quality-reviewer` | Review code quality, check type safety, enforce style consistency, verify test coverage | quality review, code review, style, types |

## API & Data Agents

| Agent | Purpose | Dispatch Keywords |
|-------|---------|-------------------|
| `api-contract-designer` | Design REST APIs, define GraphQL schemas, write OpenAPI specs, specify contracts | endpoint, contract, REST, GraphQL, route |
| `database-architect` | Design schemas, write migrations, optimize queries, define indexes, resolve N+1 problems | schema, migration, query, index, database |
| `contract-spec-author` | Write formal specifications, author interface contracts, define acceptance criteria | spec, contract, interface, protocol |
| `module-intent-architect` | Translate requirements into module specs, define module boundaries, clarify interfaces | module boundary, interface, requirements |

## Design Agents

| Agent | Purpose | Dispatch Keywords |
|-------|---------|-------------------|
| `component-designer` | Design UI components, implement frontend widgets, create React/Vue/Svelte components | component, UI, frontend, visual, widget |
| `art-director` | Direct visual aesthetics, define brand identity, set color palettes, evaluate consistency | aesthetic, brand, visual identity, style |
| `animation-choreographer` | Design animations, choreograph transitions, specify motion curves, create micro-interactions | animation, transition, motion, easing |
| `layout-architect` | Design page layouts, define information architecture, plan grid systems | layout, grid, page structure, navigation |
| `responsive-strategist` | Design responsive layouts, define breakpoints, adapt UI for mobile/tablet/desktop | responsive, breakpoint, mobile, viewport |
| `design-system-architect` | Build design systems, define design tokens, architect theme infrastructure | design tokens, theme, design system |
| `voice-strategist` | Write UX copy, craft microcopy, define voice and tone, improve error messages | copy, microcopy, tone, error message |

## Knowledge & Analysis Agents

| Agent | Purpose | Dispatch Keywords |
|-------|---------|-------------------|
| `content-researcher` | Research topics, investigate content, compare sources, extract actionable insights | research, investigate, compare, evaluate |
| `analysis-engine` | Analyze systems, audit codebases, assess technical debt, produce structured reports | analyze, assess, audit, measure, report |
| `concept-extractor` | Extract key concepts, distill articles, summarize papers, surface actionable takeaways | extract, summarize, distill, key ideas |
| `insight-synthesizer` | Synthesize cross-domain insights, identify meta-patterns, combine findings from multiple sources | synthesize, combine, cross-reference |
| `knowledge-archaeologist` | Trace knowledge evolution, recover abandoned approaches, investigate legacy decisions | history, evolution, legacy, original intent |
| `pattern-emergence` | Detect emergent patterns, identify recurring structures, surface trends across diverse inputs | pattern, recurring, trend, structural |
| `visualization-architect` | Design data visualizations, create charts and diagrams, specify rendering approaches | diagram, chart, graph, visualize |
| `graph-builder` | Build knowledge graphs, map entity relationships, construct multi-perspective networks | graph, relationship, entity, network |

## Infrastructure Agents

| Agent | Purpose | Dispatch Keywords |
|-------|---------|-------------------|
| `vmware-infrastructure` | Diagnose VMware issues, analyze ESXi/VCSA/NSX logs, generate PowerCLI commands | vmware, vcsa, esxi, nsx, vsphere, powercli, vcenter, vmkernel, log analysis |

## Meta Agents

| Agent | Purpose | Dispatch Keywords |
|-------|---------|-------------------|
| `subagent-architect` | Create new agents, design agent prompts, define agent roles, review agent effectiveness | new agent, specialized agent, create agent |
| `amplifier-cli-architect` | Design CLI tools, architect hybrid code-AI workflows, structure amplifier scenarios | CLI tool, command, scenario, amplifier tool |
| `ambiguity-guardian` | Preserve contradictions, flag ambiguous requirements, surface hidden assumptions | ambiguous, unclear, conflicting, assumption |
| `amplifier-expert` | Answer Amplifier questions, explain agent selection, troubleshoot command failures | amplifier, how to, expert, help, explain |
| `handoff-gemini` | Prepare Gemini handoffs, write HANDOFF.md dispatches, coordinate cross-model work | handoff, gemini, dispatch, cross-model |

## Review Agent Mapping

Used by superpowers skills for two-stage review:

| Review Type | Agent | When |
|-------------|-------|------|
| Spec Compliance | `spec-reviewer` | After every implementation task |
| Code Quality | `code-quality-reviewer` | After spec compliance passes |
| Security | `security-guardian` | Security-sensitive tasks or final review |
| Post-completion | `post-task-cleanup` | After all tasks pass, before finishing branch |

## Model Tier Mapping

| Agent | Tier | Claude | Gemini |
|-------|------|--------|--------|
| `agentic-search` (scouting) | Fast | `haiku` | Flash |
| `agentic-search` (deep investigation) | Balanced | `sonnet` | Pro |
| `modular-builder` (simple, 1-2 files) | Fast | `haiku` | Flash |
| `modular-builder` (multi-file) | Balanced | `sonnet` | Pro |
| `bug-hunter` | Balanced | `sonnet` | Pro |
| `database-architect` | Balanced | `sonnet` | Pro |
| `api-contract-designer` | Balanced | `sonnet` | Pro |
| `contract-spec-author` | Balanced | `sonnet` | Pro |
| `module-intent-architect` | Balanced | `sonnet` | Pro |
| `integration-specialist` | Balanced | `sonnet` | Pro |
| `performance-optimizer` | Balanced | `sonnet` | Pro |
| `component-designer` | Balanced | `sonnet` | Pro |
| `art-director` | Balanced | `sonnet` | Pro |
| `animation-choreographer` | Balanced | `sonnet` | Pro |
| `layout-architect` | Balanced | `sonnet` | Pro |
| `responsive-strategist` | Balanced | `sonnet` | Pro |
| `design-system-architect` | Balanced | `sonnet` | Pro |
| `voice-strategist` | Fast | `haiku` | Flash |
| `content-researcher` | Fast | `haiku` | Flash |
| `analysis-engine` | Balanced | `sonnet` | Pro |
| `concept-extractor` | Fast | `haiku` | Flash |
| `insight-synthesizer` | Balanced | `sonnet` | Pro |
| `knowledge-archaeologist` | Balanced | `sonnet` | Pro |
| `pattern-emergence` | Balanced | `sonnet` | Pro |
| `visualization-architect` | Balanced | `sonnet` | Pro |
| `graph-builder` | Balanced | `sonnet` | Pro |
| `vmware-infrastructure` | Balanced | `sonnet` | Pro |
| `spec-reviewer` | Fast | `haiku` | Flash |
| `code-quality-reviewer` | Balanced | `sonnet` | Pro |
| `test-coverage` (review) | Fast | `haiku` | Flash |
| `zen-architect` (review) | Balanced | `sonnet` | Pro |
| `security-guardian` | Deep | `opus` | Pro |
| `post-task-cleanup` | Fast | `haiku` | Flash |
| `subagent-architect` | Balanced | `sonnet` | Pro |
| `amplifier-cli-architect` | Balanced | `sonnet` | Pro |
| `ambiguity-guardian` | Balanced | `sonnet` | Pro |
| `amplifier-expert` | Fast | `haiku` | Flash |
| `handoff-gemini` | Fast | `haiku` | Flash |

## Selection Rules

1. Match task keywords against Dispatch Keywords column
2. If multiple agents match, pick the one whose Purpose best describes the primary goal
3. Implementation tasks default to `modular-builder`
4. Review tasks always use the Review Agent Mapping
5. When unsure: `modular-builder` for building, `bug-hunter` for fixing
6. Design agents are for UI/frontend work only
7. Knowledge agents are for research/analysis tasks
