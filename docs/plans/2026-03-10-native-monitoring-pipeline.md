# Native Monitoring Pipeline Implementation Plan

> **For Claude:** REQUIRED: Use /subagent-dev to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Prometheus + Grafana with a native TimescaleDB monitoring pipeline, JEXL alert engine, and Recharts dashboard.

**Architecture:** Metrics flow from agents through FastAPI into TimescaleDB continuous aggregates, auto-selected by time range. JEXL-based alert rules evaluated by Celery every minute feed into unified_alerts. Supabase Realtime pushes alert notifications to the React frontend. Native Recharts replaces Grafana iframes.

**Tech Stack:** FastAPI, TimescaleDB (continuous aggregates), pyjexl, Celery Beat, Supabase Realtime, React, TanStack Query, Recharts, Shadcn/UI

---

## Phase 0: Foundation (Tasks 0-5)

### Task 0: Database migration `051_alert_rules_and_monthly_ca.sql`

**Agent:** `database-architect`

**Files:**
- Create: `/opt/monorepo-workspace/universal-siem-monorepo/backend/database/migrations/051_alert_rules_and_monthly_ca.sql`

**Steps:**

- [ ] Read existing migration 050 to confirm current highest migration and understand naming convention:
  ```bash
  ls /opt/monorepo-workspace/universal-siem-monorepo/backend/database/migrations/ | sort | tail -5
  ```
- [ ] Read migration 013 lines 120-200 to understand existing CA structure before adding monthly CA:
  ```bash
  sed -n '120,200p' /opt/monorepo-workspace/universal-siem-monorepo/backend/database/migrations/013_*.sql
  ```
- [ ] Read migrations 038 and 039 to understand `unified_alerts` table structure:
  ```bash
  cat /opt/monorepo-workspace/universal-siem-monorepo/backend/database/migrations/038_*.sql
  cat /opt/monorepo-workspace/universal-siem-monorepo/backend/database/migrations/039_*.sql
  ```
- [ ] Create migration file with the following sections (use exact SQL from spec):

  **Section 1 — `siem.alert_rules` table with RLS:**
  ```sql
  CREATE TABLE siem.alert_rules (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      tenant_id UUID NOT NULL,
      name TEXT NOT NULL,
      description TEXT,
      enabled BOOLEAN DEFAULT true,
      expression TEXT NOT NULL,
      data_source TEXT NOT NULL DEFAULT 'agent_metrics',
      sustained_count INTEGER DEFAULT 3,
      cooldown_minutes INTEGER DEFAULT 15,
      severity TEXT NOT NULL DEFAULT 'warning',
      actions JSONB DEFAULT '[]',
      scope JSONB DEFAULT '{}',
      created_by UUID,
      created_at TIMESTAMPTZ DEFAULT now(),
      updated_at TIMESTAMPTZ DEFAULT now(),
      last_evaluated_at TIMESTAMPTZ,
      consecutive_hits INTEGER DEFAULT 0
  );

  ALTER TABLE siem.alert_rules ENABLE ROW LEVEL SECURITY;

  CREATE POLICY "Tenant isolation on alert_rules"
  ON siem.alert_rules FOR ALL TO authenticated
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

  CREATE POLICY "Service role full access on alert_rules"
  ON siem.alert_rules FOR ALL TO service_role
  USING (true);
  ```

  **Section 2 — `metrics_monthly` continuous aggregate (derived from `agent_metrics_daily`):**
  ```sql
  CREATE MATERIALIZED VIEW metrics_monthly
  WITH (timescaledb.continuous) AS
  SELECT
      time_bucket('1 month', bucket) AS bucket,
      agent_id,
      avg(avg_cpu) AS avg_cpu,
      max(max_cpu) AS max_cpu,
      avg(avg_memory) AS avg_memory,
      max(max_memory) AS max_memory,
      sum(total_events) AS total_events
  FROM agent_metrics_daily
  GROUP BY 1, 2;
  ```

  **Section 3 — Supabase Realtime trigger on `unified_alerts`:**
  ```sql
  CREATE OR REPLACE FUNCTION notify_alert_fired()
  RETURNS TRIGGER AS $$
  BEGIN
    PERFORM realtime.send(
      jsonb_build_object(
        'alert_id', NEW.id,
        'severity', NEW.severity,
        'source', NEW.source,
        'title', NEW.title,
        'agent_id', NEW.agent_id,
        'fired_at', NEW.created_at
      ),
      'alert_fired',
      'tenant:' || NEW.tenant_id::text || ':alerts',
      true
    );
    RETURN NULL;
  END;
  $$ LANGUAGE plpgsql SECURITY DEFINER;

  CREATE TRIGGER unified_alerts_realtime
    AFTER INSERT ON siem.unified_alerts
    FOR EACH ROW EXECUTE FUNCTION notify_alert_fired();
  ```

  **Section 4 — Schema grants for Supabase:**
  ```sql
  GRANT USAGE ON SCHEMA siem TO anon, authenticated, service_role;
  GRANT ALL ON ALL TABLES IN SCHEMA siem TO anon, authenticated, service_role;
  ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA siem
    GRANT ALL ON TABLES TO anon, authenticated, service_role;
  ```

- [ ] Run migration and verify:
  ```bash
  PGPASSWORD='7oBuuQ1fmKQMjNI0Hro6s9RShMwCDOzc' psql -U siem_user -h localhost -d siem_timeseries \
    -f /opt/monorepo-workspace/universal-siem-monorepo/backend/database/migrations/051_alert_rules_and_monthly_ca.sql
  ```
- [ ] Verify `siem.alert_rules` table exists:
  ```bash
  PGPASSWORD='7oBuuQ1fmKQMjNI0Hro6s9RShMwCDOzc' psql -U siem_user -h localhost -d siem_timeseries \
    -c "\d siem.alert_rules"
  ```
  Expected output: table definition with all columns listed above.
- [ ] Verify `metrics_monthly` CA exists:
  ```bash
  PGPASSWORD='7oBuuQ1fmKQMjNI0Hro6s9RShMwCDOzc' psql -U siem_user -h localhost -d siem_timeseries \
    -c "SELECT view_name FROM timescaledb_information.continuous_aggregates WHERE view_name = 'metrics_monthly';"
  ```
  Expected output: `metrics_monthly` row returned.
- [ ] Verify Realtime trigger exists:
  ```bash
  PGPASSWORD='7oBuuQ1fmKQMjNI0Hro6s9RShMwCDOzc' psql -U siem_user -h localhost -d siem_timeseries \
    -c "SELECT trigger_name FROM information_schema.triggers WHERE trigger_name = 'unified_alerts_realtime';"
  ```
  Expected output: `unified_alerts_realtime` row returned.
- [ ] Test trigger fires on INSERT:
  ```bash
  PGPASSWORD='7oBuuQ1fmKQMjNI0Hro6s9RShMwCDOzc' psql -U siem_user -h localhost -d siem_timeseries \
    -c "INSERT INTO siem.unified_alerts (tenant_id, severity, source, title) VALUES (gen_random_uuid(), 'warning', 'rule_engine', 'test') RETURNING id;"
  ```
  Expected output: INSERT returns a UUID; no ERROR from trigger function.
- [ ] Commit:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo && git add backend/database/migrations/051_alert_rules_and_monthly_ca.sql
  git commit -m "feat(db): add alert_rules table, monthly CA, and realtime trigger"
  ```

---

### Task 1: Install pyjexl dependency

**Agent:** `modular-builder`

**Files:**
- Modify: `/opt/monorepo-workspace/universal-siem-monorepo/backend/pyproject.toml`

**Steps:**

- [ ] Add pyjexl via uv (do NOT manually edit pyproject.toml):
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo/backend && uv add pyjexl
  ```
- [ ] Verify import works:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo/backend && uv run python -c "import pyjexl; print(pyjexl.__version__)"
  ```
  Expected output: a version string such as `0.3.0` (no ImportError).
- [ ] Verify pyjexl appears in `pyproject.toml` dependencies section.
- [ ] Commit:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo && git add backend/pyproject.toml backend/uv.lock
  git commit -m "feat(deps): add pyjexl for alert expression engine"
  ```

---

### Task 2: Build `metrics_router.py`

**Agent:** `modular-builder`

**Files:**
- Create: `/opt/monorepo-workspace/universal-siem-monorepo/backend/routers/metrics_router.py`
- Create: `/opt/monorepo-workspace/universal-siem-monorepo/backend/tests/test_metrics_router.py`

**Steps:**

- [ ] Read reference files before writing:
  - `/opt/monorepo-workspace/universal-siem-monorepo/backend/routers/grafana_router.py` (auth pattern)
  - `/opt/monorepo-workspace/universal-siem-monorepo/backend/services/agents-service/app/routers/heartbeat.py` lines 47-146 (asyncpg pattern)
  - `/opt/monorepo-workspace/universal-siem-monorepo/backend/routers/prometheus_router.py` lines 31-49 (note: sync psycopg2 — do NOT replicate)

- [ ] **TDD — Write failing tests first** in `test_metrics_router.py`:

  Test cases to write:
  - `test_resolution_1h_returns_raw` — time range <= 1h selects `agent_metrics` table
  - `test_resolution_6h_returns_5min` — 1h < range <= 24h selects `metrics_5min`
  - `test_resolution_7d_returns_hourly` — 1d < range <= 30d selects `metrics_hourly`
  - `test_resolution_90d_returns_daily` — 30d < range <= 90d selects `metrics_daily`
  - `test_resolution_1y_returns_monthly` — range > 90d selects `metrics_monthly`
  - `test_response_format_has_series_key` — response contains `series`, `resolution`, `time_range`
  - `test_series_points_have_t_and_v` — each point has `t` (ISO timestamp) and `v` (float)
  - `test_summary_endpoint_returns_fleet_stats` — `/api/metrics/summary` returns `total_agents`, `online`, `offline`, `avg_cpu`, `avg_memory`

- [ ] Run tests to confirm they fail:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo/backend && uv run pytest tests/test_metrics_router.py -v 2>&1 | head -40
  ```
  Expected output: `FAILED` for all test cases.

- [ ] Implement `metrics_router.py` with:
  - Router prefix `/api/metrics`
  - Auth via `get_auth_from_headers` (same pattern as `grafana_router.py`)
  - asyncpg connection pool (NOT sync psycopg2)
  - Pydantic models: `TimeRange`, `MetricPoint(t: datetime, v: float)`, `MetricSeries`, `MetricsResponse`
  - Resolution selector function:
    ```python
    def select_resolution(hours: float) -> tuple[str, str]:
        if hours <= 1:    return ("agent_metrics",   "raw")
        if hours <= 24:   return ("metrics_5min",    "5min")
        if hours <= 720:  return ("metrics_hourly",  "hourly")   # 30 days
        if hours <= 2160: return ("metrics_daily",   "daily")    # 90 days
        return             ("metrics_monthly",  "monthly")
    ```
  - Endpoints:
    - `GET /api/metrics/summary` — fleet health quick-stats (real data from TimescaleDB)
    - `GET /api/metrics/agents/{agent_id}` — single agent time-series, query params: `from`, `to`
    - `GET /api/metrics/fleet` — fleet-wide aggregated metrics, query params: `from`, `to`
    - `GET /api/metrics/compare` — side-by-side comparison, query params: `agent_ids` (CSV), `metrics` (CSV), `from`, `to`
    - `POST /api/metrics/query` — flexible parameterized query with request body
    - `GET /api/metrics/health` — system health overview (agent counts, CA refresh status)

- [ ] Run tests to confirm they pass:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo/backend && uv run pytest tests/test_metrics_router.py -v
  ```
  Expected output: all 8 tests `PASSED`.

- [ ] Commit:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo && \
    git add backend/routers/metrics_router.py backend/tests/test_metrics_router.py
  git commit -m "feat(api): add native metrics router with smart resolution"
  ```

---

### Task 3: Build `alert_rules_router.py`

**Agent:** `modular-builder`

**Files:**
- Create: `/opt/monorepo-workspace/universal-siem-monorepo/backend/routers/alert_rules_router.py`
- Create: `/opt/monorepo-workspace/universal-siem-monorepo/backend/tests/test_alert_rules_router.py`

**Steps:**

- [ ] Read reference files before writing:
  - `/opt/monorepo-workspace/universal-siem-monorepo/backend/routers/alerts_router.py` lines 20-26 (RLS tenant context pattern)
  - `/opt/monorepo-workspace/universal-siem-monorepo/backend/routers/grafana_router.py` (auth pattern)

- [ ] **TDD — Write failing tests first** in `test_alert_rules_router.py`:

  Test cases to write:
  - `test_list_rules_returns_empty_for_new_tenant` — GET returns `[]` for tenant with no rules
  - `test_create_rule_persists_to_db` — POST creates rule, GET returns it
  - `test_create_rule_validates_expression_not_empty` — empty expression returns 422
  - `test_update_rule_changes_fields` — PUT updates name, expression, severity
  - `test_delete_rule_removes_from_db` — DELETE removes rule, GET returns `[]`
  - `test_tenant_isolation` — rule created by tenant A not visible to tenant B
  - `test_test_endpoint_evaluates_without_inserting_alert` — POST /{id}/test returns `{matched: bool, context: dict}`, no row in unified_alerts

- [ ] Run tests to confirm they fail:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo/backend && uv run pytest tests/test_alert_rules_router.py -v 2>&1 | head -40
  ```
  Expected output: `FAILED` or `ERROR` for all test cases.

- [ ] Implement `alert_rules_router.py` with:
  - Router prefix `/api/alert-rules`
  - Auth via `get_auth_from_headers`
  - Tenant RLS context set via `SET LOCAL app.current_tenant_id = $1` (matching `alerts_router.py` lines 20-26 pattern)
  - Pydantic models: `AlertRuleCreate`, `AlertRuleUpdate`, `AlertRuleResponse`
  - Endpoints:
    - `GET /api/alert-rules` — list rules (tenant-scoped via RLS)
    - `POST /api/alert-rules` — create rule
    - `PUT /api/alert-rules/{id}` — update rule
    - `DELETE /api/alert-rules/{id}` — delete rule
    - `POST /api/alert-rules/{id}/test` — evaluate JEXL expression against latest metrics, return `{matched: bool, context: dict}` WITHOUT inserting alert

- [ ] Run tests to confirm they pass:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo/backend && uv run pytest tests/test_alert_rules_router.py -v
  ```
  Expected output: all 7 tests `PASSED`.

- [ ] Commit:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo && \
    git add backend/routers/alert_rules_router.py backend/tests/test_alert_rules_router.py
  git commit -m "feat(api): add alert rules CRUD router"
  ```

---

### Task 4: Build JEXL alert evaluator Celery task

**Agent:** `modular-builder`

**Files:**
- Create: `/opt/monorepo-workspace/universal-siem-monorepo/backend/scheduler/tasks/alert_evaluation.py`
- Modify: `/opt/monorepo-workspace/universal-siem-monorepo/backend/scheduler/celery_app.py`
- Create: `/opt/monorepo-workspace/universal-siem-monorepo/backend/tests/test_alert_evaluation.py`

**Steps:**

- [ ] Read reference files before writing:
  - `/opt/monorepo-workspace/universal-siem-monorepo/backend/scheduler/celery_app.py` lines 80-251 (beat schedule and autodiscovery)
  - Existing task files in `/opt/monorepo-workspace/universal-siem-monorepo/backend/scheduler/tasks/` to understand task module conventions

- [ ] **TDD — Write failing tests first** in `test_alert_evaluation.py`:

  Test cases to write:
  - `test_jexl_expression_true_when_cpu_above_threshold` — expression `cpu > 80` with context `{cpu: 90}` evaluates to True
  - `test_jexl_expression_false_when_cpu_below_threshold` — expression `cpu > 80` with context `{cpu: 70}` evaluates to False
  - `test_sustained_count_prevents_first_hit_from_firing` — consecutive_hits=1, sustained_count=3 -> no alert inserted
  - `test_sustained_count_fires_on_nth_hit` — consecutive_hits reaches sustained_count -> alert inserted to unified_alerts
  - `test_consecutive_hits_reset_on_false` — expression evaluates False -> consecutive_hits reset to 0
  - `test_cooldown_prevents_refiring` — alert fired, cooldown_minutes not elapsed -> no second alert inserted
  - `test_cooldown_allows_refiring_after_expiry` — cooldown elapsed -> alert fires again
  - `test_scope_agent_filter` — rule scoped to `agent_id=A` does not fire for `agent_id=B` metrics
  - `test_scope_all_fires_for_any_agent` — rule with empty scope fires for all agents

- [ ] Run tests to confirm they fail:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo/backend && uv run pytest tests/test_alert_evaluation.py -v 2>&1 | head -50
  ```
  Expected output: `FAILED` or `ERROR` for all test cases.

- [ ] Implement `alert_evaluation.py` with:
  - Celery task `evaluate_alert_rules` decorated with `@shared_task`
  - Logic flow:
    1. Query `SELECT * FROM siem.alert_rules WHERE enabled = true`
    2. For each rule: determine scope from `scope` JSONB, query latest metric window from appropriate CA
    3. Build context dict: `{cpu: float, memory: float, events: int, agent_id: str, hostname: str, ...}`
    4. Evaluate JEXL expression via `pyjexl.Jexl().evaluate(rule.expression, context)` — pyjexl is sandboxed and does not execute Python builtins
    5. If True: `consecutive_hits += 1`; if `consecutive_hits >= sustained_count`: insert into `siem.unified_alerts` with `source='rule_engine'`, reset `consecutive_hits = 0`, record `last_evaluated_at`
    6. If False: set `consecutive_hits = 0`, update `last_evaluated_at`
    7. Cooldown check: before inserting alert, query most recent alert from same rule; skip if within `cooldown_minutes`
  - Update `consecutive_hits` and `last_evaluated_at` in `siem.alert_rules` after each evaluation

- [ ] Register task in `celery_app.py` beat schedule (after line 236):
  ```python
  "evaluate-alert-rules-every-minute": {
      "task": "scheduler.tasks.alert_evaluation.evaluate_alert_rules",
      "schedule": crontab(minute="*"),
  },
  ```
- [ ] Add to autodiscovery list (lines 238-251):
  ```python
  "scheduler.tasks.alert_evaluation",
  ```

- [ ] Run tests to confirm they pass:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo/backend && uv run pytest tests/test_alert_evaluation.py -v
  ```
  Expected output: all 9 tests `PASSED`.

- [ ] Commit:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo && \
    git add backend/scheduler/tasks/alert_evaluation.py backend/scheduler/celery_app.py \
            backend/tests/test_alert_evaluation.py
  git commit -m "feat(alerts): add JEXL alert evaluation celery task"
  ```

---

### Task 5: Wire new routers into FastAPI app

**Agent:** `modular-builder`

**Files:**
- Modify: `/opt/monorepo-workspace/universal-siem-monorepo/backend/api/main.py`

**Steps:**

- [ ] Read `/opt/monorepo-workspace/universal-siem-monorepo/backend/api/main.py` lines 55-70 (import block) and lines 420-440 (router registration block).

- [ ] Add imports at lines 60-62 (after existing router imports):
  ```python
  from routers.metrics_router import router as metrics_router
  from routers.alert_rules_router import router as alert_rules_router
  ```

- [ ] Add `include_router` calls at lines 426-433 (after existing routers, before any middleware/exception handlers):
  ```python
  app.include_router(metrics_router)
  app.include_router(alert_rules_router)
  ```

- [ ] DO NOT remove `grafana_router` or `prometheus_router` imports or `include_router` calls — those are removed in Phase 3 (Task 15).

- [ ] Start the app and verify new routes are registered:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo/backend && uv run uvicorn api.main:app --host 0.0.0.0 --port 8001 &
  sleep 3
  curl -s http://localhost:8001/api/metrics/health | python3 -m json.tool
  curl -s http://localhost:8001/api/alert-rules | python3 -m json.tool
  kill %1
  ```
  Expected output: valid JSON responses (not 404).

- [ ] Verify existing routes still respond (no regression):
  ```bash
  curl -s http://localhost:8001/api/grafana/metrics/summary | python3 -m json.tool
  ```
  Expected output: existing response (not 404).

- [ ] Commit:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo && git add backend/api/main.py
  git commit -m "feat(api): wire metrics and alert-rules routers"
  ```

---

## Phase 1: Backend Integration Tests (Tasks 6-7)

### Task 6: Integration test — metrics API with real TimescaleDB data

**Agent:** `test-coverage`

**Files:**
- Create: `/opt/monorepo-workspace/universal-siem-monorepo/backend/tests/integration/test_metrics_integration.py`

**Steps:**

- [ ] Read `metrics_router.py` to understand all endpoints and resolution boundaries.
- [ ] Read existing integration tests (if any) to understand test DB setup patterns:
  ```bash
  ls /opt/monorepo-workspace/universal-siem-monorepo/backend/tests/integration/ 2>/dev/null || echo "No integration dir yet"
  ```

- [ ] Write integration tests:
  - `test_summary_returns_real_fleet_counts` — insert agent rows, call `/api/metrics/summary`, verify counts match
  - `test_resolution_boundary_1h_uses_raw` — insert into `agent_metrics`, query with `to - from = 1h`, verify `resolution == "raw"` in response
  - `test_resolution_boundary_6h_uses_5min` — query with 6h range, verify `resolution == "5min"`
  - `test_resolution_boundary_7d_uses_hourly` — query with 7d range, verify `resolution == "hourly"`
  - `test_resolution_boundary_90d_uses_daily` — query with 90d range, verify `resolution == "daily"`
  - `test_resolution_boundary_1y_uses_monthly` — query with 1y range, verify `resolution == "monthly"`
  - `test_response_format_maps_to_recharts` — verify `series[0].points` is a list of `{t, v}` objects
  - `test_compare_returns_multiple_series` — insert data for 2 agents, call `/api/metrics/compare`, verify 2 series returned

- [ ] Run integration tests:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo/backend && \
    uv run pytest tests/integration/test_metrics_integration.py -v
  ```
  Expected output: all 8 tests `PASSED`.

- [ ] Commit:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo && \
    git add backend/tests/integration/test_metrics_integration.py
  git commit -m "test: add metrics API integration tests"
  ```

---

### Task 7: Integration test — JEXL rules fire alerts

**Agent:** `test-coverage`

**Files:**
- Create: `/opt/monorepo-workspace/universal-siem-monorepo/backend/tests/integration/test_alert_rules_integration.py`

**Steps:**

- [ ] Read `alert_evaluation.py` and `alert_rules_router.py` to understand the full flow.

- [ ] Write integration tests:
  - `test_full_flow_rule_fires_alert` — create rule (sustained_count=1) -> insert metrics that match -> call `evaluate_alert_rules` -> verify row in `unified_alerts` with `source='rule_engine'`
  - `test_sustained_count_3_requires_3_consecutive_hits` — create rule (sustained_count=3) -> run evaluator once -> verify no alert -> run twice more -> verify alert fires on 3rd
  - `test_cooldown_blocks_second_alert_within_window` — fire alert -> run evaluator again immediately -> verify only 1 alert in unified_alerts
  - `test_cooldown_allows_alert_after_window` — fire alert -> manually backdate `last_evaluated_at` beyond cooldown -> run evaluator -> verify 2nd alert
  - `test_scope_agent_isolation` — create rule scoped to `agent_A` -> insert metrics for `agent_B` -> run evaluator -> verify no alert fired
  - `test_scope_all_fires_for_all_agents` — create rule with empty scope -> insert metrics for 3 agents -> run evaluator -> verify alert for all 3
  - `test_false_expression_resets_hits` — rule at consecutive_hits=2 -> expression evaluates false -> verify consecutive_hits=0 in DB

- [ ] Run integration tests:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo/backend && \
    uv run pytest tests/integration/test_alert_rules_integration.py -v
  ```
  Expected output: all 7 tests `PASSED`.

- [ ] Commit:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo && \
    git add backend/tests/integration/test_alert_rules_integration.py
  git commit -m "test: add alert rules integration tests"
  ```

---

## Phase 2: Frontend Rebuild (Tasks 8-14)

### Task 8: Create `useMetrics` hooks

**Agent:** `modular-builder`

**Files:**
- Create: `/opt/monorepo-workspace/universal-siem-monorepo/frontend/src/hooks/useMetrics.ts`

**Steps:**

- [ ] Read reference files before writing:
  - `/opt/monorepo-workspace/universal-siem-monorepo/frontend/src/hooks/useMonitoring.ts` (TanStack Query pattern to replicate)
  - `/opt/monorepo-workspace/universal-siem-monorepo/frontend/src/context/RealtimeContext.tsx` lines 281-288 (Supabase Realtime channel pattern)
  - `/opt/monorepo-workspace/universal-siem-monorepo/frontend/src/lib/supabase.ts` (supabase client singleton)
  - `/opt/monorepo-workspace/universal-siem-monorepo/frontend/src/services/api/client.ts` (axios client)

- [ ] Create `useMetrics.ts` with these hooks (DO NOT delete `useMonitoring.ts` — that is Phase 3):

  Exported types:
  ```typescript
  export type TimeRange = { from: string; to: string };
  export type MetricPoint = { t: string; v: number };
  export type MetricSeries = { agent_id: string; hostname: string; metric: string; points: MetricPoint[] };
  export type MetricsResponse = { series: MetricSeries[]; resolution: string; time_range: TimeRange };
  ```

  Exported hooks:
  - `useFleetSummary()` — GET /api/metrics/summary, refetchInterval: 30_000
  - `useAgentMetrics(agentId: string, timeRange: TimeRange)` — GET /api/metrics/agents/{id}, enabled: !!agentId
  - `useFleetMetrics(timeRange: TimeRange)` — GET /api/metrics/fleet
  - `useCompareAgents(agentIds: string[], metrics: string[], timeRange: TimeRange)` — GET /api/metrics/compare
  - `useAlertRules()` — GET /api/alert-rules + useMutation for create/update/delete/test; returns `{ rules, createRule, updateRule, deleteRule, testRule }`
  - `useRealtimeAlerts(tenantId: string)` — Supabase channel `tenant:{tenantId}:alerts`, event `alert_fired`; subscribe on mount, unsubscribe on unmount

  - Follow the exact TanStack Query pattern from `useMonitoring.ts`: `useQuery`, `staleTime: 60_000`, `refetchInterval` where appropriate
  - `useAlertRules` mutations use `useMutation` with `queryClient.invalidateQueries`

- [ ] Verify hooks compile with no TypeScript errors:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo/frontend && npx tsc --noEmit 2>&1 | grep useMetrics
  ```
  Expected output: no errors related to `useMetrics.ts`.

- [ ] Commit:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo && git add frontend/src/hooks/useMetrics.ts
  git commit -m "feat(ui): add useMetrics hooks for native monitoring"
  ```

---

### Task 9: Create `MetricChart` shared component

**Agent:** `component-designer`

**Files:**
- Create: `/opt/monorepo-workspace/universal-siem-monorepo/frontend/src/components/monitoring/MetricChart.tsx`

**Steps:**

- [ ] Read reference files before writing:
  - Find and read `PrometheusMetricsChart.tsx` lines 260-283 (direct Recharts pattern to replicate):
    ```bash
    find /opt/monorepo-workspace/universal-siem-monorepo/frontend/src -name "PrometheusMetricsChart.tsx"
    ```
  - `/opt/monorepo-workspace/universal-siem-monorepo/frontend/src/hooks/useMetrics.ts` (MetricSeries type)

- [ ] Create `components/monitoring/` directory if it does not exist.

- [ ] Implement `MetricChart.tsx` with:
  - Props interface:
    ```typescript
    interface MetricChartProps {
      agentId?: string;
      metrics: string[];
      timeRange: TimeRange;
      chartType: 'line' | 'area' | 'bar';
      height?: number;
      onTimeRangeChange?: (range: TimeRange) => void;
    }
    ```
  - Direct Recharts imports (NOT shadcn chart wrapper): `LineChart`, `AreaChart`, `BarChart`, `XAxis`, `YAxis`, `CartesianGrid`, `Tooltip`, `Legend`, `ResponsiveContainer`
  - HSL CSS variables for colors: `hsl(var(--primary))`, `hsl(var(--muted-foreground))`, `hsl(var(--destructive))`
  - `ResponsiveContainer` with `width="100%"` and configurable `height` (default 300)
  - Custom tooltip component showing timestamp and formatted value
  - Time range selector buttons: `1h | 6h | 24h | 7d | 30d | 90d`
  - Loading skeleton state using `Skeleton` from shadcn/ui (show when data is fetching)
  - Uses `useAgentMetrics` or `useFleetMetrics` hook internally based on whether `agentId` is provided

- [ ] Verify component compiles:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo/frontend && npx tsc --noEmit 2>&1 | grep MetricChart
  ```
  Expected output: no errors related to `MetricChart.tsx`.

- [ ] Commit:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo && \
    git add frontend/src/components/monitoring/MetricChart.tsx
  git commit -m "feat(ui): add MetricChart shared component"
  ```

---

### Task 10: Create `AlertRuleEditor` component

**Agent:** `component-designer`

**Files:**
- Create: `/opt/monorepo-workspace/universal-siem-monorepo/frontend/src/components/monitoring/AlertRuleEditor.tsx`

**Steps:**

- [ ] Read reference files before writing:
  - `/opt/monorepo-workspace/universal-siem-monorepo/frontend/src/hooks/useMetrics.ts` (AlertRule types, `testRule` mutation)
  - Find an existing Shadcn form example in the codebase:
    ```bash
    find /opt/monorepo-workspace/universal-siem-monorepo/frontend/src -name "*.tsx" | xargs grep -l "useForm\|react-hook-form" | head -3
    ```

- [ ] Implement `AlertRuleEditor.tsx` with:
  - Props interface:
    ```typescript
    interface AlertRuleEditorProps {
      rule?: AlertRule;           // undefined = create mode, defined = edit mode
      onSubmit: (data: AlertRuleCreate | AlertRuleUpdate) => void;
      onCancel: () => void;
    }
    ```
  - Shadcn form fields:
    - `name` — text input (required)
    - `description` — optional text input
    - `expression` — `<Textarea>` with monospace font, placeholder: `cpu > 80 && memory > 90`; show collapsible list of available metric variable names (`cpu`, `memory`, `events_per_second`, `disk_usage`, `agent_id`, `hostname`)
    - `sustained_count` — `<Slider>` from 1 to 10, default 3; label: "Fire after N consecutive hits"
    - `severity` — `<Select>` with options: `info`, `warning`, `critical`
    - `cooldown_minutes` — number input, min 1, max 1440
    - `scope` — radio group: "All agents" (empty scope) | "Specific agent" (shows agent picker) | "Agent group" (shows group picker)
    - `actions` — array builder: each action has `type` (email/webhook) and `target`; "Add Action" button adds new row; each row has a delete button
    - `enabled` — `<Switch>` toggle
  - "Test Rule" button: calls `testRule` mutation, shows inline result: "Matched" (green badge) or "No match" (muted) with context dict as JSON
  - Form validation: `expression` required, `name` required, `severity` required
  - Submit button label: "Create Rule" (create mode) or "Save Changes" (edit mode)

- [ ] Verify component compiles:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo/frontend && npx tsc --noEmit 2>&1 | grep AlertRuleEditor
  ```
  Expected output: no errors related to `AlertRuleEditor.tsx`.

- [ ] Commit:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo && \
    git add frontend/src/components/monitoring/AlertRuleEditor.tsx
  git commit -m "feat(ui): add AlertRuleEditor component"
  ```

---

### Task 11: Build Overview tab

**Agent:** `modular-builder`

**Files:**
- Create: `/opt/monorepo-workspace/universal-siem-monorepo/frontend/src/pages/monitoring/tabs/OverviewTab.tsx`

**Steps:**

- [ ] Read reference files before writing:
  - `/opt/monorepo-workspace/universal-siem-monorepo/frontend/src/hooks/useMetrics.ts` (`useFleetSummary`, `useFleetMetrics`, `useRealtimeAlerts`)
  - `/opt/monorepo-workspace/universal-siem-monorepo/frontend/src/components/monitoring/MetricChart.tsx`
  - Find an existing card/stats component pattern:
    ```bash
    find /opt/monorepo-workspace/universal-siem-monorepo/frontend/src -name "*.tsx" | xargs grep -l "CardHeader\|StatsCard" | head -3
    ```

- [ ] Create `tabs/` directory inside `pages/monitoring/` if it does not exist.

- [ ] Implement `OverviewTab.tsx` with:
  - Fleet health cards row (6 cards): Total Agents, Online, Offline, Avg CPU %, Avg Memory %, Events/s — data from `useFleetSummary()`; each card shows a trend indicator (up/down vs previous value)
  - Fleet CPU AreaChart using `<MetricChart metrics={['cpu']} chartType="area" />` with default 24h range
  - Fleet Memory AreaChart using `<MetricChart metrics={['memory']} chartType="area" />` with same time range
  - Alert activity section: last 24h alerts from `useAlertRules()`, shown as a timeline list (severity badge, title, agent, timestamp)
  - Supabase Realtime integration: call `useRealtimeAlerts(tenantId)` -> on `alert_fired` event, invalidate `['fleetSummary']` and `['alertRules']` queries
  - Loading skeletons for all sections while data is fetching

- [ ] Verify component compiles:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo/frontend && npx tsc --noEmit 2>&1 | grep OverviewTab
  ```
  Expected output: no errors related to `OverviewTab.tsx`.

- [ ] Commit:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo && \
    git add frontend/src/pages/monitoring/tabs/OverviewTab.tsx
  git commit -m "feat(ui): add monitoring Overview tab"
  ```

---

### Task 12: Build Agents tab

**Agent:** `modular-builder`

**Files:**
- Create: `/opt/monorepo-workspace/universal-siem-monorepo/frontend/src/pages/monitoring/tabs/AgentsTab.tsx`

**Steps:**

- [ ] Read reference files before writing:
  - `/opt/monorepo-workspace/universal-siem-monorepo/frontend/src/hooks/useMetrics.ts` (`useFleetSummary`, `useAgentMetrics`, `useCompareAgents`)
  - `/opt/monorepo-workspace/universal-siem-monorepo/frontend/src/components/monitoring/MetricChart.tsx`
  - Find an existing Shadcn Sheet/Drawer usage:
    ```bash
    find /opt/monorepo-workspace/universal-siem-monorepo/frontend/src -name "*.tsx" | xargs grep -l "Sheet\|Drawer" | head -3
    ```

- [ ] Implement `AgentsTab.tsx` with:
  - Time range selector at the top: `1h | 6h | 24h | 7d | 30d | 90d` (shared state across all charts on this tab)
  - Compare mode toggle button: "Compare" (off) / "Comparing N agents" (on)
  - Agent grid: responsive CSS grid (3-4 cols desktop, 1-2 cols mobile); each card shows:
    - Status dot (green = online, red = offline, grey = unknown) based on last_seen timestamp
    - Hostname as card title, Agent ID as subtitle
    - Sparkline CPU and Memory (last 1h, small Recharts `LineChart` without axes)
    - Checkbox visible when compare mode is active
  - Agent detail Shadcn `<Sheet>` (right-side drawer): opens on card click; content:
    - Full `<MetricChart>` for CPU, Memory, Events/s, Buffer (4 charts stacked)
    - Time range selector inside drawer
    - Agent metadata: hostname, OS, version, last seen
  - Compare mode: when 2-3 agents checked, show "View Comparison" button -> opens full-width comparison using `useCompareAgents`, overlays selected agents' CPU and Memory on shared charts

- [ ] Verify component compiles:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo/frontend && npx tsc --noEmit 2>&1 | grep AgentsTab
  ```
  Expected output: no errors related to `AgentsTab.tsx`.

- [ ] Commit:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo && \
    git add frontend/src/pages/monitoring/tabs/AgentsTab.tsx
  git commit -m "feat(ui): add monitoring Agents tab"
  ```

---

### Task 13: Build Alert Rules tab

**Agent:** `modular-builder`

**Files:**
- Create: `/opt/monorepo-workspace/universal-siem-monorepo/frontend/src/pages/monitoring/tabs/AlertRulesTab.tsx`

**Steps:**

- [ ] Read reference files before writing:
  - `/opt/monorepo-workspace/universal-siem-monorepo/frontend/src/hooks/useMetrics.ts` (`useAlertRules`)
  - `/opt/monorepo-workspace/universal-siem-monorepo/frontend/src/components/monitoring/AlertRuleEditor.tsx`
  - Find an existing table + dialog pattern:
    ```bash
    find /opt/monorepo-workspace/universal-siem-monorepo/frontend/src -name "*.tsx" | xargs grep -l "AlertDialog" | head -3
    ```

- [ ] Implement `AlertRulesTab.tsx` with:
  - Shadcn `<Table>` with columns: Name, Expression (truncated to 60 chars), Severity (badge), Enabled (switch), Last Fired, Consecutive Hits, Actions
  - "Create Rule" button in table header -> opens `<AlertRuleEditor>` in a Shadcn `<Dialog>`
  - Actions column per row: "Edit" button (opens `<AlertRuleEditor>` pre-filled), "Test" button (calls `testRule`, shows toast), "Delete" button (opens `<AlertDialog>` confirm)
  - Enabled column: inline `<Switch>` calling `updateRule({ enabled: !current })` on toggle
  - Empty state: "No alert rules yet. Create your first rule to get started." with Create button
  - Loading state: skeleton rows while `useAlertRules` fetches
  - After create/update/delete: `queryClient.invalidateQueries(['alertRules'])`

- [ ] Verify component compiles:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo/frontend && npx tsc --noEmit 2>&1 | grep AlertRulesTab
  ```
  Expected output: no errors related to `AlertRulesTab.tsx`.

- [ ] Commit:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo && \
    git add frontend/src/pages/monitoring/tabs/AlertRulesTab.tsx
  git commit -m "feat(ui): add monitoring Alert Rules tab"
  ```

---

### Task 14: Rebuild `MonitoringPage` with native tabs

**Agent:** `modular-builder`

**Files:**
- Modify: `/opt/monorepo-workspace/universal-siem-monorepo/frontend/src/pages/monitoring/MonitoringPage.tsx`

**Steps:**

- [ ] Read the current file fully:
  ```bash
  cat /opt/monorepo-workspace/universal-siem-monorepo/frontend/src/pages/monitoring/MonitoringPage.tsx
  ```
  Note lines 36-101 (EmbeddedDashboard component) and lines 104-148 (hardcoded dashboards array) — both are removed.

- [ ] Read the three new tab components to understand their imports:
  - `frontend/src/pages/monitoring/tabs/OverviewTab.tsx`
  - `frontend/src/pages/monitoring/tabs/AgentsTab.tsx`
  - `frontend/src/pages/monitoring/tabs/AlertRulesTab.tsx`

- [ ] Rewrite `MonitoringPage.tsx`:
  - Remove `EmbeddedDashboard` component (lines 36-101)
  - Remove `DASHBOARDS` array (lines 104-148)
  - Remove Grafana health badge from page header
  - Import `OverviewTab`, `AgentsTab`, `AlertRulesTab`
  - Import Shadcn `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent`
  - Keep the page header and breadcrumb
  - Replace iframe content with:
    ```tsx
    <Tabs defaultValue="overview">
      <TabsList>
        <TabsTrigger value="overview">Overview</TabsTrigger>
        <TabsTrigger value="agents">Agents</TabsTrigger>
        <TabsTrigger value="alert-rules">Alert Rules</TabsTrigger>
      </TabsList>
      <TabsContent value="overview"><OverviewTab /></TabsContent>
      <TabsContent value="agents"><AgentsTab /></TabsContent>
      <TabsContent value="alert-rules"><AlertRulesTab /></TabsContent>
    </Tabs>
    ```
  - Route (`/monitoring`), lazy loading, `routes.tsx` and `App.tsx` entries remain UNCHANGED

- [ ] Verify the page compiles:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo/frontend && npx tsc --noEmit 2>&1 | grep MonitoringPage
  ```
  Expected output: no errors.

- [ ] Run full frontend build to verify no broken imports:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo/frontend && npm run build 2>&1 | tail -20
  ```
  Expected output: `built in Xs` with no errors.

- [ ] Commit:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo && git add frontend/src/pages/monitoring/MonitoringPage.tsx
  git commit -m "feat(ui): rebuild MonitoringPage with native tabs"
  ```

---

## Phase 3: Cleanup & Cutover (Tasks 15-19)

### Task 15: Remove old monitoring endpoints

**Agent:** `modular-builder`

**Files:**
- Modify: `/opt/monorepo-workspace/universal-siem-monorepo/backend/api/main.py`
- Delete: `/opt/monorepo-workspace/universal-siem-monorepo/backend/routers/grafana_router.py`
- Delete: `/opt/monorepo-workspace/universal-siem-monorepo/backend/routers/prometheus_router.py`
- Delete: `/opt/monorepo-workspace/universal-siem-monorepo/backend/grafana-dashboards/` (entire directory)

**Steps:**

- [ ] Verify no other file imports from `grafana_router` or `prometheus_router` besides `main.py`:
  ```bash
  grep -r "grafana_router\|prometheus_router" /opt/monorepo-workspace/universal-siem-monorepo/backend/ --include="*.py" | grep -v main.py
  ```
  Expected output: no results.

- [ ] Remove imports and `include_router` calls from `main.py` for both grafana_router and prometheus_router.

- [ ] Delete the router files:
  ```bash
  rm /opt/monorepo-workspace/universal-siem-monorepo/backend/routers/grafana_router.py
  rm /opt/monorepo-workspace/universal-siem-monorepo/backend/routers/prometheus_router.py
  ```

- [ ] Delete grafana-dashboards directory:
  ```bash
  rm -rf /opt/monorepo-workspace/universal-siem-monorepo/backend/grafana-dashboards/
  ```

- [ ] Restart backend and confirm old routes return 404 (not 500):
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo/backend && uv run uvicorn api.main:app --host 0.0.0.0 --port 8001 &
  sleep 3
  curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/grafana/metrics/summary
  curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/prometheus/metrics
  kill %1
  ```
  Expected output: `404` for both.

- [ ] Confirm new routes still respond:
  ```bash
  curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/metrics/health
  ```
  Expected output: `200`.

- [ ] Commit:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo && git add -u
  git commit -m "refactor: remove Grafana and Prometheus routers"
  ```

---

### Task 16: Remove old frontend monitoring code

**Agent:** `modular-builder`

**Files:**
- Delete: `/opt/monorepo-workspace/universal-siem-monorepo/frontend/src/hooks/useMonitoring.ts`
- Delete: `/opt/monorepo-workspace/universal-siem-monorepo/frontend/src/pages/System/components/MonitoringTab.tsx`
- Modify: `/opt/monorepo-workspace/universal-siem-monorepo/frontend/src/App.tsx`
- Modify: `/opt/monorepo-workspace/universal-siem-monorepo/frontend/src/config/routes.tsx`

**Steps:**

- [ ] Grep for all remaining consumers of `useMonitoring` and `MonitoringTab`:
  ```bash
  grep -r "useMonitoring\|MonitoringTab" /opt/monorepo-workspace/universal-siem-monorepo/frontend/src/ --include="*.ts" --include="*.tsx" -l
  ```

- [ ] Fix any remaining imports in the files found above before deleting.

- [ ] Read `App.tsx` around line 246, remove the `/system/monitoring` route.

- [ ] Read `routes.tsx` around line 86, remove `ROUTES.SYSTEM_MONITORING` and the `MonitoringTab` lazy import.

- [ ] Delete the files:
  ```bash
  rm /opt/monorepo-workspace/universal-siem-monorepo/frontend/src/hooks/useMonitoring.ts
  rm /opt/monorepo-workspace/universal-siem-monorepo/frontend/src/pages/System/components/MonitoringTab.tsx
  ```

- [ ] Verify no remaining references:
  ```bash
  grep -r "useMonitoring\|MonitoringTab\|SYSTEM_MONITORING" \
    /opt/monorepo-workspace/universal-siem-monorepo/frontend/src/ \
    --include="*.ts" --include="*.tsx"
  ```
  Expected output: no results.

- [ ] Run full frontend build to confirm no broken imports:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo/frontend && npm run build 2>&1 | tail -20
  ```
  Expected output: `built in Xs` with no errors.

- [ ] Commit:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo && \
    git add -u frontend/src/hooks/useMonitoring.ts \
              frontend/src/pages/System/components/MonitoringTab.tsx \
              frontend/src/App.tsx \
              frontend/src/config/routes.tsx
  git commit -m "refactor: remove old monitoring hooks and System tab"
  ```

---

### Task 17: Update `RealtimeContext` for alert rules channel

**Agent:** `modular-builder`

**Files:**
- Modify: `/opt/monorepo-workspace/universal-siem-monorepo/frontend/src/context/RealtimeContext.tsx`

**Steps:**

- [ ] Read the full `RealtimeContext.tsx`, especially lines 281-295.

- [ ] Verify the existing `siem.unified_alerts` subscription covers JEXL engine alerts — they insert into the same table with `source='rule_engine'`, so no new channel is needed.

- [ ] Add a convenience hook at the bottom of the file (after all existing exports):
  ```typescript
  /**
   * Returns real-time alerts filtered to those fired by the JEXL rule engine.
   * Uses the existing unified_alerts subscription from RealtimeContext.
   */
  export function useAlertRuleRealtime() {
    const { alerts } = useRealtime();
    return alerts.filter((alert) => alert.source === 'rule_engine');
  }
  ```

- [ ] Verify the file compiles:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo/frontend && npx tsc --noEmit 2>&1 | grep RealtimeContext
  ```
  Expected output: no errors.

- [ ] Commit:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo && \
    git add frontend/src/context/RealtimeContext.tsx
  git commit -m "feat(ui): add alert rule realtime convenience hook"
  ```

---

### Task 18: Security review

**Agent:** `security-guardian`

**File scope:** All new and modified files from Tasks 0-17.

**Steps:**

- [ ] Review `siem.alert_rules` RLS policies in migration 051:
  - Verify tenant isolation: user from tenant A cannot read/write tenant B's rules
  - Verify service_role policy allows Celery to access rules without tenant context
  - Check `created_by` — should it have a FK constraint?

- [ ] Review SQL in `metrics_router.py` for injection vulnerabilities:
  - Verify all queries use parameterized placeholders (`$1`, `$2`), never f-strings or `.format()` with user input
  - Verify `agent_id` path parameter is validated as UUID before use in queries
  - Verify time range parameters are parsed as datetime objects, not raw strings in SQL

- [ ] Review JEXL expression sandboxing in `alert_evaluation.py`:
  - `pyjexl` evaluates JEXL (not Python) — verify no Python builtins are accessible through JEXL expressions
  - Attempt to inject a path traversal or denial-of-service expression such as an infinite loop or very long string concatenation — verify pyjexl handles these safely
  - If pyjexl does not adequately sandbox: add expression validation that whitelists allowed operators and rejects expressions containing `__`, `import`, or Python keywords

- [ ] Review tenant isolation in all new endpoints:
  - `metrics_router.py`: verify tenant_id from auth token filters all queries
  - `alert_rules_router.py`: verify RLS context is set before every query (not just create)
  - `alert_evaluation.py`: verify service role bypass is intentional and Celery does not leak cross-tenant data in context dicts

- [ ] Review Supabase Realtime channel scoping:
  - Channel name `tenant:{tenantId}:alerts` — verify tenantId comes from auth JWT, not request body
  - Verify a user cannot subscribe to another tenant's channel by guessing the name
  - Verify `realtime.send` with broadcast=true correctly scopes delivery to subscribed clients only

- [ ] Document all findings with file:line references and severity: Critical / High / Medium / Low / Info.

- [ ] Fix all Critical and High findings. For each fix:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo && git add <affected files>
  git commit -m "fix(security): <specific finding>"
  ```

- [ ] Final rollup commit if multiple fixes:
  ```bash
  git commit -m "fix(security): address monitoring pipeline review findings"
  ```

---

### Task 19: E2E verification

**Agent:** `test-coverage`

**Files:**
- Create: `/opt/monorepo-workspace/universal-siem-monorepo/backend/tests/e2e/test_monitoring_e2e.py`

**Steps:**

- [ ] Read all new backend files to understand the full end-to-end flow:
  - `metrics_router.py`, `alert_rules_router.py`, `alert_evaluation.py`

- [ ] Write E2E test `test_full_monitoring_pipeline`:
  1. Insert row into `siem.agent_metrics` simulating agent heartbeat (cpu=85, memory=70)
  2. Query `/api/metrics/agents/{agent_id}?from=...&to=...`, verify the metric appears
  3. Verify response format: `response["series"][0]["points"][0]` has `t` and `v` keys
  4. POST `/api/alert-rules` with `expression="cpu > 80"`, `sustained_count=1`
  5. Insert `agent_metrics` row with cpu=90
  6. Call `evaluate_alert_rules.delay().get(timeout=30)`
  7. Query `siem.unified_alerts` where `source='rule_engine'`, verify 1 row exists
  8. Verify Realtime trigger exists (skip channel delivery test if Supabase infra unavailable in test env):
     ```bash
     PGPASSWORD='7oBuuQ1fmKQMjNI0Hro6s9RShMwCDOzc' psql -U siem_user -h localhost -d siem_timeseries \
       -c "SELECT trigger_name FROM information_schema.triggers WHERE trigger_name = 'unified_alerts_realtime';"
     ```

- [ ] Write E2E test `test_alert_does_not_fire_without_sustained_count`:
  1. Create rule with `sustained_count=3`, `expression="cpu > 80"`
  2. Insert 2 metrics with cpu=90
  3. Run evaluator twice
  4. Verify zero rows in unified_alerts for this rule

- [ ] Write E2E test `test_metrics_resolution_selection_end_to_end`:
  1. Insert raw metric for an agent
  2. Query with 1h range -> verify `resolution == "raw"`
  3. Query with 7d range -> verify `resolution == "hourly"`

- [ ] Run E2E tests:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo/backend && \
    uv run pytest tests/e2e/test_monitoring_e2e.py -v --timeout=60
  ```
  Expected output: all 3 E2E tests `PASSED`.

- [ ] Commit:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo && \
    git add backend/tests/e2e/test_monitoring_e2e.py
  git commit -m "test: add monitoring pipeline E2E test"
  ```

---

## Phase 4: Infrastructure Decommission (Tasks 20-21)

### Task 20: Remove Prometheus/Grafana from infrastructure

**Agent:** `modular-builder`

**Steps:**

- [ ] Find all infrastructure files referencing Prometheus or Grafana:
  ```bash
  grep -r "prometheus\|grafana" /opt/monorepo-workspace/universal-siem-monorepo/ \
    --include="docker-compose*.yml" --include="*.yaml" --include="*.yml" \
    --include="*.conf" --include="*.ini" --include="*.j2" -l
  ```

- [ ] For each docker-compose file: remove the `prometheus` and `grafana` service blocks, their volumes, and any `depends_on` references to them.

- [ ] For each k8s manifest: remove Prometheus and Grafana `Deployment`, `Service`, `ConfigMap`, and `PersistentVolumeClaim` resources.

- [ ] For each Ansible playbook/role: remove Prometheus and Grafana installation and configuration tasks.

- [ ] For each nginx config: remove `location /grafana` proxy blocks and upstream definitions for Grafana.

- [ ] Grep the entire repo for remaining "grafana" and "prometheus" references and fix or remove them:
  ```bash
  grep -r "grafana\|prometheus" /opt/monorepo-workspace/universal-siem-monorepo/ \
    --include="*.py" --include="*.ts" --include="*.tsx" --include="*.yml" \
    --include="*.yaml" --include="*.conf" -l
  ```

- [ ] Verify backend starts cleanly after infra changes:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo/backend && uv run uvicorn api.main:app --host 0.0.0.0 --port 8001 &
  sleep 3
  curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/metrics/health
  kill %1
  ```
  Expected output: `200`.

- [ ] Commit:
  ```bash
  cd /opt/monorepo-workspace/universal-siem-monorepo && git add -u
  git commit -m "ops: remove Prometheus and Grafana from infrastructure"
  ```

---

### Task 21: Update documentation

**Agent:** `modular-builder`

**Files:**
- Modify: `/opt/universal-siem-docs/Operations/Monitoring.md`
- Create: `/opt/universal-siem-docs/Backend/Metrics-API.md`
- Create: `/opt/universal-siem-docs/Backend/Alert-Rules.md`

**Steps:**

- [ ] Read current `/opt/universal-siem-docs/Operations/Monitoring.md`.
- [ ] List existing Backend docs to follow naming conventions:
  ```bash
  ls /opt/universal-siem-docs/Backend/
  ```

- [ ] Rewrite `Monitoring.md` with:
  - New architecture overview (ASCII diagram: agents -> FastAPI -> TimescaleDB CAs -> React + Celery Beat -> unified_alerts -> Supabase Realtime -> React)
  - TimescaleDB CA resolution table (1h=raw, 6-24h=5min, 7-30d=hourly, 90d=daily, 1y=monthly)
  - How to access the monitoring dashboard (`/monitoring`, 3 tabs: Overview, Agents, Alert Rules)
  - How to create and test alert rules (UI walkthrough)
  - How JEXL expressions work (syntax, available variables: `cpu`, `memory`, `events_per_second`, `disk_usage`, `agent_id`, `hostname`)
  - Celery beat schedule entry for `evaluate_alert_rules` (runs every minute)
  - Supabase Realtime channel format: `tenant:{tenantId}:alerts`, event: `alert_fired`
  - Note: "Prometheus and Grafana have been removed as of 2026-03-10"

- [ ] Create `Backend/Metrics-API.md` documenting:
  - All endpoints with path, method, query params, response schema
  - Resolution selection logic table
  - Response format (series/points/resolution/time_range)
  - asyncpg connection pool setup

- [ ] Create `Backend/Alert-Rules.md` documenting:
  - `siem.alert_rules` schema with column descriptions
  - CRUD API endpoints
  - JEXL expression syntax and available context variables
  - `sustained_count` and `cooldown_minutes` behavior with examples
  - How to use the test endpoint
  - Celery task evaluation flow

- [ ] Archive old Grafana troubleshooting docs:
  ```bash
  find /opt/universal-siem-docs/ -name "*grafana*" -o -name "*Grafana*" | head -10
  ```
  Move any found files to `/opt/universal-siem-docs/Archive/` with a note at the top: "Archived 2026-03-10 — Grafana removed, replaced by native monitoring pipeline."

- [ ] Commit:
  ```bash
  cd /opt/universal-siem-docs && git add -A
  git commit -m "docs: update monitoring documentation for native pipeline"
  ```

---

## Summary

| Phase | Tasks | Agent(s) | Deliverables |
|-------|-------|----------|--------------|
| 0: Foundation | 0-5 | database-architect, modular-builder | Migration 051, pyjexl dep, metrics_router, alert_rules_router, alert_evaluation, wired into app |
| 1: Integration Tests | 6-7 | test-coverage | 15 integration tests: CA resolution, JEXL logic, sustained_count, cooldown, scope filtering |
| 2: Frontend Rebuild | 8-14 | modular-builder, component-designer | useMetrics, MetricChart, AlertRuleEditor, OverviewTab, AgentsTab, AlertRulesTab, rebuilt MonitoringPage |
| 3: Cleanup | 15-19 | modular-builder, security-guardian, test-coverage | Old routers deleted, old frontend removed, RealtimeContext updated, security audit complete, E2E tests passing |
| 4: Infra Decommission | 20-21 | modular-builder | Prometheus/Grafana removed from docker-compose/k8s/ansible/nginx, docs updated |

**Total tasks:** 22
**Total commits:** 22 (one per task)
**New backend files:** migration 051, metrics_router.py, alert_rules_router.py, alert_evaluation.py + 5 test files
**New frontend files:** useMetrics.ts, MetricChart.tsx, AlertRuleEditor.tsx, OverviewTab.tsx, AgentsTab.tsx, AlertRulesTab.tsx, rebuilt MonitoringPage.tsx
**Files deleted:** grafana_router.py, prometheus_router.py, grafana-dashboards/, useMonitoring.ts, MonitoringTab.tsx
