---
description: "SIEM test auto-fix pipeline: run tests, classify failures, apply known patterns, dispatch agents for novel failures. Max 3 cycles. Never modifies application code."
---

# /test-siem — SIEM Test Auto-Fix Pipeline

## Overview

Runs tests across universal-siem-monorepo services, classifies failures by type, applies known fix patterns instantly, dispatches `bug-hunter` agents for novel failures, reruns, and reports. Persists every learned fix to `.fix-patterns.json` and auto-memory.

**Announce at start:** "Starting SIEM test pipeline..."

## Arguments

```
/test-siem                    # full stack (all services + frontend)
/test-siem backend            # all backend services
/test-siem frontend           # vitest + optional playwright
/test-siem log-service        # single service
/test-siem auth-service       # single service
/test-siem anomaly-service    # single service
/test-siem snort-service      # single service
/test-siem agents-service     # single service
/test-siem devices-service    # single service
/test-siem m365-service       # single service
/test-siem integration        # integration tests only
/test-siem --health           # pre-flight health check only, no test run
/test-siem --report           # generate report from last results.json, no test run
```

## Process Graph (Authoritative)

> When this graph conflicts with prose, follow the graph.

```dot
digraph test_siem {
  rankdir=TB;

  "preflight"    [label="Phase 0: Pre-flight\nDB + K8s health" shape=box];
  "health_ok"    [label="Critical checks\ngreen?" shape=diamond];
  "abort"        [label="Print failing checks\nABORT" shape=box style=filled fillcolor=lightsalmon];
  "run_suite"    [label="Phase 1: Run suite\npytest / vitest per scope" shape=box];
  "parse"        [label="Phase 2: Parse results\nnormalize to unified JSON" shape=box];
  "any_fail"     [label="Failures > 0?" shape=diamond];
  "classify"     [label="Phase 3: Classify failures\n7 categories" shape=box];
  "patterns"     [label="Phase 4: Check known patterns\napply inline with Edit tool" shape=box];
  "agents"       [label="Phase 5: Dispatch bug-hunter\nper test file (max 3 parallel)" shape=box];
  "rerun"        [label="Phase 6: Rerun failing tests\ncheck for regression" shape=box];
  "cycle_check"  [label="Still failing?\nCycles < 3?" shape=diamond];
  "report"       [label="Phase 7: Generate report\nprint summary" shape=box style=filled fillcolor=lightgreen];

  "preflight"   -> "health_ok";
  "health_ok"   -> "abort"     [label="critical red"];
  "health_ok"   -> "run_suite" [label="green"];
  "run_suite"   -> "parse";
  "parse"       -> "any_fail";
  "any_fail"    -> "report"    [label="0 failures"];
  "any_fail"    -> "classify"  [label="failures exist"];
  "classify"    -> "patterns";
  "patterns"    -> "agents";
  "agents"      -> "rerun";
  "rerun"       -> "cycle_check";
  "cycle_check" -> "classify"  [label="yes — next cycle"];
  "cycle_check" -> "report"    [label="no more cycles or all fixed"];
}
```

---

## Platform Notes

This runs on **Linux** (mcp server, 172.31.250.2):

- **Working directory:** `/opt/monorepo-workspace/universal-siem-monorepo/`
- **Python:** Use `uv run pytest` (uv-managed environments per service)
- **Node:** Use `npm run test` from `frontend/`
- **K8s:** `kubectl` configured for local K3s cluster
- **DB:** PostgreSQL on `172.31.250.30:5432`

## Configuration

```
SIEM_ROOT=/opt/monorepo-workspace/universal-siem-monorepo
DB_HOST=172.31.250.30
DB_PORT=5432
DB_NAME=siem_timeseries
DB_USER=siem_user
DB_PASS=7oBuuQ1fmKQMjNI0Hro6s9RShMwCDOzc
K8S_NAMESPACE=siem-staging
RESULTS_DIR=$SIEM_ROOT/.test-siem
RESULTS_FILE=$SIEM_ROOT/.test-siem/results.json
PATTERNS_FILE=$SIEM_ROOT/.test-siem/.fix-patterns.json
```

Ensure `.test-siem/` directory exists before first run: `mkdir -p $SIEM_ROOT/.test-siem`

---

## Scope-to-Path Mapping

| Scope | Test Directory | Runner |
|-------|---------------|--------|
| `backend` | `backend/tests/` + all `backend/services/*/tests/` + `backend/auth-service/tests/` + `backend/m365-service/tests/` | pytest |
| `frontend` | `frontend/` | vitest |
| `log-service` | `backend/services/log-service/tests/` | pytest |
| `anomaly-service` | `backend/services/anomaly-service/tests/` | pytest |
| `snort-service` | `backend/services/snort-service/tests/` | pytest |
| `agents-service` | `backend/services/agents-service/tests/` | pytest |
| `devices-service` | `backend/services/devices-service/tests/` | pytest |
| `auth-service` | `backend/auth-service/tests/` | pytest |
| `m365-service` | `backend/m365-service/tests/` | pytest |
| `integration` | `tests/integration/api/` | pytest |
| (no arg) | backend then frontend | both |

---

## Phase 0: Pre-flight Health Check

```bash
# Database check
PGPASSWORD='7oBuuQ1fmKQMjNI0Hro6s9RShMwCDOzc' psql -U siem_user -h 172.31.250.30 -d siem_timeseries -c "SELECT 1" 2>&1

# K8s pod check
kubectl get pods -n siem-staging -o json | python3 -c "
import sys, json
data = json.load(sys.stdin)
for pod in data['items']:
    name = pod['metadata']['name']
    ready = any(c.get('status') == 'True' for c in pod.get('status', {}).get('conditions', []) if c.get('type') == 'Ready')
    print(f\"  {'✓' if ready else '✗'} {name}\")
"
```

**Decision logic:**
- DB unreachable → abort: "Database unreachable at 172.31.250.30:5432. Aborting."
- Pods not ready → warn for `integration` scope, continue for unit-only scopes
- `--health` flag → print full status table and stop

```
SIEM Health Check:
  database     ✓ reachable (172.31.250.30:5432)
  K8s pods     ✓ 13/13 ready (siem-staging)
Ready to run tests.
```

---

## Phase 1: Run Suite

Execute test commands based on scope. For each pytest scope:

```bash
cd $SIEM_ROOT/<service-path>
uv run pytest tests/ -v --tb=short --json-report --json-report-file=$SIEM_ROOT/.test-siem/pytest-report.json
```

For frontend:
```bash
cd $SIEM_ROOT/frontend
npm run test -- --run --reporter=json > $SIEM_ROOT/.test-siem/vitest-report.json 2>&1
```

For `backend` scope, run each service sequentially and merge results. Capture exit codes. Initialize cycle counter: `cycle = 1`.

---

## Phase 2: Parse Results

Read runner-specific JSON output and normalize into unified format in `.test-siem/results.json`:

```json
{
  "timestamp": "2026-03-16T13:00:00Z",
  "scope": "backend",
  "cycle": 1,
  "duration_s": 45,
  "summary": { "passed": 82, "failed": 7, "skipped": 3 },
  "failures": [
    {
      "test": "test_log_ingestion_bulk",
      "file": "backend/services/log-service/tests/test_ingestion.py",
      "service": "log-service",
      "error": "ModuleNotFoundError: No module named 'log_service.parsers.cef'",
      "traceback": "...",
      "class": null
    }
  ]
}
```

**Pytest JSON report mapping:**
- `tests[].nodeid` → `test` (function name) + `file` (path)
- `tests[].outcome` → passed/failed/skipped
- `tests[].call.longrepr` → `error` + `traceback`

**Vitest JSON mapping:**
- `testResults[].name` → `file`
- `testResults[].assertionResults[].title` → `test`
- `testResults[].assertionResults[].failureMessages` → `error`

Derive `service` from file path: `backend/services/<name>/` → `<name>`, `backend/auth-service/` → `auth-service`, `backend/m365-service/` → `m365-service`, `frontend/` → `frontend`.

Print quick tally:
```
Run 1 results: 82 passed, 7 failed, 3 skipped
Failures in: log-service (3), auth-service (2), anomaly-service (2)
```

If `failed === 0`: skip to Phase 7.

Group failing tests by file path.

---

## Phase 3: Classify Failures

For each failing test, examine `error` + `traceback` and classify using these patterns (evaluated in order, first match wins):

| Class | Regex Patterns |
|-------|---------------|
| `IMPORT_ERROR` | `ModuleNotFoundError`, `ImportError`, `Cannot find module`, `No module named` |
| `DB_SCHEMA` | `relation.*does not exist`, `UndefinedColumn`, `UndefinedTable`, `sqlalchemy.*OperationalError` |
| `AUTH_ERROR` | `status.*40[13]`, `token.*invalid`, `permission denied`, `AuthenticationError` |
| `ASYNC_TIMING` | `asyncio.*TimeoutError`, `Event loop`, `RuntimeError.*event loop`, `TimeoutError` |
| `INFRA_ERROR` | `ConnectionRefusedError`, `ConnectionError.*refused`, `pod.*not ready`, `ECONNREFUSED` |
| `ASSERTION` | `AssertionError`, `AssertionError`, `assert.*==`, `expect\(` |
| `UNKNOWN` | Anything else |

Classification populates each failure's `class` field in results.json.

Print classification summary:
```
Classifications: IMPORT_ERROR=3, ASSERTION=2, DB_SCHEMA=1, ASYNC_TIMING=1
INFRA_ERROR failures (0) will be reported but not auto-fixed.
```

Skip `INFRA_ERROR` failures from fix phases.

---

## Phase 4: Check Known Fix Patterns

Read `.test-siem/.fix-patterns.json` (create empty `[]` if not exists).

Also search episodic memory for learned patterns:
```
mcp__plugin_episodic-memory_episodic-memory__search(query="siem-test-fix pattern")
```

For each non-INFRA failure:
1. Test each pattern's `errorSignature` (treat as regex) against the failure's error text
2. If match: apply the fix described in `pattern.fix` directly using the Edit tool
3. Mark the test as `pattern-applied` with the pattern `id`

Track:
- `patterns_applied`: count of fixes applied from registry
- `pattern_ids_used`: list of matched pattern IDs

Print after this phase:
```
Pattern matches: 2 fixes applied (missing-cef-import x1, stale-auth-fixture x1)
Remaining for agent dispatch: 5 failures
```

---

## Phase 5: Dispatch Fix Agents

For failures not resolved by patterns, dispatch `bug-hunter` agents.

**Grouping:** one agent per test file. Max 3 parallel agents.

For each agent dispatch, build this context package:

```
FAILING TEST FILE: [read full content of the failing test file]
ERRORS: [paste error messages + tracebacks for all failures in this file]
SERVICE SOURCE: [read relevant source files from the service being tested]
  - log-service failures → backend/services/log-service/src/
  - auth-service failures → backend/auth-service/src/
  - anomaly-service failures → backend/services/anomaly-service/src/
  - frontend failures → frontend/src/ (relevant component)
CONFTEST: [read the service's test conftest.py for fixture context]
KNOWN PATTERNS: [paste .fix-patterns.json content as context]
REFERENCE TESTS: [read 1-2 passing test files from same service as examples]
```

Agent instruction (include verbatim):
> "You are fixing test files in universal-siem-monorepo. The application code is correct — the tests have drifted or have bugs. Fix the test file to match actual behavior. Do NOT modify any file outside of test directories. Only edit test files and test conftest files within the service's tests/ directory. When done, confirm which lines you changed and why."

Agent parameters:
- Agent: `bug-hunter` (role: implement → sonnet)
- `max_turns: 25`
- Include Subagent Resilience Protocol resume handling (see AGENTS.md)

---

## Phase 6: Rerun and Cycle

Rerun only the previously-failing test files:

```bash
cd $SIEM_ROOT/<service-path>
uv run pytest tests/test_specific_file.py -v --tb=short --json-report --json-report-file=$SIEM_ROOT/.test-siem/pytest-report.json
```

**Regression check:** Compare new results against previous run.
- If any previously-passing test now fails → a fix caused a regression
- Identify which test file was last edited, revert it: `git checkout HEAD -- <file>`
- Log: "Reverted fix to {file} — caused {N} regressions"

**Record successful fixes:**
For each test that went from failing to passing:
1. Find which test file was changed (git diff)
2. Add entry to `.test-siem/.fix-patterns.json`
3. Write memory entry (see Memory Recording section)

**Cycle decision:**
- If `failed === 0` or `cycle >= 3`: proceed to Phase 7
- Otherwise: `cycle++`, go to Phase 3 with remaining failures

Print cycle update:
```
Cycle 1 → Cycle 2: 3 failures remain after applying 4 fixes
```

---

## Phase 7: Report

Print terminal summary:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SIEM Test Results (/test-siem backend)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Passed: 89   Failed: 0   Skipped: 3
  Duration: 1m 32s

Fix Summary:
  Cycles run:        2
  Known patterns:    2 applied
  Agents dispatched: 3
  Regressions:       0

Remaining failures: none
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

If failures remain after max cycles:
```
NEEDS ATTENTION — 2 failures after 3 cycles:
  - backend/services/log-service/tests/test_parsers.py::test_cef_v2 → UNKNOWN (no pattern match)
  - backend/auth-service/tests/test_rbac.py::test_tenant_isolation → INFRA_ERROR (DB unreachable)
```

If `--report` flag: read existing `results.json`, print summary, stop (no test run or fixes).

---

## Memory Recording

After each successful agent fix (not pattern fixes), write a memory entry.

Memory file path: `~/.claude/projects/-opt-monorepo-workspace-universal-siem-monorepo/memory/siem-test-fix-{id}.md`

```markdown
---
name: siem-test-fix-{service}-{date}
description: Fix pattern: {one-line root cause}
type: feedback
tags: [siem-test-fix, test, {service-name}]
---
Error signature: {regex used for detection}
Root cause: {what was wrong in the test}
Fix applied: {what lines changed}
Why: {why the test was wrong}
Service: {e.g., log-service}
How to reapply: {step-by-step for future occurrences}
Learned from: {test filename}, cycle {N}, {YYYY-MM-DD}
```

Also append to `.test-siem/.fix-patterns.json`:
```json
{
  "id": "auto-{date}-{test-name-slug}",
  "errorSignature": "derived from error text",
  "service": "service name",
  "rootCause": "one-line description",
  "fix": "what to change",
  "learnedAt": "YYYY-MM-DD"
}
```

---

## Safety Rules (ENFORCED — never skip)

1. **NEVER edit** any file outside test directories:
   - Allowed: `backend/services/*/tests/`, `backend/tests/`, `backend/auth-service/tests/`, `backend/m365-service/tests/`, `frontend/src/__tests__/`, `frontend/src/**/__tests__/`, `tests/integration/`
   - Allowed: `.test-siem/.fix-patterns.json`
   - Allowed: per-service test `conftest.py` files
2. **NEVER edit** application source code (`backend/services/*/src/`, `backend/core/`, `frontend/src/` non-test files)
3. **NEVER edit** CI workflows (`.gitea/workflows/`)
4. **NEVER edit** root `backend/conftest.py`
5. **Max 3 fix cycles** — if failures remain after cycle 3, report and stop with NEEDS ATTENTION
6. **Regression guard** — always compare pass counts before and after each rerun; revert if regressions detected
7. **INFRA_ERROR class** — never attempt to fix these with test changes; report as infrastructure issues
8. **Never modify results.json directly** — it is written only by test runners

---

## Effort Steering

Agent dispatches use the routing matrix:
- **bug-hunter** (test fix): role=implement → sonnet, turns 20–25
- **agentic-search** (source lookup, if needed): role=scout → haiku, turns 8–12

For single-service runs (`/test-siem log-service`), expect 1–2 agents max.
