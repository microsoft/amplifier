param(
    [string]$Server = "EXCHANGELAB",
    [string]$Auth = "Kerberos",
    [string]$PasswordFile = "C:\claude\amplifier\scripts\exchange\.cred"
)

# Exchange CredSSP Session Helper
# Returns a PSSession connected to Exchange Management Shell
# Usage: $session = & .\exchange-connect.ps1 [-Server <FQDN>]

$ErrorActionPreference = "Stop"

# Build credential
if (Test-Path $PasswordFile) {
} else {
    # Fallback: prompt or use default lab password
}

# Connect via CredSSP (required for double-hop: DEV → Exchange → AD)
try {
    $session = New-PSSession -ConfigurationName Microsoft.Exchange `
        -ConnectionUri "http://$Server/PowerShell/" `
        -Authentication $Auth `
        -ErrorAction Stop

    Write-Output "CONNECTED|$Server|$($session.Id)"
    return $session
} catch {
    Write-Error "CONNECTION_FAILED|$Server|$($_.Exception.Message)"
    exit 1
}
