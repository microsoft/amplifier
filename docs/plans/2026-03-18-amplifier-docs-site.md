# Amplifier Documentation Site — Implementation Plan

> **For Claude:** REQUIRED: Use /subagent-dev to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a self-updating bilingual documentation website at https://amplifier.ergonet.pl with intelligent incremental regeneration, unified design system, and LLM-consumable data layer.

**Architecture:** Static HTML site served by IIS, generated via claude --headless with visual-explainer prompts. Gitea webhook triggers regeneration on PR merge. Page-level manifest tracks source dependencies for incremental updates. Bilingual EN/PL with AI translation.

**Tech Stack:** IIS (static site), PowerShell (webhook listener + orchestrator), claude --headless (page generation), Gitea webhook (trigger), HTML/CSS/JS (output)

---

## Task 1 [TRACER]: Infrastructure — DNS + IIS + Smoke Test Page

**Agent:** modular-builder

This is the tracer bullet. Proves the full path works: DNS → IIS → HTTPS → browser.

**Files:**
- Create: `C:\claude\amplifier-docs\en\index.html`
- Create: `C:\claude\amplifier-docs\pl\index.html`
- Create: IIS site `Amplifier_Docs` and app pool `Amplifier_Docs`
- Create: DNS A record `amplifier.ergonet.pl` → `172.31.251.100`

**Steps:**

- [ ] 1. Create the full directory structure under `C:\claude\amplifier-docs\`:
  ```powershell
  New-Item -ItemType Directory -Force -Path @(
    "C:\claude\amplifier-docs\en\deep-dives",
    "C:\claude\amplifier-docs\en\platform",
    "C:\claude\amplifier-docs\en\projects",
    "C:\claude\amplifier-docs\en\sessions\archive",
    "C:\claude\amplifier-docs\pl\deep-dives",
    "C:\claude\amplifier-docs\pl\platform",
    "C:\claude\amplifier-docs\pl\projects",
    "C:\claude\amplifier-docs\pl\sessions\archive",
    "C:\claude\amplifier-docs\assets",
    "C:\claude\amplifier-docs\prompts",
    "C:\claude\amplifier-docs\logs"
  )
  ```
  Expected output: directory creation confirmations for all paths.

- [ ] 2. Create a minimal smoke test page at `C:\claude\amplifier-docs\en\index.html`:
  ```html
  <!DOCTYPE html>
  <html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Amplifier Docs</title>
    <style>
      body { background: #0b1120; color: #e5e7eb; font-family: sans-serif;
             display: flex; align-items: center; justify-content: center;
             height: 100vh; margin: 0; }
      h1 { color: #d4a73a; }
    </style>
  </head>
  <body>
    <div><h1>Amplifier Docs</h1><p>Site is live. Full content generating...</p></div>
  </body>
  </html>
  ```

- [ ] 3. Create a matching PL smoke page at `C:\claude\amplifier-docs\pl\index.html` — same structure with text "Witryna działa. Treść jest generowana..."

- [ ] 4. Add DNS A record on FINALTEST (172.31.251.101) via PowerShell remoting:
  ```powershell
  Invoke-Command -ComputerName 172.31.251.101 -ScriptBlock {
    Add-DnsServerResourceRecordA -Name "amplifier" -ZoneName "ergonet.pl" -IPv4Address "172.31.251.100" -TimeToLive 00:05:00
  }
  ```
  Expected output: no error. Verify with: `Resolve-DnsName amplifier.ergonet.pl -Server 172.31.251.101` → should return `172.31.251.100`.

- [ ] 5. Create IIS app pool with No Managed Code:
  ```powershell
  Import-Module WebAdministration
  New-WebAppPool -Name "Amplifier_Docs"
  Set-ItemProperty "IIS:\AppPools\Amplifier_Docs" -Name managedRuntimeVersion -Value ""
  Set-ItemProperty "IIS:\AppPools\Amplifier_Docs" -Name startMode -Value "AlwaysRunning"
  ```
  Expected output: app pool created, visible in `Get-WebAppPool -Name "Amplifier_Docs"`.

- [ ] 6. Create IIS site with HTTPS binding using the wildcard cert (`*.ergonet.pl`):
  ```powershell
  # Find wildcard cert thumbprint
  $cert = Get-ChildItem Cert:\LocalMachine\My | Where-Object { $_.Subject -like "*ergonet.pl*" } | Select-Object -First 1

  # Create site
  New-Website -Name "Amplifier_Docs" `
    -PhysicalPath "C:\claude\amplifier-docs" `
    -ApplicationPool "Amplifier_Docs" `
    -Port 443 `
    -Ssl

  # Bind wildcard cert to site on SNI
  New-WebBinding -Name "Amplifier_Docs" -Protocol https -Port 443 -HostHeader "amplifier.ergonet.pl" -SslFlags 1
  $binding = Get-WebBinding -Name "Amplifier_Docs" -Protocol https -Port 443 -HostHeader "amplifier.ergonet.pl"
  $binding.AddSslCertificate($cert.Thumbprint, "My")
  ```
  Expected: site created, binding visible in `Get-WebBinding -Name "Amplifier_Docs"`.

- [ ] 7. Add URL Rewrite rule so bare `/` redirects to `/en/index.html`. Create `C:\claude\amplifier-docs\web.config`:
  ```xml
  <?xml version="1.0" encoding="UTF-8"?>
  <configuration>
    <system.webServer>
      <defaultDocument>
        <files>
          <add value="en/index.html" />
        </files>
      </defaultDocument>
      <rewrite>
        <rules>
          <rule name="Root to EN" stopProcessing="true">
            <match url="^$" />
            <action type="Redirect" url="/en/index.html" redirectType="Temporary" />
          </rule>
        </rules>
      </rewrite>
      <staticContent>
        <mimeMap fileExtension=".json" mimeType="application/json" />
        <mimeMap fileExtension=".txt" mimeType="text/plain" />
      </staticContent>
    </system.webServer>
  </configuration>
  ```

- [ ] 8. Test end-to-end:
  ```bash
  curl -sk https://amplifier.ergonet.pl
  ```
  Expected output: HTML containing "Amplifier Docs" and "Site is live". If redirect occurs, follow with `-L` flag. HTTP status must be 200.

- [ ] 9. Commit smoke test pages and web.config:
  ```bash
  cd /c/claude/amplifier-docs
  git init
  git add en/index.html pl/index.html web.config
  git commit -m "feat: add smoke test pages and IIS web.config

  Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
  ```

---

## Task 2: Design System + Shared Navigation

**Agent:** modular-builder

**Files:**
- Create: `C:\claude\amplifier-docs\prompts\_design-system.md`
- Create: `C:\claude\amplifier-docs\assets\nav.html`
- Create: `C:\claude\amplifier-docs\prompts\_translate.md`

**Steps:**

- [ ] 1. Create `C:\claude\amplifier-docs\prompts\_design-system.md` — the master design system prompt document. This file is prepended to every page generation prompt. It must contain:

  **CSS custom properties** for both dark (default) and light themes:
  ```css
  :root {
    --bg: #0b1120;
    --surface: #111827;
    --surface2: #1a2235;
    --gold: #d4a73a;
    --gold-dim: #a07828;
    --teal: #0891b2;
    --coral: #e07050;
    --text: #e5e7eb;
    --text-dim: #9ca3af;
    --border: rgba(212,167,58,0.15);
    --sidebar-w: 260px;
    --radius: 8px;
    --transition: 0.2s ease;
  }
  @media (prefers-color-scheme: light) {
    :root {
      --bg: #f8f9fa; --surface: #ffffff; --surface2: #f1f5f9;
      --text: #1a2235; --text-dim: #6b7280; --border: rgba(11,17,32,0.12);
    }
  }
  ```

  **Font imports** (Google Fonts CDN, preconnect):
  ```html
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@400;500;600;700&family=Fragment+Mono&display=swap" rel="stylesheet">
  ```

  **Sidebar HTML template** — 260px fixed left panel containing:
  - Site logo/name "Amplifier" in gold
  - Language switcher: EN | PL toggle links (swap `/en/` ↔ `/pl/` in current URL via JS)
  - Navigation sections: Home, Manual, Commands, Agents, Deep Dives (expandable: Self-Improvement, Effort Steering, AutoContext, Workflows), Platform (expandable: Overview, Linux, Windows), Projects (expandable: FuseCP, Genetics, SIEM, Amplifier), Roadmap, Sessions
  - Active page highlighted in gold
  - Hamburger button visible only on mobile (< 768px)
  - Footer: "Last updated: {DATE}" in dim text

  **Scroll spy JavaScript** — highlights the correct nav link as user scrolls through sections.

  **Card/section component CSS patterns**:
  - `.card` — surface bg, border, radius, hover lift (translateY -2px)
  - `.section-label` — gold uppercase tracking-wide text
  - `.badge` — small pill with role color coding: scout=teal, implement=blue, architect=gold, review=green, security=red, fast=gray
  - `.command-card` — grid card with name, description, category badge
  - `.agent-card` — grid card with model tier badge, turn budget

  **Animation keyframes**:
  ```css
  @keyframes fadeUp { from { opacity:0; transform:translateY(16px) } to { opacity:1; transform:translateY(0) } }
  @keyframes fadeScale { from { opacity:0; transform:scale(0.96) } to { opacity:1; transform:scale(1) } }
  ```

  **Responsive breakpoints**: sidebar collapses at 768px, hamburger appears, overlay on open.

  **LLM metadata script template** — every generated page must include:
  ```html
  <script type="application/llm+json">
  {
    "page": "{PAGE_ID}",
    "title": "{TITLE}",
    "purpose": "{ONE_LINE_PURPOSE}",
    "key_concepts": ["{CONCEPT1}", "{CONCEPT2}"],
    "source_files": ["{SOURCE1}", "{SOURCE2}"],
    "related_pages": ["{REL1}", "{REL2}"],
    "last_updated": "{ISO_DATE}"
  }
  </script>
  ```

  **Footer** with version + last-updated:
  ```html
  <footer class="site-footer">
    <span>Amplifier Docs</span>
    <span class="text-dim">Generated: {DATE}</span>
  </footer>
  ```

  The document closes with an instruction block: "Follow every CSS token, font, component pattern, and structural template above exactly. Do not invent new color values. Do not omit the LLM metadata script. Do not omit the sidebar navigation."

- [ ] 2. Create `C:\claude\amplifier-docs\assets\nav.html` — standalone sidebar HTML fragment (same sidebar markup as in design system, for direct reference by agents). This is a plain HTML fragment (no `<html>` wrapper), just the `<nav>` element with all links populated.

- [ ] 3. Create `C:\claude\amplifier-docs\prompts\_translate.md` — the reusable translation prompt template:
  ```
  You are a Polish technical translator. You will receive an English HTML documentation page and translate it to Polish.

  Rules:
  - Translate ALL visible text content to Polish using proper Polish technical terminology
  - Preserve ALL HTML structure, CSS classes, and JavaScript unchanged
  - Preserve ALL code blocks exactly as-is (do not translate code)
  - Preserve ALL command names (e.g., /brainstorm, /self-eval) unchanged
  - Preserve ALL file paths and directory names unchanged
  - Preserve ALL agent names, model names, and tool names unchanged
  - Preserve ALL URLs unchanged
  - Update the <html lang="en"> attribute to <html lang="pl">
  - Update the language switcher to reflect current language is PL, link target is EN
  - Update the LLM metadata: add "language": "pl" field
  - Common translations: "Agent" = "Agent", "Commands" = "Komendy", "Workflow" = "Przepływ pracy",
    "Platform" = "Platforma", "Session" = "Sesja", "Manual" = "Podręcznik"

  Input: {EN_FILE_PATH}
  Output: {PL_FILE_PATH}

  Read the EN file, translate, and write the PL file.
  ```

- [ ] 4. Commit all:
  ```bash
  git add prompts/_design-system.md prompts/_translate.md assets/nav.html
  git commit -m "feat: add design system prompt and navigation template

  Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
  ```

---

## Task 3: Manifest System + Generate.ps1 Orchestrator

**Agent:** modular-builder

**Files:**
- Create: `C:\claude\amplifier-docs\manifest.json`
- Create: `C:\claude\amplifier-docs\generate.ps1`

**Steps:**

- [ ] 1. Create `C:\claude\amplifier-docs\manifest.json` with all pages, source globs, and empty hashes:
  ```json
  {
    "version": 1,
    "amplifier_root": "C:\\claude\\amplifier",
    "output_root": "C:\\claude\\amplifier-docs",
    "global_triggers": [
      "assets/nav.html",
      "prompts/_design-system.md"
    ],
    "pages": [
      {
        "id": "home",
        "en_output": "en/index.html",
        "pl_output": "pl/index.html",
        "prompt": "prompts/home.md",
        "sources": ["CLAUDE.md", "AGENTS.md", "config/routing-matrix.yaml"]
      },
      {
        "id": "manual",
        "en_output": "en/manual.html",
        "pl_output": "pl/manual.html",
        "prompt": "prompts/manual.md",
        "sources": ["CLAUDE.md", "AGENTS.md", "docs/guides/*.md", "ai_context/claude_code/*.md"]
      },
      {
        "id": "commands",
        "en_output": "en/commands.html",
        "pl_output": "pl/commands.html",
        "prompt": "prompts/commands.md",
        "sources": [".claude/commands/**/*.md", "config/routing-matrix.yaml"]
      },
      {
        "id": "agents",
        "en_output": "en/agents.html",
        "pl_output": "pl/agents.html",
        "prompt": "prompts/agents.md",
        "sources": [".claude/agents/**/*.md", "config/routing-matrix.yaml"]
      },
      {
        "id": "deep-dive-self-improvement",
        "en_output": "en/deep-dives/self-improvement.html",
        "pl_output": "pl/deep-dives/self-improvement.html",
        "prompt": "prompts/deep-dive-self-improvement.md",
        "sources": [".claude/commands/self-eval.md", ".claude/commands/self-improve.md", ".claude/commands/evaluate.md", ".claude/commands/improve.md", ".claude/commands/optimize-skill.md", ".claude/commands/solve.md"]
      },
      {
        "id": "deep-dive-effort-steering",
        "en_output": "en/deep-dives/effort-steering.html",
        "pl_output": "pl/deep-dives/effort-steering.html",
        "prompt": "prompts/deep-dive-effort-steering.md",
        "sources": ["config/routing-matrix.yaml", "AGENTS.md"]
      },
      {
        "id": "deep-dive-autocontext",
        "en_output": "en/deep-dives/autocontext.html",
        "pl_output": "pl/deep-dives/autocontext.html",
        "prompt": "prompts/deep-dive-autocontext.md",
        "sources": [".mcp.json", ".claude/commands/evaluate.md", ".claude/commands/solve.md", ".claude/commands/optimize-skill.md"]
      },
      {
        "id": "deep-dive-workflows",
        "en_output": "en/deep-dives/workflows.html",
        "pl_output": "pl/deep-dives/workflows.html",
        "prompt": "prompts/deep-dive-workflows.md",
        "sources": [".claude/commands/brainstorm.md", ".claude/commands/create-plan.md", ".claude/commands/subagent-dev.md", ".claude/commands/debug.md", ".claude/commands/tdd.md", ".claude/commands/verify.md", ".claude/commands/finish-branch.md"]
      },
      {
        "id": "platform-overview",
        "en_output": "en/platform/index.html",
        "pl_output": "pl/platform/index.html",
        "prompt": "prompts/platform-overview.md",
        "sources": ["CLAUDE.md", "AGENTS.md", "scripts/setup-platform-config.sh"]
      },
      {
        "id": "platform-linux",
        "en_output": "en/platform/linux.html",
        "pl_output": "pl/platform/linux.html",
        "prompt": "prompts/platform-linux.md",
        "sources": ["CLAUDE.md", "scripts/setup-platform-config.sh", "ai_context/claude_code/*.md"]
      },
      {
        "id": "platform-windows",
        "en_output": "en/platform/windows.html",
        "pl_output": "pl/platform/windows.html",
        "prompt": "prompts/platform-windows.md",
        "sources": ["CLAUDE.md", "scripts/guard-paths.sh"]
      },
      {
        "id": "projects-index",
        "en_output": "en/projects/index.html",
        "pl_output": "pl/projects/index.html",
        "prompt": "prompts/projects-index.md",
        "sources": ["CLAUDE.md", "AGENTS.md"]
      },
      {
        "id": "project-fusecp",
        "en_output": "en/projects/fusecp.html",
        "pl_output": "pl/projects/fusecp.html",
        "prompt": "prompts/project-fusecp.md",
        "sources": ["CLAUDE.md", "AGENTS.md"]
      },
      {
        "id": "project-genetics",
        "en_output": "en/projects/genetics.html",
        "pl_output": "pl/projects/genetics.html",
        "prompt": "prompts/project-genetics.md",
        "sources": ["CLAUDE.md", "AGENTS.md"]
      },
      {
        "id": "project-siem",
        "en_output": "en/projects/siem.html",
        "pl_output": "pl/projects/siem.html",
        "prompt": "prompts/project-siem.md",
        "sources": ["CLAUDE.md", "AGENTS.md"]
      },
      {
        "id": "project-amplifier",
        "en_output": "en/projects/amplifier.html",
        "pl_output": "pl/projects/amplifier.html",
        "prompt": "prompts/project-amplifier.md",
        "sources": ["CLAUDE.md", "AGENTS.md", "config/routing-matrix.yaml", ".claude/commands/**/*.md"]
      },
      {
        "id": "roadmap",
        "en_output": "en/roadmap.html",
        "pl_output": "pl/roadmap.html",
        "prompt": "prompts/roadmap.md",
        "sources": ["docs/specs/*.md", "docs/plans/*.md"]
      },
      {
        "id": "sessions-index",
        "en_output": "en/sessions/index.html",
        "pl_output": "pl/sessions/index.html",
        "prompt": "prompts/sessions-index.md",
        "sources": []
      }
    ],
    "hashes": {}
  }
  ```

- [ ] 2. Create `C:\claude\amplifier-docs\generate.ps1` — the main orchestrator script:

  ```powershell
  #Requires -Version 7
  param(
    [switch]$Force,
    [string]$PageFilter = ".*",
    [switch]$SkipTranslation,
    [string]$AmplifierRoot = "C:\claude\amplifier"
  )

  $ErrorActionPreference = "Continue"
  $DocsRoot = "C:\claude\amplifier-docs"
  $LogDir = "$DocsRoot\logs"
  $LogFile = "$LogDir\$(Get-Date -Format 'yyyy-MM-dd-HH-mm').log"
  $ManifestPath = "$DocsRoot\manifest.json"

  function Write-Log {
    param([string]$Msg, [string]$Level = "INFO")
    $line = "$(Get-Date -Format 'HH:mm:ss') [$Level] $Msg"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line
  }

  function Get-FileHash-Combined {
    param([string[]]$Paths)
    $content = ($Paths | Sort-Object | ForEach-Object {
      if (Test-Path $_) { Get-Content $_ -Raw } else { "" }
    }) -join "`n---`n"
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($content)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    [Convert]::ToBase64String($sha.ComputeHash($bytes))
  }

  function Expand-Globs {
    param([string[]]$Patterns, [string]$Root)
    $results = @()
    foreach ($pattern in $Patterns) {
      $fullPattern = Join-Path $Root $pattern
      $results += Get-ChildItem -Path $fullPattern -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
    }
    return $results | Select-Object -Unique
  }

  # --- Step 1: Pull latest ---
  Write-Log "Pulling latest from amplifier repo..."
  Push-Location $AmplifierRoot
  git pull origin main 2>&1 | ForEach-Object { Write-Log $_ }
  Pop-Location

  # --- Step 2: Load manifest ---
  $manifest = Get-Content $ManifestPath | ConvertFrom-Json
  $hashes = if ($manifest.hashes) { $manifest.hashes | ConvertTo-HashTable } else { @{} }

  # --- Step 3: Check global triggers ---
  $globalPaths = $manifest.global_triggers | ForEach-Object { "$DocsRoot\$_" }
  $globalHash = Get-FileHash-Combined -Paths $globalPaths
  $globalChanged = ($Force -or $hashes["__global__"] -ne $globalHash)
  if ($globalChanged) { Write-Log "Global triggers changed — all pages will regenerate." }

  # --- Step 4: Determine which pages need regeneration ---
  $designSystem = Get-Content "$DocsRoot\prompts\_design-system.md" -Raw -ErrorAction SilentlyContinue

  $pages = $manifest.pages | Where-Object { $_.id -match $PageFilter }
  $pagesToGenerate = @()

  foreach ($page in $pages) {
    $sourcePaths = Expand-Globs -Patterns $page.sources -Root $AmplifierRoot
    $pageHash = Get-FileHash-Combined -Paths $sourcePaths
    if ($globalChanged -or $Force -or $hashes[$page.id] -ne $pageHash) {
      $pagesToGenerate += @{ Page = $page; Hash = $pageHash }
    } else {
      Write-Log "Skipping $($page.id) — no changes detected."
    }
  }

  Write-Log "$($pagesToGenerate.Count) page(s) queued for generation."

  # --- Step 5: Generate each page ---
  foreach ($entry in $pagesToGenerate) {
    $page = $entry.Page
    $promptPath = "$DocsRoot\$($page.prompt)"

    if (-not (Test-Path $promptPath)) {
      Write-Log "Prompt file not found: $promptPath — skipping $($page.id)." "WARN"
      continue
    }

    $pagePrompt = Get-Content $promptPath -Raw
    $combinedPrompt = "$designSystem`n`n---`n`n$pagePrompt"

    $enOutput = "$DocsRoot\$($page.en_output)"
    $enOutputDir = Split-Path $enOutput -Parent
    New-Item -ItemType Directory -Force -Path $enOutputDir | Out-Null

    Write-Log "Generating EN: $($page.id)..."
    try {
      $result = & claude --headless -p $combinedPrompt 2>&1
      if ($LASTEXITCODE -eq 0 -and $result) {
        Set-Content -Path $enOutput -Value $result -Encoding UTF8
        Write-Log "Generated: $enOutput"

        # --- Step 5b: Translation ---
        if (-not $SkipTranslation) {
          $translatePrompt = Get-Content "$DocsRoot\prompts\_translate.md" -Raw
          $translatePrompt = $translatePrompt.Replace("{EN_FILE_PATH}", $enOutput).Replace("{PL_FILE_PATH}", "$DocsRoot\$($page.pl_output)")
          $enContent = Get-Content $enOutput -Raw
          $fullTranslatePrompt = "$translatePrompt`n`nEN FILE CONTENT:`n$enContent"

          $plOutput = "$DocsRoot\$($page.pl_output)"
          $plOutputDir = Split-Path $plOutput -Parent
          New-Item -ItemType Directory -Force -Path $plOutputDir | Out-Null

          Write-Log "Translating to PL: $($page.id)..."
          $plResult = & claude --headless -p $fullTranslatePrompt 2>&1
          if ($LASTEXITCODE -eq 0 -and $plResult) {
            Set-Content -Path $plOutput -Value $plResult -Encoding UTF8
            Write-Log "Translated: $plOutput"
          } else {
            Write-Log "Translation failed for $($page.id): $plResult" "ERROR"
          }
        }

        # Update hash only on success
        $hashes[$page.id] = $entry.Hash
      } else {
        Write-Log "Generation failed for $($page.id): $result" "ERROR"
      }
    } catch {
      Write-Log "Exception generating $($page.id): $_" "ERROR"
    }
  }

  # --- Step 6: Regenerate LLM files ---
  Write-Log "Regenerating LLM documentation files..."

  # llms.txt
  $llmsTxt = "# Amplifier Documentation`n# https://amplifier.ergonet.pl`n`n"
  foreach ($page in $manifest.pages) {
    $enPath = "$DocsRoot\$($page.en_output)"
    if (Test-Path $enPath) {
      $url = "https://amplifier.ergonet.pl/$($page.en_output)"
      $llmsTxt += "> $url $($page.id)`n"
    }
  }
  Set-Content "$DocsRoot\llms.txt" -Value $llmsTxt -Encoding UTF8

  # llms-full.txt — strip HTML tags from all EN pages
  $fullTxt = ""
  foreach ($page in $manifest.pages) {
    $enPath = "$DocsRoot\$($page.en_output)"
    if (Test-Path $enPath) {
      $html = Get-Content $enPath -Raw
      $text = $html -replace '<script[^>]*>[\s\S]*?</script>', '' `
                    -replace '<style[^>]*>[\s\S]*?</style>', '' `
                    -replace '<[^>]+>', ' ' `
                    -replace '\s+', ' '
      $fullTxt += "`n`n=== $($page.id) ===`n$text"
    }
  }
  Set-Content "$DocsRoot\llms-full.txt" -Value $fullTxt.Trim() -Encoding UTF8

  # llms-structured.json — extract from manifest (commands/agents parsed separately)
  $structured = @{ pages = $manifest.pages; generated = (Get-Date -Format 'o') }
  $structured | ConvertTo-Json -Depth 10 | Set-Content "$DocsRoot\llms-structured.json" -Encoding UTF8

  # --- Step 7: Update manifest hashes ---
  $hashes["__global__"] = $globalHash
  $manifest.hashes = $hashes
  $manifest | ConvertTo-Json -Depth 10 | Set-Content $ManifestPath -Encoding UTF8

  Write-Log "Generation complete. Log: $LogFile"
  ```

  Note: The `ConvertTo-HashTable` helper function must be defined early in the script:
  ```powershell
  function ConvertTo-HashTable {
    param([Parameter(ValueFromPipeline)][PSCustomObject]$InputObject)
    $ht = @{}
    $InputObject.PSObject.Properties | ForEach-Object { $ht[$_.Name] = $_.Value }
    return $ht
  }
  ```

- [ ] 3. Test the orchestrator with a dry run:
  ```powershell
  cd C:\claude\amplifier-docs
  powershell -File generate.ps1 -Force -SkipTranslation -PageFilter "home"
  ```
  Expected: script runs without crashing, logs "Prompt file not found: ... — skipping home." (since prompts don't exist yet), exits cleanly. `logs\` directory contains a timestamped log file.

- [ ] 4. Commit:
  ```bash
  git add manifest.json generate.ps1
  git commit -m "feat: add manifest system and generate.ps1 orchestrator

  Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
  ```

---

## Task 4: Webhook Listener + Gitea Configuration

**Agent:** modular-builder

**Files:**
- Create: `C:\claude\amplifier-docs\webhook-listener.ps1`
- Create: `C:\claude\amplifier-docs\.webhook-secret` (gitignored)
- Configure: Gitea webhook on admin/amplifier repo
- Register: Windows service `amplifier-docs-webhook`

**Steps:**

- [ ] 1. Generate a random webhook secret and store it (gitignored):
  ```powershell
  $secret = -join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Max 256) })
  Set-Content "C:\claude\amplifier-docs\.webhook-secret" $secret -Encoding UTF8
  Write-Host "Secret: $secret"
  ```
  Add `.webhook-secret` to `.gitignore`:
  ```
  .webhook-secret
  logs/
  ```

- [ ] 2. Create `C:\claude\amplifier-docs\webhook-listener.ps1`:
  ```powershell
  #Requires -Version 7
  $ErrorActionPreference = "Stop"

  $Port = 9099
  $Endpoint = "/amplifier-docs-rebuild"
  $SecretFile = "C:\claude\amplifier-docs\.webhook-secret"
  $GenerateScript = "C:\claude\amplifier-docs\generate.ps1"
  $LogFile = "C:\claude\amplifier-docs\logs\webhook.log"

  function Write-Log {
    param([string]$Msg, [string]$Level = "INFO")
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [$Level] $Msg"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line -ErrorAction SilentlyContinue
  }

  function Get-HmacSha256 {
    param([string]$Secret, [string]$Body)
    $key = [System.Text.Encoding]::UTF8.GetBytes($Secret)
    $data = [System.Text.Encoding]::UTF8.GetBytes($Body)
    $hmac = New-Object System.Security.Cryptography.HMACSHA256
    $hmac.Key = $key
    "sha256=" + (($hmac.ComputeHash($data) | ForEach-Object { '{0:x2}' -f $_ }) -join '')
  }

  $secret = Get-Content $SecretFile -Raw | ForEach-Object { $_.Trim() }
  $listener = [System.Net.HttpListener]::new()
  $listener.Prefixes.Add("http://localhost:$Port/")
  $listener.Start()
  Write-Log "Webhook listener started on http://localhost:$Port$Endpoint"

  while ($listener.IsListening) {
    try {
      $context = $listener.GetContext()
      $request = $context.Request
      $response = $context.Response

      try {
        if ($request.HttpMethod -ne "POST") {
          $response.StatusCode = 405
          Write-Log "Rejected: $($request.HttpMethod) — method not allowed." "WARN"
        } elseif ($request.Url.AbsolutePath -ne $Endpoint) {
          $response.StatusCode = 404
          Write-Log "Rejected: unknown path $($request.Url.AbsolutePath)." "WARN"
        } else {
          $bodyStream = New-Object System.IO.StreamReader($request.InputStream)
          $body = $bodyStream.ReadToEnd()
          $bodyStream.Close()

          $sig = $request.Headers["X-Gitea-Signature"]
          $expected = Get-HmacSha256 -Secret $secret -Body $body
          if ($sig -ne $expected) {
            $response.StatusCode = 403
            Write-Log "Rejected: invalid HMAC signature. Got: $sig" "WARN"
          } else {
            $payload = $body | ConvertFrom-Json
            if ($payload.action -eq "closed" -and $payload.pull_request.merged -eq $true) {
              Write-Log "Valid webhook: PR #$($payload.number) merged. Spawning generate.ps1..."
              Start-Job -ScriptBlock {
                param($Script)
                & powershell -File $Script 2>&1
              } -ArgumentList $GenerateScript | Out-Null
              $response.StatusCode = 200
              $responseBody = '{"status":"queued"}'
              $bytes = [System.Text.Encoding]::UTF8.GetBytes($responseBody)
              $response.ContentType = "application/json"
              $response.OutputStream.Write($bytes, 0, $bytes.Length)
            } else {
              $response.StatusCode = 200
              Write-Log "Received non-merge event (action=$($payload.action)) — ignoring."
            }
          }
        }
      } catch {
        $response.StatusCode = 500
        Write-Log "Error processing request: $_" "ERROR"
      }

      $response.Close()
    } catch {
      Write-Log "Listener error: $_" "ERROR"
    }
  }
  ```

- [ ] 3. Register as a Windows service using NSSM (if available) or Task Scheduler:
  ```powershell
  # Option A: NSSM (preferred)
  if (Get-Command nssm -ErrorAction SilentlyContinue) {
    nssm install amplifier-docs-webhook powershell.exe "-NonInteractive -File C:\claude\amplifier-docs\webhook-listener.ps1"
    nssm set amplifier-docs-webhook AppDirectory "C:\claude\amplifier-docs"
    nssm set amplifier-docs-webhook Start SERVICE_AUTO_START
    nssm set amplifier-docs-webhook AppRestartDelay 5000
    Start-Service amplifier-docs-webhook
    Write-Host "Service registered and started via NSSM."
  } else {
    # Option B: Task Scheduler (fallback)
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NonInteractive -WindowStyle Hidden -File C:\claude\amplifier-docs\webhook-listener.ps1"
    $trigger = New-ScheduledTaskTrigger -AtStartup
    $settings = New-ScheduledTaskSettingsSet -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero)
    Register-ScheduledTask -TaskName "amplifier-docs-webhook" -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -Force
    Start-ScheduledTask -TaskName "amplifier-docs-webhook"
    Write-Host "Task registered and started via Task Scheduler."
  }
  ```

- [ ] 4. Configure Gitea webhook using MCP tool `mcp__gitea__create_repo_action_variable` or webhook API. The webhook must be created on repo `admin/amplifier`:
  - URL: `http://localhost:9099/amplifier-docs-rebuild`
  - Content type: `application/json`
  - Events: `pull_request` (merged)
  - Secret: value from `.webhook-secret`
  - Use `mcp__gitea__*` tools to verify the webhook was created: list webhooks on the repo.

- [ ] 5. Test the listener with a mock request:
  ```bash
  # Compute HMAC for test payload
  SECRET=$(cat /c/claude/amplifier-docs/.webhook-secret)
  BODY='{"action":"closed","number":1,"pull_request":{"merged":true}}'
  SIG=$(echo -n "$BODY" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print "sha256="$2}')

  curl -s -X POST http://localhost:9099/amplifier-docs-rebuild \
    -H "Content-Type: application/json" \
    -H "X-Gitea-Signature: $SIG" \
    -d "$BODY"
  ```
  Expected: `{"status":"queued"}` with HTTP 200. Check `logs\webhook.log` for "PR #1 merged" entry.

- [ ] 6. Commit:
  ```bash
  git add webhook-listener.ps1 .gitignore
  git commit -m "feat: add webhook listener and Gitea integration

  Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
  ```

---

## Task 5: Core Page Prompts — Home + Manual + Commands + Agents

**Agent:** modular-builder

**Files:**
- Create: `C:\claude\amplifier-docs\prompts\home.md`
- Create: `C:\claude\amplifier-docs\prompts\manual.md`
- Create: `C:\claude\amplifier-docs\prompts\commands.md`
- Create: `C:\claude\amplifier-docs\prompts\agents.md`

Each prompt must start with: "Read the design system at: `C:\claude\amplifier-docs\prompts\_design-system.md` and follow it exactly."

**Steps:**

- [ ] 1. Create `C:\claude\amplifier-docs\prompts\home.md` — Landing page generation prompt:

  ```
  Read the design system at: C:\claude\amplifier-docs\prompts\_design-system.md and follow it exactly.

  Generate a complete, production-quality HTML documentation page for the Amplifier AI Platform home page.

  Source files to read:
  - C:\claude\amplifier\CLAUDE.md
  - C:\claude\amplifier\AGENTS.md
  - C:\claude\amplifier\config\routing-matrix.yaml

  Page sections (in order):

  1. HERO SECTION
     - Title: "Amplifier" in Bricolage Grotesque, gold gradient
     - Subtitle: "Self-improving AI development platform"
     - Tagline: "36 agents · 35 commands · 7 model roles · 3 tiers"
     - Two CTA buttons: "Read the Manual" → /en/manual.html, "Browse Commands" → /en/commands.html

  2. KPI COUNTER ROW
     - Four animated counter cards: 36 Agents, 35 Commands, 7 Roles, 3 Model Tiers
     - Counters animate from 0 on page load using IntersectionObserver

  3. PLATFORM IDENTITY (2-column)
     - Left: What Amplifier Is (3 bullet points from CLAUDE.md Operating Principles)
     - Right: Architecture overview (static generation, subagent dispatch, quality flywheel)

  4. SEVEN-SECTION QUICK LINKS
     - Card grid (3+4 layout): Manual, Commands, Agents, Deep Dives, Platform, Projects, Sessions
     - Each card: icon (emoji), title, one-line description, arrow link
     - Hover lift effect with gold border glow

  5. RECENT ACTIVITY FEED
     - Run: git -C C:\claude\amplifier log --oneline -5 --merges
     - Display last 5 merged PRs with commit hash, message, relative date
     - Styled as a vertical timeline with gold dots

  6. PROJECT STATUS CARDS (3 columns)
     - FuseCP: C# / Blazor / .NET — Windows DEV server
     - Genetics Platform: TypeScript / Tailwind / shadcn — Linux 172.31.250.2
     - Universal SIEM: Python — Linux 172.31.250.2

  LLM metadata:
  - page: "home", title: "Amplifier Platform", purpose: "Landing page and navigation hub for the Amplifier AI development platform"
  - key_concepts: ["self-improvement", "agent dispatch", "effort steering", "subagent optimization"]
  - source_files: ["CLAUDE.md", "AGENTS.md", "config/routing-matrix.yaml"]

  Output file: C:\claude\amplifier-docs\en\index.html
  ```

- [ ] 2. Create `C:\claude\amplifier-docs\prompts\manual.md` — User manual prompt:

  ```
  Read the design system at: C:\claude\amplifier-docs\prompts\_design-system.md and follow it exactly.

  Generate a complete, production-quality HTML user manual for the Amplifier AI Platform.

  Source files to read (read ALL of them before generating):
  - C:\claude\amplifier\CLAUDE.md
  - C:\claude\amplifier\AGENTS.md
  - C:\claude\amplifier\docs\guides\*.md (read all files in this directory)
  - C:\claude\amplifier\ai_context\claude_code\*.md (read all files in this directory)

  Page sections (each gets a sidebar anchor link):

  1. GETTING STARTED — Identity, workspace root, environment setup
  2. OPERATING PRINCIPLES — 5 principles with expandable detail (Plan First, Delegate Right, Effort Steering, Parallel Execution, Ask When Uncertain)
  3. WORKFLOW COMMANDS — The three workflow entry points: brainstorm→create-plan→subagent-dev, debug→tdd→verify, retro→techdebt→self-improve
  4. EFFORT STEERING — 4 effort levels, session/role/task resolution formula, when to change effort
  5. MEMORY TOOLS — /recall, /docs search, episodic memory, priority table
  6. AGENT DISPATCH — Routing matrix rules, when to use haiku/sonnet/opus inline vs subagent, resume protocol
  7. GIT WORKFLOW — PR-first policy, review-before-merge, commit footer, Gitea vs GitHub distinction
  8. CONFIGURATION — Single source of truth hierarchy, pyproject.toml→ruff.toml→routing-matrix, uv dependency management
  9. COMPACT INSTRUCTIONS — What survives compression, recovery steps, STATE.md triggers

  Sidebar must have in-page anchor links to each of the 9 sections above.

  LLM metadata:
  - page: "manual", title: "User Manual", purpose: "Complete operational guide for using the Amplifier AI development platform"
  - key_concepts: ["workflow", "agent dispatch", "effort steering", "memory", "git policy"]
  - source_files: ["CLAUDE.md", "AGENTS.md", "docs/guides/", "ai_context/claude_code/"]

  Output file: C:\claude\amplifier-docs\en\manual.html
  ```

- [ ] 3. Create `C:\claude\amplifier-docs\prompts\commands.md` — Command reference prompt:

  ```
  Read the design system at: C:\claude\amplifier-docs\prompts\_design-system.md and follow it exactly.

  Generate a complete, production-quality HTML command reference for all Amplifier slash commands.

  Source files to read:
  - Read ALL markdown files under: C:\claude\amplifier\.claude\commands\
  - C:\claude\amplifier\config\routing-matrix.yaml

  Page layout:

  1. HEADER with search/filter bar:
     - Text search input (filters cards in real-time via JS)
     - Category filter buttons: All | Development | Investigation | Maintenance | Meta | Domain
     - Count indicator: "Showing N of 35 commands"

  2. COMMAND CARD GRID (responsive: 1-3 columns)
     Each card contains:
     - Command name in Fragment Mono: /command-name
     - Category badge with color: development=teal, investigation=coral, maintenance=gold, meta=gray, domain=blue
     - Description (first paragraph from source .md file)
     - Usage example (code block with Fragment Mono)
     - "Chains to:" pill list (other commands this calls)
     - "Related:" pill list

  3. CATEGORY GROUPING
     Group by category with section headers. Categories:
     - Development: brainstorm, create-plan, subagent-dev, tdd, verify, finish-branch, parallel-agents
     - Investigation: debug, docs, recall, retro, techdebt
     - Maintenance: self-eval, self-improve, evaluate, improve, optimize-skill, solve
     - Meta: effort, platform, help, compact
     - Domain: fix-bugs, test-verified (FuseCP-specific)
     - Design: frontend-design, design-interface, create-component, visual-explainer
     - Agent: create-agent, subagent-architect

  Filter + search must work via vanilla JS (no framework dependencies).

  LLM metadata:
  - page: "commands", title: "Command Reference", purpose: "Complete reference for all 35 Amplifier slash commands with usage examples"
  - key_concepts: ["slash commands", "workflow", "categories", "chains"]
  - source_files: [".claude/commands/"]

  Output file: C:\claude\amplifier-docs\en\commands.html
  ```

- [ ] 4. Create `C:\claude\amplifier-docs\prompts\agents.md` — Agent catalog prompt:

  ```
  Read the design system at: C:\claude\amplifier-docs\prompts\_design-system.md and follow it exactly.

  Generate a complete, production-quality HTML agent catalog for all Amplifier agents.

  Source files to read:
  - Read ALL markdown files under: C:\claude\amplifier\.claude\agents\
  - C:\claude\amplifier\config\routing-matrix.yaml

  Page layout:

  1. HEADER with filter controls:
     - Text search input (filters agent name + description)
     - Role filter buttons: All | Scout | Research | Implement | Architect | Review | Security | Fast
     - Model tier filter: All | Haiku | Sonnet | Opus
     - Count: "Showing N of 36 agents"

  2. AGENT CARD GRID (responsive: 1-3 columns)
     Each card:
     - Agent name (formatted as agent-name)
     - Role badge (color-coded): scout=teal, research=blue, implement=indigo, architect=gold, review=green, security=red, fast=gray
     - Model tier badge: haiku=sky, sonnet=violet, opus=amber
     - Turn budget: min/default/max from routing-matrix
     - Description (from agent .md file)
     - "Dispatch as:" recommendation (subagent or inline)
     - Key capabilities bullet list (3 bullets max)

  3. ROUTING MATRIX TABLE
     Full table showing all roles with model, effort level, turn budget, and description.
     Taken directly from routing-matrix.yaml.

  4. DISPATCH GUIDE
     Decision table: "When to use subagent vs inline" — 4-row table from AGENTS.md.

  Role color coding must match the badge colors used in the Commands page.
  Filter + search via vanilla JS.

  LLM metadata:
  - page: "agents", title: "Agent Catalog", purpose: "Complete catalog of all 36 Amplifier agents with roles, models, and dispatch guidance"
  - key_concepts: ["agent roles", "model tiers", "routing matrix", "turn budgets", "dispatch"]
  - source_files: [".claude/agents/", "config/routing-matrix.yaml"]

  Output file: C:\claude\amplifier-docs\en\agents.html
  ```

- [ ] 5. Commit all prompts:
  ```bash
  git add prompts/home.md prompts/manual.md prompts/commands.md prompts/agents.md
  git commit -m "feat: add core page generation prompts (home, manual, commands, agents)

  Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
  ```

---

## Task 6: Deep Dive Page Prompts (4 pages)

**Agent:** modular-builder

**Files:**
- Create: `C:\claude\amplifier-docs\prompts\deep-dive-self-improvement.md`
- Create: `C:\claude\amplifier-docs\prompts\deep-dive-effort-steering.md`
- Create: `C:\claude\amplifier-docs\prompts\deep-dive-autocontext.md`
- Create: `C:\claude\amplifier-docs\prompts\deep-dive-workflows.md`

**Steps:**

- [ ] 1. Create `C:\claude\amplifier-docs\prompts\deep-dive-self-improvement.md`:

  ```
  Read the design system at: C:\claude\amplifier-docs\prompts\_design-system.md and follow it exactly.

  Generate a deep-dive HTML page on Amplifier's self-improvement system.

  Source files to read:
  - C:\claude\amplifier\.claude\commands\self-eval.md
  - C:\claude\amplifier\.claude\commands\self-improve.md
  - C:\claude\amplifier\.claude\commands\evaluate.md
  - C:\claude\amplifier\.claude\commands\improve.md
  - C:\claude\amplifier\.claude\commands\optimize-skill.md
  - C:\claude\amplifier\.claude\commands\solve.md
  - C:\claude\amplifier\AGENTS.md (AutoContext Quality Gates section)

  For visual reference on layout quality and structure style, see:
  C:\Users\Administrator.ERGOLAB\.agent\diagrams\amplifier-self-improvement-system.html

  Page sections:

  1. FLYWHEEL DIAGRAM
     SVG or CSS diagram showing the self-improvement cycle:
     Commands Run → /self-eval scores → AutoContext accumulates → /self-improve proposes → CLAUDE.md evolves → Better outputs → Higher scores → (repeat)
     Use gold arrows, dark bg, animated on scroll.

  2. THE 5-COMMAND EVALUATION STACK
     Expandable cards for each command: /self-eval, /evaluate, /improve, /optimize-skill, /solve
     Each: purpose, when to use, expected output, example invocation.

  3. QUALITY THRESHOLDS
     Score table: < 60 = fail/retry, 60-79 = improve, 80-89 = good, 90+ = excellent
     Visual score gauge component.

  4. AUTO-RESEARCH METHODOLOGY
     How AutoContext accumulates patterns across sessions. Knowledge bridge diagram:
     AutoContext → .claude/skills/ → /recall

  5. QUALITY GATES
     Checklist-style table: after significant work (evaluate), after brainstorm (self-eval), weekly (self-improve), before recurring problems (skill_discover).

  LLM metadata:
  - page: "deep-dive-self-improvement", title: "Self-Improvement Deep Dive"
  - purpose: "Technical deep dive into Amplifier's self-improvement flywheel and evaluation system"
  - key_concepts: ["self-eval", "quality gates", "AutoContext", "flywheel", "skill optimization"]

  Output file: C:\claude\amplifier-docs\en\deep-dives\self-improvement.html
  ```

- [ ] 2. Create `C:\claude\amplifier-docs\prompts\deep-dive-effort-steering.md`:

  ```
  Read the design system at: C:\claude\amplifier-docs\prompts\_design-system.md and follow it exactly.

  Generate a deep-dive HTML page on Amplifier's effort steering system.

  Source files to read:
  - C:\claude\amplifier\config\routing-matrix.yaml
  - C:\claude\amplifier\AGENTS.md (Turn Budgets section, Effort Steering section)
  - C:\claude\amplifier\CLAUDE.md (Operating Principles #3)

  Page sections:

  1. THREE-LAYER CONCENTRIC DIAGRAM
     SVG diagram: outer ring = Session (/effort command), middle ring = Role (routing-matrix), inner ring = Task (signal-based)
     Resolution formula displayed below: resolved_effort = min(session_effort, max(role_effort, task_signals))

  2. THE FOUR EFFORT LEVELS
     Visual card row: low → medium → high → max
     Each card: label, description, turn multiplier, auto-resume behavior
     max = auto-resume up to 3 cycles, shown with circular arrow icon.

  3. ROLE → MODEL MAPPING TABLE
     Full routing-matrix table: Role | Model | Effort | Min Turns | Default Turns | Max Turns | Description
     Color-coded by model tier (haiku=sky, sonnet=violet, opus=amber).

  4. ELASTIC TURNS EXPLAINED
     Animated bar chart showing min/default/max for each role.
     Explanation of how orchestrator picks within range based on task complexity.

  5. WHEN TO CHANGE EFFORT
     Decision guide: session /effort switch examples, signal-based auto-adjustment, when to override.

  LLM metadata:
  - page: "deep-dive-effort-steering", title: "Effort Steering Deep Dive"
  - purpose: "Technical explanation of Amplifier's 3-layer effort steering system and routing matrix"
  - key_concepts: ["effort levels", "routing matrix", "turn budgets", "model tiers", "elastic turns"]

  Output file: C:\claude\amplifier-docs\en\deep-dives\effort-steering.html
  ```

- [ ] 3. Create `C:\claude\amplifier-docs\prompts\deep-dive-autocontext.md`:

  ```
  Read the design system at: C:\claude\amplifier-docs\prompts\_design-system.md and follow it exactly.

  Generate a deep-dive HTML page on AutoContext — Amplifier's AI quality system.

  Source files to read:
  - C:\claude\amplifier\.mcp.json (find autocontext server entries)
  - C:\claude\amplifier\AGENTS.md (AutoContext Quality Gates section)
  - C:\claude\amplifier\.claude\commands\evaluate.md
  - C:\claude\amplifier\.claude\commands\solve.md
  - C:\claude\amplifier\.claude\commands\optimize-skill.md

  Page sections:

  1. ARCHITECTURE DIAGRAM
     Input → Processing → Output pipeline:
     [Session Commands] → [AutoContext MCP] → [Scenarios] → [Evaluation] → [Skills/Strategies] → [CLAUDE.md Updates]
     Styled as a horizontal flow with glowing nodes.

  2. MCP TOOL CATALOG
     Grouped table of all autocontext MCP tools used in Amplifier:
     - Evaluation: autocontext_evaluate_output, autocontext_evaluate_strategy
     - Skill management: autocontext_skill_discover, autocontext_skill_advertise, autocontext_skill_select
     - Scenario: autocontext_describe_scenario, autocontext_solve_scenario, autocontext_solve_status
     - Improvement: autocontext_queue_improvement_run, autocontext_run_improvement_loop
     Each row: tool name, when called, what it returns.

  3. SKILL LIFECYCLE
     Timeline diagram: Discover → Evaluate → Advertise → Select → Apply → Refine
     With example skill names from .claude/skills/ directory if present.

  4. QUALITY SCORE SYSTEM
     How AutoContext scores outputs, what makes a score go up vs down.
     Score breakdown components, what < 80 triggers.

  5. KNOWLEDGE BRIDGE
     How AutoContext knowledge flows to /recall and .claude/skills/:
     AutoContext runs → extracts patterns → writes to skills/ → /recall indexes → next session reads.

  LLM metadata:
  - page: "deep-dive-autocontext", title: "AutoContext Deep Dive"
  - purpose: "Technical architecture of AutoContext quality evaluation and skill accumulation system"
  - key_concepts: ["AutoContext", "MCP tools", "skill lifecycle", "quality scoring", "knowledge bridge"]

  Output file: C:\claude\amplifier-docs\en\deep-dives\autocontext.html
  ```

- [ ] 4. Create `C:\claude\amplifier-docs\prompts\deep-dive-workflows.md`:

  ```
  Read the design system at: C:\claude\amplifier-docs\prompts\_design-system.md and follow it exactly.

  Generate a deep-dive HTML page on Amplifier's three workflow families.

  Source files to read:
  - C:\claude\amplifier\.claude\commands\brainstorm.md
  - C:\claude\amplifier\.claude\commands\create-plan.md
  - C:\claude\amplifier\.claude\commands\subagent-dev.md
  - C:\claude\amplifier\.claude\commands\debug.md
  - C:\claude\amplifier\.claude\commands\tdd.md
  - C:\claude\amplifier\.claude\commands\verify.md
  - C:\claude\amplifier\.claude\commands\finish-branch.md
  - C:\claude\amplifier\.claude\commands\retro.md (if exists)
  - C:\claude\amplifier\AGENTS.md

  Page sections:

  1. THREE WORKFLOW FAMILIES (tabbed or side-by-side)

     FAMILY A — Standard Feature Development:
     /brainstorm → /create-plan → /subagent-dev → /verify → /finish-branch
     Flow diagram with arrows, each node shows purpose + key output.

     FAMILY B — Investigation + Testing:
     /debug → /tdd → /verify
     Flow diagram. Debug produces hypotheses, tdd produces tests, verify confirms.

     FAMILY C — Maintenance + Improvement:
     /retro → /techdebt → /self-improve
     Flow diagram. Retro identifies issues, techdebt prioritizes, self-improve implements.

  2. QUALITY GATES TABLE
     When each gate fires, what it checks, what happens on fail:
     | Gate | Command | Threshold | Action on Fail |

  3. DECISION TREE
     "Which workflow to start with?" decision tree:
     - New feature? → brainstorm
     - Bug or mystery? → debug
     - Want better quality? → self-eval
     - Technical debt? → retro
     Rendered as an SVG or CSS tree diagram.

  4. AGENT DISPATCH INSIDE WORKFLOWS
     How /subagent-dev dispatches agents, turn budget selection, resume protocol.
     References the routing matrix from /en/agents.html.

  5. INTER-WORKFLOW HANDOFFS
     Common patterns: brainstorm → subagent-dev → tdd → verify as a full chain.

  LLM metadata:
  - page: "deep-dive-workflows", title: "Workflow Deep Dive"
  - purpose: "Technical guide to Amplifier's three workflow families and quality gate system"
  - key_concepts: ["workflow families", "quality gates", "subagent dispatch", "decision trees", "handoffs"]

  Output file: C:\claude\amplifier-docs\en\deep-dives\workflows.html
  ```

- [ ] 5. Commit all:
  ```bash
  git add prompts/deep-dive-*.md
  git commit -m "feat: add deep-dive page generation prompts

  Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
  ```

---

## Task 7: Platform + Projects + Roadmap + Sessions Prompts

**Agent:** modular-builder

**Files:**
- Create: 11 prompt files in `C:\claude\amplifier-docs\prompts\`

**Steps:**

- [ ] 1. Create `C:\claude\amplifier-docs\prompts\platform-overview.md`:

  ```
  Read the design system at: C:\claude\amplifier-docs\prompts\_design-system.md and follow it exactly.

  Generate an HTML platform overview page comparing Linux and Windows configurations.

  Source files: C:\claude\amplifier\CLAUDE.md (Identity and Environment section)

  Content:
  - Side-by-side comparison table: Linux (172.31.250.2) vs Windows (172.31.251.100)
  - Rows: Primary platform, Python (uv path), Node.js, Claude Code version, MCP registration method,
    Global MCP servers, Project MCP servers, Chrome/browser, Key paths
  - Key differences callout box (3 bullets)
  - Platform switching instructions: bash scripts/setup-platform-config.sh --force or /platform setup

  Output file: C:\claude\amplifier-docs\en\platform\index.html
  ```

- [ ] 2. Create `C:\claude\amplifier-docs\prompts\platform-linux.md`:

  ```
  Read the design system at: C:\claude\amplifier-docs\prompts\_design-system.md and follow it exactly.

  Generate an HTML page for Linux-specific Amplifier configuration.

  Source files: C:\claude\amplifier\CLAUDE.md, C:\claude\amplifier\scripts\setup-platform-config.sh, any ai_context/claude_code/*.md files

  Content:
  - Key paths table: /opt/amplifier, /opt/autocontext/autocontext, /home/claude/.local/bin/uv, etc.
  - MCP registration: claude mcp add -s user command (writes to ~/.claude.json, not .mcp.json)
  - uv setup: source ~/.local/bin/env for shell access
  - Chrome headless: Xvfb on DISPLAY=:2, how to use
  - Global vs project MCP: ~/.claude.json for global, .mcp.json for project-level
  - Configuration table: all MCP servers (autocontext, gitea, chrome-devtools, obsidian, cipher)

  Output file: C:\claude\amplifier-docs\en\platform\linux.html
  ```

- [ ] 3. Create `C:\claude\amplifier-docs\prompts\platform-windows.md`:

  ```
  Read the design system at: C:\claude\amplifier-docs\prompts\_design-system.md and follow it exactly.

  Generate an HTML page for Windows Server-specific Amplifier configuration.

  Source files: C:\claude\amplifier\CLAUDE.md, C:\claude\amplifier\scripts\guard-paths.sh (or guard-paths-linux.sh)

  Content:
  - IIS sites table: Amplifier_Docs, FuseCP_Portal, FuseCP_API
  - Path guard: C:\claude\scripts\guard-paths.sh — what it blocks, allowed paths
  - Git Bash: Unix syntax (forward slashes, /dev/null not nul), CLAUDECODE=1 fast path
  - PowerShell 7: default profile, deployment commands
  - psmux: web terminal at webpsmux.ergonet.pl
  - Windows reserved names: never create nul, con, prn, aux, com1-com9, lpt1-lpt9

  Output file: C:\claude\amplifier-docs\en\platform\windows.html
  ```

- [ ] 4. Create `C:\claude\amplifier-docs\prompts\projects-index.md`:

  ```
  Read the design system at: C:\claude\amplifier-docs\prompts\_design-system.md and follow it exactly.

  Generate an HTML hub page listing all active projects managed by Amplifier.

  Source files: C:\claude\amplifier\CLAUDE.md, C:\claude\amplifier\AGENTS.md

  Content:
  - 2x2 card grid with 4 projects:
    1. FuseCP Enterprise — C# / Blazor / .NET — Windows DEV (172.31.251.100) — Link: /en/projects/fusecp.html
    2. Genetics Platform — TypeScript / Tailwind / shadcn — Linux (172.31.250.2) — Link: /en/projects/genetics.html
    3. Universal SIEM — Python — Linux (172.31.250.2) — Link: /en/projects/siem.html
    4. Amplifier — Self-development — Both platforms — Link: /en/projects/amplifier.html
  - Each card: project name, stack badges, platform badge, brief description, status indicator (active/development)

  Output file: C:\claude\amplifier-docs\en\projects\index.html
  ```

- [ ] 5. Create `C:\claude\amplifier-docs\prompts\project-fusecp.md`:

  ```
  Read the design system at: C:\claude\amplifier-docs\prompts\_design-system.md and follow it exactly.

  Generate an HTML project page for FuseCP Enterprise.

  Source files: C:\claude\amplifier\CLAUDE.md, C:\claude\amplifier\AGENTS.md

  Content:
  - Stack: C# / Blazor / .NET — deployed to IIS on Windows Server 2025
  - CRITICAL development principles (3): Backward Compatibility, Strict Tenant Isolation, Never Trust UI
  - Architecture: Portal (Blazor) + EnterpriseServer (API) + SQL Express database
  - Deployment commands: Stop-WebAppPool, dotnet publish, Start-WebAppPool — shown in code blocks
  - Key paths: C:\claude\fusecp-enterprise, C:\FuseCP\Portal, C:\FuseCP\EnterpriseServer
  - Tenant model: organizations, packages, mailboxes, Exchange integration
  - IIS sites table: FuseCP_Portal, FuseCP_API with bindings
  - Daily bug-fix workflow with curl example

  Output file: C:\claude\amplifier-docs\en\projects\fusecp.html
  ```

- [ ] 6. Create `C:\claude\amplifier-docs\prompts\project-genetics.md`:

  ```
  Read the design system at: C:\claude\amplifier-docs\prompts\_design-system.md and follow it exactly.

  Generate an HTML project page for the Genetics Platform.

  Source files: C:\claude\amplifier\CLAUDE.md, C:\claude\amplifier\AGENTS.md

  Content:
  - Stack: TypeScript / Tailwind CSS / shadcn/ui
  - Platform: Linux Ubuntu at 172.31.250.2 (/opt/amplifier context)
  - Repo: claude/genetics-platform on Gitea
  - Development context: bioinformatics/genetics data visualization
  - Stack details: Node.js v24, TypeScript strict mode, component-driven design

  Output file: C:\claude\amplifier-docs\en\projects\genetics.html
  ```

- [ ] 7. Create `C:\claude\amplifier-docs\prompts\project-siem.md`:

  ```
  Read the design system at: C:\claude\amplifier-docs\prompts\_design-system.md and follow it exactly.

  Generate an HTML project page for Universal SIEM.

  Source files: C:\claude\amplifier\CLAUDE.md, C:\claude\amplifier\AGENTS.md

  Content:
  - Stack: Python (UV-managed), monorepo structure
  - Platform: Linux Ubuntu at 172.31.250.2
  - Repo: admin/universal-siem-monorepo on Gitea
  - Purpose: security event aggregation, detection rules, alert pipeline
  - Python project structure: pyproject.toml, uv sync, ruff linting

  Output file: C:\claude\amplifier-docs\en\projects\siem.html
  ```

- [ ] 8. Create `C:\claude\amplifier-docs\prompts\project-amplifier.md`:

  ```
  Read the design system at: C:\claude\amplifier-docs\prompts\_design-system.md and follow it exactly.

  Generate an HTML project page for Amplifier itself (the meta-project).

  Source files: C:\claude\amplifier\CLAUDE.md, C:\claude\amplifier\AGENTS.md, C:\claude\amplifier\config\routing-matrix.yaml

  Content:
  - Amplifier as a self-improving platform — manages itself via its own agents and commands
  - Agent catalog size: 36 agents, 35 commands, 7 roles
  - Self-improvement flywheel: how CLAUDE.md and AGENTS.md evolve via /self-improve
  - Repo: admin/amplifier on Gitea
  - Both-platform presence: Linux primary, Windows secondary
  - Docs site: this documentation site (https://amplifier.ergonet.pl) is itself an Amplifier output

  Output file: C:\claude\amplifier-docs\en\projects\amplifier.html
  ```

- [ ] 9. Create `C:\claude\amplifier-docs\prompts\roadmap.md`:

  ```
  Read the design system at: C:\claude\amplifier-docs\prompts\_design-system.md and follow it exactly.

  Generate an HTML roadmap page for Amplifier.

  Source files:
  - List all files in C:\claude\amplifier\docs\specs\ and read the most recent 5
  - List all files in C:\claude\amplifier\docs\plans\ and read the most recent 5

  Content:
  - Current specs timeline (by date, newest first): spec title, date, brief description from file header
  - Current plans timeline (by date, newest first): plan title, date, status (completed/in-progress/planned)
  - Feature backlog section: extract any "TODO" or "Future" sections from recent specs
  - Strategic direction: self-improvement, documentation, project expansion

  Output file: C:\claude\amplifier-docs\en\roadmap.html
  ```

- [ ] 10. Create `C:\claude\amplifier-docs\prompts\session-recap.md` — template for per-session recaps:

  ```
  Read the design system at: C:\claude\amplifier-docs\prompts\_design-system.md and follow it exactly.

  Generate a session recap HTML page for PR #{PR_NUMBER}.

  Input data (provided at generation time):
  - PR number: {PR_NUMBER}
  - PR title: {PR_TITLE}
  - Merge date: {MERGE_DATE}
  - Commit log: {COMMIT_LOG}
  - Diff stats: {DIFF_STATS}
  - Description: {PR_DESCRIPTION}

  Content sections:
  1. Session header: PR title, date, badge (feat/fix/docs/refactor)
  2. Changes summary: diff stats table (files changed, insertions, deletions)
  3. Commit timeline: each commit as a timeline item
  4. Key decisions: extracted from PR description or commit messages
  5. Files touched: grouped by type (commands, agents, scripts, docs)

  Output file: C:\claude\amplifier-docs\en\sessions\pr-{PR_NUMBER}.html
  ```

- [ ] 11. Create `C:\claude\amplifier-docs\prompts\sessions-index.md`:

  ```
  Read the design system at: C:\claude\amplifier-docs\prompts\_design-system.md and follow it exactly.

  Generate a sessions index HTML page showing the rolling 30-day window of PRs.

  Source: run git -C C:\claude\amplifier log --merges --since="30 days ago" --format="%H|%s|%ai" to get merged PRs

  Content:
  - Rolling 30-day list of merged PRs, newest first
  - Each entry: date badge, PR title, commit hash (short), link to individual recap page
  - Month grouping with separator headers
  - "Older sessions" link → /en/sessions/archive/

  Output file: C:\claude\amplifier-docs\en\sessions\index.html
  ```

- [ ] 12. Commit all:
  ```bash
  git add prompts/platform-*.md prompts/projects-index.md prompts/project-*.md prompts/roadmap.md prompts/session-recap.md prompts/sessions-index.md
  git commit -m "feat: add platform, project, roadmap, and session prompt files

  Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
  ```

---

## Task 8: Initial Full Generation — EN Pages

**Agent:** modular-builder

**Files:**
- Generate: all EN HTML pages under `C:\claude\amplifier-docs\en\`

**Steps:**

- [ ] 1. Run full EN generation (skipping translation for now):
  ```powershell
  cd C:\claude\amplifier-docs
  powershell -File generate.ps1 -Force -SkipTranslation
  ```
  Expected: script runs, calls `claude --headless` for each page, writes HTML files to `en/` subdirectories. Log file created in `logs/`.

- [ ] 2. Verify each generated page exists and is non-empty. Check all expected outputs:
  ```powershell
  $expectedPages = @(
    "en\index.html", "en\manual.html", "en\commands.html", "en\agents.html",
    "en\deep-dives\self-improvement.html", "en\deep-dives\effort-steering.html",
    "en\deep-dives\autocontext.html", "en\deep-dives\workflows.html",
    "en\platform\index.html", "en\platform\linux.html", "en\platform\windows.html",
    "en\projects\index.html", "en\projects\fusecp.html", "en\projects\genetics.html",
    "en\projects\siem.html", "en\projects\amplifier.html",
    "en\roadmap.html", "en\sessions\index.html"
  )
  foreach ($page in $expectedPages) {
    $path = "C:\claude\amplifier-docs\$page"
    $exists = Test-Path $path
    $size = if ($exists) { (Get-Item $path).Length } else { 0 }
    Write-Host "$page : exists=$exists size=$size"
  }
  ```
  Expected: all pages exist with size > 1000 bytes.

- [ ] 3. Validate page structure — each page must contain:
  ```powershell
  $checks = @("sidebar", "Bricolage Grotesque", "application/llm+json", "#0b1120", "amplifier.ergonet.pl")
  foreach ($page in $expectedPages) {
    $content = Get-Content "C:\claude\amplifier-docs\$page" -Raw -ErrorAction SilentlyContinue
    foreach ($check in $checks) {
      if (-not $content.Contains($check)) {
        Write-Host "MISSING '$check' in $page" -ForegroundColor Red
      }
    }
  }
  ```
  Expected: no MISSING warnings.

- [ ] 4. Debug any generation failures:
  - Review the log file: `Get-Content "C:\claude\amplifier-docs\logs\*.log" | Select-String "ERROR"`
  - For failed pages: fix the prompt, then re-run with `-PageFilter "page-id"` to regenerate only that page
  - Common issues: prompt too long (split into smaller sections), claude --headless timeout (simplify prompt), bad HTML output (add explicit "output valid HTML5" instruction to prompt)

- [ ] 5. Browser verification — open in Chrome:
  - Navigate to `https://amplifier.ergonet.pl` — should redirect to `/en/index.html`
  - Click through all sidebar navigation links — each should load the correct page
  - Verify design system applied: deep blue background, gold headers, sidebar visible
  - Verify Fragment Mono font in code blocks
  - Test mobile view: resize to < 768px, hamburger should appear

- [ ] 6. Commit all generated EN pages:
  ```bash
  git add en/
  git commit -m "feat: initial EN page generation — all 18 pages

  Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
  ```

---

## Task 9: Polish Translation — All Pages

**Agent:** modular-builder

**Files:**
- Generate: all PL HTML pages under `C:\claude\amplifier-docs\pl\`

**Steps:**

- [ ] 1. Run translation pass for all pages:
  ```powershell
  cd C:\claude\amplifier-docs
  powershell -File generate.ps1 -Force
  ```
  (Without -SkipTranslation this time — will translate all EN pages.)

  Alternatively, run translation only (if generate.ps1 supports it):
  ```powershell
  powershell -File generate.ps1 -Force -PageFilter ".*"
  ```

- [ ] 2. Verify each PL page exists and is non-empty:
  ```powershell
  $plPages = @(
    "pl\index.html", "pl\manual.html", "pl\commands.html", "pl\agents.html",
    "pl\deep-dives\self-improvement.html", "pl\deep-dives\effort-steering.html",
    "pl\deep-dives\autocontext.html", "pl\deep-dives\workflows.html",
    "pl\platform\index.html", "pl\platform\linux.html", "pl\platform\windows.html",
    "pl\projects\index.html", "pl\projects\fusecp.html", "pl\projects\genetics.html",
    "pl\projects\siem.html", "pl\projects\amplifier.html",
    "pl\roadmap.html", "pl\sessions\index.html"
  )
  foreach ($page in $plPages) {
    $path = "C:\claude\amplifier-docs\$page"
    $exists = Test-Path $path
    $size = if ($exists) { (Get-Item $path).Length } else { 0 }
    Write-Host "$page : exists=$exists size=$size"
  }
  ```

- [ ] 3. Validate Polish translation quality — spot check 3 pages:
  ```powershell
  # Check that Polish text is present (not just English copied)
  $plContent = Get-Content "C:\claude\amplifier-docs\pl\index.html" -Raw
  # Polish markers: common Polish words that should appear in a technical translation
  $polishMarkers = @("Podręcznik", "Komendy", "Platforma", "Agenci", "Sesje", "Projekty")
  foreach ($marker in $polishMarkers) {
    if ($plContent -match $marker) { Write-Host "FOUND Polish: $marker" -ForegroundColor Green }
    else { Write-Host "MISSING Polish: $marker" -ForegroundColor Yellow }
  }
  ```

- [ ] 4. Verify code blocks are untranslated:
  - Open `pl\commands.html` — command names like `/brainstorm`, `/self-eval` must be in English
  - Open `pl\platform\linux.html` — file paths must be unchanged
  - Open `pl\agents.html` — agent names like `agentic-search`, `bug-hunter` must be unchanged

- [ ] 5. Test language switcher in browser:
  - Navigate to `https://amplifier.ergonet.pl/en/index.html`
  - Click "PL" language switcher — should navigate to `https://amplifier.ergonet.pl/pl/index.html`
  - Click "EN" — should navigate back
  - Verify the switcher correctly swaps `/en/` ↔ `/pl/` in the URL for all pages

- [ ] 6. Fix any translation issues — re-run individual page translation:
  ```powershell
  powershell -File generate.ps1 -PageFilter "manual" -Force
  ```

- [ ] 7. Commit all PL pages:
  ```bash
  git add pl/
  git commit -m "feat: Polish translation — all 18 pages generated

  Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
  ```

---

## Task 10: LLM Documentation Layer

**Agent:** modular-builder

**Files:**
- Create/verify: `C:\claude\amplifier-docs\llms.txt`
- Create/verify: `C:\claude\amplifier-docs\llms-full.txt`
- Create/verify: `C:\claude\amplifier-docs\llms-structured.json`

**Steps:**

- [ ] 1. Verify `C:\claude\amplifier-docs\llms.txt` was generated by `generate.ps1`. It must follow the standard llms.txt format:
  ```
  # Amplifier Documentation
  # https://amplifier.ergonet.pl

  > https://amplifier.ergonet.pl/en/index.html home
  Landing page and navigation hub for the Amplifier AI development platform.

  > https://amplifier.ergonet.pl/en/manual.html manual
  Complete operational guide for using the Amplifier AI development platform.
  ...
  ```
  Validate: 18+ entries, one per page, each with URL and description.

- [ ] 2. Verify `C:\claude\amplifier-docs\llms-full.txt`:
  ```powershell
  $fullTxt = Get-Content "C:\claude\amplifier-docs\llms-full.txt" -Raw
  Write-Host "Size: $($fullTxt.Length) characters"
  Write-Host "Sections: $((Select-String '===' 'C:\claude\amplifier-docs\llms-full.txt').Count)"
  ```
  Expected: > 50,000 characters, 18+ sections delimited by `=== page-id ===`.

- [ ] 3. Enhance `C:\claude\amplifier-docs\llms-structured.json` with richer data. Run a generation pass to extract structured data from the generated HTML pages:
  ```powershell
  # Extract command data from en/commands.html
  # Extract agent data from en/agents.html
  # Build structured JSON with arrays: commands[], agents[], workflows[], platform{}

  $structured = @{
    generated = (Get-Date -Format 'o')
    site = "https://amplifier.ergonet.pl"
    pages = @()
    commands = @()  # Populated by parsing en/commands.html
    agents = @()    # Populated by parsing en/agents.html
    workflows = @("brainstorm→create-plan→subagent-dev", "debug→tdd→verify", "retro→techdebt→self-improve")
    platform = @{
      linux = "172.31.250.2"
      windows = "172.31.251.100"
      python = "uv 3.13"
      nodejs = "v24"
    }
  }
  # Add page metadata from LLM JSON embedded in each page
  foreach ($page in (Get-ChildItem "C:\claude\amplifier-docs\en" -Recurse -Filter "*.html")) {
    $content = Get-Content $page.FullName -Raw
    if ($content -match '<script type="application/llm\+json">([\s\S]*?)</script>') {
      try {
        $meta = $Matches[1] | ConvertFrom-Json
        $structured.pages += $meta
      } catch { }
    }
  }
  $structured | ConvertTo-Json -Depth 10 | Set-Content "C:\claude\amplifier-docs\llms-structured.json" -Encoding UTF8
  ```

- [ ] 4. Validate JSON parses correctly:
  ```powershell
  $json = Get-Content "C:\claude\amplifier-docs\llms-structured.json" | ConvertFrom-Json
  Write-Host "Pages: $($json.pages.Count)"
  Write-Host "Valid JSON: True"
  ```
  Expected: pages count ≥ 18, no parse errors.

- [ ] 5. Verify all 3 LLM files are accessible via HTTPS:
  ```bash
  curl -sk https://amplifier.ergonet.pl/llms.txt | head -5
  curl -sk https://amplifier.ergonet.pl/llms-full.txt | head -3
  curl -sk https://amplifier.ergonet.pl/llms-structured.json | python3 -m json.tool --no-indent | head -5
  ```
  Expected: each returns content with HTTP 200.

- [ ] 6. Commit:
  ```bash
  git add llms.txt llms-full.txt llms-structured.json
  git commit -m "feat: add LLM documentation layer (llms.txt, llms-full.txt, llms-structured.json)

  Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
  ```

---

## Task 11: CLAUDE.md Integration

**Agent:** modular-builder

**Files:**
- Modify: `C:\claude\amplifier\CLAUDE.md`

**Steps:**

- [ ] 1. Read `C:\claude\amplifier\CLAUDE.md` and locate the "Memory and Documentation Tools" table. The table currently has columns: Tool | How to invoke | What it retrieves.

- [ ] 2. Add three new rows to the table after the existing entries:
  ```markdown
  | Docs site | `WebFetch("https://amplifier.ergonet.pl/llms.txt")` | Navigation index of all Amplifier documentation |
  | Full docs | `WebFetch("https://amplifier.ergonet.pl/llms-full.txt")` | Complete docs as concatenated plain text |
  | Structured | `WebFetch("https://amplifier.ergonet.pl/llms-structured.json")` | Machine-queryable JSON: commands, agents, workflows, platform |
  ```

- [ ] 3. Verify the table renders correctly (no broken markdown formatting, columns aligned).

- [ ] 4. Commit in the Amplifier repo (not amplifier-docs):
  ```bash
  cd /c/claude/amplifier
  git add CLAUDE.md
  git commit -m "docs: add amplifier docs site to CLAUDE.md tools table

  Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
  ```

- [ ] 5. Create a PR on Gitea for the CLAUDE.md update using `mcp__gitea__create_pull_request`:
  - Branch: `docs/amplifier-docs-site-claude-md`
  - Title: "docs: add amplifier docs site URLs to Memory and Documentation Tools table"
  - Body: summarize the 3 new WebFetch entries

---

## Task 12: Verification + Security Review

**Agent:** test-coverage (verification steps), security-guardian (security steps)

**Files:** Read-only verification — no file modifications expected.

**Verification Steps:**

- [ ] 1. DNS resolution:
  ```bash
  nslookup amplifier.ergonet.pl 172.31.251.101
  ```
  Expected: `Address: 172.31.251.100`

- [ ] 2. HTTPS redirect from root:
  ```bash
  curl -skI https://amplifier.ergonet.pl/
  ```
  Expected: `HTTP/2 302` (or 200 if default document serves directly) with body containing "Amplifier".

- [ ] 3. All EN pages — status 200:
  ```bash
  for page in en/index.html en/manual.html en/commands.html en/agents.html \
    en/deep-dives/self-improvement.html en/deep-dives/effort-steering.html \
    en/deep-dives/autocontext.html en/deep-dives/workflows.html \
    en/platform/index.html en/platform/linux.html en/platform/windows.html \
    en/projects/index.html en/projects/fusecp.html en/projects/genetics.html \
    en/projects/siem.html en/projects/amplifier.html \
    en/roadmap.html en/sessions/index.html; do
    STATUS=$(curl -sk -o /dev/null -w "%{http_code}" "https://amplifier.ergonet.pl/$page")
    echo "$STATUS $page"
  done
  ```
  Expected: all return `200`.

- [ ] 4. All PL pages — status 200 (same list with `pl/` prefix).

- [ ] 5. Sidebar nav links — verify all hrefs in sidebar point to existing pages:
  ```powershell
  $sidebarLinks = (Select-String -Path "C:\claude\amplifier-docs\en\index.html" -Pattern 'href="(/[^"]+\.html)"').Matches.Groups[1].Value
  foreach ($link in $sidebarLinks) {
    $path = "C:\claude\amplifier-docs" + $link
    $exists = Test-Path $path
    Write-Host "$exists : $link"
  }
  ```
  Expected: all `True`.

- [ ] 6. Language switcher hrefs — in each EN page, the PL switcher link must point to the corresponding `/pl/` URL and vice versa. Spot check 5 pages.

- [ ] 7. LLM files validation:
  ```bash
  curl -sk https://amplifier.ergonet.pl/llms.txt | wc -l          # expect > 20 lines
  curl -sk https://amplifier.ergonet.pl/llms-full.txt | wc -c     # expect > 50000 chars
  curl -sk https://amplifier.ergonet.pl/llms-structured.json | python3 -m json.tool > /dev/null && echo "Valid JSON"
  ```

- [ ] 8. Webhook listener test:
  ```bash
  curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:9099/amplifier-docs-rebuild \
    -H "Content-Type: application/json" \
    -H "X-Gitea-Signature: sha256=invalid" \
    -d '{"action":"closed"}'
  ```
  Expected: `403` (invalid signature rejected).

  ```bash
  # Test with valid signature (using stored secret)
  SECRET=$(cat /c/claude/amplifier-docs/.webhook-secret)
  BODY='{"action":"closed","number":99,"pull_request":{"merged":true}}'
  SIG="sha256=$(echo -n $BODY | openssl dgst -sha256 -hmac $SECRET | awk '{print $2}')"
  curl -s -w "\n%{http_code}" -X POST http://localhost:9099/amplifier-docs-rebuild \
    -H "Content-Type: application/json" \
    -H "X-Gitea-Signature: $SIG" \
    -d "$BODY"
  ```
  Expected: `{"status":"queued"}` with `200`.

- [ ] 9. Incremental regeneration test:
  ```powershell
  # Record current hash for one page
  $before = (Get-Item "C:\claude\amplifier-docs\en\agents.html").LastWriteTime

  # Modify a source file
  Add-Content "C:\claude\amplifier\AGENTS.md" "`n<!-- test change -->"

  # Run incremental (no -Force)
  powershell -File "C:\claude\amplifier-docs\generate.ps1" -PageFilter "agents"

  # Check that agents.html was regenerated but other pages were not
  $after = (Get-Item "C:\claude\amplifier-docs\en\agents.html").LastWriteTime
  Write-Host "agents.html regenerated: $($after -gt $before)"

  # Revert the test change
  $content = Get-Content "C:\claude\amplifier\AGENTS.md" | Select-Object -SkipLast 1
  Set-Content "C:\claude\amplifier\AGENTS.md" $content
  ```
  Expected: `agents.html regenerated: True`, other pages unchanged.

- [ ] 10. Force regeneration test:
  ```powershell
  powershell -File "C:\claude\amplifier-docs\generate.ps1" -Force -SkipTranslation -PageFilter "home"
  ```
  Expected: `en\index.html` regenerated, log entry confirms `-Force` mode.

**Security Steps:**

- [ ] 11. Scan generated HTML for sensitive data:
  ```powershell
  $patterns = @("api.key", "password", "secret", "172.31.251.1[0-9][0-9]", "fusecp-admin-key", "webhook-secret")
  foreach ($pattern in $patterns) {
    $matches = Select-String -Path "C:\claude\amplifier-docs\en\*.html" -Pattern $pattern -CaseSensitive:$false
    if ($matches) {
      Write-Host "SENSITIVE DATA FOUND ($pattern):" -ForegroundColor Red
      $matches | ForEach-Object { Write-Host "  $($_.Filename):$($_.LineNumber)" }
    }
  }
  ```
  Expected: no matches for sensitive patterns. Internal IPs in platform docs are acceptable but must be reviewed.

- [ ] 12. Verify webhook listener binds only to localhost:
  ```powershell
  netstat -an | Select-String "9099"
  ```
  Expected: only `127.0.0.1:9099` — not `0.0.0.0:9099`.

- [ ] 13. Verify HMAC validation — invalid signatures must be rejected with 403 (already tested in step 8). Additionally test:
  - Empty signature header → 403
  - Wrong algorithm prefix (`sha1=...` instead of `sha256=`) → 403

- [ ] 14. IIS directory listing check:
  ```bash
  curl -sk https://amplifier.ergonet.pl/en/
  ```
  Expected: either 403 (directory listing disabled) or 200 (serves index.html). Must NOT return a directory listing page showing file names.

- [ ] 15. Verification sign-off: document all pass/fail results in a summary comment or log file at `C:\claude\amplifier-docs\logs\verification-{DATE}.log`.

---

## Execution Notes

- **Wave 1 (parallel):** Tasks 1 (infrastructure)
- **Wave 2 (sequential):** Tasks 2, 3, 4 (design system → manifest → webhook — each depends on previous)
- **Wave 3 (parallel):** Tasks 5, 6, 7 (all prompt writing — independent of each other)
- **Wave 4 (sequential):** Task 8 (EN generation — depends on prompts)
- **Wave 5 (sequential):** Task 9 (PL translation — depends on EN pages)
- **Wave 6 (parallel):** Tasks 10, 11 (LLM layer + CLAUDE.md — independent)
- **Wave 7:** Task 12 (verification — must be last)

**Total estimated:** 12 tasks, 7 waves. Waves 3 can parallelize 3 agents.
