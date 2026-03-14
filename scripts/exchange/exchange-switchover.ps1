param(
    [Parameter(Mandatory=$true)]
    [string]$Database,
    [string]$TargetServer,
    [string]$ExchangeServer = "EXCHANGELAB",
    [string]$Auth = "Kerberos"
)

# Exchange Database Switchover — Move active database to another DAG node
# Usage: .\exchange-switchover.ps1 -Database "DAG-DB01" [-TargetServer "EXCHANGELAB2"]

$ErrorActionPreference = "Stop"

try {
    $session = New-PSSession -ConfigurationName Microsoft.Exchange `
        -ConnectionUri "http://$ExchangeServer/PowerShell/" `
        -Authentication $Auth `
        -ErrorAction Stop
} catch {
    Write-Output "PHASE|CONNECTION|FAIL|$($_.Exception.Message)"
    exit 1
}

# Phase 1: Pre-check
Write-Output "PHASE|PRECHECK|START|Checking database $Database status"

$preStatus = Invoke-Command -Session $session -ScriptBlock {
    param($db) Get-MailboxDatabaseCopyStatus -Identity $db | Select-Object Name, Status, ActiveDatabaseCopy, MailboxServer
} -ArgumentList $Database

$activeServer = ($preStatus | Where-Object { $_.Status -eq "Mounted" }).MailboxServer
$healthyCopies = ($preStatus | Where-Object { $_.Status -eq "Healthy" }).MailboxServer

if (-not $activeServer) {
    Write-Output "PHASE|PRECHECK|FAIL|Database $Database not found or not mounted"
    Remove-PSSession $session; exit 1
}

if (-not $TargetServer) {
    $TargetServer = $healthyCopies | Select-Object -First 1
}

if (-not $TargetServer) {
    Write-Output "PHASE|PRECHECK|FAIL|No healthy passive copy available for switchover"
    Remove-PSSession $session; exit 1
}

Write-Output "PHASE|PRECHECK|PASS|Active=$activeServer, Target=$TargetServer, HealthyCopies=$($healthyCopies -join ',')"

# Phase 2: Impact assessment
$mailboxCount = Invoke-Command -Session $session -ScriptBlock {
    param($db) (Get-Mailbox -Database $db -ResultSize Unlimited | Measure-Object).Count
} -ArgumentList $Database

Write-Output "PHASE|IMPACT|INFO|$mailboxCount mailboxes will be briefly unavailable during switchover"
Write-Output "PHASE|CONFIRM|WAITING|Move $Database from $activeServer to $TargetServer? ($mailboxCount mailboxes)"

# Phase 3: Execute switchover
try {
    Invoke-Command -Session $session -ScriptBlock {
        param($db, $target) Move-ActiveMailboxDatabase -Identity $db -ActivateOnServer $target -Confirm:$false
    } -ArgumentList $Database, $TargetServer

    Write-Output "PHASE|EXECUTE|PASS|Switchover initiated"
} catch {
    Write-Output "PHASE|EXECUTE|FAIL|$($_.Exception.Message)"
    Remove-PSSession $session; exit 1
}

# Phase 4: Post-verify (wait and check)
Start-Sleep -Seconds 10

$postStatus = Invoke-Command -Session $session -ScriptBlock {
    param($db) Get-MailboxDatabaseCopyStatus -Identity $db | Select-Object Name, Status, MailboxServer
} -ArgumentList $Database

foreach ($copy in $postStatus) {
    $status = if ($copy.Status -match "Mounted|Healthy") { "PASS" } else { "WARN" }
    Write-Output "PHASE|VERIFY|$status|$($copy.Name) on $($copy.MailboxServer): $($copy.Status)"
}

$newActive = ($postStatus | Where-Object { $_.Status -eq "Mounted" }).MailboxServer
if ($newActive -eq $TargetServer) {
    Write-Output "PHASE|RESULT|PASS|Switchover complete: $Database now active on $TargetServer"
} else {
    Write-Output "PHASE|RESULT|WARN|Switchover may still be in progress. Current active: $newActive"
}

Remove-PSSession $session -ErrorAction SilentlyContinue
