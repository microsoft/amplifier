# Exchange Server 2019 Administration Reference

> Quick reference for Exchange 2019/SE PowerShell administration. Optimized for `/recall exchange <topic>` searches.
> For deep dives: `mcp__context7__query-docs(libraryId='/websites/learn_microsoft_en-us_exchange', query='<topic>')`
>
> All commands run from Exchange Management Shell (EMS) unless noted.
> Connect remotely: `$s = New-PSSession -ConfigurationName Microsoft.Exchange -ConnectionUri http://EXCHANGELAB/PowerShell/ -Authentication Kerberos; Import-PSSession $s`

---

## Lab Environment

| Role | Hostname | IP | Notes |
|------|----------|----|-------|
| Mailbox node 1 | EXCHANGELAB | 172.31.251.103 | Primary DAG member |
| Mailbox node 2 | EXCHANGELAB2 | 172.31.251.104 | Secondary DAG member |
| DAG cluster VIP | FuseCP-DAG | 172.31.251.110 | Failover cluster name |
| AD / DNS / FSW | FINALTEST | 172.31.251.101 | File share witness host |
| Management workstation | DEV | 172.31.251.100 | Run EMS sessions from here |

**Connection method:** CredSSP via WinRM from DEV (172.31.251.100)
**Credentials:** `ERGOLAB\Administrator`
**DAG name:** Confirm with `Get-DatabaseAvailabilityGroup`
**Databases:** Confirm with `Get-MailboxDatabase | Select Name, Server`

---

## DAG & Database Management

### Key Cmdlets

| Cmdlet | Purpose |
|--------|---------|
| `Get-DatabaseAvailabilityGroup` | Show DAG config, members, witness |
| `Get-MailboxDatabase` | List databases and active server |
| `Get-MailboxDatabaseCopyStatus` | Replication health per copy |
| `Add-MailboxDatabaseCopy` | Add a new passive copy to a DAG member |
| `Move-ActiveMailboxDatabase` | Switchover active database to another node |
| `Update-MailboxDatabaseCopy` | Reseed a database copy or content index |
| `Remove-MailboxDatabaseCopy` | Remove a passive copy |
| `Add-DatabaseAvailabilityGroupServer` | Add server to DAG |
| `New-DatabaseAvailabilityGroup` | Create a new DAG |

### Get-MailboxDatabaseCopyStatus

```powershell
# All copies on local server
Get-MailboxDatabaseCopyStatus -Server $env:COMPUTERNAME | Format-Table Name,Status,CopyQueueLength,ReplayQueueLength,ContentIndexState -Auto

# Specific database
Get-MailboxDatabaseCopyStatus -Identity "DB01"

# Content index health across all copies
Get-MailboxDatabaseCopyStatus -Server $env:COMPUTERNAME | Format-Table Name,Status,ContentIndex* -Auto
```

**Key status values:** `Healthy`, `Mounted`, `Disconnected`, `Failed`, `FailedAndSuspended`, `Seeding`
**Gotcha:** `CopyQueueLength > 10` warrants investigation; `> 100` is a problem.

### Move-ActiveMailboxDatabase

Performs a **switchover** (graceful) or **failover** (forced) of the active database copy.

```powershell
# Graceful switchover to specific server
Move-ActiveMailboxDatabase "DB01" -ActivateOnServer "EXCHANGELAB2"

# Move all active databases off a server (before maintenance)
Move-ActiveMailboxDatabase -Server EXCHANGELAB -ActivateOnServer EXCHANGELAB2

# Emergency — skip all health checks
Move-ActiveMailboxDatabase "DB01" -ActivateOnServer "EXCHANGELAB2" -SkipHealthChecks

# Skip individual checks selectively
Move-ActiveMailboxDatabase "DB01" -ActivateOnServer "EXCHANGELAB2" -SkipActiveCopyChecks -SkipLagChecks
```

**Available skip parameters:** `-SkipHealthChecks`, `-SkipActiveCopyChecks`, `-SkipLagChecks`, `-SkipClientExperienceChecks`
**Gotcha:** Use skip flags only in emergencies — they bypass safety gates.

### Add-MailboxDatabaseCopy

```powershell
# Add copy with immediate seeding
Add-MailboxDatabaseCopy -Identity "DB01" -MailboxServer "EXCHANGELAB2"

# Add copy but seed later (for large DBs over slow links)
Add-MailboxDatabaseCopy -Identity "DB01" -MailboxServer "EXCHANGELAB2" -SeedingPostponed

# Manually trigger seeding after postponed add
Update-MailboxDatabaseCopy -Identity "DB01\EXCHANGELAB2"
```

### Update-MailboxDatabaseCopy (Reseed)

```powershell
# Full reseed of a copy
Update-MailboxDatabaseCopy -Identity "DB01\EXCHANGELAB2"

# Reseed only content index catalog (when DB is healthy, index is broken)
Update-MailboxDatabaseCopy -Identity "DB01\EXCHANGELAB2" -CatalogOnly

# Reseed catalog from specific source
Update-MailboxDatabaseCopy -Identity "DB01\EXCHANGELAB2" -SourceServer "EXCHANGELAB" -CatalogOnly
```

**Gotcha:** Reseeding a full database suspends replication first — replication auto-resumes on completion.

### DAG Membership

```powershell
# Create new DAG
New-DatabaseAvailabilityGroup -Name "DAG01" -WitnessServer "FINALTEST" -WitnessDirectory "C:\DAGWitness\DAG01" -DatabaseAvailabilityGroupIpAddresses 172.31.251.110

# Add server to existing DAG
Add-DatabaseAvailabilityGroupServer -Identity "DAG01" -MailboxServer "EXCHANGELAB"
Add-DatabaseAvailabilityGroupServer -Identity "DAG01" -MailboxServer "EXCHANGELAB2"

# View DAG status
Get-DatabaseAvailabilityGroup -Status | Format-List Name,Servers,WitnessServer,OperationalServers
```

---

## Mail Flow & Transport

### Key Cmdlets

| Cmdlet | Purpose |
|--------|---------|
| `Get-Queue` | View transport queues and status |
| `Get-Message` | Inspect messages in a queue |
| `Retry-Queue` | Force immediate retry on stuck queues |
| `Suspend-Queue` | Pause queue delivery |
| `Resume-Queue` | Resume a suspended queue |
| `Remove-Message` | Delete messages from queues |
| `Test-Mailflow` | End-to-end mail flow test |
| `Get-TransportService` | Transport service status |
| `Redirect-Message` | Drain messages to another server |

### Get-Queue

```powershell
# All queues on local server
Get-Queue

# Queues with messages stuck in Retry
Get-Queue -Filter "Status -eq 'Retry'"

# High-volume queues
Get-Queue -Filter "(Status -eq 'Retry') -and (MessageCount -gt 100)"

# Queues to a specific domain
Get-Queue -Filter "NextHopDomain -like 'contoso.com*'"

# Smart host connector queues
Get-Queue -Include SmartHostConnectorDelivery

# Check retry timing on a specific queue
Get-Queue -Identity "EXCHANGELAB\contoso.com" | Format-Table -Auto Identity,Status,LastRetryTime,NextRetryTime
```

**Queue Identity format:** `<ServerName>\<NextHopDomain>` (e.g., `EXCHANGELAB\contoso.com`)

### Queue Operations

```powershell
# Force retry on all Retry queues
Get-Queue -Filter "Status -eq 'Retry'" | Retry-Queue

# Retry specific queue
Retry-Queue -Identity "EXCHANGELAB\contoso.com"

# Suspend delivery (stop outbound, messages stay in queue)
Suspend-Queue -Identity "EXCHANGELAB\contoso.com"

# Resume suspended queue
Resume-Queue -Identity "EXCHANGELAB\contoso.com"

# Delete all messages in a queue with NDR
Get-Message -Queue "EXCHANGELAB\contoso.com" | Remove-Message -WithNDR $true

# Delete without NDR (use in spam scenarios)
Get-Message -Queue "EXCHANGELAB\contoso.com" | Remove-Message -WithNDR $false
```

### Test-Mailflow

```powershell
# Basic local loopback test
Test-Mailflow

# Test to external recipient
Test-Mailflow -TargetEmailAddress "testuser@contoso.com"

# Test between two Exchange servers
Test-Mailflow -TargetMailboxServer EXCHANGELAB2
```

### Drain Transport Before Maintenance

```powershell
# Redirect messages to another server, then drain
Redirect-Message -Server EXCHANGELAB -Target EXCHANGELAB2.ergolab.local

# Restart transport to apply component state changes
Restart-Service MSExchangeTransport
```

---

## Certificate Management

### Key Cmdlets

| Cmdlet | Purpose |
|--------|---------|
| `Get-ExchangeCertificate` | List certificates on Exchange server |
| `New-ExchangeCertificate` | Create new cert or renewal request |
| `Enable-ExchangeCertificate` | Bind certificate to Exchange services |
| `Import-ExchangeCertificate` | Import CA-issued certificate |
| `Remove-ExchangeCertificate` | Remove certificate |

### Get-ExchangeCertificate

```powershell
# All certificates on local server
Get-ExchangeCertificate | Format-Table Thumbprint,Subject,NotAfter,Services -Auto

# Certificate on remote server
Get-ExchangeCertificate -Server EXCHANGELAB2 | Format-Table Thumbprint,Subject,NotAfter,Services -Auto

# Find expiring within 60 days
Get-ExchangeCertificate | Where-Object { $_.NotAfter -lt (Get-Date).AddDays(60) } | Format-Table Thumbprint,Subject,NotAfter -Auto
```

### Renew Self-Signed Certificate

```powershell
# Renew by thumbprint (keeps same key)
Get-ExchangeCertificate -Thumbprint "BC37CBE2E59566BFF7D01FEAC9B6517841475F2D" | New-ExchangeCertificate -RenewSameKey -Force

# Renew with exportable private key
Get-ExchangeCertificate -Thumbprint "BC37CBE2E59566BFF7D01FEAC9B6517841475F2D" | New-ExchangeCertificate -Force -PrivateKeyExportable $true
```

### Renew CA-Issued Certificate (CSR workflow)

```powershell
# Step 1: Generate renewal request file
$txtrequest = Get-ExchangeCertificate -Thumbprint "5DB9879E38E36BCB60B761E29794392B23D1C054" | New-ExchangeCertificate -GenerateRequest
[System.IO.File]::WriteAllBytes('C:\CertRequests\RenewalRequest.req', [System.Text.Encoding]::Unicode.GetBytes($txtrequest))

# Step 2: Submit .req to CA, receive .cer file

# Step 3: Import the issued certificate
Import-ExchangeCertificate -FileData ([System.IO.File]::ReadAllBytes('C:\CertRequests\IssuedCert.cer')) -PrivateKeyExportable $true

# Step 4: Enable on services (IIS = HTTPS, SMTP = TLS, POP, IMAP)
Enable-ExchangeCertificate -Thumbprint "NEW_THUMBPRINT" -Services IIS,SMTP,POP,IMAP -Force
```

**Gotcha:** After `Enable-ExchangeCertificate`, IIS services restart automatically. Plan for brief outage.
**Gotcha:** `-Force` suppresses the prompt asking to overwrite existing service bindings.

---

## Maintenance Mode

Full maintenance mode procedure for a DAG member. Always do this before patching, hardware work, or reboots.

### Enter Maintenance Mode (EXCHANGELAB)

```powershell
$server = "EXCHANGELAB"
$targetServer = "EXCHANGELAB2"

# Step 1: Drain HubTransport (stop accepting new messages)
Set-ServerComponentState $server -Component HubTransport -State Draining -Requester Maintenance
Restart-Service MSExchangeTransport

# Step 2: Drain UM calls (if Unified Messaging is in use)
Set-ServerComponentState $server -Component UMCallRouter -State Draining -Requester Maintenance

# Step 3: Redirect messages to another server
Redirect-Message -Server $server -Target "$targetServer.ergolab.local"

# Step 4: Suspend cluster node (pause DAG participation)
Suspend-ClusterNode $server

# Step 5: Move all active databases off this node
Set-MailboxServer $server -DatabaseCopyActivationDisabledAndMoveNow $True
Set-MailboxServer $server -DatabaseCopyAutoActivationPolicy Blocked

# Step 6: Set server-wide offline (marks server as in maintenance)
Set-ServerComponentState $server -Component ServerWideOffline -State Inactive -Requester Maintenance
```

### Verify Maintenance Mode Entered

```powershell
$server = "EXCHANGELAB"

# All components should show Inactive or Draining
Get-ServerComponentState $server | Format-Table Component,State -Autosize

# Should show DatabaseCopyAutoActivationPolicy = Blocked
Get-MailboxServer $server | Format-List DatabaseCopyAutoActivationPolicy

# Cluster node should be Paused
Get-ClusterNode $server | Format-List

# Confirm no active databases on this server
Get-MailboxDatabaseCopyStatus -Server $server | Where-Object {$_.Status -eq "Mounted"}

# Confirm transport queues are draining
Get-Queue
```

### Exit Maintenance Mode (return server to production)

```powershell
$server = "EXCHANGELAB"

# Step 1: Bring server-wide online
Set-ServerComponentState $server -Component ServerWideOffline -State Active -Requester Maintenance

# Step 2: Resume UM (if applicable)
Set-ServerComponentState $server -Component UMCallRouter -State Active -Requester Maintenance

# Step 3: Resume cluster node participation
Resume-ClusterNode $server

# Step 4: Re-enable database auto-activation
Set-MailboxServer $server -DatabaseCopyAutoActivationPolicy Unrestricted
Set-MailboxServer $server -DatabaseCopyActivationDisabledAndMoveNow $False

# Step 5: Resume all database copies
Get-MailboxDatabaseCopyStatus -Server $server | Resume-MailboxDatabaseCopy

# Step 6: Resume HubTransport
Set-ServerComponentState $server -Component HubTransport -State Active -Requester Maintenance
Restart-Service MSExchangeTransport
```

**Gotcha:** After exiting, run `Get-ServerComponentState $server | Format-Table Component,State -Auto` — all components should be `Active`.

---

## Server Health & Components

### Key Cmdlets

| Cmdlet | Purpose |
|--------|---------|
| `Test-ServiceHealth` | Quick check that all required services are running |
| `Get-HealthReport` | Summarized health set status |
| `Get-ServerHealth` | Raw health monitor data |
| `Get-ServerComponentState` | Component operational state |
| `Set-ServerComponentState` | Change component state |

### Test-ServiceHealth

```powershell
# Check all services on local server
Test-ServiceHealth

# Check specific server
Test-ServiceHealth -Server EXCHANGELAB2
```

Returns list of services that should be running vs. currently running. Any "Services not running" entries require immediate attention.

### Get-HealthReport

```powershell
# Summary of all health sets on a server
Get-HealthReport -Identity EXCHANGELAB | Format-Table Server,HealthSetName,AlertValue,ServerComponent -Auto

# Show only unhealthy sets
Get-HealthReport -Identity EXCHANGELAB | Where-Object {$_.AlertValue -ne "Healthy"} | Format-Table -Auto
```

**AlertValue options:** `Healthy`, `Warning`, `Unhealthy`, `Disabled`

### Get-ServerHealth (Detailed Monitors)

```powershell
# All monitors on a server
Get-ServerHealth -Server EXCHANGELAB | Format-Table Name,AlertValue,HealthSetName -Auto

# Monitors for a specific health set
Get-ServerHealth -HealthSet "MSExchangeRPC" -Server EXCHANGELAB | Format-Table Name,AlertValue -Auto

# IMAP-related monitors
Get-ServerHealth EXCHANGELAB.ergolab.local | Where-Object {$_.HealthSetName -like "IMAP*"}

# Show only unhealthy monitors
Get-ServerHealth -Server EXCHANGELAB | Where-Object {$_.AlertValue -eq "Unhealthy"}
```

### Get-ServerComponentState

```powershell
# All components on local server
Get-ServerComponentState EXCHANGELAB | Format-Table Component,State -Autosize

# Specific component
Get-ServerComponentState EXCHANGELAB -Component HubTransport

# Check both nodes at once
"EXCHANGELAB","EXCHANGELAB2" | ForEach-Object { Get-ServerComponentState $_ | Format-Table Component,State -AutoSize }
```

**Key components:** `ServerWideOffline`, `HubTransport`, `FrontendTransport`, `Monitoring`, `RecoveryActionsEnabled`, `UMCallRouter`

---

## Mailbox Operations

### Key Cmdlets

| Cmdlet | Purpose |
|--------|---------|
| `Get-MailboxStatistics` | Size, item count, last logon |
| `Get-MailboxFolderStatistics` | Per-folder breakdown |
| `Get-Mailbox` | Mailbox config including quotas |
| `Set-Mailbox` | Configure mailbox settings, quotas |
| `New-MoveRequest` | Initiate mailbox move/migration |
| `Get-MoveRequest` | Check move request status |
| `Remove-MoveRequest` | Clean up completed move requests |

### Get-MailboxStatistics

```powershell
# Single mailbox
Get-MailboxStatistics -Identity "user@ergolab.local" | Format-List DisplayName,TotalItemSize,ItemCount,LastLogonTime

# All mailboxes, sorted by size
Get-MailboxStatistics -Server EXCHANGELAB | Sort-Object TotalItemSize -Descending | Select-Object -First 20 DisplayName,TotalItemSize,ItemCount

# Archive mailbox statistics
Get-MailboxStatistics "user@ergolab.local" -Archive | Format-List DisplayName,TotalItemSize,ItemCount
```

### Get-MailboxFolderStatistics

```powershell
# All folders for a user
Get-MailboxFolderStatistics -Identity "user@ergolab.local" | Format-Table FolderPath,ItemsInFolder,FolderSize -Auto

# Recoverable Items folder (check for litigation/retention)
Get-MailboxFolderStatistics -Identity "user@ergolab.local" -FolderScope RecoverableItems | Format-List FolderName,ItemCount,TotalSize

# Archive recoverable items
Get-MailboxFolderStatistics "user@ergolab.local" -Archive -FolderScope "Recoverable Items" | Format-List FolderName,ItemCount,TotalSize
```

### Mailbox Quotas

```powershell
# View quota settings for a mailbox
Get-Mailbox -Identity "user@ergolab.local" | Format-List UseDatabaseQuotaDefaults,IssueWarningQuota,ProhibitSendQuota,ProhibitSendReceiveQuota

# Set per-mailbox quotas (overrides database defaults)
Set-Mailbox -Identity "user@ergolab.local" `
  -IssueWarningQuota 1.8GB `
  -ProhibitSendQuota 2GB `
  -ProhibitSendReceiveQuota 2.1GB `
  -UseDatabaseQuotaDefaults $false

# Reset to use database defaults
Set-Mailbox -Identity "user@ergolab.local" -UseDatabaseQuotaDefaults $true

# View database-level default quotas
Get-MailboxDatabase "DB01" | Format-List IssueWarningQuota,ProhibitSendQuota,ProhibitSendReceiveQuota
```

### New-MoveRequest / Get-MoveRequest

```powershell
# Move mailbox to different database
New-MoveRequest -Identity "user@ergolab.local" -TargetDatabase "DB02"

# Move with ignore rule limit errors (useful for large mailboxes)
New-MoveRequest -Identity "user@ergolab.local" -TargetDatabase "DB02" -IgnoreRuleLimitErrors $true

# Check status of all move requests
Get-MoveRequest | Format-Table DisplayName,Status,PercentComplete -Auto

# Get detailed progress on a specific move
Get-MoveRequestStatistics -Identity "user@ergolab.local" | Format-List DisplayName,Status,PercentComplete,BytesTransferred,TotalMailboxSize

# Clean up completed requests
Get-MoveRequest -MoveStatus Completed | Remove-MoveRequest

# Cancel a move in progress
Get-MoveRequest -Identity "user@ergolab.local" | Remove-MoveRequest
```

**Move statuses:** `Queued`, `InProgress`, `AutoSuspended`, `CompletionInProgress`, `Completed`, `CompletedWithWarning`, `Failed`

---

## Recipient Management

### Mailbox Creation

```powershell
# Create user mailbox (user must exist in AD)
Enable-Mailbox -Identity "ERGOLAB\jsmith" -Database "DB01"

# Create new user + mailbox in one step
New-Mailbox -Name "John Smith" -Alias jsmith -UserPrincipalName jsmith@ergolab.local `
  -SamAccountName jsmith -Password (ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force) `
  -Database "DB01"

# Create shared mailbox
New-Mailbox -Shared -Name "Helpdesk" -Alias helpdesk -DisplayName "Help Desk" `
  -PrimarySMTPAddress helpdesk@ergolab.local -Database "DB01"

# Create room mailbox
New-Mailbox -Room -Name "Conference Room A" -Alias confrooma `
  -PrimarySMTPAddress confrooma@ergolab.local -Database "DB01"
```

### Mailbox Permissions

```powershell
# Grant Full Access (user can open another's mailbox)
Add-MailboxPermission -Identity "sharedmailbox@ergolab.local" -User "jsmith" -AccessRights FullAccess -InheritanceType All

# Grant Send As
Add-ADPermission -Identity "sharedmailbox" -User "jsmith" -ExtendedRights "Send As"

# Grant Send on Behalf
Set-Mailbox -Identity "sharedmailbox@ergolab.local" -GrantSendOnBehalfTo "jsmith"

# View current permissions
Get-MailboxPermission -Identity "sharedmailbox@ergolab.local" | Where-Object {$_.User -notlike "NT AUTHORITY*"}
```

### Distribution Groups

```powershell
# Create distribution group
New-DistributionGroup -Name "IT Team" -Alias itteam -PrimarySMTPAddress itteam@ergolab.local -Type Distribution

# Create mail-enabled security group
New-DistributionGroup -Name "IT Security" -Alias itsecurity -Type Security

# Add members
Add-DistributionGroupMember -Identity "IT Team" -Member "jsmith@ergolab.local"

# List members
Get-DistributionGroupMember -Identity "IT Team" | Format-Table DisplayName,PrimarySmtpAddress -Auto

# Create dynamic distribution group
New-DynamicDistributionGroup -Name "All Employees" `
  -IncludedRecipients "MailboxUsers" `
  -ConditionalDepartment "All"

# View dynamic group membership preview
$ddg = Get-DynamicDistributionGroup "All Employees"
Get-Recipient -RecipientPreviewFilter $ddg.RecipientFilter | Select-Object DisplayName,PrimarySmtpAddress
```

---

## Compliance & Audit

### Key Cmdlets

| Cmdlet | Purpose |
|--------|---------|
| `Search-Mailbox` | Search and copy/delete mailbox content |
| `New-MailboxSearch` | Create In-Place eDiscovery search |
| `Get-MailboxAuditLog` | View mailbox audit log entries |
| `Set-Mailbox -AuditEnabled` | Enable mailbox audit logging |
| `New-HoldPolicy` | Create litigation/In-Place hold |

### Mailbox Audit Logging

```powershell
# Enable audit logging on a mailbox
Set-Mailbox -Identity "jsmith@ergolab.local" -AuditEnabled $true -AuditLogAgeLimit 180 `
  -AuditOwner MailboxLogin,HardDelete,SoftDelete `
  -AuditDelegate SendOnBehalf,MoveToDeletedItems `
  -AuditAdmin Copy,MessageBind

# Search audit log for a user's actions
Search-MailboxAuditLog -Identity "jsmith@ergolab.local" -LogonTypes Owner -ShowDetails `
  -StartDate (Get-Date).AddDays(-30) -EndDate (Get-Date) |
  Select-Object Operation,LogonUserDisplayName,LastAccessed,DestFolderPathName

# Check who accessed a mailbox
Search-MailboxAuditLog -Identity "ceo@ergolab.local" -LogonTypes Delegate,Admin `
  -StartDate (Get-Date).AddDays(-7) -EndDate (Get-Date) | Format-Table Operation,LogonUserDisplayName -Auto
```

### Content Search / Litigation Hold

```powershell
# Place mailbox on litigation hold (indefinite)
Set-Mailbox -Identity "jsmith@ergolab.local" -LitigationHoldEnabled $true

# Litigation hold with duration (days)
Set-Mailbox -Identity "jsmith@ergolab.local" -LitigationHoldEnabled $true -LitigationHoldDuration 2555

# Check hold status
Get-Mailbox -Identity "jsmith@ergolab.local" | Format-List LitigationHoldEnabled,LitigationHoldDate,LitigationHoldDuration

# Search mailbox content
Search-Mailbox -Identity "jsmith@ergolab.local" -SearchQuery "subject:confidential" `
  -TargetMailbox "admin@ergolab.local" -TargetFolder "SearchResults" -LogLevel Full
```

---

## Common Troubleshooting

### Replication Lag / Copy Queue Buildup

```powershell
# Identify which copies are lagging
Get-MailboxDatabaseCopyStatus * | Where-Object {$_.CopyQueueLength -gt 10} |
  Format-Table Name,Status,CopyQueueLength,ReplayQueueLength -Auto

# Check network replication connectivity between nodes
Test-ReplicationHealth

# Suspend and resume a copy to reset replication
Suspend-MailboxDatabaseCopy -Identity "DB01\EXCHANGELAB2" -SuspendComment "Troubleshooting"
Resume-MailboxDatabaseCopy -Identity "DB01\EXCHANGELAB2"

# Full reseed if copy is failed/disconnected
Update-MailboxDatabaseCopy -Identity "DB01\EXCHANGELAB2"
```

### Content Index Failures

```powershell
# Find databases with unhealthy content index
Get-MailboxDatabaseCopyStatus * | Where-Object {$_.ContentIndexState -ne "Healthy"} |
  Format-Table Name,Status,ContentIndexState -Auto

# Reseed just the catalog (fast — no DB copy needed)
Update-MailboxDatabaseCopy -Identity "DB01\EXCHANGELAB2" -CatalogOnly

# Reseed catalog from specific healthy source
Update-MailboxDatabaseCopy -Identity "DB01\EXCHANGELAB2" -SourceServer "EXCHANGELAB" -CatalogOnly

# Restart Exchange Search services if catalog reseed fails
Restart-Service MSExchangeFastSearch
Restart-Service HostControllerService
```

### Transport Queue Buildup

```powershell
# Identify backed-up queues
Get-Queue | Where-Object {$_.MessageCount -gt 50} | Format-Table Identity,Status,MessageCount,NextRetryTime -Auto

# Check poison message queue
Get-Queue -Identity "EXCHANGELAB\Poison"

# Force retry all stuck queues
Get-Queue -Filter "Status -eq 'Retry'" | Retry-Queue

# Check SMTP send connector configuration
Get-SendConnector | Format-Table Name,Enabled,AddressSpaces,SmartHosts -Auto

# Check receive connector status
Get-ReceiveConnector | Format-Table Name,Enabled,Bindings -Auto

# View transport logs (last 100 lines)
Get-TransportService EXCHANGELAB | Format-List
# Logs at: C:\Program Files\Microsoft\Exchange Server\V15\TransportRoles\Logs\
```

### Certificate Issues

```powershell
# Find expiring certificates
Get-ExchangeCertificate | Where-Object {$_.NotAfter -lt (Get-Date).AddDays(90)} |
  Format-Table Thumbprint,Subject,NotAfter,Services -Auto

# Check which certificate is bound to each service
Get-ExchangeCertificate | Format-Table Thumbprint,Subject,Services,NotAfter -Auto

# Test SMTP TLS
Test-SmtpConnectivity -Identity EXCHANGELAB

# Verify certificate is properly enabled for services
Get-ExchangeCertificate -Thumbprint "THUMBPRINT" | Format-List Subject,Services,NotBefore,NotAfter,Thumbprint
```

### DAG Cluster Health

```powershell
# Full DAG replication health check
Test-ReplicationHealth

# Check cluster quorum state
Get-ClusterNode | Format-Table Name,State -Auto

# View DAG network status
Get-DatabaseAvailabilityGroupNetwork | Format-Table Name,ReplicationEnabled,Subnets -Auto

# Check witness server connectivity
Test-DirectoryServerConnectivity

# View cluster event log for recent errors
Get-ClusterLog -Node EXCHANGELAB -TimeSpan 60  # last 60 minutes
```

### Service Not Starting

```powershell
# Check all Exchange services
Test-ServiceHealth -Server EXCHANGELAB

# View services with non-running state
Get-Service | Where-Object {$_.DisplayName -like "Microsoft Exchange*" -and $_.Status -ne "Running"}

# Restart core transport service
Restart-Service MSExchangeTransport

# Restart IIS (affects OWA, ECP, ActiveSync, EWS)
iisreset /noforce

# Check Windows event log for Exchange errors
Get-EventLog -LogName Application -Source *Exchange* -EntryType Error -Newest 20 |
  Format-Table TimeGenerated,Source,EventID,Message -Wrap
```

---

## Quick Reference Card

### Daily Health Check Script

```powershell
# Paste into EMS for a quick environment overview
Write-Host "=== DAG Replication Health ===" -ForegroundColor Cyan
Test-ReplicationHealth | Format-Table Server,Check,Result -Auto

Write-Host "`n=== Database Copy Status ===" -ForegroundColor Cyan
Get-MailboxDatabaseCopyStatus * | Format-Table Name,Status,CopyQueueLength,ContentIndexState -Auto

Write-Host "`n=== Unhealthy Health Sets ===" -ForegroundColor Cyan
"EXCHANGELAB","EXCHANGELAB2" | ForEach-Object {
  Get-HealthReport -Identity $_ | Where-Object {$_.AlertValue -ne "Healthy"} |
    Format-Table Server,HealthSetName,AlertValue -Auto
}

Write-Host "`n=== Transport Queues (>10 messages) ===" -ForegroundColor Cyan
Get-Queue | Where-Object {$_.MessageCount -gt 10} | Format-Table Identity,Status,MessageCount -Auto

Write-Host "`n=== Expiring Certificates (90 days) ===" -ForegroundColor Cyan
Get-ExchangeCertificate | Where-Object {$_.NotAfter -lt (Get-Date).AddDays(90)} |
  Format-Table Thumbprint,Subject,NotAfter,Services -Auto
```

### Component State Reference

| Component | Active | Inactive/Draining |
|-----------|--------|-------------------|
| `ServerWideOffline` | Normal ops | Server in maintenance |
| `HubTransport` | Accepting/routing mail | Draining queues |
| `FrontendTransport` | Client mail accepted | Not accepting inbound |
| `Monitoring` | Managed availability on | Health checks paused |
| `RecoveryActionsEnabled` | Auto-recovery active | Recovery actions blocked |
| `UMCallRouter` | UM routing active | UM calls redirected |

### Move-ActiveMailboxDatabase Skip Flags

| Flag | Skips |
|------|-------|
| `-SkipHealthChecks` | All safety checks (nuclear option) |
| `-SkipActiveCopyChecks` | Active copy state validation |
| `-SkipLagChecks` | Copy/replay queue length limits |
| `-SkipClientExperienceChecks` | Client connection health |

---

*Sources: Microsoft Learn — Exchange Server documentation*
*Context7 library: `/websites/learn_microsoft_en-us_exchange`*
