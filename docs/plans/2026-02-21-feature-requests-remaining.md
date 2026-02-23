# FuseCP Feature Requests — Remaining Tasks (5-12 Restated as 1-8)

> **Status: ALL 8 TASKS COMPLETE** — Implemented via /subagent-dev, merged as PR #109 (2026-02-21). Post-merge fixes: PR #110 (photo gating), migration 096 (Polish diacritics + missing i18n key). All deployed to production.

**Goal:** Implement the remaining 8 tasks from the FuseCP feature requests plan. Tasks 1-4 from the original plan (Phase 4 OperationsLogging fix + Phase 1 Mailbox General Tab redesign) are already DONE as of 2026-02-21. This document covers: Phase 3 (Mail Flow Tab accordion + searchable forwarding picker) and Phase 2 (Organization contact fields in DB/API/UI + AD thumbnailPhoto read/write + mailbox avatar).

**Architecture:**
- Blazor Server (.NET 8) portal with Minimal API backend in `Program.cs` (inline, not separate endpoint files)
- AD/Exchange providers via WinRM
- All DB changes ADDITIVE only — writing to `Packages` table (the SolidCP organization table, NOT a custom `Organizations` table)
- MailboxGeneralTab accordion style: Bootstrap-style with `data-bs-toggle="collapse"`, `accordion-item`, `accordion-header`, `accordion-button`, `accordion-collapse collapse show`, `accordion-body` — this is already implemented and must be matched in MailboxMailFlowTab

**Key confirmed facts:**
- `_orgMailboxes` type: `List<FuseCP.Database.Models.SolidCP.ExchangeAccount>` (fields: `AccountID`, `DisplayName`, `AccountName`, `PrimaryEmailAddress`)
- `LoadOrgMailboxes()` is only called inside `ShowAddModal()` — NOT during `OnInitializedAsync` — must be changed for forwarding picker
- Organization API endpoints live in `Program.cs` inline under `orgGroup` (not a separate Endpoints file)
- `IOrganizationApiClient` in Portal does NOT yet have GetContactAsync/UpdateContactAsync
- DB table for org contact fields: `Packages` (SolidCP schema), accessed via `PackageRepository`
- Migration sequence: next number after `092_AddMailboxGeneralTabTranslations.sql` is **093**
- `IAdApiClient` does NOT have GetUserPhotoAsync/SetUserPhotoAsync — full implementation needed

**Tech Stack:** C# .NET 8, Blazor Server, Minimal APIs (inline in Program.cs), SQL Server, WinRM (Exchange/AD providers), Dapper ORM

---

## Design System Reference

**MailboxGeneralTab accordion (already implemented — MATCH THIS EXACTLY):**
- Bootstrap-style: `<div class="accordion">`, `<div class="accordion-item">`, `<h2 class="accordion-header">`, `<button class="accordion-button" data-bs-toggle="collapse" data-bs-target="#collapseXxx">`, `<div class="accordion-collapse collapse show">`, `<div class="accordion-body">`
- All sections use `show` class to start expanded
- Source: `src/FuseCP.Portal/Components/Pages/Exchange/Tabs/MailboxGeneralTab.razor`
- Design playground reference: `C:/claude/fusecp-enterprise/tmp/mailbox-general-tab-playground.html`

---

## Task 1: Mail Flow Tab — Replace Forwarding TextInput with Searchable Picker (FR #33)

**Agent:** component-designer
**Estimated turns:** 15

**Files:**
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.Portal\Components\Pages\Exchange\Tabs\MailboxMailFlowTab.razor`
- Reference (read-only): `C:\claude\fusecp-enterprise\tmp\mailbox-general-tab-playground.html`

**Context:**
Current forwarding flow (lines 41-57 of MailboxMailFlowTab.razor): when `_enableForwarding` is true, shows a `<TextInput>` bound to `_forwardingAddress` string. This must become a searchable org mailbox picker.

The `_orgMailboxes` list (`List<ExchangeAccount>`) and `LoadOrgMailboxes()` already exist but are only loaded on modal open. The forwarding picker needs its own search state, a separate computed filter (that excludes the current mailbox), and immediate load on init.

The selected value stored in `_forwardingAddress` remains a string (email address) — no DTO changes needed. When a mailbox is selected from the picker, `_forwardingAddress` is set to `account.PrimaryEmailAddress`. A selected chip shows `DisplayName <PrimaryEmailAddress>`. Clearing resets `_forwardingAddress = ""`.

The 150ms blur delay before hiding dropdown (`Task.Delay(150)`) is required so that `@onmousedown` on a dropdown item fires before the input loses focus.

- [x] **Step 1: Read MailboxMailFlowTab.razor in full**
  Read all 525 lines. Confirm exact line numbers for: forwarding TextInput block (lines 41-57), `_forwardingAddress` declaration, `_orgMailboxes` declaration (line 283), `FilteredOrgMailboxes` property (lines 286-300), `LoadOrgMailboxes()` (lines 353-364), `ShowAddModal()` (lines 340-351), `OnInitializedAsync()` (line 308).

- [x] **Step 2: Add forwarding-picker state variables in @code**
  In the `// Address book search` block (around line 280), ADD alongside existing variables:
  ```csharp
  // Forwarding picker state (separate from Add Sender modal state)
  private string _forwardingSearch = "";
  private bool _showForwardingDropdown = false;

  private IEnumerable<FuseCP.Database.Models.SolidCP.ExchangeAccount> FilteredForwardingMailboxes =>
      _orgMailboxes
          .Where(a =>
              !string.IsNullOrEmpty(a.PrimaryEmailAddress) &&
              !a.PrimaryEmailAddress.Equals(Identity, StringComparison.OrdinalIgnoreCase) &&
              (string.IsNullOrEmpty(_forwardingSearch) ||
               a.DisplayName.Contains(_forwardingSearch, StringComparison.OrdinalIgnoreCase) ||
               (a.PrimaryEmailAddress?.Contains(_forwardingSearch, StringComparison.OrdinalIgnoreCase) ?? false)))
          .Take(20);
  ```
  Note: `Identity` is the current mailbox's email/samAccountName — exclude it from the picker.

- [x] **Step 3: Load org mailboxes on init**
  In `LoadSettings()` (around line 310), after the existing settings are loaded, add:
  ```csharp
  // Pre-load org mailboxes for forwarding picker (don't wait for modal open)
  if (OrganizationId > 0 && _orgMailboxes.Count == 0)
      await LoadOrgMailboxes();
  ```
  This ensures the dropdown is populated immediately when the user enables forwarding.

- [x] **Step 4: Add forwarding picker helper methods**
  In the `@code` block, add:
  ```csharp
  private string GetForwardingDisplayText()
  {
      if (string.IsNullOrEmpty(_forwardingAddress)) return "";
      var account = _orgMailboxes.FirstOrDefault(a =>
          a.PrimaryEmailAddress?.Equals(_forwardingAddress, StringComparison.OrdinalIgnoreCase) ?? false);
      return account is not null
          ? $"{account.DisplayName} <{account.PrimaryEmailAddress}>"
          : _forwardingAddress; // fallback: show raw address if not in org list
  }

  private void SelectForwardingMailbox(FuseCP.Database.Models.SolidCP.ExchangeAccount account)
  {
      _forwardingAddress = account.PrimaryEmailAddress ?? account.AccountName;
      _forwardingSearch = "";
      _showForwardingDropdown = false;
  }

  private void ClearForwardingAddress()
  {
      _forwardingAddress = "";
      _forwardingSearch = "";
      _showForwardingDropdown = false;
  }
  ```

- [x] **Step 5: Replace the forwarding TextInput block**
  Remove lines 43-45 (the `<TextInput>` for forwarding). Replace with:
  ```razor
  @if (!string.IsNullOrEmpty(_forwardingAddress))
  {
      <!-- Selected mailbox chip -->
      <div class="flex items-center gap-2 p-2 border rounded bg-surface-alt">
          <span class="text-sm text-primary flex-1">@GetForwardingDisplayText()</span>
          <button type="button"
                  class="text-muted hover:text-error text-lg leading-none"
                  @onclick="ClearForwardingAddress"
                  title="Clear forwarding address">
              &times;
          </button>
      </div>
  }
  else
  {
      <!-- Forwarding search picker -->
      <div class="relative">
          @if (_loadingMailboxes)
          {
              <p class="text-xs text-muted">@T["common.loading"]...</p>
          }
          else
          {
              <input type="text"
                     class="input w-full"
                     placeholder="@T["exchange.search_mailbox_placeholder"]"
                     @bind="_forwardingSearch"
                     @bind:event="oninput"
                     @onfocus="() => _showForwardingDropdown = true"
                     @onblur="@(() => Task.Delay(150).ContinueWith(_ => { _showForwardingDropdown = false; InvokeAsync(StateHasChanged); }))" />
              @if (_showForwardingDropdown && FilteredForwardingMailboxes.Any())
              {
                  <div class="absolute z-10 w-full mt-1 border rounded shadow-lg bg-surface max-h-48 overflow-y-auto">
                      @foreach (var account in FilteredForwardingMailboxes)
                      {
                          <div class="flex flex-col px-3 py-2 cursor-pointer hover:bg-surface-alt"
                               @onmousedown="() => SelectForwardingMailbox(account)">
                              <span class="text-sm font-medium text-primary">@account.DisplayName</span>
                              <span class="text-xs text-muted">@account.PrimaryEmailAddress</span>
                          </div>
                      }
                  </div>
              }
              else if (_showForwardingDropdown && !string.IsNullOrWhiteSpace(_forwardingSearch) && !FilteredForwardingMailboxes.Any())
              {
                  <div class="absolute z-10 w-full mt-1 border rounded shadow-lg bg-surface p-3">
                      <span class="text-xs text-muted">@T["common.no_results"]</span>
                  </div>
              }
          }
      </div>
  }
  ```

- [x] **Step 6: Build and verify**
  ```bash
  cd /c/claude/fusecp-enterprise && dotnet build src/FuseCP.Portal/FuseCP.Portal.csproj --no-restore 2>&1 | tail -10
  ```
  Confirm zero build errors. Confirm `_forwardingAddress` is still used by `SaveSettings()` via `MailboxMailFlowDto` — no DTO changes required.

- [x] **Step 7: Commit**
  ```bash
  cd /c/claude/fusecp-enterprise
  git add src/FuseCP.Portal/Components/Pages/Exchange/Tabs/MailboxMailFlowTab.razor
  git commit -m "feat(portal): replace forwarding TextInput with searchable mailbox picker

  Replace plain text input for forwarding address (lines 43-45) with a
  searchable dropdown that reuses existing _orgMailboxes infrastructure.
  Separate forwarding state (_forwardingSearch, _showForwardingDropdown,
  FilteredForwardingMailboxes) excludes current mailbox from results.
  Org mailboxes pre-loaded on init (not just on modal open).
  Selected address shown as display chip with clear button.

  FR #33

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

## Task 2: Mail Flow Tab — Wrap 4 Sections in Bootstrap Accordion (FR #33)

**Agent:** component-designer
**Estimated turns:** 12

**Files:**
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.Portal\Components\Pages\Exchange\Tabs\MailboxMailFlowTab.razor`

**Context:**
After Task 1, the forwarding section has the new picker. Now wrap all 4 sections in Bootstrap-style accordion to match `MailboxGeneralTab.razor`.

Current structure: 4 `<div class="border rounded p-4">` blocks inside `<form class="section-group">`.
Target structure: 4 `accordion-item` blocks inside `<div class="accordion" id="mailFlowAccordion">`.

The existing inner content of each section (radio buttons, checkbox lists, add/remove buttons, size limit inputs) stays UNCHANGED — only the wrapping chrome changes.

Section IDs to use:
1. `collapseForwarding` / `headingForwarding` — Forwarding
2. `collapseAccept` / `headingAccept` — Accept Messages From
3. `collapseReject` / `headingReject` — Reject Messages From
4. `collapseSizeLimits` / `headingSizeLimits` — Message Size Limits

- [x] **Step 1: Read MailboxMailFlowTab.razor in full (post-Task 1 state)**
  Identify exact boundaries of each of the 4 sections by their heading text. Map start/end line numbers.

- [x] **Step 2: Wrap the `<form>` contents in accordion container**
  Replace `<form @onsubmit="SaveSettings" @onsubmit:preventDefault class="section-group">` outer wrapper such that the 4 flat divs become accordion items. The form tag must still wrap the accordion for submit to work.

  Accordion template for each section:
  ```razor
  <div class="accordion-item">
      <h2 class="accordion-header" id="headingForwarding">
          <button class="accordion-button"
                  type="button"
                  data-bs-toggle="collapse"
                  data-bs-target="#collapseForwarding"
                  aria-expanded="true"
                  aria-controls="collapseForwarding">
              @T["exchange.forwarding"]
          </button>
      </h2>
      <div id="collapseForwarding"
           class="accordion-collapse collapse show"
           aria-labelledby="headingForwarding"
           data-bs-parent="#mailFlowAccordion">
          <div class="accordion-body">
              <!-- ALL existing forwarding section content goes here, UNCHANGED -->
          </div>
      </div>
  </div>
  ```
  Apply same pattern for Accept (using `collapseAccept`/`headingAccept`), Reject (`collapseReject`/`headingReject`), and Size Limits (`collapseSizeLimits`/`headingSizeLimits`).

- [x] **Step 3: Remove the old flat `<div class="border rounded p-4">` wrappers**
  Each of the 4 old wrapper divs should be removed — their inner content is now inside `accordion-body`.

- [x] **Step 4: Add the Save button outside the accordion (at form bottom)**
  Verify the Save button and any global error/success alerts remain outside the accordion items, at the bottom of the form.

- [x] **Step 5: Build and verify**
  ```bash
  cd /c/claude/fusecp-enterprise && dotnet build src/FuseCP.Portal/FuseCP.Portal.csproj --no-restore 2>&1 | tail -10
  ```

- [x] **Step 6: Commit**
  ```bash
  cd /c/claude/fusecp-enterprise
  git add src/FuseCP.Portal/Components/Pages/Exchange/Tabs/MailboxMailFlowTab.razor
  git commit -m "feat(portal): wrap MailboxMailFlowTab sections in Bootstrap accordion

  Replace 4 flat border-rounded divs with Bootstrap accordion matching
  MailboxGeneralTab pattern. Section IDs: collapseForwarding, collapseAccept,
  collapseReject, collapseSizeLimits. All sections default open (show class).
  Inner section content unchanged.

  FR #33

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

## Task 3: Add Contact Columns to Packages Table (FR #36)

**Agent:** database-architect
**Estimated turns:** 8

**Files:**
- Create: `C:\claude\fusecp-enterprise\src\FuseCP.Database\Migrations\093_AddOrganizationContactFields.sql`

**CRITICAL CONSTRAINT:** ALL changes ADDITIVE only. The `Packages` table is a SolidCP-compatible table. Never drop, rename, or alter existing columns. Every new column is nullable.

**Context:**
Contact fields for organizations are stored in the `Packages` table (not a custom `Organizations` table). The PackageRepository reads from `Packages`. The migration number is 093 (last was 092).

- [x] **Step 1: Inspect current Packages table schema**
  ```bash
  sqlcmd -S "(local)\SQLEXPRESS" -d FuseCPLab -Q "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Packages' ORDER BY ORDINAL_POSITION"
  ```
  Confirm the table name is `Packages` and list any existing contact-related columns to avoid duplication.

- [x] **Step 2: Create the migration file**
  Write `093_AddOrganizationContactFields.sql`:
  ```sql
  -- Migration 093: Add organization contact fields to Packages table
  -- ADDITIVE ONLY: All columns nullable, no existing columns modified
  -- SolidCP compatible: Packages table is shared with SolidCP schema

  IF NOT EXISTS (
      SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
      WHERE TABLE_NAME = 'Packages' AND COLUMN_NAME = 'CompanyLegalName'
  )
  BEGIN
      ALTER TABLE [dbo].[Packages]
          ADD [CompanyLegalName]  NVARCHAR(255)  NULL,
              [TaxId]             NVARCHAR(100)  NULL,
              [ContactPhone]      NVARCHAR(50)   NULL,
              [ContactEmail]      NVARCHAR(255)  NULL,
              [Address]           NVARCHAR(500)  NULL,
              [City]              NVARCHAR(100)  NULL,
              [State]             NVARCHAR(100)  NULL,
              [PostalCode]        NVARCHAR(20)   NULL,
              [Country]           NVARCHAR(100)  NULL,
              [Website]           NVARCHAR(500)  NULL;
  END
  GO
  ```
  Note: Using `ContactPhone` and `ContactEmail` (prefixed) to avoid conflict if SolidCP already has generic `Phone`/`Email` columns in the table. The Step 1 schema check will confirm.

- [x] **Step 3: Apply migration to local database**
  ```bash
  sqlcmd -S "(local)\SQLEXPRESS" -d FuseCPLab -i src/FuseCP.Database/Migrations/093_AddOrganizationContactFields.sql
  ```
  Verify the columns were added:
  ```bash
  sqlcmd -S "(local)\SQLEXPRESS" -d FuseCPLab -Q "SELECT COLUMN_NAME, IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Packages' AND COLUMN_NAME IN ('CompanyLegalName','TaxId','ContactPhone','ContactEmail','Address','City','State','PostalCode','Country','Website')"
  ```
  All 10 columns must appear with `IS_NULLABLE = YES`.

- [x] **Step 4: Commit**
  ```bash
  cd /c/claude/fusecp-enterprise
  git add src/FuseCP.Database/Migrations/093_AddOrganizationContactFields.sql
  git commit -m "feat(db): add 10 contact fields to Packages table — migration 093 (ADDITIVE only)

  New nullable columns: CompanyLegalName, TaxId, ContactPhone, ContactEmail,
  Address, City, State, PostalCode, Country, Website.
  Idempotent (IF NOT EXISTS guard). No existing columns modified.
  SolidCP Packages table compatibility preserved.

  FR #36

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

## Task 4: Add Organization Contact API Endpoints (FR #36)

**Agent:** modular-builder
**Estimated turns:** 15

**Files:**
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.EnterpriseServer\Program.cs` (add endpoints to existing `orgGroup`)
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.Database\Repositories\SolidCP\PackageRepository.cs` (add contact methods)
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.Database\Repositories\SolidCP\IPackageRepository.cs` (add interface methods)

**Context:**
Organization API endpoints are defined inline in `Program.cs` under the `orgGroup` route group (around line 565). `PackageRepository` uses Dapper with `SqlConnection` created per call (no shared connection). All new endpoints follow the existing `orgGroup.MapGet/MapPost` pattern and use `IPackageRepository` which is already DI-registered.

DTOs belong near the endpoint definitions in `Program.cs` (existing pattern — check where other response records are defined in Program.cs).

- [x] **Step 1: Read relevant Program.cs section and PackageRepository**
  Read `Program.cs` lines 560-650 to understand the orgGroup endpoint pattern. Read `PackageRepository.cs` in full to understand Dapper usage pattern (connection per method, `CommandDefinition`, `ConfigureAwait(false)`). Read `IPackageRepository.cs` to understand interface style.

- [x] **Step 2: Define contact DTOs**
  Near the existing DTO/record definitions in `Program.cs` (or in a new file `src/FuseCP.EnterpriseServer/Models/OrganizationContactDtos.cs`), add:
  ```csharp
  public sealed record OrganizationContactDto(
      string? CompanyLegalName,
      string? TaxId,
      string? ContactPhone,
      string? ContactEmail,
      string? Address,
      string? City,
      string? State,
      string? PostalCode,
      string? Country,
      string? Website
  );
  ```
  Single record used for both GET response and PUT request body.

- [x] **Step 3: Add GetContactAsync to IPackageRepository and PackageRepository**
  In `IPackageRepository.cs`:
  ```csharp
  Task<OrganizationContactDto?> GetContactAsync(int packageId, CancellationToken ct = default);
  ```
  In `PackageRepository.cs`:
  ```csharp
  public async Task<OrganizationContactDto?> GetContactAsync(int packageId, CancellationToken ct = default)
  {
      await using var connection = new SqlConnection(_connectionString);
      var command = new CommandDefinition(
          @"SELECT CompanyLegalName, TaxId, ContactPhone, ContactEmail, Address,
                   City, State, PostalCode, Country, Website
            FROM Packages WHERE PackageID = @packageId",
          new { packageId },
          cancellationToken: ct);
      return await connection.QuerySingleOrDefaultAsync<OrganizationContactDto>(command).ConfigureAwait(false);
  }
  ```

- [x] **Step 4: Add UpdateContactAsync to IPackageRepository and PackageRepository**
  In `IPackageRepository.cs`:
  ```csharp
  Task UpdateContactAsync(int packageId, OrganizationContactDto contact, CancellationToken ct = default);
  ```
  In `PackageRepository.cs`:
  ```csharp
  public async Task UpdateContactAsync(int packageId, OrganizationContactDto contact, CancellationToken ct = default)
  {
      await using var connection = new SqlConnection(_connectionString);
      var command = new CommandDefinition(
          @"UPDATE Packages SET
              CompanyLegalName = @CompanyLegalName,
              TaxId = @TaxId,
              ContactPhone = @ContactPhone,
              ContactEmail = @ContactEmail,
              Address = @Address,
              City = @City,
              State = @State,
              PostalCode = @PostalCode,
              Country = @Country,
              Website = @Website
            WHERE PackageID = @packageId",
          new
          {
              contact.CompanyLegalName, contact.TaxId, contact.ContactPhone, contact.ContactEmail,
              contact.Address, contact.City, contact.State, contact.PostalCode, contact.Country,
              contact.Website, packageId
          },
          cancellationToken: ct);
      await connection.ExecuteAsync(command).ConfigureAwait(false);
  }
  ```

- [x] **Step 5: Register two new endpoints in Program.cs orgGroup**
  In `Program.cs`, after the existing `orgGroup.MapGet("/{id:int}/quota", ...)` endpoint, add:
  ```csharp
  orgGroup.MapGet("/{id:int}/contact", async (
      int id,
      IPackageRepository packageRepo,
      CancellationToken ct) =>
  {
      var contact = await packageRepo.GetContactAsync(id, ct);
      return contact is null ? Results.NotFound() : Results.Ok(contact);
  })
  .WithName("GetOrganizationContact")
  .WithDescription("Returns contact information fields for an organization")
  .Produces<OrganizationContactDto>(StatusCodes.Status200OK)
  .Produces(StatusCodes.Status404NotFound);

  orgGroup.MapPut("/{id:int}/contact", async (
      int id,
      OrganizationContactDto body,
      IPackageRepository packageRepo,
      CancellationToken ct) =>
  {
      // Verify the package exists before updating
      var existing = await packageRepo.GetByIdAsync(id, ct);
      if (existing is null) return Results.NotFound();
      await packageRepo.UpdateContactAsync(id, body, ct);
      return Results.Ok();
  })
  .WithName("UpdateOrganizationContact")
  .WithDescription("Updates contact information fields for an organization")
  .Produces(StatusCodes.Status200OK)
  .Produces(StatusCodes.Status404NotFound);
  ```

- [x] **Step 6: Build and smoke test**
  ```bash
  cd /c/claude/fusecp-enterprise && dotnet build --no-restore 2>&1 | tail -10
  ```
  After starting the API, test:
  ```bash
  curl -sk -H "X-Api-Key: fusecp-admin-key-2026" "http://localhost:5010/api/organizations/101/contact"
  ```

- [x] **Step 7: Commit**
  ```bash
  cd /c/claude/fusecp-enterprise
  git add src/FuseCP.EnterpriseServer/Program.cs \
          src/FuseCP.Database/Repositories/SolidCP/PackageRepository.cs \
          src/FuseCP.Database/Repositories/SolidCP/IPackageRepository.cs
  git commit -m "feat(api): add GET/PUT /api/organizations/{id}/contact endpoints

  New contact endpoints read/write 10 fields (CompanyLegalName, TaxId,
  ContactPhone, ContactEmail, Address, City, State, PostalCode, Country,
  Website) from Packages table via PackageRepository. Added to orgGroup
  route group (PlatformAdmin auth). OrganizationContactDto used for
  both GET response and PUT request body.

  FR #36

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

## Task 5: Add Contact Section to OrganizationEdit.razor (FR #36)

**Agent:** component-designer
**Estimated turns:** 15

**Files:**
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.Portal\Services\IOrganizationApiClient.cs`
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.Portal\Services\OrganizationApiClient.cs`
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.Portal\Components\Pages\Admin\OrganizationEdit.razor`
- Reference (read-only): `C:\claude\fusecp-enterprise\tmp\mailbox-general-tab-playground.html`

**Context:**
`OrganizationEdit.razor` is a simple flat form (no accordion currently) injecting `IOrganizationApiClient OrgApi`. It manages name, status, and hosting plan. The Contact Information section will be added as a new `accordion-item` BELOW the existing form content, using the same Bootstrap accordion pattern as MailboxGeneralTab.

The `IOrganizationApiClient` needs two new methods: `GetContactAsync(int packageId)` and `UpdateContactAsync(int packageId, OrganizationContactDto contact)`. The portal uses `ApiResult<T>` and `ApiOperationResult` patterns — match existing client methods.

Since the whole OrganizationEdit form is not currently accordion-based, we add only the Contact section as an accordion and leave existing fields in their flat layout. The form submit button wires both the existing save and the new contact save.

- [x] **Step 1: Read OrganizationEdit.razor in full**
  Read all 237 lines. Understand: how `Id` parameter is used, what `OnInitializedAsync` loads, how save works (calls OrgApi methods), where the submit button is. Note that `_package.PackageID` is the ID used for API calls.

- [x] **Step 2: Read IOrganizationApiClient.cs and OrganizationApiClient.cs**
  Read both files fully. Understand `ApiResult<T>` pattern, how HTTP calls are made (`_httpClient.GetFromJsonAsync`, `PutAsJsonAsync`, etc.), base URL configuration, and how `X-Api-Key` header is set.

- [x] **Step 3: Define OrganizationContactDto in portal services**
  In `IOrganizationApiClient.cs` (after existing records), add:
  ```csharp
  public sealed record OrganizationContactDto(
      string? CompanyLegalName,
      string? TaxId,
      string? ContactPhone,
      string? ContactEmail,
      string? Address,
      string? City,
      string? State,
      string? PostalCode,
      string? Country,
      string? Website
  );
  ```

- [x] **Step 4: Add interface methods to IOrganizationApiClient**
  ```csharp
  Task<ApiResult<OrganizationContactDto>> GetContactAsync(int packageId, CancellationToken ct = default);
  Task<ApiOperationResult> UpdateContactAsync(int packageId, OrganizationContactDto contact, CancellationToken ct = default);
  ```

- [x] **Step 5: Implement in OrganizationApiClient.cs**
  Following existing implementation patterns:
  ```csharp
  public async Task<ApiResult<OrganizationContactDto>> GetContactAsync(int packageId, CancellationToken ct = default)
  {
      var response = await _httpClient.GetAsync($"/api/organizations/{packageId}/contact", ct);
      if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
          return ApiResult<OrganizationContactDto>.Ok(new OrganizationContactDto(null, null, null, null, null, null, null, null, null, null));
      if (!response.IsSuccessStatusCode)
          return ApiResult<OrganizationContactDto>.Fail($"Failed to load contact: {response.StatusCode}");
      var dto = await response.Content.ReadFromJsonAsync<OrganizationContactDto>(cancellationToken: ct);
      return ApiResult<OrganizationContactDto>.Ok(dto!);
  }

  public async Task<ApiOperationResult> UpdateContactAsync(int packageId, OrganizationContactDto contact, CancellationToken ct = default)
  {
      var response = await _httpClient.PutAsJsonAsync($"/api/organizations/{packageId}/contact", contact, ct);
      return response.IsSuccessStatusCode
          ? ApiOperationResult.Ok()
          : ApiOperationResult.Fail($"Failed to update contact: {response.StatusCode}");
  }
  ```
  Adjust method signatures to match existing `ApiResult<T>` / `ApiOperationResult` factory patterns exactly.

- [x] **Step 6: Add contact state variables to OrganizationEdit.razor @code**
  ```csharp
  private OrganizationContactDto _contact = new(null, null, null, null, null, null, null, null, null, null);
  private bool _contactLoaded = false;

  // Mutable fields for binding (records are immutable, so use separate variables)
  private string? _companyLegalName;
  private string? _taxId;
  private string? _contactPhone;
  private string? _contactEmail;
  private string? _contactAddress;
  private string? _contactCity;
  private string? _contactState;
  private string? _contactPostalCode;
  private string? _contactCountry;
  private string? _contactWebsite;
  ```
  In `OnInitializedAsync`, after loading `_package`, add:
  ```csharp
  var contactResult = await OrgApi.GetContactAsync(Id);
  if (contactResult.IsSuccess && contactResult.Data is not null)
  {
      var c = contactResult.Data;
      _companyLegalName = c.CompanyLegalName;
      _taxId = c.TaxId;
      _contactPhone = c.ContactPhone;
      _contactEmail = c.ContactEmail;
      _contactAddress = c.Address;
      _contactCity = c.City;
      _contactState = c.State;
      _contactPostalCode = c.PostalCode;
      _contactCountry = c.Country;
      _contactWebsite = c.Website;
  }
  _contactLoaded = true;
  ```

- [x] **Step 7: Wire contact save alongside existing save**
  In the existing save handler, after the org name/status/plan updates succeed, add:
  ```csharp
  var contactDto = new OrganizationContactDto(
      _companyLegalName, _taxId, _contactPhone, _contactEmail,
      _contactAddress, _contactCity, _contactState, _contactPostalCode,
      _contactCountry, _contactWebsite);
  await OrgApi.UpdateContactAsync(Id, contactDto);
  ```

- [x] **Step 8: Add Contact Information accordion section to razor markup**
  Below the existing form content (before the save button), add:
  ```razor
  @if (_contactLoaded)
  {
      <div class="accordion mt-4" id="orgContactAccordion">
          <div class="accordion-item">
              <h2 class="accordion-header" id="headingOrgContact">
                  <button class="accordion-button"
                          type="button"
                          data-bs-toggle="collapse"
                          data-bs-target="#collapseOrgContact"
                          aria-expanded="true"
                          aria-controls="collapseOrgContact">
                      @T["org.contact_information"]
                  </button>
              </h2>
              <div id="collapseOrgContact"
                   class="accordion-collapse collapse show"
                   aria-labelledby="headingOrgContact"
                   data-bs-parent="#orgContactAccordion">
                  <div class="accordion-body">
                      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                              <label class="label">@T["org.company_legal_name"]</label>
                              <input type="text" class="input" @bind="_companyLegalName" />
                          </div>
                          <div>
                              <label class="label">@T["org.tax_id"]</label>
                              <input type="text" class="input" @bind="_taxId" />
                          </div>
                          <div>
                              <label class="label">@T["org.contact_phone"]</label>
                              <input type="tel" class="input" @bind="_contactPhone" />
                          </div>
                          <div>
                              <label class="label">@T["org.contact_email"]</label>
                              <input type="email" class="input" @bind="_contactEmail" />
                          </div>
                          <div class="md:col-span-2">
                              <label class="label">@T["org.address"]</label>
                              <input type="text" class="input" @bind="_contactAddress" />
                          </div>
                          <div>
                              <label class="label">@T["org.city"]</label>
                              <input type="text" class="input" @bind="_contactCity" />
                          </div>
                          <div>
                              <label class="label">@T["org.state"]</label>
                              <input type="text" class="input" @bind="_contactState" />
                          </div>
                          <div>
                              <label class="label">@T["org.postal_code"]</label>
                              <input type="text" class="input" @bind="_contactPostalCode" />
                          </div>
                          <div>
                              <label class="label">@T["org.country"]</label>
                              <input type="text" class="input" @bind="_contactCountry" />
                          </div>
                          <div>
                              <label class="label">@T["org.website"]</label>
                              <input type="url" class="input" @bind="_contactWebsite" />
                          </div>
                      </div>
                  </div>
              </div>
          </div>
      </div>
  }
  ```

- [x] **Step 9: Add i18n keys for new contact labels**
  Create migration `094_AddOrgContactTranslations.sql` with EN/PL translations for:
  `org.contact_information`, `org.company_legal_name`, `org.tax_id`, `org.contact_phone`,
  `org.contact_email`, `org.address`, `org.city`, `org.state`, `org.postal_code`,
  `org.country`, `org.website`

- [x] **Step 10: Build and verify**
  ```bash
  cd /c/claude/fusecp-enterprise && dotnet build --no-restore 2>&1 | tail -10
  ```

- [x] **Step 11: Commit**
  ```bash
  cd /c/claude/fusecp-enterprise
  git add src/FuseCP.Portal/Services/IOrganizationApiClient.cs \
          src/FuseCP.Portal/Services/OrganizationApiClient.cs \
          src/FuseCP.Portal/Components/Pages/Admin/OrganizationEdit.razor \
          src/FuseCP.Database/Migrations/094_AddOrgContactTranslations.sql
  git commit -m "feat(portal): add Contact Information section to OrganizationEdit

  New accordion section with 10 contact fields in 2-column grid layout.
  Loads from GET /api/organizations/{id}/contact on init, saves alongside
  existing org name/status/plan save. Added GetContactAsync/UpdateContactAsync
  to IOrganizationApiClient. Added i18n keys (migration 094).

  FR #36

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

## Task 6: Add thumbnailPhoto Read/Write to AD Provider and API (FR #37)

**Agent:** modular-builder
**Estimated turns:** 18

**Files:**
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.Providers.AD\AdProvider.cs`
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.EnterpriseServer\Endpoints\ADEndpoints.cs`

**Context:**
AD stores `thumbnailPhoto` as a raw byte array (JPEG). Max size enforced: 100KB. The provider needs `GetUserPhotoAsync` (return base64 string or null) and `SetUserPhotoAsync` (accept base64 string or null to clear). Exposed via two new API endpoints: `GET /api/ad/users/{identity}/photo` and `PUT /api/ad/users/{identity}/photo`.

The AD provider uses WinRM to communicate with the AD controller at 172.31.251.101. Read `AdProvider.cs` first to understand whether `GetUserAsync` and `UpdateUserAsync` use `DirectoryEntry` directly or via WinRM PowerShell — the photo methods must use the same approach.

- [x] **Step 1: Read AdProvider.cs in full**
  Understand how `GetUserAsync`, `UpdateUserAsync` work. Confirm whether `thumbnailPhoto` access is via `DirectorySearcher`/`DirectoryEntry` or via PowerShell WinRM (Get-ADUser). Identify the method signature pattern and error handling style used.

- [x] **Step 2: Read ADEndpoints.cs in full**
  Understand existing endpoint patterns: parameter naming, auth requirements, error response shapes, how `IAdProvider` or `IAdApiClient` is injected.

- [x] **Step 3: Add GetUserPhotoAsync to the AD provider**
  If using `DirectoryEntry`:
  ```csharp
  public Task<string?> GetUserPhotoAsync(string identity)
  {
      try
      {
          using var entry = GetUserDirectoryEntry(identity); // use existing helper
          var photoBytes = entry.Properties["thumbnailPhoto"].Value as byte[];
          if (photoBytes == null || photoBytes.Length == 0) return Task.FromResult<string?>(null);
          return Task.FromResult<string?>(Convert.ToBase64String(photoBytes));
      }
      catch
      {
          return Task.FromResult<string?>(null);
      }
  }
  ```
  If using PowerShell WinRM, use `Get-ADUser -Identity {identity} -Properties thumbnailPhoto` and extract the byte array from the result.

- [x] **Step 4: Add SetUserPhotoAsync to the AD provider**
  If using `DirectoryEntry`:
  ```csharp
  public Task SetUserPhotoAsync(string identity, string? base64Photo)
  {
      using var entry = GetUserDirectoryEntry(identity);
      if (string.IsNullOrEmpty(base64Photo))
      {
          entry.Properties["thumbnailPhoto"].Clear();
      }
      else
      {
          var bytes = Convert.FromBase64String(base64Photo);
          if (bytes.Length > 100 * 1024)
              throw new ArgumentException("Photo size exceeds 100KB AD limit");
          entry.Properties["thumbnailPhoto"].Value = bytes;
      }
      entry.CommitChanges();
      return Task.CompletedTask;
  }
  ```
  If using PowerShell WinRM, use `Set-ADUser -Identity {identity} -Replace @{thumbnailPhoto=[byte[]]...}` or `-Clear thumbnailPhoto`.

- [x] **Step 5: Add the methods to the IAdProvider interface (if applicable)**
  If an `IAdProvider` interface exists, add:
  ```csharp
  Task<string?> GetUserPhotoAsync(string identity);
  Task SetUserPhotoAsync(string identity, string? base64Photo);
  ```

- [x] **Step 6: Add GET and PUT photo endpoints to ADEndpoints.cs**
  ```csharp
  adGroup.MapGet("/users/{identity}/photo", async (
      string identity,
      IAdProvider adProvider,
      CancellationToken ct) =>
  {
      var photoBase64 = await adProvider.GetUserPhotoAsync(identity);
      return photoBase64 is null
          ? Results.NotFound()
          : Results.Ok(new { photoBase64 });
  })
  .WithName("GetAdUserPhoto")
  .WithDescription("Returns the thumbnailPhoto for an AD user as base64, or 404 if none set");

  adGroup.MapPut("/users/{identity}/photo", async (
      string identity,
      PhotoRequest body,
      IAdProvider adProvider,
      CancellationToken ct) =>
  {
      try
      {
          await adProvider.SetUserPhotoAsync(identity, body.PhotoBase64);
          return Results.Ok();
      }
      catch (ArgumentException ex)
      {
          return Results.BadRequest(new { error = ex.Message });
      }
  })
  .WithName("SetAdUserPhoto")
  .WithDescription("Sets or clears the thumbnailPhoto for an AD user (null PhotoBase64 = clear)");
  ```
  Add `PhotoRequest` record near ADEndpoints: `public sealed record PhotoRequest(string? PhotoBase64);`

- [x] **Step 7: Build and verify**
  ```bash
  cd /c/claude/fusecp-enterprise && dotnet build --no-restore 2>&1 | tail -10
  ```

- [x] **Step 8: Commit**
  ```bash
  cd /c/claude/fusecp-enterprise
  git add src/FuseCP.Providers.AD/AdProvider.cs \
          src/FuseCP.EnterpriseServer/Endpoints/ADEndpoints.cs
  git commit -m "feat(ad): add thumbnailPhoto read/write to AD provider and endpoints

  New GetUserPhotoAsync (returns base64 or null) and SetUserPhotoAsync
  (accepts base64 or null to clear, enforces 100KB limit) in AdProvider.
  Exposed as GET/PUT /api/ad/users/{identity}/photo.

  FR #37

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

## Task 7: Add Circular Avatar to MailboxGeneralTab (FR #37)

**Agent:** component-designer
**Estimated turns:** 18

**Files:**
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.Portal\Services\IAdApiClient.cs` (portal-side AD client interface)
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.Portal\Services\AdApiClient.cs` (portal-side AD client impl)
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.Portal\Components\Pages\Exchange\Tabs\MailboxGeneralTab.razor`
- Reference (read-only): `C:\claude\fusecp-enterprise\tmp\mailbox-general-tab-playground.html`

**Context:**
`MailboxGeneralTab.razor` already injects `IAdApiClient` (for password resets). The portal-side `IAdApiClient` needs two new methods calling the new photo endpoints added in Task 6.

The avatar is placed ABOVE the accordion sections (before `<div class="accordion" id="generalTabAccordion">`). Initials fallback: first char of `_firstName` + first char of `_lastName` (already loaded from the API).

The `InputFile` component for upload must be hidden behind a styled label (standard Blazor pattern). Photo upload fires immediately on file select (not on form save). 100KB client-side size check before uploading.

- [x] **Step 1: Read IAdApiClient.cs and AdApiClient.cs**
  Understand existing method signatures, HTTP call patterns, `ApiResult<T>` usage. Confirm the base URL and auth header patterns match.

- [x] **Step 2: Add photo methods to IAdApiClient**
  ```csharp
  Task<ApiResult<string?>> GetUserPhotoAsync(string identity, CancellationToken ct = default);
  Task<ApiOperationResult> SetUserPhotoAsync(string identity, string? base64Photo, CancellationToken ct = default);
  ```

- [x] **Step 3: Implement in AdApiClient.cs**
  ```csharp
  public async Task<ApiResult<string?>> GetUserPhotoAsync(string identity, CancellationToken ct = default)
  {
      var response = await _httpClient.GetAsync($"/api/ad/users/{Uri.EscapeDataString(identity)}/photo", ct);
      if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
          return ApiResult<string?>.Ok(null);
      if (!response.IsSuccessStatusCode)
          return ApiResult<string?>.Fail($"Failed to load photo: {response.StatusCode}");
      var result = await response.Content.ReadFromJsonAsync<PhotoResponse>(cancellationToken: ct);
      return ApiResult<string?>.Ok(result?.PhotoBase64);
  }

  public async Task<ApiOperationResult> SetUserPhotoAsync(string identity, string? base64Photo, CancellationToken ct = default)
  {
      var response = await _httpClient.PutAsJsonAsync(
          $"/api/ad/users/{Uri.EscapeDataString(identity)}/photo",
          new { PhotoBase64 = base64Photo }, ct);
      return response.IsSuccessStatusCode
          ? ApiOperationResult.Ok()
          : ApiOperationResult.Fail($"Failed to update photo: {response.StatusCode}");
  }

  private sealed record PhotoResponse(string? PhotoBase64);
  ```

- [x] **Step 4: Add avatar state and helpers in MailboxGeneralTab @code**
  ```csharp
  private string? _photoBase64;
  private bool _photoLoading = false;
  private string? _photoError;

  private string AvatarInitials =>
      $"{_firstName?.FirstOrDefault()}{_lastName?.FirstOrDefault()}".Trim().ToUpper();

  private async Task LoadPhotoAsync()
  {
      var result = await AdApiClient.GetUserPhotoAsync(Identity);
      if (result.IsSuccess) _photoBase64 = result.Data;
  }
  ```
  Call `LoadPhotoAsync()` inside `OnInitializedAsync` (or `LoadSettings`) after `_firstName` / `_lastName` are populated.

- [x] **Step 5: Add upload and clear handlers**
  ```csharp
  private async Task HandlePhotoUpload(InputFileChangeEventArgs e)
  {
      _photoError = null;
      var file = e.File;
      if (file.Size > 100 * 1024)
      {
          _photoError = T["exchange.photo_too_large"]; // "Photo must be under 100KB"
          return;
      }
      _photoLoading = true;
      StateHasChanged();
      try
      {
          using var stream = file.OpenReadStream(maxAllowedSize: 100 * 1024);
          var bytes = new byte[file.Size];
          await stream.ReadExactlyAsync(bytes);
          var base64 = Convert.ToBase64String(bytes);
          var result = await AdApiClient.SetUserPhotoAsync(Identity, base64);
          if (result.IsSuccess) _photoBase64 = base64;
          else _photoError = result.ErrorMessage;
      }
      catch (Exception ex) { _photoError = ex.Message; }
      _photoLoading = false;
  }

  private async Task ClearPhoto()
  {
      _photoLoading = true;
      StateHasChanged();
      var result = await AdApiClient.SetUserPhotoAsync(Identity, null);
      if (result.IsSuccess) _photoBase64 = null;
      else _photoError = result.ErrorMessage;
      _photoLoading = false;
  }
  ```

- [x] **Step 6: Add avatar CSS to the tab's `<style>` block**
  ```css
  .avatar-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 10px;
      padding: 16px 0 24px;
  }
  .avatar-circle {
      width: 96px;
      height: 96px;
      border-radius: 50%;
      border: 2px solid var(--bs-border-color, #dee2e6);
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--bs-secondary-bg, #f8f9fa);
      font-size: 2rem;
      font-weight: 700;
      color: var(--bs-primary, #0d6efd);
      user-select: none;
  }
  .avatar-circle img {
      width: 100%;
      height: 100%;
      object-fit: cover;
  }
  .avatar-actions {
      display: flex;
      gap: 8px;
  }
  ```

- [x] **Step 7: Add avatar markup above the accordion in razor**
  Before `<div class="accordion" id="generalTabAccordion">`, add:
  ```razor
  <div class="avatar-container">
      <div class="avatar-circle">
          @if (_photoLoading)
          {
              <span class="spinner-border spinner-border-sm" role="status"></span>
          }
          else if (!string.IsNullOrEmpty(_photoBase64))
          {
              <img src="data:image/jpeg;base64,@_photoBase64" alt="@T["exchange.user_photo"]" />
          }
          else
          {
              <span>@AvatarInitials</span>
          }
      </div>
      @if (!string.IsNullOrEmpty(_photoError))
      {
          <small class="text-danger">@_photoError</small>
      }
      <div class="avatar-actions">
          <label class="btn btn-sm btn-outline-secondary" style="cursor: pointer;">
              @T["exchange.upload_photo"]
              <InputFile OnChange="HandlePhotoUpload" accept=".jpg,.jpeg,.png" style="display: none;" />
          </label>
          @if (!string.IsNullOrEmpty(_photoBase64))
          {
              <button type="button" class="btn btn-sm btn-outline-danger" @onclick="ClearPhoto">
                  @T["exchange.clear_photo"]
              </button>
          }
      </div>
  </div>
  ```

- [x] **Step 8: Add i18n keys for photo UI**
  Create migration `095_AddPhotoTranslations.sql` with EN/PL translations for:
  `exchange.upload_photo`, `exchange.clear_photo`, `exchange.user_photo`, `exchange.photo_too_large`

- [x] **Step 9: Build and verify**
  ```bash
  cd /c/claude/fusecp-enterprise && dotnet build --no-restore 2>&1 | tail -10
  ```

- [x] **Step 10: Commit**
  ```bash
  cd /c/claude/fusecp-enterprise
  git add src/FuseCP.Portal/Services/IAdApiClient.cs \
          src/FuseCP.Portal/Services/AdApiClient.cs \
          src/FuseCP.Portal/Components/Pages/Exchange/Tabs/MailboxGeneralTab.razor \
          src/FuseCP.Database/Migrations/095_AddPhotoTranslations.sql
  git commit -m "feat(portal): add circular avatar with photo upload to MailboxGeneralTab

  Circular 96px avatar above accordion: shows thumbnailPhoto (base64 JPEG)
  from AD or initials fallback. Upload (100KB max, jpg/png) fires immediately.
  Clear button removes photo from AD. Spinner during load/upload.
  Added GetUserPhotoAsync/SetUserPhotoAsync to IAdApiClient.
  Added i18n keys for photo UI (migration 095).

  FR #37

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

## Task 8: Build, Test and Cleanup

**Agent:** post-task-cleanup
**Estimated turns:** 12

**Files:**
- Review: all files modified in Tasks 1-7
- Run: full build and test suite

**Context:**
Final verification pass after all 7 implementation tasks. Verify build cleanliness, test pass rate, DB additivity, accordion pattern consistency, and no dead code.

- [x] **Step 1: Full solution build**
  ```bash
  cd /c/claude/fusecp-enterprise && dotnet build 2>&1 | tail -20
  ```
  Zero errors required. Treat warnings as issues to resolve.

- [x] **Step 2: Run all tests**
  ```bash
  cd /c/claude/fusecp-enterprise && dotnet test tests/ 2>&1 | tail -30
  ```
  All existing tests must pass. Report any regressions.

- [x] **Step 3: Verify DB migrations are additive**
  ```bash
  sqlcmd -S "(local)\SQLEXPRESS" -d FuseCPLab -Q "
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'Packages'
    AND COLUMN_NAME IN ('CompanyLegalName','TaxId','ContactPhone','ContactEmail',
                        'Address','City','State','PostalCode','Country','Website')
    ORDER BY COLUMN_NAME"
  ```
  All 10 columns must exist and be `IS_NULLABLE = YES`.

- [x] **Step 4: Verify accordion pattern consistency**
  Grep both tab files for accordion class names:
  ```bash
  grep -n "accordion-item\|accordion-button\|accordion-collapse" \
    src/FuseCP.Portal/Components/Pages/Exchange/Tabs/MailboxGeneralTab.razor \
    src/FuseCP.Portal/Components/Pages/Exchange/Tabs/MailboxMailFlowTab.razor \
    src/FuseCP.Portal/Components/Pages/Admin/OrganizationEdit.razor
  ```
  Confirm all three files use `accordion-item`, `accordion-button`, `accordion-collapse collapse show` consistently.

- [x] **Step 5: Scan for dead code in MailboxMailFlowTab.razor**
  Verify the old `<TextInput>` for forwarding is completely removed (no commented-out block). Verify `_forwardingAddress` string variable is still in use in `SaveSettings()`. Verify `_forwardingSearch` and `_showForwardingDropdown` are declared and used in markup.

- [x] **Step 6: Verify forwarding picker excludes current mailbox**
  Confirm `FilteredForwardingMailboxes` filters out the mailbox whose `Identity` matches the current mailbox's email address.

- [x] **Step 7: Scan for unused variables**
  Run:
  ```bash
  cd /c/claude/fusecp-enterprise && dotnet build --no-restore 2>&1 | grep -i "warning.*unused\|CS0219\|CS0168"
  ```
  Fix any unused variable warnings introduced by the new code.

- [x] **Step 8: Final commit for any cleanup changes**
  ```bash
  cd /c/claude/fusecp-enterprise
  git add .
  git commit -m "chore: post-implementation cleanup for Mail Flow Tab and Phase 2 features

  Fix unused variables, verify accordion consistency across 3 files,
  confirm DB migration additivity. All builds clean, all tests pass.

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

## Summary Table

| Task | Phase | Agent | Primary Files | FR | est. turns |
|------|-------|-------|---------------|-----|------------|
| 1 | Phase 3 | component-designer | `MailboxMailFlowTab.razor` | #33 | 15 |
| 2 | Phase 3 | component-designer | `MailboxMailFlowTab.razor` | #33 | 12 |
| 3 | Phase 2 | database-architect | `093_AddOrganizationContactFields.sql` | #36 | 8 |
| 4 | Phase 2 | modular-builder | `Program.cs`, `PackageRepository.cs`, `IPackageRepository.cs` | #36 | 15 |
| 5 | Phase 2 | component-designer | `IOrganizationApiClient.cs`, `OrganizationApiClient.cs`, `OrganizationEdit.razor` | #36 | 15 |
| 6 | Phase 2 | modular-builder | `AdProvider.cs`, `ADEndpoints.cs` | #37 | 18 |
| 7 | Phase 2 | component-designer | `IAdApiClient.cs`, `AdApiClient.cs`, `MailboxGeneralTab.razor` | #37 | 18 |
| 8 | All | post-task-cleanup | All modified files | — | 12 |

**Total tasks: 8** | **Total estimated turns: 113**

### Dependency Order

Tasks 1 and 2 are independent of Tasks 3-7 and can be dispatched in parallel.
Tasks 3 → 4 → 5 must be sequential (schema before API before UI).
Task 6 → Task 7 must be sequential (AD provider endpoints before portal client).
Task 8 runs last after all others complete.

### Key Architecture Reminders

- `_orgMailboxes` type: `List<FuseCP.Database.Models.SolidCP.ExchangeAccount>` — use `PrimaryEmailAddress` (nullable) and `DisplayName`
- `LoadOrgMailboxes()` is currently only called on modal open — Task 1 MUST also call it in `LoadSettings()`
- Organization API endpoints: inline in `Program.cs` under `orgGroup`, NOT in a separate Endpoints file
- DB table for org contact fields: `Packages` (SolidCP), NOT a custom `Organizations` table
- Migration number: 093 is next (last was `092_AddMailboxGeneralTabTranslations.sql`)
- Bootstrap accordion classes (not custom CSS) — matches existing MailboxGeneralTab pattern
