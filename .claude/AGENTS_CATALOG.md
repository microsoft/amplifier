# Amplifier Agents Catalog

This catalog documents all available agents in the Amplifier system, their purposes, trigger keywords, and combination patterns.

## ✅ Implemented Agents (21)

### Core Development Agents

#### zen-architect
- **Purpose**: Design system architecture with ruthless simplicity
- **Trigger keywords**: design, architecture, plan, approach, structure
- **Modes**: ANALYZE (requirements), ARCHITECT (system design), REVIEW (code quality)
- **Combines with**: modular-builder, test-coverage, api-contract-designer

#### modular-builder  
- **Purpose**: Build code from specifications following modular philosophy
- **Trigger keywords**: implement, build, create, add feature
- **Modes**: Implementation from zen-architect specs
- **Combines with**: zen-architect (specs), test-coverage (testing)

#### bug-hunter
- **Purpose**: Systematically find and fix bugs
- **Trigger keywords**: fix, broken, error, not working, debug
- **Combines with**: root-cause-analyzer, test-coverage

#### test-coverage
- **Purpose**: Analyze test coverage and suggest comprehensive test cases
- **Trigger keywords**: test, coverage, validation
- **Combines with**: All development agents

#### integration-specialist
- **Purpose**: Handle external integrations and dependencies
- **Trigger keywords**: integrate, connect, API, dependency, external service
- **Combines with**: api-contract-designer, security-guardian

### Performance & Optimization

#### performance-optimizer
- **Purpose**: Profile and optimize code performance
- **Trigger keywords**: slow, performance, optimize, speed up, bottleneck
- **Combines with**: database-architect, integration-specialist

#### database-architect
- **Purpose**: Design database schemas and optimize queries
- **Trigger keywords**: database, schema, query, SQL, storage
- **Combines with**: performance-optimizer, zen-architect

### Security & Quality

#### security-guardian
- **Purpose**: Perform security reviews and vulnerability assessments
- **Trigger keywords**: security, auth, password, token, deploy, production
- **Combines with**: integration-specialist, api-contract-designer

#### api-contract-designer
- **Purpose**: Design REST/GraphQL APIs and specifications
- **Trigger keywords**: API, endpoint, contract, REST, GraphQL
- **Combines with**: zen-architect, security-guardian

### Knowledge Synthesis

#### concept-extractor
- **Purpose**: Extract atomic concepts from documents
- **Trigger keywords**: extract, concepts, analyze document
- **Combines with**: insight-synthesizer, pattern-emergence

#### insight-synthesizer
- **Purpose**: Find breakthrough connections between concepts
- **Trigger keywords**: synthesize, connect, breakthrough, innovation
- **Combines with**: concept-extractor, pattern-emergence

#### knowledge-archaeologist
- **Purpose**: Trace evolution of ideas over time
- **Trigger keywords**: history, evolution, timeline, past
- **Combines with**: concept-extractor, visualization-architect

#### visualization-architect
- **Purpose**: Transform data into visual representations
- **Trigger keywords**: visualize, graph, diagram, chart
- **Combines with**: All knowledge synthesis agents

#### pattern-emergence
- **Purpose**: Detect emergent patterns from diverse perspectives
- **Trigger keywords**: patterns, emergence, meta-analysis
- **Combines with**: insight-synthesizer, ambiguity-guardian

#### ambiguity-guardian
- **Purpose**: Preserve productive tensions and contradictions
- **Trigger keywords**: contradiction, paradox, uncertainty, ambiguity
- **Combines with**: pattern-emergence, concept-extractor

### Analysis & Research

#### analysis-engine
- **Purpose**: Multi-mode analysis (DEEP, SYNTHESIS, TRIAGE)
- **Trigger keywords**: analyze, review, check, evaluate
- **Modes**: DEEP (thorough), SYNTHESIS (combine), TRIAGE (filter)
- **Combines with**: All agents for comprehensive analysis

#### content-researcher
- **Purpose**: Research content from files and documentation
- **Trigger keywords**: research, find, search, what is
- **Combines with**: concept-extractor, knowledge-archaeologist

#### graph-builder
- **Purpose**: Build multi-perspective knowledge graphs
- **Trigger keywords**: graph, network, relationships, connections
- **Combines with**: concept-extractor, visualization-architect

### Meta Agents

#### subagent-architect
- **Purpose**: Create new specialized agents
- **Trigger keywords**: new agent, create agent, need specialist
- **Special**: Creates other agents

#### amplifier-cli-architect
- **Purpose**: Expert on Amplifier CLI Tools and hybrid architectures
- **Trigger keywords**: amplifier tool, CLI, hybrid architecture
- **Modes**: CONTEXTUALIZE, GUIDE, VALIDATE
- **Combines with**: zen-architect, modular-builder

#### post-task-cleanup
- **Purpose**: Clean up after task completion
- **Trigger keywords**: completed, finished, done, cleanup
- **Combines with**: Runs after any task completion

## ❌ Missing Agents (12)

These agents are referenced in orchestration files but not yet implemented:

### High Priority (Frequently Referenced)

#### root-cause-analyzer ⚠️
- **Purpose**: Perform systematic root cause analysis
- **Referenced in**: Bug fixing workflows, debugging patterns
- **Would combine with**: bug-hunter, performance-optimizer

#### code-review-specialist ⚠️
- **Purpose**: Comprehensive code review and quality assessment
- **Referenced in**: All code modification workflows
- **Would combine with**: zen-architect, security-guardian

#### system-architecture-advisor ⚠️
- **Purpose**: Advise on system-level architecture decisions
- **Referenced in**: Design and architecture workflows
- **Would combine with**: zen-architect, api-contract-designer

#### refactor-architect ⚠️
- **Purpose**: Design and guide refactoring efforts
- **Referenced in**: Code improvement workflows
- **Would combine with**: zen-architect, code-review-specialist

### Medium Priority

#### devops-strategy-consultant
- **Purpose**: CI/CD and deployment strategy
- **Referenced in**: Deployment and production workflows
- **Would combine with**: security-guardian, integration-specialist

#### cache-specialist
- **Purpose**: Design and optimize caching strategies
- **Referenced in**: Performance optimization workflows
- **Would combine with**: performance-optimizer, database-architect

#### architecture-reviewer
- **Purpose**: Review architectural decisions
- **Referenced in**: Design validation workflows
- **Would combine with**: system-architecture-advisor, zen-architect

### Lower Priority (Knowledge Synthesis)

#### triage-specialist
- **Purpose**: Rapid filtering of large content volumes
- **Referenced in**: AGENTS.md
- **Would combine with**: analysis-engine

#### analysis-expert
- **Purpose**: Deep analysis mode specialist
- **Referenced in**: AGENTS.md
- **Would combine with**: analysis-engine

#### synthesis-master
- **Purpose**: Combine multiple sources
- **Referenced in**: AGENTS.md
- **Would combine with**: insight-synthesizer

#### tension-keeper
- **Purpose**: Preserve productive tensions
- **Referenced in**: AGENTS.md
- **Would combine with**: ambiguity-guardian

#### uncertainty-navigator
- **Purpose**: Navigate areas of uncertainty
- **Referenced in**: AGENTS.md
- **Would combine with**: ambiguity-guardian

## Agent Combination Patterns

### The "Full Stack" (Feature Development)
```
zen-architect → modular-builder → test-coverage → code-review-specialist* → security-guardian
```

### The "Debug Squad" (Issue Resolution)
```
bug-hunter → root-cause-analyzer* → test-coverage → performance-optimizer
```

### The "Knowledge Team" (Research & Analysis)
```
content-researcher → concept-extractor → insight-synthesizer → pattern-emergence
```

### The "Architecture Board" (System Design)
```
zen-architect → system-architecture-advisor* → api-contract-designer → database-architect
```

### The "Performance Team" (Optimization)
```
performance-optimizer → database-architect → cache-specialist* → integration-specialist
```

### The "Security Review" (Pre-deployment)
```
security-guardian → code-review-specialist* → devops-strategy-consultant* → test-coverage
```

*Agents marked with * are not yet implemented

## Usage Guidelines

1. **Always spawn agents in parallel** when possible
2. **Use at least 2-3 agents** for non-trivial tasks
3. **Combine complementary agents** for comprehensive solutions
4. **Create new agents** when existing ones don't fit

## Creating New Agents

To create a new agent:
1. Identify a specific, focused need
2. Use the `subagent-architect` agent
3. Define clear trigger keywords
4. Document combination patterns
5. Update this catalog

## Agent Health Status

| Status | Count | Description |
|--------|-------|-------------|
| ✅ Implemented | 21 | Ready to use |
| ⚠️ High Priority Missing | 4 | Critical for workflows |
| 🟡 Medium Priority Missing | 3 | Important but not critical |
| 🔵 Low Priority Missing | 5 | Nice to have |

**Total Coverage: 21/33 (64%)**

## Next Steps

1. Implement the 4 high-priority missing agents
2. Add agent capability matrix showing dependencies
3. Create agent performance metrics
4. Build agent health monitoring system