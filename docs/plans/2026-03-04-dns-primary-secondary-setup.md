# DNS Primary/Secondary Setup Implementation Plan

> **For Claude:** REQUIRED: Use /subagent-dev to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Set up proper primary/secondary DNS with FINALTEST as primary (dns1.lab.ergonet.pl / 46.45.123.211) and DEV as secondary (dns2.lab.ergonet.pl / 46.45.123.210), and update FuseCP to auto-create secondary zones with correct NS and SOA when provisioning tenant organizations.

**Architecture:** Infrastructure scripts fix the lab environment first (WinRM, glue records, firewall, existing zones). Then the FuseCP codebase is extended: `DnsSettings` record gains 10 new fields loaded from `ServiceProperties` (SolidCP-compatible group="DNS"), `IDnsProvider`/`MsDnsProvider` gain 5 new methods for secondary zones, NS records, and SOA configuration, and `OrganizationProvisioningService` is enhanced to call them during provisioning. A new `GET/PUT /api/dns/settings` admin endpoint exposes configuration. All DB changes are additive-only migrations.

**Tech Stack:** C# (.NET 8), PowerShell (DnsServer module), SQL Server, Blazor (InteractiveServer), WinRM

**Spec:** `docs/specs/2026-03-04-dns-primary-secondary-setup-design.md`

---

## Task 0: Research — Trace DNS provider architecture and DI wiring

**Agent:** `agentic-search`
**Model:** haiku

**Files to Read:**
- `src/FuseCP.Providers.DNS/IDnsProvider.cs`
- `src/FuseCP.Providers.DNS/MsDnsProvider.cs`
- `src/FuseCP.EnterpriseServer/Services/IServerSettingsService.cs`
- `src/FuseCP.EnterpriseServer/Services/ServerSettingsService.cs`
- `src/FuseCP.Database/Repositories/SolidCP/IServerSettingsRepository.cs`
- `src/FuseCP.Database/Repositories/SolidCP/ServerSettingsRepository.cs`
- `src/FuseCP.EnterpriseServer/Services/OrganizationProvisioningService.cs`
- `src/FuseCP.EnterpriseServer/Endpoints/DomainDnsEndpoints.cs`
- `src/FuseCP.EnterpriseServer/Program.cs`

**Steps:**
- [ ] **Step 1: Map IDnsProvider interface**
  Read `IDnsProvider.cs` — list all 9 method signatures and their parameter types.

- [ ] **Step 2: Trace MsDnsProvider PowerShell patterns**
  Read `MsDnsProvider.cs` — document `_psExecutor.ExecuteCommandAsync` call signature, `PowerShellCommand` constructor usage, and the `GetRecordCreationCommand` switch pattern (lines 218-268).

- [ ] **Step 3: Document DnsSettings loading chain**
  Read `ServerSettingsService.cs:101-120` — trace `GetDnsSettingsAsync` flow. Read `IServerSettingsRepository.cs:55-60` — note `GetServicePropertiesAsync` vs `GetServicePropertiesByGroupAsync` signatures.

- [ ] **Step 4: Trace provisioning DNS section**
  Read `OrganizationProvisioningService.cs:173-230` — document the exact sequence: settings validation, `CreateZoneAsync`, template loop, rollback registration.

- [ ] **Step 5: Identify DI registration for DNS**
  Read `Program.cs` — find the `MsDnsProvider` and `IDnsProvider` registration lines and note exact DI scope (Singleton/Scoped/Transient).

- [ ] **Step 6: Document existing DNS endpoint patterns**
  Read `DomainDnsEndpoints.cs:10-24` — note the `MapGroup` pattern, auth requirements, and TenantContext usage.

- [ ] **Step 7: Produce findings report**
  Write a structured findings report covering: (a) exact `PowerShellCommand` constructor overloads available, (b) whether `_psExecutor` supports a `-ComputerName` parameter pass-through for remote execution, (c) exact cache key patterns in `ServerSettingsService`, (d) DI registration lines for DNS components in `Program.cs`, (e) any existing `GetServicePropertiesByGroupAsync` call using group="DNS" (there should be none yet).

---

## Task 1: Infrastructure — Fix WinRM to FINALTEST

**Agent:** `bug-hunter`
**Model:** sonnet

**Files to Create:**
- `scripts/dns/Diagnose-WinRM-FINALTEST.ps1`
- `scripts/dns/Fix-WinRM-FINALTEST.ps1`

**Steps:**
- [ ] **Step 1: Create diagnostic script**
  Create `scripts/dns/Diagnose-WinRM-FINALTEST.ps1`:

```powershell
<#
.SYNOPSIS
    Diagnoses WinRM connectivity from DEV to FINALTEST (172.31.251.101).
    Checks firewall rules, listener status, and SPNs.

.NOTES
    Run on DEV (172.31.251.100) as Administrator.
    WinRM TCP/UDP 53 via RPC works (DNS cmdlets -ComputerName), but WinRM on 5985 times out.
#>

param(
    [string]$TargetHost = "172.31.251.101",
    [string]$TargetName = "FINALTEST"
)

Write-Host "=== WinRM Diagnostics: DEV -> $TargetName ($TargetHost) ===" -ForegroundColor Cyan

# Test basic connectivity
Write-Host "`n[1] TCP port 5985 reachability" -ForegroundColor Yellow
$tcpTest = Test-NetConnection -ComputerName $TargetHost -Port 5985 -WarningAction SilentlyContinue
Write-Host "  TCP 5985 open: $($tcpTest.TcpTestSucceeded)"

$tcpTest443 = Test-NetConnection -ComputerName $TargetHost -Port 5986 -WarningAction SilentlyContinue
Write-Host "  TCP 5986 open: $($tcpTest443.TcpTestSucceeded)"

# Test WinRM session
Write-Host "`n[2] WinRM session attempt (10s timeout)" -ForegroundColor Yellow
try {
    $so = New-PSSessionOption -OpenTimeout 10000 -OperationTimeout 10000
    $session = New-PSSession -ComputerName $TargetHost -SessionOption $so -Authentication Negotiate -ErrorAction Stop
    Write-Host "  WinRM session: SUCCESS" -ForegroundColor Green
    Remove-PSSession $session
} catch {
    Write-Host "  WinRM session FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# Check local WinRM listeners
Write-Host "`n[3] Local WinRM listeners on $TargetName (via DNS RPC)" -ForegroundColor Yellow
try {
    $listeners = Invoke-Command -ComputerName $TargetHost -ScriptBlock {
        winrm enumerate winrm/config/listener 2>&1
    } -ErrorAction Stop
    Write-Host $listeners
} catch {
    Write-Host "  Cannot enumerate listeners via Invoke-Command: $($_.Exception.Message)" -ForegroundColor Red
    # Fallback: use psexec or just report
    Write-Host "  Try running on FINALTEST directly: winrm enumerate winrm/config/listener"
}

# Check firewall rules via netsh (works via RPC-based cmdlets)
Write-Host "`n[4] Firewall WinRM rules on $TargetName (via Get-NetFirewallRule)" -ForegroundColor Yellow
try {
    $rules = Get-NetFirewallRule -CimSession $TargetHost -DisplayGroup "Windows Remote Management" -ErrorAction Stop
    foreach ($r in $rules) {
        Write-Host "  Rule: $($r.DisplayName) | Enabled: $($r.Enabled) | Direction: $($r.Direction) | Profile: $($r.Profile)"
    }
} catch {
    Write-Host "  CimSession failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Check SPNs
Write-Host "`n[5] WSMAN SPN check for $TargetName" -ForegroundColor Yellow
try {
    $spns = & setspn -L $TargetName 2>&1
    $wsmanSpns = $spns | Where-Object { $_ -match "WSMAN" }
    if ($wsmanSpns) {
        Write-Host "  WSMAN SPNs found:" -ForegroundColor Green
        $wsmanSpns | ForEach-Object { Write-Host "    $_" }
    } else {
        Write-Host "  No WSMAN SPNs found — this may cause Kerberos auth failures" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  SPN check failed: $($_.Exception.Message)"
}

Write-Host "`n=== Diagnosis complete ===" -ForegroundColor Cyan
```

- [ ] **Step 2: Create fix script**
  Create `scripts/dns/Fix-WinRM-FINALTEST.ps1`:

```powershell
<#
.SYNOPSIS
    Fixes WinRM on FINALTEST to allow connections from DEV.
    Must be run DIRECTLY on FINALTEST (172.31.251.101) as Administrator.

.NOTES
    Since WinRM from DEV fails, RDP to FINALTEST and run this script there,
    or use: psexec \\FINALTEST -s powershell -File Fix-WinRM-FINALTEST.ps1
#>

Write-Host "=== Fixing WinRM on FINALTEST ===" -ForegroundColor Cyan

# Ensure WinRM service is running
Write-Host "[1] Starting WinRM service..." -ForegroundColor Yellow
Set-Service -Name WinRM -StartupType Automatic
Start-Service -Name WinRM -ErrorAction SilentlyContinue

# Run quick config to create default listeners
Write-Host "[2] Running winrm quickconfig..." -ForegroundColor Yellow
winrm quickconfig -quiet -force 2>&1 | Write-Host

# Enable WinRM firewall rules for Domain and Private profiles
Write-Host "[3] Enabling WinRM firewall rules..." -ForegroundColor Yellow
Enable-NetFirewallRule -DisplayGroup "Windows Remote Management"

# Also ensure port 5985 is open inbound
$existing5985 = Get-NetFirewallRule -DisplayName "WinRM-HTTP-FuseCP" -ErrorAction SilentlyContinue
if (-not $existing5985) {
    New-NetFirewallRule `
        -DisplayName "WinRM-HTTP-FuseCP" `
        -Direction Inbound `
        -Protocol TCP `
        -LocalPort 5985 `
        -Action Allow `
        -Profile Domain,Private `
        -Description "Allow WinRM HTTP from lab network (FuseCP automation)"
    Write-Host "  Created WinRM-HTTP-FuseCP firewall rule" -ForegroundColor Green
} else {
    Write-Host "  WinRM-HTTP-FuseCP rule already exists, ensuring enabled..." -ForegroundColor Yellow
    Enable-NetFirewallRule -DisplayName "WinRM-HTTP-FuseCP"
}

# Check and set TrustedHosts to include DEV (172.31.251.100)
Write-Host "[4] Configuring TrustedHosts..." -ForegroundColor Yellow
$currentTrusted = (Get-Item WSMan:\localhost\Client\TrustedHosts).Value
if ($currentTrusted -notmatch "172\.31\.251\.100") {
    $newTrusted = if ([string]::IsNullOrWhiteSpace($currentTrusted)) {
        "172.31.251.100"
    } else {
        "$currentTrusted,172.31.251.100"
    }
    Set-Item WSMan:\localhost\Client\TrustedHosts -Value $newTrusted -Force
    Write-Host "  TrustedHosts updated: $newTrusted" -ForegroundColor Green
} else {
    Write-Host "  172.31.251.100 already in TrustedHosts" -ForegroundColor Green
}

# Register WSMAN SPNs if missing
Write-Host "[5] Registering WSMAN SPNs..." -ForegroundColor Yellow
$hostname = $env:COMPUTERNAME
$fqdn = [System.Net.Dns]::GetHostEntry($hostname).HostName
setspn -S "WSMAN/$hostname" "$hostname" 2>&1 | Write-Host
setspn -S "WSMAN/$fqdn" "$hostname" 2>&1 | Write-Host

# Test local WinRM listener
Write-Host "[6] Verifying WinRM listener..." -ForegroundColor Yellow
winrm enumerate winrm/config/listener 2>&1 | Write-Host

Write-Host "`n=== Fix complete. Test from DEV: Test-NetConnection -ComputerName 172.31.251.101 -Port 5985 ===" -ForegroundColor Cyan
```

- [ ] **Step 3: Commit**
  ```bash
  cd /c/claude/fusecp-enterprise
  git add scripts/dns/Diagnose-WinRM-FINALTEST.ps1 scripts/dns/Fix-WinRM-FINALTEST.ps1
  git commit -m "infra: add WinRM diagnostic and fix scripts for FINALTEST

  Co-Authored-By: Claude <noreply@anthropic.com>"
  ```

---

## Task 2: Infrastructure — DNS glue records and firewall rules

**Agent:** `modular-builder`
**Model:** sonnet

**Files to Create:**
- `scripts/dns/Setup-DnsGlueAndFirewall.ps1`

**Steps:**
- [ ] **Step 1: Create glue records and firewall script**
  Create `scripts/dns/Setup-DnsGlueAndFirewall.ps1`:

```powershell
<#
.SYNOPSIS
    Creates dns1/dns2 glue records in lab.ergonet.pl and opens firewall ports for
    DNS queries (TCP/UDP 53) and zone transfers (TCP 53, restricted).

.NOTES
    Run on FINALTEST (172.31.251.101) as Administrator.
    FINALTEST = 172.31.251.101 = dns1 = 46.45.123.211
    DEV       = 172.31.251.100 = dns2 = 46.45.123.210
#>

param(
    [string]$PrimaryDnsIpLab    = "172.31.251.101",   # FINALTEST lab IP
    [string]$SecondaryDnsIpLab  = "172.31.251.100",   # DEV lab IP
    [string]$PrimaryDnsIpPub    = "46.45.123.211",    # dns1 public IP
    [string]$SecondaryDnsIpPub  = "46.45.123.210",    # dns2 public IP
    [string]$ZoneName           = "lab.ergonet.pl"
)

Write-Host "=== DNS Glue Records and Firewall Setup ===" -ForegroundColor Cyan

# --- Glue records in lab.ergonet.pl ---
Write-Host "`n[1] Creating DNS glue records in $ZoneName..." -ForegroundColor Yellow

# Check if zone exists
$zone = Get-DnsServerZone -Name $ZoneName -ErrorAction SilentlyContinue
if (-not $zone) {
    Write-Host "  ERROR: Zone $ZoneName not found on this server!" -ForegroundColor Red
    exit 1
}

# dns1 A record (primary / FINALTEST)
$existingDns1 = Get-DnsServerResourceRecord -ZoneName $ZoneName -Name "dns1" -RRType A -ErrorAction SilentlyContinue
if ($existingDns1) {
    Write-Host "  dns1 A record already exists: $($existingDns1.RecordData.IPv4Address)" -ForegroundColor Yellow
} else {
    Add-DnsServerResourceRecordA -ZoneName $ZoneName -Name "dns1" -IPv4Address $PrimaryDnsIpPub -TimeToLive 3600
    Write-Host "  Created: dns1 A $PrimaryDnsIpPub" -ForegroundColor Green
}

# dns2 A record (secondary / DEV)
$existingDns2 = Get-DnsServerResourceRecord -ZoneName $ZoneName -Name "dns2" -RRType A -ErrorAction SilentlyContinue
if ($existingDns2) {
    Write-Host "  dns2 A record already exists: $($existingDns2.RecordData.IPv4Address)" -ForegroundColor Yellow
} else {
    Add-DnsServerResourceRecordA -ZoneName $ZoneName -Name "dns2" -IPv4Address $SecondaryDnsIpPub -TimeToLive 3600
    Write-Host "  Created: dns2 A $SecondaryDnsIpPub" -ForegroundColor Green
}

# --- Firewall rules on FINALTEST (primary DNS) ---
Write-Host "`n[2] Configuring firewall on FINALTEST (primary DNS)..." -ForegroundColor Yellow

# DNS queries — TCP/UDP 53 inbound from anywhere
$existingDnsQuery = Get-NetFirewallRule -DisplayName "DNS-Queries-FuseCP" -ErrorAction SilentlyContinue
if (-not $existingDnsQuery) {
    New-NetFirewallRule `
        -DisplayName "DNS-Queries-FuseCP" `
        -Direction Inbound `
        -Protocol TCP `
        -LocalPort 53 `
        -Action Allow `
        -Profile Any `
        -Description "Allow inbound DNS TCP queries (FuseCP managed)"
    New-NetFirewallRule `
        -DisplayName "DNS-Queries-UDP-FuseCP" `
        -Direction Inbound `
        -Protocol UDP `
        -LocalPort 53 `
        -Action Allow `
        -Profile Any `
        -Description "Allow inbound DNS UDP queries (FuseCP managed)"
    Write-Host "  Created DNS query rules (TCP+UDP 53 from Any)" -ForegroundColor Green
} else {
    Write-Host "  DNS query rules already exist" -ForegroundColor Yellow
}

# Zone transfer — TCP 53 inbound restricted to DEV lab IP only
$existingZtRule = Get-NetFirewallRule -DisplayName "DNS-ZoneTransfer-FuseCP" -ErrorAction SilentlyContinue
if (-not $existingZtRule) {
    New-NetFirewallRule `
        -DisplayName "DNS-ZoneTransfer-FuseCP" `
        -Direction Inbound `
        -Protocol TCP `
        -LocalPort 53 `
        -RemoteAddress $SecondaryDnsIpLab `
        -Action Allow `
        -Profile Any `
        -Description "Allow zone transfer TCP 53 from DEV (secondary DNS) only"
    Write-Host "  Created zone transfer rule (TCP 53 from $SecondaryDnsIpLab only)" -ForegroundColor Green
} else {
    Write-Host "  Zone transfer rule already exists" -ForegroundColor Yellow
}

# --- Firewall rules on DEV (secondary DNS) via Invoke-Command ---
Write-Host "`n[3] Configuring firewall on DEV ($SecondaryDnsIpLab) (secondary DNS)..." -ForegroundColor Yellow

try {
    Invoke-Command -ComputerName $SecondaryDnsIpLab -ScriptBlock {
        param($PrimaryIp, $SecondaryIp)

        # DNS queries
        $q = Get-NetFirewallRule -DisplayName "DNS-Queries-FuseCP" -ErrorAction SilentlyContinue
        if (-not $q) {
            New-NetFirewallRule -DisplayName "DNS-Queries-FuseCP" -Direction Inbound -Protocol TCP -LocalPort 53 -Action Allow -Profile Any -Description "Allow inbound DNS TCP queries (FuseCP managed)"
            New-NetFirewallRule -DisplayName "DNS-Queries-UDP-FuseCP" -Direction Inbound -Protocol UDP -LocalPort 53 -Action Allow -Profile Any -Description "Allow inbound DNS UDP queries (FuseCP managed)"
            Write-Host "  DEV: Created DNS query rules" -ForegroundColor Green
        } else {
            Write-Host "  DEV: DNS query rules already exist" -ForegroundColor Yellow
        }

        # Zone transfer incoming from FINALTEST
        $zt = Get-NetFirewallRule -DisplayName "DNS-ZoneTransfer-FuseCP" -ErrorAction SilentlyContinue
        if (-not $zt) {
            New-NetFirewallRule -DisplayName "DNS-ZoneTransfer-FuseCP" -Direction Inbound -Protocol TCP -LocalPort 53 -RemoteAddress $PrimaryIp -Action Allow -Profile Any -Description "Allow zone transfer TCP 53 from FINALTEST (primary DNS) only"
            Write-Host "  DEV: Created zone transfer rule (TCP 53 from $PrimaryIp)" -ForegroundColor Green
        } else {
            Write-Host "  DEV: Zone transfer rule already exists" -ForegroundColor Yellow
        }
    } -ArgumentList $PrimaryDnsIpLab, $SecondaryDnsIpLab -ErrorAction Stop
} catch {
    Write-Host "  WARNING: Could not configure DEV firewall remotely: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "  Run manually on DEV:" -ForegroundColor Yellow
    Write-Host "    New-NetFirewallRule -DisplayName 'DNS-Queries-FuseCP' -Direction Inbound -Protocol TCP -LocalPort 53 -Action Allow -Profile Any"
    Write-Host "    New-NetFirewallRule -DisplayName 'DNS-Queries-UDP-FuseCP' -Direction Inbound -Protocol UDP -LocalPort 53 -Action Allow -Profile Any"
    Write-Host "    New-NetFirewallRule -DisplayName 'DNS-ZoneTransfer-FuseCP' -Direction Inbound -Protocol TCP -LocalPort 53 -RemoteAddress $PrimaryDnsIpLab -Action Allow -Profile Any"
}

Write-Host "`n=== Glue records and firewall setup complete ===" -ForegroundColor Cyan
```

- [ ] **Step 2: Commit**
  ```bash
  cd /c/claude/fusecp-enterprise
  git add scripts/dns/Setup-DnsGlueAndFirewall.ps1
  git commit -m "infra: add DNS glue records and firewall setup script

  Co-Authored-By: Claude <noreply@anthropic.com>"
  ```

---

## Task 3: Infrastructure — Fix existing tenant zones and create secondaries

**Agent:** `modular-builder`
**Model:** sonnet

**Files to Create:**
- `scripts/dns/Fix-ExistingZones-AddSecondaries.ps1`

**Steps:**
- [ ] **Step 1: Create zone fix script**
  Create `scripts/dns/Fix-ExistingZones-AddSecondaries.ps1`:

```powershell
<#
.SYNOPSIS
    Fixes existing tenant zones on FINALTEST and creates secondary zones on DEV.
    - Enables zone transfers to DEV (172.31.251.100)
    - Adds notify to DEV
    - Adds NS record dns2.lab.ergonet.pl
    - Updates SOA responsible person
    - Creates secondary zone on DEV for each fixed zone

.NOTES
    Run on FINALTEST (172.31.251.101) as Administrator.
    Existing tenant zones: tenanta.lab.ergonet.pl, tenantb.lab.ergonet.pl
    DEV must be reachable via WinRM (run Fix-WinRM-FINALTEST.ps1 first).
#>

param(
    [string[]]$TenantZones       = @("tenanta.lab.ergonet.pl", "tenantb.lab.ergonet.pl"),
    [string]$SecondaryDnsIpLab   = "172.31.251.100",   # DEV
    [string]$PrimaryDnsIpLab     = "172.31.251.101",   # FINALTEST
    [string]$SecondaryNsHostname = "dns2.lab.ergonet.pl",
    [string]$ResponsiblePerson   = "hostmaster.lab.ergonet.pl"
)

Write-Host "=== Fix Existing Tenant Zones + Create Secondaries ===" -ForegroundColor Cyan

foreach ($zoneName in $TenantZones) {
    Write-Host "`n--- Processing zone: $zoneName ---" -ForegroundColor Yellow

    # Verify zone exists on FINALTEST
    $zone = Get-DnsServerZone -Name $zoneName -ErrorAction SilentlyContinue
    if (-not $zone) {
        Write-Host "  WARNING: Zone $zoneName not found on FINALTEST, skipping" -ForegroundColor Red
        continue
    }

    # 1. Enable zone transfers to secondary only
    Write-Host "  [1] Enabling zone transfer to $SecondaryDnsIpLab..."
    Set-DnsServerPrimaryZone `
        -Name $zoneName `
        -SecureSecondaries TransferToSecureServers `
        -SecondaryServers $SecondaryDnsIpLab `
        -Notify Notify `
        -NotifyServers $SecondaryDnsIpLab
    Write-Host "      Done: SecureSecondaries=TransferToSecureServers, Notify=$SecondaryDnsIpLab" -ForegroundColor Green

    # 2. Update SOA responsible person, refresh, retry, expire, minimum TTL
    Write-Host "  [2] Updating SOA..."
    $soaRecord = Get-DnsServerResourceRecord -ZoneName $zoneName -RRType SOA -Name "@"
    if ($soaRecord) {
        $newSoa = $soaRecord.Clone()
        $newSoa.RecordData.ResponsiblePerson = $ResponsiblePerson
        $newSoa.RecordData.RefreshInterval   = [TimeSpan]::FromSeconds(3600)
        $newSoa.RecordData.RetryDelay        = [TimeSpan]::FromSeconds(600)
        $newSoa.RecordData.ExpireLimit       = [TimeSpan]::FromSeconds(1209600)
        $newSoa.RecordData.MinimumTimeToLive = [TimeSpan]::FromSeconds(86400)
        Set-DnsServerResourceRecord -ZoneName $zoneName -OldInputObject $soaRecord -NewInputObject $newSoa
        Write-Host "      SOA updated: ResponsiblePerson=$ResponsiblePerson" -ForegroundColor Green
    } else {
        Write-Host "      WARNING: SOA record not found for $zoneName" -ForegroundColor Red
    }

    # 3. Add NS record for dns2 if not already present
    Write-Host "  [3] Adding NS record $SecondaryNsHostname..."
    $existingNs = Get-DnsServerResourceRecord -ZoneName $zoneName -RRType NS -Name "@" -ErrorAction SilentlyContinue |
        Where-Object { $_.RecordData.NameServer -eq "$SecondaryNsHostname." }
    if ($existingNs) {
        Write-Host "      NS record $SecondaryNsHostname already exists" -ForegroundColor Yellow
    } else {
        Add-DnsServerResourceRecord -ZoneName $zoneName -NS -Name "@" -NameServer "$SecondaryNsHostname."
        Write-Host "      Added NS record: $SecondaryNsHostname" -ForegroundColor Green
    }

    # 4. Create secondary zone on DEV
    Write-Host "  [4] Creating secondary zone on DEV ($SecondaryDnsIpLab)..."
    try {
        Invoke-Command -ComputerName $SecondaryDnsIpLab -ScriptBlock {
            param($ZoneName, $MasterIp)
            $existing = Get-DnsServerZone -Name $ZoneName -ErrorAction SilentlyContinue
            if ($existing) {
                Write-Host "      Secondary zone $ZoneName already exists on DEV" -ForegroundColor Yellow
            } else {
                Add-DnsServerSecondaryZone `
                    -Name $ZoneName `
                    -ZoneFile "$ZoneName.dns" `
                    -MasterServers $MasterIp
                Write-Host "      Created secondary zone $ZoneName (master: $MasterIp)" -ForegroundColor Green
            }
        } -ArgumentList $zoneName, $PrimaryDnsIpLab -ErrorAction Stop
        Write-Host "      Secondary zone created on DEV" -ForegroundColor Green
    } catch {
        Write-Host "      ERROR creating secondary zone on DEV: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "      Run manually on DEV: Add-DnsServerSecondaryZone -Name '$zoneName' -ZoneFile '$zoneName.dns' -MasterServers $PrimaryDnsIpLab"
    }

    # 5. Force zone transfer
    Write-Host "  [5] Triggering zone transfer to DEV..."
    try {
        Invoke-Command -ComputerName $SecondaryDnsIpLab -ScriptBlock {
            param($ZoneName)
            Start-DnsServerZoneTransfer -Name $ZoneName -FullTransfer
        } -ArgumentList $zoneName -ErrorAction Stop
        Write-Host "      Zone transfer initiated" -ForegroundColor Green
    } catch {
        Write-Host "      WARNING: Could not trigger transfer: $($_.Exception.Message)" -ForegroundColor Yellow
    }

    Write-Host "  Zone $zoneName: DONE" -ForegroundColor Green
}

Write-Host "`n=== All zones processed ===" -ForegroundColor Cyan
Write-Host "Verify with: Resolve-DnsName tenanta.lab.ergonet.pl -Server $SecondaryDnsIpLab"
```

- [ ] **Step 2: Commit**
  ```bash
  cd /c/claude/fusecp-enterprise
  git add scripts/dns/Fix-ExistingZones-AddSecondaries.ps1
  git commit -m "infra: add script to fix existing tenant zones and create secondary zones

  Co-Authored-By: Claude <noreply@anthropic.com>"
  ```

---

## Task 4: Database — Migration 120: Seed ServiceProperties and secondary DNS service

**Agent:** `database-architect`
**Model:** sonnet

**Files to Create:**
- `src/FuseCP.Database/Migrations/120_SeedDnsServicePropertiesAndSecondary.sql`

**Steps:**
- [ ] **Step 1: Write failing verification query**
  Before writing the migration, verify what currently exists:
  ```sql
  -- Run to confirm current state (should show only ExternalAddress, InternalAddress, ServerName)
  SELECT PropertyName, PropertyValue
  FROM ServiceProperties
  WHERE ServiceID = 2
  ORDER BY PropertyName;

  -- Confirm secondary DNS service does NOT exist yet
  SELECT s.ServiceID, s.ServerID, s.ServiceName
  FROM Services s
  INNER JOIN Providers p ON s.ProviderID = p.ProviderID
  WHERE p.ProviderID = 410 AND s.ServerID = 6;
  ```

- [ ] **Step 2: Write migration 120**
  Create `src/FuseCP.Database/Migrations/120_SeedDnsServicePropertiesAndSecondary.sql`:

```sql
-- Migration 120: Seed DNS ServiceProperties and create secondary DNS service entry
-- SolidCP-compatible property names for DNS group (backward compatible, additive only)
-- Primary DNS: ServiceID=2, ServerID=1 (FINALTEST, 172.31.251.101)
-- Secondary DNS: new service on ServerID=6 (DEV, 172.31.251.100)

-- =============================================
-- Part 1: Seed ServiceProperties for primary DNS (ServiceID=2)
-- These match SolidCP production property names exactly for backward compatibility.
-- =============================================

-- nameservers: semicolon-separated NS hostnames
IF NOT EXISTS (SELECT 1 FROM ServiceProperties WHERE ServiceID = 2 AND PropertyName = 'nameservers')
    INSERT INTO ServiceProperties (ServiceID, PropertyName, PropertyValue)
    VALUES (2, 'nameservers', 'dns1.lab.ergonet.pl;dns2.lab.ergonet.pl');
ELSE
    UPDATE ServiceProperties
    SET PropertyValue = 'dns1.lab.ergonet.pl;dns2.lab.ergonet.pl'
    WHERE ServiceID = 2 AND PropertyName = 'nameservers';

-- allowzonetransfers: IP allowed to request zone transfers (secondary DNS lab IP)
IF NOT EXISTS (SELECT 1 FROM ServiceProperties WHERE ServiceID = 2 AND PropertyName = 'allowzonetransfers')
    INSERT INTO ServiceProperties (ServiceID, PropertyName, PropertyValue)
    VALUES (2, 'allowzonetransfers', '172.31.251.100');
ELSE
    UPDATE ServiceProperties
    SET PropertyValue = '172.31.251.100'
    WHERE ServiceID = 2 AND PropertyName = 'allowzonetransfers';

-- responsibleperson: SOA RNAME field
IF NOT EXISTS (SELECT 1 FROM ServiceProperties WHERE ServiceID = 2 AND PropertyName = 'responsibleperson')
    INSERT INTO ServiceProperties (ServiceID, PropertyName, PropertyValue)
    VALUES (2, 'responsibleperson', 'hostmaster.lab.ergonet.pl');
ELSE
    UPDATE ServiceProperties
    SET PropertyValue = 'hostmaster.lab.ergonet.pl'
    WHERE ServiceID = 2 AND PropertyName = 'responsibleperson';

-- refreshinterval: SOA refresh in seconds
IF NOT EXISTS (SELECT 1 FROM ServiceProperties WHERE ServiceID = 2 AND PropertyName = 'refreshinterval')
    INSERT INTO ServiceProperties (ServiceID, PropertyName, PropertyValue)
    VALUES (2, 'refreshinterval', '3600');
ELSE
    UPDATE ServiceProperties
    SET PropertyValue = '3600'
    WHERE ServiceID = 2 AND PropertyName = 'refreshinterval';

-- retrydelay: SOA retry in seconds
IF NOT EXISTS (SELECT 1 FROM ServiceProperties WHERE ServiceID = 2 AND PropertyName = 'retrydelay')
    INSERT INTO ServiceProperties (ServiceID, PropertyName, PropertyValue)
    VALUES (2, 'retrydelay', '600');
ELSE
    UPDATE ServiceProperties
    SET PropertyValue = '600'
    WHERE ServiceID = 2 AND PropertyName = 'retrydelay';

-- expirelimit: SOA expire in seconds (14 days)
IF NOT EXISTS (SELECT 1 FROM ServiceProperties WHERE ServiceID = 2 AND PropertyName = 'expirelimit')
    INSERT INTO ServiceProperties (ServiceID, PropertyName, PropertyValue)
    VALUES (2, 'expirelimit', '1209600');
ELSE
    UPDATE ServiceProperties
    SET PropertyValue = '1209600'
    WHERE ServiceID = 2 AND PropertyName = 'expirelimit';

-- minimumttl: SOA minimum TTL in seconds (1 day)
IF NOT EXISTS (SELECT 1 FROM ServiceProperties WHERE ServiceID = 2 AND PropertyName = 'minimumttl')
    INSERT INTO ServiceProperties (ServiceID, PropertyName, PropertyValue)
    VALUES (2, 'minimumttl', '86400');
ELSE
    UPDATE ServiceProperties
    SET PropertyValue = '86400'
    WHERE ServiceID = 2 AND PropertyName = 'minimumttl';

-- RecordDefaultTTL: default TTL for new records (1 hour)
IF NOT EXISTS (SELECT 1 FROM ServiceProperties WHERE ServiceID = 2 AND PropertyName = 'RecordDefaultTTL')
    INSERT INTO ServiceProperties (ServiceID, PropertyName, PropertyValue)
    VALUES (2, 'RecordDefaultTTL', '3600');
ELSE
    UPDATE ServiceProperties
    SET PropertyValue = '3600'
    WHERE ServiceID = 2 AND PropertyName = 'RecordDefaultTTL';

-- RecordMinimumTTL: minimum allowed TTL for records (5 minutes)
IF NOT EXISTS (SELECT 1 FROM ServiceProperties WHERE ServiceID = 2 AND PropertyName = 'RecordMinimumTTL')
    INSERT INTO ServiceProperties (ServiceID, PropertyName, PropertyValue)
    VALUES (2, 'RecordMinimumTTL', '300');
ELSE
    UPDATE ServiceProperties
    SET PropertyValue = '300'
    WHERE ServiceID = 2 AND PropertyName = 'RecordMinimumTTL';

-- =============================================
-- Part 2: Create secondary DNS service entry
-- ProviderID=410 = Microsoft DNS 2012/2016/2019
-- ServerID=6 = DEV (172.31.251.100)
-- =============================================

DECLARE @SecondaryServiceId INT;

-- Create service row if it doesn't exist
IF NOT EXISTS (
    SELECT 1 FROM Services
    WHERE ServerID = 6 AND ProviderID = 410
)
BEGIN
    INSERT INTO Services (ServerID, ProviderID, ServiceName, Comments, Status, MaxAccounts)
    VALUES (6, 410, 'DNS (Secondary)', 'Secondary DNS server on DEV (dns2.lab.ergonet.pl)', 1, 0);

    SET @SecondaryServiceId = SCOPE_IDENTITY();

    -- Seed ServiceProperties for secondary DNS service
    INSERT INTO ServiceProperties (ServiceID, PropertyName, PropertyValue)
    VALUES (@SecondaryServiceId, 'ServerName', '172.31.251.100');

    INSERT INTO ServiceProperties (ServiceID, PropertyName, PropertyValue)
    VALUES (@SecondaryServiceId, 'ExternalAddress', '46.45.123.210');

    PRINT 'Created secondary DNS service (ServiceID=' + CAST(@SecondaryServiceId AS NVARCHAR) + ') on ServerID=6';
END
ELSE
BEGIN
    SELECT @SecondaryServiceId = ServiceID FROM Services WHERE ServerID = 6 AND ProviderID = 410;
    PRINT 'Secondary DNS service already exists (ServiceID=' + CAST(@SecondaryServiceId AS NVARCHAR) + ')';
END

-- =============================================
-- Part 3: Link primary service to secondary via secondarydnsservices property
-- =============================================

IF NOT EXISTS (SELECT 1 FROM ServiceProperties WHERE ServiceID = 2 AND PropertyName = 'secondarydnsservices')
    INSERT INTO ServiceProperties (ServiceID, PropertyName, PropertyValue)
    VALUES (2, 'secondarydnsservices', CAST(@SecondaryServiceId AS NVARCHAR));
ELSE
    UPDATE ServiceProperties
    SET PropertyValue = CAST(@SecondaryServiceId AS NVARCHAR)
    WHERE ServiceID = 2 AND PropertyName = 'secondarydnsservices';

PRINT 'Updated primary DNS service (ServiceID=2) with secondarydnsservices=' + CAST(@SecondaryServiceId AS NVARCHAR);

-- =============================================
-- Verification query
-- =============================================
SELECT 'Primary DNS ServiceProperties' AS Context, PropertyName, PropertyValue
FROM ServiceProperties WHERE ServiceID = 2
ORDER BY PropertyName;
```

- [ ] **Step 3: Verify migration runs correctly**
  After applying, run verification:
  ```sql
  SELECT PropertyName, PropertyValue FROM ServiceProperties WHERE ServiceID = 2 ORDER BY PropertyName;
  -- Should return: allowzonetransfers, expirelimit, minimumttl, nameservers, RecordDefaultTTL,
  -- RecordMinimumTTL, refreshinterval, responsibleperson, retrydelay, secondarydnsservices
  -- Plus original: ExternalAddress, InternalAddress, ServerName
  ```

- [ ] **Step 4: Commit**
  ```bash
  cd /c/claude/fusecp-enterprise
  git add src/FuseCP.Database/Migrations/120_SeedDnsServicePropertiesAndSecondary.sql
  git commit -m "db: migration 120 — seed DNS ServiceProperties and secondary service entry

  Co-Authored-By: Claude <noreply@anthropic.com>"
  ```

---

## Task 5: Expand DnsSettings record and ServerSettingsService

**Agent:** `modular-builder`
**Model:** sonnet

**Files to Modify:**
- `src/FuseCP.EnterpriseServer/Services/IServerSettingsService.cs:48-53`
- `src/FuseCP.EnterpriseServer/Services/ServerSettingsService.cs:101-120`

**Steps:**
- [ ] **Step 1: Write test (TDD — failing)**
  In the test project, add a test that verifies the new fields are populated from mock ServiceProperties. The test should fail until the implementation is complete.

  Create/extend `tests/FuseCP.EnterpriseServer.Tests/Services/ServerSettingsServiceTests.cs` (or the equivalent test file for this service). Write a test named `GetDnsSettingsAsync_LoadsNameServersFromServiceProperties`:

  ```csharp
  [Fact]
  public async Task GetDnsSettingsAsync_LoadsNameServersFromServiceProperties()
  {
      // Arrange
      var mockRepo = new Mock<IServerSettingsRepository>();
      var server = new ServerRecord { ServerID = 1, DnsEnabled = true, DnsServer = "172.31.251.101" };
      mockRepo.Setup(r => r.GetAllServersAsync(default)).ReturnsAsync([server]);
      mockRepo.Setup(r => r.GetServicePropertiesByGroupAsync(1, "DNS", default))
          .ReturnsAsync(new Dictionary<string, string>
          {
              ["nameservers"]        = "dns1.lab.ergonet.pl;dns2.lab.ergonet.pl",
              ["allowzonetransfers"] = "172.31.251.100",
              ["responsibleperson"]  = "hostmaster.lab.ergonet.pl",
              ["refreshinterval"]    = "3600",
              ["retrydelay"]         = "600",
              ["expirelimit"]        = "1209600",
              ["minimumttl"]         = "86400",
              ["RecordDefaultTTL"]   = "3600",
              ["RecordMinimumTTL"]   = "300",
              ["secondarydnsservices"] = "3",
          });
      mockRepo.Setup(r => r.GetServicePropertiesAsync(3, default))
          .ReturnsAsync(new Dictionary<string, string> { ["ServerName"] = "172.31.251.100" });

      var cache = new MemoryCache(new MemoryCacheOptions());
      var logger = NullLogger<ServerSettingsService>.Instance;
      var svc = new ServerSettingsService(mockRepo.Object, cache, logger);

      // Act
      var settings = await svc.GetDnsSettingsAsync(1);

      // Assert
      settings.NameServers.Should().BeEquivalentTo(["dns1.lab.ergonet.pl", "dns2.lab.ergonet.pl"]);
      settings.AllowZoneTransfers.Should().Be("172.31.251.100");
      settings.ResponsiblePerson.Should().Be("hostmaster.lab.ergonet.pl");
      settings.RefreshInterval.Should().Be(3600);
      settings.RetryDelay.Should().Be(600);
      settings.ExpireLimit.Should().Be(1209600);
      settings.MinimumTtl.Should().Be(86400);
      settings.RecordDefaultTtl.Should().Be(3600);
      settings.RecordMinimumTtl.Should().Be(300);
      settings.SecondaryDnsServiceId.Should().Be(3);
      settings.SecondaryServer.Should().Be("172.31.251.100");
  }
  ```

- [ ] **Step 2: Verify test fails**
  ```bash
  cd /c/claude/fusecp-enterprise
  uv run dotnet test --filter "GetDnsSettingsAsync_LoadsNameServersFromServiceProperties" 2>&1 | tail -20
  ```
  Confirm compilation error or assertion failure.

- [ ] **Step 3: Expand DnsSettings record**
  Modify `src/FuseCP.EnterpriseServer/Services/IServerSettingsService.cs`, replacing lines 48-53:

  ```csharp
  public sealed record DnsSettings
  {
      public string Server { get; init; } = "";
      public string Username { get; init; } = "";
      public string Password { get; init; } = "";
      // Fields loaded from ServiceProperties (SolidCP-compatible property names)
      public string[] NameServers { get; init; } = [];
      public string AllowZoneTransfers { get; init; } = "";
      public int? SecondaryDnsServiceId { get; init; }
      public string ResponsiblePerson { get; init; } = "";
      public int RefreshInterval { get; init; } = 3600;
      public int RetryDelay { get; init; } = 600;
      public int ExpireLimit { get; init; } = 1209600;
      public int MinimumTtl { get; init; } = 86400;
      public int RecordDefaultTtl { get; init; } = 3600;
      public int RecordMinimumTtl { get; init; } = 300;
      // Resolved from SecondaryDnsServiceId via GetServicePropertiesAsync
      public string SecondaryServer { get; init; } = "";
  }
  ```

- [ ] **Step 4: Expand GetDnsSettingsAsync**
  Modify `src/FuseCP.EnterpriseServer/Services/ServerSettingsService.cs`, replacing lines 101-120:

  ```csharp
  public async Task<DnsSettings> GetDnsSettingsAsync(int serverId = 1, CancellationToken ct = default)
  {
      return await _cache.GetOrCreateAsync($"dns-settings-{serverId}", async entry =>
      {
          entry.AbsoluteExpirationRelativeToNow = CacheDuration;
          _logger.LogDebug("Loading DNS settings from DB for server {ServerId}", serverId);

          var allServers = await _repo.GetAllServersAsync(ct);
          var dnsServer = allServers.FirstOrDefault(s => s.DnsEnabled && !string.IsNullOrEmpty(s.DnsServer))
              ?? await _repo.GetServerAsync(serverId, ct);

          var props = await _repo.GetServicePropertiesByGroupAsync(
              dnsServer?.ServerID ?? serverId, "DNS", ct);

          // Resolve secondary server IP from the linked service
          string secondaryServer = "";
          int? secondaryServiceId = null;
          if (props.TryGetValue("secondarydnsservices", out var secondaryIdStr)
              && int.TryParse(secondaryIdStr, out var secondaryId))
          {
              secondaryServiceId = secondaryId;
              var secondaryProps = await _repo.GetServicePropertiesAsync(secondaryId, ct);
              secondaryServer = secondaryProps.GetValueOrDefault("ServerName") ?? "";
          }

          // Parse semicolon-separated nameservers
          var nameServers = props.TryGetValue("nameservers", out var nsStr) && !string.IsNullOrEmpty(nsStr)
              ? nsStr.Split(';', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
              : [];

          return new DnsSettings
          {
              Server = dnsServer?.DnsServer ?? "",
              Username = dnsServer?.DnsUsername ?? "",
              Password = dnsServer?.DnsPassword ?? "",
              NameServers = nameServers,
              AllowZoneTransfers = props.GetValueOrDefault("allowzonetransfers") ?? "",
              SecondaryDnsServiceId = secondaryServiceId,
              ResponsiblePerson = props.GetValueOrDefault("responsibleperson") ?? "",
              RefreshInterval = int.TryParse(props.GetValueOrDefault("refreshinterval"), out var ri) ? ri : 3600,
              RetryDelay = int.TryParse(props.GetValueOrDefault("retrydelay"), out var rd) ? rd : 600,
              ExpireLimit = int.TryParse(props.GetValueOrDefault("expirelimit"), out var el) ? el : 1209600,
              MinimumTtl = int.TryParse(props.GetValueOrDefault("minimumttl"), out var mt) ? mt : 86400,
              RecordDefaultTtl = int.TryParse(props.GetValueOrDefault("RecordDefaultTTL"), out var rdt) ? rdt : 3600,
              RecordMinimumTtl = int.TryParse(props.GetValueOrDefault("RecordMinimumTTL"), out var rmt) ? rmt : 300,
              SecondaryServer = secondaryServer
          };
      }) ?? new DnsSettings();
  }
  ```

- [ ] **Step 5: Verify test passes**
  ```bash
  cd /c/claude/fusecp-enterprise
  dotnet test --filter "GetDnsSettingsAsync_LoadsNameServersFromServiceProperties" 2>&1 | tail -20
  ```

- [ ] **Step 6: Commit**
  ```bash
  cd /c/claude/fusecp-enterprise
  git add src/FuseCP.EnterpriseServer/Services/IServerSettingsService.cs \
          src/FuseCP.EnterpriseServer/Services/ServerSettingsService.cs
  git commit -m "feat: expand DnsSettings record with ServiceProperties fields

  Load nameservers, SOA params, zone transfer config, and secondary server
  from ServiceProperties (SolidCP-compatible DNS group properties).

  Co-Authored-By: Claude <noreply@anthropic.com>"
  ```

---

## Task 6: Add new methods to IDnsProvider and MsDnsProvider

**Agent:** `modular-builder`
**Model:** sonnet

**Files to Modify:**
- `src/FuseCP.Providers.DNS/IDnsProvider.cs:1-19`
- `src/FuseCP.Providers.DNS/MsDnsProvider.cs:1-318`

**Steps:**
- [ ] **Step 1: Write failing unit tests for new methods**
  Create/extend `tests/FuseCP.Providers.DNS.Tests/MsDnsProviderTests.cs`:

  ```csharp
  [Fact]
  public async Task CreateSecondaryZoneAsync_ExecutesCorrectPowerShellCommand()
  {
      // Arrange: mock executor to capture command, return success
      var executor = new Mock<IPowerShellExecutor>();
      executor.Setup(e => e.ExecuteCommandAsync(It.IsAny<PowerShellCommand>(), It.IsAny<CancellationToken>()))
              .ReturnsAsync(ProviderResult.Ok());
      var logger = NullLogger<MsDnsProvider>.Instance;
      var provider = new MsDnsProvider(executor.Object, logger);

      // Act
      var result = await provider.CreateSecondaryZoneAsync("test.lab.ergonet.pl", "172.31.251.101", "172.31.251.100");

      // Assert
      result.Success.Should().BeTrue();
      executor.Verify(e => e.ExecuteCommandAsync(
          It.Is<PowerShellCommand>(c =>
              c.CommandName == "Add-DnsServerSecondaryZone" &&
              c.Parameters.ContainsKey("Name") &&
              c.Parameters.ContainsKey("MasterServers")),
          It.IsAny<CancellationToken>()), Times.Once);
  }

  [Fact]
  public async Task SetZoneTransferAsync_ExecutesCorrectPowerShellCommand()
  {
      var executor = new Mock<IPowerShellExecutor>();
      executor.Setup(e => e.ExecuteCommandAsync(It.IsAny<PowerShellCommand>(), It.IsAny<CancellationToken>()))
              .ReturnsAsync(ProviderResult.Ok());
      var provider = new MsDnsProvider(executor.Object, NullLogger<MsDnsProvider>.Instance);

      var result = await provider.SetZoneTransferAsync("test.lab.ergonet.pl", ["172.31.251.100"], ["172.31.251.100"]);

      result.Success.Should().BeTrue();
      executor.Verify(e => e.ExecuteCommandAsync(
          It.Is<PowerShellCommand>(c => c.CommandName == "Set-DnsServerPrimaryZone"),
          It.IsAny<CancellationToken>()), Times.Once);
  }

  [Fact]
  public async Task AddNsRecordAsync_ExecutesAddDnsServerResourceRecord()
  {
      var executor = new Mock<IPowerShellExecutor>();
      executor.Setup(e => e.ExecuteCommandAsync(It.IsAny<PowerShellCommand>(), It.IsAny<CancellationToken>()))
              .ReturnsAsync(ProviderResult.Ok());
      var provider = new MsDnsProvider(executor.Object, NullLogger<MsDnsProvider>.Instance);

      var result = await provider.AddNsRecordAsync("test.lab.ergonet.pl", "dns2.lab.ergonet.pl");

      result.Success.Should().BeTrue();
  }

  [Fact]
  public async Task SetSoaAsync_ExecutesSetDnsServerResourceRecord()
  {
      var executor = new Mock<IPowerShellExecutor>();
      executor.Setup(e => e.ExecuteCommandAsync(It.IsAny<PowerShellCommand>(), It.IsAny<CancellationToken>()))
              .ReturnsAsync(ProviderResult.Ok());
      var provider = new MsDnsProvider(executor.Object, NullLogger<MsDnsProvider>.Instance);

      var result = await provider.SetSoaAsync("test.lab.ergonet.pl", "hostmaster.lab.ergonet.pl", 3600, 600, 1209600, 86400);

      result.Success.Should().BeTrue();
  }
  ```

- [ ] **Step 2: Verify tests fail**
  ```bash
  cd /c/claude/fusecp-enterprise
  dotnet build src/FuseCP.Providers.DNS/ 2>&1 | tail -10
  ```

- [ ] **Step 3: Add new method signatures to IDnsProvider**
  Modify `src/FuseCP.Providers.DNS/IDnsProvider.cs`, adding after line 17 (after `DeleteRecordAsync`):

  ```csharp
  // Secondary zone management
  Task<ProviderResult> CreateSecondaryZoneAsync(string zoneName, string masterServerIp, string? computerName = null, CancellationToken ct = default);
  Task<ProviderResult> DeleteSecondaryZoneAsync(string zoneName, string? computerName = null, CancellationToken ct = default);

  // Zone transfer and NS configuration
  Task<ProviderResult> SetZoneTransferAsync(string zoneName, string[] secondaryIps, string[]? notifyIps = null, CancellationToken ct = default);
  Task<ProviderResult> AddNsRecordAsync(string zoneName, string nameServer, CancellationToken ct = default);
  Task<ProviderResult> SetSoaAsync(string zoneName, string responsiblePerson, int refreshInterval, int retryDelay, int expireLimit, int minimumTtl, CancellationToken ct = default);
  ```

- [ ] **Step 4: Implement new methods in MsDnsProvider**
  Add the following methods to `src/FuseCP.Providers.DNS/MsDnsProvider.cs` after the `DeleteZoneAsync` method (after line 62):

  ```csharp
  public async Task<ProviderResult> CreateSecondaryZoneAsync(
      string zoneName, string masterServerIp, string? computerName = null, CancellationToken ct = default)
  {
      _logger.LogInformation("Creating secondary DNS zone {ZoneName} on {ComputerName} with master {Master}",
          zoneName, computerName ?? "localhost", masterServerIp);

      var parameters = new Dictionary<string, object?>
      {
          ["Name"] = zoneName,
          ["ZoneFile"] = $"{zoneName}.dns",
          ["MasterServers"] = masterServerIp
      };
      if (!string.IsNullOrEmpty(computerName))
          parameters["ComputerName"] = computerName;

      var command = new PowerShellCommand("Add-DnsServerSecondaryZone", parameters);
      return await _psExecutor.ExecuteCommandAsync(command, ct);
  }

  public async Task<ProviderResult> DeleteSecondaryZoneAsync(
      string zoneName, string? computerName = null, CancellationToken ct = default)
  {
      _logger.LogInformation("Deleting secondary DNS zone {ZoneName} on {ComputerName}",
          zoneName, computerName ?? "localhost");

      var parameters = new Dictionary<string, object?>
      {
          ["Name"] = zoneName,
          ["Force"] = true
      };
      if (!string.IsNullOrEmpty(computerName))
          parameters["ComputerName"] = computerName;

      var command = new PowerShellCommand("Remove-DnsServerZone", parameters);
      return await _psExecutor.ExecuteCommandAsync(command, ct);
  }

  public async Task<ProviderResult> SetZoneTransferAsync(
      string zoneName, string[] secondaryIps, string[]? notifyIps = null, CancellationToken ct = default)
  {
      _logger.LogInformation("Configuring zone transfer for {ZoneName}: secondaries={Secondaries}",
          zoneName, string.Join(",", secondaryIps));

      var parameters = new Dictionary<string, object?>
      {
          ["Name"] = zoneName,
          ["SecureSecondaries"] = "TransferToSecureServers",
          ["SecondaryServers"] = secondaryIps,
          ["Notify"] = "Notify"
      };
      if (notifyIps is { Length: > 0 })
          parameters["NotifyServers"] = notifyIps;

      var command = new PowerShellCommand("Set-DnsServerPrimaryZone", parameters);
      return await _psExecutor.ExecuteCommandAsync(command, ct);
  }

  public async Task<ProviderResult> AddNsRecordAsync(
      string zoneName, string nameServer, CancellationToken ct = default)
  {
      _logger.LogInformation("Adding NS record {NameServer} to zone {ZoneName}", nameServer, zoneName);

      // Ensure trailing dot for FQDN
      var fqdnNs = nameServer.EndsWith('.') ? nameServer : $"{nameServer}.";
      var command = new PowerShellCommand("Add-DnsServerResourceRecord", new Dictionary<string, object?>
      {
          ["ZoneName"] = zoneName,
          ["Name"] = "@",
          ["NS"] = true,
          ["NameServer"] = fqdnNs,
          ["TimeToLive"] = TimeSpan.FromSeconds(3600)
      });
      return await _psExecutor.ExecuteCommandAsync(command, ct);
  }

  public async Task<ProviderResult> SetSoaAsync(
      string zoneName, string responsiblePerson, int refreshInterval, int retryDelay,
      int expireLimit, int minimumTtl, CancellationToken ct = default)
  {
      _logger.LogInformation("Setting SOA for zone {ZoneName}: RP={RP}", zoneName, responsiblePerson);

      // SOA must be updated via Get/Set pattern since Set-DnsServerSOA doesn't exist in all versions
      var getCommand = new PowerShellCommand("Get-DnsServerResourceRecord", new Dictionary<string, object?>
      {
          ["ZoneName"] = zoneName,
          ["RRType"] = "SOA",
          ["Name"] = "@"
      });

      // Build a script block that does the clone-and-set pattern
      var scriptCommand = new PowerShellCommand(
          $@"$soa = Get-DnsServerResourceRecord -ZoneName '{zoneName}' -RRType SOA -Name '@';
             $newSoa = $soa.Clone();
             $newSoa.RecordData.ResponsiblePerson = '{responsiblePerson}.';
             $newSoa.RecordData.RefreshInterval   = [TimeSpan]::FromSeconds({refreshInterval});
             $newSoa.RecordData.RetryDelay        = [TimeSpan]::FromSeconds({retryDelay});
             $newSoa.RecordData.ExpireLimit       = [TimeSpan]::FromSeconds({expireLimit});
             $newSoa.RecordData.MinimumTimeToLive = [TimeSpan]::FromSeconds({minimumTtl});
             Set-DnsServerResourceRecord -ZoneName '{zoneName}' -OldInputObject $soa -NewInputObject $newSoa",
          new Dictionary<string, object?>(),
          isScript: true);

      return await _psExecutor.ExecuteCommandAsync(scriptCommand, ct);
  }
  ```

  Note: If `PowerShellCommand` does not support an `isScript` flag, use the existing pattern and pass the block as a script string with `Invoke-Expression` or adapt to the existing `IPowerShellExecutor` API per Task 0 findings.

- [ ] **Step 5: Verify tests pass**
  ```bash
  cd /c/claude/fusecp-enterprise
  dotnet test --filter "MsDnsProvider" 2>&1 | tail -20
  ```

- [ ] **Step 6: Commit**
  ```bash
  cd /c/claude/fusecp-enterprise
  git add src/FuseCP.Providers.DNS/IDnsProvider.cs \
          src/FuseCP.Providers.DNS/MsDnsProvider.cs
  git commit -m "feat: add secondary zone, NS record, SOA, and zone transfer methods to DNS provider

  New IDnsProvider methods: CreateSecondaryZoneAsync, DeleteSecondaryZoneAsync,
  SetZoneTransferAsync, AddNsRecordAsync, SetSoaAsync.
  MsDnsProvider implements all five using PowerShell DnsServer cmdlets.

  Co-Authored-By: Claude <noreply@anthropic.com>"
  ```

---

## Task 7: Enhance OrganizationProvisioningService for secondary zones

**Agent:** `modular-builder`
**Model:** sonnet

**Files to Modify:**
- `src/FuseCP.EnterpriseServer/Services/OrganizationProvisioningService.cs:173-230`

**Steps:**
- [ ] **Step 1: Write failing integration test**
  In the test project, add or extend `OrganizationProvisioningServiceTests.cs`. Write a test that mocks `IDnsProvider` and verifies the full enhanced flow:

  ```csharp
  [Fact]
  public async Task ProvisionOrganization_WithDns_CreatesSecondaryZoneAndNsRecords()
  {
      // Setup mocks to verify sequence:
      // 1. CreateZoneAsync called
      // 2. SetSoaAsync called
      // 3. AddNsRecordAsync called for each nameserver in DnsSettings.NameServers
      // 4. SetZoneTransferAsync called with secondary IP
      // 5. CreateSecondaryZoneAsync called with secondary server IP
      // (Actual mock setup depends on how the service is wired — adapt to constructor signature)
      // ...
      // Assert all 5 DNS provider methods were called in the provisioning flow
  }
  ```

- [ ] **Step 2: Verify test fails (compilation or assertion)**

- [ ] **Step 3: Enhance DNS provisioning block**
  Modify `src/FuseCP.EnterpriseServer/Services/OrganizationProvisioningService.cs`.

  Replace the DNS provisioning section (lines 173-230) with the enhanced version:

  ```csharp
  // 4. DNS provisioning
  string? dnsZone = null;
  if (request.DnsEnabled)
  {
      var dnsSettings = await _settingsSvc.GetDnsSettingsAsync(request.ServerId, ct);
      if (string.IsNullOrEmpty(dnsSettings.Server))
      {
          throw new InvalidOperationException(
              "DNS provisioning is enabled but no DNS server is configured. " +
              "Please configure DNS settings in Server configuration before enabling DNS for organizations.");
      }

      dnsZone = request.Domain ?? $"{slug}.{adSettings.TempDomain}";

      // 4a. Create primary zone
      var zoneResult = await _dnsProvider.CreateZoneAsync(dnsZone, ct);
      if (!zoneResult.Success)
          throw new InvalidOperationException($"DNS zone creation failed: {zoneResult.ErrorMessage}");

      created.Add(new CreatedResource("DNS Zone", async rollbackCt =>
      {
          await _dnsProvider.DeleteZoneAsync(dnsZone, rollbackCt);
          // Rollback secondary zone too
          if (!string.IsNullOrEmpty(dnsSettings.SecondaryServer))
              await _dnsProvider.DeleteSecondaryZoneAsync(dnsZone, dnsSettings.SecondaryServer, rollbackCt);
      }));
      _logger.LogInformation("Created DNS zone {Zone} for organization {Name}", dnsZone, request.Name);

      // 4b. Configure SOA from DnsSettings
      if (!string.IsNullOrEmpty(dnsSettings.ResponsiblePerson))
      {
          var soaResult = await _dnsProvider.SetSoaAsync(
              dnsZone,
              dnsSettings.ResponsiblePerson,
              dnsSettings.RefreshInterval,
              dnsSettings.RetryDelay,
              dnsSettings.ExpireLimit,
              dnsSettings.MinimumTtl,
              ct);
          if (!soaResult.Success)
              _logger.LogWarning("Failed to set SOA for zone {Zone}: {Error}", dnsZone, soaResult.ErrorMessage);
      }

      // 4c. Add configured NS records (Windows auto-adds the primary server's own hostname;
      //     we add our canonical dns1/dns2 hostnames from DnsSettings.NameServers)
      foreach (var ns in dnsSettings.NameServers)
      {
          if (string.IsNullOrWhiteSpace(ns)) continue;
          var nsResult = await _dnsProvider.AddNsRecordAsync(dnsZone, ns, ct);
          if (!nsResult.Success)
              _logger.LogWarning("Failed to add NS record {Ns} to zone {Zone}: {Error}", ns, dnsZone, nsResult.ErrorMessage);
      }

      // 4d. Enable zone transfers to secondary server
      if (!string.IsNullOrEmpty(dnsSettings.AllowZoneTransfers))
      {
          var transferIps = dnsSettings.AllowZoneTransfers
              .Split(';', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
          var ztResult = await _dnsProvider.SetZoneTransferAsync(dnsZone, transferIps, transferIps, ct);
          if (!ztResult.Success)
              _logger.LogWarning("Failed to configure zone transfer for {Zone}: {Error}", dnsZone, ztResult.ErrorMessage);
      }

      // 4e. Create secondary zone on secondary DNS server
      if (!string.IsNullOrEmpty(dnsSettings.SecondaryServer))
      {
          var secondaryResult = await _dnsProvider.CreateSecondaryZoneAsync(
              dnsZone, dnsSettings.Server, dnsSettings.SecondaryServer, ct);
          if (!secondaryResult.Success)
              _logger.LogWarning("Failed to create secondary zone for {Zone} on {Secondary}: {Error}",
                  dnsZone, dnsSettings.SecondaryServer, secondaryResult.ErrorMessage);
          else
              _logger.LogInformation("Created secondary zone {Zone} on {Secondary}", dnsZone, dnsSettings.SecondaryServer);
      }

      // 4f. Apply record templates from ResourceGroupDnsRecords (Exchange group = 12)
      var templates = await _dnsRepo.GetResourceGroupRecordsAsync(12, ct);
      var appliedCount = 0;

      foreach (var template in templates)
      {
          try
          {
              var recordName = ResolvePlaceholders(template.RecordName, dnsZone, "");
              var recordData = ResolvePlaceholders(template.RecordData, dnsZone, "");

              var recordRequest = new CreateDnsRecordRequest
              {
                  ZoneName = dnsZone,
                  Name = recordName,
                  RecordType = template.RecordType,
                  RecordData = recordData,
                  Ttl = dnsSettings.RecordDefaultTtl,
                  Priority = template.MXPriority
              };

              var recordResult = await _dnsProvider.CreateRecordAsync(recordRequest, ct);
              if (recordResult.Success)
                  appliedCount++;
              else
                  _logger.LogWarning("Failed to apply DNS template {Name} ({Type}) to zone {Zone}: {Error}",
                      template.RecordName, template.RecordType, dnsZone, recordResult.ErrorMessage);
          }
          catch (Exception ex)
          {
              _logger.LogWarning(ex, "Error applying DNS template {Name} to zone {Zone}", template.RecordName, dnsZone);
          }
      }

      results["DNS"] = $"Created ({dnsZone}, {appliedCount}/{templates.Count} templates applied, secondary: {dnsSettings.SecondaryServer})";
  }
  ```

- [ ] **Step 4: Verify tests pass**
  ```bash
  cd /c/claude/fusecp-enterprise
  dotnet test --filter "ProvisionOrganization_WithDns" 2>&1 | tail -20
  dotnet build 2>&1 | tail -10
  ```

- [ ] **Step 5: Commit**
  ```bash
  cd /c/claude/fusecp-enterprise
  git add src/FuseCP.EnterpriseServer/Services/OrganizationProvisioningService.cs
  git commit -m "feat: enhance DNS provisioning to create secondary zones, NS records, and SOA

  After creating the primary zone, the provisioning service now:
  - Sets SOA parameters from DnsSettings (responsible person, TTLs)
  - Adds NS records from configured nameservers
  - Enables zone transfers to secondary server
  - Creates secondary zone on secondary DNS server with rollback support

  Co-Authored-By: Claude <noreply@anthropic.com>"
  ```

---

## Task 8: DNS Settings API endpoints

**Agent:** `modular-builder`
**Model:** sonnet

**Files to Modify:**
- `src/FuseCP.EnterpriseServer/Endpoints/DomainDnsEndpoints.cs` (add new static class at end)
- `src/FuseCP.EnterpriseServer/Program.cs` (register new endpoint group)

**Files to Modify (repository layer):**
- `src/FuseCP.Database/Repositories/SolidCP/IServerSettingsRepository.cs:50-66`
- `src/FuseCP.Database/Repositories/SolidCP/ServerSettingsRepository.cs` (add `UpdateDnsSettingsAsync`)

**Steps:**
- [ ] **Step 1: Add UpdateDnsSettingsAsync to IServerSettingsRepository**
  Modify `src/FuseCP.Database/Repositories/SolidCP/IServerSettingsRepository.cs`, adding after line 56:

  ```csharp
  Task UpdateDnsSettingsAsync(int serviceId, Dictionary<string, string> properties, CancellationToken ct = default);
  ```

- [ ] **Step 2: Implement UpdateDnsSettingsAsync in ServerSettingsRepository**
  In `src/FuseCP.Database/Repositories/SolidCP/ServerSettingsRepository.cs`, add after the existing `SetServicePropertyAsync` method:

  ```csharp
  public async Task UpdateDnsSettingsAsync(int serviceId, Dictionary<string, string> properties, CancellationToken ct = default)
  {
      foreach (var (name, value) in properties)
          await SetServicePropertyAsync(serviceId, name, value, ct);
  }
  ```

- [ ] **Step 3: Add IServerSettingsService method for updating DNS settings**
  Modify `src/FuseCP.EnterpriseServer/Services/IServerSettingsService.cs`, adding to the interface:

  ```csharp
  Task UpdateDnsSettingsAsync(UpdateDnsSettingsRequest request, CancellationToken ct = default);
  ```

  Add the request record:

  ```csharp
  public sealed record UpdateDnsSettingsRequest
  {
      public string[]? NameServers { get; init; }
      public string? AllowZoneTransfers { get; init; }
      public string? ResponsiblePerson { get; init; }
      public int? RefreshInterval { get; init; }
      public int? RetryDelay { get; init; }
      public int? ExpireLimit { get; init; }
      public int? MinimumTtl { get; init; }
      public int? RecordDefaultTtl { get; init; }
      public int? RecordMinimumTtl { get; init; }
  }
  ```

- [ ] **Step 4: Implement UpdateDnsSettingsAsync in ServerSettingsService**
  Add to `src/FuseCP.EnterpriseServer/Services/ServerSettingsService.cs`:

  ```csharp
  public async Task UpdateDnsSettingsAsync(UpdateDnsSettingsRequest request, CancellationToken ct = default)
  {
      // Get current DNS service ID via ServiceProperties lookup
      // For now, use ServiceID=2 (primary DNS) — the primary service is always ID 2 in lab
      const int primaryDnsServiceId = 2;

      var props = new Dictionary<string, string>();
      if (request.NameServers is not null)
          props["nameservers"] = string.Join(";", request.NameServers);
      if (request.AllowZoneTransfers is not null)
          props["allowzonetransfers"] = request.AllowZoneTransfers;
      if (request.ResponsiblePerson is not null)
          props["responsibleperson"] = request.ResponsiblePerson;
      if (request.RefreshInterval.HasValue)
          props["refreshinterval"] = request.RefreshInterval.Value.ToString();
      if (request.RetryDelay.HasValue)
          props["retrydelay"] = request.RetryDelay.Value.ToString();
      if (request.ExpireLimit.HasValue)
          props["expirelimit"] = request.ExpireLimit.Value.ToString();
      if (request.MinimumTtl.HasValue)
          props["minimumttl"] = request.MinimumTtl.Value.ToString();
      if (request.RecordDefaultTtl.HasValue)
          props["RecordDefaultTTL"] = request.RecordDefaultTtl.Value.ToString();
      if (request.RecordMinimumTtl.HasValue)
          props["RecordMinimumTTL"] = request.RecordMinimumTtl.Value.ToString();

      await _repo.UpdateDnsSettingsAsync(primaryDnsServiceId, props, ct);
      await InvalidateCacheAsync();
  }
  ```

- [ ] **Step 5: Create DnsSettingsEndpoints**
  Add a new static class `DnsSettingsEndpoints` at the end of `src/FuseCP.EnterpriseServer/Endpoints/DomainDnsEndpoints.cs` (after line 215):

  ```csharp
  public static class DnsSettingsEndpoints
  {
      public static void MapDnsSettingsEndpoints(this WebApplication app)
      {
          var group = app.MapGroup("/api/dns/settings")
              .WithTags("DNS Settings")
              .RequireAuthorization("PlatformAdmin");

          group.MapGet("/", GetDnsSettings);
          group.MapPut("/", UpdateDnsSettings);
      }

      private static async Task<IResult> GetDnsSettings(
          IServerSettingsService settingsSvc,
          CancellationToken ct)
      {
          var settings = await settingsSvc.GetDnsSettingsAsync(ct: ct);
          return Results.Ok(new
          {
              server = settings.Server,
              nameServers = settings.NameServers,
              allowZoneTransfers = settings.AllowZoneTransfers,
              secondaryDnsServiceId = settings.SecondaryDnsServiceId,
              secondaryServer = settings.SecondaryServer,
              responsiblePerson = settings.ResponsiblePerson,
              refreshInterval = settings.RefreshInterval,
              retryDelay = settings.RetryDelay,
              expireLimit = settings.ExpireLimit,
              minimumTtl = settings.MinimumTtl,
              recordDefaultTtl = settings.RecordDefaultTtl,
              recordMinimumTtl = settings.RecordMinimumTtl
          });
      }

      private static async Task<IResult> UpdateDnsSettings(
          [FromBody] UpdateDnsSettingsRequest request,
          IServerSettingsService settingsSvc,
          CancellationToken ct)
      {
          await settingsSvc.UpdateDnsSettingsAsync(request, ct);
          var updated = await settingsSvc.GetDnsSettingsAsync(ct: ct);
          return Results.Ok(new
          {
              message = "DNS settings updated",
              nameServers = updated.NameServers,
              responsiblePerson = updated.ResponsiblePerson
          });
      }
  }
  ```

- [ ] **Step 6: Register in Program.cs**
  In `src/FuseCP.EnterpriseServer/Program.cs`, add the registration call alongside the existing `MapDomainDnsEndpoints()` line:

  ```csharp
  app.MapDnsSettingsEndpoints();
  ```

- [ ] **Step 7: Build and verify**
  ```bash
  cd /c/claude/fusecp-enterprise
  dotnet build src/FuseCP.EnterpriseServer/ 2>&1 | tail -15
  ```

- [ ] **Step 8: Commit**
  ```bash
  cd /c/claude/fusecp-enterprise
  git add src/FuseCP.EnterpriseServer/Endpoints/DomainDnsEndpoints.cs \
          src/FuseCP.EnterpriseServer/Services/IServerSettingsService.cs \
          src/FuseCP.EnterpriseServer/Services/ServerSettingsService.cs \
          src/FuseCP.Database/Repositories/SolidCP/IServerSettingsRepository.cs \
          src/FuseCP.Database/Repositories/SolidCP/ServerSettingsRepository.cs \
          src/FuseCP.EnterpriseServer/Program.cs
  git commit -m "feat: add GET/PUT /api/dns/settings admin endpoints

  PlatformAdmin-only endpoints to read and update DNS ServiceProperties
  (nameservers, SOA params, zone transfer config). Cache invalidated on PUT.

  Co-Authored-By: Claude <noreply@anthropic.com>"
  ```

---

## Task 9: Portal DNS Settings admin page (translations only — UI deferred)

**Agent:** `database-architect`
**Model:** sonnet

**Files to Create:**
- `src/FuseCP.Database/Migrations/121_AddDnsSettingsTranslations.sql`

**Steps:**
- [ ] **Step 1: Create translations migration 121**
  Create `src/FuseCP.Database/Migrations/121_AddDnsSettingsTranslations.sql`:

```sql
-- Migration 121: Add DNS Settings page translations (EN + PL)
-- Keys for the DNS Settings admin page (portal UI deferred to future task)

-- English translations
INSERT INTO Translations (LanguageCode, [Key], Value) VALUES
('en', 'dns.settings.title',              'DNS Settings'),
('en', 'dns.settings.primaryServer',      'Primary DNS Server'),
('en', 'dns.settings.secondaryServer',    'Secondary DNS Server'),
('en', 'dns.settings.nameservers',        'Nameservers'),
('en', 'dns.settings.nameserversHint',    'Semicolon-separated hostnames (e.g. dns1.example.com;dns2.example.com)'),
('en', 'dns.settings.allowZoneTransfers', 'Allow Zone Transfers (IP)'),
('en', 'dns.settings.responsiblePerson',  'SOA Responsible Person'),
('en', 'dns.settings.refreshInterval',    'SOA Refresh Interval (seconds)'),
('en', 'dns.settings.retryDelay',         'SOA Retry Delay (seconds)'),
('en', 'dns.settings.expireLimit',        'SOA Expire Limit (seconds)'),
('en', 'dns.settings.minimumTtl',         'SOA Minimum TTL (seconds)'),
('en', 'dns.settings.recordDefaultTtl',   'Record Default TTL (seconds)'),
('en', 'dns.settings.recordMinimumTtl',   'Record Minimum TTL (seconds)'),
('en', 'dns.settings.saved',              'DNS settings saved successfully'),
('en', 'dns.settings.saveError',          'Failed to save DNS settings')
ON CONFLICT ([Key], LanguageCode) DO NOTHING;

-- Polish translations
INSERT INTO Translations (LanguageCode, [Key], Value) VALUES
('pl', 'dns.settings.title',              'Ustawienia DNS'),
('pl', 'dns.settings.primaryServer',      'Główny serwer DNS'),
('pl', 'dns.settings.secondaryServer',    'Pomocniczy serwer DNS'),
('pl', 'dns.settings.nameservers',        'Serwery nazw (NS)'),
('pl', 'dns.settings.nameserversHint',    'Nazwy oddzielone średnikiem (np. dns1.example.com;dns2.example.com)'),
('pl', 'dns.settings.allowZoneTransfers', 'Zezwól na transfer stref (IP)'),
('pl', 'dns.settings.responsiblePerson',  'Osoba odpowiedzialna (SOA)'),
('pl', 'dns.settings.refreshInterval',    'Interwał odświeżania SOA (sekundy)'),
('pl', 'dns.settings.retryDelay',         'Opóźnienie ponowień SOA (sekundy)'),
('pl', 'dns.settings.expireLimit',        'Limit wygaśnięcia SOA (sekundy)'),
('pl', 'dns.settings.minimumTtl',         'Minimalny TTL SOA (sekundy)'),
('pl', 'dns.settings.recordDefaultTtl',   'Domyślny TTL rekordu (sekundy)'),
('pl', 'dns.settings.recordMinimumTtl',   'Minimalny TTL rekordu (sekundy)'),
('pl', 'dns.settings.saved',              'Ustawienia DNS zostały zapisane'),
('pl', 'dns.settings.saveError',          'Nie udało się zapisać ustawień DNS')
ON CONFLICT ([Key], LanguageCode) DO NOTHING;
```

- [ ] **Step 2: Commit**
  ```bash
  cd /c/claude/fusecp-enterprise
  git add src/FuseCP.Database/Migrations/121_AddDnsSettingsTranslations.sql
  git commit -m "db: migration 121 — add DNS Settings page translations (EN + PL)

  Co-Authored-By: Claude <noreply@anthropic.com>"
  ```

---

## Task 10: Spec review and code quality review

**Agent:** `spec-reviewer` then `code-quality-reviewer`
**Model:** haiku (spec-reviewer), sonnet (code-quality-reviewer)

**Steps:**
- [ ] **Step 1: Spec compliance review**
  Dispatch `spec-reviewer` with the spec file and a list of all changed files. Verify:
  - All 5 spec sections implemented: WinRM, glue/firewall, existing zones, DB migration, code changes
  - `DnsSettings` record has all 10+ fields from spec Section 2.2
  - `IDnsProvider` has all 5 new methods from spec Section 2.3
  - `OrganizationProvisioningService` runs all 5 post-zone steps (SOA, remove auto-NS, add NS, zone transfer, secondary zone)
  - API endpoints `GET/PUT /api/dns/settings` exist and are PlatformAdmin-only
  - Migration 120 seeds all required properties with correct SolidCP-compatible names

- [ ] **Step 2: Code quality review**
  Dispatch `code-quality-reviewer` with the changed C# files. Verify:
  - `DnsSettings` is `sealed record` with correct default values
  - Cache key pattern follows existing conventions (`$"dns-settings-{serverId}"`)
  - `SetSoaAsync` script injection safety (zone names are validated before reaching this method)
  - `UpdateDnsSettingsAsync` uses PATCH-style (only updates provided fields, not full overwrite)
  - All new `IDnsProvider` methods follow existing `Task<ProviderResult>` return pattern

- [ ] **Step 3: Fix any issues found by reviewers**

---

## Task 11: End-to-end verification

**Agent:** `test-coverage`
**Model:** haiku

**Steps:**
- [ ] **Step 1: Run full test suite**
  ```bash
  cd /c/claude/fusecp-enterprise
  dotnet test 2>&1 | tail -30
  ```

- [ ] **Step 2: Build release configuration**
  ```bash
  cd /c/claude/fusecp-enterprise
  dotnet build --configuration Release 2>&1 | tail -15
  ```

- [ ] **Step 3: Manual DNS verification commands**
  After deploying to lab, run from any machine:
  ```powershell
  # Verify primary DNS serves the zone
  Resolve-DnsName tenanta.lab.ergonet.pl -Server 172.31.251.101

  # Verify secondary DNS serves the zone (after transfer)
  Resolve-DnsName tenanta.lab.ergonet.pl -Server 172.31.251.100

  # Verify NS records include both dns1 and dns2
  Resolve-DnsName tenanta.lab.ergonet.pl -Server 172.31.251.101 -Type NS

  # Verify SOA responsible person
  Resolve-DnsName tenanta.lab.ergonet.pl -Server 172.31.251.101 -Type SOA

  # Verify glue records
  Resolve-DnsName dns1.lab.ergonet.pl -Server 172.31.251.101
  Resolve-DnsName dns2.lab.ergonet.pl -Server 172.31.251.101
  ```

- [ ] **Step 4: API smoke test**
  ```bash
  # GET DNS settings (verify all new fields populated)
  curl -sk -H "X-Api-Key: fusecp-admin-key-2026" \
    "http://localhost:5010/api/dns/settings" | python -m json.tool

  # PUT update DNS settings
  curl -sk -X PUT \
    -H "X-Api-Key: fusecp-admin-key-2026" \
    -H "Content-Type: application/json" \
    -d '{"responsiblePerson":"hostmaster.lab.ergonet.pl","refreshInterval":3600}' \
    "http://localhost:5010/api/dns/settings" | python -m json.tool
  ```

- [ ] **Step 5: Provision a new test organization and verify**
  Through the portal or API, provision a new test organization with DNS enabled. Verify:
  - Primary zone created on FINALTEST
  - Secondary zone created on DEV
  - Both NS records (dns1 + dns2) present on the primary zone
  - SOA has correct responsible person
  - Zone transfer succeeds

- [ ] **Step 6: Test rollback**
  Delete the test organization. Verify both primary and secondary zones are removed.

---

## Task 12: Cleanup

**Agent:** `post-task-cleanup`
**Model:** haiku

**Steps:**
- [ ] **Step 1: Lint and format check**
  ```bash
  cd /c/claude/fusecp-enterprise
  make check 2>&1 | tail -20
  ```

- [ ] **Step 2: Remove any debug logging or TODO comments added during implementation**

- [ ] **Step 3: Verify no dead code introduced** (unused using directives, unreachable branches)

- [ ] **Step 4: Final commit (cleanup only)**
  ```bash
  cd /c/claude/fusecp-enterprise
  git add -p
  git commit -m "chore: post-task cleanup for DNS primary/secondary feature

  Co-Authored-By: Claude <noreply@anthropic.com>"
  ```

- [ ] **Step 5: Create PR**
  ```bash
  cd /c/claude/fusecp-enterprise
  tea pr create \
    --title "feat: DNS primary/secondary setup with auto-provisioning" \
    --description "Implements DNS primary/secondary redundancy. Infrastructure scripts for WinRM, glue records, firewall, and existing zone fixes. DB migrations 120-121. Expanded DnsSettings, 5 new IDnsProvider methods, enhanced provisioning flow, GET/PUT /api/dns/settings endpoints." \
    --base main
  ```
