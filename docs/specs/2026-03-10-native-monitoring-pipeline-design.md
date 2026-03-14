# Native Monitoring Pipeline — Replace Prometheus + Grafana

**Date:** 2026-03-10
**Status:** Approved
**Complexity:** Medium (22 tasks, 4 phases)

## Problem

The current SIEM monitoring stack has multiple issues:
- `/api/grafana/metrics/summary` returns hardcoded mock data
- Monitoring page relies entirely on Grafana iframes — if Grafana is down, monitoring is blank
- Prometheus is a proxy layer adding infrastructure overhead without deep integration
- No native Recharts on monitoring pages despite using Recharts everywhere else
- No flexible alert conditions — alerts come from fixed sources only (snort, anomaly, security)
- No WebSocket push for monitoring (5-10s polling only)
- Two extra services (Prometheus + Grafana) to maintain

## Goal

Replace Prometheus + Grafana with a native monitoring pipeline:
- TimescaleDB continuous aggregates for metrics storage and downsampling
- FastAPI metrics router with smart resolution selection
- JEXL-based alert expression engine evaluated by Celery
- Native Recharts monitoring dashboard (no iframes)
- Supabase Realtime for push notifications (no custom WebSocket server)

## Architecture

```
Agents → Backend API → TimescaleDB (continuous aggregates) → React Dashboard
                ↓
         Celery Beat (1min) → JEXL rule evaluation → unified_alerts
                                                         ↓
                                              Supabase Realtime trigger
                                                         ↓
                                              React (supabase.channel())
```

## Changes

### Backend — New Files

#### `backend/routers/metrics_router.py`
Replaces both `grafana_router.py` and `prometheus_router.py`.

Endpoints:
- `GET /api/metrics/summary` — Fleet health quick-stats (real data, not mock)
- `GET /api/metrics/agents/{agent_id}` — Single agent time-series
- `GET /api/metrics/fleet` — Fleet-wide aggregated metrics
- `GET /api/metrics/compare` — Side-by-side agent comparison
- `POST /api/metrics/query` — Flexible parameterized query
- `GET /api/metrics/health` — System health overview

Smart resolution selection by time range:
- Last 1 hour → agent_metrics (raw, 1-min)
- Last 6 hours → metrics_5min
- Last 24 hours → metrics_5min
- Last 7 days → metrics_hourly
- Last 30 days → metrics_hourly
- Last 90 days → metrics_daily
- Last 1 year → metrics_monthly

Response format (maps directly to Recharts):
```json
{
  "series": [
    {
      "agent_id": "agent-001",
      "hostname": "DC-SERVER-01",
      "metric": "cpu_usage_percent",
      "points": [
        {"t": "2026-03-10T16:00:00Z", "v": 42.5}
      ]
    }
  ],
  "resolution": "5min",
  "time_range": {"from": "...", "to": "..."}
}
```

#### `backend/routers/alert_rules_router.py`
CRUD for user-defined JEXL alert rules.

Endpoints:
- `GET /api/alert-rules` — List rules (tenant-scoped via RLS)
- `POST /api/alert-rules` — Create rule
- `PUT /api/alert-rules/{id}` — Update rule
- `DELETE /api/alert-rules/{id}` — Delete rule
- `POST /api/alert-rules/{id}/test` — Test rule against latest data without firing

#### `backend/scheduler/tasks/evaluate_alert_rules.py`
Celery task running every 1 minute:
1. Fetch all enabled alert_rules
2. For each rule: query latest metrics, build context dict, evaluate JEXL expression
3. If TRUE: increment consecutive_hits; if >= sustained_count → insert into unified_alerts + execute actions
4. If FALSE: reset consecutive_hits to 0

Python JEXL library: `pyjexl` (pip install pyjexl)

### Database — Migrations

#### New table: `siem.alert_rules`
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

#### New continuous aggregate: `metrics_monthly`
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

#### Supabase Realtime trigger on unified_alerts
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

#### Schema grants for Supabase
```sql
GRANT USAGE ON SCHEMA siem TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA siem TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA siem
  GRANT ALL ON TABLES TO anon, authenticated, service_role;
```

### Frontend — New/Modified Files

#### New: `src/hooks/useMetrics.ts`
Replaces `src/hooks/useMonitoring.ts`. TanStack Query hooks:
- `useFleetSummary()` — GET /api/metrics/summary
- `useAgentMetrics(agentId, timeRange)` — GET /api/metrics/agents/{id}
- `useFleetMetrics(timeRange)` — GET /api/metrics/fleet
- `useCompareAgents(agentIds, metrics, timeRange)` — GET /api/metrics/compare
- `useAlertRules()` — CRUD hooks for alert rules
- `useRealtimeAlerts(tenantId)` — Supabase Realtime subscription

#### New: `src/components/monitoring/MetricChart.tsx`
Shared Recharts component for all metric visualizations.
Props: agentId, metrics[], timeRange, chartType (line/area/bar).

#### Rebuilt: `src/pages/monitoring/MonitoringPage.tsx`
Three tabs:
1. **Overview** — Fleet health cards (live) + fleet charts + alert timeline
2. **Agents** — Agent grid with sparklines + detail drawer + compare mode
3. **Alert Rules** — Rule list + editor + test + history

#### New: `src/components/monitoring/AlertRuleEditor.tsx`
Shadcn form: expression input, sustained count slider, severity selector, scope picker, action builder, test button.

### Files Deleted

- `backend/routers/grafana_router.py`
- `backend/routers/prometheus_router.py`
- `backend/grafana-dashboards/*.json`
- `frontend/src/hooks/useMonitoring.ts`
- `frontend/src/pages/monitoring/MonitoringPage.tsx` (rebuilt)
- `frontend/src/pages/System/components/MonitoringTab.tsx` (merged into monitoring page)

### Infrastructure Removed (Phase 4, after validation)

- Prometheus service from docker-compose / k8s / ansible
- Grafana service from docker-compose / k8s / ansible
- Grafana-related nginx proxy rules

## Impact

- **Agents:** No changes — heartbeat protocol unchanged
- **Users:** Better monitoring experience, user-defined alert rules
- **Ops:** Two fewer services to maintain (Prometheus + Grafana)
- **Performance:** Faster queries via TimescaleDB CAs vs PromQL proxy

## Agent Allocation

| Phase | Agent | Responsibility |
|-------|-------|---------------|
| Codebase Research | agentic-search | Pre-implementation recon |
| Database | database-architect | Migrations, CAs, RLS, triggers |
| API Design | api-contract-designer | Metrics API contract |
| Implementation | modular-builder | Backend + frontend |
| UI Components | component-designer | MetricChart, AlertRuleEditor |
| Testing | test-coverage | Unit + integration + E2E |
| Security | security-guardian | RLS audit |
| Architecture | zen-architect | Final review |
| Cleanup | post-task-cleanup | Remove dead code + infra |

## Test Plan

- [ ] Metrics API returns real data from TimescaleDB (not mocks)
- [ ] Smart resolution selects correct CA per time range
- [ ] JEXL rule evaluates correctly against metric context
- [ ] Sustained count prevents single-spike false alerts
- [ ] Cooldown prevents alert spam after firing
- [ ] RLS enforces tenant isolation on alert_rules
- [ ] Supabase Realtime delivers alert to correct tenant channel
- [ ] Recharts renders time-series from API response without transformation
- [ ] Agent compare mode overlays multiple series
- [ ] Alert rule test button evaluates without firing
- [ ] Old Grafana/Prometheus endpoints return 410 Gone during transition
- [ ] E2E: heartbeat → metric stored → chart renders → rule fires → alert appears in UI
