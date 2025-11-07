# Amplifier Commands Inventory - Baseline

**Generated**: 2025-11-06
**Purpose**: Inventory of all slash commands in `.claude/commands/`
**Status**: 19 commands documented ✅

---

## Quick Overview

**Total Commands**: 19
**Categories**: 2 (DDD Workflow: 8, Utilities: 11)
**Status**: All active and documented

---

## DDD Workflow Commands (8)

### Core Workflow
1. `/ddd:0-help` - Complete DDD workflow guide
2. `/ddd:prime` - Load DDD context for session
3. `/ddd:status` - Check current DDD progress
4. `/ddd:1-plan` - Phase 1: Planning & design
5. `/ddd:2-docs` - Phase 2: Documentation updates
6. `/ddd:3-code-plan` - Phase 3: Code implementation planning
7. `/ddd:4-code` - Phase 4: Implementation & verification
8. `/ddd:5-finish` - Phase 5: Cleanup & finalization

**Pattern**: Structured 5-phase feature development with docs as specification

---

## Utility Commands (11)

### Git & Version Control
- `/commit` - Well-formatted conventional commits

### Code Review & Analysis
- `/review-changes` - Review code since last commit
- `/review-code-at-path <path>` - Targeted philosophical review

### Task Orchestration
- `/ultrathink-task <task>` - Orchestrate sub-agents for complex tasks
- `/create-plan` - Generate implementation plan
- `/execute-plan <plan_path>` - Execute implementation plan

### Session Management
- `/transcripts [query]` - Restore/manage conversation transcripts
- `/prime` - Prime environment and verify setup

### Modular Development
- `/modular-build <ask>` - Generate complete modules from natural language

### Design & UI
- `/designer <task>` - Transform design ideas into refined solutions
- `/test-webapp-ui <url>` - Test web application UI

---

## Key Integration Patterns

**Context Loading**: All commands load @philosophy and @methodology docs
**Sub-Agent Delegation**: Commands spawn specialized agents (zen-architect, modular-builder, etc.)
**Task Tracking**: Most commands use TodoWrite for progress tracking
**Iteration Support**: Phases 2 & 4 iterate until user approves
**Authorization Gates**: Critical operations require explicit user approval

---

## File Locations

```
.claude/commands/
├── commit.md
├── create-plan.md
├── designer.md
├── ddd/
│   ├── 0-help.md
│   ├── 1-plan.md
│   ├── 2-docs.md
│   ├── 3-code-plan.md
│   ├── 4-code.md
│   ├── 5-finish.md
│   ├── prime.md
│   └── status.md
├── execute-plan.md
├── modular-build.md
├── prime.md
├── review-changes.md
├── review-code-at-path.md
├── test-webapp-ui.md
├── transcripts.md
└── ultrathink-task.md
```

---

## Common Workflows

**Full Feature Development**:
```
/ddd:prime → /ddd:1-plan → /ddd:2-docs → 
/ddd:3-code-plan → /ddd:4-code → /ddd:5-finish
```

**Quick Task**:
```
/ultrathink-task → /commit
```

**Design Work**:
```
/designer → /test-webapp-ui → /commit
```

---

**Status**: Complete baseline ✅
**Reference**: Full 62-page report available in agent findings
