# Subagent Resilience Protocol - Design Specification

**Date:** 2026-02-14
**Status:** Validated Design
**Authors:** Claude Code Team

## Problem

Subagents launched via the Task tool can exhaust their context window during execution. Two failure modes occur:

1. **Abrupt stop with partial results** - Agent reaches context limit and returns incomplete work
2. **Summary mode fallback** - Model shifts to summarizing instead of completing actual work

Recent context budget guardrails help agents avoid generating excessive context, but don't protect against incoming context pressure from:
- Large file reads
- Verbose tool results
- Tasks too big for one agent pass

## Goals

1. **Mechanical safety net** - Prevent agents from reaching the "conservation instinct" threshold by using max_turns to stop them before pressure builds
2. **Graceful continuation** - When an agent is stopped mid-task, use resume to continue with preserved context
3. **Upstream prevention** - Improve how skills decompose work before dispatch so each agent gets a right-sized task
4. **No new infrastructure** - Work entirely within existing Task tool capabilities (max_turns, resume, prompt design)

## Non-Goals

- Modifying Claude Code internals or the Task tool itself
- Building a custom orchestration framework
- Changing agent definitions (budget guardrails already added are sufficient)
- Handling the main conversation's context pressure (separate concern)

## Solution

### Part 1: max_turns + Resume Pattern

#### Turn Budgets by Agent Role

| Agent Role | max_turns | Rationale |
|------------|-----------|-----------|
| Research / exploration | 8-10 | Reads files, returns findings. Low output. |
| Analysis (zen-architect, bug-hunter) | 12-15 | Reads + reasons. Moderate output. |
| Implementation (modular-builder) | 15-20 | Reads + writes files. High tool usage. |
| Review (test-coverage, security-guardian) | 10-12 | Reads + evaluates. Moderate. |
| Quick tasks (haiku scouts, context gathering) | 5-8 | Small, focused jobs. |

#### Resume Protocol

1. **Dispatch** agent with max_turns=N
2. **Agent returns** result + agent_id
3. **Orchestrator evaluates** - Is the work complete?
   - **Completion signals**: Files written, conclusions stated, explicit "done" markers
   - **Incompletion signals**: Trailing "I'll now...", partial lists, no conclusion, mid-sentence stops
4. **If incomplete** → resume(agent_id) with prompt: "Continue your work. You were stopped due to turn limits. Focus on completing the remaining items."
5. **Max 3 resume cycles** before escalating to user
6. **If complete** → Use the result normally

**Key principle:** The agent doesn't need to know about this pattern. It gets stopped, gets resumed with full prior context, continues. Each resume gets a fresh output budget.

### Part 2: Task Decomposition Guidelines

#### Task Sizing Rules

| Dimension | Guideline | Why |
|-----------|-----------|-----|
| Files to read | 3-5 per agent | Each file read consumes context. |
| Files to modify | 1-3 per agent | Writing is more context-intensive than reading. |
| Objective count | 1 per agent | Single clear deliverable. |
| Output scope | One component/module | A function, a class, a test file. |

#### Decomposition Heuristic

**Instead of this:**
- "Implement the authentication system" (too large)
- "Review all changed files" (unbounded scope)

**Do this:**
- Split into: token generation, middleware, login endpoint, session storage (4 agents)
- Split by concern: "review auth changes", "review API changes" (2 agents)

**Exception:** If a task is indivisible (single large file, atomic refactor), accept it but set generous max_turns and rely on the resume pattern.

#### Where These Rules Apply

- `writing-plans` skill - Each plan step must pass the sizing test
- `subagent-driven-development` - Validate sizing before dispatch
- `dispatching-parallel-agents` - Each parallel agent gets one focused task
- Any manual Task dispatch from the main conversation

## Implementation

### Files to Modify

| File | Action | What |
|------|--------|------|
| `AGENTS.md` | Edit | Add "Subagent Resilience Protocol" section with max_turns table, resume protocol, decomposition guidelines |
| `DISCOVERIES.md` | Edit | Document the finding: subagents experience context compaction causing abrupt stops and summary-mode fallback |

**No changes to:**
- Agent definition files (budget guardrails already sufficient)
- Superpowers skill files
- Infrastructure or frameworks

### Content Details

#### AGENTS.md Addition

Add new section "Subagent Resilience Protocol" after "Sub-Agent Optimization Strategy" with:
1. Turn budget table (research, analysis, implementation, review, quick tasks)
2. Resume protocol steps (dispatch, evaluate, resume, escalate)
3. Task decomposition rules (files to read/modify, objective count, output scope)
4. Decomposition heuristic with examples
5. Where rules apply (writing-plans, subagent-driven-development, etc.)

#### DISCOVERIES.md Addition

Add entry under date 2026-02-14:
- **Issue**: Subagents exhaust context window during execution
- **Root Cause**: Incoming context pressure (file reads, tool results, oversized tasks)
- **Solution**: max_turns budgets + resume pattern + task decomposition guidelines
- **Prevention**: Size tasks to 3-5 files read, 1-3 files modified, 1 objective per agent

## Agent Allocation

| Phase | Agent | Responsibility |
|-------|-------|---------------|
| Implementation | modular-builder | Edit AGENTS.md and DISCOVERIES.md per specification |
| Review | zen-architect | Validate guidance is clear, actionable, and aligns with philosophy |
| Cleanup | post-task-cleanup | Verify no stale content, files end with newlines |

## Git Workflow

1. Create branch `feature/subagent-resilience-protocol`
2. Edit `AGENTS.md` and `DISCOVERIES.md`
3. Commit with message: `docs: add subagent resilience protocol for context management`
4. Push to fork (psklarkins/amplifier or equivalent)
5. Create PR with summary of changes

## Test Plan

### Manual Validation Tests

1. **Intentional overload test**
   - Dispatch modular-builder with task: "Read and analyze all files in ai_context/ directory"
   - Set max_turns=10
   - Expected: Agent stops gracefully, resume continues work, completes within 3 cycles

2. **Large implementation test**
   - Dispatch modular-builder with task: "Implement complete authentication system with 4 endpoints"
   - Set max_turns=15
   - Expected: Agent returns partial work, resume picks up where it left off

3. **Research agent test**
   - Dispatch analysis-expert with task: "Analyze all files matching pattern **/*.md and extract key concepts"
   - Set max_turns=8
   - Expected: Agent processes subset, resume continues remainder

4. **Parallel decomposition test**
   - Use dispatching-parallel-agents to split large task per decomposition rules
   - Expected: Each agent completes its focused subtask without needing resume

### Acceptance Criteria

- [ ] Agent returns results or clearly signals incomplete state
- [ ] Resume continues work without context loss or repetition
- [ ] No silent truncation (agent either completes or explicitly states remaining work)
- [ ] No surprise summarization (agent does actual work, not just descriptions)
- [ ] Turn budgets prevent hitting hard context limits

### Observation Period

- Run protocol for 2 weeks
- Track: resume success rate, turn budget adequacy by role, decomposition effectiveness
- Tune: Adjust max_turns values based on observed completion rates

## Success Criteria

1. **Agents complete assigned work to conclusion** - OR clearly hand back with enough information for orchestrator to continue
2. **No more silent truncation** - Agents either finish or explicitly state what remains
3. **No surprise summarization** - Agents do the work, don't just describe what they would do
4. **Turn budgets are effective starting points** - Values may be tuned based on observation, but prevent context exhaustion
5. **Decomposition prevents oversized tasks** - Tasks passing the sizing test rarely need resume
6. **Resume works seamlessly** - Agents pick up where they left off without repetition or confusion

## References

- Task tool documentation: `.claude/docs/` (max_turns, resume parameters)
- Context budget guardrails: Added to 30 agents on 2026-02-06
- Related decisions: `ai_working/decisions/` (context management strategies)

## Revision History

| Date | Change | Author |
|------|--------|--------|
| 2026-02-14 | Initial design specification | Claude Code Team |
