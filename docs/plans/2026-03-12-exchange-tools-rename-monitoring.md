# ExchangeTools Rename & Monitoring Implementation Plan

> **For Claude:** REQUIRED: Use /subagent-dev to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename ExchangePurge to ExchangeTools across the entire codebase, then add Exchange health monitoring with a background collector, dashboard, and report generation.

**Architecture:** Two-phase approach: (1) mechanical rename of all namespaces, projects, config, UI, docs, and Gitea repo; (2) new ExchangeTools.Monitor project with SQLite-backed health collector, Blazor dashboard pages, and HTML report generation from DB data.

**Tech Stack:** .NET 10, Blazor Server, SQLite (Microsoft.Data.Sqlite), PowerShell SDK, xUnit

---

### Task 0: Research — Map All Files Requiring Rename

**Agent:** agentic-search
**Model:** haiku
**max_turns:** 8

**READ-ONLY MODE: You are a research agent. Use ONLY Read, Glob, Grep, LS, and search tools. Do NOT use Edit, Write, Bash, or any tool that modifies files or executes commands. Your job is to gather and return information, not to make changes.**

**Objective:** Produce a complete inventory of every file in `C:\claude\exchange-purge\` containing the string `ExchangePurge` (case-sensitive), grouped by type. Output a structured list with file paths and line counts per file.

**Files:**
- Read: `C:\claude\exchange-purge\ExchangePurge.sln`
- Glob: `C:\claude\exchange-purge\src\**\*.cs`
- Glob: `C:\claude\exchange-purge\src\**\*.razor`
- Glob: `C:\claude\exchange-purge\src\**\*.csproj`
- Glob: `C:\claude\exchange-purge\src\**\*.json`
- Glob: `C:\claude\exchange-purge\tests\**\*.cs`
- Glob: `C:\claude\exchange-purge\tests\**\*.csproj`
- Glob: `C:\claude\exchange-purge\docs\**\*.md`
- Read: `C:\claude\exchange-purge\README.md`

- [ ] **Step 1: Inventory source .cs files**
  Grep for `ExchangePurge` in `C:\claude\exchange-purge\src\` (all .cs files). Record file paths and match counts.

- [ ] **Step 2: Inventory test .cs files**
  Grep for `ExchangePurge` in `C:\claude\exchange-purge\tests\` (all .cs files). Record file paths and match counts.

- [ ] **Step 3: Inventory .razor and .csproj files**
  Grep for `ExchangePurge` in all .razor and .csproj files. Record paths.

- [ ] **Step 4: Inventory config and solution files**
  Grep in `appsettings.json`, `ExchangePurge.sln`, `Program.cs`. Note exact line numbers for the strings `Exchange-Purge-Operators`, `Exchange-Purge-Approvers`, `exchange-purge.db`, `exchangepurge-.log`.

- [ ] **Step 5: Inventory docs and README**
  Grep `ExchangePurge` in `docs/` and `README.md`.

- [ ] **Step 6: Return structured report**
  Output the full list grouped as: Source .cs, Test .cs, .razor, .csproj, Config, Docs. Include total file count.

---

### Task 1: Rename — ExchangePurge → ExchangeTools (All Files)

**Agent:** modular-builder
**Model:** sonnet
**max_turns:** 20

**Objective:** Perform a complete mechanical rename of ExchangePurge to ExchangeTools across the entire solution. Use PowerShell scripts for bulk operations — do NOT manually edit individual files.

**Files:**
- Modify: `C:\claude\exchange-purge\ExchangePurge.sln` → rename to `ExchangeTools.sln`
- Modify: All 8 `*.csproj` files (rename + update content)
- Modify: All 80+ `.cs` files (namespace/using updates)
- Modify: All 24+ `.razor` files (using/PageTitle updates)
- Modify: `C:\claude\exchange-purge\src\ExchangePurge.Web\appsettings.json`
- Modify: `C:\claude\exchange-purge\src\ExchangePurge.Web\Program.cs`
- Modify: `C:\claude\exchange-purge\src\ExchangePurge.Web\Components\Layout\MainLayout.razor`
- Modify: `C:\claude\exchange-purge\README.md`

- [ ] **Step 1: Content replacement in all .cs and .razor files**

  Run this PowerShell script from `C:\claude\exchange-purge\`:

  ```powershell
  # Replace ExchangePurge with ExchangeTools in all .cs and .razor files
  $root = 'C:\claude\exchange-purge'
  $files = Get-ChildItem -Path $root -Recurse -Include '*.cs','*.razor' |
      Where-Object { $_.FullName -notmatch '\\obj\\' -and $_.FullName -notmatch '\\bin\\' }
  foreach ($file in $files) {
      $content = Get-Content $file.FullName -Raw -Encoding UTF8
      if ($content -match 'ExchangePurge') {
          $updated = $content -replace 'ExchangePurge', 'ExchangeTools'
          Set-Content -Path $file.FullName -Value $updated -Encoding UTF8 -NoNewline
          Write-Host "Updated: $($file.FullName)"
      }
  }
  ```

- [ ] **Step 2: Update .csproj files content**

  Run this PowerShell script to update all .csproj file contents:

  ```powershell
  $root = 'C:\claude\exchange-purge'
  $files = Get-ChildItem -Path $root -Recurse -Include '*.csproj' |
      Where-Object { $_.FullName -notmatch '\\obj\\' }
  foreach ($file in $files) {
      $content = Get-Content $file.FullName -Raw -Encoding UTF8
      if ($content -match 'ExchangePurge') {
          $updated = $content -replace 'ExchangePurge', 'ExchangeTools'
          # Also update the CLI AssemblyName
          $updated = $updated -replace '<AssemblyName>exchange-purge</AssemblyName>', '<AssemblyName>exchange-tools</AssemblyName>'
          Set-Content -Path $file.FullName -Value $updated -Encoding UTF8 -NoNewline
          Write-Host "Updated: $($file.FullName)"
      }
  }
  ```

- [ ] **Step 3: Rename project directories under src/**

  Run this PowerShell script to rename the four src project folders:

  ```powershell
  $root = 'C:\claude\exchange-purge'
  $renames = @(
      @{ Old = 'src\ExchangePurge.Core';       New = 'src\ExchangeTools.Core' },
      @{ Old = 'src\ExchangePurge.PowerShell'; New = 'src\ExchangeTools.PowerShell' },
      @{ Old = 'src\ExchangePurge.Cli';        New = 'src\ExchangeTools.Cli' },
      @{ Old = 'src\ExchangePurge.Web';        New = 'src\ExchangeTools.Web' }
  )
  foreach ($r in $renames) {
      $oldPath = Join-Path $root $r.Old
      $newPath = Join-Path $root $r.New
      if (Test-Path $oldPath) {
          Rename-Item -Path $oldPath -NewName (Split-Path $r.New -Leaf)
          Write-Host "Renamed: $($r.Old) -> $($r.New)"
      }
  }
  ```

- [ ] **Step 4: Rename project directories under tests/**

  ```powershell
  $root = 'C:\claude\exchange-purge'
  $renames = @(
      @{ Old = 'tests\ExchangePurge.Core.Tests';       New = 'tests\ExchangeTools.Core.Tests' },
      @{ Old = 'tests\ExchangePurge.PowerShell.Tests'; New = 'tests\ExchangeTools.PowerShell.Tests' },
      @{ Old = 'tests\ExchangePurge.E2E';              New = 'tests\ExchangeTools.E2E' },
      @{ Old = 'tests\ExchangePurge.Web.Tests';        New = 'tests\ExchangeTools.Web.Tests' }
  )
  foreach ($r in $renames) {
      $oldPath = Join-Path $root $r.Old
      $newPath = Join-Path $root $r.New
      if (Test-Path $oldPath) {
          Rename-Item -Path $oldPath -NewName (Split-Path $r.New -Leaf)
          Write-Host "Renamed: $($r.Old) -> $($r.New)"
      }
  }
  ```

- [ ] **Step 5: Rename .csproj files within their new directories**

  ```powershell
  $root = 'C:\claude\exchange-purge'
  $csprojFiles = Get-ChildItem -Path $root -Recurse -Filter 'ExchangePurge*.csproj' |
      Where-Object { $_.FullName -notmatch '\\obj\\' }
  foreach ($f in $csprojFiles) {
      $newName = $f.Name -replace 'ExchangePurge', 'ExchangeTools'
      Rename-Item -Path $f.FullName -NewName $newName
      Write-Host "Renamed csproj: $($f.Name) -> $newName"
  }
  ```

- [ ] **Step 6: Update ExchangePurge.sln — rename file and update all project paths/names**

  The .sln file content was already updated in Step 2 (ExchangePurge→ExchangeTools in all text files). Now rename the solution file itself:

  ```powershell
  $slnOld = 'C:\claude\exchange-purge\ExchangePurge.sln'
  $slnNew = 'C:\claude\exchange-purge\ExchangeTools.sln'
  if (Test-Path $slnOld) {
      Rename-Item -Path $slnOld -NewName 'ExchangeTools.sln'
      Write-Host "Renamed solution file to ExchangeTools.sln"
  }
  ```

  The solution file's project path references were updated in Step 2. Verify the .sln now contains paths like `src\ExchangeTools.Core\ExchangeTools.Core.csproj` (not the old `src\ExchangePurge.Core\...`). If Steps 1-2 ran before the directory renames, the paths are correct in content. The directory renames in Steps 3-4 match those paths.

- [ ] **Step 7: Update appsettings.json**

  Edit `C:\claude\exchange-purge\src\ExchangeTools.Web\appsettings.json`. The content replacement in Step 2 will have changed `ExchangePurge` strings. Verify manually that these specific values are correct:
  - `"ConnectionString": "Data Source=exchange-tools.db"` (was `exchange-purge.db`) — note: lowercase with hyphens, not camelCase — this was NOT caught by the ExchangePurge→ExchangeTools replace. Edit directly:

  ```powershell
  $path = 'C:\claude\exchange-purge\src\ExchangeTools.Web\appsettings.json'
  $content = Get-Content $path -Raw -Encoding UTF8
  $content = $content -replace 'exchange-purge\.db', 'exchange-tools.db'
  $content = $content -replace 'exchangepurge-\.log', 'exchangetools-.log'
  $content = $content -replace 'Exchange-Purge-Operators', 'Exchange-Tools-Operators'
  $content = $content -replace 'Exchange-Purge-Approvers', 'Exchange-Tools-Approvers'
  Set-Content -Path $path -Value $content -Encoding UTF8 -NoNewline
  Write-Host "Updated appsettings.json"
  ```

- [ ] **Step 8: Update Program.cs default group name strings**

  Edit `C:\claude\exchange-purge\src\ExchangeTools.Web\Program.cs`. The `ExchangePurge` → `ExchangeTools` replace in Step 1 handles namespace/using lines. Verify that lines 54-55 now read:
  ```csharp
  var requiredGroup = builder.Configuration.GetValue<string>("Auth:RequiredGroup") ?? "Exchange-Tools-Operators";
  var destructiveGroup = builder.Configuration.GetValue<string>("Auth:DestructiveGroup") ?? "Exchange-Tools-Approvers";
  ```
  If they still say `Exchange-Purge-*`, apply the same regex replace:
  ```powershell
  $path = 'C:\claude\exchange-purge\src\ExchangeTools.Web\Program.cs'
  $content = Get-Content $path -Raw -Encoding UTF8
  $content = $content -replace 'Exchange-Purge-Operators', 'Exchange-Tools-Operators'
  $content = $content -replace 'Exchange-Purge-Approvers', 'Exchange-Tools-Approvers'
  Set-Content -Path $path -Value $content -Encoding UTF8 -NoNewline
  ```

- [ ] **Step 9: Update MainLayout.razor brand name**

  Edit `C:\claude\exchange-purge\src\ExchangeTools.Web\Components\Layout\MainLayout.razor`. Line 5 should now read:
  ```razor
  <div class="px-4 pb-4 text-base font-semibold text-primary-400 border-b border-sidebar mb-2">ExchangeTools</div>
  ```
  The Step 1 replacement handles this. Verify visually.

- [ ] **Step 10: Update README.md**

  ```powershell
  $path = 'C:\claude\exchange-purge\README.md'
  $content = Get-Content $path -Raw -Encoding UTF8
  $content = $content -replace 'ExchangePurge', 'ExchangeTools'
  $content = $content -replace 'exchange-purge', 'exchange-tools'
  Set-Content -Path $path -Value $content -Encoding UTF8 -NoNewline
  ```

- [ ] **Step 11: Verify build succeeds**

  ```powershell
  cd C:\claude\exchange-purge
  dotnet build ExchangeTools.sln
  ```
  The build must succeed with zero errors. If there are errors, read the error output carefully — most likely causes are:
  - A project reference path still pointing to old folder name (fix in the relevant .csproj)
  - A `using` statement missed (fix with targeted search/replace)
  - The `ExchangeTools.Web.Endpoints.HealthEndpoint` reference in Program.cs (check this compiles correctly)

- [ ] **Step 12: Verify no ExchangePurge identifiers remain in source**

  ```powershell
  $remaining = Get-ChildItem -Path C:\claude\exchange-purge\src -Recurse -Include '*.cs','*.razor','*.csproj','*.json' |
      Where-Object { $_.FullName -notmatch '\\obj\\' -and $_.FullName -notmatch '\\bin\\' } |
      Select-String -Pattern 'ExchangePurge' |
      Select-Object -ExpandProperty Path -Unique
  if ($remaining) {
      Write-Host "REMAINING ExchangePurge references in:"
      $remaining | ForEach-Object { Write-Host "  $_" }
  } else {
      Write-Host "CLEAN: No ExchangePurge references remain in src/"
  }
  # Also check tests/
  $remainingTests = Get-ChildItem -Path C:\claude\exchange-purge\tests -Recurse -Include '*.cs','*.csproj' |
      Where-Object { $_.FullName -notmatch '\\obj\\' } |
      Select-String -Pattern 'ExchangePurge' |
      Select-Object -ExpandProperty Path -Unique
  if ($remainingTests) {
      Write-Host "REMAINING in tests:"
      $remainingTests | ForEach-Object { Write-Host "  $_" }
  }
  ```

- [ ] **Step 13: Run existing tests**

  ```powershell
  cd C:\claude\exchange-purge
  dotnet test ExchangeTools.sln --filter "FullyQualifiedName!~E2E" --no-build
  ```
  All existing unit tests must pass. The E2E tests are excluded as they require a live Exchange connection.

- [ ] **Step 14: Commit**

  ```bash
  cd /c/claude/exchange-purge
  git add -A
  git commit -m "$(cat <<'EOF'
  refactor: rename ExchangePurge to ExchangeTools across entire solution

  Mechanical rename of all namespaces, assemblies, project folders, .csproj
  files, .sln, config keys, AD group names, DB filename, log filename, and
  UI brand label. No logic changes — identifier substitution only.

  Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
  EOF
  )"
  ```

---

### Task 2: Update Docs — ExchangePurge References in Markdown

**Agent:** modular-builder
**Model:** haiku
**max_turns:** 8

**Objective:** Update all markdown files in `docs/` and the project root that reference ExchangePurge, changing them to ExchangeTools.

**Files:**
- Modify: `C:\claude\exchange-purge\docs\specs\2026-03-07-exchange-purge-design.md`
- Modify: Any other `.md` files in `docs/plans/` referencing ExchangePurge
- Modify: `C:\claude\exchange-purge\README.md` (if not fully covered by Task 1)

- [ ] **Step 1: Bulk replace in all markdown files**

  ```powershell
  $root = 'C:\claude\exchange-purge'
  $mdFiles = Get-ChildItem -Path $root -Recurse -Include '*.md' |
      Where-Object { $_.FullName -notmatch '\\obj\\' -and $_.FullName -notmatch '\\bin\\' }
  foreach ($f in $mdFiles) {
      $content = Get-Content $f.FullName -Raw -Encoding UTF8
      if ($content -match 'ExchangePurge|exchange-purge') {
          $updated = $content -replace 'ExchangePurge', 'ExchangeTools'
          $updated = $updated -replace 'exchange-purge', 'exchange-tools'
          Set-Content -Path $f.FullName -Value $updated -Encoding UTF8 -NoNewline
          Write-Host "Updated: $($f.FullName)"
      }
  }
  ```

- [ ] **Step 2: Verify docs updated**

  Check `docs/specs/2026-03-07-exchange-purge-design.md` — note the filename itself is NOT renamed (the spec says only update cross-references, not rename the spec file). The file content should now say ExchangeTools throughout.

- [ ] **Step 3: Commit**

  ```bash
  cd /c/claude/exchange-purge
  git add docs/ README.md
  git commit -m "$(cat <<'EOF'
  docs: update ExchangePurge references to ExchangeTools in markdown files

  Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
  EOF
  )"
  ```

---

### Task 3: Gitea Repo Rename + Update Git Remote

**Agent:** modular-builder
**Model:** haiku
**max_turns:** 6

**Objective:** Rename the Gitea repository from `exchange-purge` to `exchange-tools` and update the local git remote URL.

**Files:**
- Modify: `C:\claude\exchange-purge\.git\config` (remote URL)

- [ ] **Step 1: Rename Gitea repo via MCP**

  Use `mcp__gitea__edit_repo` (or the appropriate Gitea MCP rename tool) to rename the repository:
  - Owner: `claude` (or `admin` — check with `mcp__gitea__get_my_user_info`)
  - Repo: `exchange-purge`
  - New name: `exchange-tools`

  If the MCP tool does not support repo rename directly, use the Gitea web API:
  ```bash
  curl -X PATCH "https://gitea.ergonet.pl:3001/api/v1/repos/admin/exchange-purge" \
    -H "Content-Type: application/json" \
    -H "Authorization: token $(cat ~/.gitea-token)" \
    -d '{"name": "exchange-tools"}'
  ```

- [ ] **Step 2: Update local git remote URL**

  ```bash
  cd /c/claude/exchange-purge
  git remote set-url origin https://gitea.ergonet.pl:3001/admin/exchange-tools.git
  git remote -v
  ```

- [ ] **Step 3: Push renamed branch to verify remote works**

  ```bash
  cd /c/claude/exchange-purge
  git push origin main
  ```

- [ ] **Step 4: Confirm**

  Verify `git remote -v` shows `https://gitea.ergonet.pl:3001/admin/exchange-tools.git` for origin.

---

### Task 4: ExchangeTools.Monitor — Project Scaffold, Models, SQLite Schema

**Agent:** modular-builder
**Model:** sonnet
**max_turns:** 15

**Objective:** Create the `src/ExchangeTools.Monitor/` class library with all model types, the SQLite schema initialization service (`HealthRepository`), and wire it into the solution.

**Files:**
- Create: `C:\claude\exchange-purge\src\ExchangeTools.Monitor\ExchangeTools.Monitor.csproj`
- Create: `C:\claude\exchange-purge\src\ExchangeTools.Monitor\Models\OverallStatus.cs`
- Create: `C:\claude\exchange-purge\src\ExchangeTools.Monitor\Models\HealthSnapshot.cs`
- Create: `C:\claude\exchange-purge\src\ExchangeTools.Monitor\Models\HealthCheckResult.cs`
- Create: `C:\claude\exchange-purge\src\ExchangeTools.Monitor\Models\HealthReport.cs`
- Create: `C:\claude\exchange-purge\src\ExchangeTools.Monitor\Models\MonitorConfig.cs`
- Create: `C:\claude\exchange-purge\src\ExchangeTools.Monitor\HealthRepository.cs`
- Modify: `C:\claude\exchange-purge\ExchangeTools.sln` (add Monitor project)
- Modify: `C:\claude\exchange-purge\src\ExchangeTools.Web\ExchangeTools.Web.csproj` (add ProjectReference)

- [ ] **Step 1: Create ExchangeTools.Monitor.csproj**

  ```xml
  <Project Sdk="Microsoft.NET.Sdk">
    <PropertyGroup>
      <TargetFramework>net10.0</TargetFramework>
      <RootNamespace>ExchangeTools.Monitor</RootNamespace>
      <AssemblyName>ExchangeTools.Monitor</AssemblyName>
      <GenerateDocumentationFile>true</GenerateDocumentationFile>
    </PropertyGroup>
    <ItemGroup>
      <PackageReference Include="Microsoft.Data.Sqlite" Version="10.0.0-*" />
      <PackageReference Include="Microsoft.Extensions.Hosting.Abstractions" Version="10.0.0-*" />
      <PackageReference Include="Microsoft.Extensions.Logging.Abstractions" Version="10.0.0-*" />
      <PackageReference Include="Microsoft.Extensions.Configuration.Abstractions" Version="10.0.0-*" />
      <PackageReference Include="Serilog" Version="4.3.1" />
    </ItemGroup>
    <ItemGroup>
      <ProjectReference Include="..\ExchangeTools.PowerShell\ExchangeTools.PowerShell.csproj" />
    </ItemGroup>
  </Project>
  ```

- [ ] **Step 2: Create OverallStatus.cs**

  ```csharp
  namespace ExchangeTools.Monitor.Models;

  /// <summary>Aggregate health status for a collection snapshot.</summary>
  public enum OverallStatus
  {
      Green,
      Yellow,
      Red,
      Collecting,
      Failed
  }
  ```

- [ ] **Step 3: Create HealthSnapshot.cs**

  ```csharp
  using ExchangeTools.Monitor.Models;

  namespace ExchangeTools.Monitor.Models;

  /// <summary>One collection run's aggregate result stored in health_snapshots.</summary>
  public sealed class HealthSnapshot
  {
      public long Id { get; init; }
      public DateTime Timestamp { get; init; }
      public OverallStatus OverallStatus { get; set; }
      public int? DurationMs { get; set; }
  }
  ```

- [ ] **Step 4: Create HealthCheckResult.cs**

  ```csharp
  namespace ExchangeTools.Monitor.Models;

  /// <summary>One check result row within a snapshot, stored in health_check_results.</summary>
  public sealed class HealthCheckResult
  {
      public long Id { get; init; }
      public long SnapshotId { get; init; }

      /// <summary>Category matches the check type: ServiceHealth, DAGReplication, DatabaseCopies,
      /// Certificates, TransportQueues, ManagedAvailability, BigFunnelIndex, DiskSpace, Endpoints, ServerComponents.</summary>
      public string Category { get; init; } = string.Empty;

      public string CheckName { get; init; } = string.Empty;

      /// <summary>Server name this result applies to. Null for multi-server or global checks.</summary>
      public string? Server { get; init; }

      /// <summary>Passed | Failed | Warning | Info</summary>
      public string Status { get; init; } = string.Empty;

      /// <summary>Check-specific structured data serialized as JSON.</summary>
      public string DetailJson { get; init; } = string.Empty;
  }
  ```

- [ ] **Step 5: Create HealthReport.cs**

  ```csharp
  namespace ExchangeTools.Monitor.Models;

  /// <summary>Index row for a generated HTML health report, stored in health_reports.</summary>
  public sealed class HealthReport
  {
      public long Id { get; init; }
      public DateTime Timestamp { get; init; }
      public long SnapshotId { get; init; }

      /// <summary>Relative path under the reports/ directory.</summary>
      public string Filename { get; init; } = string.Empty;

      public OverallStatus OverallStatus { get; init; }
  }
  ```

- [ ] **Step 6: Create MonitorConfig.cs**

  ```csharp
  namespace ExchangeTools.Monitor.Models;

  public sealed class MonitorConfig
  {
      public int CollectionIntervalMinutes { get; init; } = 15;
      public string ReportSchedule { get; init; } = "0 8 * * *";
      public string[] Servers { get; init; } = Array.Empty<string>();
      public EndpointConfig[] Endpoints { get; init; } = Array.Empty<EndpointConfig>();
      public AlertThresholdsConfig AlertThresholds { get; init; } = new();
  }

  public sealed class EndpointConfig
  {
      public string Name { get; init; } = string.Empty;
      public string Url { get; init; } = string.Empty;
  }

  public sealed class AlertThresholdsConfig
  {
      public int CertExpiryRedDays { get; init; } = 14;
      public int CertExpiryYellowDays { get; init; } = 30;
      public int DiskFreeYellowPercent { get; init; } = 15;
  }
  ```

- [ ] **Step 7: Create HealthRepository.cs**

  Full implementation with `InitializeAsync()`, all CRUD methods for the three tables.

  ```csharp
  using ExchangeTools.Monitor.Models;
  using Microsoft.Data.Sqlite;

  namespace ExchangeTools.Monitor;

  /// <summary>
  /// SQLite data access for health_snapshots, health_check_results, and health_reports tables.
  /// Uses raw Microsoft.Data.Sqlite (no EF Core), consistent with the rest of the codebase.
  /// </summary>
  public sealed class HealthRepository
  {
      private readonly string _connStr;

      public HealthRepository(string connectionString)
      {
          _connStr = connectionString;
      }

      public async Task InitializeAsync()
      {
          await using var conn = new SqliteConnection(_connStr);
          await conn.OpenAsync();

          await using var cmd = conn.CreateCommand();
          cmd.CommandText = """
              CREATE TABLE IF NOT EXISTS health_snapshots (
                  id             INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp      TEXT    NOT NULL,
                  overall_status TEXT    NOT NULL,
                  duration_ms    INTEGER
              );

              CREATE TABLE IF NOT EXISTS health_check_results (
                  id            INTEGER PRIMARY KEY AUTOINCREMENT,
                  snapshot_id   INTEGER NOT NULL REFERENCES health_snapshots(id),
                  category      TEXT    NOT NULL,
                  check_name    TEXT    NOT NULL,
                  server        TEXT,
                  status        TEXT    NOT NULL,
                  detail_json   TEXT    NOT NULL
              );

              CREATE TABLE IF NOT EXISTS health_reports (
                  id             INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp      TEXT    NOT NULL,
                  snapshot_id    INTEGER NOT NULL REFERENCES health_snapshots(id),
                  filename       TEXT    NOT NULL,
                  overall_status TEXT    NOT NULL
              );
              """;
          await cmd.ExecuteNonQueryAsync();
      }

      // --- Snapshots ---

      public async Task<long> CreateSnapshotAsync(DateTime timestamp, OverallStatus status)
      {
          await using var conn = new SqliteConnection(_connStr);
          await conn.OpenAsync();
          await using var cmd = conn.CreateCommand();
          cmd.CommandText = """
              INSERT INTO health_snapshots (timestamp, overall_status)
              VALUES (@ts, @status);
              SELECT last_insert_rowid();
              """;
          cmd.Parameters.AddWithValue("@ts", timestamp.ToString("O"));
          cmd.Parameters.AddWithValue("@status", status.ToString());
          var result = await cmd.ExecuteScalarAsync();
          return Convert.ToInt64(result);
      }

      public async Task UpdateSnapshotAsync(long id, OverallStatus status, int durationMs)
      {
          await using var conn = new SqliteConnection(_connStr);
          await conn.OpenAsync();
          await using var cmd = conn.CreateCommand();
          cmd.CommandText = """
              UPDATE health_snapshots
              SET overall_status = @status, duration_ms = @ms
              WHERE id = @id;
              """;
          cmd.Parameters.AddWithValue("@status", status.ToString());
          cmd.Parameters.AddWithValue("@ms", durationMs);
          cmd.Parameters.AddWithValue("@id", id);
          await cmd.ExecuteNonQueryAsync();
      }

      public async Task<HealthSnapshot?> GetLatestSnapshotAsync()
      {
          await using var conn = new SqliteConnection(_connStr);
          await conn.OpenAsync();
          await using var cmd = conn.CreateCommand();
          cmd.CommandText = """
              SELECT id, timestamp, overall_status, duration_ms
              FROM health_snapshots
              WHERE overall_status NOT IN ('Collecting', 'Failed')
              ORDER BY id DESC LIMIT 1;
              """;
          await using var reader = await cmd.ExecuteReaderAsync();
          if (!await reader.ReadAsync()) return null;
          return MapSnapshot(reader);
      }

      public async Task<List<HealthSnapshot>> GetSnapshotsAsync(int limit = 100)
      {
          await using var conn = new SqliteConnection(_connStr);
          await conn.OpenAsync();
          await using var cmd = conn.CreateCommand();
          cmd.CommandText = "SELECT id, timestamp, overall_status, duration_ms FROM health_snapshots ORDER BY id DESC LIMIT @limit;";
          cmd.Parameters.AddWithValue("@limit", limit);
          var results = new List<HealthSnapshot>();
          await using var reader = await cmd.ExecuteReaderAsync();
          while (await reader.ReadAsync())
              results.Add(MapSnapshot(reader));
          return results;
      }

      // --- Check Results ---

      public async Task InsertCheckResultAsync(HealthCheckResult result)
      {
          await using var conn = new SqliteConnection(_connStr);
          await conn.OpenAsync();
          await using var cmd = conn.CreateCommand();
          cmd.CommandText = """
              INSERT INTO health_check_results (snapshot_id, category, check_name, server, status, detail_json)
              VALUES (@snapshotId, @category, @checkName, @server, @status, @detailJson);
              """;
          cmd.Parameters.AddWithValue("@snapshotId", result.SnapshotId);
          cmd.Parameters.AddWithValue("@category", result.Category);
          cmd.Parameters.AddWithValue("@checkName", result.CheckName);
          cmd.Parameters.AddWithValue("@server", (object?)result.Server ?? DBNull.Value);
          cmd.Parameters.AddWithValue("@status", result.Status);
          cmd.Parameters.AddWithValue("@detailJson", result.DetailJson);
          await cmd.ExecuteNonQueryAsync();
      }

      public async Task<List<HealthCheckResult>> GetCheckResultsForSnapshotAsync(long snapshotId)
      {
          await using var conn = new SqliteConnection(_connStr);
          await conn.OpenAsync();
          await using var cmd = conn.CreateCommand();
          cmd.CommandText = """
              SELECT id, snapshot_id, category, check_name, server, status, detail_json
              FROM health_check_results WHERE snapshot_id = @snapshotId;
              """;
          cmd.Parameters.AddWithValue("@snapshotId", snapshotId);
          var results = new List<HealthCheckResult>();
          await using var reader = await cmd.ExecuteReaderAsync();
          while (await reader.ReadAsync())
              results.Add(MapCheckResult(reader));
          return results;
      }

      /// <summary>Returns check results for the last N snapshots for sparkline data, filtered by category.</summary>
      public async Task<List<HealthCheckResult>> GetCheckResultsForSparklineAsync(string category, int snapshotCount = 96)
      {
          await using var conn = new SqliteConnection(_connStr);
          await conn.OpenAsync();
          await using var cmd = conn.CreateCommand();
          cmd.CommandText = """
              SELECT r.id, r.snapshot_id, r.category, r.check_name, r.server, r.status, r.detail_json
              FROM health_check_results r
              INNER JOIN (
                  SELECT id FROM health_snapshots
                  WHERE overall_status NOT IN ('Collecting', 'Failed')
                  ORDER BY id DESC LIMIT @count
              ) s ON r.snapshot_id = s.id
              WHERE r.category = @category
              ORDER BY r.snapshot_id ASC;
              """;
          cmd.Parameters.AddWithValue("@count", snapshotCount);
          cmd.Parameters.AddWithValue("@category", category);
          var results = new List<HealthCheckResult>();
          await using var reader = await cmd.ExecuteReaderAsync();
          while (await reader.ReadAsync())
              results.Add(MapCheckResult(reader));
          return results;
      }

      // --- Reports ---

      public async Task<long> InsertReportAsync(HealthReport report)
      {
          await using var conn = new SqliteConnection(_connStr);
          await conn.OpenAsync();
          await using var cmd = conn.CreateCommand();
          cmd.CommandText = """
              INSERT INTO health_reports (timestamp, snapshot_id, filename, overall_status)
              VALUES (@ts, @snapshotId, @filename, @status);
              SELECT last_insert_rowid();
              """;
          cmd.Parameters.AddWithValue("@ts", report.Timestamp.ToString("O"));
          cmd.Parameters.AddWithValue("@snapshotId", report.SnapshotId);
          cmd.Parameters.AddWithValue("@filename", report.Filename);
          cmd.Parameters.AddWithValue("@status", report.OverallStatus.ToString());
          var result = await cmd.ExecuteScalarAsync();
          return Convert.ToInt64(result);
      }

      public async Task<List<HealthReport>> GetReportsAsync(int limit = 200)
      {
          await using var conn = new SqliteConnection(_connStr);
          await conn.OpenAsync();
          await using var cmd = conn.CreateCommand();
          cmd.CommandText = """
              SELECT id, timestamp, snapshot_id, filename, overall_status
              FROM health_reports ORDER BY id DESC LIMIT @limit;
              """;
          cmd.Parameters.AddWithValue("@limit", limit);
          var results = new List<HealthReport>();
          await using var reader = await cmd.ExecuteReaderAsync();
          while (await reader.ReadAsync())
              results.Add(MapReport(reader));
          return results;
      }

      public async Task<HealthReport?> GetReportByIdAsync(long id)
      {
          await using var conn = new SqliteConnection(_connStr);
          await conn.OpenAsync();
          await using var cmd = conn.CreateCommand();
          cmd.CommandText = "SELECT id, timestamp, snapshot_id, filename, overall_status FROM health_reports WHERE id = @id;";
          cmd.Parameters.AddWithValue("@id", id);
          await using var reader = await cmd.ExecuteReaderAsync();
          if (!await reader.ReadAsync()) return null;
          return MapReport(reader);
      }

      // --- Mappers ---

      private static HealthSnapshot MapSnapshot(SqliteDataReader r) => new()
      {
          Id = r.GetInt64(0),
          Timestamp = DateTime.Parse(r.GetString(1)),
          OverallStatus = Enum.Parse<OverallStatus>(r.GetString(2)),
          DurationMs = r.IsDBNull(3) ? null : r.GetInt32(3)
      };

      private static HealthCheckResult MapCheckResult(SqliteDataReader r) => new()
      {
          Id = r.GetInt64(0),
          SnapshotId = r.GetInt64(1),
          Category = r.GetString(2),
          CheckName = r.GetString(3),
          Server = r.IsDBNull(4) ? null : r.GetString(4),
          Status = r.GetString(5),
          DetailJson = r.GetString(6)
      };

      private static HealthReport MapReport(SqliteDataReader r) => new()
      {
          Id = r.GetInt64(0),
          Timestamp = DateTime.Parse(r.GetString(1)),
          SnapshotId = r.GetInt64(2),
          Filename = r.GetString(3),
          OverallStatus = Enum.Parse<OverallStatus>(r.GetString(4))
      };
  }
  ```

- [ ] **Step 8: Add ExchangeTools.Monitor to ExchangeTools.sln**

  Edit `C:\claude\exchange-purge\ExchangeTools.sln`. Add a new project entry. The Monitor project GUID should be freshly generated (use `[System.Guid]::NewGuid().ToString("B").ToUpper()` in PowerShell to generate one). Add after the ExchangeTools.Web project entry and before the closing `EndProject` of the src folder:

  ```
  Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "ExchangeTools.Monitor", "src\ExchangeTools.Monitor\ExchangeTools.Monitor.csproj", "{NEW-GUID-HERE}"
  EndProject
  ```

  Also add the Monitor project GUID to:
  - `GlobalSection(ProjectConfigurationPlatforms)` — 6 entries (Debug/Release × Any CPU/x64/x86)
  - `GlobalSection(NestedProjects)` — one entry mapping Monitor GUID to src folder GUID `{827E0CD3-B72D-47B6-A68D-7590B98EB39B}`

- [ ] **Step 9: Add ProjectReference to ExchangeTools.Web.csproj**

  Edit `C:\claude\exchange-purge\src\ExchangeTools.Web\ExchangeTools.Web.csproj`. Add inside the existing `<ItemGroup>` that contains other ProjectReferences (or create a new one):

  ```xml
  <ProjectReference Include="..\ExchangeTools.Monitor\ExchangeTools.Monitor.csproj" />
  ```

- [ ] **Step 10: Build verification**

  ```powershell
  cd C:\claude\exchange-purge
  dotnet build ExchangeTools.sln
  ```
  Must succeed with zero errors.

- [ ] **Step 11: Commit**

  ```bash
  cd /c/claude/exchange-purge
  git add src/ExchangeTools.Monitor/ ExchangeTools.sln src/ExchangeTools.Web/ExchangeTools.Web.csproj
  git commit -m "$(cat <<'EOF'
  feat: add ExchangeTools.Monitor project scaffold with models and HealthRepository

  New class library with SQLite schema (health_snapshots, health_check_results,
  health_reports), all model types, MonitorConfig, and full HealthRepository
  data access layer. Wired into solution and Web project reference.

  Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
  EOF
  )"
  ```

---

### Task 5: HealthCollector Background Service (All 10 Check Categories)

**Agent:** modular-builder
**Model:** sonnet
**max_turns:** 20

**Objective:** Implement the `HealthCollector` IHostedService that runs all 10 check categories on a configurable interval, using the scheduled-task pattern for Exchange cmdlets that require SYSTEM context, and stores results in SQLite via `HealthRepository`.

**Files:**
- Create: `C:\claude\exchange-purge\src\ExchangeTools.Monitor\HealthCollector.cs`
- Create: `C:\claude\exchange-purge\src\ExchangeTools.Monitor\CheckScripts\CollectionScript.ps1` (template, generated at runtime)

- [ ] **Step 1: Create HealthCollector.cs — class skeleton and startup**

  ```csharp
  using System.Diagnostics;
  using System.Text.Json;
  using ExchangeTools.Monitor.Models;
  using ExchangeTools.PowerShell;
  using Microsoft.Extensions.Hosting;
  using Microsoft.Extensions.Logging;
  using Serilog;

  namespace ExchangeTools.Monitor;

  /// <summary>
  /// Background service that collects Exchange health metrics on a configurable schedule
  /// and stores structured results in SQLite via HealthRepository.
  /// </summary>
  public sealed class HealthCollector : IHostedService, IDisposable
  {
      private readonly HealthRepository _repo;
      private readonly MonitorConfig _config;
      private readonly IExchangeConnection _exchange;
      private readonly ILogger<HealthCollector> _logger;
      private Timer? _timer;

      // Exposed for "Collect Now" button on the dashboard
      public Task? CurrentRun { get; private set; }
      public event Action? CollectionCompleted;

      public HealthCollector(
          HealthRepository repo,
          MonitorConfig config,
          IExchangeConnection exchange,
          ILogger<HealthCollector> logger)
      {
          _repo = repo;
          _config = config;
          _exchange = exchange;
          _logger = logger;
      }

      public Task StartAsync(CancellationToken ct)
      {
          var interval = TimeSpan.FromMinutes(_config.CollectionIntervalMinutes);
          _timer = new Timer(_ => _ = RunOnceAsync(), null, TimeSpan.Zero, interval);
          _logger.LogInformation("HealthCollector started. Interval: {Interval} minutes", _config.CollectionIntervalMinutes);
          return Task.CompletedTask;
      }

      public Task StopAsync(CancellationToken ct)
      {
          _timer?.Change(Timeout.Infinite, 0);
          return Task.CompletedTask;
      }

      public void Dispose() => _timer?.Dispose();

      /// <summary>Runs a single collection pass. Called by the timer and by the "Collect Now" button.</summary>
      public async Task RunOnceAsync()
      {
          var sw = Stopwatch.StartNew();
          var timestamp = DateTime.UtcNow;
          long snapshotId = 0;

          try
          {
              snapshotId = await _repo.CreateSnapshotAsync(timestamp, OverallStatus.Collecting);
              _logger.LogInformation("Health collection started. SnapshotId={SnapshotId}", snapshotId);

              var results = await CollectAllChecksAsync(snapshotId);

              foreach (var r in results)
                  await _repo.InsertCheckResultAsync(r);

              var overall = ComputeOverallStatus(results);
              sw.Stop();
              await _repo.UpdateSnapshotAsync(snapshotId, overall, (int)sw.ElapsedMilliseconds);
              _logger.LogInformation("Health collection complete. Status={Status} Duration={Ms}ms", overall, sw.ElapsedMilliseconds);
          }
          catch (Exception ex)
          {
              sw.Stop();
              _logger.LogError(ex, "Health collection failed. SnapshotId={SnapshotId}", snapshotId);
              if (snapshotId > 0)
                  await _repo.UpdateSnapshotAsync(snapshotId, OverallStatus.Failed, (int)sw.ElapsedMilliseconds);
          }
          finally
          {
              CollectionCompleted?.Invoke();
          }
      }
  ```

- [ ] **Step 2: Implement CollectAllChecksAsync — dispatches all 10 check methods in parallel where safe**

  The 10 checks fall into two execution groups:
  - **Group A (Exchange cmdlets via scheduled task / SYSTEM context):** ServiceHealth, ServerComponents, DAGReplication, DatabaseCopies, Certificates, TransportQueues, ManagedAvailability, BigFunnelIndex
  - **Group B (Direct execution — no Exchange snap-in required):** DiskSpace (WMI via Invoke-Command), Endpoints (HTTP probe)

  ```csharp
      private async Task<List<HealthCheckResult>> CollectAllChecksAsync(long snapshotId)
      {
          // Build the PowerShell script that collects all Exchange checks at once
          // to minimize scheduled task round-trips
          var exchangeResults = await RunExchangeCollectionScriptAsync(snapshotId);

          // Run disk and endpoint checks directly (no Exchange snap-in needed)
          var diskResults = await CollectDiskSpaceAsync(snapshotId);
          var endpointResults = await CollectEndpointsAsync(snapshotId);

          var all = new List<HealthCheckResult>();
          all.AddRange(exchangeResults);
          all.AddRange(diskResults);
          all.AddRange(endpointResults);
          return all;
      }
  ```

- [ ] **Step 3: Implement RunExchangeCollectionScriptAsync — scheduled task pattern**

  This method writes a PowerShell script, registers it as a scheduled task running as SYSTEM (so the Exchange snap-in loads correctly), executes it, reads back JSON output, then deserializes into `HealthCheckResult` objects.

  ```csharp
      private async Task<List<HealthCheckResult>> RunExchangeCollectionScriptAsync(long snapshotId)
      {
          var outputPath = Path.Combine(Path.GetTempPath(), $"et-health-{snapshotId}.json");
          var scriptPath = Path.Combine(Path.GetTempPath(), $"et-health-{snapshotId}.ps1");
          var servers = string.Join(",", _config.Servers.Select(s => $"'{s}'"));
          var maxMailboxes = 50;

          var script = $$"""
              $ErrorActionPreference = 'Continue'
              $servers = @({{servers}})
              $results = [System.Collections.Generic.List[object]]::new()

              function Add-Result($category, $checkName, $server, $status, $detail) {
                  $results.Add(@{
                      category = $category; checkName = $checkName
                      server = $server; status = $status
                      detailJson = ($detail | ConvertTo-Json -Compress -Depth 5)
                  })
              }

              # Load Exchange snap-in
              try {
                  Add-PSSnapin Microsoft.Exchange.Management.PowerShell.SnapIn -ErrorAction Stop
              } catch {
                  Add-Result 'ServiceHealth' 'SnapIn' $null 'Failed' @{ error = $_.ToString() }
                  $results | ConvertTo-Json -Depth 5 | Set-Content '{{outputPath}}' -Encoding UTF8
                  return
              }

              foreach ($srv in $servers) {
                  # 1. Service Health
                  try {
                      $sh = Test-ServiceHealth -Server $srv
                      foreach ($role in $sh) {
                          $notRunning = @($role.ServicesNotRunning)
                          $status = if ($notRunning.Count -eq 0) { 'Passed' } else { 'Failed' }
                          Add-Result 'ServiceHealth' $role.Role $srv $status @{
                              role = $role.Role
                              servicesRunning = @($role.ServicesRunning)
                              servicesNotRunning = $notRunning
                              runningCount = $role.ServicesRunning.Count
                              notRunningCount = $notRunning.Count
                          }
                      }
                  } catch { Add-Result 'ServiceHealth' 'Error' $srv 'Failed' @{ error = $_.ToString() } }

                  # 2. Server Components
                  try {
                      $sc = Get-ServerComponentState -Identity $srv
                      foreach ($comp in $sc) {
                          $status = if ($comp.State -eq 'Active') { 'Passed' } else { 'Warning' }
                          Add-Result 'ServerComponents' $comp.Component $srv $status @{
                              component = $comp.Component; state = $comp.State.ToString()
                          }
                      }
                  } catch { Add-Result 'ServerComponents' 'Error' $srv 'Failed' @{ error = $_.ToString() } }

                  # 3. DAG Replication
                  try {
                      $rh = Test-ReplicationHealth -Server $srv
                      foreach ($check in $rh) {
                          $status = if ($check.Result -eq 'Passed') { 'Passed' } else { 'Failed' }
                          Add-Result 'DAGReplication' $check.Check $srv $status @{
                              check = $check.Check; result = $check.Result.ToString()
                              error = $check.Error
                          }
                      }
                  } catch { Add-Result 'DAGReplication' 'Error' $srv 'Failed' @{ error = $_.ToString() } }

                  # 4. Certificates
                  try {
                      $certs = Get-ExchangeCertificate -Server $srv
                      foreach ($cert in $certs) {
                          $daysToExpiry = ($cert.NotAfter - (Get-Date)).TotalDays
                          $status = if ($daysToExpiry -lt {{_config.AlertThresholds.CertExpiryRedDays}}) { 'Failed' }
                                    elseif ($daysToExpiry -lt {{_config.AlertThresholds.CertExpiryYellowDays}}) { 'Warning' }
                                    else { 'Passed' }
                          Add-Result 'Certificates' $cert.Subject $srv $status @{
                              thumbprint = $cert.Thumbprint; subject = $cert.Subject
                              notAfter = $cert.NotAfter.ToString('O')
                              daysToExpiry = [int]$daysToExpiry
                              services = $cert.Services.ToString()
                          }
                      }
                  } catch { Add-Result 'Certificates' 'Error' $srv 'Failed' @{ error = $_.ToString() } }

                  # 5. Transport Queues
                  try {
                      $queues = Get-Queue -Server $srv
                      foreach ($q in $queues) {
                          $status = if ($q.MessageCount -gt 100) { 'Warning' } else { 'Passed' }
                          Add-Result 'TransportQueues' $q.Identity.ToString() $srv $status @{
                              identity = $q.Identity.ToString()
                              deliveryType = $q.DeliveryType.ToString()
                              messageCount = $q.MessageCount; status = $q.Status.ToString()
                          }
                      }
                  } catch { Add-Result 'TransportQueues' 'Error' $srv 'Failed' @{ error = $_.ToString() } }

                  # 6. Managed Availability
                  try {
                      $hr = Get-HealthReport -Server $srv
                      foreach ($hs in $hr) {
                          $status = if ($hs.AlertValue -eq 'Unhealthy') { 'Failed' }
                                    elseif ($hs.AlertValue -eq 'Degraded') { 'Warning' }
                                    else { 'Passed' }
                          Add-Result 'ManagedAvailability' $hs.HealthSet $srv $status @{
                              healthSet = $hs.HealthSet; alertValue = $hs.AlertValue.ToString()
                          }
                      }
                  } catch { Add-Result 'ManagedAvailability' 'Error' $srv 'Failed' @{ error = $_.ToString() } }
              }

              # 7. Database Copies (cluster-wide, run once)
              try {
                  $dbs = Get-MailboxDatabaseCopyStatus -AllDatabaseCopies
                  foreach ($db in $dbs) {
                      $status = if ($db.Status -eq 'Healthy') { 'Passed' }
                                elseif ($db.Status -eq 'Mounted') { 'Passed' }
                                else { 'Failed' }
                      $srv = if ($db.MailboxServer) { $db.MailboxServer } else { $db.Name.Split('\')[0] }
                      $ciState = if ($db.ContentIndexState) { $db.ContentIndexState.ToString() } else { 'Unknown' }
                      $ciStatus = if ($ciState -ne 'Healthy') { 'Warning' } else { 'Passed' }
                      if ($status -eq 'Failed') { $ciStatus = $status }
                      Add-Result 'DatabaseCopies' $db.Name $srv $status @{
                          databaseName = $db.DatabaseName; server = $srv
                          status = $db.Status.ToString()
                          copyQueueLength = $db.CopyQueueLength
                          replayQueueLength = $db.ReplayQueueLength
                          contentIndexState = $ciState
                      }
                  }
              } catch { Add-Result 'DatabaseCopies' 'Error' $null 'Failed' @{ error = $_.ToString() } }

              # 8. Big Funnel / Mailbox Index (sampled)
              try {
                  $mbxList = Get-Mailbox -ResultSize {{maxMailboxes}} -RecipientTypeDetails UserMailbox
                  $indexed = 0; $notIndexed = 0; $corrupted = 0
                  foreach ($mbx in $mbxList) {
                      try {
                          $stats = Get-MailboxStatistics -Identity $mbx.Alias
                          if ($stats.IsIndexingEnabled -eq $true) { $indexed++ }
                          else { $notIndexed++ }
                      } catch { $notIndexed++ }
                  }
                  $status = if ($notIndexed -gt ($indexed * 0.1)) { 'Warning' } else { 'Passed' }
                  Add-Result 'BigFunnelIndex' 'MailboxIndexing' $null $status @{
                      indexedCount = $indexed; notIndexedCount = $notIndexed
                      corruptedCount = $corrupted; sampledMailboxes = $mbxList.Count
                  }
              } catch { Add-Result 'BigFunnelIndex' 'Error' $null 'Failed' @{ error = $_.ToString() } }

              $results | ConvertTo-Json -Depth 5 | Set-Content '{{outputPath}}' -Encoding UTF8
              """;

          await File.WriteAllTextAsync(scriptPath, script);

          try
          {
              // Register and run as SYSTEM via scheduled task (same pattern as purge engine)
              var taskName = $"ExchangeTools-HealthCheck-{snapshotId}";
              var register = $"""
                  $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument '-NonInteractive -NoProfile -File "{scriptPath}"'
                  $principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -RunLevel Highest
                  Register-ScheduledTask -TaskName '{taskName}' -Action $action -Principal $principal -Force | Out-Null
                  Start-ScheduledTask -TaskName '{taskName}'
                  $timeout = 120
                  $elapsed = 0
                  do {{ Start-Sleep 2; $elapsed += 2; $info = Get-ScheduledTask -TaskName '{taskName}' }} while ($info.State -eq 'Running' -and $elapsed -lt $timeout)
                  Unregister-ScheduledTask -TaskName '{taskName}' -Confirm:$false
                  """;

              using var proc = new Process();
              proc.StartInfo = new ProcessStartInfo("powershell.exe",
                  $"-NonInteractive -NoProfile -Command \"{register.Replace("\"", "\\\"")}\"")
              {
                  UseShellExecute = false,
                  RedirectStandardOutput = true,
                  RedirectStandardError = true,
                  CreateNoWindow = true
              };
              proc.Start();
              await proc.WaitForExitAsync();

              if (!File.Exists(outputPath))
              {
                  _logger.LogWarning("Health collection script produced no output at {Path}", outputPath);
                  return [];
              }

              var json = await File.ReadAllTextAsync(outputPath);
              return DeserializeScriptOutput(json, snapshotId);
          }
          finally
          {
              if (File.Exists(scriptPath)) File.Delete(scriptPath);
              if (File.Exists(outputPath)) File.Delete(outputPath);
          }
      }
  ```

- [ ] **Step 4: Implement DeserializeScriptOutput**

  ```csharp
      private List<HealthCheckResult> DeserializeScriptOutput(string json, long snapshotId)
      {
          var results = new List<HealthCheckResult>();
          try
          {
              var items = JsonSerializer.Deserialize<JsonElement[]>(json);
              if (items is null) return results;

              foreach (var item in items)
              {
                  results.Add(new HealthCheckResult
                  {
                      SnapshotId = snapshotId,
                      Category = item.GetProperty("category").GetString() ?? "Unknown",
                      CheckName = item.GetProperty("checkName").GetString() ?? "Unknown",
                      Server = item.TryGetProperty("server", out var srv) && srv.ValueKind != JsonValueKind.Null
                          ? srv.GetString() : null,
                      Status = item.GetProperty("status").GetString() ?? "Info",
                      DetailJson = item.GetProperty("detailJson").GetString() ?? "{}"
                  });
              }
          }
          catch (Exception ex)
          {
              _logger.LogError(ex, "Failed to deserialize health check script output");
          }
          return results;
      }
  ```

- [ ] **Step 5: Implement CollectDiskSpaceAsync — WMI via Invoke-Command**

  ```csharp
      private async Task<List<HealthCheckResult>> CollectDiskSpaceAsync(long snapshotId)
      {
          var results = new List<HealthCheckResult>();

          foreach (var server in _config.Servers)
          {
              try
              {
                  using var proc = new Process();
                  var script = $"""
                      Invoke-Command -ComputerName '{server}' -ScriptBlock {{
                          Get-WmiObject Win32_LogicalDisk -Filter "DriveType=3" |
                          Select-Object DeviceID,
                              @{{n='FreeBytes';e={{$_.FreeSpace}}}},
                              @{{n='TotalBytes';e={{$_.Size}}}} |
                          ConvertTo-Json -Compress
                      }}
                      """;

                  proc.StartInfo = new ProcessStartInfo("powershell.exe",
                      $"-NonInteractive -NoProfile -Command \"{script.Replace("\"", "\\\"")}\"")
                  {
                      UseShellExecute = false,
                      RedirectStandardOutput = true,
                      CreateNoWindow = true
                  };
                  proc.Start();
                  var output = await proc.StandardOutput.ReadToEndAsync();
                  await proc.WaitForExitAsync();

                  var drives = JsonSerializer.Deserialize<JsonElement[]>(output.Trim());
                  if (drives is null) continue;

                  foreach (var drive in drives)
                  {
                      var free = drive.GetProperty("FreeBytes").GetInt64();
                      var total = drive.GetProperty("TotalBytes").GetInt64();
                      var freePct = total > 0 ? (double)free / total * 100 : 100;
                      var status = freePct < _config.AlertThresholds.DiskFreeYellowPercent ? "Warning" : "Passed";
                      var detail = JsonSerializer.Serialize(new
                      {
                          drive = drive.GetProperty("DeviceID").GetString(),
                          freeBytes = free, totalBytes = total,
                          freePct = Math.Round(freePct, 1)
                      });

                      results.Add(new HealthCheckResult
                      {
                          SnapshotId = snapshotId,
                          Category = "DiskSpace",
                          CheckName = drive.GetProperty("DeviceID").GetString() ?? "?",
                          Server = server,
                          Status = status,
                          DetailJson = detail
                      });
                  }
              }
              catch (Exception ex)
              {
                  _logger.LogWarning(ex, "Disk space check failed for server {Server}", server);
                  results.Add(new HealthCheckResult
                  {
                      SnapshotId = snapshotId, Category = "DiskSpace",
                      CheckName = "Error", Server = server, Status = "Failed",
                      DetailJson = JsonSerializer.Serialize(new { error = ex.Message })
                  });
              }
          }

          return results;
      }
  ```

- [ ] **Step 6: Implement CollectEndpointsAsync — HTTP probes**

  ```csharp
      private async Task<List<HealthCheckResult>> CollectEndpointsAsync(long snapshotId)
      {
          var results = new List<HealthCheckResult>();
          using var http = new HttpClient(new HttpClientHandler { ServerCertificateCustomValidationCallback = (_, _, _, _) => true });
          http.Timeout = TimeSpan.FromSeconds(10);

          foreach (var ep in _config.Endpoints)
          {
              var sw = Stopwatch.StartNew();
              try
              {
                  var response = await http.GetAsync(ep.Url);
                  sw.Stop();
                  var isOk = (int)response.StatusCode >= 200 && (int)response.StatusCode < 300;
                  results.Add(new HealthCheckResult
                  {
                      SnapshotId = snapshotId, Category = "Endpoints",
                      CheckName = ep.Name, Server = null,
                      Status = isOk ? "Passed" : "Failed",
                      DetailJson = JsonSerializer.Serialize(new
                      {
                          url = ep.Url, httpStatus = (int)response.StatusCode,
                          responseTimeMs = sw.ElapsedMilliseconds
                      })
                  });
              }
              catch (Exception ex)
              {
                  sw.Stop();
                  results.Add(new HealthCheckResult
                  {
                      SnapshotId = snapshotId, Category = "Endpoints",
                      CheckName = ep.Name, Server = null, Status = "Failed",
                      DetailJson = JsonSerializer.Serialize(new
                      {
                          url = ep.Url, error = ex.Message,
                          responseTimeMs = sw.ElapsedMilliseconds
                      })
                  });
              }
          }

          return results;
      }
  ```

- [ ] **Step 7: Implement ComputeOverallStatus**

  ```csharp
      private OverallStatus ComputeOverallStatus(List<HealthCheckResult> results)
      {
          // Red conditions
          var hasRed = results.Any(r =>
              (r.Category == "ServiceHealth" && r.Status == "Failed") ||
              (r.Category == "DAGReplication" && r.Status == "Failed") ||
              (r.Category == "Certificates" && r.Status == "Failed") ||
              (r.Category == "DatabaseCopies" && r.Status == "Failed") ||
              (r.Category == "Endpoints" && r.Status == "Failed"));

          if (hasRed) return OverallStatus.Red;

          // Yellow conditions
          var hasYellow = results.Any(r =>
              (r.Category == "Certificates" && r.Status == "Warning") ||
              (r.Category == "DiskSpace" && r.Status == "Warning") ||
              r.Status == "Warning");

          // Also check content index state in DatabaseCopies detail
          var dbCopyYellow = results
              .Where(r => r.Category == "DatabaseCopies" && r.Status == "Passed")
              .Any(r => {
                  try {
                      var d = JsonSerializer.Deserialize<JsonElement>(r.DetailJson);
                      return d.TryGetProperty("contentIndexState", out var ci) &&
                             ci.GetString() != "Healthy";
                  } catch { return false; }
              });

          if (hasYellow || dbCopyYellow) return OverallStatus.Yellow;

          return OverallStatus.Green;
      }
  }  // end class
  ```

- [ ] **Step 8: Build verification**

  ```powershell
  cd C:\claude\exchange-purge
  dotnet build ExchangeTools.sln
  ```
  Must succeed with zero errors.

- [ ] **Step 9: Commit**

  ```bash
  cd /c/claude/exchange-purge
  git add src/ExchangeTools.Monitor/HealthCollector.cs
  git commit -m "$(cat <<'EOF'
  feat: implement HealthCollector with all 10 Exchange health check categories

  Background service runs Exchange checks via scheduled-task pattern (SYSTEM
  context), WMI disk probes, and HTTP endpoint probes. Computes Green/Yellow/Red
  status per spec thresholds and stores results in SQLite.

  Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
  EOF
  )"
  ```

---

### Task 6: Health Dashboard Page and 8 Detail Components

**Agent:** modular-builder
**Model:** sonnet
**max_turns:** 20

**Objective:** Create the `/health` Blazor dashboard page with status banner, summary cards with sparklines, collapsible detail sections, and action buttons. Create all 8 reusable detail components.

**Files:**
- Create: `C:\claude\exchange-purge\src\ExchangeTools.Web\Components\Pages\HealthDashboardPage.razor`
- Create: `C:\claude\exchange-purge\src\ExchangeTools.Web\Components\Health\ServiceHealthDetail.razor`
- Create: `C:\claude\exchange-purge\src\ExchangeTools.Web\Components\Health\DagReplicationDetail.razor`
- Create: `C:\claude\exchange-purge\src\ExchangeTools.Web\Components\Health\DatabaseCopiesDetail.razor`
- Create: `C:\claude\exchange-purge\src\ExchangeTools.Web\Components\Health\CertificatesDetail.razor`
- Create: `C:\claude\exchange-purge\src\ExchangeTools.Web\Components\Health\TransportQueuesDetail.razor`
- Create: `C:\claude\exchange-purge\src\ExchangeTools.Web\Components\Health\ManagedAvailabilityDetail.razor`
- Create: `C:\claude\exchange-purge\src\ExchangeTools.Web\Components\Health\DiskSpaceDetail.razor`
- Create: `C:\claude\exchange-purge\src\ExchangeTools.Web\Components\Health\EndpointsDetail.razor`

- [ ] **Step 1: Create HealthDashboardPage.razor**

  ```razor
  @page "/health"
  @attribute [Authorize(Policy = "Operator")]
  @inject HealthRepository HealthRepo
  @inject HealthCollector Collector
  @inject ILogger<HealthDashboardPage> Logger
  @implements IDisposable
  @using ExchangeTools.Monitor
  @using ExchangeTools.Monitor.Models
  @using System.Text.Json

  <PageTitle>Health Dashboard - ExchangeTools</PageTitle>

  @if (_snapshot is null)
  {
      <div class="flex items-center justify-center h-64">
          <p class="text-sidebar-muted">No health data collected yet. Click "Collect Now" to run the first check.</p>
      </div>
  }
  else
  {
      <!-- Status Banner -->
      <div class="@GetBannerClass() rounded-lg p-4 mb-6 flex items-center justify-between">
          <div>
              <span class="text-lg font-bold uppercase">@_snapshot.OverallStatus.ToString()</span>
              <span class="ml-4 text-sm opacity-80">Last collected @GetRelativeTime(_snapshot.Timestamp)</span>
          </div>
          <div class="text-sm opacity-80">Next collection in @GetCountdown()</div>
      </div>

      <!-- Summary Cards -->
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
          <div class="bg-surface rounded-lg p-4 border border-sidebar">
              <div class="text-xs text-sidebar-muted mb-1">Services</div>
              <div class="text-2xl font-bold @GetCardColor("ServiceHealth")">@GetServiceSummary()</div>
              <div class="text-xs text-sidebar-muted mt-1">running/total</div>
          </div>
          <div class="bg-surface rounded-lg p-4 border border-sidebar">
              <div class="text-xs text-sidebar-muted mb-1">DAG</div>
              <div class="text-2xl font-bold @GetCardColor("DAGReplication")">@GetDagSummary()</div>
              <div class="text-xs text-sidebar-muted mt-1">checks passed</div>
          </div>
          <div class="bg-surface rounded-lg p-4 border border-sidebar">
              <div class="text-xs text-sidebar-muted mb-1">Certificates</div>
              <div class="text-2xl font-bold @GetCardColor("Certificates")">@GetCertSummary()</div>
              <div class="text-xs text-sidebar-muted mt-1">days to nearest expiry</div>
          </div>
          <div class="bg-surface rounded-lg p-4 border border-sidebar">
              <div class="text-xs text-sidebar-muted mb-1">Disk</div>
              <div class="text-2xl font-bold @GetCardColor("DiskSpace")">@GetDiskSummary()</div>
              <div class="text-xs text-sidebar-muted mt-1">lowest free %</div>
          </div>
          <div class="bg-surface rounded-lg p-4 border border-sidebar">
              <div class="text-xs text-sidebar-muted mb-1">Endpoints</div>
              <div class="text-2xl font-bold @GetCardColor("Endpoints")">@GetEndpointSummary()</div>
              <div class="text-xs text-sidebar-muted mt-1">probes ok</div>
          </div>
          <div class="bg-surface rounded-lg p-4 border border-sidebar">
              <div class="text-xs text-sidebar-muted mb-1">Queues</div>
              <div class="text-2xl font-bold @GetCardColor("TransportQueues")">@GetQueueSummary()</div>
              <div class="text-xs text-sidebar-muted mt-1">total messages</div>
          </div>
      </div>

      <!-- Action Bar -->
      <div class="flex gap-3 mb-6">
          <button @onclick="CollectNow" disabled="@_collecting"
                  class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 transition-colors">
              @(_collecting ? "Collecting..." : "Collect Now")
          </button>
          <button @onclick="GenerateReport"
                  class="px-4 py-2 bg-surface border border-sidebar text-body rounded-md hover:bg-sidebar-hover transition-colors">
              Generate Report
          </button>
      </div>

      <!-- Detail Sections -->
      <div class="space-y-4">
          <ServiceHealthDetail Results="_checkResults.Where(r => r.Category == "ServiceHealth").ToList()" />
          <DagReplicationDetail Results="_checkResults.Where(r => r.Category == "DAGReplication").ToList()" />
          <DatabaseCopiesDetail Results="_checkResults.Where(r => r.Category == "DatabaseCopies").ToList()" />
          <CertificatesDetail Results="_checkResults.Where(r => r.Category == "Certificates").ToList()" />
          <TransportQueuesDetail Results="_checkResults.Where(r => r.Category == "TransportQueues").ToList()" />
          <ManagedAvailabilityDetail Results="_checkResults.Where(r => r.Category == "ManagedAvailability").ToList()" />
          <DiskSpaceDetail Results="_checkResults.Where(r => r.Category == "DiskSpace").ToList()" />
          <EndpointsDetail Results="_checkResults.Where(r => r.Category == "Endpoints").ToList()" />
      </div>
  }

  @code {
      private HealthSnapshot? _snapshot;
      private List<HealthCheckResult> _checkResults = [];
      private bool _collecting;
      private Timer? _refreshTimer;

      protected override async Task OnInitializedAsync()
      {
          await LoadDataAsync();
          Collector.CollectionCompleted += OnCollectionCompleted;
          _refreshTimer = new Timer(_ => InvokeAsync(StateHasChanged), null,
              TimeSpan.FromSeconds(30), TimeSpan.FromSeconds(30));
      }

      private async Task LoadDataAsync()
      {
          _snapshot = await HealthRepo.GetLatestSnapshotAsync();
          if (_snapshot is not null)
              _checkResults = await HealthRepo.GetCheckResultsForSnapshotAsync(_snapshot.Id);
      }

      private void OnCollectionCompleted()
      {
          _collecting = false;
          InvokeAsync(async () => { await LoadDataAsync(); StateHasChanged(); });
      }

      private async Task CollectNow()
      {
          _collecting = true;
          StateHasChanged();
          _ = Collector.RunOnceAsync();
      }

      private async Task GenerateReport()
      {
          // Handled in Task 7 — ReportGenerator
          if (_snapshot is null) return;
          Logger.LogInformation("On-demand report generation triggered for snapshot {Id}", _snapshot.Id);
      }

      public void Dispose()
      {
          _refreshTimer?.Dispose();
          Collector.CollectionCompleted -= OnCollectionCompleted;
      }

      private string GetBannerClass() => _snapshot?.OverallStatus switch
      {
          OverallStatus.Green  => "bg-green-700 text-white",
          OverallStatus.Yellow => "bg-amber-600 text-white",
          OverallStatus.Red    => "bg-red-700 text-white",
          _                    => "bg-gray-600 text-white"
      };

      private string GetCardColor(string category)
      {
          var hasFail = _checkResults.Any(r => r.Category == category && r.Status == "Failed");
          var hasWarn = _checkResults.Any(r => r.Category == category && r.Status == "Warning");
          return hasFail ? "text-red-400" : hasWarn ? "text-amber-400" : "text-green-400";
      }

      private string GetRelativeTime(DateTime utc)
      {
          var diff = DateTime.UtcNow - utc;
          if (diff.TotalMinutes < 1) return "just now";
          if (diff.TotalMinutes < 60) return $"{(int)diff.TotalMinutes} minutes ago";
          return $"{(int)diff.TotalHours} hours ago";
      }

      private string GetCountdown()
      {
          if (_snapshot is null) return "—";
          // Approximate: last snapshot + interval
          return "~soon";
      }

      private string GetServiceSummary()
      {
          var all = _checkResults.Where(r => r.Category == "ServiceHealth").ToList();
          var passed = all.Count(r => r.Status == "Passed");
          return $"{passed}/{all.Count}";
      }

      private string GetDagSummary()
      {
          var all = _checkResults.Where(r => r.Category == "DAGReplication").ToList();
          var passed = all.Count(r => r.Status == "Passed");
          return $"{passed}/{all.Count}";
      }

      private string GetCertSummary()
      {
          var certs = _checkResults.Where(r => r.Category == "Certificates").ToList();
          if (!certs.Any()) return "—";
          var minDays = certs
              .Select(r => { try { var d = JsonSerializer.Deserialize<JsonElement>(r.DetailJson); return d.TryGetProperty("daysToExpiry", out var v) ? v.GetInt32() : 999; } catch { return 999; } })
              .Min();
          return $"{minDays}d";
      }

      private string GetDiskSummary()
      {
          var disks = _checkResults.Where(r => r.Category == "DiskSpace").ToList();
          if (!disks.Any()) return "—";
          var minPct = disks
              .Select(r => { try { var d = JsonSerializer.Deserialize<JsonElement>(r.DetailJson); return d.TryGetProperty("freePct", out var v) ? v.GetDouble() : 100.0; } catch { return 100.0; } })
              .Min();
          return $"{minPct:F0}%";
      }

      private string GetEndpointSummary()
      {
          var eps = _checkResults.Where(r => r.Category == "Endpoints").ToList();
          var ok = eps.Count(r => r.Status == "Passed");
          return $"{ok}/{eps.Count}";
      }

      private string GetQueueSummary()
      {
          var queues = _checkResults.Where(r => r.Category == "TransportQueues").ToList();
          var total = queues
              .Sum(r => { try { var d = JsonSerializer.Deserialize<JsonElement>(r.DetailJson); return d.TryGetProperty("messageCount", out var v) ? v.GetInt32() : 0; } catch { return 0; } });
          return total.ToString();
      }
  }
  ```

- [ ] **Step 2: Create reusable detail component template**

  All 8 detail components share a common structure: a collapsible section with a header showing the category name + status badge, and a table of per-server rows. Create each component following this pattern. Below is the complete implementation for all 8:

  **ServiceHealthDetail.razor:**
  ```razor
  @using ExchangeTools.Monitor.Models
  @using System.Text.Json

  <details class="bg-surface border border-sidebar rounded-lg" open>
      <summary class="px-4 py-3 cursor-pointer font-medium flex items-center justify-between">
          <span>Service Health</span>
          <span class="@GetBadgeClass() px-2 py-0.5 rounded text-xs font-medium">
              @(Results.Count(r => r.Status == "Passed"))/@Results.Count passed
          </span>
      </summary>
      <div class="px-4 pb-4 overflow-x-auto">
          <table class="w-full text-sm">
              <thead><tr class="text-sidebar-muted border-b border-sidebar">
                  <th class="text-left py-2 pr-4">Server</th>
                  <th class="text-left py-2 pr-4">Role</th>
                  <th class="text-left py-2 pr-4">Running</th>
                  <th class="text-left py-2">Not Running</th>
              </tr></thead>
              <tbody>
              @foreach (var r in Results.OrderBy(r => r.Server).ThenBy(r => r.CheckName))
              {
                  var detail = ParseDetail(r.DetailJson);
                  <tr class="border-b border-sidebar last:border-0 @(r.Status == "Failed" ? "bg-red-950/20" : "")">
                      <td class="py-2 pr-4 text-sidebar-muted">@r.Server</td>
                      <td class="py-2 pr-4">@r.CheckName</td>
                      <td class="py-2 pr-4 text-green-400">@GetProp(detail, "runningCount")</td>
                      <td class="py-2 @(r.Status == "Failed" ? "text-red-400 font-medium" : "")">@GetProp(detail, "notRunningCount")</td>
                  </tr>
              }
              </tbody>
          </table>
      </div>
  </details>

  @code {
      [Parameter] public List<HealthCheckResult> Results { get; set; } = [];

      private string GetBadgeClass() => Results.Any(r => r.Status == "Failed")
          ? "bg-red-900 text-red-300"
          : Results.Any(r => r.Status == "Warning")
          ? "bg-amber-900 text-amber-300"
          : "bg-green-900 text-green-300";

      private JsonElement? ParseDetail(string json)
      { try { return JsonSerializer.Deserialize<JsonElement>(json); } catch { return null; } }

      private string GetProp(JsonElement? el, string key)
      {
          if (el is null) return "—";
          return el.Value.TryGetProperty(key, out var v) ? v.ToString() : "—";
      }
  }
  ```

  **DagReplicationDetail.razor:** Same structure. Columns: Server | Check | Result. Red row on Failed.

  **DatabaseCopiesDetail.razor:** Columns: Database | Server | Status | Copy Queue | Replay Queue | Content Index. Red row when Status != Healthy/Mounted. Yellow when ContentIndexState != Healthy.

  **CertificatesDetail.razor:** Columns: Server | Subject | Expiry | Days Left | Services. Red row when daysToExpiry < 14, amber when < 30.

  **TransportQueuesDetail.razor:** Columns: Server | Identity | Delivery Type | Messages | Status. Amber row when messageCount > 100.

  **ManagedAvailabilityDetail.razor:** Columns: Server | Health Set | Alert Value. Red on Unhealthy, amber on Degraded.

  **DiskSpaceDetail.razor:** Columns: Server | Drive | Free % | Free (GB) | Total (GB). Amber row when freePct < 15%.

  **EndpointsDetail.razor:** Columns: Name | URL | HTTP Status | Response Time. Red row when Status == Failed.

  Implement all 8 components fully, following the same pattern as ServiceHealthDetail. Each must:
  - Parse `DetailJson` to extract display values
  - Apply conditional row coloring based on status
  - Show a pass/fail badge in the `<summary>` header

- [ ] **Step 3: Build verification**

  ```powershell
  cd C:\claude\exchange-purge
  dotnet build ExchangeTools.sln
  ```

- [ ] **Step 4: Commit**

  ```bash
  cd /c/claude/exchange-purge
  git add src/ExchangeTools.Web/Components/
  git commit -m "$(cat <<'EOF'
  feat: add health dashboard page and 8 detail components

  HealthDashboardPage at /health with status banner, summary cards, action
  buttons, and collapsible per-category detail sections. All 8 detail
  components render per-server rows with conditional status coloring.

  Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
  EOF
  )"
  ```

---

### Task 7: ReportGenerator, ReportScheduler, and Health Reports Page

**Agent:** modular-builder
**Model:** sonnet
**max_turns:** 15

**Objective:** Implement `ReportGenerator` (self-contained HTML from snapshot data), `ReportScheduler` (cron-based IHostedService), and the `/health/reports` Blazor page.

**Files:**
- Create: `C:\claude\exchange-purge\src\ExchangeTools.Monitor\ReportGenerator.cs`
- Create: `C:\claude\exchange-purge\src\ExchangeTools.Monitor\ReportScheduler.cs`
- Create: `C:\claude\exchange-purge\src\ExchangeTools.Web\Components\Pages\HealthReportsPage.razor`

- [ ] **Step 1: Create ReportGenerator.cs**

  ```csharp
  using System.Text;
  using ExchangeTools.Monitor.Models;
  using Microsoft.Extensions.Logging;

  namespace ExchangeTools.Monitor;

  /// <summary>
  /// Renders a health snapshot and its check results into a self-contained HTML report
  /// with inline CSS. No external resource dependencies.
  /// </summary>
  public sealed class ReportGenerator
  {
      private readonly HealthRepository _repo;
      private readonly ILogger<ReportGenerator> _logger;
      private readonly string _reportsDir;

      public ReportGenerator(HealthRepository repo, ILogger<ReportGenerator> logger, string reportsDir = "reports")
      {
          _repo = repo;
          _logger = logger;
          _reportsDir = reportsDir;
          Directory.CreateDirectory(_reportsDir);
      }

      /// <summary>
      /// Generates an HTML report for the given snapshot. Saves to reports/ and inserts a health_reports row.
      /// Returns the relative filename on success.
      /// </summary>
      public async Task<string> GenerateAsync(long snapshotId)
      {
          var snapshot = (await _repo.GetSnapshotsAsync(1000)).FirstOrDefault(s => s.Id == snapshotId)
              ?? throw new InvalidOperationException($"Snapshot {snapshotId} not found");
          var results = await _repo.GetCheckResultsForSnapshotAsync(snapshotId);

          var filename = $"exchange-tools-health-{snapshot.Timestamp:yyyyMMdd-HHmm}.html";
          var fullPath = Path.Combine(_reportsDir, filename);

          var html = RenderHtml(snapshot, results);
          await File.WriteAllTextAsync(fullPath, html, Encoding.UTF8);

          var report = new HealthReport
          {
              Timestamp = DateTime.UtcNow,
              SnapshotId = snapshotId,
              Filename = filename,
              OverallStatus = snapshot.OverallStatus
          };
          await _repo.InsertReportAsync(report);

          _logger.LogInformation("Health report generated: {Filename}", filename);
          return filename;
      }

      private static string RenderHtml(HealthSnapshot snapshot, List<HealthCheckResult> results)
      {
          var statusColor = snapshot.OverallStatus switch
          {
              OverallStatus.Green  => "#16a34a",
              OverallStatus.Yellow => "#d97706",
              OverallStatus.Red    => "#dc2626",
              _                    => "#6b7280"
          };

          var sb = new StringBuilder();
          sb.AppendLine($$"""
              <!DOCTYPE html>
              <html lang="en">
              <head>
              <meta charset="UTF-8">
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
              <title>ExchangeTools Health Report — {{snapshot.Timestamp:yyyy-MM-dd HH:mm}} UTC</title>
              <style>
              body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                     background: #0d1117; color: #c9d1d9; margin: 0; padding: 24px; }
              h1 { color: {{statusColor}}; border-bottom: 2px solid {{statusColor}}; padding-bottom: 8px; }
              h2 { color: #8b949e; font-size: 1rem; text-transform: uppercase; letter-spacing: 0.05em;
                   margin-top: 32px; margin-bottom: 8px; }
              table { width: 100%; border-collapse: collapse; margin-bottom: 24px; font-size: 0.875rem; }
              th { text-align: left; padding: 8px 12px; background: #161b22; color: #8b949e;
                   border-bottom: 1px solid #30363d; }
              td { padding: 8px 12px; border-bottom: 1px solid #21262d; }
              tr:last-child td { border-bottom: none; }
              .pass { color: #3fb950; } .fail { color: #f85149; } .warn { color: #d29922; }
              .badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
              .badge-green { background: #0d4429; color: #3fb950; }
              .badge-red { background: #3d1a1a; color: #f85149; }
              .badge-yellow { background: #3d2c00; color: #d29922; }
              .meta { color: #8b949e; font-size: 0.875rem; margin-bottom: 24px; }
              </style>
              </head>
              <body>
              <h1>ExchangeTools Health Report</h1>
              <div class="meta">
                  <strong>Status:</strong> <span class="badge badge-{{GetBadgeClass(snapshot.OverallStatus)}}">{{snapshot.OverallStatus}}</span>
                  &nbsp; <strong>Collected:</strong> {{snapshot.Timestamp:yyyy-MM-dd HH:mm:ss}} UTC
                  &nbsp; <strong>Duration:</strong> {{snapshot.DurationMs?.ToString() ?? "—"}} ms
                  &nbsp; <strong>Generated:</strong> {{DateTime.UtcNow:yyyy-MM-dd HH:mm:ss}} UTC
              </div>
              """);

          // Summary table
          sb.AppendLine("""
              <h2>Summary</h2>
              <table>
              <tr><th>Category</th><th>Passed</th><th>Failed</th><th>Warnings</th></tr>
              """);
          var categories = results.GroupBy(r => r.Category);
          foreach (var cat in categories.OrderBy(c => c.Key))
          {
              var passed = cat.Count(r => r.Status == "Passed");
              var failed = cat.Count(r => r.Status == "Failed");
              var warned = cat.Count(r => r.Status == "Warning");
              sb.AppendLine($"""<tr><td>{cat.Key}</td><td class="pass">{passed}</td><td class="{(failed > 0 ? "fail" : "")}">{failed}</td><td class="{(warned > 0 ? "warn" : "")}">{warned}</td></tr>""");
          }
          sb.AppendLine("</table>");

          // Per-category detail tables
          foreach (var cat in categories.OrderBy(c => c.Key))
          {
              sb.AppendLine($"<h2>{cat.Key}</h2><table>");
              sb.AppendLine("<tr><th>Server</th><th>Check</th><th>Status</th><th>Detail</th></tr>");
              foreach (var r in cat.OrderBy(r => r.Server).ThenBy(r => r.CheckName))
              {
                  var cssClass = r.Status == "Failed" ? "fail" : r.Status == "Warning" ? "warn" : "pass";
                  var detail = r.DetailJson.Length > 200 ? r.DetailJson[..200] + "…" : r.DetailJson;
                  sb.AppendLine($"""<tr><td>{r.Server ?? "—"}</td><td>{r.CheckName}</td><td class="{cssClass}">{r.Status}</td><td style="font-family:monospace;font-size:0.75rem">{System.Web.HttpUtility.HtmlEncode(detail)}</td></tr>""");
              }
              sb.AppendLine("</table>");
          }

          sb.AppendLine("</body></html>");
          return sb.ToString();
      }

      private static string GetBadgeClass(OverallStatus s) => s switch
      {
          OverallStatus.Green  => "green",
          OverallStatus.Yellow => "yellow",
          OverallStatus.Red    => "red",
          _                    => "yellow"
      };
  }
  ```

- [ ] **Step 2: Create ReportScheduler.cs**

  The scheduler parses a cron expression to determine when to fire. Use a simple daily-at-HH:MM implementation (full cron parser is out of scope for this project; parse `0 H * * *` format).

  ```csharp
  using ExchangeTools.Monitor.Models;
  using Microsoft.Extensions.Hosting;
  using Microsoft.Extensions.Logging;

  namespace ExchangeTools.Monitor;

  /// <summary>
  /// Scheduled report generator. Runs ReportGenerator on a daily schedule
  /// configured by Monitor:ReportSchedule (cron format, default "0 8 * * *").
  /// Supports simple daily cron expressions only: "minute hour * * *".
  /// </summary>
  public sealed class ReportScheduler : IHostedService, IDisposable
  {
      private readonly ReportGenerator _generator;
      private readonly HealthRepository _repo;
      private readonly MonitorConfig _config;
      private readonly ILogger<ReportScheduler> _logger;
      private Timer? _timer;

      public ReportScheduler(
          ReportGenerator generator,
          HealthRepository repo,
          MonitorConfig config,
          ILogger<ReportScheduler> logger)
      {
          _generator = generator;
          _repo = repo;
          _config = config;
          _logger = logger;
      }

      public Task StartAsync(CancellationToken ct)
      {
          var delay = GetDelayUntilNextRun(_config.ReportSchedule);
          _logger.LogInformation("ReportScheduler: next run in {Delay}", delay);
          _timer = new Timer(OnTick, null, delay, TimeSpan.FromDays(1));
          return Task.CompletedTask;
      }

      private void OnTick(object? _)
      {
          _ = RunAsync();
      }

      private async Task RunAsync()
      {
          _logger.LogInformation("Scheduled report generation triggered");
          try
          {
              var snapshot = await _repo.GetLatestSnapshotAsync();
              if (snapshot is null)
              {
                  _logger.LogWarning("No snapshot available for scheduled report generation");
                  return;
              }
              var filename = await _generator.GenerateAsync(snapshot.Id);
              _logger.LogInformation("Scheduled report generated: {Filename}", filename);
          }
          catch (Exception ex)
          {
              _logger.LogError(ex, "Scheduled report generation failed");
          }
      }

      /// <summary>
      /// Parses "minute hour * * *" cron and returns delay until next occurrence.
      /// </summary>
      internal static TimeSpan GetDelayUntilNextRun(string cron)
      {
          try
          {
              var parts = cron.Split(' ');
              if (parts.Length >= 2 &&
                  int.TryParse(parts[0], out var minute) &&
                  int.TryParse(parts[1], out var hour))
              {
                  var now = DateTime.Now;
                  var next = new DateTime(now.Year, now.Month, now.Day, hour, minute, 0);
                  if (next <= now) next = next.AddDays(1);
                  return next - now;
              }
          }
          catch { /* fallback */ }

          // Default: run in 24 hours
          return TimeSpan.FromHours(24);
      }

      public Task StopAsync(CancellationToken ct)
      {
          _timer?.Change(Timeout.Infinite, 0);
          return Task.CompletedTask;
      }

      public void Dispose() => _timer?.Dispose();
  }
  ```

- [ ] **Step 3: Create HealthReportsPage.razor**

  ```razor
  @page "/health/reports"
  @attribute [Authorize(Policy = "Operator")]
  @inject HealthRepository HealthRepo
  @inject NavigationManager Nav
  @using ExchangeTools.Monitor
  @using ExchangeTools.Monitor.Models

  <PageTitle>Health Reports - ExchangeTools</PageTitle>

  <div class="max-w-4xl">
      <div class="flex items-center justify-between mb-6">
          <h1 class="text-xl font-semibold text-heading">Health Reports</h1>
          <a href="/health" class="text-sm text-primary-400 hover:underline">← Dashboard</a>
      </div>

      @if (_reports.Count == 0)
      {
          <p class="text-sidebar-muted">No reports generated yet. Use the Dashboard to generate a report.</p>
      }
      else
      {
          <table class="w-full text-sm">
              <thead>
                  <tr class="text-sidebar-muted border-b border-sidebar">
                      <th class="text-left py-2 pr-6">Timestamp (UTC)</th>
                      <th class="text-left py-2 pr-6">Status</th>
                      <th class="text-left py-2">Download</th>
                  </tr>
              </thead>
              <tbody>
              @foreach (var report in _reports)
              {
                  <tr class="border-b border-sidebar last:border-0 hover:bg-sidebar-hover">
                      <td class="py-3 pr-6 text-body">@report.Timestamp.ToString("yyyy-MM-dd HH:mm") UTC</td>
                      <td class="py-3 pr-6">
                          <span class="@GetBadgeClass(report.OverallStatus) px-2 py-0.5 rounded text-xs font-medium">
                              @report.OverallStatus
                          </span>
                      </td>
                      <td class="py-3">
                          <a href="/api/health/reports/@report.Id/download"
                             class="text-primary-400 hover:underline text-sm"
                             download="@report.Filename">
                              @report.Filename
                          </a>
                      </td>
                  </tr>
              }
              </tbody>
          </table>
      }
  </div>

  @code {
      private List<HealthReport> _reports = [];

      protected override async Task OnInitializedAsync()
      {
          _reports = await HealthRepo.GetReportsAsync();
      }

      private static string GetBadgeClass(OverallStatus s) => s switch
      {
          OverallStatus.Green  => "bg-green-900 text-green-300",
          OverallStatus.Yellow => "bg-amber-900 text-amber-300",
          OverallStatus.Red    => "bg-red-900 text-red-300",
          _                    => "bg-gray-800 text-gray-300"
      };
  }
  ```

- [ ] **Step 4: Build verification**

  ```powershell
  cd C:\claude\exchange-purge
  dotnet build ExchangeTools.sln
  ```

- [ ] **Step 5: Commit**

  ```bash
  cd /c/claude/exchange-purge
  git add src/ExchangeTools.Monitor/ReportGenerator.cs src/ExchangeTools.Monitor/ReportScheduler.cs src/ExchangeTools.Web/Components/Pages/HealthReportsPage.razor
  git commit -m "$(cat <<'EOF'
  feat: add ReportGenerator, ReportScheduler, and HealthReportsPage

  Self-contained HTML report generation with inline CSS. Daily scheduled
  report via cron-based ReportScheduler. Reports list page at /health/reports
  with download links served via /api/health/reports/{id}/download.

  Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
  EOF
  )"
  ```

---

### Task 8: Wire Everything Together — Program.cs, Nav, Config, Download Endpoint

**Agent:** modular-builder
**Model:** sonnet
**max_turns:** 12

**Objective:** Register all Monitor services in `Program.cs`, add Health nav links to `MainLayout.razor`, add the `Monitor` config section to `appsettings.json`, add a `/api/health/reports/{id}/download` endpoint, and initialize `HealthRepository` on startup.

**Files:**
- Modify: `C:\claude\exchange-purge\src\ExchangeTools.Web\Program.cs`
- Modify: `C:\claude\exchange-purge\src\ExchangeTools.Web\Components\Layout\MainLayout.razor`
- Modify: `C:\claude\exchange-purge\src\ExchangeTools.Web\appsettings.json`
- Create: `C:\claude\exchange-purge\src\ExchangeTools.Web\Endpoints\HealthReportDownloadEndpoint.cs`

- [ ] **Step 1: Add Monitor config section to appsettings.json**

  Add after the existing `"Logging"` section:

  ```json
  "Monitor": {
    "CollectionIntervalMinutes": 15,
    "ReportSchedule": "0 8 * * *",
    "Servers": ["EXCHANGELAB", "EXCHANGELAB2"],
    "Endpoints": [
      { "Name": "OWA", "Url": "https://lab.ergonet.pl/owa" },
      { "Name": "ECP", "Url": "https://lab.ergonet.pl/ecp" },
      { "Name": "Autodiscover", "Url": "https://autodiscover.lab.ergonet.pl/autodiscover/autodiscover.xml" }
    ],
    "AlertThresholds": {
      "CertExpiryRedDays": 14,
      "CertExpiryYellowDays": 30,
      "DiskFreeYellowPercent": 15
    }
  }
  ```

- [ ] **Step 2: Register Monitor services in Program.cs**

  After the `builder.Services.AddSingleton<IExchangeConnection>` line, add:

  ```csharp
  // Monitor services
  var monitorConfig = builder.Configuration.GetSection("Monitor").Get<ExchangeTools.Monitor.Models.MonitorConfig>()
      ?? new ExchangeTools.Monitor.Models.MonitorConfig();
  builder.Services.AddSingleton(monitorConfig);
  builder.Services.AddSingleton(_ => new ExchangeTools.Monitor.HealthRepository(connString));
  builder.Services.AddSingleton<ExchangeTools.Monitor.ReportGenerator>(sp =>
      new ExchangeTools.Monitor.ReportGenerator(
          sp.GetRequiredService<ExchangeTools.Monitor.HealthRepository>(),
          sp.GetRequiredService<ILogger<ExchangeTools.Monitor.ReportGenerator>>(),
          "reports"));
  builder.Services.AddSingleton<ExchangeTools.Monitor.HealthCollector>();
  builder.Services.AddHostedService(sp => sp.GetRequiredService<ExchangeTools.Monitor.HealthCollector>());
  builder.Services.AddSingleton<ExchangeTools.Monitor.ReportScheduler>();
  builder.Services.AddHostedService(sp => sp.GetRequiredService<ExchangeTools.Monitor.ReportScheduler>());
  ```

  Also add HealthRepository initialization in the startup block, after `await templateService.SeedBuiltInAsync()`:

  ```csharp
  var healthRepo = app.Services.GetRequiredService<ExchangeTools.Monitor.HealthRepository>();
  await healthRepo.InitializeAsync();
  ```

- [ ] **Step 3: Create HealthReportDownloadEndpoint.cs**

  ```csharp
  using ExchangeTools.Monitor;
  using Microsoft.AspNetCore.Mvc;

  namespace ExchangeTools.Web.Endpoints;

  public static class HealthReportDownloadEndpoint
  {
      public static void Map(WebApplication app)
      {
          app.MapGet("/api/health/reports/{id:long}/download", async (
              long id,
              HealthRepository repo,
              ILogger<HealthReportDownloadEndpoint> logger) =>
          {
              var report = await repo.GetReportByIdAsync(id);
              if (report is null)
                  return Results.NotFound();

              var fullPath = Path.Combine("reports", report.Filename);
              if (!File.Exists(fullPath))
              {
                  logger.LogWarning("Report file not found on disk: {Path}", fullPath);
                  return Results.NotFound();
              }

              var bytes = await File.ReadAllBytesAsync(fullPath);
              return Results.File(bytes, "text/html", report.Filename);
          }).RequireAuthorization("Operator");
      }
  }
  ```

  Register this endpoint in `Program.cs` after the existing `HealthEndpoint.Map(app)` call:

  ```csharp
  ExchangeTools.Web.Endpoints.HealthReportDownloadEndpoint.Map(app);
  ```

- [ ] **Step 4: Update MainLayout.razor — add Health nav section**

  After the "Tools" section divider (line 25 in the current file), add:

  ```razor
  <div class="hidden px-3 pt-3 mt-2 border-t border-sidebar text-xs font-medium text-sidebar-muted uppercase tracking-wider mb-1 md:block">Health</div>
  <NavLink href="health" class="block px-3 py-2 text-sidebar-muted no-underline rounded-md transition-colors duration-fast hover:bg-sidebar-hover hover:text-heading">Dashboard</NavLink>
  <NavLink href="health/reports" class="block px-3 py-2 text-sidebar-muted no-underline rounded-md transition-colors duration-fast hover:bg-sidebar-hover hover:text-heading">Reports</NavLink>
  ```

  Insert this AFTER the `<NavLink href="storage-analysis" ...>` line and BEFORE the closing `</nav>` tag.

- [ ] **Step 5: Wire "Generate Report" button in HealthDashboardPage.razor**

  Update the `GenerateReport` method in `HealthDashboardPage.razor` to call `ReportGenerator` and trigger a browser download:

  ```csharp
  @inject ReportGenerator ReportGen
  @inject NavigationManager Nav

  // In @code block, update GenerateReport:
  private async Task GenerateReport()
  {
      if (_snapshot is null) return;
      var filename = await ReportGen.GenerateAsync(_snapshot.Id);
      Nav.NavigateTo($"/api/health/reports?latest=true", forceLoad: true);
      // Navigate to the reports page after generation
      Nav.NavigateTo("/health/reports");
  }
  ```

  Actually: the cleanest approach is to navigate to the download URL after generating. Get the latest report ID and redirect:

  ```csharp
  private async Task GenerateReport()
  {
      if (_snapshot is null) return;
      try {
          var filename = await ReportGen.GenerateAsync(_snapshot.Id);
          // Refresh reports list then navigate to download
          var reports = await HealthRepo.GetReportsAsync(1);
          if (reports.Count > 0)
              Nav.NavigateTo($"/api/health/reports/{reports[0].Id}/download", forceLoad: true);
      } catch (Exception ex) {
          Logger.LogError(ex, "On-demand report generation failed");
      }
  }
  ```

- [ ] **Step 6: Build verification**

  ```powershell
  cd C:\claude\exchange-purge
  dotnet build ExchangeTools.sln
  ```
  Must succeed with zero errors.

- [ ] **Step 7: Commit**

  ```bash
  cd /c/claude/exchange-purge
  git add src/ExchangeTools.Web/
  git commit -m "$(cat <<'EOF'
  feat: wire Monitor services into Program.cs, nav, config, and download endpoint

  Register HealthCollector, ReportGenerator, ReportScheduler in DI. Initialize
  HealthRepository on startup. Add Health nav section to sidebar. Add Monitor
  config block to appsettings.json. Add /api/health/reports/{id}/download endpoint.

  Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
  EOF
  )"
  ```

---

### Task 9: Build Verification and Test Run

**Agent:** modular-builder
**Model:** haiku
**max_turns:** 10

**Objective:** Verify the full solution builds cleanly, all existing unit tests pass, and acceptance criteria 1–7 (rename) are validated.

**Files:**
- Read: `C:\claude\exchange-purge\ExchangeTools.sln`

- [ ] **Step 1: Full solution build**

  ```powershell
  cd C:\claude\exchange-purge
  dotnet build ExchangeTools.sln --configuration Release
  ```
  Must succeed with zero errors. If errors appear, read and fix them before proceeding.

- [ ] **Step 2: Run unit tests (exclude E2E)**

  ```powershell
  cd C:\claude\exchange-purge
  dotnet test ExchangeTools.sln --filter "FullyQualifiedName!~E2E" --configuration Release --logger "console;verbosity=normal"
  ```
  All tests must pass. Fix any failures before proceeding.

- [ ] **Step 3: Validate acceptance criteria 1–7**

  Run each check and record the result:

  ```powershell
  # AC1: Build succeeds (verified in Step 1)

  # AC2: No ExchangePurge identifiers in src/ or tests/
  $hits = Get-ChildItem C:\claude\exchange-purge\src,C:\claude\exchange-purge\tests -Recurse -Include '*.cs','*.razor','*.csproj','*.json' |
      Where-Object { $_.FullName -notmatch '\\obj\\' -and $_.FullName -notmatch '\\bin\\' } |
      Select-String 'ExchangePurge'
  if ($hits) { Write-Error "AC2 FAIL: ExchangePurge still referenced in $($hits.Count) locations" }
  else { Write-Host "AC2 PASS: No ExchangePurge identifiers remain" }

  # AC3: CLI binary name
  $cliCsproj = Get-Content 'C:\claude\exchange-purge\src\ExchangeTools.Cli\ExchangeTools.Cli.csproj' -Raw
  if ($cliCsproj -match 'exchange-tools') { Write-Host "AC3 PASS: CLI AssemblyName = exchange-tools" }
  else { Write-Error "AC3 FAIL: CLI AssemblyName not updated" }

  # AC4: appsettings.json contains exchange-tools.db and exchangetools-.log
  $settings = Get-Content 'C:\claude\exchange-purge\src\ExchangeTools.Web\appsettings.json' -Raw
  if ($settings -match 'exchange-tools\.db' -and $settings -match 'exchangetools-\.log') { Write-Host "AC4 PASS" }
  else { Write-Error "AC4 FAIL: appsettings.json still has old db/log paths" }

  # AC5: Exchange-Tools-Operators group name
  if ($settings -match 'Exchange-Tools-Operators') { Write-Host "AC5 PASS" }
  else { Write-Error "AC5 FAIL: appsettings.json still has Exchange-Purge-Operators" }

  # AC6: Git remote URL (manual check — Task 3 handles this)
  git -C C:\claude\exchange-purge remote -v

  # AC7: All unit tests pass (verified in Step 2)
  ```

- [ ] **Step 4: Commit verification report**

  ```bash
  cd /c/claude/exchange-purge
  git add -A
  git status
  # Only commit if there are any fixup changes from the verification steps
  ```

---

### Task 10: Spec Compliance Review

**Agent:** test-coverage
**Model:** sonnet
**max_turns:** 12

**Objective:** Verify all spec requirements are implemented. Check rename completeness, all 10 health checks are present, all new pages exist, all 3 DB tables initialized, and all acceptance criteria are addressable.

**READ-ONLY MODE: You are a research agent. Use ONLY Read, Glob, Grep, LS, and search tools. Do NOT use Edit, Write, Bash, or any tool that modifies files or executes commands.**

**Files to examine:**
- `C:\claude\exchange-purge\src\ExchangeTools.Monitor\HealthCollector.cs`
- `C:\claude\exchange-purge\src\ExchangeTools.Monitor\HealthRepository.cs`
- `C:\claude\exchange-purge\src\ExchangeTools.Monitor\ReportGenerator.cs`
- `C:\claude\exchange-purge\src\ExchangeTools.Monitor\ReportScheduler.cs`
- `C:\claude\exchange-purge\src\ExchangeTools.Web\Components\Pages\HealthDashboardPage.razor`
- `C:\claude\exchange-purge\src\ExchangeTools.Web\Components\Pages\HealthReportsPage.razor`
- `C:\claude\exchange-purge\src\ExchangeTools.Web\Program.cs`
- `C:\claude\exchange-purge\src\ExchangeTools.Web\appsettings.json`

- [ ] **Step 1: Verify rename completeness**
  Grep `ExchangePurge` in `src/` and `tests/`. Report any remaining occurrences.

- [ ] **Step 2: Verify all 10 check categories present in HealthCollector.cs**
  Confirm: ServiceHealth, ServerComponents, DAGReplication, DatabaseCopies, Certificates, TransportQueues, ManagedAvailability, BigFunnelIndex, DiskSpace, Endpoints.

- [ ] **Step 3: Verify SQLite schema — all 3 tables**
  Read `HealthRepository.cs` and confirm `health_snapshots`, `health_check_results`, `health_reports` tables are created in `InitializeAsync()`.

- [ ] **Step 4: Verify all 8 detail components exist**
  Glob `src/ExchangeTools.Web/Components/Health/*.razor`. Must find 8 files.

- [ ] **Step 5: Verify service registration in Program.cs**
  Read `Program.cs` — confirm `HealthCollector`, `ReportScheduler`, `HealthRepository`, `ReportGenerator` are registered. Confirm `HealthRepository.InitializeAsync()` is called.

- [ ] **Step 6: Verify Monitor config section in appsettings.json**
  Read `appsettings.json` — confirm `Monitor` section with `CollectionIntervalMinutes`, `ReportSchedule`, `Servers`, `Endpoints`, `AlertThresholds` keys.

- [ ] **Step 7: Verify acceptance criteria mapping**
  For each of the 26 acceptance criteria in the spec, note which file/method satisfies it or flag if missing.

- [ ] **Step 8: Report**
  Output a structured pass/fail list. Flag any gaps for the code-quality review agent.

---

### Task 11: Code Quality Review

**Agent:** zen-architect
**Model:** sonnet
**max_turns:** 12

**Objective:** Architecture review of the Monitor project — evaluate component boundaries, data access patterns, background service lifecycle, and Blazor page design. Produce a list of actionable issues (if any) ordered by severity.

**READ-ONLY MODE: You are a research agent. Use ONLY Read, Glob, Grep, LS, and search tools. Do NOT use Edit, Write, Bash, or any tool that modifies files or executes commands.**

**Focus areas:**
1. `HealthCollector` — is the scheduled task cleanup robust? Are temp files cleaned up on exception? Does the service handle cancellation correctly?
2. `ReportGenerator` — is `System.Web.HttpUtility` available in .NET 10? (Check if `System.Web` is referenced; if not, use `System.Net.WebUtility.HtmlEncode` instead.)
3. `HealthRepository` — does each method open a new connection? Is this consistent with the rest of the codebase? Are all parameters safe from SQL injection?
4. `HealthDashboardPage` — is the `IDisposable` pattern correct? Does the `Timer` get disposed? Is the event unsubscription safe?
5. `ReportScheduler` — does `GetDelayUntilNextRun` correctly handle timezones (server local vs UTC)?

**Output:** Structured list of findings with severity (Critical / Major / Minor) and the specific fix required for each Critical/Major issue.

---

### Task 12: Fix Issues from Reviews

**Agent:** modular-builder
**Model:** sonnet
**max_turns:** 12

**Objective:** Apply all Critical and Major fixes identified by Task 10 (spec compliance) and Task 11 (code quality) reviewers.

**Files:** Determined by review output.

- [ ] **Step 1: Apply Critical fixes**
  Address all Critical items from Task 11 first (likely: `System.Web.HttpUtility` → `System.Net.WebUtility`, temp file cleanup in finally block, etc.)

- [ ] **Step 2: Apply Major fixes**
  Address all Major items from Task 11.

- [ ] **Step 3: Address spec gaps from Task 10**
  If any of the 10 check categories are missing or miscategorized, add/fix them.

- [ ] **Step 4: Build verification**

  ```powershell
  cd C:\claude\exchange-purge
  dotnet build ExchangeTools.sln --configuration Release
  dotnet test ExchangeTools.sln --filter "FullyQualifiedName!~E2E" --configuration Release
  ```

- [ ] **Step 5: Final commit**

  ```bash
  cd /c/claude/exchange-purge
  git add -A
  git commit -m "$(cat <<'EOF'
  fix: apply code quality and spec compliance review findings

  Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
  EOF
  )"
  ```
