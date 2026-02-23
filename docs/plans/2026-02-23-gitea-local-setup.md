# Gitea Local Setup — Two-Stage Git Workflow

> **For Claude:** REQUIRED: Use /subagent-dev (if subagents available) or /execute-plan to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Install Gitea as the primary local git service with enterprise features, using GitHub as an always-current backup via push mirrors.

**Architecture:** Download Gitea binary → configure with SQLite on port 3001 → register as Windows service → migrate all 19 repos from GitHub → set up push mirrors back to GitHub → configure branch protection on all default branches → update local git remotes.

**Tech Stack:** Gitea 1.25.4, Windows Service (sc.exe), SQLite, GitHub API (gh CLI), PowerShell, Git Bash

---

## Repo Reference Table

| Repo | Default Branch | Private |
|------|---------------|---------|
| universal-siem-monorepo | main | yes |
| fusecp-enterprise | main | yes |
| heda-monorepo | main | yes |
| universal-siem-agent-aot | main | yes |
| amplifier | main | no |
| oscars | main | no |
| webpsmux | main | no |
| psmux | master | no |
| superpowers | main | no |
| ExchangeScripts | main | yes |
| genetics-platform | master | yes |
| claude-memory | main | yes |
| FuseCP | main | no |
| universal-siem-docs | main | yes |
| universal-siem-linux-agent | master | yes |
| universal-siem-agent | main | yes |
| claude-tools | develop | no |
| universal-siem-shared | master | yes |
| roslyn-tools-server | master | yes |

---

## Task 1: Download and Install Gitea Binary

**Agent:** `integration-specialist`

**Files:**
- Create: `C:\gitea\` (directory)
- Create: `C:\gitea\custom\conf\` (directory)
- Create: `C:\gitea\data\` (directory)
- Create: `C:\gitea\log\` (directory)
- Create: `C:\gitea\gitea.exe` (downloaded binary)

### Steps

- [ ] Create the Gitea directory structure:
  ```powershell
  New-Item -ItemType Directory -Force -Path C:\gitea
  New-Item -ItemType Directory -Force -Path C:\gitea\custom\conf
  New-Item -ItemType Directory -Force -Path C:\gitea\data
  New-Item -ItemType Directory -Force -Path C:\gitea\log
  ```
  Expected output: `Directory: C:\gitea` for each subdirectory.

- [ ] Download the Gitea binary:
  ```powershell
  Invoke-WebRequest `
    -Uri "https://dl.gitea.com/gitea/1.25.4/gitea-1.25.4-windows-4.0-amd64.exe" `
    -OutFile "C:\gitea\gitea.exe"
  ```
  Expected: File downloads without error. File size should be approximately 100–120 MB.

- [ ] Verify the binary version:
  ```bash
  /c/gitea/gitea.exe --version
  ```
  Expected output:
  ```
  Gitea version 1.25.4 built with GNU/Linux/...
  ```

- [ ] Commit progress note (no code files to commit at this stage — binary is not tracked in git).

---

## Task 2: Create app.ini Configuration

**Agent:** `modular-builder`

**Files:**
- Create: `C:\gitea\custom\conf\app.ini`

### Steps

- [ ] Create `C:\gitea\custom\conf\app.ini` with the following content:

  ```ini
  APP_NAME = Gitea — psklarkins Local
  RUN_MODE = prod
  RUN_USER = FUSECP$

  [server]
  HTTP_ADDR       = 0.0.0.0
  HTTP_PORT       = 3001
  ROOT_URL        = http://localhost:3001/
  DISABLE_SSH     = true
  OFFLINE_MODE    = false

  [database]
  DB_TYPE  = sqlite3
  PATH     = C:/gitea/data/gitea.db

  [repository]
  ROOT           = C:/gitea/data/gitea-repositories
  DEFAULT_BRANCH = main

  [mirror]
  ENABLED             = true
  DISABLE_NEW_PUSH    = false
  MIN_INTERVAL        = 1m
  DEFAULT_INTERVAL    = 10m

  [log]
  MODE      = file
  LEVEL     = Info
  ROOT_PATH = C:/gitea/log

  [service]
  DISABLE_REGISTRATION              = true
  REQUIRE_SIGNIN_VIEW               = false
  ENABLE_NOTIFY_MAIL                = false
  NO_REPLY_ADDRESS                  = noreply@localhost

  [security]
  INSTALL_LOCK   = false
  SECRET_KEY     = changeme_generate_on_first_run
  INTERNAL_TOKEN = changeme_generate_on_first_run

  [actions]
  ENABLED = false
  ```

  > **Note:** `INSTALL_LOCK = false` allows the initial web setup wizard to run. After completing setup via the web UI, Gitea will set this to `true` automatically and generate real `SECRET_KEY` and `INTERNAL_TOKEN` values.

- [ ] Verify the file exists and is readable:
  ```bash
  cat /c/gitea/custom/conf/app.ini | head -20
  ```
  Expected: First 20 lines of the config display correctly.

- [ ] Commit the configuration to the amplifier repo for reference:
  ```bash
  cp /c/gitea/custom/conf/app.ini /c/claude/amplifier/docs/plans/gitea-app.ini.reference
  cd /c/claude/amplifier
  git add docs/plans/gitea-app.ini.reference
  git commit -m "docs: add Gitea app.ini reference config"
  ```

---

## Task 3: Register and Start Gitea Windows Service

**Agent:** `integration-specialist`

**Files:**
- No new files — Windows service registration via `sc.exe`

### Steps

- [ ] Register Gitea as a Windows service:
  ```powershell
  sc.exe create gitea `
    start= auto `
    binPath= "\"C:\gitea\gitea.exe\" web --config \"C:\gitea\custom\conf\app.ini\"" `
    DisplayName= "Gitea - Git Service"
  ```
  Expected output:
  ```
  [SC] CreateService SUCCESS
  ```

- [ ] Set a description on the service (optional but recommended):
  ```powershell
  sc.exe description gitea "Gitea local git hosting service on port 3001"
  ```

- [ ] Start the service:
  ```powershell
  sc.exe start gitea
  ```
  Expected output:
  ```
  SERVICE_NAME: gitea
          TYPE               : 10  WIN32_OWN_PROCESS
          STATE              : 2  START_PENDING
  ```

- [ ] Wait 5 seconds, then verify the service is running:
  ```powershell
  Start-Sleep -Seconds 5
  sc.exe query gitea
  ```
  Expected: `STATE : 4  RUNNING`

- [ ] Verify Gitea responds on port 3001:
  ```bash
  curl -s -o /dev/null -w "%{http_code}" http://localhost:3001/
  ```
  Expected output: `200` (the initial setup wizard page).

- [ ] Complete the initial web setup by navigating to `http://localhost:3001/` in a browser or via API. Set:
  - **Database type:** SQLite3
  - **Site title:** Gitea — psklarkins Local
  - **Admin username:** `admin`
  - **Admin password:** (set a strong password, store in MEMORY.md)
  - **Admin email:** admin@localhost

  > **Note:** After completing setup, Gitea sets `INSTALL_LOCK = true` in app.ini. The service will need a restart if config was written during setup.

- [ ] Restart the service after initial setup to apply any config changes:
  ```powershell
  sc.exe stop gitea
  Start-Sleep -Seconds 3
  sc.exe start gitea
  Start-Sleep -Seconds 5
  sc.exe query gitea
  ```
  Expected: `STATE : 4  RUNNING`

- [ ] Verify the Gitea API is responding:
  ```bash
  curl -s "http://localhost:3001/api/v1/version"
  ```
  Expected output:
  ```json
  {"version":"1.25.4"}
  ```

---

## Task 4: Create GitHub Personal Access Token for Push Mirrors

**Agent:** `security-guardian`

**Files:**
- No files created — token stored in environment / Gitea secrets

### Steps

- [ ] Get the current GitHub CLI token (fine-grained or classic with `repo` scope):
  ```bash
  gh auth token
  ```
  Expected: Prints a token string (ghp_... or github_pat_...).

  > **Note:** If the current token does not have `repo` scope (required for mirroring private repos), create a new classic token at https://github.com/settings/tokens with scopes: `repo` (full), `workflow` (for workflow file push). Store the new token carefully.

- [ ] Verify the token works and has access to private repos:
  ```bash
  GH_TOKEN=$(gh auth token)
  curl -s -H "Authorization: token $GH_TOKEN" \
    "https://api.github.com/repos/psklarkins/fusecp-enterprise" \
    | grep '"private"'
  ```
  Expected output:
  ```
    "private": true,
  ```

- [ ] Verify the token works with all 19 repos (test one private, one public):
  ```bash
  GH_TOKEN=$(gh auth token)
  curl -s -H "Authorization: token $GH_TOKEN" \
    "https://api.github.com/repos/psklarkins/universal-siem-monorepo" \
    | grep '"name"'
  curl -s -H "Authorization: token $GH_TOKEN" \
    "https://api.github.com/repos/psklarkins/amplifier" \
    | grep '"name"'
  ```
  Expected: Both return `"name": "universal-siem-monorepo"` and `"name": "amplifier"` respectively.

- [ ] Store the token as an environment variable for use in subsequent tasks (do NOT commit to git):
  ```powershell
  [System.Environment]::SetEnvironmentVariable("GITEA_GH_PAT", (gh auth token), "Machine")
  ```
  This persists across reboots and makes the PAT available to scripts.

---

## Task 5: Create Migration Script — Import All 19 Repos from GitHub

**Agent:** `integration-specialist`

**Files:**
- Create: `C:\claude\scripts\gitea-migrate-repos.sh`

### Steps

- [ ] Create `C:\claude\scripts\gitea-migrate-repos.sh`:

  ```bash
  #!/usr/bin/env bash
  # gitea-migrate-repos.sh
  # Migrates all 19 psklarkins repos from GitHub into local Gitea instance.
  # Usage: GITEA_ADMIN_TOKEN=<token> GH_PAT=<pat> bash gitea-migrate-repos.sh

  set -euo pipefail

  GITEA_URL="http://localhost:3001"
  GITEA_ADMIN_TOKEN="${GITEA_ADMIN_TOKEN:-}"
  GH_PAT="${GH_PAT:-$(gh auth token 2>/dev/null || echo '')}"
  GITEA_OWNER="admin"

  if [[ -z "$GITEA_ADMIN_TOKEN" ]]; then
    echo "ERROR: GITEA_ADMIN_TOKEN is required. Generate one at http://localhost:3001/user/settings/applications"
    exit 1
  fi

  if [[ -z "$GH_PAT" ]]; then
    echo "ERROR: GH_PAT (GitHub Personal Access Token) is required."
    exit 1
  fi

  # repo_name:default_branch:is_private
  REPOS=(
    "universal-siem-monorepo:main:true"
    "fusecp-enterprise:main:true"
    "heda-monorepo:main:true"
    "universal-siem-agent-aot:main:true"
    "amplifier:main:false"
    "oscars:main:false"
    "webpsmux:main:false"
    "psmux:master:false"
    "superpowers:main:false"
    "ExchangeScripts:main:true"
    "genetics-platform:master:true"
    "claude-memory:main:true"
    "FuseCP:main:false"
    "universal-siem-docs:main:true"
    "universal-siem-linux-agent:master:true"
    "universal-siem-agent:main:true"
    "claude-tools:develop:false"
    "universal-siem-shared:master:true"
    "roslyn-tools-server:master:true"
  )

  SUCCESS=0
  FAILED=0

  for entry in "${REPOS[@]}"; do
    IFS=':' read -r repo_name default_branch is_private <<< "$entry"

    echo "==> Migrating $repo_name (branch: $default_branch, private: $is_private)..."

    HTTP_STATUS=$(curl -s -o /tmp/gitea_migrate_response.json -w "%{http_code}" \
      -X POST "$GITEA_URL/api/v1/repos/migrate" \
      -H "Authorization: token $GITEA_ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"clone_addr\": \"https://github.com/psklarkins/${repo_name}.git\",
        \"auth_token\": \"${GH_PAT}\",
        \"mirror\": false,
        \"private\": ${is_private},
        \"repo_name\": \"${repo_name}\",
        \"repo_owner\": \"${GITEA_OWNER}\",
        \"description\": \"Migrated from github.com/psklarkins/${repo_name}\"
      }")

    if [[ "$HTTP_STATUS" == "201" ]]; then
      echo "    OK: $repo_name migrated successfully."
      SUCCESS=$((SUCCESS + 1))
    elif [[ "$HTTP_STATUS" == "409" ]]; then
      echo "    SKIP: $repo_name already exists in Gitea."
      SUCCESS=$((SUCCESS + 1))
    else
      echo "    FAIL: $repo_name returned HTTP $HTTP_STATUS"
      cat /tmp/gitea_migrate_response.json
      FAILED=$((FAILED + 1))
    fi

    # Brief pause to avoid rate limiting
    sleep 2
  done

  echo ""
  echo "Migration complete: $SUCCESS succeeded, $FAILED failed."
  if [[ $FAILED -gt 0 ]]; then
    exit 1
  fi
  ```

- [ ] Make the script executable:
  ```bash
  chmod +x /c/claude/scripts/gitea-migrate-repos.sh
  ```

- [ ] Generate a Gitea admin API token:
  - Navigate to `http://localhost:3001/user/settings/applications`
  - Create a token named `migration-script` with all permissions
  - Copy the token value (shown only once)

- [ ] Run the migration script:
  ```bash
  GITEA_ADMIN_TOKEN="<paste-token-here>" \
  GH_PAT="$(gh auth token)" \
  bash /c/claude/scripts/gitea-migrate-repos.sh
  ```
  Expected output (each repo):
  ```
  ==> Migrating universal-siem-monorepo (branch: main, private: true)...
      OK: universal-siem-monorepo migrated successfully.
  ```
  Final line expected:
  ```
  Migration complete: 19 succeeded, 0 failed.
  ```

  > **Note:** Large repos (universal-siem-monorepo, fusecp-enterprise) may take several minutes to clone. The script uses `sleep 2` between repos to avoid GitHub rate limiting.

- [ ] Verify all 19 repos appear in Gitea:
  ```bash
  curl -s -H "Authorization: token $GITEA_ADMIN_TOKEN" \
    "http://localhost:3001/api/v1/repos/search?limit=50&uid=1" \
    | python3 -c "import sys,json; repos=json.load(sys.stdin)['data']; print(f'{len(repos)} repos found'); [print(f'  - {r[\"name\"]}') for r in repos]"
  ```
  Expected: `19 repos found` followed by all repo names.

- [ ] Commit the migration script:
  ```bash
  cd /c/claude
  git add scripts/gitea-migrate-repos.sh
  git commit -m "chore: add Gitea repo migration script (19 repos from psklarkins)"
  ```

---

## Task 6: Configure Push Mirrors for All Repos

**Agent:** `integration-specialist`

**Files:**
- Create: `C:\claude\scripts\gitea-push-mirrors.sh`

### Steps

- [ ] Create `C:\claude\scripts\gitea-push-mirrors.sh`:

  ```bash
  #!/usr/bin/env bash
  # gitea-push-mirrors.sh
  # Configures push mirrors from Gitea back to GitHub for all 19 repos.
  # Push mirrors sync on every commit and at DEFAULT_INTERVAL (10m).
  # Usage: GITEA_ADMIN_TOKEN=<token> GH_PAT=<pat> bash gitea-push-mirrors.sh

  set -euo pipefail

  GITEA_URL="http://localhost:3001"
  GITEA_ADMIN_TOKEN="${GITEA_ADMIN_TOKEN:-}"
  GH_PAT="${GH_PAT:-$(gh auth token 2>/dev/null || echo '')}"
  GITEA_OWNER="admin"
  GH_USER="psklarkins"

  if [[ -z "$GITEA_ADMIN_TOKEN" ]]; then
    echo "ERROR: GITEA_ADMIN_TOKEN is required."
    exit 1
  fi

  if [[ -z "$GH_PAT" ]]; then
    echo "ERROR: GH_PAT (GitHub Personal Access Token) is required."
    exit 1
  fi

  REPOS=(
    "universal-siem-monorepo"
    "fusecp-enterprise"
    "heda-monorepo"
    "universal-siem-agent-aot"
    "amplifier"
    "oscars"
    "webpsmux"
    "psmux"
    "superpowers"
    "ExchangeScripts"
    "genetics-platform"
    "claude-memory"
    "FuseCP"
    "universal-siem-docs"
    "universal-siem-linux-agent"
    "universal-siem-agent"
    "claude-tools"
    "universal-siem-shared"
    "roslyn-tools-server"
  )

  SUCCESS=0
  FAILED=0

  for repo in "${REPOS[@]}"; do
    echo "==> Configuring push mirror for $repo..."

    HTTP_STATUS=$(curl -s -o /tmp/gitea_mirror_response.json -w "%{http_code}" \
      -X POST "$GITEA_URL/api/v1/repos/${GITEA_OWNER}/${repo}/push_mirrors" \
      -H "Authorization: token $GITEA_ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"remote_address\": \"https://github.com/${GH_USER}/${repo}.git\",
        \"remote_username\": \"${GH_USER}\",
        \"remote_password\": \"${GH_PAT}\",
        \"interval\": \"10m\",
        \"sync_on_commit\": true
      }")

    if [[ "$HTTP_STATUS" == "200" || "$HTTP_STATUS" == "201" ]]; then
      echo "    OK: push mirror configured for $repo."
      SUCCESS=$((SUCCESS + 1))
    elif [[ "$HTTP_STATUS" == "409" ]]; then
      echo "    SKIP: push mirror already exists for $repo."
      SUCCESS=$((SUCCESS + 1))
    else
      echo "    FAIL: $repo returned HTTP $HTTP_STATUS"
      cat /tmp/gitea_mirror_response.json
      FAILED=$((FAILED + 1))
    fi

    sleep 1
  done

  echo ""
  echo "Push mirror setup: $SUCCESS succeeded, $FAILED failed."
  if [[ $FAILED -gt 0 ]]; then
    exit 1
  fi
  ```

- [ ] Make the script executable:
  ```bash
  chmod +x /c/claude/scripts/gitea-push-mirrors.sh
  ```

- [ ] Run the push mirror setup:
  ```bash
  GITEA_ADMIN_TOKEN="<paste-token-here>" \
  GH_PAT="$(gh auth token)" \
  bash /c/claude/scripts/gitea-push-mirrors.sh
  ```
  Expected output per repo:
  ```
  ==> Configuring push mirror for universal-siem-monorepo...
      OK: push mirror configured for universal-siem-monorepo.
  ```
  Final line expected:
  ```
  Push mirror setup: 19 succeeded, 0 failed.
  ```

- [ ] Trigger a manual sync on one repo and verify it reaches GitHub:
  ```bash
  # Trigger sync
  curl -s -X POST \
    -H "Authorization: token $GITEA_ADMIN_TOKEN" \
    "http://localhost:3001/api/v1/repos/admin/amplifier/push_mirrors-sync"

  # Wait 30 seconds, then check the amplifier repo on GitHub
  sleep 30
  gh api repos/psklarkins/amplifier --jq '.pushed_at'
  ```
  Expected: The `pushed_at` timestamp on GitHub updates to within the last minute.

- [ ] Commit the push mirrors script:
  ```bash
  cd /c/claude
  git add scripts/gitea-push-mirrors.sh
  git commit -m "chore: add Gitea push mirrors setup script (Gitea→GitHub backup)"
  ```

---

## Task 7: Configure Branch Protection on All Repos

**Agent:** `security-guardian`

**Files:**
- Create: `C:\claude\scripts\gitea-branch-protection.sh`

### Steps

- [ ] Create `C:\claude\scripts\gitea-branch-protection.sh`:

  ```bash
  #!/usr/bin/env bash
  # gitea-branch-protection.sh
  # Configures branch protection on all default branches.
  # Blocks direct push; requires PR. 0 approvals required (solo dev workflow).
  # Usage: GITEA_ADMIN_TOKEN=<token> bash gitea-branch-protection.sh

  set -euo pipefail

  GITEA_URL="http://localhost:3001"
  GITEA_ADMIN_TOKEN="${GITEA_ADMIN_TOKEN:-}"
  GITEA_OWNER="admin"

  if [[ -z "$GITEA_ADMIN_TOKEN" ]]; then
    echo "ERROR: GITEA_ADMIN_TOKEN is required."
    exit 1
  fi

  # repo_name:default_branch
  REPOS=(
    "universal-siem-monorepo:main"
    "fusecp-enterprise:main"
    "heda-monorepo:main"
    "universal-siem-agent-aot:main"
    "amplifier:main"
    "oscars:main"
    "webpsmux:main"
    "psmux:master"
    "superpowers:main"
    "ExchangeScripts:main"
    "genetics-platform:master"
    "claude-memory:main"
    "FuseCP:main"
    "universal-siem-docs:main"
    "universal-siem-linux-agent:master"
    "universal-siem-agent:main"
    "claude-tools:develop"
    "universal-siem-shared:master"
    "roslyn-tools-server:master"
  )

  SUCCESS=0
  FAILED=0

  for entry in "${REPOS[@]}"; do
    IFS=':' read -r repo branch <<< "$entry"

    echo "==> Protecting $repo ($branch)..."

    HTTP_STATUS=$(curl -s -o /tmp/gitea_protect_response.json -w "%{http_code}" \
      -X POST "$GITEA_URL/api/v1/repos/${GITEA_OWNER}/${repo}/branch_protections" \
      -H "Authorization: token $GITEA_ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"branch_name\": \"${branch}\",
        \"enable_push\": false,
        \"enable_push_whitelist\": false,
        \"enable_merge_whitelist\": false,
        \"enable_status_check\": false,
        \"require_signed_commits\": false,
        \"required_approvals\": 0,
        \"block_on_rejected_reviews\": false,
        \"block_on_official_review_requests\": false,
        \"dismiss_stale_approvals\": false
      }")

    if [[ "$HTTP_STATUS" == "200" || "$HTTP_STATUS" == "201" ]]; then
      echo "    OK: branch protection set on $repo/$branch."
      SUCCESS=$((SUCCESS + 1))
    elif [[ "$HTTP_STATUS" == "422" ]]; then
      echo "    SKIP: branch protection already exists on $repo/$branch."
      SUCCESS=$((SUCCESS + 1))
    else
      echo "    FAIL: $repo/$branch returned HTTP $HTTP_STATUS"
      cat /tmp/gitea_protect_response.json
      FAILED=$((FAILED + 1))
    fi

    sleep 1
  done

  echo ""
  echo "Branch protection: $SUCCESS succeeded, $FAILED failed."
  if [[ $FAILED -gt 0 ]]; then
    exit 1
  fi
  ```

- [ ] Make the script executable:
  ```bash
  chmod +x /c/claude/scripts/gitea-branch-protection.sh
  ```

- [ ] Run the branch protection script:
  ```bash
  GITEA_ADMIN_TOKEN="<paste-token-here>" \
  bash /c/claude/scripts/gitea-branch-protection.sh
  ```
  Expected final line:
  ```
  Branch protection: 19 succeeded, 0 failed.
  ```

- [ ] Verify protection is active on one repo (fusecp-enterprise/main):
  ```bash
  curl -s \
    -H "Authorization: token $GITEA_ADMIN_TOKEN" \
    "http://localhost:3001/api/v1/repos/admin/fusecp-enterprise/branch_protections" \
    | python3 -c "import sys,json; data=json.load(sys.stdin); [print(f'  - {r[\"branch_name\"]}: enable_push={r[\"enable_push\"]}') for r in data]"
  ```
  Expected output:
  ```
    - main: enable_push=False
  ```

- [ ] Commit the branch protection script:
  ```bash
  cd /c/claude
  git add scripts/gitea-branch-protection.sh
  git commit -m "chore: add Gitea branch protection setup script (all default branches)"
  ```

---

## Task 8: Update Local Git Remotes for All Cloned Repos

**Agent:** `integration-specialist`

**Files:**
- Create: `C:\claude\scripts\gitea-update-remotes.sh`

### Steps

- [ ] Identify which repos are currently cloned locally under `C:\claude\`:
  ```bash
  find /c/claude -maxdepth 2 -name ".git" -type d | sed 's|/.git||' | sort
  ```
  Expected: List of repo root directories (e.g., `/c/claude/amplifier`, `/c/claude/fusecp-enterprise`, etc.)

- [ ] Create `C:\claude\scripts\gitea-update-remotes.sh`:

  ```bash
  #!/usr/bin/env bash
  # gitea-update-remotes.sh
  # Updates git remotes in locally cloned repos:
  #   - Renames 'origin' to 'github' (preserves direct GitHub access)
  #   - Sets 'origin' to Gitea (new primary)
  # Usage: bash gitea-update-remotes.sh

  set -euo pipefail

  GITEA_URL="http://localhost:3001"
  GITEA_OWNER="admin"

  # Map of local path to Gitea repo name
  # Format: "local_path:gitea_repo_name"
  REPOS=(
    "/c/claude/amplifier:amplifier"
    "/c/claude/fusecp-enterprise:fusecp-enterprise"
    "/c/claude/universal-siem-monorepo:universal-siem-monorepo"
    "/c/claude/heda-monorepo:heda-monorepo"
    "/c/claude/psmux:psmux"
    "/c/claude/webpsmux:webpsmux"
    "/c/claude/oscars:oscars"
    "/c/claude/superpowers:superpowers"
    "/c/claude/universal-siem-agent:universal-siem-agent"
  )

  for entry in "${REPOS[@]}"; do
    IFS=':' read -r local_path repo_name <<< "$entry"

    if [[ ! -d "$local_path/.git" ]]; then
      echo "SKIP: $local_path is not a git repo (not cloned locally)."
      continue
    fi

    echo "==> Updating remotes for $local_path..."
    cd "$local_path"

    CURRENT_ORIGIN=$(git remote get-url origin 2>/dev/null || echo "")

    if [[ -z "$CURRENT_ORIGIN" ]]; then
      echo "    WARN: No 'origin' remote found. Setting Gitea as origin."
      git remote add origin "${GITEA_URL}/${GITEA_OWNER}/${repo_name}.git"
    elif echo "$CURRENT_ORIGIN" | grep -q "localhost:3001"; then
      echo "    SKIP: origin already points to Gitea."
    else
      # origin points to GitHub — rename it, add Gitea as new origin
      echo "    Renaming origin → github..."
      git remote rename origin github 2>/dev/null || git remote set-url github "$CURRENT_ORIGIN"

      echo "    Adding Gitea as origin..."
      git remote add origin "${GITEA_URL}/${GITEA_OWNER}/${repo_name}.git"
    fi

    # Ensure github remote has correct push URL (explicit HTTPS)
    GITHUB_URL="https://github.com/psklarkins/${repo_name}.git"
    if git remote get-url github &>/dev/null; then
      git remote set-url --push github "$GITHUB_URL"
    fi

    echo "    Remotes after update:"
    git remote -v | sed 's/^/      /'
    echo ""
  done

  echo "Remote update complete."
  ```

- [ ] Make the script executable:
  ```bash
  chmod +x /c/claude/scripts/gitea-update-remotes.sh
  ```

- [ ] Run the remote update script:
  ```bash
  bash /c/claude/scripts/gitea-update-remotes.sh
  ```
  Expected output per repo (example for amplifier):
  ```
  ==> Updating remotes for /c/claude/amplifier...
      Renaming origin → github...
      Adding Gitea as origin...
      Remotes after update:
        github  https://github.com/psklarkins/amplifier.git (fetch)
        github  https://github.com/psklarkins/amplifier.git (push)
        origin  http://localhost:3001/admin/amplifier.git (fetch)
        origin  http://localhost:3001/admin/amplifier.git (push)

  Remote update complete.
  ```

- [ ] Manually verify one repo (amplifier):
  ```bash
  cd /c/claude/amplifier && git remote -v
  ```
  Expected:
  ```
  github  https://github.com/psklarkins/amplifier.git (fetch)
  github  https://github.com/psklarkins/amplifier.git (push)
  origin  http://localhost:3001/admin/amplifier.git (fetch)
  origin  http://localhost:3001/admin/amplifier.git (push)
  ```

- [ ] Test fetch from new origin (Gitea):
  ```bash
  cd /c/claude/amplifier && git fetch origin
  ```
  Expected: No errors; Gitea responds with branch info.

- [ ] Commit the remote update script:
  ```bash
  cd /c/claude
  git add scripts/gitea-update-remotes.sh
  git commit -m "chore: add Gitea remote update script (sets origin=Gitea, github=GitHub)"
  ```

---

## Task 9: Update Amplifier Workflow Docs

**Agent:** `modular-builder`

**Files:**
- Modify: `C:\claude\amplifier\AGENTS.md` — Add "Git Workflow" section
- Modify: `C:\Users\Administrator.ERGOLAB\.claude\projects\C--claude-amplifier\memory\MEMORY.md` — Add Gitea service info

### Steps

- [ ] Add a "Git Workflow" section to `C:\claude\amplifier\AGENTS.md` after the CI/CD Policy section:

  ```markdown
  ## Git Workflow — Gitea-First (Two-Stage)

  **PRIMARY remote**: Gitea at http://localhost:3001/ (port 3001)
  **BACKUP remote**: GitHub at https://github.com/psklarkins/ (push mirror, auto-syncs on commit)

  ### Remote Layout (all locally cloned repos)
  - `origin` → Gitea (primary, all day-to-day pushes go here)
  - `github` → GitHub (backup, never push manually — Gitea mirrors automatically)

  ### Daily Workflow
  1. Work and commit locally as usual
  2. Push to `origin` (Gitea): `git push origin feature/my-feature`
  3. Open PR on Gitea: http://localhost:3001/admin/{repo}/pulls
  4. Merge PR on Gitea — push mirror triggers GitHub backup automatically
  5. Never push directly to `main`/`master`/`develop` — branch protection enforced

  ### Branch Protection Rules (all 19 repos)
  - Direct push to default branch is BLOCKED
  - PR is required to merge
  - 0 approvals required (solo dev)
  - Status checks: disabled (no CI configured on Gitea yet)

  ### GitHub Actions
  - GitHub Actions runner at C:\actions-runner\ still runs CI on GitHub
  - When Gitea push mirror syncs, GitHub Actions fires on the mirrored commits
  - This provides CI coverage without needing Gitea Actions
  ```

- [ ] Add Gitea info to MEMORY.md under a new "## Gitea Local Git Service" section:

  ```markdown
  ## Gitea Local Git Service (installed 2026-02-23)
  - **URL**: http://localhost:3001/
  - **Service**: Windows service `gitea` (sc.exe, auto-start)
  - **Version**: 1.25.4
  - **Install dir**: `C:\gitea\`
  - **Config**: `C:\gitea\custom\conf\app.ini`
  - **Data/DB**: `C:\gitea\data\gitea.db` (SQLite)
  - **Repos**: `C:\gitea\data\gitea-repositories\`
  - **Logs**: `C:\gitea\log\`
  - **Admin user**: `admin` (password stored separately)
  - **Repos hosted**: 19 (all psklarkins repos)
  - **Push mirrors**: All 19 repos mirror back to GitHub on commit + every 10 min
  - **Branch protection**: All default branches (main/master/develop) — PR required, 0 approvals
  - **Scripts**: `C:\claude\scripts\gitea-*.sh`
  - **Port conflict note**: Port 3000 is taken by OpenCode observability (Node.js)
  ```

- [ ] Commit the documentation updates:
  ```bash
  cd /c/claude/amplifier
  git add AGENTS.md
  git commit -m "docs: add Gitea-first git workflow documentation to AGENTS.md"
  ```

---

## Task 10: Verification and Smoke Test

**Agent:** `integration-specialist`

**Files:**
- No new files — verification only

### Steps

- [ ] **Test 1: Push a test commit via Gitea and verify it reaches GitHub**

  ```bash
  # Create a test branch in amplifier repo
  cd /c/claude/amplifier
  git checkout -b test/gitea-push-mirror-$(date +%Y%m%d)
  echo "# Gitea push mirror test $(date)" >> /c/claude/amplifier/docs/plans/gitea-smoke-test.txt
  git add docs/plans/gitea-smoke-test.txt
  git commit -m "test: Gitea push mirror smoke test"

  # Push to Gitea (new origin)
  git push origin test/gitea-push-mirror-$(date +%Y%m%d)
  ```
  Expected: Push succeeds with `Branch 'test/...' set up to track remote branch`.

- [ ] Wait up to 60 seconds, then verify the branch appeared on GitHub:
  ```bash
  sleep 30
  gh api repos/psklarkins/amplifier/branches \
    --jq '.[] | select(.name | startswith("test/gitea")) | .name'
  ```
  Expected: The test branch name is printed, confirming push mirror synced.

- [ ] Clean up the test branch (on both remotes):
  ```bash
  cd /c/claude/amplifier
  git push origin --delete test/gitea-push-mirror-$(date +%Y%m%d)
  git checkout main
  git branch -d test/gitea-push-mirror-$(date +%Y%m%d) 2>/dev/null || true
  ```

- [ ] **Test 2: Verify branch protection blocks direct push to main**

  ```bash
  cd /c/claude/amplifier
  git push origin main
  ```
  Expected: Push is REJECTED with an error like:
  ```
  remote: Branch is protected by a rule.
  ! [remote rejected] main -> main (protected)
  error: failed to push some refs to 'http://localhost:3001/admin/amplifier.git'
  ```

- [ ] **Test 3: Verify PR workflow on Gitea**

  - Create a feature branch:
    ```bash
    cd /c/claude/amplifier
    git checkout -b test/pr-workflow-$(date +%Y%m%d)
    echo "PR workflow test" >> /tmp/pr-test.txt
    git add /tmp/pr-test.txt 2>/dev/null || echo "file not in repo, skipping"
    git commit --allow-empty -m "test: PR workflow verification"
    git push origin test/pr-workflow-$(date +%Y%m%d)
    ```
  - Open a PR via Gitea API:
    ```bash
    curl -s -X POST \
      -H "Authorization: token $GITEA_ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      "http://localhost:3001/api/v1/repos/admin/amplifier/pulls" \
      -d "{
        \"title\": \"Test PR — Gitea workflow verification\",
        \"head\": \"test/pr-workflow-$(date +%Y%m%d)\",
        \"base\": \"main\",
        \"body\": \"Smoke test PR to verify Gitea branch protection and PR workflow.\"
      }" | python3 -c "import sys,json; pr=json.load(sys.stdin); print(f'PR #{pr[\"number\"]}: {pr[\"html_url\"]}')"
    ```
    Expected: `PR #1: http://localhost:3001/admin/amplifier/pulls/1`
  - Merge via Gitea API:
    ```bash
    PR_NUM=1  # replace with actual PR number
    curl -s -X POST \
      -H "Authorization: token $GITEA_ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      "http://localhost:3001/api/v1/repos/admin/amplifier/pulls/${PR_NUM}/merge" \
      -d '{"Do":"merge","merge_message_field":"Merge test PR — smoke test"}'
    ```
    Expected: HTTP 200, PR merged.

- [ ] **Test 4: Verify Gitea service survives a restart**
  ```powershell
  Restart-Service gitea
  Start-Sleep -Seconds 10
  sc.exe query gitea
  ```
  Expected: `STATE : 4  RUNNING`
  ```bash
  curl -s "http://localhost:3001/api/v1/version"
  ```
  Expected: `{"version":"1.25.4"}`

- [ ] **Document any issues encountered** in `C:\claude\amplifier\docs\plans\gitea-issues.md` if any test fails.

- [ ] Final commit to mark plan complete:
  ```bash
  cd /c/claude/amplifier
  git add docs/plans/
  git commit -m "docs: Gitea setup smoke test results and verification complete"
  ```

---

## Reference: Gitea Admin Token Generation

After completing initial setup, generate a long-lived API token for scripts:

1. Navigate to `http://localhost:3001/user/settings/applications`
2. Token Name: `admin-scripts`
3. Expiration: None (or 1 year)
4. Scopes: All (or at minimum: `repo`, `admin:repo_hook`, `admin:org`)
5. Click "Generate Token" — copy immediately (shown once)

Store as machine-level environment variable:
```powershell
[System.Environment]::SetEnvironmentVariable("GITEA_ADMIN_TOKEN", "<token>", "Machine")
```

---

## Troubleshooting

### Gitea service fails to start
```powershell
# Check Windows Event Log
Get-EventLog -LogName Application -Source "gitea" -Newest 10

# Check Gitea log directly
Get-Content C:\gitea\log\gitea.log -Tail 50
```

### Port 3001 already in use
```powershell
netstat -ano | findstr :3001
# Kill the conflicting process by PID if needed
```

### Push mirror not syncing
```bash
# Check mirror status via API
curl -s -H "Authorization: token $GITEA_ADMIN_TOKEN" \
  "http://localhost:3001/api/v1/repos/admin/amplifier/push_mirrors" \
  | python3 -m json.tool

# Trigger manual sync
curl -s -X POST \
  -H "Authorization: token $GITEA_ADMIN_TOKEN" \
  "http://localhost:3001/api/v1/repos/admin/amplifier/push_mirrors-sync"
```

### Migration fails for a repo
```bash
# Check if repo already exists
curl -s -H "Authorization: token $GITEA_ADMIN_TOKEN" \
  "http://localhost:3001/api/v1/repos/admin/{repo_name}"

# Delete and re-migrate if needed
curl -s -X DELETE -H "Authorization: token $GITEA_ADMIN_TOKEN" \
  "http://localhost:3001/api/v1/repos/admin/{repo_name}"
```

### RUN_USER error on service start
If Gitea fails with `RUN_USER` mismatch, update `app.ini`:
```ini
RUN_USER = Administrator
```
Or use the machine account name as shown by `whoami` in PowerShell.
