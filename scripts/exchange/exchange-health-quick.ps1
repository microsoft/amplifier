param(
    [string]$Server = "EXCHANGELAB.lab.ergonet.pl",
    [string]$Username = "ERGOLAB\Administrator"
)

# Exchange Quick Health Check — 4 fast, non-disruptive checks
# Returns pipe-delimited results: CHECK|STATUS|DETAILS

$ErrorActionPreference = "SilentlyContinue"
$secPass = ConvertTo-SecureString "Exchange@Lab2026" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential($Username, $secPass)

try {
    $session = New-PSSession -ConfigurationName Microsoft.Exchange `
        -ConnectionUri "http://$Server/PowerShell/" `
        -Authentication Credssp `
        -Credential $cred `
        -ErrorAction Stop
} catch {
    Write-Output "CONNECTION|FAIL|Cannot connect to $Server - $($_.Exception.Message)"
    exit 1
}

# 1. Database Copy Status
try {
    $copies = Invoke-Command -Session $session -ScriptBlock {
        Get-MailboxDatabaseCopyStatus | Select-Object Name, Status, ContentIndexState, CopyQueueLength, ReplayQueueLength
    }
    foreach ($copy in $copies) {
        $status = if ($copy.Status -match "Healthy|Mounted") { "PASS" }
                  elseif ($copy.Status -match "Suspended|Initializing") { "WARN" }
                  else { "FAIL" }
        Write-Output "DatabaseCopy|$status|$($copy.Name): $($copy.Status), CI=$($copy.ContentIndexState), CopyQ=$($copy.CopyQueueLength), ReplayQ=$($copy.ReplayQueueLength)"
    }
} catch {
    Write-Output "DatabaseCopy|FAIL|Error: $($_.Exception.Message)"
}

# 2. Replication Health
try {
    $replHealth = Invoke-Command -Session $session -ScriptBlock {
        Test-ReplicationHealth | Select-Object Check, Result, Error
    }
    foreach ($check in $replHealth) {
        $status = if ($check.Result -eq "Passed") { "PASS" } else { "FAIL" }
        $detail = if ($check.Error) { "$($check.Check): $($check.Error)" } else { $check.Check }
        Write-Output "ReplicationHealth|$status|$detail"
    }
} catch {
    Write-Output "ReplicationHealth|FAIL|Error: $($_.Exception.Message)"
}

# 3. Service Health
try {
    $svcHealth = Invoke-Command -Session $session -ScriptBlock {
        Test-ServiceHealth | Select-Object Role, RequiredServicesRunning
    }
    foreach ($role in $svcHealth) {
        $status = if ($role.RequiredServicesRunning) { "PASS" } else { "FAIL" }
        Write-Output "ServiceHealth|$status|$($role.Role): RequiredRunning=$($role.RequiredServicesRunning)"
    }
} catch {
    Write-Output "ServiceHealth|FAIL|Error: $($_.Exception.Message)"
}

# 4. Server Component State
try {
    $components = Invoke-Command -Session $session -ScriptBlock {
        Get-ExchangeServer | ForEach-Object {
            $server = $_.Name
            Get-ServerComponentState -Identity $server | Where-Object { $_.State -ne "Active" } | ForEach-Object {
                [PSCustomObject]@{ Server = $server; Component = $_.Component; State = $_.State }
            }
        }
    }
    if ($components) {
        foreach ($c in $components) {
            Write-Output "ServerComponents|WARN|$($c.Server): $($c.Component) = $($c.State)"
        }
    } else {
        Write-Output "ServerComponents|PASS|All components Active on all servers"
    }
} catch {
    Write-Output "ServerComponents|FAIL|Error: $($_.Exception.Message)"
}

Remove-PSSession $session -ErrorAction SilentlyContinue
