# Amplifier Cowork — Task Handoff

## Dispatch Status: IN_PROGRESS

> **Protocol:** Only the designated receiver should act.
> - Claude acts on: `IDLE`, `PR_READY`, `REVIEWING`, `DEPLOYING`
> - Gemini acts on: `WAITING_FOR_GEMINI`

## State Transitions

```
IDLE ──(Claude writes task)──→ WAITING_FOR_GEMINI
WAITING_FOR_GEMINI ──(Gemini starts)──→ IN_PROGRESS
IN_PROGRESS ──(Gemini pushes PR)──→ PR_READY
PR_READY ──(Claude reviews)──→ REVIEWING
REVIEWING ──(Claude merges/deploys)──→ DEPLOYING
DEPLOYING ──(Claude tests pass)──→ IDLE
```

---

## Current Task

**From:** Claude → Gemini
**Branch:** feature/dns-settings
**Priority:** normal
**Repository:** C:\claude\fusecp-enterprise
**Working Directory:** C:\claude\fusecp-enterprise
**PR Target:** master on psklarkins/fusecp-enterprise

### Objective
Add DNS server configuration to the Servers settings page and create a new DNS Settings page with nameserver config and configurable default DNS record templates.

### Spec
`docs/specs/2026-02-17-dns-settings-design.md` — read the full spec before starting.

### Detailed Requirements

**Part A: Add DNS fields to Server model chain (follow existing AD/HyperV/Exchange pattern exactly)**

1. **`src/FuseCP.Database/Models/Server.cs`** — Add 4 fields after line 36 (after Exchange section):
   ```csharp
   // DNS Configuration
   public bool DnsEnabled { get; set; }
   public string? DnsServer { get; set; }
   public string? DnsUsername { get; set; }
   public string? DnsPassword { get; set; }
   ```

2. **`src/FuseCP.EnterpriseServer/Models/ServerRequests.cs`** — Add DNS fields to:
   - `CreateServerRequest` (after line 122): DnsEnabled, DnsServer, DnsUsername, DnsPassword (with XML doc comments matching Exchange pattern)
   - `UpdateServerRequest` (after line 244): same 4 fields
   - `ServerResponse` (after line 351): DnsEnabled, DnsServer, DnsUsername (NO password). Update `FromServer()` mapper at line 358-379 to include the 3 DNS fields.

3. **`src/FuseCP.Portal/Services/Models/ApiModels.cs`** — Add DNS fields to Portal-side CreateServerRequest and UpdateServerRequest (same pattern as the ones you just modified in ServerRequests.cs). Also add DNS fields to any ServerResponse in this file.

4. **`src/FuseCP.Portal/Components/Pages/Settings/ServerEdit.razor`**:
   - Add new `<Card>` block after Exchange card (line 249) and before save buttons (line 251). Copy the Exchange card pattern (lines 201-249) and change:
     - Title: "DNS Configuration"
     - Toggle: `_model.DnsEnabled`
     - Fields: DnsServer (placeholder "e.g., 172.31.251.101"), DnsUsername, DnsPassword
   - Add DNS fields to `ServerEditModel` class (line 405-423)
   - Add DNS mapping in `LoadServerAsync()` at line 296-310
   - Add DNS fields to Create request builder at line 329-346
   - Add DNS password handling in Update path at line 357-371, and DNS fields in UpdateServerRequest at line 373-390

5. **`src/FuseCP.Portal/Components/Pages/Settings/Servers.razor`**:
   - Add DNS badge at line 138 (before the `@if (!server.ADEnabled && ...)` fallback):
     ```razor
     @if (server.DnsEnabled)
     {
         <Badge Variant="BadgeVariant.Primary" Size="BadgeSize.Small">DNS</Badge>
     }
     ```
   - Update the no-services check at line 139 to include: `&& !server.DnsEnabled`
   - Update `GetConnectionHost()` at line 390-403 to include DNS fallback before the ServerName fallback:
     ```csharp
     if (server.DnsEnabled && !string.IsNullOrEmpty(server.DnsServer))
         return server.DnsServer;
     ```

**Part B: DNS Settings page with nameserver config and record templates**

6. **Create `src/FuseCP.Database/Models/DnsSetting.cs`**:
   ```csharp
   namespace FuseCP.Database.Models;

   public sealed class DnsSetting
   {
       public int Id { get; init; }
       public string? PrimaryNameserver { get; set; }
       public string? SecondaryNameserver { get; set; }
       public int DefaultTtl { get; set; } = 3600;
   }
   ```

7. **Create `src/FuseCP.Database/Models/DnsRecordTemplate.cs`**:
   ```csharp
   namespace FuseCP.Database.Models;

   public sealed class DnsRecordTemplate
   {
       public int Id { get; init; }
       public required string Name { get; set; }
       public required string RecordType { get; set; }
       public required string Value { get; set; }
       public int? Priority { get; set; }
       public int? Ttl { get; set; }
   }
   ```

8. **Create `src/FuseCP.Database/Repositories/DnsSettingsRepository.cs`** — Follow existing repository patterns (Dapper, connection string from config). Methods:
   - `GetSettingsAsync()` — returns DnsSetting (INSERT default if not exists)
   - `SaveSettingsAsync(DnsSetting)` — UPDATE the single row
   - `GetTemplatesAsync()` — returns List<DnsRecordTemplate>
   - `GetTemplateAsync(int id)` — single template
   - `CreateTemplateAsync(DnsRecordTemplate)` — INSERT, return new ID
   - `UpdateTemplateAsync(DnsRecordTemplate)` — UPDATE
   - `DeleteTemplateAsync(int id)` — DELETE

9. **Create `src/FuseCP.EnterpriseServer/Endpoints/DnsSettingsEndpoints.cs`** — Follow `DnsEndpoints.cs` pattern exactly. Routes:
   ```
   GET    /api/dns/settings                    GetSettings
   PUT    /api/dns/settings                    UpdateSettings
   GET    /api/dns/settings/templates          GetTemplates
   POST   /api/dns/settings/templates          CreateTemplate
   PUT    /api/dns/settings/templates/{id}     UpdateTemplate
   DELETE /api/dns/settings/templates/{id}     DeleteTemplate
   ```
   All require `PlatformAdmin` authorization. Define request DTOs in same file.

10. **Register endpoints in `src/FuseCP.EnterpriseServer/Program.cs`** — Add `app.MapDnsSettingsEndpoints();` near the existing `app.MapDnsEndpoints();` call. Register `DnsSettingsRepository` in DI.

11. **Create Portal API client** — Either add methods to existing `IServerApiClient`/`ServerApiClient` or create new `IDnsSettingsApiClient`/`DnsSettingsApiClient`. Methods for all 6 endpoints.

12. **Create `src/FuseCP.Portal/Components/Pages/Settings/DnsSettings.razor`**:
    - Route: `/settings/dns`
    - Authorization: `[Authorize(Roles = "Administrator")]`
    - Inherits: `FeedbackPageBase`
    - Two sections:
      - **Nameserver Configuration card**: Primary NS, Secondary NS, Default TTL fields with Save button
      - **Record Templates card**: DataTable or manual table showing templates. Add/Edit/Delete. Record Type dropdown: A, AAAA, CNAME, MX, TXT, SRV, NS, CAA. Priority field visible only when RecordType is MX or SRV.
    - Follow existing page patterns (LoadingSpinner, error handling, ToastService)

13. **Create DB migration SQL script** at `scripts/migrations/dns-settings.sql`:
    ```sql
    ALTER TABLE Servers ADD
        DnsEnabled BIT NOT NULL DEFAULT 0,
        DnsServer NVARCHAR(255) NULL,
        DnsUsername NVARCHAR(255) NULL,
        DnsPassword NVARCHAR(255) NULL;

    CREATE TABLE DnsSettings (
        Id INT NOT NULL PRIMARY KEY DEFAULT 1,
        PrimaryNameserver NVARCHAR(255) NULL,
        SecondaryNameserver NVARCHAR(255) NULL,
        DefaultTtl INT NOT NULL DEFAULT 3600,
        CONSTRAINT CK_DnsSettings_SingleRow CHECK (Id = 1)
    );

    INSERT INTO DnsSettings (Id, DefaultTtl) VALUES (1, 3600);

    CREATE TABLE DnsRecordTemplates (
        Id INT IDENTITY(1,1) PRIMARY KEY,
        Name NVARCHAR(255) NOT NULL,
        RecordType NVARCHAR(10) NOT NULL,
        Value NVARCHAR(1000) NOT NULL,
        Priority INT NULL,
        Ttl INT NULL
    );
    ```

### Context Loading (use your full 1M context)
Load these files completely before starting:
- `docs/specs/2026-02-17-dns-settings-design.md` — full design spec
- `src/FuseCP.Database/Models/Server.cs` — current Server model (37 lines)
- `src/FuseCP.EnterpriseServer/Models/ServerRequests.cs` — request/response DTOs (397 lines)
- `src/FuseCP.Portal/Services/Models/ApiModels.cs` — Portal-side DTOs
- `src/FuseCP.Portal/Components/Pages/Settings/ServerEdit.razor` — server edit form (425 lines)
- `src/FuseCP.Portal/Components/Pages/Settings/Servers.razor` — server list (405 lines)
- `src/FuseCP.EnterpriseServer/Endpoints/DnsEndpoints.cs` — endpoint pattern to follow (234 lines)
- `src/FuseCP.Database/Repositories/SolidCP/DnsRepository.cs` — repository pattern to follow
- `src/FuseCP.EnterpriseServer/Program.cs` — DI registration and endpoint mapping
- `src/FuseCP.Portal/Services/IServerApiClient.cs` — API client interface
- `src/FuseCP.Portal/Services/ServerApiClient.cs` — API client implementation
- COWORK.md — refresh protocol understanding
- This task section of HANDOFF.md

### Files YOU May Modify
- `src/FuseCP.Database/Models/Server.cs`
- `src/FuseCP.Database/Models/` (create new files)
- `src/FuseCP.Database/Repositories/` (create new files)
- `src/FuseCP.EnterpriseServer/Models/ServerRequests.cs`
- `src/FuseCP.EnterpriseServer/Endpoints/` (create new files)
- `src/FuseCP.EnterpriseServer/Program.cs`
- `src/FuseCP.Portal/Services/Models/ApiModels.cs`
- `src/FuseCP.Portal/Services/IServerApiClient.cs` (or create new client)
- `src/FuseCP.Portal/Services/ServerApiClient.cs` (or create new client)
- `src/FuseCP.Portal/Components/Pages/Settings/ServerEdit.razor`
- `src/FuseCP.Portal/Components/Pages/Settings/Servers.razor`
- `src/FuseCP.Portal/Components/Pages/Settings/` (create DnsSettings.razor)
- `scripts/migrations/` (create SQL script)

### Files You Must NOT Modify
- .claude/* (always)
- CLAUDE.md (always)
- C:\FuseCP\* (always)
- C:\Przemek\OPENCODE.md (always)
- `src/FuseCP.Providers.DNS/` (Claude handles provider changes post-merge)
- `src/FuseCP.EnterpriseServer/Services/FuseCPServer/FuseCPDnsProvider.cs` (Claude removes post-merge)
- `src/FuseCP.EnterpriseServer/Services/OrganizationProvisioningService.cs` (Claude handles post-merge)
- `src/FuseCP.EnterpriseServer/appsettings.json` (Claude handles post-merge)

### Acceptance Criteria
- [ ] DNS fields added to Server.cs, CreateServerRequest, UpdateServerRequest, ServerResponse (both API and Portal sides)
- [ ] ServerEdit.razor has DNS Configuration card matching Exchange card pattern
- [ ] Servers.razor shows DNS badge when DnsEnabled=true
- [ ] DnsSetting and DnsRecordTemplate models created
- [ ] DnsSettingsRepository with full CRUD operations
- [ ] DnsSettingsEndpoints registered and working (6 endpoints)
- [ ] DnsSettings.razor page with nameserver config + template table
- [ ] Record type dropdown has all 8 types (A, AAAA, CNAME, MX, TXT, SRV, NS, CAA)
- [ ] Priority field only visible for MX and SRV record types
- [ ] DB migration SQL script created
- [ ] All code committed to feature branch with clear messages
- [ ] Build passes with 0 errors

### Build & Verify (MUST complete before creating PR)

Run these commands and confirm they pass. Do NOT create a PR until all pass:

```bash
cd /c/claude/fusecp-enterprise/src/FuseCP.Portal && dotnet build --configuration Release
cd /c/claude/fusecp-enterprise/src/FuseCP.EnterpriseServer && dotnet build --configuration Release
```

Expected: Build succeeded, 0 errors for both projects.

If build fails, fix the errors before proceeding. Include build output summary in PR description.

### Agent Tier Unlocks
primary + knowledge only

---

## History

| Date | Direction | Task | PR | Result |
|------|-----------|------|-----|--------|
| 2026-02-16 | Gemini → Claude | Initial cowork setup | — | Agents synced, protocol established |
| 2026-02-17 | Claude → Gemini | Browser integration tests (API-UI parity) | PR#221 (closed, wrong repo) | Gemini created tests in fusecp-enterprise. Claude fixed runner (timeouts, verdict logic), ran suite. Initial: 4 PASS (36%). |
| 2026-02-17 | Claude | Fix all integration issues | — | Fixed HyperV connection string bug (500→200), AuditLog error handling, rewrote test suite to be Blazor-aware. Final: 11/11 PASS (100%). Report: `fusecp-enterprise/docs/reports/integration-report.md` |
| 2026-02-17 | Claude → Gemini | LoadingSpinner + shared Pagination for log pages | PR#74 | Success. Gemini: correct implementation, build passed, right repo. Claude: fixed 4 review issues (loading UX consistency, error handling, null-coalescing, missing @using). First successful improved handoff. |
