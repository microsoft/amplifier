# Amplifier Agents Inventory - Baseline

**Generated**: 2025-11-06
**Purpose**: Inventory of all specialized agents in `.claude/agents/`
**Status**: 30 agents documented ✅

---

## Quick Overview

**Total Agents**: 30
**Categories**: 5 (Development, Design, Knowledge, Architecture, Meta)
**Model**: Inherit from project config
**Status**: All active and documented

---

## Core Development Agents (6)

1. **zen-architect** - Architecture design & code planning (ANALYZE/ARCHITECT/REVIEW modes)
2. **modular-builder** - Implementation from specifications (Bricks & Studs pattern)
3. **bug-hunter** - Systematic debugging & root cause analysis
4. **test-coverage** - Test strategy & gap analysis
5. **security-guardian** - Security review & vulnerability assessment
6. **integration-specialist** - System integration & API coordination

**Pattern**: zen-architect designs → modular-builder implements → bug-hunter validates → test-coverage ensures coverage → security-guardian reviews

---

## Design & UX Agents (8)

1. **design-system-architect** - Design tokens & system foundation
2. **component-designer** - Individual component design
3. **animation-choreographer** - Motion design & timing
4. **art-director** - Visual direction & aesthetic
5. **layout-architect** - Layout systems & spatial design
6. **responsive-strategist** - Multi-device strategies
7. **visualization-architect** - Data visualization
8. **voice-strategist** - Tone & copy design

**Collaboration**: Tokens → Components → Motion → Visual → Responsive → Layout → Data → Copy

---

## Knowledge Synthesis Agents (6)

1. **concept-extractor** - Atomic concept extraction from articles
2. **insight-synthesizer** - Cross-domain pattern discovery
3. **knowledge-archaeologist** - Deep knowledge mining
4. **analysis-engine** - Multi-dimensional analysis
5. **content-researcher** - Research compilation
6. **contract-spec-author** - Technical specification writing

**Flow**: Extract → Mine patterns → Structure → Synthesize → Research → Formalize

---

## Architecture & Infrastructure Agents (5)

1. **api-contract-designer** - API design & contracts
2. **database-architect** - Database design & schema
3. **module-intent-architect** - Module purpose & boundaries
4. **graph-builder** - Knowledge graph construction
5. **performance-optimizer** - Performance tuning

**Use**: Information → API design / DB design → Implementation → Tuning

---

## Meta & Orchestration Agents (3)

1. **subagent-architect** - New agent definition & design (only agent that creates agents)
2. **amplifier-cli-architect** - CLI tool pattern expertise (CONTEXTUALIZE/GUIDE/VALIDATE modes)
3. **pattern-emergence** - Multi-perspective orchestration & pattern detection

**Role**: System-level management, agent creation, tool patterns, output synthesis

---

## Utility & Governance Agents (2)

1. **post-task-cleanup** - Codebase hygiene & artifact removal
2. **ambiguity-guardian** - Clarification & requirement disambiguation

---

## Key Patterns

**Parallel Execution**: Independent agents work simultaneously
**Sequential Dependencies**: Specs → Implementation → Testing → Review
**Collaboration**: Agents delegate to each other (zen-architect → modular-builder)
**Philosophy Alignment**: All agents respect @IMPLEMENTATION_PHILOSOPHY.md

---

## Agent Selection Framework

```
Code problem? → bug-hunter
Design problem? → design-system-architect or component-designer
Planning/architecture? → zen-architect
Implementation from spec? → modular-builder
Knowledge/synthesis? → concept-extractor, insight-synthesizer
Security/infrastructure? → security-guardian, api-contract-designer
Task complete? → post-task-cleanup
```

---

## File Locations

```
.claude/agents/
├── zen-architect.md
├── modular-builder.md
├── bug-hunter.md
├── test-coverage.md
├── design-system-architect.md
├── component-designer.md
├── animation-choreographer.md
├── concept-extractor.md
├── insight-synthesizer.md
├── subagent-architect.md
├── amplifier-cli-architect.md
└── [25 more agents...]
```

---

**Status**: Complete baseline ✅
**Reference**: Full 50-page comprehensive report available in agent findings
