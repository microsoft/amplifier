param(
    [Parameter(Mandatory=$true)]
    [int]$PrNumber,

    [ValidateSet("squash", "merge", "rebase")]
    [string]$MergeStyle = "squash",

    [switch]$DeleteBranch,

    [string]$GiteaUrl = "https://gitea.ergonet.pl:3001",
    [string]$Repo = "",
    [string]$Token = $env:GITEA_ADMIN_TOKEN,

    [string]$RepoDir = ""
)

if (-not $Token) {
    $Token = "2b1322e34ee940a072903a6d52c59aca82858d12"
}

# Skip SSL validation and force TLS 1.2 (self-signed cert) — must be set before any API calls
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
try {
    Add-Type @"
using System.Net;
using System.Net.Security;
using System.Security.Cryptography.X509Certificates;
public class TrustAllCertsPolicy {
    public static void Enable() {
        ServicePointManager.ServerCertificateValidationCallback =
            delegate { return true; };
    }
}
"@
    [TrustAllCertsPolicy]::Enable()
} catch {
    # Type may already be added in this session
    [System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
}

# Helper: check if PR exists in a given repo via Gitea API
function Test-PrExists {
    param([string]$RepoSlug, [int]$PrNum, [string]$BaseUrl, [string]$ApiToken)
    try {
        $null = Invoke-RestMethod -Uri "$BaseUrl/api/v1/repos/$RepoSlug/pulls/$PrNum" `
            -Headers @{ "Authorization" = "token $ApiToken" } -Method Get
        return $true
    } catch {
        return $false
    }
}

# Auto-detect repo from git remote if not provided
if (-not $Repo) {
    try {
        # Collect all candidate repos from git directories
        $candidateRepos = @()

        # Use -RepoDir if provided
        if ($RepoDir) {
            $remoteUrl = & git -C $RepoDir remote get-url origin 2>&1
            if ($LASTEXITCODE -eq 0 -and $remoteUrl -match 'gitea\.ergonet\.pl:3001/(.+?)(?:\.git)?$') {
                $candidateRepos += $Matches[1]
            }
        } else {
            # Gather candidates from CWD and common locations
            $searchDirs = @()

            # CWD first
            $root = & git rev-parse --show-toplevel 2>&1
            if ($LASTEXITCODE -eq 0) { $searchDirs += $root }

            # Common repo locations (deduplicated against CWD)
            foreach ($dir in @("C:\claude\fusecp-enterprise", "C:\claude\amplifier", "C:\claude\universal-siem-monorepo")) {
                if ((Test-Path "$dir\.git") -and ($searchDirs -notcontains $dir)) {
                    $searchDirs += $dir
                }
            }

            foreach ($dir in $searchDirs) {
                $remoteUrl = & git -C $dir remote get-url origin 2>&1
                if ($LASTEXITCODE -eq 0 -and $remoteUrl -match 'gitea\.ergonet\.pl:3001/(.+?)(?:\.git)?$') {
                    $slug = $Matches[1]
                    if ($candidateRepos -notcontains $slug) {
                        $candidateRepos += $slug
                    }
                }
            }
        }

        if ($candidateRepos.Count -eq 0) {
            throw "Could not find any git repos with Gitea remotes. Pass -RepoDir or -Repo explicitly."
        }

        # Verify which repo actually has this PR via API
        $found = $false
        foreach ($candidate in $candidateRepos) {
            if (Test-PrExists -RepoSlug $candidate -PrNum $PrNumber -BaseUrl $GiteaUrl -ApiToken $Token) {
                $Repo = $candidate
                $found = $true
                Write-Host "Auto-detected repo: $Repo (PR #$PrNumber found via API)"
                break
            }
        }

        if (-not $found) {
            $tried = $candidateRepos -join ", "
            throw "PR #$PrNumber not found in any candidate repo ($tried). Pass -Repo 'owner/repo' explicitly."
        }
    } catch {
        Write-Error "Failed to auto-detect repo. Error: $_"
        exit 1
    }
}

$uri = "$GiteaUrl/api/v1/repos/$Repo/pulls/$PrNumber/merge"

$payload = @{
    Do                         = $MergeStyle
    delete_branch_after_merge  = [bool]$DeleteBranch
} | ConvertTo-Json -Compress

$headers = @{
    "Authorization" = "token $Token"
    "Content-Type"  = "application/json"
}

try {
    Invoke-RestMethod -Uri $uri -Method Post -Headers $headers -Body $payload
    Write-Host "PR #$PrNumber merged successfully ($MergeStyle)"
    if ($DeleteBranch) {
        Write-Host "Branch deleted after merge"
    }
} catch {
    Write-Error "Failed to merge PR #${PrNumber}: $_"
    exit 1
}
