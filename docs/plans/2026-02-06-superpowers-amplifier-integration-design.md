# Superpowers + Amplifier v2 Integration Design

**Date:** 2026-02-06
**Status:** Approved

## Goal

Fork the superpowers plugin and deeply integrate Amplifier v2's 30 specialized agents into 4 key skills, making brainstorming the central session hub.

## Architecture

Fork `obra/superpowers` to `psklarkins/superpowers`. Modify 4 skill files and add 1 shared reference file. Install as local plugin. Core superpowers discipline (TDD, verification, red flags) stays untouched — we add agent awareness, not rewrite workflows.

## Agent Task-Type Mapping

The core of the integration. All 4 skills consult this shared mapping.

| Task Type | Amplifier Agent | When |
|-----------|----------------|------|
| Architecture/Design | `zen-architect` | Planning, system design, module specs |
| Implementation | `modular-builder` | Building code from specs |
| Testing | `test-coverage` | Test strategy, writing tests, gap analysis |
| Debugging | `bug-hunter` | Failures, errors, unexpected behavior |
| Security Review | `security-guardian` | Pre-deploy, auth, data handling |
| Integration | `integration-specialist` | External APIs, MCP servers, dependencies |
| Performance | `performance-optimizer` | Bottlenecks, optimization |
| Cleanup | `post-task-cleanup` | Post-implementation hygiene |
| UI/Component | `component-designer` | Frontend components |
| API Design | `api-contract-designer` | Endpoint specs, contracts |
| Database | `database-architect` | Schema, migrations, queries |

**Detection heuristics** — skills match tasks by keywords: "implement/build/create" -> modular-builder; "test/coverage/verify" -> test-coverage; "fix/debug/error" -> bug-hunter; "security/auth/secrets" -> security-guardian; etc.

## Skill Changes

### 1. Brainstorming (Session Hub)

Brainstorming becomes the central starting point for most sessions.

**New session-start responsibilities:**
- **Context gathering** — project state, recent commits, open branches, existing plans
- **Agent awareness priming** — surface which Amplifier agents are relevant for the task
- **Memory consultation** — check episodic memory for related past conversations and decisions
- **Workflow routing** — after design validation, recommend the right execution path:
  - Simple task -> implement directly with modular-builder
  - Medium task -> write plan -> subagent-driven-development
  - Complex task -> write plan -> parallel agents for independent pieces
  - Investigation -> dispatch bug-hunter or parallel specialists

**Agent-informed design exploration:**
- When exploring approaches, identify which specialists are relevant
- Knowing security-guardian exists means security gets a dedicated task, not sprinkled comments

**Design output gains Agent Allocation section:**
```markdown
## Agent Allocation

| Phase | Agent | Responsibility |
|-------|-------|---------------|
| Architecture | zen-architect | System design, module boundaries |
| Implementation | modular-builder | Build from specs |
| Testing | test-coverage | Test strategy and coverage |
| Security | security-guardian | Pre-deploy review |
| Cleanup | post-task-cleanup | Final hygiene pass |
```

### 2. Writing-Plans

Each task gains an `Agent:` field, auto-assigned by task type.

**Updated task template:**
```markdown
### Task N: [Component Name]

**Agent:** modular-builder
**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Step 1: Write the failing test**
[Complete code]
...
```

**Review tasks get explicit agents:**
```markdown
### Task N+1: Security Review

**Agent:** security-guardian
**Scope:** Review Tasks 1-N for OWASP Top 10, secret detection, auth patterns
**Output:** Security findings with file:line references
```

**Execution handoff updated:**
```markdown
> **For Claude:** Use superpowers:subagent-driven-development to execute.
> Each task specifies its Agent — dispatch that Amplifier agent as the
> subagent for implementation. Use test-coverage for spec compliance
> review and security-guardian for security-sensitive tasks.
```

### 3. Subagent-Driven-Development

Dispatches the specific Amplifier agent named in each task instead of generic subagents.

**Changed dispatch flow:**
1. Read task from plan — note the `Agent:` field
2. Dispatch that Amplifier agent via Task tool
3. Pass full task text + context (never make subagent read the file)
4. Agent executes, tests, commits, self-reviews
5. Two-stage review with Amplifier agents:
   - Spec compliance -> `test-coverage` agent
   - Code quality -> `zen-architect` in REVIEW mode
   - Security-sensitive -> add `security-guardian` as third reviewer

**Agent-specific implementer prompts:**
```markdown
You are the modular-builder agent implementing Task 3: User Authentication

## Your Strengths
You build self-contained, regeneratable modules following the "bricks and
studs" philosophy. Focus on clean contracts, complete implementation, and
modular boundaries.

## Task Description
[FULL TEXT from plan]
...
```

**Parallel review safety:** spec-compliance and security reviews CAN run in parallel (both read-only). Implementation agents CANNOT overlap on same files.

**Post-task cleanup:** After all tasks pass review, dispatch `post-task-cleanup` before finishing-a-development-branch.

### 4. Dispatching-Parallel-Agents

Selects the right Amplifier specialist per investigation domain.

**Domain-to-agent mapping:**
- Test failures -> `bug-hunter`
- Performance issues -> `performance-optimizer`
- Security findings -> `security-guardian`
- Integration breakage -> `integration-specialist`
- UI regressions -> `component-designer`

**Example dispatch:**
```
Single message, three parallel Task calls:
- Task bug-hunter: "Fix 3 failing tests in auth.test.ts"
- Task integration-specialist: "API connection failures to payment service"
- Task performance-optimizer: "Response time regression in /api/search"
```

### 5. Using-Superpowers (Minor Update)

Points to brainstorming as the recommended starting point for any creative or implementation work.

## Files to Change

| File | Changes |
|------|---------|
| `skills/brainstorming/SKILL.md` | Agent allocation, session hub, memory consultation, workflow routing |
| `skills/writing-plans/SKILL.md` | `Agent:` field in task template, auto-assignment, review agent mapping |
| `skills/subagent-driven-development/SKILL.md` | Agent-specific dispatch, Amplifier reviewers, post-task-cleanup step |
| `skills/dispatching-parallel-agents/SKILL.md` | Specialist selection by domain, examples |
| `skills/using-superpowers/SKILL.md` | Point to brainstorming as session start |
| `AMPLIFIER-AGENTS.md` (NEW) | Shared agent mapping table referenced by all skills |

## What We Don't Change

- Core discipline enforcement (TDD, verification, red flags, iron laws)
- The other 9 skills (they work fine as-is)
- Plugin structure or metadata
- Skill frontmatter format
- Superpowers philosophy (evidence before claims, root cause before fixes)

## Workflow Summary

```
brainstorm (session hub)
  -> design with agent awareness
  -> write plan with Agent: fields
  -> execute via subagent-driven-dev (dispatches Amplifier agents)
     -> two-stage review (test-coverage + zen-architect)
     -> post-task-cleanup
  -> finish development branch
```
