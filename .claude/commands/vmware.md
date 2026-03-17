---
description: "VMware infrastructure administration: diagnose ESXi/VCSA/NSX issues, generate PowerCLI commands, troubleshoot vmkernel errors, investigate vSphere failures."
---

# /vmware — VMware Infrastructure Administration

## Overview

Diagnose VMware issues, analyze ESXi/VCSA/NSX logs, generate PowerCLI commands, troubleshoot vmkernel errors, investigate vSphere failures, and produce infrastructure remediation steps.

**Announce at start:** "VMware Admin: analyzing $ARGUMENTS"

## Usage

```
/vmware <query or symptom>
```

## Arguments

$ARGUMENTS

Free-form description of the VMware issue, question, or task. Examples:

- `/vmware ESXi host not responding after patch`
- `/vmware VCSA disk space alert on partition /storage/seat`
- `/vmware generate PowerCLI to migrate VMs off host for maintenance`
- `/vmware vmkernel WARNING: Heap_Align`
- `/vmware NSX distributed firewall rules not applying`
- `/vmware storage latency high on datastore NFS01`

## Execution

Dispatch the `vmware-infrastructure` agent with the user's query:

```
Agent(subagent_type="vmware-infrastructure", prompt=<user query + any context>)
```

The agent has access to: Glob, Grep, LS, Read, WebFetch, TodoWrite, WebSearch, BashOutput, KillBash, Bash.

## Capabilities

| Area | What it can do |
|------|---------------|
| **ESXi** | Log analysis, vmkernel errors, hardware health, storage paths, networking |
| **VCSA** | Service health, disk partitions, database issues, certificate expiry |
| **NSX** | Distributed firewall, logical switches, edge services, transport nodes |
| **PowerCLI** | Generate scripts for bulk operations, migrations, reporting |
| **Troubleshooting** | Root cause analysis from logs, event correlation, remediation steps |
| **Capacity** | VM placement, resource contention, DRS/HA configuration review |

## Output Format

The agent produces structured output:

```
## VMware Analysis: <topic>

### Current State
<observed symptoms, log entries, metrics>

### Diagnosis
<root cause hypothesis with evidence>

### Recommended Action
<specific steps with PowerCLI/esxcli commands>

### Verification
<commands to confirm the fix worked>
```

## Effort Steering

| Query type | Effort | Reasoning |
|------------|--------|-----------|
| PowerCLI generation | low | Templated output |
| Log analysis | medium | Pattern matching across logs |
| Root cause analysis | high | Complex correlation across components |

## Integration

**Pairs with:**
- `/debug` — For systematic hypothesis-driven analysis of complex VMware failures
- `/recall vmware` — Search local docs for past VMware investigations
- Context7 / WebSearch — For VMware KB articles and documentation

## Red Flags

- Never run destructive PowerCLI commands (Remove-VM, Remove-Datastore) without user confirmation
- Never put a host in maintenance mode without checking DRS/HA can accommodate the migration
- Never modify NSX firewall rules without understanding the current rule set
- Always verify after every remediation action
