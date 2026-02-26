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

# Auto-detect repo from git remote if not provided
if (-not $Repo) {
    try {
        # Use -RepoDir if provided, otherwise find repo from CWD or current branch context
        $gitDir = ""
        if ($RepoDir) {
            $gitDir = $RepoDir
        } else {
            # First try CWD
            $root = & git rev-parse --show-toplevel 2>&1
            if ($LASTEXITCODE -eq 0) {
                $gitDir = $root
            }
            # If CWD is not a git repo or doesn't have a Gitea remote, search common locations
            if ($gitDir) {
                $remoteCheck = & git -C $gitDir remote get-url origin 2>&1
                if ($remoteCheck -notmatch 'gitea\.ergonet\.pl:3001') {
                    $gitDir = ""
                }
            }
            if (-not $gitDir) {
                $searchDirs = @("C:\claude\fusecp-enterprise", "C:\claude\amplifier", "C:\claude\universal-siem-monorepo")
                foreach ($dir in $searchDirs) {
                    if (Test-Path "$dir\.git") {
                        $remoteCheck = & git -C $dir remote get-url origin 2>&1
                        if ($remoteCheck -match 'gitea\.ergonet\.pl:3001') {
                            # For merge, we need RepoDir to be explicit or contextual
                            # Use the repo that has a non-main branch checked out (likely the one being worked on)
                            $currentBranch = & git -C $dir rev-parse --abbrev-ref HEAD 2>&1
                            if ($currentBranch -and $currentBranch -ne "main" -and $currentBranch -ne "master") {
                                $gitDir = $dir
                                break
                            }
                        }
                    }
                }
            }
            # Last resort: just use the first Gitea-connected repo
            if (-not $gitDir) {
                $searchDirs = @("C:\claude\fusecp-enterprise", "C:\claude\amplifier", "C:\claude\universal-siem-monorepo")
                foreach ($dir in $searchDirs) {
                    if (Test-Path "$dir\.git") {
                        $remoteCheck = & git -C $dir remote get-url origin 2>&1
                        if ($remoteCheck -match 'gitea\.ergonet\.pl:3001') {
                            $gitDir = $dir
                            break
                        }
                    }
                }
            }
            if (-not $gitDir) {
                throw "Could not find a git repo with Gitea remote. Pass -RepoDir or -Repo explicitly."
            }
        }
        $remoteUrl = & git -C $gitDir remote get-url origin 2>&1
        if ($LASTEXITCODE -ne 0) { throw "Failed to get origin remote URL from $gitDir" }
        # Parse: https://...@gitea.ergonet.pl:3001/owner/repo.git -> owner/repo
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
