# Agent Resilience + Retro Schema — Design Spec

**Date:** 2026-03-18
**Status:** Approved for implementation

---

## Problem

Amplifier's agent dispatch has three concrete gaps:

1. **Retro output is unstructured.** `/retro` emits free-form text. No trend tracking, no historical queries, no way to compare session smoothness over time.
2. **Failure classification is ad-hoc.** The existing Subagent Resilience Protocol uses an imperative checklist ("is it a hard failure? timeout? incomplete?") with no shared taxonomy. Orchestrators re-derive the same logic in every session.
3. **No loop detection.** An agent can repeat the same failing tool call indefinitely within its turn budget, burning turns with no progress and returning a context_overflow result that obscures the real cause.

---

## Goal

Cherry-pick three patterns from Fabro (open-source workflow orchestration) into Amplifier's existing architecture:

1. **Failure taxonomy** — six named classes with explicit retry/resume rules, added to AGENTS.md.
2. **Loop detection** — pattern-based detection on the last 10 tool calls, with steering injection and hard stop, added to AGENTS.md.
3. **Structured retro schema** — friction recorded per agent via the existing SubagentStop hook; `/retro` computes a smoothness rating and writes to `recall-index.sqlite`.

All changes integrate into existing infrastructure. No new tools, hooks, or external dependencies are introduced.

---

## Changes

### Change 1: Failure Classification Taxonomy

**Location:** `AGENTS.md`, inside Subagent Resilience Protocol, after the Resume Protocol section.

Add a six-class failure taxonomy table and decision tree. Claude reads this and applies it when evaluating agent results — no code changes needed.

**Taxonomy:**

| Class | Trigger | Retry? | Resume? |
|-------|---------|--------|---------|
| `transient` | API 500, rate limit, timeout, network error | Yes (auto, up to 3×) | No |
| `deterministic` | Wrong path, missing module, bad syntax | No | No — fix the prompt |
| `context_overflow` | Turn limit hit, context window full | No | Yes (reduced scope) |
| `stuck_loop` | Same action repeated 3+ times (see Change 2) | No | No — escalate |
| `canceled` | User interrupt, hook kill | No | No |
| `scope_violation` | Write in read-only mode, wrong directory | No | No — fix constraints |

**Decision tree for the orchestrator:**

1. Classify the failure using the table above.
2. `transient` → wait briefly, retry (up to 3 times). If 3rd retry fails, escalate to user.
3. `context_overflow` → resume with reduced scope (invoke Resume Protocol).
4. `deterministic` → report to user with the specific error message and a prompt-fix suggestion. Do not retry.
5. `stuck_loop` → terminate the agent, report the repeating pattern to the user.
6. `canceled` → report, do not retry.
7. `scope_violation` → report with the constraint that was violated, do not retry.

### Change 2: Tool Call Loop Detection

**Location:** `AGENTS.md`, new subsection under Subagent Resilience Protocol, after the Synthesis Guard section.

**Pattern detection — check the last 10 tool calls for:**

| Pattern | Definition |
|---------|------------|
| Length-1 repeat | Same tool + identical arguments, 3+ consecutive times |
| Length-2 cycle | A→B→A→B with identical inputs each iteration |
| Length-3 cycle | A→B→C→A→B→C with identical inputs each iteration |

**What does NOT count as a loop:**
- Reading different files (same tool, different arguments — no match).
- Retrying a tool call after making a code change (edit content differs — no match).
- Running tests after each edit (test output differs — no match).
- Key signal: identical inputs producing the same (failed) output.

**Response protocol:**

1. **First detection:** Inject steering via SendMessage to the agent: "Loop detected: you are repeating [tool + argument pattern]. Stop and try a different approach."
2. **Second detection in the same agent session:** Hard stop. Classify as `stuck_loop`. Report to user with the exact repeating pattern and a recommended next action.
3. Loop steering injection counts as 1 of the 3 allowed resume cycles. Second detection terminates the agent regardless of remaining resume cycles.

### Change 3A: Friction Recording (hook_stop.py)

**Location:** `.claude/tools/hook_stop.py` (existing SubagentStop hook).

On every SubagentStop event, append one JSON line to `tmp/friction.jsonl`. This file is session-scoped and cleared at session start.

**Schema for one friction record:**

```json
{
  "ts": "2026-03-18T14:23:01Z",
  "agent": "amplifier-core:modular-builder",
  "model": "sonnet",
  "status": "failed",
  "failure_class": "deterministic",
  "friction_kind": "wrong_approach",
  "resume_count": 2,
  "loop_detected": false,
  "turns_used": 18,
  "description": "Agent tried to edit nonexistent file 3 times"
}
```

**Field definitions:**

| Field | Type | Values |
|-------|------|--------|
| `ts` | ISO 8601 string | UTC timestamp |
| `agent` | string | `plugin:agent-name` |
| `model` | string | `haiku`, `sonnet`, `opus` |
| `status` | string | `success`, `failed`, `canceled` |
| `failure_class` | string or null | See taxonomy (null on success) |
| `friction_kind` | string or null | `retry`, `timeout`, `wrong_approach`, `tool_failure`, `ambiguity`, `loop` (null on success) |
| `resume_count` | integer | 0–3 |
| `loop_detected` | boolean | true if loop pattern triggered |
| `turns_used` | integer | Turns consumed before stop |
| `description` | string | One-sentence human-readable summary |

Success entries are also recorded (status: `success`; `failure_class` and `friction_kind` are null).

### Change 3B: Smoothness Heuristic (/retro command)

**Location:** `amplifier-core/commands/retro.md` (in `amplifier-plugins` repo).

The `/retro` command reads `tmp/friction.jsonl`, computes a smoothness rating, and writes a structured record to SQLite. The heuristic is deterministic:

| Rating | Condition |
|--------|-----------|
| `Effortless` | All agents succeeded, 0 friction entries |
| `Smooth` | All goals met, ≤2 retries total, 0 loops detected |
| `Bumpy` | Goals met, but 3+ retries OR 1 loop detection |
| `Struggled` | Goals met, but resume cycles exhausted OR 2+ loops detected |
| `Failed` | Unresolved agent failures; user had to take over |

Conditions are evaluated in order; first match wins. "Goals met" is determined by whether any agent ended with `status: failed` and no subsequent successful re-attempt.

### Change 3C: Retro Table in recall-index.sqlite

**Location:** `scripts/recall/index-all.py` (schema init section).

Add table creation:

```sql
CREATE TABLE IF NOT EXISTS retros (
  id              INTEGER PRIMARY KEY,
  session_id      TEXT NOT NULL,
  timestamp       TEXT NOT NULL,
  smoothness      TEXT NOT NULL,
  total_agents    INTEGER,
  successful_agents INTEGER,
  total_retries   INTEGER,
  loops_detected  INTEGER,
  friction_points TEXT,
  learnings       TEXT,
  open_items      TEXT,
  UNIQUE(session_id)
);
```

`friction_points`, `learnings`, and `open_items` are stored as JSON strings.

**Learnings categories:** `repo`, `code`, `workflow`, `tool`
**Open items kinds:** `tech_debt`, `follow_up`, `investigation`, `test_gap`

---

## Files Changed

| File | Repo | Change |
|------|------|--------|
| `AGENTS.md` | `claude/amplifier` | Add ~60 lines: failure taxonomy table + decision tree + loop detection protocol, inside Subagent Resilience Protocol |
| `.claude/tools/hook_stop.py` | `claude/amplifier` | Add ~30 lines: append one JSON record to `tmp/friction.jsonl` on every SubagentStop event |
| `scripts/recall/index-all.py` | `claude/amplifier` | Add ~10 lines: `retros` table creation in schema init |
| `amplifier-core/commands/retro.md` | `claude/amplifier-plugins` | Rewrite retro command: parse `tmp/friction.jsonl`, compute smoothness, emit structured output, write to `recall-index.sqlite` |

---

## Agent Allocation

| Phase | Agent | Responsibility |
|-------|-------|----------------|
| AGENTS.md protocol update | `amplifier-core:modular-builder` | Write failure taxonomy table, decision tree, and loop detection subsection into AGENTS.md |
| hook_stop.py friction logging | `amplifier-core:modular-builder` | Add JSON-append logic to existing SubagentStop hook; handle missing `tmp/` directory gracefully |
| Retro schema + SQLite table | `amplifier-core:database-architect` | Add `retros` table DDL to `scripts/recall/index-all.py` schema init; verify no conflict with existing tables |
| Retro command update | `amplifier-core:modular-builder` | Parse `tmp/friction.jsonl`, apply smoothness heuristic, emit structured markdown output, write record to `recall-index.sqlite` via existing connection pattern |
| Verification | `amplifier-core:test-coverage` | Verify hook appends valid JSON, retro reads and parses correctly, smoothness ratings resolve deterministically, SQLite write succeeds |

---

## Test Plan

### Hook output (hook_stop.py)

1. Trigger a SubagentStop event (run any short agent task to completion).
2. Confirm `tmp/friction.jsonl` exists and contains exactly one valid JSON line per agent invocation.
3. Confirm all required fields are present and correctly typed.
4. Confirm a success entry has `failure_class: null` and `friction_kind: null`.
5. Simulate a `deterministic` failure; confirm `failure_class` is set to `"deterministic"`.
6. Confirm `tmp/friction.jsonl` is cleared at session start (not carried over from prior session).

### Smoothness heuristic (/retro)

7. Synthesize a `friction.jsonl` with 0 entries → expect rating `Effortless`.
8. Synthesize with 2 retries, 0 loops, all success → expect `Smooth`.
9. Synthesize with 3 retries, 0 loops, all goals met → expect `Bumpy`.
10. Synthesize with 1 loop detection, goals met → expect `Bumpy`.
11. Synthesize with exhausted resume cycles (resume_count=3 on any entry) → expect `Struggled`.
12. Synthesize with 2 loop detections → expect `Struggled`.
13. Synthesize with an unresolved `status: failed` entry → expect `Failed`.

### SQLite write (/retro)

14. Run `/retro` with a non-empty `friction.jsonl`. Confirm `retros` table exists in `recall-index.sqlite`.
15. Confirm the inserted row's `session_id` matches the current session.
16. Run `/retro` again for the same session; confirm `UNIQUE(session_id)` constraint triggers an upsert (not duplicate insert).
17. Query `SELECT smoothness, total_agents, loops_detected FROM retros ORDER BY timestamp DESC LIMIT 5` and confirm values match the synthesized input.

### Loop detection (AGENTS.md protocol — behavioral test)

18. In a test agent session, inject a tool call trace with a length-1 repeat (same tool + arguments, 3 times). Confirm orchestrator injects steering message on first detection.
19. Inject a second loop detection in the same session. Confirm agent is terminated and classified as `stuck_loop`.
20. Inject a length-2 A→B→A→B cycle with identical inputs. Confirm detection triggers.
21. Inject tool calls reading different files with the same tool. Confirm no false positive.

---

## Acceptance Criteria

All criteria are pass/fail with no ambiguity:

- `tmp/friction.jsonl` contains one valid JSON record per agent stop, with all required fields present and typed correctly.
- `/retro` smoothness output matches the deterministic heuristic table for all seven test cases (items 7–13 above).
- `retros` table exists in `recall-index.sqlite` after first `/retro` run.
- Running `/retro` twice for the same session does not insert duplicate rows.
- Loop steering message is injected on first detection; agent is terminated on second detection in the same session.
- No new external dependencies are introduced; no new hooks are registered.
