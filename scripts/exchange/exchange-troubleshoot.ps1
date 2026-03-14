param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("mail-flow","replication","content-index","database","certificate","performance")]
    [string]$Symptom,
    [string]$Server = "EXCHANGELAB",
    [string]$Auth = "Kerberos",
    [int]$EventCount = 20
)

# Exchange Troubleshooter — gather diagnostic data for analysis
# Usage: .\exchange-troubleshoot.ps1 -Symptom "replication" [-Server <FQDN>]
# Returns structured data for agent analysis

$ErrorActionPreference = "SilentlyContinue"

try {
    $session = New-PSSession -ConfigurationName Microsoft.Exchange `
        -ConnectionUri "http://$Server/PowerShell/" `
        -Authentication $Auth `
        -ErrorAction Stop
} catch {
    Write-Output "SECTION|CONNECTION|FAIL|$($_.Exception.Message)"
    exit 1
}

Write-Output "SECTION|SYMPTOM|$Symptom|Gathering diagnostics from $Server"

switch ($Symptom) {
    "replication" {
        # Database copy status
        $copies = Invoke-Command -Session $session -ScriptBlock {
            Get-MailboxDatabaseCopyStatus | Select-Object Name, Status, ContentIndexState, CopyQueueLength, ReplayQueueLength, LastInspectedLogTime, LastCopyNotificationedLogTime
        }
        foreach ($c in $copies) {
            Write-Output "DATA|CopyStatus|$($c.Name)|Status=$($c.Status),CI=$($c.ContentIndexState),CopyQ=$($c.CopyQueueLength),ReplayQ=$($c.ReplayQueueLength)"
        }

        # Replication health
        $replHealth = Invoke-Command -Session $session -ScriptBlock { Test-ReplicationHealth }
        foreach ($r in $replHealth) {
            Write-Output "DATA|ReplHealth|$($r.Check)|$($r.Result) $($r.Error)"
        }

        # Recent replication events
        $events = Invoke-Command -Session $session -ScriptBlock {
            param($count) Get-WinEvent -LogName "Application" -FilterXPath "*[System[Provider[@Name='MSExchangeRepl'] and (Level=1 or Level=2 or Level=3)]]" -MaxEvents $count -ErrorAction SilentlyContinue | Select-Object TimeCreated, Id, LevelDisplayName, Message
        } -ArgumentList $EventCount
        foreach ($e in $events) {
            $msg = ($e.Message -replace "`r`n"," " -replace "`n"," ").Substring(0, [Math]::Min(200, $e.Message.Length))
            Write-Output "EVENT|MSExchangeRepl|$($e.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss'))|ID=$($e.Id)|$($e.LevelDisplayName)|$msg"
        }
    }

    "mail-flow" {
        # Mail flow test
        $mf = Invoke-Command -Session $session -ScriptBlock { Test-MailFlow }
        Write-Output "DATA|MailFlow|Result=$($mf.TestMailflowResult)|Latency=$($mf.MessageLatencyTime)"

        # Queue status
        $queues = Invoke-Command -Session $session -ScriptBlock { Get-Queue }
        foreach ($q in $queues) {
            Write-Output "DATA|Queue|$($q.Identity)|Count=$($q.MessageCount),Status=$($q.Status),Type=$($q.DeliveryType),NextHop=$($q.NextHopDomain)"
        }

        # Transport service config
        $transport = Invoke-Command -Session $session -ScriptBlock {
            Get-TransportService | Select-Object Name, MaxOutboundConnections, MaxPerDomainOutboundConnections, InternalDNSServers, ExternalDNSServers
        }
        foreach ($t in $transport) {
            Write-Output "DATA|Transport|$($t.Name)|MaxOut=$($t.MaxOutboundConnections),MaxPerDomain=$($t.MaxPerDomainOutboundConnections)"
        }

        # Transport events
        $events = Invoke-Command -Session $session -ScriptBlock {
            param($count) Get-WinEvent -LogName "Application" -FilterXPath "*[System[Provider[@Name='MSExchangeTransport'] and (Level=1 or Level=2 or Level=3)]]" -MaxEvents $count -ErrorAction SilentlyContinue | Select-Object TimeCreated, Id, LevelDisplayName, Message
        } -ArgumentList $EventCount
        foreach ($e in $events) {
            $msg = ($e.Message -replace "`r`n"," ").Substring(0, [Math]::Min(200, $e.Message.Length))
            Write-Output "EVENT|Transport|$($e.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss'))|ID=$($e.Id)|$($e.LevelDisplayName)|$msg"
        }
    }

    "content-index" {
        $copies = Invoke-Command -Session $session -ScriptBlock {
            Get-MailboxDatabaseCopyStatus | Select-Object Name, ContentIndexState, ContentIndexErrorMessage
        }
        foreach ($c in $copies) {
            $status = if ($c.ContentIndexState -eq "Healthy") { "PASS" } else { "FAIL" }
            Write-Output "DATA|ContentIndex|$($c.Name)|State=$($c.ContentIndexState),Error=$($c.ContentIndexErrorMessage)"
        }
    }

    "database" {
        $dbs = Invoke-Command -Session $session -ScriptBlock {
            Get-MailboxDatabase -Status | Select-Object Name, Server, Mounted, DatabaseSize, AvailableNewMailboxSpace, EdbFilePath, LogFolderPath
        }
        foreach ($db in $dbs) {
            Write-Output "DATA|Database|$($db.Name)|Server=$($db.Server),Mounted=$($db.Mounted),Size=$($db.DatabaseSize),FreeSpace=$($db.AvailableNewMailboxSpace)"
            Write-Output "DATA|DatabasePaths|$($db.Name)|EDB=$($db.EdbFilePath),Logs=$($db.LogFolderPath)"
        }
    }

    "certificate" {
        $certs = Invoke-Command -Session $session -ScriptBlock {
            Get-ExchangeCertificate | Select-Object Subject, Issuer, NotBefore, NotAfter, Services, Thumbprint, Status, SelfSigned
        }
        foreach ($cert in $certs) {
            $daysLeft = ($cert.NotAfter - (Get-Date)).Days
            Write-Output "DATA|Certificate|$($cert.Subject)|Expires=$($cert.NotAfter.ToString('yyyy-MM-dd')),DaysLeft=$daysLeft,Services=$($cert.Services),SelfSigned=$($cert.SelfSigned),Status=$($cert.Status)"
        }
    }

    "performance" {
        # RPC latency and connections
        $rpc = Invoke-Command -Session $session -ScriptBlock {
            Get-MailboxDatabase -Status | Select-Object Name, MountedOnServer
        }
        foreach ($db in $rpc) {
            Write-Output "DATA|MountedDB|$($db.Name)|Server=$($db.MountedOnServer)"
        }

        # Queue lengths as performance indicator
        $queues = Invoke-Command -Session $session -ScriptBlock { Get-Queue | Where-Object { $_.MessageCount -gt 0 } }
        foreach ($q in $queues) {
            Write-Output "DATA|QueueBacklog|$($q.Identity)|Count=$($q.MessageCount)"
        }

        # Mailbox count per database
        $dbStats = Invoke-Command -Session $session -ScriptBlock {
            Get-MailboxDatabase | ForEach-Object {
                $count = (Get-Mailbox -Database $_.Name -ResultSize Unlimited | Measure-Object).Count
                [PSCustomObject]@{ Database = $_.Name; MailboxCount = $count }
            }
        }
        foreach ($s in $dbStats) {
            Write-Output "DATA|MailboxCount|$($s.Database)|$($s.MailboxCount)"
        }
    }
}

Write-Output "SECTION|COMPLETE|$Symptom|Diagnostics gathered"
Remove-PSSession $session -ErrorAction SilentlyContinue
