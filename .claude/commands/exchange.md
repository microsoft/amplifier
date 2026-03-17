---
description: "Exchange Server 2019 administration: health monitoring, DAG operations, maintenance mode, troubleshooting. Three modes: health, admin, troubleshoot."
platforms: ["windows"]
---

# /exchange — Exchange Server Administration

## Overview

Comprehensive Exchange 2019/SE administration via PowerShell remoting. Three subcommands: health monitoring, administrative operations, and troubleshooting.

**Announce at start:** "Exchange Admin: <subcommand> on <target>."

## Usage

```
/exchange health [--server <name>] [--full]
/exchange admin <operation> [args]
/exchange troubleshoot <symptom>
```

## Arguments

$ARGUMENTS

## Lab Environment

| Server | IP | Role |
|--------|-----|------|
| EXCHANGELAB | 172.31.251.103 | Exchange 2019 node 1 |
| EXCHANGELAB2 | 172.31.251.104 | Exchange 2019 node 2 |
| FuseCP-DAG | 172.31.251.110 | DAG cluster VIP |
| FINALTEST | 172.31.251.101 | AD/DNS, file share witness |

**Connection:** CredSSP via WinRM from DEV (172.31.251.100).

## PowerShell Execution Pattern

All Exchange operations use pre-built PowerShell scripts in `scripts/exchange/`. NEVER use inline `powershell -Command` — Git Bash mangles dollar signs.

```bash
powershell -File "C:/claude/amplifier/scripts/exchange/<script>.ps1" -Parameter "value"
```

Parse output by `|` delimiter. Format: `PHASE|STEP|STATUS|DETAILS` or `DATA|TYPE|IDENTITY|VALUES`.

## Documentation Access

Three tiers for Exchange cmdlet reference:

1. **Local:** `docs/reference/exchange-admin.md` — common cmdlets, copy-paste ready
2. **Recall:** `/recall exchange <topic>` — BM25 search across indexed docs
3. **Context7:** `mcp__context7__query-docs(libraryId='/websites/learn_microsoft_en-us_exchange', query='<cmdlet or topic>')` — 35K Microsoft docs snippets, use for deep dives or unfamiliar cmdlets

---

## Subcommand: `health`

### Parse flags
- No flags or `--server <name>`: quick health (4 checks)
- `--full`: all 8 checks

### Quick Health (default)

```bash
C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -File "C:/claude/amplifier/scripts/exchange/exchange-health-quick.ps1"
```

### Full Health

```bash
C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -File "C:/claude/amplifier/scripts/exchange/exchange-health.ps1"
```

**Note:** Exchange Management Shell requires **Windows PowerShell 5.1** (not pwsh 7). Always use the full path `C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe`. Default auth is Kerberos (implicit credentials). For DAG cross-node operations requiring double-hop, pass `-Auth Credssp`.

### Present Results

Parse pipe-delimited output and present as a dashboard:

```
## Exchange Health Report

| Check | Status | Details |
|-------|--------|---------|
| DatabaseCopy: DAG-DB01\EXCHANGELAB | PASS | Mounted, CI=Healthy |
| DatabaseCopy: DAG-DB01\EXCHANGELAB2 | PASS | Healthy, CopyQ=0 |
| ReplicationHealth: ClusterNetwork | PASS | |
| ServiceHealth: Mailbox | PASS | RequiredRunning=True |
| ...

Summary: X PASS, Y WARN, Z FAIL
```

If any FAIL: suggest specific remediation. If unfamiliar with the failure, query Context7:
```
mcp__context7__query-docs(libraryId='/websites/learn_microsoft_en-us_exchange', query='<failure description>')
```

---

## Subcommand: `admin <operation>`

### Available Operations

| Operation | Script | Risk | User Confirm? |
|-----------|--------|------|--------------|
| `switchover <db> [target]` | exchange-switchover.ps1 | Medium | YES |
| `maintenance-on <server>` | exchange-maintenance-on.ps1 | High | YES |
| `maintenance-off <server>` | exchange-maintenance-off.ps1 | High | YES |
| `reseed <db> <server>` | (inline PS) | Medium | YES |
| `suspend <db> <server>` | (inline PS) | Low | NO |
| `resume <db> <server>` | (inline PS) | Low | NO |

### Safety Pattern (ALL operations)

1. **Pre-check** — verify current state before acting
2. **Impact assessment** — count affected mailboxes, databases
3. **User confirmation** — STOP and wait (except Low risk)
4. **Execute** — run PowerShell script
5. **Post-verify** — re-check affected components
6. **Notify** — ntfy.sh push for long operations

### Switchover

```bash
powershell -File "C:/claude/amplifier/scripts/exchange/exchange-switchover.ps1" -Database "DAG-DB01" -TargetServer "EXCHANGELAB2"
```

Parse PHASE output. Stop at `PHASE|CONFIRM|WAITING` — present impact to user and wait for confirmation. After "yes", the script continues automatically.

**For manual confirmation flow:** Run the script, capture the CONFIRM line, present to user, then if approved run `Move-ActiveMailboxDatabase` directly via a small confirm script.

### Maintenance Mode

**Enter:**
```bash
powershell -File "C:/claude/amplifier/scripts/exchange/exchange-maintenance-on.ps1" -TargetServer "EXCHANGELAB"
```

Reports 6 phases. Present each phase result as it completes. Final output confirms 0 active databases and 0 active components on target.

**Exit:**
```bash
powershell -File "C:/claude/amplifier/scripts/exchange/exchange-maintenance-off.ps1" -TargetServer "EXCHANGELAB"
```

Reports 5 phases. Verifies all components back to Active.

### Reseed (inline)

For database copy reseed, write and execute a targeted script:

```powershell
# Write to scripts/exchange/exchange-reseed.ps1
Suspend-MailboxDatabaseCopy -Identity "$Database\$Server" -Confirm:$false
Update-MailboxDatabaseCopy -Identity "$Database\$Server" -DeleteExistingFiles -Confirm:$false
```

Monitor progress with `Get-MailboxDatabaseCopyStatus` until Status returns to Healthy.

### Suspend / Resume (low risk, no confirm)

```powershell
Suspend-MailboxDatabaseCopy -Identity "$Database\$Server" -Confirm:$false
Resume-MailboxDatabaseCopy -Identity "$Database\$Server" -Confirm:$false
```

---

## Subcommand: `troubleshoot <symptom>`

### Available Symptoms

| Symptom | Investigates |
|---------|-------------|
| `mail-flow` | Test-MailFlow, queues, transport service, transport events |
| `replication` | Copy status, replication health, MSExchangeRepl events |
| `content-index` | ContentIndexState per database copy |
| `database` | Database size, mount state, paths, free space |
| `certificate` | Expiry dates, services bound, self-signed status |
| `performance` | Queue backlogs, mailbox distribution, mounted DB locations |

### Execution

```bash
powershell -File "C:/claude/amplifier/scripts/exchange/exchange-troubleshoot.ps1" -Symptom "replication"
```

### Analysis Pattern

After gathering diagnostic data:

1. **Parse output** — group DATA and EVENT lines by type
2. **Identify anomalies** — unhealthy statuses, high queue lengths, error events
3. **Correlate timeline** — when did events start? what changed?
4. **Form hypothesis** — root cause based on evidence
5. **Recommend fix** — specific remediation steps with verification commands
6. **Context7 fallback** — for unfamiliar error codes or event IDs:
   ```
   mcp__context7__query-docs(libraryId='/websites/learn_microsoft_en-us_exchange', query='event ID <number> Exchange replication')
   ```

### Present Results

```
## Troubleshoot: replication

### Current State
| Database Copy | Status | CopyQ | ReplayQ |
|--------------|--------|-------|---------|
| DAG-DB01\EXCHANGELAB | Mounted | - | - |
| DAG-DB01\EXCHANGELAB2 | Healthy | 0 | 0 |

### Events (last 20)
| Time | Event ID | Level | Message |
|------|----------|-------|---------|
| 14:22:03 | 1221 | Warning | Copy queue building... |

### Diagnosis
<root cause hypothesis with evidence>

### Recommended Action
<specific steps with PowerShell commands>

### Verification
<commands to confirm the fix worked>
```

---

## Effort Steering

| Subcommand | Effort | Reasoning |
|------------|--------|-----------|
| health | low | Read-only checks |
| admin | high | Production changes need deep reasoning |
| troubleshoot | high | Complex correlation across multiple systems |

## Integration

**Pairs with:**
- `/fix-bugs` — Exchange-area bugs may need server-level investigation
- `/verify` — Include Exchange health as verification evidence
- `/recall exchange` — Search local Exchange reference docs

**Documentation:**
- `docs/reference/exchange-admin.md` — cmdlet reference
- Context7: `/websites/learn_microsoft_en-us_exchange` (35K snippets)

## Common Mistakes

**Using inline powershell -Command**
- Fix: Always use `-File` with script files. Git Bash breaks `$` in inline commands.

**Connecting to the server being maintained**
- Fix: Maintenance scripts auto-connect to the PARTNER server, not the target.

**Running admin operations without checking health first**
- Fix: Always run `/exchange health` before `/exchange admin`.

## Red Flags

- Never run maintenance-on without confirming the partner server is healthy
- Never reseed while the active copy is on the same server
- Never ignore CredSSP connection failures — they mean the double-hop chain is broken
- Always verify after every admin operation — the post-check is not optional
