# Hyper-V Cluster Awareness Implementation Plan

> **For Claude:** REQUIRED: Use /subagent-dev to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Configure a Windows Failover Cluster between FUSECP and HYPERVLAB, then make FuseCP's Hyper-V provider fully cluster-aware with live migration, maintenance mode, and cluster health monitoring.

**Architecture:** New `IHyperVClusterProvider` interface extends `IHyperVProvider` with cluster operations. A `HyperVClusterProvider` wraps per-node providers and resolves the VM owner node before every operation. New API route group `/api/hyperv/clusters/` sits alongside existing standalone routes. Additive-only DB schema changes.

**Tech Stack:** C# (.NET 8), PowerShell (FailoverClusters module), SQL Server, Blazor (InteractiveServer), WinRM

**Spec:** `docs/specs/2026-03-01-hyperv-cluster-awareness-design.md`

---

## Task 0: Research existing HyperV provider architecture

**Agent:** `agentic-search`
**Model:** haiku
**Purpose:** Produce a findings report mapping every method that needs cluster-aware overriding, the full `ExecutePowerShellAsync` flow, WinRM session management, and DI registration patterns.

**Files to Read:**
- `src/FuseCP.Providers.HyperV/IHyperVProvider.cs`
- `src/FuseCP.Providers.HyperV/HyperVProvider.cs`
- `src/FuseCP.Providers.HyperV/Scripts/HyperVScripts.cs`
- `src/FuseCP.Providers.HyperV/Models/VirtualMachine.cs`
- `src/FuseCP.Providers.HyperV/Models/VmCreateRequest.cs`
- `src/FuseCP.Providers.HyperV/Models/VmUpdateRequest.cs`
- `src/FuseCP.Providers.HyperV/Models/VirtualMachineEx.cs`
- `src/FuseCP.Providers.HyperV/Models/VirtualSwitch.cs`
- `src/FuseCP.Providers.HyperV/Models/VmSnapshot.cs`
- `src/FuseCP.Providers.HyperV/RemotePowerShellExecutor.cs`
- `src/FuseCP.Providers.HyperV/IPowerShellExecutor.cs`
- `src/FuseCP.Providers.HyperV/PowerShellExecutorFactory.cs`
- `src/FuseCP.EnterpriseServer/Services/HyperVProviderFactory.cs`
- `src/FuseCP.EnterpriseServer/Endpoints/HyperVEndpoints.cs`
- `src/FuseCP.EnterpriseServer/Program.cs`
- `src/FuseCP.Database/Models/Service.cs`

**Steps:**
- [ ] READ `IHyperVProvider.cs` — list all 77 methods with signatures; mark each that operates on a single VM by ID (these must be overridden in HyperVClusterProvider to first call `ResolveOwnerNodeAsync`)
- [ ] READ `HyperVProvider.cs` — trace `ExecutePowerShellAsync` call chain; document how the WinRM host is injected; identify constructor signature
- [ ] READ `RemotePowerShellExecutor.cs` — understand how WinRM sessions are established and how the target hostname is passed
- [ ] READ `PowerShellExecutorFactory.cs` — understand how executors are created per-host
- [ ] READ `HyperVProviderFactory.cs` — document the existing `Dictionary<string, IHyperVProvider>` cache, initialization sequence, and DI registration
- [ ] READ `HyperVEndpoints.cs` — note the `MapGroup("/api/hyperv/{host}")` pattern and auth requirements
- [ ] READ `Program.cs` — document exact DI registration lines for HyperV providers and factory
- [ ] READ `Scripts/HyperVScripts.cs` — inventory every static method; note the string interpolation pattern used for parameters
- [ ] READ all Models files — document existing properties on `VirtualMachine.cs`, `VmCreateRequest.cs`
- [ ] Produce a written findings report with file:line references for every method that must be overridden; confirm the exact parameter type passed to constructor for standalone provider (hostname string vs. options object)

---

## Task 1: Infrastructure — iSCSI Connection and Failover Cluster Setup

**Agent:** `modular-builder`
**Model:** sonnet
**Purpose:** Create an idempotent PowerShell setup script that connects iSCSI storage, installs Failover Clustering, validates, creates the cluster, configures quorum, adds CSV, enables live migration, and registers DNS.

**Files to Create:**
- `scripts/cluster-setup/Setup-HyperVCluster.ps1`

**Steps:**
- [ ] Create directory `scripts/cluster-setup/` if it does not exist
- [ ] Create `scripts/cluster-setup/Setup-HyperVCluster.ps1` with the full idempotent script below

```powershell
<#
.SYNOPSIS
    Sets up a Windows Failover Cluster between FUSECP and HYPERVLAB with iSCSI
    shared storage and file share witness quorum.

.PARAMETER ClusterName
    Name of the cluster to create. Default: LabCluster

.PARAMETER ClusterIP
    Static IP address for the cluster. Default: 172.31.251.105

.PARAMETER WitnessShare
    UNC path for file share witness. Default: \\FINALTEST\ClusterWitness

.PARAMETER CsvDiskName
    Name of the cluster disk to add as CSV. Default: "Cluster Disk 1"

.PARAMETER DnsZone
    DNS zone for cluster A record. Default: lab.ergonet.pl

.PARAMETER iSCSIDiscoveryIPs
    Array of iSCSI target discovery IP addresses.
    Default: 172.16.11.111, 172.16.12.111

.EXAMPLE
    .\Setup-HyperVCluster.ps1
    .\Setup-HyperVCluster.ps1 -ClusterName MyCluster -ClusterIP 172.31.251.106
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$ClusterName     = "LabCluster",
    [string]$ClusterIP       = "172.31.251.105",
    [string]$WitnessShare    = "\\FINALTEST\ClusterWitness",
    [string]$CsvDiskName     = "Cluster Disk 1",
    [string]$DnsZone         = "lab.ergonet.pl",
    [string[]]$iSCSIDiscoveryIPs = @("172.16.11.111", "172.16.12.111")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Nodes = @("FUSECP", "HYPERVLAB")

function Write-Step {
    param([string]$Message)
    Write-Host "`n[STEP] $Message" -ForegroundColor Cyan
}

function Write-Skip {
    param([string]$Message)
    Write-Host "  [SKIP] $Message (already done)" -ForegroundColor Yellow
}

function Write-Done {
    param([string]$Message)
    Write-Host "  [OK]   $Message" -ForegroundColor Green
}

# ---------------------------------------------------------------------------
# Step 1: iSCSI — Connect targets on both nodes
# ---------------------------------------------------------------------------
Write-Step "Connecting iSCSI targets on both nodes"
foreach ($Node in $Nodes) {
    Invoke-Command -ComputerName $Node -ScriptBlock {
        param($DiscoveryIPs)
        $service = Get-Service -Name MSiSCSI -ErrorAction SilentlyContinue
        if ($service.Status -ne 'Running') {
            Start-Service MSiSCSI
            Set-Service MSiSCSI -StartupType Automatic
        }
        foreach ($ip in $DiscoveryIPs) {
            $existing = Get-IscsiTargetPortal -TargetPortalAddress $ip -ErrorAction SilentlyContinue
            if (-not $existing) {
                New-IscsiTargetPortal -TargetPortalAddress $ip | Out-Null
            }
            Update-IscsiTarget -ErrorAction SilentlyContinue | Out-Null
        }
        $targets = Get-IscsiTarget | Where-Object { -not $_.IsConnected }
        foreach ($target in $targets) {
            Connect-IscsiTarget -NodeAddress $target.NodeAddress -IsPersistent $true | Out-Null
        }
    } -ArgumentList (,$iSCSIDiscoveryIPs)
    Write-Done "iSCSI connected on $Node"
}

# ---------------------------------------------------------------------------
# Step 2: Install Failover-Clustering feature on both nodes
# ---------------------------------------------------------------------------
Write-Step "Installing Failover-Clustering feature on both nodes"
foreach ($Node in $Nodes) {
    $feature = Invoke-Command -ComputerName $Node -ScriptBlock {
        Get-WindowsFeature -Name Failover-Clustering
    }
    if ($feature.Installed) {
        Write-Skip "Failover-Clustering already installed on $Node"
    } else {
        Invoke-Command -ComputerName $Node -ScriptBlock {
            Install-WindowsFeature -Name Failover-Clustering -IncludeManagementTools -Restart:$false
        }
        Write-Done "Failover-Clustering installed on $Node"
    }
}

# ---------------------------------------------------------------------------
# Step 3: Validate cluster prerequisites
# ---------------------------------------------------------------------------
Write-Step "Running Test-Cluster validation"
$testResult = Test-Cluster -Node $Nodes -Include "Storage", "Network", "Hyper-V Configuration" -ErrorAction SilentlyContinue
if ($testResult) {
    Write-Done "Test-Cluster completed (review report at $($testResult.PSPath))"
} else {
    Write-Warning "Test-Cluster returned no result — check logs manually before proceeding"
}

# ---------------------------------------------------------------------------
# Step 4: Create cluster (idempotent)
# ---------------------------------------------------------------------------
Write-Step "Creating cluster '$ClusterName' with IP $ClusterIP"
$existingCluster = Get-Cluster -Name $ClusterName -ErrorAction SilentlyContinue
if ($existingCluster) {
    Write-Skip "Cluster '$ClusterName' already exists"
} else {
    New-Cluster -Name $ClusterName -Node $Nodes -StaticAddress $ClusterIP -NoStorage | Out-Null
    Write-Done "Cluster '$ClusterName' created"
}

# ---------------------------------------------------------------------------
# Step 5: Create witness share directory on FINALTEST and configure quorum
# ---------------------------------------------------------------------------
Write-Step "Configuring File Share Witness at $WitnessShare"
$shareName = Split-Path $WitnessShare -Leaf
$shareExists = Invoke-Command -ComputerName FINALTEST -ScriptBlock {
    param($ShareName)
    Get-SmbShare -Name $ShareName -ErrorAction SilentlyContinue
} -ArgumentList $shareName

if (-not $shareExists) {
    Invoke-Command -ComputerName FINALTEST -ScriptBlock {
        param($SharePath, $ShareName, $ClusterName)
        $dir = "C:\ClusterWitness\$ShareName"
        if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
        New-SmbShare -Name $ShareName -Path $dir -FullAccess "$ClusterName$" | Out-Null
    } -ArgumentList $WitnessShare, $shareName, $ClusterName
    Write-Done "Witness share created on FINALTEST"
} else {
    Write-Skip "Witness share '$shareName' already exists on FINALTEST"
}

$quorum = Get-ClusterQuorum -Cluster $ClusterName
if ($quorum.QuorumType -ne 'NodeAndFileShareMajority') {
    Set-ClusterQuorum -Cluster $ClusterName -FileShareWitness $WitnessShare | Out-Null
    Write-Done "Quorum set to FileShareWitness ($WitnessShare)"
} else {
    Write-Skip "Quorum already set to NodeAndFileShareMajority"
}

# ---------------------------------------------------------------------------
# Step 6: Add shared disk as Cluster Shared Volume
# ---------------------------------------------------------------------------
Write-Step "Adding '$CsvDiskName' as Cluster Shared Volume"
$existingCsv = Get-ClusterSharedVolume -Cluster $ClusterName -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -eq $CsvDiskName }
if ($existingCsv) {
    Write-Skip "CSV '$CsvDiskName' already added"
} else {
    # First make sure the disk is available to the cluster
    $availDisk = Get-ClusterAvailableDisk -Cluster $ClusterName |
        Where-Object { $_.Name -eq $CsvDiskName } |
        Select-Object -First 1
    if ($availDisk) {
        $availDisk | Add-ClusterDisk | Out-Null
    }
    Add-ClusterSharedVolume -Cluster $ClusterName -Name $CsvDiskName | Out-Null
    Write-Done "CSV '$CsvDiskName' added — accessible at C:\ClusterStorage\Volume1\ on both nodes"
}

# ---------------------------------------------------------------------------
# Step 7: Enable Live Migration with Kerberos auth on both nodes
# ---------------------------------------------------------------------------
Write-Step "Enabling Live Migration on both nodes"
foreach ($Node in $Nodes) {
    Invoke-Command -ComputerName $Node -ScriptBlock {
        Enable-VMMigration
        Set-VMMigrationNetwork "172.31.251.0/24"
        Set-VMHost -VirtualMachineMigrationAuthenticationType Kerberos
    }
    Write-Done "Live Migration enabled on $Node"
}

# ---------------------------------------------------------------------------
# Step 8: Add DNS A record for cluster
# ---------------------------------------------------------------------------
Write-Step "Adding DNS A record: $ClusterName.$DnsZone -> $ClusterIP"
$existingDns = Get-DnsServerResourceRecord -ZoneName $DnsZone -Name $ClusterName `
    -RRType A -ErrorAction SilentlyContinue
if ($existingDns) {
    Write-Skip "DNS record '$ClusterName.$DnsZone' already exists"
} else {
    Add-DnsServerResourceRecordA -ZoneName $DnsZone -Name $ClusterName -IPv4Address $ClusterIP
    Write-Done "DNS A record added: $ClusterName.$DnsZone -> $ClusterIP"
}

Write-Host "`n[DONE] Cluster setup complete." -ForegroundColor Green
Write-Host "Validate with:" -ForegroundColor White
Write-Host "  Get-ClusterNode -Cluster $ClusterName" -ForegroundColor Gray
Write-Host "  Get-ClusterQuorum -Cluster $ClusterName" -ForegroundColor Gray
Write-Host "  Test-Path C:\ClusterStorage\Volume1\ (run on both nodes)" -ForegroundColor Gray
```

---

## Task 2: Run cluster setup and validate infrastructure

**Agent:** `modular-builder`
**Model:** sonnet
**Purpose:** Execute the setup script from Task 1 and validate the cluster is healthy before any code changes are made.

**Prerequisites:** Task 1 complete, iSCSI target LUN accessible from both nodes.

**Steps:**
- [ ] Confirm iSCSI LUN is visible on both nodes: run `Get-Disk | Where-Object { $_.BusType -eq 'iSCSI' }` via WinRM on FUSECP and HYPERVLAB; verify the same disk serial number appears on both
- [ ] Run `scripts/cluster-setup/Setup-HyperVCluster.ps1` from FUSECP (requires FailoverClusters module on the local machine or run via WinRM session to FUSECP)
- [ ] Validate cluster nodes: `Get-ClusterNode -Cluster LabCluster` — both FUSECP and HYPERVLAB must show State `Up`
- [ ] Validate quorum: `Get-ClusterQuorum -Cluster LabCluster` — QuorumType must be `NodeAndFileShareMajority`
- [ ] Validate CSV on FUSECP: `Test-Path C:\ClusterStorage\Volume1\` must return `True`
- [ ] Validate CSV on HYPERVLAB: `Invoke-Command -ComputerName HYPERVLAB -ScriptBlock { Test-Path C:\ClusterStorage\Volume1\ }` must return `True`
- [ ] Validate live migration: create a test VM on FUSECP (`New-VM -Name TestMigrate -MemoryStartupBytes 256MB -Path C:\ClusterStorage\Volume1\`), register it as HA (`Add-ClusterVirtualMachineRole -VirtualMachine TestMigrate`), then migrate it (`Move-ClusterVirtualMachineRole -Name TestMigrate -Node HYPERVLAB`) and confirm success
- [ ] Remove test VM after validation
- [ ] Document any deviations from expected behavior in `ai_working/decisions/`

---

## Task 3: Database migration

**Agent:** `modular-builder`
**Model:** sonnet
**Purpose:** Create the additive SQL migration for cluster support. No existing columns or tables are altered or dropped. Next migration number is 114.

**Files to Create:**
- `src/FuseCP.Database/Migrations/114_AddHyperVClusterTables.sql`

**Steps:**
- [ ] Create `src/FuseCP.Database/Migrations/114_AddHyperVClusterTables.sql` with the following SQL:

```sql
-- Migration 114: Add Hyper-V Cluster Support Tables and Columns
-- ADDITIVE ONLY — no existing columns, tables, or indexes are altered or dropped.
-- Backward compatible: NULL values on new columns mean "legacy row = Standalone behavior".

-- -----------------------------------------------------------------------
-- 1. Add cluster columns to Servers table
-- -----------------------------------------------------------------------
ALTER TABLE Servers ADD HyperVClusterName NVARCHAR(255) NULL;
ALTER TABLE Servers ADD HyperVClusterRole NVARCHAR(50) NULL;
-- HyperVClusterRole allowed values:
--   'Node'       — this server is a member of a Failover Cluster
--   'Standalone' — this server is explicitly standalone (not in a cluster)
--   NULL         — legacy row; treated as Standalone

-- -----------------------------------------------------------------------
-- 2. New HyperVClusters table
-- -----------------------------------------------------------------------
CREATE TABLE HyperVClusters (
    ClusterID    INT           IDENTITY(1,1) PRIMARY KEY,
    ClusterName  NVARCHAR(255) NOT NULL,
    ClusterFqdn  NVARCHAR(255) NOT NULL,
    ClusterIP    NVARCHAR(50)  NOT NULL,
    CsvPath      NVARCHAR(500) NOT NULL,
    QuorumType   NVARCHAR(50)  NULL,
    CreatedAt    DATETIME      DEFAULT GETDATE(),
    IsActive     BIT           DEFAULT 1
);

-- -----------------------------------------------------------------------
-- 3. Seed LabCluster
-- -----------------------------------------------------------------------
INSERT INTO HyperVClusters (ClusterName, ClusterFqdn, ClusterIP, CsvPath, QuorumType, IsActive)
VALUES (
    'LabCluster',
    'LabCluster.lab.ergonet.pl',
    '172.31.251.105',
    'C:\ClusterStorage\Volume1\',
    'NodeAndFileShareMajority',
    1
);

-- -----------------------------------------------------------------------
-- 4. Tag both Hyper-V servers as cluster nodes
-- -----------------------------------------------------------------------
UPDATE Servers
SET    HyperVClusterName = 'LabCluster',
       HyperVClusterRole = 'Node'
WHERE  HyperVHost IN ('172.31.251.100', '172.31.251.102')
  AND  HyperVHost IS NOT NULL;
```

- [ ] Run the migration against the FuseCPLab database:
  ```powershell
  Invoke-Sqlcmd -ServerInstance "(local)\SQLEXPRESS" -Database "FuseCPLab" `
    -InputFile "src/FuseCP.Database/Migrations/114_AddHyperVClusterTables.sql"
  ```
- [ ] Verify: `SELECT * FROM HyperVClusters` returns 1 row for LabCluster
- [ ] Verify: `SELECT HyperVHost, HyperVClusterName, HyperVClusterRole FROM Servers WHERE HyperVClusterName IS NOT NULL` returns both node rows

---

## Task 4: Cluster models and interface

**Agent:** `modular-builder`
**Model:** sonnet
**Purpose:** Create the `HyperVCluster.cs` models, the `IHyperVClusterProvider` interface, and add the three new nullable properties to `VirtualMachine.cs`.

**Files to Create:**
- `src/FuseCP.Providers.HyperV/Models/HyperVCluster.cs`
- `src/FuseCP.Providers.HyperV/IHyperVClusterProvider.cs`

**Files to Modify:**
- `src/FuseCP.Providers.HyperV/Models/VirtualMachine.cs` — add `OwnerNode`, `ClusterName`, `IsHighlyAvailable`

**Steps:**
- [ ] Read `src/FuseCP.Providers.HyperV/Models/VirtualMachine.cs` to understand existing property naming conventions and namespace
- [ ] Read `src/FuseCP.Providers.HyperV/IHyperVProvider.cs` to confirm namespace and method return types
- [ ] Create `src/FuseCP.Providers.HyperV/Models/HyperVCluster.cs`:

```csharp
namespace FuseCP.Providers.HyperV.Models;

/// <summary>
/// Represents a single node in a Windows Failover Cluster.
/// </summary>
public class ClusterNode
{
    public string Name { get; set; } = string.Empty;

    /// <summary>Up, Down, or Paused</summary>
    public string State { get; set; } = string.Empty;

    public double CpuUsagePercent { get; set; }
    public long MemoryUsedMb { get; set; }
    public int VmCount { get; set; }
}

/// <summary>
/// Cluster-level health summary.
/// </summary>
public class ClusterHealth
{
    public string ClusterName { get; set; } = string.Empty;

    /// <summary>Healthy, DegradedQuorum, or NoQuorum</summary>
    public string QuorumState { get; set; } = string.Empty;

    public IEnumerable<ClusterNode> Nodes { get; set; } = [];
    public int TotalVms { get; set; }
    public DateTime LastUpdated { get; set; } = DateTime.UtcNow;
}

/// <summary>
/// Request model for live migrating a VM to a destination node.
/// </summary>
public class MigrateVmRequest
{
    public string DestinationNode { get; set; } = string.Empty;
}
```

- [ ] Create `src/FuseCP.Providers.HyperV/IHyperVClusterProvider.cs`:

```csharp
using FuseCP.Providers.HyperV.Models;

namespace FuseCP.Providers.HyperV;

/// <summary>
/// Extends IHyperVProvider with cluster-aware operations for Windows Failover Clusters.
/// All VM operations in the implementation resolve the current owner node before
/// executing commands against that node via WinRM.
/// </summary>
public interface IHyperVClusterProvider : IHyperVProvider
{
    // ------------------------------------------------------------------
    // Cluster topology
    // ------------------------------------------------------------------

    /// <summary>Returns all nodes in the cluster with state and resource metrics.</summary>
    Task<IEnumerable<ClusterNode>> GetClusterNodesAsync();

    /// <summary>Returns all VMs registered in the cluster, each with ownerNode set.</summary>
    Task<IEnumerable<VirtualMachine>> GetClusterVmsAsync();

    /// <summary>Returns overall cluster health: quorum state and per-node status.</summary>
    Task<ClusterHealth> GetClusterHealthAsync();

    // ------------------------------------------------------------------
    // Owner resolution
    // ------------------------------------------------------------------

    /// <summary>
    /// Resolves which cluster node currently owns the specified VM.
    /// Throws InvalidOperationException if the VM is not found in the cluster.
    /// </summary>
    Task<string> GetVmOwnerNodeAsync(Guid vmId);

    // ------------------------------------------------------------------
    // VM cluster operations
    // ------------------------------------------------------------------

    /// <summary>Live migrates the VM to the specified destination node.</summary>
    Task MigrateVmAsync(Guid vmId, string destinationNode);

    // ------------------------------------------------------------------
    // Node maintenance
    // ------------------------------------------------------------------

    /// <summary>
    /// Drains all VMs off the specified source node using live migration,
    /// then pauses the node (Suspend-ClusterNode -Drain).
    /// </summary>
    Task MigrateAllVmsFromNodeAsync(string sourceNode);

    /// <summary>
    /// Enters or exits maintenance mode on the specified node.
    /// enterMaintenance=true: Suspend-ClusterNode -Drain
    /// enterMaintenance=false: Resume-ClusterNode
    /// </summary>
    Task SetNodeMaintenanceAsync(string node, bool enterMaintenance);
}
```

- [ ] Modify `src/FuseCP.Providers.HyperV/Models/VirtualMachine.cs` — append three nullable properties at the end of the class body:

```csharp
    // Cluster fields — null for VMs on standalone hosts
    public string? OwnerNode { get; set; }
    public string? ClusterName { get; set; }
    public bool IsHighlyAvailable { get; set; }
```

- [ ] Verify the project builds: `dotnet build src/FuseCP.Providers.HyperV/FuseCP.Providers.HyperV.csproj`

---

## Task 5: Cluster PowerShell scripts

**Agent:** `modular-builder`
**Model:** sonnet
**Purpose:** Create `HyperVClusterScripts.cs` as a static class in the `Scripts/` folder, following the exact same pattern as the existing `HyperVScripts.cs`.

**Files to Create:**
- `src/FuseCP.Providers.HyperV/Scripts/HyperVClusterScripts.cs`

**Steps:**
- [ ] Read `src/FuseCP.Providers.HyperV/Scripts/HyperVScripts.cs` in full to understand the class pattern, namespace, and string interpolation conventions
- [ ] Create `src/FuseCP.Providers.HyperV/Scripts/HyperVClusterScripts.cs`:

```csharp
namespace FuseCP.Providers.HyperV.Scripts;

/// <summary>
/// All PowerShell command strings for cluster-aware Hyper-V operations.
/// Every method returns a complete PS script string ready for ExecutePowerShellAsync.
/// No PowerShell is inlined in provider or endpoint code.
/// </summary>
public static class HyperVClusterScripts
{
    // ------------------------------------------------------------------
    // Cluster topology
    // ------------------------------------------------------------------

    /// <summary>Get all cluster nodes with state.</summary>
    public static string GetClusterNodes(string clusterFqdn) => $"""
        Get-ClusterNode -Cluster '{clusterFqdn}' |
        Select-Object Name,
            @{{Name='State';Expression={{$_.State.ToString()}}}},
            @{{Name='CpuUsagePercent';Expression={{$_.CPULoad}}}},
            @{{Name='MemoryUsedMb';Expression={{[math]::Round($_.MemoryAvailable / 1MB, 0)}}}} |
        ConvertTo-Json -Depth 2
        """;

    /// <summary>Get all VMs registered as cluster resources with their current owner node.</summary>
    public static string GetClusterVms(string clusterFqdn) => $"""
        Get-ClusterGroup -Cluster '{clusterFqdn}' |
        Where-Object {{ $_.GroupType -eq 'VirtualMachine' }} |
        Select-Object Name,
            @{{Name='OwnerNode';Expression={{$_.OwnerNode.Name}}}},
            @{{Name='State';Expression={{$_.State.ToString()}}}} |
        ConvertTo-Json -Depth 2
        """;

    /// <summary>Resolve the current owner node name for a specific VM by its ID.</summary>
    public static string GetVmOwnerNode(Guid vmId, string clusterFqdn) => $"""
        $group = Get-ClusterGroup -Cluster '{clusterFqdn}' |
            Where-Object {{ $_.GroupType -eq 'VirtualMachine' -and $_.Name -like '*{vmId}*' }}
        if ($null -eq $group) {{ throw "VM {vmId} not found in cluster {clusterFqdn}" }}
        $group.OwnerNode.Name
        """;

    // ------------------------------------------------------------------
    // Live migration
    // ------------------------------------------------------------------

    /// <summary>Live migrate a specific VM to a destination node.</summary>
    public static string MigrateVm(Guid vmId, string sourceNode, string destinationNode, string csvPath) => $"""
        Move-VM -Name (Get-VM -Id '{vmId}' -ComputerName '{sourceNode}').Name `
                -ComputerName '{sourceNode}' `
                -DestinationHost '{destinationNode}' `
                -DestinationStoragePath '{csvPath}'
        """;

    /// <summary>
    /// Drain all VMs from a node using live migration (Move-ClusterVirtualMachineRole).
    /// Used as the first step of entering maintenance mode.
    /// </summary>
    public static string MigrateAllVmsFromNode(string sourceNode, string clusterFqdn) => $"""
        Get-ClusterGroup -Cluster '{clusterFqdn}' |
        Where-Object {{ $_.GroupType -eq 'VirtualMachine' -and $_.OwnerNode.Name -eq '{sourceNode}' }} |
        ForEach-Object {{
            $_ | Move-ClusterVirtualMachineRole -MigrationType Live
        }}
        """;

    // ------------------------------------------------------------------
    // Node maintenance
    // ------------------------------------------------------------------

    /// <summary>Pause a cluster node and drain its workloads (enter maintenance).</summary>
    public static string SuspendClusterNode(string nodeName, string clusterFqdn) => $"""
        Suspend-ClusterNode -Name '{nodeName}' -Cluster '{clusterFqdn}' -Drain
        """;

    /// <summary>Resume a cluster node from maintenance (paused) state.</summary>
    public static string ResumeClusterNode(string nodeName, string clusterFqdn) => $"""
        Resume-ClusterNode -Name '{nodeName}' -Cluster '{clusterFqdn}'
        """;

    // ------------------------------------------------------------------
    // Cluster health
    // ------------------------------------------------------------------

    /// <summary>Get cluster quorum state combined with per-node status for a health summary.</summary>
    public static string GetClusterHealth(string clusterFqdn) => $"""
        $cluster = Get-Cluster -Name '{clusterFqdn}'
        $nodes   = Get-ClusterNode -Cluster '{clusterFqdn}'
        $quorum  = Get-ClusterQuorum -Cluster '{clusterFqdn}'
        $vmCount = (Get-ClusterGroup -Cluster '{clusterFqdn}' |
                    Where-Object {{ $_.GroupType -eq 'VirtualMachine' }}).Count

        [PSCustomObject]@{{
            ClusterName  = $cluster.Name
            QuorumState  = $quorum.QuorumType.ToString()
            TotalVms     = $vmCount
            Nodes        = $nodes | Select-Object `
                Name,
                @{{Name='State';Expression={{$_.State.ToString()}}}},
                @{{Name='CpuUsagePercent';Expression={{$_.CPULoad}}}},
                @{{Name='MemoryUsedMb';Expression={{[math]::Round($_.MemoryAvailable / 1MB, 0)}}}},
                @{{Name='VmCount';Expression={{
                    (Get-ClusterGroup -Cluster '{clusterFqdn}' |
                     Where-Object {{ $_.GroupType -eq 'VirtualMachine' -and $_.OwnerNode.Name -eq $_.Name }}).Count
                }}}}
        }} | ConvertTo-Json -Depth 3
        """;

    // ------------------------------------------------------------------
    // VM cluster registration and creation
    // ------------------------------------------------------------------

    /// <summary>Register an existing VM as a highly-available cluster resource.</summary>
    public static string RegisterClusterVm(string vmName, string clusterFqdn) => $"""
        Add-ClusterVirtualMachineRole -VirtualMachine '{vmName}' -Cluster '{clusterFqdn}'
        """;

    /// <summary>
    /// Create a new VM on the CSV path and immediately register it as a cluster resource.
    /// Uses the same parameter set as the standalone New-VM but forces the path to CSV.
    /// </summary>
    public static string CreateVmOnCsv(string vmName, long memoryMb, int cpuCount, string csvPath, string clusterFqdn) => $"""
        $vm = New-VM -Name '{vmName}' `
                     -MemoryStartupBytes {memoryMb}MB `
                     -Path '{csvPath}' `
                     -Generation 2
        Set-VMProcessor $vm -Count {cpuCount}
        Add-ClusterVirtualMachineRole -VirtualMachine '{vmName}' -Cluster '{clusterFqdn}'
        Get-VM -Id $vm.Id | Select-Object * | ConvertTo-Json -Depth 2
        """;
}
```

- [ ] Verify the project builds: `dotnet build src/FuseCP.Providers.HyperV/FuseCP.Providers.HyperV.csproj`

---

## Task 6: Cluster provider implementation

**Agent:** `modular-builder`
**Model:** sonnet
**Purpose:** Implement `HyperVClusterProvider` which wraps per-node `IHyperVProvider` instances, resolves owner node before every VM operation, and implements all cluster-specific methods.

**Files to Create:**
- `src/FuseCP.Providers.HyperV/HyperVClusterProvider.cs`

**Steps:**
- [ ] Read `src/FuseCP.Providers.HyperV/HyperVProvider.cs` in full to understand the constructor signature, how `ExecutePowerShellAsync` is called, and which methods operate on a single VM by ID
- [ ] Read `src/FuseCP.Providers.HyperV/IHyperVProvider.cs` in full to get all method signatures
- [ ] Read the Task 0 findings report (in `ai_working/`) for the complete list of methods that require owner-node override
- [ ] Create `src/FuseCP.Providers.HyperV/HyperVClusterProvider.cs` implementing `IHyperVClusterProvider`:
  - Constructor accepts: `string clusterName`, `string clusterFqdn`, `string csvPath`, `Dictionary<string, IHyperVProvider> nodeProviders`
    - `clusterName` — the cluster's short name (e.g., "LabCluster")
    - `clusterFqdn` — the fully-qualified cluster DNS name (e.g., "LabCluster.lab.ergonet.pl")
    - `csvPath` — the CSV storage path (e.g., `C:\ClusterStorage\Volume1\`)
    - `nodeProviders` — dictionary keyed by node short name (FUSECP, HYPERVLAB) → per-node provider
  - Store `_clusterEntryProvider` = the first available node provider (used for cluster-wide PS commands)
  - Implement `private async Task<string> ResolveOwnerNodeAsync(Guid vmId)`:
    ```csharp
    private async Task<string> ResolveOwnerNodeAsync(Guid vmId)
    {
        var script = HyperVClusterScripts.GetVmOwnerNode(vmId, _clusterFqdn);
        var result = await _clusterEntryProvider.ExecutePowerShellAsync(script);
        return result.FirstOrDefault()?.ToString()
            ?? throw new InvalidOperationException($"VM {vmId} not found in cluster {_clusterFqdn}");
    }
    ```
  - Override all VM operations that take a `Guid vmId` parameter (from `IHyperVProvider`) to call `ResolveOwnerNodeAsync(vmId)` first, then delegate to `_nodeProviders[ownerNode]`
  - Implement `GetClusterNodesAsync` using `HyperVClusterScripts.GetClusterNodes`
  - Implement `GetClusterVmsAsync` using `HyperVClusterScripts.GetClusterVms`; set `IsHighlyAvailable = true`, `ClusterName = _clusterName` on each VM result
  - Implement `GetClusterHealthAsync` using `HyperVClusterScripts.GetClusterHealth`
  - Implement `GetVmOwnerNodeAsync(Guid vmId)` — public wrapper calling `ResolveOwnerNodeAsync`
  - Implement `MigrateVmAsync(Guid vmId, string destinationNode)`:
    - Resolve owner node
    - Execute `HyperVClusterScripts.MigrateVm(vmId, ownerNode, destinationNode, _csvPath)` against `_nodeProviders[ownerNode]`
  - Implement `MigrateAllVmsFromNodeAsync(string sourceNode)` using `HyperVClusterScripts.MigrateAllVmsFromNode`
  - Implement `SetNodeMaintenanceAsync(string node, bool enterMaintenance)`:
    - if `enterMaintenance`: first call `MigrateAllVmsFromNodeAsync(node)`, then execute `HyperVClusterScripts.SuspendClusterNode`
    - if `!enterMaintenance`: execute `HyperVClusterScripts.ResumeClusterNode`
  - VM creation override: use `HyperVClusterScripts.CreateVmOnCsv` targeting any `Up` node, set `IsHighlyAvailable = true`, `ClusterName = _clusterName` on the returned VM
- [ ] Verify the project builds: `dotnet build src/FuseCP.Providers.HyperV/FuseCP.Providers.HyperV.csproj`

---

## Task 7: Provider factory update

**Agent:** `modular-builder`
**Model:** sonnet
**Purpose:** Add cluster provider support to `HyperVProviderFactory` while keeping the existing standalone `GetProviderAsync(host)` method completely unchanged.

**Files to Modify:**
- `src/FuseCP.EnterpriseServer/Services/HyperVProviderFactory.cs`

**Steps:**
- [ ] Read `src/FuseCP.EnterpriseServer/Services/HyperVProviderFactory.cs` in full to understand the existing dictionary, initialization, and DI dependencies
- [ ] Read `src/FuseCP.Database/Repositories/SolidCP/IHyperVRepository.cs` to understand available DB query methods
- [ ] Add a private field `_clusterProviders = new Dictionary<string, IHyperVClusterProvider>()` (cluster name → provider)
- [ ] Add `GetClusterProviderAsync(string clusterName)`:
  - Check `_clusterProviders` cache first
  - On cache miss: query `HyperVClusters` table for the cluster record; query `Servers` where `HyperVClusterName = clusterName`; build per-node providers using existing `GetProviderAsync(nodeHostname)` calls; construct `HyperVClusterProvider`; cache and return
  - Throws `KeyNotFoundException` if cluster name not found in DB
- [ ] Add `GetAllClusterNamesAsync()`:
  - Query `HyperVClusters` table where `IsActive = 1`; return list of `ClusterName` strings
- [ ] Add `IsClusterNodeAsync(string host)`:
  - Query `Servers` where `HyperVHost = host` and `HyperVClusterRole = 'Node'`; return bool
- [ ] Verify existing `GetProviderAsync(host)` signature and behavior are unchanged — do not modify it
- [ ] Verify the project builds: `dotnet build src/FuseCP.EnterpriseServer/FuseCP.EnterpriseServer.csproj`

---

## Task 8: API endpoints

**Agent:** `modular-builder`
**Model:** sonnet
**Purpose:** Create the cluster route group and register it alongside existing standalone routes. All cluster endpoints require `PlatformAdmin` authorization.

**Files to Create:**
- `src/FuseCP.EnterpriseServer/Endpoints/HyperVClusterEndpoints.cs`

**Files to Modify:**
- `src/FuseCP.EnterpriseServer/Endpoints/HyperVEndpoints.cs` — register the cluster endpoint group
- `src/FuseCP.EnterpriseServer/Program.cs` — register `IHyperVClusterProvider` resolution via factory in DI

**Steps:**
- [ ] Read `src/FuseCP.EnterpriseServer/Endpoints/HyperVEndpoints.cs` in full to understand the `MapGroup` pattern, auth requirements, and how the factory is resolved
- [ ] Read `src/FuseCP.EnterpriseServer/Program.cs` to understand the DI registration pattern for existing HyperV services
- [ ] Create `src/FuseCP.EnterpriseServer/Endpoints/HyperVClusterEndpoints.cs` with the following routes, all under `MapGroup("/api/hyperv/clusters").RequireAuthorization("PlatformAdmin")`:

  | Method | Route | Handler |
  |--------|-------|---------|
  | GET | `/` | List all clusters (name, IP, node count, health summary) |
  | GET | `/{cluster}` | Cluster health: quorum state, node states, VM count |
  | GET | `/{cluster}/vms` | All VMs across cluster, each with `ownerNode` set |
  | POST | `/{cluster}/vms` | Create VM on cluster (uses CSV path, registers as HA) |
  | GET | `/{cluster}/vms/{vmId}` | VM detail; auto-resolves current owner node |
  | POST | `/{cluster}/vms/{vmId}/migrate` | Live migrate; body: `MigrateVmRequest` |
  | POST | `/{cluster}/vms/{vmId}/{action}` | Start / stop / snapshot; routes to owner node |
  | GET | `/{cluster}/nodes` | Node list with state (Up, Down, Paused) |
  | POST | `/{cluster}/nodes/{node}/maintenance` | Drain VMs then pause node |
  | POST | `/{cluster}/nodes/{node}/resume` | Resume node from maintenance |

- [ ] Each handler resolves `IHyperVProviderFactory` from DI and calls `GetClusterProviderAsync(cluster)`; returns `404` if cluster not found, `500` with error message on provider exception
- [ ] Modify `HyperVEndpoints.cs` to call `HyperVClusterEndpoints.Map(app)` (or equivalent registration pattern matching the existing codebase) so the cluster routes are registered
- [ ] Modify `Program.cs` to register `HyperVProviderFactory` as the implementation for both `IHyperVProviderFactory` and any cluster-related interface — do not duplicate existing registrations; verify the factory is already registered and only add if needed
- [ ] Verify the full solution builds: `dotnet build src/FuseCP.EnterpriseServer/FuseCP.EnterpriseServer.csproj`
- [ ] Start the API with `dotnet run --project src/FuseCP.EnterpriseServer` and verify `GET /api/hyperv/clusters` returns 200 with the LabCluster entry (from migration seed data)
- [ ] Stop the service after verification

---

## Task 9: Portal UI — Cluster pages

**Agent:** `modular-builder`
**Model:** sonnet
**Purpose:** Add two Blazor pages for cluster management and update the navigation sidebar to include a Clusters section under Hyper-V.

**Files to Create:**
- `src/FuseCP.Portal/Components/Pages/HyperV/Clusters/Index.razor` — cluster list page
- `src/FuseCP.Portal/Components/Pages/HyperV/Clusters/Detail.razor` — cluster detail with nodes table, VMs table, migration dialog, maintenance controls

**Files to Modify:**
- `src/FuseCP.Portal/Components/Layout/ContextSidebar.razor` — add Clusters subsection under Hyper-V

**Steps:**
- [ ] Read `src/FuseCP.Portal/Components/Pages/HyperV/Library.razor` in full to understand the Blazor InteractiveServer pattern, API client injection, authorization attribute, and component conventions used in existing HyperV pages
- [ ] Read `src/FuseCP.Portal/Components/Layout/ContextSidebar.razor` — find the Hyper-V nav section to understand where and how to add the Clusters subsection
- [ ] Read any existing HyperV API client service in the Portal (grep for `IHyperVApiClient`) to understand how cluster endpoints will be called
- [ ] Create `src/FuseCP.Portal/Components/Pages/HyperV/Clusters/Index.razor`:
  - Route: `@page "/hyperv/clusters"`
  - Attribute: `[Authorize(Roles = "Administrator")]`
  - Calls `GET /api/hyperv/clusters` on load
  - Displays a card/table with columns: Cluster Name, IP, Quorum State, Node Count, VM Count
  - Each row links to `/hyperv/clusters/{name}`
  - Uses `LoadingSpinner`, `EmptyState`, `ErrorAlert` shared components consistent with existing pages
- [ ] Create `src/FuseCP.Portal/Components/Pages/HyperV/Clusters/Detail.razor`:
  - Route: `@page "/hyperv/clusters/{ClusterName}"`
  - Attribute: `[Authorize(Roles = "Administrator")]`
  - Health bar at top: cluster name, quorum status badge (Healthy=green, DegradedQuorum=yellow, NoQuorum=red), last-updated timestamp
  - Nodes table: Name, State badge, CPU %, Memory MB, VM Count; row actions: "Enter Maintenance" button (opens confirm dialog listing VMs to be drained), "Resume" button (only shown when node is Paused)
  - VMs table: Name, State, Owner Node, VM actions: Start, Stop, Migrate (opens migration dialog), Snapshot
  - Migration dialog: source node (read-only), destination node dropdown (only Up nodes, excludes source), Confirm button calls `POST /api/hyperv/clusters/{cluster}/vms/{vmId}/migrate`; on success updates `ownerNode` in the VMs table row
  - Maintenance confirm dialog: lists VMs that will be drained; Confirm calls `POST /api/hyperv/clusters/{cluster}/nodes/{node}/maintenance`; on success node row updates to Paused state
  - All dialogs use the existing `ConfirmDialog` or `Modal` shared components
  - Uses `@rendermode InteractiveServer`
- [ ] Modify `src/FuseCP.Portal/Components/Layout/ContextSidebar.razor` — add a "Clusters" nav link pointing to `/hyperv/clusters` in the Hyper-V section, following the same NavLink pattern used for the existing Hyper-V library link
- [ ] Verify the Portal builds: `dotnet build src/FuseCP.Portal/FuseCP.Portal.csproj`
- [ ] Start the Portal and verify `/hyperv/clusters` loads and displays LabCluster
- [ ] Stop the service after verification

---

## Task 10: Integration tests

**Agent:** `test-coverage`
**Model:** sonnet
**Purpose:** Create a PowerShell integration test script covering all 15 test cases from the spec, following the same patterns as the existing `Run-TenantIntegrationTests.ps1`.

**Files to Create:**
- `scripts/api-tests/Run-ClusterIntegrationTests.ps1`

**Steps:**
- [ ] Read `scripts/api-tests/Run-TenantIntegrationTests.ps1` in full to understand: base URL construction, admin/tenant key passing, request helper functions, result tracking, pass/fail reporting format
- [ ] Create `scripts/api-tests/Run-ClusterIntegrationTests.ps1` with the 15 test cases from the spec:

  | # | Test | Method | Endpoint | Expected |
  |---|------|--------|----------|----------|
  | 1 | List clusters | GET | `/api/hyperv/clusters` | Array with `name: "LabCluster"` |
  | 2 | Cluster health | GET | `/api/hyperv/clusters/LabCluster` | `quorumState: "Healthy"`, `nodes` array |
  | 3 | Create cluster VM | POST | `/api/hyperv/clusters/LabCluster/vms` | 201, `isHighlyAvailable: true`, path contains `ClusterStorage\Volume1` |
  | 4 | List cluster VMs | GET | `/api/hyperv/clusters/LabCluster/vms` | All VMs have non-null `ownerNode` |
  | 5 | VM detail | GET | `/api/hyperv/clusters/LabCluster/vms/{id}` | VM detail with correct `ownerNode` |
  | 6 | Start VM | POST | `/api/hyperv/clusters/LabCluster/vms/{id}/start` | 200, state becomes Running |
  | 7 | Stop VM | POST | `/api/hyperv/clusters/LabCluster/vms/{id}/stop` | 200, state becomes Off |
  | 8 | Live migrate | POST | `/api/hyperv/clusters/LabCluster/vms/{id}/migrate` | 200, `ownerNode` changed to destination |
  | 9 | Post-migration start | POST | `/api/hyperv/clusters/LabCluster/vms/{id}/start` | 200 — routes to new owner |
  | 10 | Snapshot | POST | `/api/hyperv/clusters/LabCluster/vms/{id}/snapshot` | 200 — routes to current owner |
  | 11 | Node list | GET | `/api/hyperv/clusters/LabCluster/nodes` | Both nodes, state Up |
  | 12 | Enter maintenance | POST | `/api/hyperv/clusters/LabCluster/nodes/HYPERVLAB/maintenance` | 200, node Paused, VMs on FUSECP |
  | 13 | Resume node | POST | `/api/hyperv/clusters/LabCluster/nodes/HYPERVLAB/resume` | 200, node Up |
  | 14 | Tenant key rejected | GET | `/api/hyperv/clusters` (tenant key) | 403 Forbidden |
  | 15 | Standalone routes unbroken | GET | `/api/hyperv/HYPERVLAB/vms` | 200, existing behavior |

- [ ] Script accepts `-BaseUrl`, `-AdminKey`, `-TenantKey` parameters with defaults matching the lab environment
- [ ] Script tracks `$Passed`, `$Failed` counters; prints summary at end: "X/15 tests passed"
- [ ] Tests 3–13 use the VM created in test 3 (capture `vmId` from the 201 response and reuse it across subsequent tests)
- [ ] Test 8 captures the new `ownerNode` and uses it to verify test 9 routes correctly
- [ ] After test 13 (resume), clean up the test VM by calling DELETE or stop+remove
- [ ] Run the test script against the lab API and verify all 15 pass

---

## Task 11: Security review

**Agent:** `security-guardian`
**Model:** opus
**Purpose:** Review all new cluster endpoints, the provider implementation, and the factory for security issues. Verify PlatformAdmin enforcement on every route, confirm tenant keys receive 403, check for command injection, and validate WinRM credential handling.

**Files to Review:**
- `src/FuseCP.EnterpriseServer/Endpoints/HyperVClusterEndpoints.cs`
- `src/FuseCP.Providers.HyperV/HyperVClusterProvider.cs`
- `src/FuseCP.Providers.HyperV/Scripts/HyperVClusterScripts.cs`
- `src/FuseCP.EnterpriseServer/Services/HyperVProviderFactory.cs`
- `src/FuseCP.EnterpriseServer/Program.cs`

**Steps:**
- [ ] Verify every route in `HyperVClusterEndpoints.cs` has `.RequireAuthorization("PlatformAdmin")` — no route is missing the attribute or inheriting a weaker policy
- [ ] Verify that when a request is made with a tenant-scoped API key, it receives `403 Forbidden` (not 401 or 404) on any `/api/hyperv/clusters/*` endpoint
- [ ] Review `HyperVClusterScripts.cs` for command injection: check that all string interpolation values (cluster FQDN, node names, VM IDs) are properly validated or sanitized before being inserted into PS command strings; flag any input that flows directly from user-supplied request body or URL parameters without validation
- [ ] Review `HyperVClusterEndpoints.cs` error responses: verify that 500 error messages do not leak internal infrastructure details (hostnames, file paths, stack traces) to API callers
- [ ] Review WinRM credential handling in `HyperVClusterProvider.cs` and `HyperVProviderFactory.cs`: verify credentials are not logged, not returned in responses, and not stored in memory beyond their required scope
- [ ] Verify the `MigrateVmRequest.DestinationNode` value is validated against the known cluster node list before being passed to `HyperVClusterScripts.MigrateVm` — a caller should not be able to specify an arbitrary hostname
- [ ] Verify the `{action}` route parameter in `POST /clusters/{cluster}/vms/{vmId}/{action}` is validated against an allowlist (start, stop, snapshot) and does not allow arbitrary PS injection
- [ ] Document findings in a brief security review note in `ai_working/decisions/`; create a decision record if any design changes are required
- [ ] If issues are found, raise them as blocking items before Task 12

---

## Task 12: Final cleanup

**Agent:** `post-task-cleanup`
**Model:** haiku
**Purpose:** Final hygiene pass across all new and modified files before the branch is submitted for PR review.

**Files to Review:**
- All files created or modified in Tasks 1–11

**Steps:**
- [ ] Read each new file and verify: no debug `Console.WriteLine` or `Write-Host` debug statements left in C# code; no commented-out code blocks; no `// TODO` or `// FIXME` comments without an accompanying issue reference
- [ ] Verify every C# file ends with a newline character
- [ ] Verify every `.sql` file ends with a newline character
- [ ] Verify every `.ps1` script ends with a newline character
- [ ] Verify every `.razor` file ends with a newline character
- [ ] Check for unused `using` directives in all new C# files
- [ ] Check for unused `@using` directives in all new Razor files
- [ ] Verify namespace declarations match the project conventions (check existing files in the same directory for the correct namespace)
- [ ] Run `dotnet build C:\claude\fusecp-enterprise\src\FuseCP.EnterpriseServer\FuseCP.EnterpriseServer.csproj` — must produce 0 errors, 0 warnings
- [ ] Run `dotnet build C:\claude\fusecp-enterprise\src\FuseCP.Portal\FuseCP.Portal.csproj` — must produce 0 errors, 0 warnings
- [ ] Run `dotnet build C:\claude\fusecp-enterprise\src\FuseCP.Providers.HyperV\FuseCP.Providers.HyperV.csproj` — must produce 0 errors, 0 warnings
- [ ] Review all PowerShell scripts for consistent indentation (4 spaces) and parameter block formatting
- [ ] Verify `scripts/cluster-setup/Setup-HyperVCluster.ps1` has no hardcoded credentials
- [ ] Verify the migration file `114_AddHyperVClusterTables.sql` contains no data from non-lab environments (no production IPs or names other than the lab)
- [ ] Final confirmation: run `scripts/api-tests/Run-ClusterIntegrationTests.ps1` — all 15 tests must pass

---

## Summary

| Task | Agent | Model | Deliverable |
|------|-------|-------|-------------|
| 0 — Research | `agentic-search` | haiku | Findings report: file:line map of all methods requiring override |
| 1 — Infra script | `modular-builder` | sonnet | `scripts/cluster-setup/Setup-HyperVCluster.ps1` |
| 2 — Infra validation | `modular-builder` | sonnet | Validated cluster: both nodes Up, CSV accessible, live migration works |
| 3 — DB migration | `modular-builder` | sonnet | `src/FuseCP.Database/Migrations/114_AddHyperVClusterTables.sql` (applied) |
| 4 — Models & interface | `modular-builder` | sonnet | `HyperVCluster.cs`, `IHyperVClusterProvider.cs`, `VirtualMachine.cs` updated |
| 5 — PS scripts | `modular-builder` | sonnet | `src/FuseCP.Providers.HyperV/Scripts/HyperVClusterScripts.cs` |
| 6 — Provider impl | `modular-builder` | sonnet | `src/FuseCP.Providers.HyperV/HyperVClusterProvider.cs` |
| 7 — Factory update | `modular-builder` | sonnet | `HyperVProviderFactory.cs` with cluster resolution, standalone path unchanged |
| 8 — API endpoints | `modular-builder` | sonnet | `HyperVClusterEndpoints.cs` + wired into `HyperVEndpoints.cs` and `Program.cs` |
| 9 — Portal UI | `modular-builder` | sonnet | `Clusters/Index.razor`, `Clusters/Detail.razor`, `ContextSidebar.razor` updated |
| 10 — Integration tests | `test-coverage` | sonnet | `scripts/api-tests/Run-ClusterIntegrationTests.ps1` — 15/15 passing |
| 11 — Security review | `security-guardian` | opus | Security sign-off: PlatformAdmin enforcement, no injection, no leakage |
| 12 — Cleanup | `post-task-cleanup` | haiku | All files clean, 0 build warnings, 15/15 tests passing |
