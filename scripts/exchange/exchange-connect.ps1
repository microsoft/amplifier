param(
    [string]$Server = "EXCHANGELAB.lab.ergonet.pl",
    [string]$Username = "ERGOLAB\Administrator",
    [string]$PasswordFile = "C:\claude\amplifier\scripts\exchange\.cred"
)

# Exchange CredSSP Session Helper
# Returns a PSSession connected to Exchange Management Shell
# Usage: $session = & .\exchange-connect.ps1 [-Server <FQDN>]

$ErrorActionPreference = "Stop"

# Build credential
if (Test-Path $PasswordFile) {
    $secPass = Get-Content $PasswordFile | ConvertTo-SecureString
} else {
    # Fallback: prompt or use default lab password
    $secPass = ConvertTo-SecureString "Exchange@Lab2026" -AsPlainText -Force
}
$cred = New-Object System.Management.Automation.PSCredential($Username, $secPass)

# Connect via CredSSP (required for double-hop: DEV → Exchange → AD)
try {
    $session = New-PSSession -ConfigurationName Microsoft.Exchange `
        -ConnectionUri "http://$Server/PowerShell/" `
        -Authentication Credssp `
        -Credential $cred `
        -ErrorAction Stop

    Write-Output "CONNECTED|$Server|$($session.Id)"
    return $session
} catch {
    Write-Error "CONNECTION_FAILED|$Server|$($_.Exception.Message)"
    exit 1
}
