# Amplifier Plugin Marketplace Deployment Plan

> **For Claude:** REQUIRED: Use /subagent-dev to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Register `amplifier-plugins` as a Claude Code marketplace on Windows so all 6 plugins load natively.

**Architecture:** Clone the existing Gitea repo into `~/.claude/plugins/marketplaces/`, add a `marketplace.json` manifest that Claude Code expects, register in `known_marketplaces.json`, and enable plugins in `settings.json`. PowerShell-first.

**Tech Stack:** PowerShell 7, Git, Claude Code plugin system, Gitea MCP

---

## Task 1: Add marketplace.json to repo [TRACER]

**Agent:** modular-builder
**Model:** sonnet

This is the tracer bullet — creates the manifest that Claude Code needs to recognize the repo as a marketplace. Without this file, nothing else works.

**Files:**
- Create: `amplifier-plugins/.claude-plugin/marketplace.json` (via Gitea API)

- [ ] **Step 1: Create marketplace.json via Gitea MCP**

Use `mcp__gitea__create_file` to add `.claude-plugin/marketplace.json` to the repo root:

```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "amplifier-marketplace",
  "description": "Amplifier AI development platform — 36 agents, 47 commands, platform and project plugins",
  "owner": {
    "name": "Amplifier",
    "email": "cc@ergonet.pl"
  },
  "plugins": [
    {
      "name": "amplifier-core",
      "description": "Self-improving AI platform — 36 agents, 38 commands, effort steering, AutoContext evaluation",
      "version": "2026.03.18",
      "source": "./amplifier-core",
      "category": "development",
      "strict": false
    },
    {
      "name": "amplifier-windows",
      "description": "Windows platform plugin — paths, IIS, PowerShell, guard-paths for Windows Server",
      "version": "2026.03.18",
      "source": "./amplifier-windows",
      "category": "development",
      "strict": false
    },
    {
      "name": "amplifier-linux",
      "description": "Linux platform plugin — uv paths, Chrome headless, global MCP registration",
      "version": "2026.03.18",
      "source": "./amplifier-linux",
      "category": "development",
      "strict": false
    },
    {
      "name": "amplifier-fusecp",
      "description": "FuseCP project plugin — fix-bugs, test-verified commands, .NET/Blazor deployment",
      "version": "2026.03.18",
      "source": "./amplifier-fusecp",
      "category": "development",
      "strict": false
    },
    {
      "name": "amplifier-siem",
      "description": "Universal SIEM project plugin — test-siem command, Python pipeline testing",
      "version": "2026.03.18",
      "source": "./amplifier-siem",
      "category": "development",
      "strict": false
    },
    {
      "name": "amplifier-genetics",
      "description": "Genetics Platform project plugin — TypeScript/Tailwind/shadcn context",
      "version": "2026.03.18",
      "source": "./amplifier-genetics",
      "category": "development",
      "strict": false
    }
  ]
}
```

- [ ] **Step 2: Verify the file exists on Gitea**

Run: `mcp__gitea__get_file_content(owner="claude", repo="amplifier-plugins", ref="main", filePath=".claude-plugin/marketplace.json")`
Expected: 200 OK with the JSON content above.

---

## Task 2: Rewrite install.ps1 for proper marketplace registration

**Agent:** modular-builder
**Model:** sonnet

The current `install.ps1` clones to `~/.claude/plugins/cache/` which is the WRONG location. Real marketplaces go to `~/.claude/plugins/marketplaces/`. This task rewrites it.

**Files:**
- Modify: `amplifier-plugins/install.ps1` (via Gitea API — `mcp__gitea__update_file`)

- [ ] **Step 1: Update install.ps1 via Gitea MCP**

New content for `install.ps1`:

```powershell
#Requires -Version 5
# Amplifier Plugins — Windows Marketplace Installer
# Registers amplifier-plugins as a Claude Code marketplace.

$ErrorActionPreference = "Stop"

$MarketplaceUrl = "https://gitea.ergonet.pl:3001/claude/amplifier-plugins.git"
$ClaudeDir = Join-Path $env:USERPROFILE ".claude"
$PluginsDir = Join-Path $ClaudeDir "plugins"
$MarketplacesDir = Join-Path $PluginsDir "marketplaces"
$InstallDir = Join-Path $MarketplacesDir "amplifier-marketplace"
$KnownFile = Join-Path $PluginsDir "known_marketplaces.json"
$SettingsFile = Join-Path $ClaudeDir "settings.json"

Write-Host "=== Amplifier Plugin Marketplace Installer ===" -ForegroundColor Cyan

# --- Step 1: Clone or update marketplace repo ---
if (Test-Path (Join-Path $InstallDir ".git")) {
    Write-Host "Updating existing installation..."
    Push-Location $InstallDir
    git pull origin main --quiet
    Pop-Location
} else {
    Write-Host "Installing fresh..."
    New-Item -ItemType Directory -Force -Path $MarketplacesDir | Out-Null
    git clone $MarketplaceUrl $InstallDir --quiet
}

# --- Step 2: Register in known_marketplaces.json ---
$known = @{}
if (Test-Path $KnownFile) {
    $known = Get-Content $KnownFile -Raw | ConvertFrom-Json -AsHashtable
}

$known["amplifier-marketplace"] = @{
    source = @{
        source = "url"
        url    = $MarketplaceUrl
    }
    installLocation = $InstallDir
    lastUpdated     = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
}

$known | ConvertTo-Json -Depth 10 | Set-Content $KnownFile -Encoding UTF8
Write-Host "Registered in known_marketplaces.json" -ForegroundColor Green

# --- Step 3: Enable plugins in settings.json ---
$settings = @{}
if (Test-Path $SettingsFile) {
    $settings = Get-Content $SettingsFile -Raw | ConvertFrom-Json -AsHashtable
}

if (-not $settings.ContainsKey("enabledPlugins")) {
    $settings["enabledPlugins"] = @{}
}

# Enable core + platform (auto-detect Windows)
$pluginsToEnable = @(
    "amplifier-core@amplifier-marketplace"
    "amplifier-windows@amplifier-marketplace"
)

foreach ($plugin in $pluginsToEnable) {
    if (-not $settings["enabledPlugins"].ContainsKey($plugin)) {
        $settings["enabledPlugins"][$plugin] = $true
        Write-Host "  Enabled: $plugin" -ForegroundColor Green
    } else {
        Write-Host "  Already enabled: $plugin" -ForegroundColor Yellow
    }
}

$settings | ConvertTo-Json -Depth 10 | Set-Content $SettingsFile -Encoding UTF8

# --- Step 4: List installed plugins ---
Write-Host ""
Write-Host "Installed plugins:" -ForegroundColor Green
Get-ChildItem "$InstallDir\amplifier-*" -Directory | ForEach-Object {
    $manifest = Join-Path $_.FullName ".claude-plugin\plugin.json"
    if (Test-Path $manifest) {
        $json = Get-Content $manifest -Raw | ConvertFrom-Json
        $enabled = if ($settings["enabledPlugins"].ContainsKey("$($json.name)@amplifier-marketplace")) { "[ON]" } else { "[--]" }
        Write-Host "  $enabled $($json.name): $($json.description)"
    }
}

Write-Host ""
Write-Host "Done. Restart Claude Code or run /reload-plugins to activate." -ForegroundColor Green
Write-Host ""
Write-Host "To enable project plugins:" -ForegroundColor Cyan
Write-Host '  $s = gc ~/.claude/settings.json | ConvertFrom-Json -AsHashtable'
Write-Host '  $s.enabledPlugins["amplifier-fusecp@amplifier-marketplace"] = $true'
Write-Host '  $s | ConvertTo-Json -Depth 10 | sc ~/.claude/settings.json'
```

- [ ] **Step 2: Push the update via Gitea MCP**

Use `mcp__gitea__update_file` with the SHA of the current `install.ps1` (`8b813c2ddb19c891a85f7a3bbaf7907ef8e12440`).

- [ ] **Step 3: Verify the update**

Run: `mcp__gitea__get_file_content(owner="claude", repo="amplifier-plugins", ref="main", filePath="install.ps1")`
Expected: new content with `marketplaces` path and `known_marketplaces.json` registration.

---

## Task 3: Run installer and activate plugins

**Agent:** integration-specialist
**Model:** sonnet

This task runs the installer locally and verifies the marketplace is registered.

**Files:**
- Modify: `~/.claude/plugins/known_marketplaces.json`
- Modify: `~/.claude/settings.json`
- Create: `~/.claude/plugins/marketplaces/amplifier-marketplace/` (git clone)

- [ ] **Step 1: Remove stale local scaffold**

```powershell
# Remove the empty scaffold from earlier attempt
if (Test-Path "C:\claude\amplifier-plugins") {
    Remove-Item -Recurse -Force "C:\claude\amplifier-plugins"
}
```

- [ ] **Step 2: Run the installer**

```powershell
# Clone fresh and run
$tempDir = Join-Path $env:TEMP "amplifier-plugins-installer"
if (Test-Path $tempDir) { Remove-Item -Recurse -Force $tempDir }
git clone https://gitea.ergonet.pl:3001/claude/amplifier-plugins.git $tempDir
powershell -File "$tempDir\install.ps1"
```

- [ ] **Step 3: Verify marketplace registration**

```powershell
# Check known_marketplaces.json has the entry
$known = Get-Content "$env:USERPROFILE\.claude\plugins\known_marketplaces.json" -Raw | ConvertFrom-Json
$known.'amplifier-marketplace' | Format-List
```

Expected output: `source`, `installLocation`, `lastUpdated` fields present.

- [ ] **Step 4: Verify settings.json has enabled plugins**

```powershell
$settings = Get-Content "$env:USERPROFILE\.claude\settings.json" -Raw | ConvertFrom-Json
$settings.enabledPlugins | Get-Member -MemberType NoteProperty | Where-Object { $_.Name -match "amplifier" }
```

Expected: `amplifier-core@amplifier-marketplace` and `amplifier-windows@amplifier-marketplace` entries.

- [ ] **Step 5: Verify file structure**

```powershell
# Marketplace cloned correctly
Test-Path "$env:USERPROFILE\.claude\plugins\marketplaces\amplifier-marketplace\.claude-plugin\marketplace.json"
# Core plugin has agents
(Get-ChildItem "$env:USERPROFILE\.claude\plugins\marketplaces\amplifier-marketplace\amplifier-core\agents\*.md").Count
# Core plugin has commands
(Get-ChildItem "$env:USERPROFILE\.claude\plugins\marketplaces\amplifier-marketplace\amplifier-core\commands\*.md").Count
```

Expected: `True`, `36`, `38` (plus 8 in ddd/).

- [ ] **Step 6: Commit (no code change — this is local activation)**

No git commit needed — this is local configuration.

---

## Task 4: Enable project plugins and add .amplifier-project markers

**Agent:** modular-builder
**Model:** haiku

- [ ] **Step 1: Enable amplifier-fusecp plugin**

```powershell
$settings = Get-Content "$env:USERPROFILE\.claude\settings.json" -Raw | ConvertFrom-Json -AsHashtable
$settings["enabledPlugins"]["amplifier-fusecp@amplifier-marketplace"] = $true
$settings | ConvertTo-Json -Depth 10 | Set-Content "$env:USERPROFILE\.claude\settings.json" -Encoding UTF8
```

- [ ] **Step 2: Create .amplifier-project marker in FuseCP repo**

```powershell
Set-Content "C:\claude\fusecp-enterprise\.amplifier-project" "amplifier-fusecp" -NoNewline
```

- [ ] **Step 3: Create .amplifier-project marker in Amplifier repo (self-reference)**

```powershell
Set-Content "C:\claude\amplifier\.amplifier-project" "amplifier-core" -NoNewline
```

- [ ] **Step 4: Verify markers**

```powershell
Get-Content "C:\claude\fusecp-enterprise\.amplifier-project"
Get-Content "C:\claude\amplifier\.amplifier-project"
```

Expected: `amplifier-fusecp` and `amplifier-core`.

---

## Task 5: Verify plugins load in Claude Code

**Agent:** integration-specialist
**Model:** sonnet

This is the critical verification — do the plugins actually load?

- [ ] **Step 1: Restart Claude Code and check for plugin loading**

Exit the current Claude Code session and start a new one:

```bash
claude
```

- [ ] **Step 2: Check that amplifier-core commands appear**

In the new session, verify `/brainstorm` is available (it's an amplifier-core command).
Type `/brainstorm` — if it expands to the brainstorm prompt, the plugin is loaded.

- [ ] **Step 3: Check that agents are available**

Dispatch a test agent:
```
Agent(subagent_type="amplifier-expert", prompt="What is Amplifier?", description="test plugin agent")
```

If it dispatches successfully, agents from the plugin are loaded.

- [ ] **Step 4: Check platform plugin loaded**

The session should show Windows-specific content from `amplifier-windows/CLAUDE.md` in the context.

- [ ] **Step 5: If plugins don't load — debug**

Check these common failure points:
1. `marketplace.json` schema mismatch — compare with `claude-plugins-official` format
2. Plugin source paths — `./amplifier-core` must resolve relative to marketplace root
3. `known_marketplaces.json` — entry format must match exactly
4. `enabledPlugins` — key format must be `name@marketplace-name`

If Claude Code doesn't recognize the marketplace format, fall back to manual symlink:
```powershell
# Fallback: symlink plugins directly into .claude/
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.claude\agents" -Target "$env:USERPROFILE\.claude\plugins\marketplaces\amplifier-marketplace\amplifier-core\agents" -Force
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.claude\commands" -Target "$env:USERPROFILE\.claude\plugins\marketplaces\amplifier-marketplace\amplifier-core\commands" -Force
```

---

## Requirement Coverage

```
Requirement → Task Mapping:
  ✓ marketplace.json manifest         → Task 1
  ✓ install.ps1 rewrite               → Task 2
  ✓ Local installation + registration → Task 3
  ✓ Project markers                   → Task 4
  ✓ Verification                      → Task 5
  — Docs site path update             → DEFERRED (scope reduction)
  — Linux deployment                  → DEFERRED (scope reduction)
  — install.sh rewrite                → DEFERRED (scope reduction)
```

## Plan Quality Checklist

- [x] **Zero silent failures** — Task 5 has explicit debug steps if plugins don't load
- [x] **Every error has a name** — schema mismatch, path resolution, format errors listed
- [x] **Observability** — each step has verification commands with expected output
- [x] **Nothing deferred is vague** — docs site + Linux deferred with clear scope
- [x] **Scope mode honored** — REDUCTION: Windows only, no docs migration
