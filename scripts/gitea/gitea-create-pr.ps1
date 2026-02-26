param(
    [Parameter(Mandatory=$true)]
    [string]$Title,

    [Parameter(Mandatory=$true)]
    [string]$Head,

    [string]$Base = "main",

    [string]$Body = "",

    [string]$GiteaUrl = "https://gitea.ergonet.pl:3001",
    [string]$Repo = "",
    [string]$Token = $env:GITEA_ADMIN_TOKEN,

    [string]$RepoDir = ""
)

if (-not $Token) {
    $Token = "2b1322e34ee940a072903a6d52c59aca82858d12"
}

# Auto-detect repo from git remote if not provided
if (-not $Repo) {
    try {
        # Use -RepoDir if provided, otherwise find repo that has the Head branch
        $gitDir = ""
        if ($RepoDir) {
            $gitDir = $RepoDir
        } else {
            # First try CWD
            $root = & git rev-parse --show-toplevel 2>&1
            if ($LASTEXITCODE -eq 0) {
                # Verify this repo actually has the branch we're creating the PR for
                $branchCheck = & git -C $root branch --list $Head 2>&1
                if ($branchCheck -and $branchCheck.Trim()) {
                    $gitDir = $root
                }
            }
            # If CWD repo doesn't have the branch, search common repo locations
            if (-not $gitDir) {
                $searchDirs = @("C:\claude\fusecp-enterprise", "C:\claude\amplifier", "C:\claude\universal-siem-monorepo")
                foreach ($dir in $searchDirs) {
                    if (Test-Path "$dir\.git") {
                        $branchCheck = & git -C $dir branch --list $Head 2>&1
                        if ($branchCheck -and $branchCheck.Trim()) {
                            $gitDir = $dir
                            break
                        }
                    }
                }
            }
            if (-not $gitDir) {
                throw "Could not find a git repo containing branch '$Head'. Pass -RepoDir or -Repo explicitly."
            }
        }
        $remoteUrl = & git -C $gitDir remote get-url origin 2>&1
        if ($LASTEXITCODE -ne 0) { throw "Failed to get origin remote URL from $gitDir" }
        # Parse: https://...@gitea.ergonet.pl:3001/owner/repo.git -> owner/repo
        # Also handles: https://gitea.ergonet.pl:3001/owner/repo.git
        if ($remoteUrl -match 'gitea\.ergonet\.pl:3001/(.+?)(?:\.git)?$') {
            $Repo = $Matches[1]
            Write-Host "Auto-detected repo: $Repo (from $gitDir)"
        } else {
            Write-Error "Could not detect Gitea repo from origin remote: $remoteUrl"
            Write-Error "Pass -Repo 'owner/repo' explicitly."
            exit 1
        }
    } catch {
        Write-Error "Failed to auto-detect repo. Error: $_"
        exit 1
    }
}

# Skip SSL validation (self-signed/internal cert)
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }

$uri = "$GiteaUrl/api/v1/repos/$Repo/pulls"

$payload = @{
    title = $Title
    head  = $Head
    base  = $Base
    body  = $Body
} | ConvertTo-Json -Compress

$headers = @{
    "Authorization" = "token $Token"
    "Content-Type"  = "application/json"
}

try {
    $response = Invoke-RestMethod -Uri $uri -Method Post -Headers $headers -Body $payload
    Write-Host "PR_NUMBER=$($response.number)"
    Write-Host "PR_URL=$($response.html_url)"
    Write-Host "PR created successfully: #$($response.number) - $($response.title)"
} catch {
    Write-Error "Failed to create PR: $_"
    exit 1
}
