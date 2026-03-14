param(
    [Parameter(Mandatory=$true)]
    [string]$TargetServer,
    [string]$ExchangeServer = "EXCHANGELAB.lab.ergonet.pl",
    [string]$Username = "ERGOLAB\Administrator"
)

# Enter Exchange Maintenance Mode — 6-step procedure
# Usage: .\exchange-maintenance-on.ps1 -TargetServer "EXCHANGELAB"

$ErrorActionPreference = "Stop"
$secPass = ConvertTo-SecureString "Exchange@Lab2026" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential($Username, $secPass)

# Connect to a server that is NOT the target (so we keep our session alive)
$connectTo = if ($TargetServer -match "EXCHANGELAB2") { "EXCHANGELAB.lab.ergonet.pl" } else { "EXCHANGELAB2.lab.ergonet.pl" }

try {
    $session = New-PSSession -ConfigurationName Microsoft.Exchange `
        -ConnectionUri "http://$connectTo/PowerShell/" `
        -Authentication Credssp `
        -Credential $cred `
        -ErrorAction Stop
} catch {
    Write-Output "PHASE|CONNECTION|FAIL|$($_.Exception.Message)"
    exit 1
}

$fqdn = "$TargetServer.lab.ergonet.pl"

# Step 1: Drain transport queues
Write-Output "PHASE|STEP1|START|Draining transport queues on $TargetServer"
try {
    Invoke-Command -Session $session -ScriptBlock {
        param($server, $partner)
        Set-ServerComponentState -Identity $server -Component HubTransport -State Draining -Requester Maintenance
        Redirect-Message -Server $server -Target $partner
    } -ArgumentList $fqdn, $connectTo
    Write-Output "PHASE|STEP1|PASS|Transport queues draining, messages redirected to $connectTo"
} catch {
    Write-Output "PHASE|STEP1|FAIL|$($_.Exception.Message)"
}

# Step 2: Suspend cluster node (for DAG)
Write-Output "PHASE|STEP2|START|Suspending cluster node $TargetServer"
try {
    Invoke-Command -Session $session -ScriptBlock {
        param($server) Suspend-ClusterNode -Name $server -ErrorAction Stop
    } -ArgumentList $TargetServer
    Write-Output "PHASE|STEP2|PASS|Cluster node suspended"
} catch {
    Write-Output "PHASE|STEP2|WARN|$($_.Exception.Message) (may not be clustered)"
}

# Step 3: Move all active databases off target
Write-Output "PHASE|STEP3|START|Moving active databases off $TargetServer"
try {
    $activeDbs = Invoke-Command -Session $session -ScriptBlock {
        param($server) Get-MailboxDatabaseCopyStatus -Server $server | Where-Object { $_.Status -eq "Mounted" }
    } -ArgumentList $TargetServer

    $movedCount = 0
    foreach ($db in $activeDbs) {
        $dbName = ($db.Name -split "\\")[0]
        Invoke-Command -Session $session -ScriptBlock {
            param($name) Move-ActiveMailboxDatabase -Identity $name -Confirm:$false
        } -ArgumentList $dbName
        $movedCount++
        Write-Output "PHASE|STEP3|INFO|Moved $dbName off $TargetServer"
    }
    Write-Output "PHASE|STEP3|PASS|Moved $movedCount databases"
} catch {
    Write-Output "PHASE|STEP3|FAIL|$($_.Exception.Message)"
}

# Step 4: Set DatabaseCopyAutoActivation to Blocked
Write-Output "PHASE|STEP4|START|Blocking database activation on $TargetServer"
try {
    Invoke-Command -Session $session -ScriptBlock {
        param($server) Set-MailboxServer -Identity $server -DatabaseCopyAutoActivationPolicy Blocked
    } -ArgumentList $fqdn
    Write-Output "PHASE|STEP4|PASS|Auto-activation blocked"
} catch {
    Write-Output "PHASE|STEP4|FAIL|$($_.Exception.Message)"
}

# Step 5: Set all server components to Inactive
Write-Output "PHASE|STEP5|START|Setting server components to Inactive"
try {
    Invoke-Command -Session $session -ScriptBlock {
        param($server)
        Set-ServerComponentState -Identity $server -Component ServerWideOffline -State Inactive -Requester Maintenance
    } -ArgumentList $fqdn
    Write-Output "PHASE|STEP5|PASS|All components set to Inactive"
} catch {
    Write-Output "PHASE|STEP5|FAIL|$($_.Exception.Message)"
}

# Step 6: Verify
Write-Output "PHASE|STEP6|START|Verifying maintenance mode"
Start-Sleep -Seconds 5

$verifyDbs = Invoke-Command -Session $session -ScriptBlock {
    param($server) Get-MailboxDatabaseCopyStatus -Server $server | Select-Object Name, Status
} -ArgumentList $TargetServer

$verifyComponents = Invoke-Command -Session $session -ScriptBlock {
    param($server) Get-ServerComponentState -Identity $server | Where-Object { $_.State -eq "Active" }
} -ArgumentList $fqdn

$activeOnTarget = $verifyDbs | Where-Object { $_.Status -eq "Mounted" }
$activeComponents = $verifyComponents | Measure-Object

if ($activeOnTarget.Count -eq 0 -and $activeComponents.Count -eq 0) {
    Write-Output "PHASE|STEP6|PASS|$TargetServer fully in maintenance mode. 0 active databases, 0 active components."
} else {
    Write-Output "PHASE|STEP6|WARN|$TargetServer partially in maintenance. ActiveDBs=$($activeOnTarget.Count), ActiveComponents=$($activeComponents.Count)"
}

Write-Output "PHASE|RESULT|DONE|Maintenance mode procedure complete for $TargetServer"

Remove-PSSession $session -ErrorAction SilentlyContinue
