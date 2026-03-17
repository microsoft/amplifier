# SIEM Tech Debt Fixes — Staged Plan

> **For Claude:** REQUIRED: Use /subagent-dev to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox syntax for tracking. Each stage = separate branch + PR.

**Goal:** Fix 75 critical+high tech debt issues across 9 service areas, one PR per stage.

**Architecture:** Each stage targets one service, fixing critical items first then high. Tests must pass before PR. No new features — only debt reduction.

**Tech Stack:** Python 3.13, FastAPI, asyncpg, psycopg2, React 19, TypeScript, Vitest

**Branch pattern:** `techdebt/stage-N-<service-name>`

**Working directory:** `/opt/monorepo-workspace/universal-siem-monorepo/`

---

## Stage 1: auth-service (4 critical, 7 high)

Branch: `techdebt/stage-1-auth-service`

### Task 1.1: Fix declarative_base deprecation + JWT config duplication
**Agent:** bug-hunter
**Files:** `auth-service/models/auth.py`, `auth-service/security.py`, `auth-service/settings.py`
- [ ] Replace `from sqlalchemy.ext.declarative import declarative_base` with `from sqlalchemy.orm import declarative_base` in `models/auth.py:19-22`
- [ ] Identify all JWT config values duplicated between `security.py:20-25` and `settings.py`
- [ ] Remove duplicates from `security.py`, import from `settings.py` as single source of truth
- [ ] Verify no circular imports introduced

### Task 1.2: Fix O(n) bcrypt scan for agent API keys
**Agent:** bug-hunter
**Files:** `auth-service/crud.py`
- [ ] Analyze `crud.py:691-735` — current O(n) pattern iterates all keys doing bcrypt compare
- [ ] Add key prefix index lookup: store and query by unhashed prefix (first 8 chars) before bcrypt
- [ ] Ensure prefix lookup narrows candidates before expensive bcrypt comparison
- [ ] Add docstring explaining the prefix-index pattern

### Task 1.3: Replace print() debug statements in ldap.py
**Agent:** bug-hunter
**Files:** `auth-service/ldap.py`
- [ ] Audit `ldap.py:553-647` for all `print()` calls
- [ ] Replace each with appropriate `logger.debug()` or `logger.error()` calls
- [ ] Ensure logger is properly imported and initialized at module level
- [ ] Verify no print() remain in the range

### Task 1.4: Fix Pydantic v2 Config + pool config consolidation
**Agent:** modular-builder
**Files:** `auth-service/settings.py`, `auth-service/session.py`, `auth-service/constants.py`
- [ ] Migrate `settings.py:90-94` from `class Config` to `model_config = SettingsConfigDict(...)`
- [ ] Identify the three conflicting pool config sources: `session.py`, `constants.py`, `settings.py`
- [ ] Designate `settings.py` as single source, remove duplicates from `session.py` and `constants.py`
- [ ] Update all pool construction to read from settings

### Task 1.5: Fix dependencies.py deprecation + stale TODO + hardcoded group names
**Agent:** modular-builder
**Files:** `auth-service/dependencies.py`, `auth-service/admin.py`, `auth-service/jwt.py`
- [ ] In `dependencies.py`: complete migration of deprecated code or remove the deprecation notice (do not leave both paths)
- [ ] In `admin.py:43-46`: remove stale TODO about `is_ldap` — field already exists, no action needed
- [ ] In `jwt.py:152`: extract hardcoded group name strings to named constants (module-level or settings)

### Task 1.6: Fix ldap3 imports + add jti to refresh tokens
**Agent:** modular-builder
**Files:** `auth-service/ldap.py`, `auth-service/security.py`
- [ ] Move repeated `ldap3` imports from inside 4 methods to module level in `ldap.py`
- [ ] In `security.py:115-128`: add `jti` (JWT ID) claim to refresh token generation using `uuid4()`
- [ ] Add revocation check stub that looks up `jti` in a deny-list (Redis key or DB table); document as future work if infrastructure not available

### Task 1.7: Run tests + create PR
**Agent:** test-coverage
**Files:** `auth-service/`
- [ ] Run `uv run pytest auth-service/tests/ -v`
- [ ] Run full backend suite and confirm no regressions
- [ ] Commit: `git commit -m "fix(auth): resolve 4 critical + 7 high tech debt items"`
- [ ] Push branch and create PR: `techdebt/stage-1-auth-service` → `main`

---

## Stage 2: agents-service (6 critical, 7 high)

Branch: `techdebt/stage-2-agents-service`

### Task 2.1: Extract duplicate agent-online check + fix STATUS SQL CASE
**Agent:** bug-hunter
**Files:** `agents-service/powershell.py`, `agents-service/updates.py`, `agents-service/constants.py`
- [ ] Extract the duplicated agent-online check from 4 endpoints (`powershell.py`, `updates.py`) into a shared helper function `is_agent_online(agent_id, db)`
- [ ] Replace all 4 call sites with the helper
- [ ] Identify the 4 duplicated `STATUS CASE` SQL fragments with inconsistent thresholds (120 vs 300 seconds)
- [ ] Define `AGENT_ONLINE_THRESHOLD_SECONDS = 300` constant in `constants.py`
- [ ] Replace all 4 SQL fragments with a shared function or SQL fragment using the constant

### Task 2.2: Sanitize bare except + fix timing attack + fix utcnow deprecation
**Agent:** bug-hunter
**Files:** `agents-service/` (all ~15 instances), `agents-service/auth_legacy.py`, `agents-service/admin_keys.py`
- [ ] Audit all `except Exception as e` blocks that return `str(e)` to clients; replace with generic error message, log full error server-side
- [ ] In `auth_legacy.py:61`: replace plaintext API key comparison with `hmac.compare_digest()` for constant-time comparison
- [ ] In `admin_keys.py:158`: replace `datetime.utcnow()` with `datetime.now(timezone.utc)`

### Task 2.3: Fix module-level Fernet init crash
**Agent:** bug-hunter
**Files:** `agents-service/admin_keys.py`
- [ ] Move Fernet initialization from module level (`admin_keys.py:27-30`) into a FastAPI `Depends` dependency or a lazy getter function
- [ ] Ensure the service does not crash at import time if the encryption env var is missing
- [ ] Add clear error message when the dependency is called without the env var set

### Task 2.4: Extract shared auth.py + remove dead code + modernize typing
**Agent:** modular-builder
**Files:** `agents-service/auth.py`, `agents-service/agent_event_converter.py`, `agents-service/powershell.py`, `agents-service/` (typing imports)
- [ ] Extract `auth.py` into a shared library location (e.g., `shared/auth.py`) so both agents-service and devices-service (Stage 6) can import it
- [ ] Remove dead batch conversion functions from `agent_event_converter.py:265-299`
- [ ] Replace old-style `typing` imports (`List`, `Dict`, `Optional`, `Tuple`) with built-in generics (`list`, `dict`, `str | None`) across agents-service files including `powershell.py`

### Task 2.5: Extract named constants + decompose large functions
**Agent:** modular-builder
**Files:** `agents-service/constants.py`, `agents-service/log_processor.py`, `agents-service/health.py`
- [ ] Add named constants for magic numbers: `DEFAULT_PORT = 8000`, `AGENT_TIMEOUT_SECONDS = 120`, `AGENT_OFFLINE_THRESHOLD = 300`, `MAX_BATCH_SIZE = 10000`
- [ ] Replace all magic number usages with the constants
- [ ] Decompose `_process_file_logs` (120 lines) into 3-4 focused private functions
- [ ] Decompose `get_fleet_health` (110 lines) by extracting business logic into helper functions

### Task 2.6: Run tests + create PR
**Agent:** test-coverage
**Files:** `agents-service/`
- [ ] Run `uv run pytest agents-service/tests/ -v`
- [ ] Run full backend suite and confirm no regressions
- [ ] Commit: `git commit -m "fix(agents): resolve 6 critical + 7 high tech debt items"`
- [ ] Push branch and create PR: `techdebt/stage-2-agents-service` → `main`

---

## Stage 3: snort-service (3 critical, 6 high)

Branch: `techdebt/stage-3-snort-service`

### Task 3.1: Fix asyncpg API misuse (fetchrow)
**Agent:** bug-hunter
**Files:** `snort-service/audit.py`
- [ ] In `audit.py:275` and `audit.py:286`: replace `conn.fetchone()` (psycopg2 API) with `conn.fetchrow()` (asyncpg API)
- [ ] Audit remaining file for any other psycopg2-style calls in async context

### Task 3.2: Migrate correlation.py and threat_scorer.py from psycopg2 to asyncpg
**Agent:** database-architect
**Files:** `snort-service/correlation.py`, `snort-service/threat_scorer.py`
- [ ] In `correlation.py`: replace all `psycopg2` connection/cursor usage with `asyncpg` pool pattern
- [ ] Add error handling in `_load_attack_patterns` — wrap in `try/except`, log on failure, return empty dict as fallback
- [ ] In `threat_scorer.py`: replace psycopg2 with asyncpg pool
- [ ] In `threat_scorer.py`: replace hardcoded DB path/connection string with config from settings

### Task 3.3: Fix hardcoded IPs, wrong column names, and deprecated APIs
**Agent:** bug-hunter
**Files:** `snort-service/threat_scorer.py`, `snort-service/sensor_manager.py`, `snort-service/blocked_ip_cache.py`
- [ ] Move hardcoded IP prefixes in `threat_scorer.py` to settings/config
- [ ] In `sensor_manager.py:556`: fix wrong column names `src_ip`/`dest_ip` → `src_addr`/`dst_addr`
- [ ] In `sensor_manager.py:253`: replace `asyncio.get_event_loop()` with `asyncio.get_running_loop()`
- [ ] In `blocked_ip_cache.py:69`: replace hardcoded `verify=False` with configurable `use_tls_verify: bool = True` from settings
- [ ] In `sensor_manager.py`: replace `paramiko.AutoAddPolicy()` with `paramiko.RejectPolicy()` and document that known_hosts must be populated; add config flag `allow_unknown_hosts` defaulting to False

### Task 3.4: Run tests + create PR
**Agent:** test-coverage
**Files:** `snort-service/`
- [ ] Run `uv run pytest snort-service/tests/ -v`
- [ ] Run full backend suite and confirm no regressions
- [ ] Commit: `git commit -m "fix(snort): resolve 3 critical + 6 high tech debt items"`
- [ ] Push branch and create PR: `techdebt/stage-3-snort-service` → `main`

---

## Stage 4: anomaly-service (3 critical, 7 high)

Branch: `techdebt/stage-4-anomaly-service`

### Task 4.1: Fix broken email template + SQL injection
**Agent:** bug-hunter
**Files:** `anomaly-service/alerting.py`, `anomaly-service/anomaly_storage.py`
- [ ] In `alerting.py:631-659`: identify the regular string that should be an f-string; convert to f-string with correct variable interpolation
- [ ] In `anomaly_storage.py`: find all 5 `INTERVAL '%s hours'` string interpolation patterns
- [ ] Replace each with a parameterized query using `$1` placeholder and passing the value as a query parameter (asyncpg style)

### Task 4.2: Scope psycopg2 migration (no implementation)
**Agent:** database-architect
**Files:** `anomaly-service/anomaly_storage.py`
- [ ] Audit full scope of psycopg2 usage in `anomaly_storage.py`
- [ ] Document migration complexity and estimated file count in a `# TECH-DEBT:` comment at top of file
- [ ] Create a tracking comment listing all sync DB call sites that need async migration
- [ ] Do NOT migrate — scope only, flag for a dedicated future stage

### Task 4.3: Fix config, deprecated APIs, and timezone issues
**Agent:** modular-builder
**Files:** `anomaly-service/alerting.py`, `anomaly-service/anomaly_storage.py`
- [ ] In `alerting.py:17`: move hardcoded dashboard URL to settings with key `DASHBOARD_BASE_URL`
- [ ] In `alerting.py:668`: replace `asyncio.get_event_loop()` with `asyncio.get_running_loop()`
- [ ] In `alerting.py`: add docstring/comment to `alert_cache` documenting the in-memory limitation and restart behavior
- [ ] In `anomaly_storage.py`: replace all `datetime.fromtimestamp()` calls with `datetime.fromtimestamp(..., tz=timezone.utc)`

### Task 4.4: Fix feature extractor encoder misuse + model cache stub
**Agent:** modular-builder
**Files:** `anomaly-service/feature_extractor.py`, `anomaly-service/feature_extractor_v2.py`, `anomaly-service/model_cache.py`
- [ ] In `feature_extractor.py:257`: create a separate `UsernameEncoder` instead of reusing `IPEncoder` for username fields
- [ ] In `feature_extractor_v2.py:811`: create a separate `DestIPEncoder` instead of reusing `connector_encoder` for dst_ip fields
- [ ] In `model_cache.py`: evaluate `cache_warmup()` — if it has no real implementation, either implement basic warmup (load models from disk on startup) or remove the method entirely; do not leave a stub

### Task 4.5: Run tests + create PR
**Agent:** test-coverage
**Files:** `anomaly-service/`
- [ ] Run `uv run pytest anomaly-service/tests/ -v`
- [ ] Run full backend suite and confirm no regressions
- [ ] Commit: `git commit -m "fix(anomaly): resolve 3 critical + 7 high tech debt items"`
- [ ] Push branch and create PR: `techdebt/stage-4-anomaly-service` → `main`

---

## Stage 5: log-service (3 critical, 7 high)

Branch: `techdebt/stage-5-log-service`

### Task 5.1: Fix broken imports + bare except swallowing errors + remove dev test function
**Agent:** bug-hunter
**Files:** `log-service/base_parser.py`, `log-service/federated_search.py`
- [ ] In `base_parser.py:186` and `base_parser.py:198`: add missing `app.` prefix to broken import paths
- [ ] In `federated_search.py:858`, `federated_search.py:909`, `federated_search.py:561`: replace `except: pass` with `except Exception as e: logger.warning("...", exc_info=True)`
- [ ] In `federated_search.py:976-1010`: remove the dev test function entirely; confirm it is not referenced anywhere before deleting

### Task 5.2: Extract duplicate log-type alias map + remove redundant LDAP normalization
**Agent:** modular-builder
**Files:** `log-service/` (3 files with duplicate map), `log-service/federated_search.py`
- [ ] Find the 3 locations with duplicate log-type alias maps
- [ ] Extract to `log-service/constants.py` (or equivalent) as `LOG_TYPE_ALIAS_MAP`
- [ ] Replace all 3 usages with the constant
- [ ] In `federated_search.py:641-648`: remove the per-row LDAP normalization that duplicates batch normalization logic

### Task 5.3: Fix TODO, parser cache, stats aggregation, and deprecated API
**Agent:** modular-builder
**Files:** `log-service/logs_router.py`, `log-service/` (hot path files), `log-service/federated_search.py`
- [ ] In `logs_router.py:179`: evaluate the TODO — either implement it or create a Gitea issue and replace the TODO with `# See issue #<N>`
- [ ] In the hot path: move parser instantiation from per-row to module-level cache (instantiate once, reuse)
- [ ] In `get_stats`: replace Python-side full-query aggregation with `COUNT`, `SUM`, `AVG` SQL aggregation in the DB query
- [ ] Replace `asyncio.get_event_loop()` with `asyncio.get_running_loop()` in log-service

### Task 5.4: Decompose _transform_hot_tier_to_frontend
**Agent:** modular-builder
**Files:** `log-service/federated_search.py`
- [ ] Decompose the 450-line `_transform_hot_tier_to_frontend` function (`federated_search.py:443-896`) into per-parser transform functions
- [ ] Create private functions: `_transform_windows_event`, `_transform_syslog`, `_transform_snort`, etc.
- [ ] `_transform_hot_tier_to_frontend` becomes a dispatcher that calls the appropriate per-parser function
- [ ] Each per-parser function should be ≤80 lines

### Task 5.5: Run tests + create PR
**Agent:** test-coverage
**Files:** `log-service/`
- [ ] Run `uv run pytest log-service/tests/ -v`
- [ ] Run full backend suite and confirm no regressions
- [ ] Commit: `git commit -m "fix(logs): resolve 3 critical + 7 high tech debt items"`
- [ ] Push branch and create PR: `techdebt/stage-5-log-service` → `main`

---

## Stage 6: devices-service (3 critical, 5 high)

Branch: `techdebt/stage-6-devices-service`

### Task 6.1: Fix module-level event loop + separate asyncpg pool
**Agent:** bug-hunter
**Files:** `devices-service/device_tasks.py`, `devices-service/poller.py`
- [ ] In `device_tasks.py:12`: remove module-level `asyncio.get_event_loop()` anti-pattern; wrap task execution in `asyncio.run()` or ensure tasks are scheduled through the existing event loop via `asyncio.ensure_future()`
- [ ] In `poller.py:24-27`: remove the separately created asyncpg pool; inject the shared application pool via FastAPI `Depends` or pass it as a parameter

### Task 6.2: Fix TLS verify=False in mikrotik.py
**Agent:** bug-hunter
**Files:** `devices-service/mikrotik.py`
- [ ] In `mikrotik.py:22`: replace hardcoded `verify=False` with `use_ssl_verify: bool` parameter sourced from device settings or app config
- [ ] Default to `True` (verify enabled); allow per-device override for self-signed cert environments

### Task 6.3: Consolidate provider duplication + fix bare except + add semaphore
**Agent:** modular-builder
**Files:** `devices-service/devices_router.py`, `devices-service/poller.py`
- [ ] In `devices_router.py:260-304`: merge near-duplicate `_test_provider` and `_get_provider` into a single factory function with a `test_mode: bool = False` parameter
- [ ] In `devices_router.py:339-408`: replace the 5 copy-pasted provider call blocks with an async context manager that handles setup/teardown
- [ ] In `poller.py:94-101`: replace bare `except` with typed exception handling; store the error reason in the poll result record
- [ ] Add a semaphore (e.g., `asyncio.Semaphore(10)`) to limit concurrent on-demand provider connections
- [ ] Note: `auth.py` deduplication with agents-service handled in Stage 2; import from shared location here

### Task 6.4: Run tests + create PR
**Agent:** test-coverage
**Files:** `devices-service/`
- [ ] Run `uv run pytest devices-service/tests/ -v`
- [ ] Run full backend suite and confirm no regressions
- [ ] Commit: `git commit -m "fix(devices): resolve 3 critical + 5 high tech debt items"`
- [ ] Push branch and create PR: `techdebt/stage-6-devices-service` → `main`

---

## Stage 7: m365-service (0 critical, 5 high)

Branch: `techdebt/stage-7-m365-service`

### Task 7.1: Migrate Pydantic Config + extract duplicate response builders
**Agent:** modular-builder
**Files:** `m365-service/config.py`, `m365-service/` (4 endpoints with duplicated tenant response)
- [ ] In `config.py:44`: migrate `class Config` to `model_config = SettingsConfigDict(...)`
- [ ] Identify the 4 endpoints with duplicated tenant response construction
- [ ] Extract a `build_tenant_response(tenant, ...)` helper function
- [ ] Replace all 4 call sites with the helper

### Task 7.2: Extract duplicate search pattern + fix ORM bypass + fix cert cleanup
**Agent:** modular-builder
**Files:** `m365-service/search.py`, `m365-service/message_trace.py`
- [ ] In `search.py`: extract the 3 duplicated search patterns into a shared `_execute_search(query, params)` handler
- [ ] In `message_trace.py:51-103`: replace raw SQL with ORM query using the existing model classes
- [ ] In `message_trace.py:118`: wrap temp cert file operations in a `try/finally` block; ensure cleanup runs even on exception

### Task 7.3: Run tests + create PR
**Agent:** test-coverage
**Files:** `m365-service/`
- [ ] Run `uv run pytest m365-service/tests/ -v`
- [ ] Run full backend suite and confirm no regressions
- [ ] Commit: `git commit -m "fix(m365): resolve 5 high tech debt items"`
- [ ] Push branch and create PR: `techdebt/stage-7-m365-service` → `main`

---

## Stage 8: core-backend (0 critical, 4 high)

Branch: `techdebt/stage-8-core-backend`

### Task 8.1: Fix all 4 high-priority core-backend items
**Agent:** bug-hunter
**Files:** `backend/alerts_router.py`, `backend/csrf.py`
- [ ] In `alerts_router.py`: remove the local `_set_rls_context` duplicate; import from middleware module
- [ ] In `alerts_router.py`: find the 3 endpoints calling `get_db_pool()` inline; replace with `pool: asyncpg.Pool = Depends(get_db_pool)` in function signatures
- [ ] In `alerts_router.py`: replace `datetime.utcnow()` with `datetime.now(timezone.utc)`
- [ ] In `csrf.py`: identify the two exempt-path lists at `csrf.py:47-62` and `csrf.py:136-153`; merge into a single `CSRF_EXEMPT_PATHS: frozenset` constant and reference it in both locations

### Task 8.2: Run tests + create PR
**Agent:** test-coverage
**Files:** `backend/`
- [ ] Run `uv run pytest backend/tests/ -v`
- [ ] Run full backend suite and confirm no regressions
- [ ] Commit: `git commit -m "fix(core): resolve 4 high tech debt items"`
- [ ] Push branch and create PR: `techdebt/stage-8-core-backend` → `main`

---

## Stage 9: frontend (2 critical, 3 high)

Branch: `techdebt/stage-9-frontend`

### Task 9.1: Remove console.log leaking build info
**Agent:** modular-builder
**Files:** `frontend/src/version.ts`
- [ ] Locate all `console.log` statements in `version.ts`
- [ ] Remove them entirely (do not replace with comments)
- [ ] Verify no other version/build info is logged at app startup

### Task 9.2: Migrate top 3 direct apiClient call sites to React Query
**Agent:** modular-builder
**Files:** `frontend/src/components/CeleryTab.tsx`, `frontend/src/components/SnortIDSSettings.tsx`, `frontend/src/components/HealthTab.tsx`
- [ ] For each file: identify all direct `apiClient.get/post/delete` calls outside of React Query hooks
- [ ] Create or extend a query hook (e.g., `useCeleryStatus`, `useSnortSettings`, `useHealthStatus`) using `useQuery` or `useMutation` from TanStack Query
- [ ] Replace direct `apiClient` calls + `useState`/`useEffect` data-fetch patterns with the query hooks
- [ ] Preserve existing error and loading UI

### Task 9.3: Split defaultColumns.ts + convert setInterval pollers + delete dead component
**Agent:** modular-builder
**Files:** `frontend/src/defaultColumns.ts`, `frontend/src/` (5 files with setInterval), `frontend/src/components/FederatedStatsPanel.tsx`
- [ ] Split `defaultColumns.ts` (1582 lines) into per-log-type files: `columns/windowsColumns.ts`, `columns/syslogColumns.ts`, `columns/snortColumns.ts`, etc. with a barrel `columns/index.ts`
- [ ] Update all imports of `defaultColumns.ts` to use the new barrel
- [ ] In the 5 files using manual `setInterval` for polling: replace with TanStack Query `refetchInterval` option on the relevant `useQuery` calls; remove `useEffect` + `setInterval` + `clearInterval` boilerplate
- [ ] Delete `FederatedStatsPanel.tsx` — confirm zero imports/usages before deleting

### Task 9.4: Run tests + create PR
**Agent:** test-coverage
**Files:** `frontend/`
- [ ] Run `npx vitest run` (or `uv run` equivalent for frontend)
- [ ] Confirm TypeScript compiles with no new errors: `npx tsc --noEmit`
- [ ] Run full backend suite and confirm no regressions
- [ ] Commit: `git commit -m "fix(frontend): resolve 2 critical + 3 high tech debt items"`
- [ ] Push branch and create PR: `techdebt/stage-9-frontend` → `main`

---

## Summary Table

| Stage | Service | Critical | High | Tasks | Agent(s) |
|-------|---------|----------|------|-------|----------|
| 1 | auth-service | 4 | 7 | 7 | bug-hunter, modular-builder, test-coverage |
| 2 | agents-service | 6 | 7 | 6 | bug-hunter, modular-builder, test-coverage |
| 3 | snort-service | 3 | 6 | 4 | bug-hunter, database-architect, test-coverage |
| 4 | anomaly-service | 3 | 7 | 5 | bug-hunter, database-architect, modular-builder, test-coverage |
| 5 | log-service | 3 | 7 | 5 | bug-hunter, modular-builder, test-coverage |
| 6 | devices-service | 3 | 5 | 4 | bug-hunter, modular-builder, test-coverage |
| 7 | m365-service | 0 | 5 | 3 | modular-builder, test-coverage |
| 8 | core-backend | 0 | 4 | 2 | bug-hunter, test-coverage |
| 9 | frontend | 2 | 3 | 4 | modular-builder, test-coverage |
| **Total** | | **24** | **51** | **40** | |
