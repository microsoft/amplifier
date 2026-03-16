# /test-siem — SIEM Test Auto-Fix Pipeline

**Date:** 2026-03-16
**Status:** Approved
**Based on:** `/test-verified` (FuseCP E2E auto-fix pipeline)

## Problem

The universal-siem-monorepo has tests spread across 8+ microservices (pytest) and a React frontend (vitest/playwright). Tests break due to schema drift, import changes, fixture staleness, and async timing issues. Currently there's no automated way to run, classify, and fix test failures — CI uses `continue-on-error: true` so failures don't even block builds.

## Goal

Create `/test-siem` — a selective test runner with automated failure classification, known-pattern application, agent-dispatched fixes, and learning loop. Same philosophy as `/test-verified`: never modify application code, only fix test code.

## Scope Selection

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
/test-siem m365-service       # single service (backend/m365-service)
/test-siem integration        # integration tests only
/test-siem --health           # pre-flight only
/test-siem --report           # report from last results, no run
```

**Working directory:** `/opt/monorepo-workspace/universal-siem-monorepo/`

## Pipeline Phases

### Phase 0: Pre-flight Health Check

- Check PostgreSQL reachable: `PGPASSWORD='7oBuuQ1fmKQMjNI0Hro6s9RShMwCDOzc' psql -U siem_user -h 172.31.250.30 -d siem_timeseries -c "SELECT 1"`
- Check K8s pods: `kubectl get pods -n siem-staging -o json`
- DB unreachable → abort
- Pods not ready → warn for integration scope, skip for unit-only
- `--health` → print status table and stop

### Phase 1: Run Suite

| Scope | Command |
|-------|---------|
| `backend` | `cd backend && uv run pytest tests/ -v --tb=short --json-report` |
| `frontend` | `cd frontend && npm run test -- --run --reporter=json` |
| `log-service` | `cd backend/services/log-service && uv run pytest tests/ -v --tb=short --json-report` |
| `auth-service` | `cd backend/auth-service && uv run pytest tests/ -v --tb=short --json-report` |
| `anomaly-service` | `cd backend/services/anomaly-service && uv run pytest tests/ -v --tb=short --json-report` |
| `snort-service` | `cd backend/services/snort-service && uv run pytest tests/ -v --tb=short --json-report` |
| `agents-service` | `cd backend/services/agents-service && uv run pytest tests/ -v --tb=short --json-report` |
| `devices-service` | `cd backend/services/devices-service && uv run pytest tests/ -v --tb=short --json-report` |
| `m365-service` | `cd backend/m365-service && uv run pytest tests/ -v --tb=short --json-report` |
| `integration` | `cd tests/integration && uv run pytest api/ -v --tb=short --json-report` |
| (no arg) | Run backend then frontend sequentially |

Results saved to `.test-siem/results.json`.

### Phase 2: Parse Results

Normalize pytest JSON report and vitest JSON output into unified format:

```json
{
  "timestamp": "ISO-8601",
  "scope": "backend|frontend|<service>",
  "duration_s": 45,
  "summary": { "passed": 82, "failed": 7, "skipped": 3 },
  "failures": [
    {
      "test": "test_name",
      "file": "relative/path/to/test.py",
      "service": "log-service",
      "error": "error message",
      "traceback": "full traceback",
      "class": null
    }
  ]
}
```

If `failed === 0`: skip to Phase 7.

### Phase 3: Classify Failures

| Class | Patterns |
|-------|----------|
| `IMPORT_ERROR` | `ModuleNotFoundError`, `ImportError`, `Cannot find module`, `No module named` |
| `DB_SCHEMA` | `relation.*does not exist`, `UndefinedColumn`, `UndefinedTable`, `sqlalchemy.*OperationalError` |
| `AUTH_ERROR` | `status.*40[13]`, `token.*invalid`, `permission denied`, `AuthenticationError` |
| `ASYNC_TIMING` | `asyncio.*TimeoutError`, `Event loop`, `RuntimeError.*event loop`, `TimeoutError` |
| `INFRA_ERROR` | `ConnectionRefusedError`, `ConnectionError.*refused`, `pod.*not ready`, `ECONNREFUSED` |
| `ASSERTION` | `AssertionError`, `assert.*==`, `expect\(` (catch-all after above) |
| `UNKNOWN` | No match |

`INFRA_ERROR` is reported but never auto-fixed.

### Phase 4: Known Fix Patterns

Read `.test-siem/.fix-patterns.json` + search episodic memory for `siem-test-fix`.

For each non-INFRA failure: match `errorSignature` regex, apply fix via Edit tool if matched.

### Phase 5: Dispatch Fix Agents

Group by failing test file. Max 3 parallel `bug-hunter` agents (sonnet, max_turns 25).

Context per agent: failing test file, errors, service source (read-only), conftest, known patterns, 1-2 passing tests as reference.

Agent instruction: fix test files only, never modify application code.

### Phase 6: Rerun and Cycle

Rerun only previously-failing files. Regression guard: revert via `git checkout HEAD -- <file>` if new failures appear. Record successful fixes to `.fix-patterns.json` and memory.

Max 3 cycles. If failures remain → Phase 7 with NEEDS ATTENTION.

### Phase 7: Report

Terminal summary with pass/fail/skip counts, fix summary (cycles, patterns applied, agents dispatched, regressions), and remaining failures list.

## Safety Rules

1. **NEVER edit** files outside test directories (`backend/services/*/tests/`, `backend/tests/`, `backend/auth-service/tests/`, `backend/m365-service/tests/`, `frontend/src/__tests__/`, `frontend/src/**/__tests__/`, `tests/integration/`)
2. **NEVER edit** application source code, CI workflows, or root conftest.py
3. **Max 3 fix cycles**
4. **Regression guard** — revert if pass count drops
5. **INFRA_ERROR** — report only, never auto-fix
6. **Never modify results.json directly**

## Files Changed

| File | Action |
|------|--------|
| `.claude/commands/test-siem.md` | Create — the skill definition |
| `config/platform/exclude.windows.txt` | Update — exclude test-siem on Windows |

## Agent Allocation

| Phase | Agent | Responsibility |
|-------|-------|---------------|
| Pre-flight | (inline) | Health checks via Bash |
| Run + Parse | (inline) | Execute test commands, normalize results |
| Classify | (inline) | Regex classification |
| Pattern matching | (inline) | Apply known fixes |
| Novel fixes | bug-hunter (sonnet) | Fix unknown test failures |
| Report | (inline) | Generate summary |

## Test Plan

- [ ] `/test-siem --health` shows DB and pod status
- [ ] `/test-siem log-service` runs only log-service tests
- [ ] `/test-siem backend` runs all backend services
- [ ] `/test-siem frontend` runs vitest
- [ ] Classification correctly buckets a sample IMPORT_ERROR and ASSERTION failure
- [ ] Known pattern from `.fix-patterns.json` is applied on second run
- [ ] Regression guard reverts a fix that breaks a passing test
