# /exchange — Comprehensive Exchange Server 2019 Administration Skill

**Date:** 2026-03-14
**Status:** Validated Design
**Author:** Amplifier Design Session

---

## Problem

No Exchange-specific administration command exists in Amplifier. Exchange DAG management, health monitoring, and troubleshooting require manual PowerShell sessions. Existing Exchange code in FuseCP handles multi-tenant mailbox operations but not server-level DAG administration. There is no structured way to run health checks, perform safe maintenance operations, or correlate diagnostic data across the two-node DAG.

## Goal

Build a `/exchange` command with three subcommands:

- **health** — monitoring dashboard with PASS/WARN/FAIL output across 8 check categories
- **admin** — safe operation wrapper with validate→confirm→execute→verify pattern
- **troubleshoot** — hypothesis-driven investigation with event log correlation

All PowerShell runs via script files to avoid Git Bash argument mangling. Documentation access follows a three-tier strategy: local reference doc (instant), recall BM25 index, and Context7 live Microsoft docs.

---

## Lab Environment

| Host | IP | Role |
|------|----|------|
| EXCHANGELAB | 172.31.251.103 | Exchange 2019 node 1 |
| EXCHANGELAB2 | 172.31.251.104 | Exchange 2019 node 2 |
| FuseCP-DAG | 172.31.251.110 | DAG cluster VIP |
| FINALTEST | 172.31.251.101 | AD/DNS, file share witness |
| DEV | 172.31.251.100 | Orchestration host (CredSSP origin) |

Connection method: CredSSP via WinRM from DEV. All scripts use `New-PSSession` with `Authentication CredSSP`.

---

## Changes

### `/exchange health [--server <name>] [--full]`

Quick health dashboard. Default runs the top 4 fast checks. `--full` runs all 8.

| Check | Cmdlet | Default |
|-------|--------|---------|
| Database copy status | `Get-MailboxDatabaseCopyStatus` | Yes |
| Replication health | `Test-ReplicationHealth` | Yes |
| Service health | `Test-ServiceHealth` | Yes |
| Server components | `Get-ServerComponentState` | Yes |
| Mail flow | `Test-Mailflow` | Full only |
| Transport queues | `Get-Queue` | Full only |
| Certificates | `Get-ExchangeCertificate` | Full only |
| DAG network | `Get-DatabaseAvailabilityGroupNetwork` | Full only |

Output format: structured table with status (PASS/WARN/FAIL), server, check name, detail. Exit non-zero on any FAIL.

### `/exchange admin <operation>`

Safe operation wrapper. Every operation runs: validate → confirm → execute → verify. User confirmation is mandatory before execute. Post-operation verification runs automatically.

Supported operations:

| Operation | Description |
|-----------|-------------|
| `switchover` | Move active database copy to passive node |
| `maintenance-on` | Enter maintenance mode (6-step procedure) |
| `maintenance-off` | Exit maintenance mode |
| `reseed` | Reseed a database copy |
| `suspend` | Suspend database copy replication |
| `resume` | Resume database copy replication |
| `queue-drain` | Drain transport queues before maintenance |
| `cert-renew` | Renew Exchange certificate |

The 6-step maintenance-on procedure:
1. Suspend cluster node
2. Set ServerWideOffline component state
3. Redirect messages via `Redirect-Message`
4. Suspend database copies
5. Set maintenance mode in DAG
6. Stop cluster service

### `/exchange troubleshoot <symptom>`

Hypothesis-driven investigation. Phases: gather → correlate → diagnose → recommend.

Supported symptoms:

| Symptom | Primary Checks | Event Sources |
|---------|---------------|---------------|
| `mail-flow` | Queue depth, connectors, SMTP logs | MSExchangeTransport, Application |
| `replication` | Copy status, queue lengths, network | MSExchangeRepl, System |
| `content-index` | Catalog state, crawler status | MSExchangeFastSearch |
| `database` | Mountability, disk space, copy lag | MSExchangeIS, System |
| `client-access` | RPC, OWA, Autodiscover, ActiveSync | MSExchangeRPC, IIS |
| `certificate` | Expiry, services bound, chain | Security, Application |
| `performance` | CPU, memory, disk I/O, processor queues | System, PerfLib |

For unrecognized error codes, fall back to `mcp__context7__query-docs` with library `/websites/learn_microsoft_en-us_exchange` (35K snippets).

### PowerShell Script Library (`scripts/exchange/`)

All scripts: parameterized, structured output (JSON or formatted tables), CredSSP auth.

| Script | Purpose |
|--------|---------|
| `exchange-health.ps1` | Full 8-check health dashboard |
| `exchange-health-quick.ps1` | Fast 4-check health |
| `exchange-connect.ps1` | CredSSP session helper (returns reusable session) |
| `exchange-maintenance-on.ps1` | Enter maintenance (6-step) |
| `exchange-maintenance-off.ps1` | Exit maintenance |
| `exchange-switchover.ps1` | Database switchover with verification |
| `exchange-troubleshoot.ps1` | Gather diagnostic data for a given symptom |

Script invocation pattern from Git Bash:
```bash
powershell -File scripts/exchange/exchange-health.ps1 -Server EXCHANGELAB -Full
```

Never use `-Command` with inline PowerShell — Git Bash mangles quotes and special characters.

### Documentation Access (Three-Tier)

| Tier | Source | How |
|------|--------|-----|
| 1 | `docs/reference/exchange-admin.md` | Direct read — instant, no network |
| 2 | `/recall exchange <topic>` | BM25 FTS5 over local session history |
| 3 | `mcp__context7__query-docs` | Live Microsoft Exchange docs, 35K snippets |

The command checks Tier 1 first. Escalates to Tier 2 for context from past sessions. Escalates to Tier 3 for unknown cmdlets, error codes, or procedures not in the reference doc.

---

## Files Changed

| File | Change |
|------|--------|
| `.claude/commands/exchange.md` | NEW — main command with 3 subcommands |
| `scripts/exchange/exchange-health.ps1` | NEW — full 8-check health dashboard |
| `scripts/exchange/exchange-health-quick.ps1` | NEW — fast 4-check health |
| `scripts/exchange/exchange-connect.ps1` | NEW — CredSSP session helper |
| `scripts/exchange/exchange-maintenance-on.ps1` | NEW — enter maintenance mode |
| `scripts/exchange/exchange-maintenance-off.ps1` | NEW — exit maintenance mode |
| `scripts/exchange/exchange-switchover.ps1` | NEW — database switchover |
| `scripts/exchange/exchange-troubleshoot.ps1` | NEW — diagnostic data gather |
| `docs/reference/exchange-admin.md` | NEW — cmdlet reference (built separately) |

---

## Agent Allocation

| Phase | Agent | Role | Responsibility |
|-------|-------|------|---------------|
| Research | agentic-search | scout | Review existing Exchange provider + ExchangeTools in FuseCP |
| Command | modular-builder | implement | Write `/exchange` command file |
| Scripts | modular-builder | implement | Build PowerShell script library |
| Integration | integration-specialist | implement | Wire Context7 + recall + ntfy notifications |
| Validation | spec-reviewer | review | Verify against lab environment |
| Cleanup | post-task-cleanup | fast | Final hygiene pass |

---

## Test Plan

- [ ] `/exchange health` runs the 4 default checks on EXCHANGELAB and prints PASS/WARN/FAIL
- [ ] `/exchange health --full` runs all 8 checks and returns structured report
- [ ] `/exchange admin switchover` moves active database with pre/post verification
- [ ] `/exchange admin maintenance-on` completes the 6-step procedure and prompts for confirmation
- [ ] `/exchange admin maintenance-off` reverses maintenance state and verifies components
- [ ] `/exchange troubleshoot replication` identifies copy queue issues and provides recommendations
- [ ] Context7 queries return relevant Exchange 2019 documentation snippets
- [ ] `/recall exchange` finds session history and the local reference doc
- [ ] All PowerShell scripts run via `-File` (not `-Command`) to avoid Git Bash mangling
- [ ] CredSSP sessions connect successfully from DEV to EXCHANGELAB and EXCHANGELAB2
