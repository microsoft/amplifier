# Hyper-V Cluster Awareness Design Spec

**Date:** 2026-03-01
**Status:** Approved
**Author:** Claude (validated design)

---

## Problem

FuseCP's Hyper-V provider has zero cluster awareness. Every VM operation routes to a specific host via `{host}` in the API URL and executes PowerShell commands such as `Get-VM -Id '{guid}'` against that one WinRM target. This causes four concrete failures:

1. **VM lookup fails after live migration** — `Get-VM -Id` only searches the local node; a VM that has migrated is invisible from its former host.
2. **VM creation uses local paths** — VMs are created under `C:\Hyper-V\` on the target host. VMs on local storage cannot be live-migrated.
3. **No owner-node resolution** — The API has no mechanism to determine which cluster node currently owns a VM.
4. **No cluster operations** — Live migration, node maintenance mode, and cluster health monitoring are entirely absent.

All 40+ PowerShell commands in the provider are single-host only. The provider factory caches host→provider mappings at startup and never refreshes. SolidCP (the predecessor) also lacked cluster support; its `Services.ClusterID` column is a grouping concept only, not functional cluster management.

---

## Goal

1. Configure a Windows Failover Cluster between FUSECP (172.31.251.100) and HYPERVLAB (172.31.251.102) with shared iSCSI storage and a file share witness.
2. Make FuseCP's Hyper-V provider fully cluster-aware so it correctly manages VMs that migrate between cluster nodes.
3. Expose live migration, node maintenance mode, and cluster health monitoring through the FuseCP API and Portal.

---

## Current State

### Infrastructure

| Host | IP | RAM | vCPU | Free Disk | Notes |
|------|----|-----|------|-----------|-------|
| FUSECP | 172.31.251.100 | 32 GB | 8 | 129 GB | Hyper-V installed, 0 VMs, Failover Clustering NOT installed |
| HYPERVLAB | 172.31.251.102 | 24 GB | 4 | 221 GB | Hyper-V installed, 2 VMs (off), Failover Clustering NOT installed |

Both servers run Windows Server 2025, are members of `lab.ergonet.pl`, and run as VMware VMs (nested virtualization). iSCSI initiators are configured:

- FUSECP: `iqn.1991-05.com.microsoft:dev.lab.ergonet.pl`
- HYPERVLAB: `iqn.1991-05.com.microsoft:hypervlab.lab.ergonet.pl`

### FuseCP Code

| File | Role |
|------|------|
| `src/FuseCP.Providers.HyperV/HyperVProvider.cs` | Standalone single-host provider, 40+ PS commands all using `Get-VM -Id` against local node |
| `src/FuseCP.EnterpriseServer/Services/HyperVProviderFactory.cs` | `Dictionary<string, IHyperVProvider>` keyed by hostname, initialized once at startup, never refreshed |
| `src/FuseCP.Providers.HyperV/HyperVScripts.cs` | All PowerShell command strings |
| `src/FuseCP.EnterpriseServer/Endpoints/HyperVEndpoints.cs` | All routes under `/api/hyperv/{host}` |
| `src/FuseCP.Providers.HyperV/Models/VirtualMachine.cs` | VM response model |
| `src/FuseCP.Providers.HyperV/Models/VmUpdateRequest.cs` | VM mutation request model |
| `src/FuseCP.Database/Repositories/SolidCP/IHyperVRepository.cs` | VM count queries only |

---

## Changes

### Part 1: Infrastructure — Failover Cluster Setup

**Prerequisites provided by user:**
- iSCSI target with at least one LUN accessible from both nodes.
- File share path on FINALTEST for quorum witness.

**Cluster creation sequence (PowerShell on FUSECP):**

```powershell
# 1. Install Failover Clustering on both nodes
Install-WindowsFeature -Name Failover-Clustering -IncludeManagementTools -ComputerName FUSECP
Install-WindowsFeature -Name Failover-Clustering -IncludeManagementTools -ComputerName HYPERVLAB

# 2. Connect iSCSI targets on both nodes and format/partition the shared LUN
# (run on both nodes via WinRM; exact LUN IQN filled in at setup time)

# 3. Validate cluster prerequisites
Test-Cluster -Node FUSECP, HYPERVLAB -Include "Storage", "Network", "Hyper-V Configuration"

# 4. Create cluster with static IP
New-Cluster -Name LabCluster -Node FUSECP, HYPERVLAB -StaticAddress 172.31.251.105

# 5. Configure File Share Witness
Set-ClusterQuorum -Cluster LabCluster -FileShareWitness \\FINALTEST\ClusterWitness

# 6. Add shared LUN as Cluster Shared Volume
Add-ClusterSharedVolume -Name "Cluster Disk 1"
# Resulting path on both nodes: C:\ClusterStorage\Volume1\

# 7. Enable Live Migration with Kerberos auth on both nodes
Enable-VMMigration
Set-VMMigrationNetwork 172.31.251.0/24
Set-VMHost -VirtualMachineMigrationAuthenticationType Kerberos

# 8. Add DNS A record
Add-DnsServerResourceRecordA -ZoneName lab.ergonet.pl -Name LabCluster -IPv4Address 172.31.251.105
```

**Deliverable:** PowerShell setup script at `scripts/cluster-setup/Setup-HyperVCluster.ps1`.

---

### Part 2: Database Schema (Additive Only)

All changes are strictly additive. No existing columns or tables are altered or dropped.

**New columns on `Servers` table:**

```sql
ALTER TABLE Servers ADD HyperVClusterName NVARCHAR(255) NULL;
ALTER TABLE Servers ADD HyperVClusterRole NVARCHAR(50) NULL;
-- HyperVClusterRole values: 'Node' (cluster member) or 'Standalone' (unmanaged)
-- NULL means legacy row — treated as Standalone
```

**New table `HyperVClusters`:**

```sql
CREATE TABLE HyperVClusters (
    ClusterID    INT IDENTITY(1,1) PRIMARY KEY,
    ClusterName  NVARCHAR(255) NOT NULL,
    ClusterFqdn  NVARCHAR(255) NOT NULL,
    ClusterIP    NVARCHAR(50)  NOT NULL,
    CsvPath      NVARCHAR(500) NOT NULL,
    QuorumType   NVARCHAR(50)  NULL,
    CreatedAt    DATETIME      DEFAULT GETDATE(),
    IsActive     BIT           DEFAULT 1
);
```

**Migration script location:** `src/FuseCP.Database/Migrations/2026-03-01-HyperVCluster.sql`

---

### Part 3: Provider Layer

#### New interface `IHyperVClusterProvider`

Extends `IHyperVProvider` (no changes to the base interface). All methods are async.

```csharp
public interface IHyperVClusterProvider : IHyperVProvider
{
    // Cluster topology
    Task<IEnumerable<ClusterNode>> GetClusterNodesAsync();
    Task<IEnumerable<VirtualMachine>> GetClusterVmsAsync();
    Task<ClusterHealth> GetClusterHealthAsync();

    // Owner resolution
    Task<string> GetVmOwnerNodeAsync(Guid vmId);

    // VM cluster operations
    Task MigrateVmAsync(Guid vmId, string destinationNode);

    // Node maintenance
    Task MigrateAllVmsFromNodeAsync(string sourceNode);
    Task SetNodeMaintenanceAsync(string node, bool enterMaintenance);
}
```

**File:** `src/FuseCP.Providers.HyperV/IHyperVClusterProvider.cs`

#### Owner Node Resolution Pattern

Every overridden VM operation in `HyperVClusterProvider` first resolves the current owner node before executing against that node. This is implemented as a private helper:

```csharp
private async Task<string> ResolveOwnerNodeAsync(Guid vmId)
{
    // Executes: Get-ClusterGroup -Cluster {clusterFqdn} |
    //           Where-Object { $_.GroupType -eq 'VirtualMachine' -and $_.Name -eq '{vmId}' } |
    //           Select-Object -ExpandProperty OwnerNode
    var script = HyperVClusterScripts.GetVmOwnerNode(vmId, _clusterFqdn);
    var result = await _clusterEntryProvider.ExecutePowerShellAsync(script);
    return result.FirstOrDefault()?.ToString()
        ?? throw new InvalidOperationException($"VM {vmId} not found in cluster {_clusterFqdn}");
}
```

All inherited VM operations (`GetVmAsync`, `StartVmAsync`, `StopVmAsync`, `CreateSnapshotAsync`, etc.) are overridden to call `ResolveOwnerNodeAsync` first, then forward execution to the per-node WinRM connection.

#### New `HyperVClusterProvider`

- Wraps per-node `HyperVProvider` instances (one per node, maintained in an internal dictionary).
- Overrides all VM operations from `IHyperVProvider` to inject owner-node resolution.
- Adds all cluster-specific operations from `IHyperVClusterProvider`.
- VM creation uses `CsvPath` (from `HyperVClusters.CsvPath`, default `C:\ClusterStorage\Volume1\`) and registers the VM via `Add-ClusterVirtualMachineRole`.

**File:** `src/FuseCP.Providers.HyperV/HyperVClusterProvider.cs`

#### New `HyperVClusterScripts`

Static class containing all cluster-aware PowerShell command strings. No PowerShell is inlined elsewhere.

Key script groups:

| Script | PowerShell Cmdlet |
|--------|--------------------|
| `GetClusterNodes` | `Get-ClusterNode -Cluster {fqdn}` |
| `GetClusterVms` | `Get-ClusterGroup -Cluster {fqdn} \| Where GroupType -eq VirtualMachine` |
| `GetVmOwnerNode` | `(Get-ClusterGroup -Cluster {fqdn} -Name {vmId}).OwnerNode.Name` |
| `MigrateVm` | `Move-VM -Name {vmId} -ComputerName {sourceNode} -DestinationHost {destNode} -DestinationStoragePath {csvPath}` |
| `MigrateAllVmsFromNode` | `Get-ClusterGroup ... \| Move-ClusterVirtualMachineRole -MigrationType Live` |
| `SetNodeMaintenance` | `Suspend-ClusterNode -Name {node} -Drain` / `Resume-ClusterNode -Name {node}` |
| `GetClusterHealth` | `Get-Cluster -Name {fqdn} \| Select Name, QuorumState` combined with `Get-ClusterNode` |
| `RegisterClusterVm` | `Add-ClusterVirtualMachineRole -VirtualMachine {name} -Cluster {fqdn}` |

**File:** `src/FuseCP.Providers.HyperV/HyperVClusterScripts.cs`

---

### Part 4: Factory Changes

`HyperVProviderFactory` gains cluster support while keeping the existing standalone path unchanged.

**New methods:**

```csharp
// Existing — unchanged signature and behavior
Task<IHyperVProvider> GetProviderAsync(string host);

// New
Task<IHyperVClusterProvider> GetClusterProviderAsync(string clusterName);
Task<IEnumerable<string>> GetAllClusterNamesAsync();
Task<bool> IsClusterNodeAsync(string host);
```

**Initialization changes:**

- At startup (or on first access), factory reads `HyperVClusters` table and builds one `HyperVClusterProvider` per active cluster.
- `Servers.HyperVClusterRole` is consulted to determine whether a host is a standalone or a cluster node.
- Cluster providers are cached by `ClusterName`. The cache is refreshed when `GetClusterProviderAsync` is called and the cluster name is not found (handles new clusters added at runtime).

**File:** `src/FuseCP.EnterpriseServer/Services/HyperVProviderFactory.cs`

---

### Part 5: API Endpoints

All existing standalone routes remain unchanged.

**New cluster route group** registered in `HyperVClusterEndpoints.cs`:

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/api/hyperv/clusters` | List all clusters (name, IP, node count, health) |
| `GET` | `/api/hyperv/clusters/{cluster}` | Cluster health: quorum state, node states, VM count |
| `GET` | `/api/hyperv/clusters/{cluster}/vms` | All VMs across cluster, each with `ownerNode` |
| `POST` | `/api/hyperv/clusters/{cluster}/vms` | Create VM on cluster (uses CSV path, registers as HA) |
| `GET` | `/api/hyperv/clusters/{cluster}/vms/{vmId}` | VM detail; auto-resolves current owner node |
| `POST` | `/api/hyperv/clusters/{cluster}/vms/{vmId}/migrate` | Live migrate to specified destination node |
| `POST` | `/api/hyperv/clusters/{cluster}/vms/{vmId}/{action}` | Start / stop / snapshot; routes to owner node |
| `GET` | `/api/hyperv/clusters/{cluster}/nodes` | Node list with state (Up, Down, Paused) |
| `POST` | `/api/hyperv/clusters/{cluster}/nodes/{node}/maintenance` | Drain all VMs then pause node |
| `POST` | `/api/hyperv/clusters/{cluster}/nodes/{node}/resume` | Resume node from maintenance |

**Authorization:** All cluster endpoints require `PlatformAdmin` role. Tenant-scoped API keys receive `403 Forbidden`.

**VM response model — new fields added to `VirtualMachine.cs`:**

```csharp
public string? OwnerNode { get; set; }       // null for standalone VMs
public string? ClusterName { get; set; }     // null for standalone VMs
public bool IsHighlyAvailable { get; set; }  // true when registered as cluster resource
```

**Files:**
- New: `src/FuseCP.EnterpriseServer/Endpoints/HyperVClusterEndpoints.cs`
- Modified: `src/FuseCP.Providers.HyperV/Models/VirtualMachine.cs`

---

### Part 6: Portal UI

**Navigation changes:**

- The existing "Hyper-V" section in the sidebar gains two subsections: "Standalone Hosts" (existing pages, unchanged) and "Clusters" (new).

**Cluster overview page (`/portal/hyperv/clusters/{cluster}`):**

- Health bar: cluster name, quorum status (Healthy / DegradedQuorum / NoQuorum), last-updated timestamp.
- Nodes table: columns — Name, State (Up/Down/Paused), CPU %, Memory %, VM Count. Row actions: Enter Maintenance, Resume.
- VMs table: columns — Name, State, Owner Node, CPU, Memory. Row actions: Start, Stop, Migrate, Snapshot.

**Migration dialog:**

- Source node: read-only, auto-filled from current `ownerNode`.
- Destination node: dropdown populated from nodes in state `Up`, excluding the source node.
- Confirm button executes `POST /api/hyperv/clusters/{cluster}/vms/{vmId}/migrate`.
- On success: table row updates with new `ownerNode`.

**Maintenance flow:**

- Enter Maintenance button opens a warning dialog listing VMs that will be drained.
- On confirm: `POST /api/hyperv/clusters/{cluster}/nodes/{node}/maintenance`.
- Node row updates to state `Paused`; VMs table updates with new owner nodes.
- Resume button: `POST /api/hyperv/clusters/{cluster}/nodes/{node}/resume`.

**Razor pages affected:**
- New: `src/FuseCP.Portal/Pages/HyperV/Clusters/Index.cshtml` (cluster list)
- New: `src/FuseCP.Portal/Pages/HyperV/Clusters/Detail.cshtml` (cluster overview, nodes, VMs)
- Modified: `src/FuseCP.Portal/Pages/Shared/_HyperVNav.cshtml` (or equivalent nav partial)

---

### Part 7: Testing

**Infrastructure validation (manual, pre-code):**

- [ ] Both nodes show `Up` in `Get-ClusterNode`
- [ ] Quorum healthy: `Get-ClusterQuorum` shows `NodeAndFileShareMajority`
- [ ] CSV accessible on both nodes: `Test-Path C:\ClusterStorage\Volume1\` returns `True` from both
- [ ] Manual live migration via PowerShell succeeds: `Move-VM` completes without error

**API integration tests** (script: `scripts/api-tests/Run-ClusterIntegrationTests.ps1`):

| # | Test | Method | Endpoint | Expected |
|---|------|--------|----------|----------|
| 1 | List clusters | GET | `/api/hyperv/clusters` | `[{ "name": "LabCluster", ... }]` |
| 2 | Cluster health | GET | `/api/hyperv/clusters/LabCluster` | `{ "quorumState": "Healthy", "nodes": [...] }` |
| 3 | Create cluster VM | POST | `/api/hyperv/clusters/LabCluster/vms` | `201` with `isHighlyAvailable: true`, path under `C:\ClusterStorage\Volume1\` |
| 4 | List cluster VMs | GET | `/api/hyperv/clusters/LabCluster/vms` | All VMs present, each with non-null `ownerNode` |
| 5 | VM detail | GET | `/api/hyperv/clusters/LabCluster/vms/{id}` | VM detail with correct `ownerNode` |
| 6 | Start VM | POST | `/api/hyperv/clusters/LabCluster/vms/{id}/start` | `200`, VM state becomes `Running` |
| 7 | Stop VM | POST | `/api/hyperv/clusters/LabCluster/vms/{id}/stop` | `200`, VM state becomes `Off` |
| 8 | Live migrate | POST | `/api/hyperv/clusters/LabCluster/vms/{id}/migrate` | `200`, `ownerNode` changes to destination |
| 9 | Post-migration start | POST | `/api/hyperv/clusters/LabCluster/vms/{id}/start` | `200` — routes to new owner node |
| 10 | Snapshot | POST | `/api/hyperv/clusters/LabCluster/vms/{id}/snapshot` | `200` — routes to current owner node |
| 11 | Node list | GET | `/api/hyperv/clusters/LabCluster/nodes` | Both nodes present, state `Up` |
| 12 | Enter maintenance | POST | `/api/hyperv/clusters/LabCluster/nodes/HYPERVLAB/maintenance` | `200`, node state becomes `Paused`, VMs drained to FUSECP |
| 13 | Resume node | POST | `/api/hyperv/clusters/LabCluster/nodes/HYPERVLAB/resume` | `200`, node state returns to `Up` |
| 14 | Tenant key rejected | GET | `/api/hyperv/clusters` (tenant key) | `403 Forbidden` |
| 15 | Standalone routes unbroken | GET | `/api/hyperv/HYPERVLAB/vms` | `200`, existing behavior unchanged |

**Failure scenario tests:**

| Scenario | Expected Behavior |
|----------|-------------------|
| `GET /clusters/{c}/vms/{id}` where VM migrated since last request | Provider calls `GetVmOwnerNodeAsync`, re-routes to correct node, returns `200` |
| Enter maintenance with running VMs | All running VMs drained via live migration before node is paused; returns `200` only after drain completes |
| `POST /vms` (create) with one node Down | VM created on remaining Up node; returns `201` with `ownerNode` set to the Up node |

---

## Impact

### Files to Create (6)

| File | Purpose |
|------|---------|
| `src/FuseCP.Providers.HyperV/IHyperVClusterProvider.cs` | New cluster provider interface |
| `src/FuseCP.Providers.HyperV/HyperVClusterProvider.cs` | Cluster provider implementation |
| `src/FuseCP.Providers.HyperV/HyperVClusterScripts.cs` | Cluster PowerShell command strings |
| `src/FuseCP.EnterpriseServer/Endpoints/HyperVClusterEndpoints.cs` | Cluster API route group |
| `src/FuseCP.Providers.HyperV/Models/HyperVCluster.cs` | ClusterNode, ClusterHealth response models |
| `src/FuseCP.Database/Migrations/2026-03-01-HyperVCluster.sql` | Additive DB migration |

### Files to Modify (9)

| File | Change |
|------|--------|
| `src/FuseCP.EnterpriseServer/Services/HyperVProviderFactory.cs` | Add cluster provider resolution methods |
| `src/FuseCP.EnterpriseServer/Endpoints/HyperVEndpoints.cs` | Register `HyperVClusterEndpoints` route group |
| `src/FuseCP.Providers.HyperV/Models/VirtualMachine.cs` | Add `OwnerNode`, `ClusterName`, `IsHighlyAvailable` |
| `src/FuseCP.EnterpriseServer/Program.cs` | Register `IHyperVClusterProvider` DI bindings |
| `src/FuseCP.EnterpriseServer/appsettings.json` | Add cluster configuration section |
| `src/FuseCP.Portal/Pages/HyperV/Clusters/Index.cshtml` | New — cluster list page |
| `src/FuseCP.Portal/Pages/HyperV/Clusters/Detail.cshtml` | New — cluster detail page |
| `src/FuseCP.Portal/Pages/Shared/_HyperVNav.cshtml` | Add Clusters nav subsection |
| `scripts/api-tests/Run-ClusterIntegrationTests.ps1` | New — cluster integration test script |

### Constraints

- **No breaking changes.** All existing standalone host routes (`/api/hyperv/{host}/*`) and behavior are preserved exactly.
- **Database additive only.** No existing columns, tables, or indexes are altered or dropped.
- **Tenant isolation.** All cluster endpoints are restricted to `PlatformAdmin`. Tenant-scoped API keys receive `403`.

---

## Agent Allocation

| Phase | Agent | Responsibility |
|-------|-------|---------------|
| Codebase Research | `agentic-search` | Deep-dive existing HyperV provider files before any changes; produce findings report |
| Infrastructure Scripts | `modular-builder` | `scripts/cluster-setup/Setup-HyperVCluster.ps1` |
| Architecture Review | `zen-architect` | Validate cluster provider design against simplicity and correctness criteria |
| Database Migration | `modular-builder` | `src/FuseCP.Database/Migrations/2026-03-01-HyperVCluster.sql` |
| Provider Interface | `modular-builder` | `IHyperVClusterProvider.cs` and `HyperVCluster.cs` models |
| Provider Implementation | `modular-builder` | `HyperVClusterProvider.cs` with owner-node resolution pattern |
| PowerShell Scripts | `modular-builder` | `HyperVClusterScripts.cs` |
| Factory Update | `modular-builder` | Update `HyperVProviderFactory.cs` |
| API Endpoints | `modular-builder` | `HyperVClusterEndpoints.cs` + register in `HyperVEndpoints.cs` and `Program.cs` |
| Portal UI | `modular-builder` | Cluster pages, migration dialog, maintenance flow, nav update |
| Integration Tests | `test-coverage` | `scripts/api-tests/Run-ClusterIntegrationTests.ps1` covering all 15 test cases |
| Security Review | `security-guardian` | Verify `PlatformAdmin`-only enforcement on all cluster endpoints; verify no cross-tenant data exposure |
| Cleanup | `post-task-cleanup` | Final hygiene pass — remove debug code, verify no unused imports, confirm formatting |

---

## Test Plan (Acceptance Criteria)

All criteria must pass before this feature is considered complete.

### Infrastructure

- [ ] `Get-ClusterNode -Cluster LabCluster` returns both FUSECP and HYPERVLAB with state `Up`
- [ ] `Get-ClusterQuorum -Cluster LabCluster` returns `NodeAndFileShareMajority`
- [ ] `Test-Path C:\ClusterStorage\Volume1\` returns `True` from both FUSECP and HYPERVLAB
- [ ] Manual `Move-VM` (live migration) completes successfully via PowerShell

### API

- [ ] `GET /api/hyperv/clusters` returns `LabCluster` in the list
- [ ] `GET /api/hyperv/clusters/LabCluster` returns `quorumState: Healthy` and both nodes
- [ ] `POST /api/hyperv/clusters/LabCluster/vms` creates VM with path under `C:\ClusterStorage\Volume1\` and `isHighlyAvailable: true`
- [ ] `GET /api/hyperv/clusters/LabCluster/vms` returns all VMs with a non-null `ownerNode` on each
- [ ] `GET /api/hyperv/clusters/LabCluster/vms/{id}` returns correct `ownerNode` after a live migration has occurred
- [ ] `POST /api/hyperv/clusters/LabCluster/vms/{id}/start` succeeds regardless of which node currently owns the VM
- [ ] `POST /api/hyperv/clusters/LabCluster/vms/{id}/migrate` changes `ownerNode` to the requested destination
- [ ] `POST /api/hyperv/clusters/LabCluster/nodes/HYPERVLAB/maintenance` returns `200`, node state becomes `Paused`, all VMs relocated to FUSECP
- [ ] `POST /api/hyperv/clusters/LabCluster/nodes/HYPERVLAB/resume` returns `200`, node state returns to `Up`
- [ ] `GET /api/hyperv/HYPERVLAB/vms` (standalone route) continues to return `200` with existing behavior
- [ ] Tenant-scoped API key receives `403` on any `/api/hyperv/clusters/*` endpoint

### Portal

- [ ] Cluster list page loads without errors and displays LabCluster
- [ ] Cluster detail page displays node table and VM table with correct states
- [ ] Migration dialog populates destination dropdown with only `Up` nodes excluding the source
- [ ] Maintenance flow drains VMs and updates node state to `Paused` in the UI
- [ ] Resume updates node state to `Up` in the UI
