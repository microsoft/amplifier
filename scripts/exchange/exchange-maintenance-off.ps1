param(
    [Parameter(Mandatory=$true)]
    [string]$TargetServer,
    [string]$ExchangeServer = "EXCHANGELAB",
    [string]$Auth = "Kerberos"
)

# Exit Exchange Maintenance Mode — reverse of maintenance-on
# Usage: .\exchange-maintenance-off.ps1 -TargetServer "EXCHANGELAB"

$ErrorActionPreference = "Stop"

$connectTo = if ($TargetServer -match "EXCHANGELAB2") { "EXCHANGELAB" } else { "EXCHANGELAB2" }

try {
    $session = New-PSSession -ConfigurationName Microsoft.Exchange `
        -ConnectionUri "http://$connectTo/PowerShell/" `
        -Authentication $Auth `
        -ErrorAction Stop
} catch {
    Write-Output "PHASE|CONNECTION|FAIL|$($_.Exception.Message)"
    exit 1
}

$fqdn = "$TargetServer"

# Step 1: Set server components back to Active
Write-Output "PHASE|STEP1|START|Activating server components on $TargetServer"
try {
    Invoke-Command -Session $session -ScriptBlock {
        param($server)
        Set-ServerComponentState -Identity $server -Component ServerWideOffline -State Active -Requester Maintenance
    } -ArgumentList $fqdn
    Write-Output "PHASE|STEP1|PASS|Components set to Active"
} catch {
    Write-Output "PHASE|STEP1|FAIL|$($_.Exception.Message)"
}

# Step 2: Unblock database auto-activation
Write-Output "PHASE|STEP2|START|Unblocking database activation"
try {
    Invoke-Command -Session $session -ScriptBlock {
        param($server) Set-MailboxServer -Identity $server -DatabaseCopyAutoActivationPolicy Unrestricted
    } -ArgumentList $fqdn
    Write-Output "PHASE|STEP2|PASS|Auto-activation unrestricted"
} catch {
    Write-Output "PHASE|STEP2|FAIL|$($_.Exception.Message)"
}

# Step 3: Resume cluster node
Write-Output "PHASE|STEP3|START|Resuming cluster node"
try {
    Invoke-Command -Session $session -ScriptBlock {
        param($server) Resume-ClusterNode -Name $server -ErrorAction Stop
    } -ArgumentList $TargetServer
    Write-Output "PHASE|STEP3|PASS|Cluster node resumed"
} catch {
    Write-Output "PHASE|STEP3|WARN|$($_.Exception.Message)"
}

# Step 4: Resume HubTransport
Write-Output "PHASE|STEP4|START|Resuming transport"
try {
    Invoke-Command -Session $session -ScriptBlock {
        param($server)
        Set-ServerComponentState -Identity $server -Component HubTransport -State Active -Requester Maintenance
    } -ArgumentList $fqdn
    Write-Output "PHASE|STEP4|PASS|HubTransport active"
} catch {
    Write-Output "PHASE|STEP4|FAIL|$($_.Exception.Message)"
}

# Step 5: Verify
Write-Output "PHASE|STEP5|START|Verifying server is back online"
Start-Sleep -Seconds 5

$components = Invoke-Command -Session $session -ScriptBlock {
    param($server) Get-ServerComponentState -Identity $server | Where-Object { $_.State -ne "Active" }
} -ArgumentList $fqdn

$dbStatus = Invoke-Command -Session $session -ScriptBlock {
    param($server) Get-MailboxDatabaseCopyStatus -Server $server | Select-Object Name, Status
} -ArgumentList $TargetServer

$inactiveCount = ($components | Measure-Object).Count
$healthyDbs = ($dbStatus | Where-Object { $_.Status -match "Healthy|Mounted" } | Measure-Object).Count
$totalDbs = ($dbStatus | Measure-Object).Count

if ($inactiveCount -eq 0) {
    Write-Output "PHASE|STEP5|PASS|All components Active. Databases: $healthyDbs/$totalDbs healthy"
} else {
    Write-Output "PHASE|STEP5|WARN|$inactiveCount components still inactive. Databases: $healthyDbs/$totalDbs"
}

Write-Output "PHASE|RESULT|DONE|$TargetServer back online"

Remove-PSSession $session -ErrorAction SilentlyContinue
