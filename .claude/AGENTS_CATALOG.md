# Amplifier Agents Catalog

Complete reference for all 30 specialized agents. Each agent is defined in `.claude/agents/<name>.md`.

## Core Development Agents

| Agent | Purpose | Dispatch Keywords |
|-------|---------|-------------------|
| `agentic-search` | Intelligent 3-phase codebase search with ctags (Recon/Search/Synthesis) | search, find, where, how does, understand, explore |
| `zen-architect` | Architecture, design, code review (3 modes: ANALYZE/ARCHITECT/REVIEW) | plan, design, architect, structure, review |
| `modular-builder` | Primary implementation from specifications (bricks-and-studs) | implement, build, create, write code |
| `bug-hunter` | Hypothesis-driven debugging and root cause analysis | fix, debug, error, failure, broken |
| `test-coverage` | Test analysis, gap identification, test case design | test, coverage, verify, validate |
| `security-guardian` | Security reviews, OWASP, vulnerability assessment | security, auth, secrets, vulnerability |
| `post-task-cleanup` | Codebase hygiene after task completion | cleanup, hygiene, lint, unused, dead code |
| `performance-optimizer` | Measure-first performance analysis and optimization | performance, slow, optimize, bottleneck |
| `integration-specialist` | External services, APIs, MCP servers, dependency health | API, MCP, external, dependency, integration |

## API & Data Agents

| Agent | Purpose | Dispatch Keywords |
|-------|---------|-------------------|
| `api-contract-designer` | REST/GraphQL API contracts and specifications | endpoint, contract, REST, GraphQL, route |
| `database-architect` | Schema design, query optimization, migrations | schema, migration, query, index, database |
| `contract-spec-author` | Formal contract and implementation specification docs | spec, contract, interface, protocol |
| `module-intent-architect` | Translate natural language to module specifications | module boundary, interface, requirements |

## Design Agents

| Agent | Purpose | Dispatch Keywords |
|-------|---------|-------------------|
| `component-designer` | Individual UI component design and implementation | component, UI, frontend, visual, widget |
| `art-director` | Aesthetic direction and visual strategy | aesthetic, brand, visual identity, style |
| `animation-choreographer` | Motion design, animations, transitions | animation, transition, motion, easing |
| `layout-architect` | Page-level layout, information architecture | layout, grid, page structure, navigation |
| `responsive-strategist` | Responsive design, breakpoints, device adaptation | responsive, breakpoint, mobile, viewport |
| `design-system-architect` | Design tokens, theme systems, design foundations | design tokens, theme, design system |
| `voice-strategist` | UX writing, microcopy, voice & tone | copy, microcopy, tone, error message |

## Knowledge & Analysis Agents

| Agent | Purpose | Dispatch Keywords |
|-------|---------|-------------------|
| `content-researcher` | Extract actionable insights from content collections | research, investigate, compare, evaluate |
| `analysis-engine` | Multi-mode analysis (DEEP/SYNTHESIS/TRIAGE) | analyze, assess, audit, measure, report |
| `concept-extractor` | Extract atomic concepts from articles/papers | extract, summarize, distill, key ideas |
| `insight-synthesizer` | Cross-domain connections and meta-pattern recognition | synthesize, combine, cross-reference |
| `knowledge-archaeologist` | Trace knowledge evolution, find abandoned approaches | history, evolution, legacy, original intent |
| `pattern-emergence` | Detect emergent patterns from diverse perspectives | pattern, recurring, trend, structural |
| `visualization-architect` | Data visualization and knowledge graph rendering | diagram, chart, graph, visualize |
| `graph-builder` | Multi-perspective knowledge graph construction | graph, relationship, entity, network |

## Meta Agents

| Agent | Purpose | Dispatch Keywords |
|-------|---------|-------------------|
| `subagent-architect` | Create new specialized agents | new agent, specialized agent, create agent |
| `amplifier-cli-architect` | CLI tool design for hybrid code/AI architectures | CLI tool, command, scenario, amplifier tool |
| `ambiguity-guardian` | Preserve productive contradictions and uncertainty | ambiguous, unclear, conflicting, assumption |

## Review Agent Mapping

Used by superpowers skills for two-stage review:

| Review Type | Agent | When |
|-------------|-------|------|
| Spec Compliance | `test-coverage` | After every implementation task |
| Code Quality | `zen-architect` (REVIEW mode) | After spec compliance passes |
| Security | `security-guardian` | Security-sensitive tasks or final review |
| Post-completion | `post-task-cleanup` | After all tasks pass, before finishing branch |

## Model Tier Mapping

| Agent | Tier | Claude | Gemini |
|-------|------|--------|--------|
| `modular-builder` (simple) | Fast | `haiku` | Flash |
| `modular-builder` (multi-file) | Balanced | `sonnet` | Pro |
| `bug-hunter` | Balanced | `sonnet` | Pro |
| `database-architect` | Balanced | `sonnet` | Pro |
| `test-coverage` (review) | Fast | `haiku` | Flash |
| `zen-architect` (review) | Balanced | `sonnet` | Pro |
| `security-guardian` | Deep | `opus` | Pro |
| `post-task-cleanup` | Fast | `haiku` | Flash |

## Selection Rules

1. Match task keywords against Dispatch Keywords column
2. If multiple agents match, pick the one whose Purpose best describes the primary goal
3. Implementation tasks default to `modular-builder`
4. Review tasks always use the Review Agent Mapping
5. When unsure: `modular-builder` for building, `bug-hunter` for fixing
6. Design agents are for UI/frontend work only
7. Knowledge agents are for research/analysis tasks
