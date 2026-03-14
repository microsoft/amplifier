param(
    [string]$Server = "EXCHANGELAB.lab.ergonet.pl",
    [string]$Username = "ERGOLAB\Administrator"
)

# Exchange Full Health Check — all 8 checks
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

# 1-4: Same as quick health (database copies, replication, services, components)

# Database Copy Status
try {
    $copies = Invoke-Command -Session $session -ScriptBlock {
        Get-MailboxDatabaseCopyStatus | Select-Object Name, Status, ContentIndexState, CopyQueueLength, ReplayQueueLength, LastInspectedLogTime
    }
    foreach ($copy in $copies) {
        $status = if ($copy.Status -match "Healthy|Mounted") { "PASS" }
                  elseif ($copy.Status -match "Suspended|Initializing") { "WARN" }
                  else { "FAIL" }
        $lag = if ($copy.LastInspectedLogTime) { "LastLog=$($copy.LastInspectedLogTime.ToString('HH:mm:ss'))" } else { "" }
        Write-Output "DatabaseCopy|$status|$($copy.Name): $($copy.Status), CI=$($copy.ContentIndexState), CopyQ=$($copy.CopyQueueLength), ReplayQ=$($copy.ReplayQueueLength) $lag"
    }
} catch {
    Write-Output "DatabaseCopy|FAIL|Error: $($_.Exception.Message)"
}

# Replication Health
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

# Service Health
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

# Server Component State
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

# 5. Mail Flow Test
try {
    $mailflow = Invoke-Command -Session $session -ScriptBlock {
        Test-MailFlow | Select-Object TestMailflowResult, MessageLatencyTime
    }
    $status = if ($mailflow.TestMailflowResult -eq "Success") { "PASS" } else { "FAIL" }
    Write-Output "MailFlow|$status|Result=$($mailflow.TestMailflowResult), Latency=$($mailflow.MessageLatencyTime)"
} catch {
    Write-Output "MailFlow|WARN|Test-MailFlow not available or failed: $($_.Exception.Message)"
}

# 6. Transport Queues
try {
    $queues = Invoke-Command -Session $session -ScriptBlock {
        Get-Queue | Where-Object { $_.MessageCount -gt 0 } | Select-Object Identity, DeliveryType, Status, MessageCount, NextHopDomain
    }
    if ($queues) {
        foreach ($q in $queues) {
            $status = if ($q.MessageCount -gt 100) { "WARN" } else { "PASS" }
            Write-Output "TransportQueues|$status|$($q.Identity): $($q.MessageCount) msgs, Type=$($q.DeliveryType), Status=$($q.Status)"
        }
    } else {
        Write-Output "TransportQueues|PASS|All queues empty"
    }
} catch {
    Write-Output "TransportQueues|FAIL|Error: $($_.Exception.Message)"
}

# 7. Certificates
try {
    $certs = Invoke-Command -Session $session -ScriptBlock {
        Get-ExchangeCertificate | Where-Object { $_.NotAfter -lt (Get-Date).AddDays(30) -and $_.Services -ne "None" } |
            Select-Object Subject, NotAfter, Services, Thumbprint
    }
    if ($certs) {
        foreach ($cert in $certs) {
            $daysLeft = ($cert.NotAfter - (Get-Date)).Days
            $status = if ($daysLeft -lt 0) { "FAIL" } elseif ($daysLeft -lt 14) { "WARN" } else { "PASS" }
            Write-Output "Certificates|$status|$($cert.Subject): expires in $daysLeft days, Services=$($cert.Services)"
        }
    } else {
        Write-Output "Certificates|PASS|No certificates expiring within 30 days"
    }
} catch {
    Write-Output "Certificates|FAIL|Error: $($_.Exception.Message)"
}

# 8. DAG Network
try {
    $dagNet = Invoke-Command -Session $session -ScriptBlock {
        Get-DatabaseAvailabilityGroupNetwork | Select-Object Name, Subnets, ReplicationEnabled, MapiAccessEnabled
    }
    foreach ($net in $dagNet) {
        Write-Output "DAGNetwork|PASS|$($net.Name): Subnets=$($net.Subnets -join ','), Repl=$($net.ReplicationEnabled), MAPI=$($net.MapiAccessEnabled)"
    }
} catch {
    Write-Output "DAGNetwork|FAIL|Error: $($_.Exception.Message)"
}

Remove-PSSession $session -ErrorAction SilentlyContinue
