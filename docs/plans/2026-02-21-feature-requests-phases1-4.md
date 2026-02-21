# FuseCP Feature Requests Implementation Plan (Phases 1-4)

> **For Claude:** REQUIRED: Use /subagent-dev (if subagents available) or /execute-plan to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Implement 4 phases of FuseCP feature requests: Mailbox General Tab redesign with AD contact fields, Organization contact data enrichment with AD thumbnail photo, Mail Flow Tab redesign with searchable forwarding picker, and Operations Logging middleware fix.

**Architecture:** Blazor Server (.NET 8) portal with Minimal APIs backend. AD/Exchange providers via WinRM. All DB changes must be ADDITIVE for SolidCP in-place upgrade compatibility. Consistent accordion design system across all UI phases.

**Tech Stack:** C# .NET 8, Blazor Server, Minimal APIs, SQL Server, WinRM (Exchange/AD providers), Dapper ORM

---

## Design System Reference

All UI phases use the same accordion design from the approved playground (`C:/claude/fusecp-enterprise/tmp/mailbox-general-tab-playground.html`):

- Dark theme (`#0f1419` background), card-based layout (`#161b22`)
- CSS classes: `section-card`, `section-header`, `section-body`, `section-body-inner`
- 32px icons, 90-degree chevron rotation, `max-height` 350ms transition animation
- Color-coded section badges: blue / green / orange / purple
- Font stack: DM Sans (body) + JetBrains Mono (code/values)
- All accordion sections default open; toggle independently

---

## Phase 4: Operations Logging Fix (FR #48) -- COMPLETED

> Quick win — single file change, fully independent. Fix first before any UI work.
>
> **Status:** DONE. The try/catch/finally pattern with `statusCode = 500` in catch block is already in `OperationsLoggingMiddleware.cs:54-63`.

---

### Task 1: Fix OperationsLoggingMiddleware Status Code Capture

**Agent:** bug-hunter

**Files:**
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.EnterpriseServer\Middleware\OperationsLoggingMiddleware.cs:54-98`

**Context:**
The current `try/finally` pattern reads `context.Response.StatusCode` inside the `finally` block. At that point the status code is still `200` because ASP.NET's exception handler middleware hasn't yet set it to `500`. The fix is to introduce a catch block that sets a local `statusCode` variable to `500` when an exception is caught, then rethrows so the exception handler can still process it normally.

Current pattern (lines 54-98):
```csharp
try
{
    await _next(context);
}
finally
{
    var statusCode = context.Response.StatusCode;
    // logs statusCode — always 200 even on exceptions
}
```

Target pattern:
```csharp
var statusCode = context.Response.StatusCode; // default
try
{
    await _next(context);
    statusCode = context.Response.StatusCode;
}
catch (Exception)
{
    statusCode = 500;
    throw; // rethrow so exception handler still fires
}
finally
{
    // log using captured statusCode
}
```

- [x] **Step 1: Read and understand current middleware**
  Read `OperationsLoggingMiddleware.cs` lines 1-130 in full to understand the complete try/finally structure, what variables are captured, and how logging is performed in the finally block.

- [x] **Step 2: Apply the catch-and-rethrow fix**
  Refactor the try/finally into try/catch(rethrow)/finally:
  - Declare `int statusCode` before the try block, initialized to `context.Response.StatusCode` (default 200).
  - In the try body: after `await _next(context)`, assign `statusCode = context.Response.StatusCode`.
  - Add `catch (Exception) { statusCode = 500; throw; }` between try and finally.
  - In the finally block: use the local `statusCode` variable (not `context.Response.StatusCode`).
  - Preserve all existing logging logic unchanged — only the status code source changes.

- [x] **Step 3: Verify no other status code reads in the file**
  Grep `OperationsLoggingMiddleware.cs` for `StatusCode` and confirm the only remaining read is in the finally block using the local variable.

- [x] **Step 4: Build and smoke test**
  ```bash
  cd /c/claude/fusecp-enterprise
  dotnet build src/FuseCP.EnterpriseServer/FuseCP.EnterpriseServer.csproj --no-restore 2>&1 | tail -5
  ```
  Trigger a 500 response (e.g., call a non-existent endpoint) and verify the operations log entry shows `StatusCode: 500`.

- [x] **Step 5: Commit**
  ```bash
  git add src/FuseCP.EnterpriseServer/Middleware/OperationsLoggingMiddleware.cs
  git commit -m "fix(middleware): capture 500 status code before exception handler resets it

  The try/finally pattern read context.Response.StatusCode in finally, which
  is still 200 at that point because ASP.NET exception handler runs after.
  Add catch block to capture 500 in a local variable and rethrow.

  Fixes FR #48

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

## Phase 1: Mailbox General Tab Redesign (FR #44, #42, #38) -- COMPLETED

> Establish the accordion design system in Blazor. Extends existing mailbox tab with full AD contact fields using the IAdApiClient bridge already in use for password resets.
>
> **Status:** DONE (2026-02-21). Implemented via PR #107 (Gemini: DTO + accordion layout + migration 092) + PR #108 (Claude: wired AD contact fields load/save via AdApiClient). Deployed to Portal.

---

### Task 2: Extend MailboxGeneralSettings DTO with AD Contact Fields

**Agent:** modular-builder

**Files:**
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.Providers.Exchange\Models\MailboxSettings.cs`
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.EnterpriseServer\Endpoints\ExchangeEndpoints.cs:656-714`

**Context:**
`MailboxGeneralSettings` currently has 7 properties (DisplayName, FirstName, LastName, Initials, Alias, HideFromAddressLists, and one more). The AD contact fields live in `AdUser.cs` and are already handled by `AdProvider.UpdateUserAsync()`. The goal here is to define a shared `AdContactFields` record/class that can be embedded in the Exchange DTO and also used standalone. The existing GET/PUT `/mailboxes/{identity}/general` endpoints will be extended to accept and return the new fields. The endpoints should call `IAdApiClient` to fetch/save the AD portion.

- [x] **Step 1: Read current MailboxSettings.cs and AdUser.cs**
  Read both files in full to understand existing property naming conventions, data annotations, and nullable patterns used in the codebase.

- [x] **Step 2: Define AdContactFields record**
  In `MailboxSettings.cs` (or a new `AdContactFields.cs` in the same Models folder), add:
  ```csharp
  public record AdContactFields
  {
      // Organization section
      public string? JobTitle { get; init; }
      public string? Department { get; init; }
      public string? Company { get; init; }
      public string? Manager { get; init; }

      // Contact Numbers section
      public string? TelephoneNumber { get; init; }
      public string? Mobile { get; init; }
      public string? Fax { get; init; }
      public string? HomePhone { get; init; }
      public string? Pager { get; init; }
      public string? IpPhone { get; init; }

      // Address section
      public string? StreetAddress { get; init; }
      public string? City { get; init; }
      public string? State { get; init; }
      public string? PostalCode { get; init; }
      public string? Country { get; init; }

      // Account Information section
      public string? WebPage { get; init; }
      public string? Notes { get; init; }
  }
  ```

- [x] **Step 3: Embed AdContactFields in MailboxGeneralSettings**
  Add `public AdContactFields? AdContact { get; init; }` to `MailboxGeneralSettings`. This keeps the existing Exchange fields intact and adds the AD block as an optional nested object.

- [x] **Step 4: Extend GET /mailboxes/{identity}/general endpoint**
  In `ExchangeEndpoints.cs`, after the endpoint fetches the Exchange general settings, add a parallel call to `IAdApiClient.GetUserAsync(identity)` and map the result to `AdContactFields`. Return the combined DTO.

- [x] **Step 5: Extend PUT /mailboxes/{identity}/general endpoint**
  When `AdContact` is present in the request body, extract it and call `IAdApiClient.UpdateUserAsync(identity, adUserUpdate)` mapping `AdContactFields` → `AdUser` update model. Execute Exchange and AD saves in parallel (Task.WhenAll pattern) for performance.

- [x] **Step 6: Build and verify no regressions**
  ```bash
  cd /c/claude/fusecp-enterprise
  dotnet build --no-restore 2>&1 | tail -10
  ```

- [x] **Step 7: Commit**
  ```bash
  git add src/FuseCP.Providers.Exchange/Models/MailboxSettings.cs \
          src/FuseCP.EnterpriseServer/Endpoints/ExchangeEndpoints.cs
  git commit -m "feat(exchange): extend MailboxGeneralSettings with AD contact fields

  Add AdContactFields record (19 fields: org, contact numbers, address,
  account info). Embed in MailboxGeneralSettings. Extend GET/PUT general
  endpoints to fetch/save AD fields via IAdApiClient in parallel.

  Part of FR #44 #42 #38

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

### Task 3: Redesign MailboxGeneralTab.razor with Accordion Sections

**Agent:** component-designer

**Files:**
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.Portal\Components\Pages\Exchange\Tabs\MailboxGeneralTab.razor`
- Reference (read-only): `C:/claude/fusecp-enterprise/tmp/mailbox-general-tab-playground.html`

**Context:**
Current tab has 6 fields in a flat layout. Target: 5 accordion sections matching the approved playground design. The tab already uses `IAdApiClient` for password resets (bridge pattern exists). The new AD contact fields come from the extended API response (Task 2).

The 5 accordion sections:
1. **Mailbox Settings** (blue badge) — DisplayName, FirstName, LastName, Initials, Alias, HideFromAddressLists
2. **Organization** (green badge) — JobTitle, Department, Company, Manager
3. **Contact Numbers** (orange badge) — TelephoneNumber, Mobile, Fax, HomePhone, Pager, IpPhone
4. **Address** (purple badge) — StreetAddress, City, State, PostalCode, Country
5. **Account Information** (blue badge) — WebPage, Notes, plus read-only: database, server, username

- [x] **Step 1: Read playground and current tab**
  Read the full playground HTML to extract exact CSS classes, color variables, animation definitions, and HTML structure. Read the current `MailboxGeneralTab.razor` in full to understand existing bindings, state variables, and service calls.

- [x] **Step 2: Add accordion CSS to the tab's `<style>` block**
  Extract and adapt the complete CSS from the playground:
  - Variables: `--bg-primary: #0f1419`, `--bg-card: #161b22`, `--border: #21262d`, `--text-primary: #e6edf3`, `--text-secondary: #7d8590`, `--accent-blue: #58a6ff`, `--accent-green: #3fb950`, `--accent-orange: #d29922`, `--accent-purple: #bc8cff`
  - `.section-card` — card container with border-radius, border, background
  - `.section-header` — flexbox row, cursor pointer, padding, hover state
  - `.section-body` — overflow hidden, max-height transition (0 → 350px) at 350ms ease
  - `.section-body-inner` — inner padding
  - `.badge` variants: `.badge-blue`, `.badge-green`, `.badge-orange`, `.badge-purple`
  - `.chevron` — `transition: transform 0.3s ease`, `.open .chevron { transform: rotate(90deg) }`
  - `.field-row` — two-column grid layout for label/input pairs
  - `.field-label`, `.field-input` — label styling with JetBrains Mono for read-only values

- [x] **Step 3: Add C# accordion toggle state**
  In the `@code` block, add:
  ```csharp
  private bool _mailboxOpen = true;
  private bool _orgOpen = true;
  private bool _contactOpen = true;
  private bool _addressOpen = true;
  private bool _accountOpen = true;

  private void ToggleSection(ref bool state) => state = !state;
  ```

- [x] **Step 4: Add AdContactFields binding properties**
  Add C# properties bound to the `AdContact` portion of the loaded `MailboxGeneralSettings`. On save, the updated `AdContact` block is included in the PUT request body.

- [x] **Step 5: Rebuild razor markup with 5 accordion sections**
  Replace the flat field list with the accordion structure. Each section:
  ```razor
  <div class="section-card">
      <div class="section-header @(_mailboxOpen ? "open" : "")"
           @onclick="() => _mailboxOpen = !_mailboxOpen">
          <span class="section-icon">📋</span>
          <span class="section-title">Mailbox Settings</span>
          <span class="badge badge-blue">Core</span>
          <span class="chevron">›</span>
      </div>
      <div class="section-body" style="max-height: @(_mailboxOpen ? "350px" : "0")">
          <div class="section-body-inner">
              <!-- existing fields unchanged -->
          </div>
      </div>
  </div>
  ```
  Apply same pattern for Organization, Contact Numbers, Address, Account Information sections. Account Information section shows WebPage and Notes as editable, plus read-only database/server/username fields styled with JetBrains Mono.

- [x] **Step 6: Wire save button to include AdContact fields**
  Ensure the existing save handler serializes the full DTO including the `AdContact` block when calling the PUT endpoint.

- [x] **Step 7: Build and verify**
  ```bash
  cd /c/claude/fusecp-enterprise
  dotnet build src/FuseCP.Portal/FuseCP.Portal.csproj --no-restore 2>&1 | tail -10
  ```

- [x] **Step 8: Commit**
  ```bash
  git add src/FuseCP.Portal/Components/Pages/Exchange/Tabs/MailboxGeneralTab.razor
  git commit -m "feat(portal): redesign MailboxGeneralTab with 5 accordion sections

  Replace flat layout with accordion: Mailbox Settings, Organization,
  Contact Numbers, Address, Account Information. Wire AD contact fields
  from extended API response. Adopt dark accordion design system.

  FR #44 #42 #38

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

### Task 4: Test Phase 1 End-to-End

**Agent:** test-coverage

**Files:**
- Test: `C:\claude\fusecp-enterprise\tests\FuseCP.EnterpriseServer.Tests\Exchange\MailboxGeneralTests.cs`

**Context:**
Verify the extended DTO round-trips correctly. Validate that AD contact fields are fetched on GET and saved on PUT. Confirm accordion UI renders all 5 sections and toggle state is independent.

- [x] **Step 1: Write API unit tests for the extended DTO**
  Add tests to `MailboxGeneralTests.cs` (or create it if not present):
  - `GET /mailboxes/{identity}/general` returns `AdContact` block when AD user exists
  - `PUT /mailboxes/{identity}/general` with `AdContact` data calls AD update endpoint
  - `PUT` without `AdContact` field does not error (null is valid)
  - Status 200 on success, 404 when mailbox not found

- [x] **Step 2: Write Blazor component render tests**
  If the project has Blazor unit tests (bUnit or equivalent), verify:
  - All 5 accordion sections render with correct headings and badges
  - Toggle state: clicking a section header collapses it (max-height → 0)
  - Save button visible and enabled when form is dirty

- [x] **Step 3: Run tests and confirm pass**
  ```bash
  cd /c/claude/fusecp-enterprise
  dotnet test tests/ --filter "MailboxGeneral" 2>&1 | tail -20
  ```

- [x] **Step 4: Commit tests**
  ```bash
  git add tests/
  git commit -m "test(exchange): add MailboxGeneral accordion and AD contact field tests

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

## Phase 3: Mail Flow Tab Redesign (FR #33) -- COMPLETED

> Reuses the accordion design system established in Phase 1. Key change: replace plain text forwarding input with a searchable mailbox picker. Infrastructure (LoadOrgMailboxes, FilteredOrgMailboxes) already exists but is not wired to the forwarding field.

---

### Task 5: Redesign MailboxMailFlowTab.razor with Accordion + Searchable Forwarding Picker

**Agent:** component-designer

**Files:**
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.Portal\Components\Pages\Exchange\Tabs\MailboxMailFlowTab.razor`
- Reference (read-only): `C:/claude/fusecp-enterprise/tmp/group-c-mailflow-playground.html`

**Context:**
Current tab (525 lines):
- Lines 43-45: Plain `TextInput` for forwarding address — the problem
- Lines 286-300: `FilteredOrgMailboxes` computed property with search/filter logic
- Lines 340-364: `LoadOrgMailboxes()` fetches all org mailboxes
- Lines 436-472: Searchable dropdown with filtered results exists for Add Sender modal

The forwarding picker should reuse the same search/dropdown pattern already used for Add Sender. The accordion wrapping (4 sections) uses the same design system CSS from Phase 1 (already in the portal's shared stylesheet or added here if isolated).

4 accordion sections:
1. **Forwarding** (blue badge) — Searchable picker to select destination mailbox, "Also keep a copy in this mailbox" checkbox
2. **Accept Messages From** (green badge) — Existing add/remove list UI wrapped in accordion
3. **Reject Messages From** (orange badge) — Existing add/remove list UI wrapped in accordion
4. **Message Size Limits** (purple badge) — Max send/receive KB fields wrapped in accordion

- [x] **Step 1: Read current MailboxMailFlowTab.razor in full**
  Read all 525 lines. Map: forwarding field location (43-45), search infrastructure (286-300, 340-364), and the Add Sender modal search dropdown (436-472). Understand all existing `@bind`, `@onclick`, and state variables.

- [x] **Step 2: Read the mail flow playground**
  Read `group-c-mailflow-playground.html` to extract the forwarding picker design: search input, dropdown list, selected-mailbox display chip, clear button.

- [x] **Step 3: Add accordion CSS if not already present**
  Check if the accordion CSS from Phase 1 is in a shared stylesheet. If not, add the same CSS block (variables, `.section-card`, `.section-header`, `.section-body`, `.section-body-inner`, badges, chevron) to this tab's `<style>` section.

- [x] **Step 4: Add forwarding picker state variables**
  In `@code`, add:
  ```csharp
  private bool _forwardingOpen = true;
  private bool _acceptOpen = true;
  private bool _rejectOpen = true;
  private bool _sizeLimitsOpen = true;

  // Forwarding picker search
  private string _forwardingSearch = "";
  private bool _showForwardingDropdown = false;

  private IEnumerable<MailboxSummary> FilteredForwardingMailboxes =>
      string.IsNullOrWhiteSpace(_forwardingSearch)
          ? OrgMailboxes.Take(10)
          : OrgMailboxes.Where(m =>
              m.DisplayName.Contains(_forwardingSearch, StringComparison.OrdinalIgnoreCase) ||
              m.Email.Contains(_forwardingSearch, StringComparison.OrdinalIgnoreCase))
            .Take(20);
  ```
  (`OrgMailboxes` is already populated by `LoadOrgMailboxes()` at lines 340-364.)

- [x] **Step 5: Replace forwarding plain text input with searchable picker**
  Remove lines 43-45 (`TextInput` for forwarding). Replace with:
  ```razor
  @if (!string.IsNullOrEmpty(Settings.ForwardingAddress))
  {
      <!-- Selected chip: show display name + email, with X clear button -->
      <div class="selected-chip">
          <span>@GetForwardingDisplayName()</span>
          <button @onclick="ClearForwarding">×</button>
      </div>
  }
  else
  {
      <!-- Search input -->
      <input type="text"
             placeholder="Search mailboxes..."
             @bind="_forwardingSearch"
             @bind:event="oninput"
             @onfocus="() => _showForwardingDropdown = true"
             @onblur="() => Task.Delay(150).ContinueWith(_ => { _showForwardingDropdown = false; InvokeAsync(StateHasChanged); })"
             class="field-input" />
      @if (_showForwardingDropdown && FilteredForwardingMailboxes.Any())
      {
          <div class="dropdown-list">
              @foreach (var mailbox in FilteredForwardingMailboxes)
              {
                  <div class="dropdown-item" @onmousedown="() => SelectForwardingMailbox(mailbox)">
                      <span class="item-name">@mailbox.DisplayName</span>
                      <span class="item-email">@mailbox.Email</span>
                  </div>
              }
          </div>
      }
  }
  ```
  Add `SelectForwardingMailbox(MailboxSummary m)` and `ClearForwarding()` C# methods.

- [x] **Step 6: Wrap all 4 sections in accordion containers**
  Wrap Forwarding, Accept Messages From, Reject Messages From, and Message Size Limits in the standard accordion structure (section-card / section-header / section-body). Preserve ALL existing internal logic — only wrap with accordion chrome.

- [x] **Step 7: Build and verify**
  ```bash
  cd /c/claude/fusecp-enterprise
  dotnet build src/FuseCP.Portal/FuseCP.Portal.csproj --no-restore 2>&1 | tail -10
  ```

- [x] **Step 8: Commit**
  ```bash
  git add src/FuseCP.Portal/Components/Pages/Exchange/Tabs/MailboxMailFlowTab.razor
  git commit -m "feat(portal): redesign MailboxMailFlowTab with accordion and forwarding picker

  Replace plain text forwarding input with searchable mailbox picker using
  existing LoadOrgMailboxes infrastructure. Wrap all 4 mail flow sections
  (Forwarding, Accept, Reject, Size Limits) in accordion containers.

  FR #33

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

## Phase 2: Organization Contact Data + AD Thumbnail Photo (FR #36, #37) -- COMPLETED

> Most complex phase — includes DB schema changes (highest risk). All schema changes ADDITIVE only.

---

### Task 6: Add Contact Columns to Organizations Table (Schema Migration)

**Agent:** database-architect

**Files:**
- Create: `C:\claude\fusecp-enterprise\src\FuseCP.Database\Migrations\V0XX__AddOrganizationContactFields.sql`
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.Database\Models\Organization.cs` (or wherever the EF/Dapper model is defined)

**CRITICAL CONSTRAINT:** ALL changes are ADDITIVE only. Never drop, rename, or alter existing columns. The `Organizations` table is a SolidCP-compatible table — only add new nullable columns.

- [x] **Step 1: Inspect current Organizations schema**
  Run:
  ```bash
  sqlcmd -S "(local)\SQLEXPRESS" -d FuseCPLab -Q "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'SoapPackages' OR TABLE_NAME = 'Organizations' ORDER BY TABLE_NAME, ORDINAL_POSITION"
  ```
  Identify the exact Organizations table name and all existing columns. Confirm which columns are safe to add alongside.

- [x] **Step 2: Write additive migration script**
  Create `V0XX__AddOrganizationContactFields.sql` (replace XX with next migration number):
  ```sql
  -- ADDITIVE ONLY: New contact fields for FR #36
  -- All columns nullable, no existing columns modified

  IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                 WHERE TABLE_NAME = 'Organizations' AND COLUMN_NAME = 'CompanyLegalName')
  BEGIN
      ALTER TABLE [dbo].[Organizations]
          ADD [CompanyLegalName]  NVARCHAR(255)  NULL,
              [TaxId]             NVARCHAR(100)  NULL,
              [Phone]             NVARCHAR(50)   NULL,
              [Email]             NVARCHAR(255)  NULL,
              [Address]           NVARCHAR(500)  NULL,
              [City]              NVARCHAR(100)  NULL,
              [State]             NVARCHAR(100)  NULL,
              [PostalCode]        NVARCHAR(20)   NULL,
              [Country]           NVARCHAR(100)  NULL,
              [Website]           NVARCHAR(500)  NULL;
  END
  GO
  ```
  Wrap each `ALTER TABLE` in an existence check so the script is idempotent.

- [x] **Step 3: Update the Organization C# model**
  Add corresponding nullable properties to the `Organization` model class:
  ```csharp
  public string? CompanyLegalName { get; set; }
  public string? TaxId { get; set; }
  public string? Phone { get; set; }
  public string? Email { get; set; }
  public string? Address { get; set; }
  public string? City { get; set; }
  public string? State { get; set; }
  public string? PostalCode { get; set; }
  public string? Country { get; set; }
  public string? Website { get; set; }
  ```

- [x] **Step 4: Apply migration to local database**
  ```bash
  sqlcmd -S "(local)\SQLEXPRESS" -d FuseCPLab -i src/FuseCP.Database/Migrations/V0XX__AddOrganizationContactFields.sql
  ```
  Verify columns exist:
  ```bash
  sqlcmd -S "(local)\SQLEXPRESS" -d FuseCPLab -Q "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Organizations' AND COLUMN_NAME IN ('CompanyLegalName','TaxId','Phone','Email','Country')"
  ```

- [x] **Step 5: Commit**
  ```bash
  git add src/FuseCP.Database/Migrations/ \
          src/FuseCP.Database/Models/
  git commit -m "feat(db): add 10 contact fields to Organizations table (ADDITIVE only)

  New nullable columns: CompanyLegalName, TaxId, Phone, Email, Address,
  City, State, PostalCode, Country, Website. Migration is idempotent.
  No existing columns modified.

  FR #36

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

### Task 7: Add Organization Contact API Endpoints

**Agent:** modular-builder

**Files:**
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.EnterpriseServer\Endpoints\OrganizationsEndpoints.cs`
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.EnterpriseServer\Services\OrganizationsRepository.cs` (or equivalent data access layer)

**Context:**
Add two new endpoints following existing patterns in `OrganizationsEndpoints.cs`:
- `GET /organizations/{id}/contact` — returns the 10 new contact fields for an org
- `PUT /organizations/{id}/contact` — updates those fields

These are separate from the existing org CRUD endpoints to keep the changes additive and isolated.

- [x] **Step 1: Read OrganizationsEndpoints.cs and OrganizationsRepository.cs in full**
  Understand existing endpoint patterns: how auth is enforced, how parameters are validated, how the repository is called, and what response shapes look like.

- [x] **Step 2: Define OrganizationContactRequest/Response DTOs**
  In the endpoints file or a shared DTOs file:
  ```csharp
  public record OrganizationContactRequest(
      string? CompanyLegalName,
      string? TaxId,
      string? Phone,
      string? Email,
      string? Address,
      string? City,
      string? State,
      string? PostalCode,
      string? Country,
      string? Website
  );

  public record OrganizationContactResponse(
      string? CompanyLegalName,
      string? TaxId,
      string? Phone,
      string? Email,
      string? Address,
      string? City,
      string? State,
      string? PostalCode,
      string? Country,
      string? Website
  );
  ```

- [x] **Step 3: Add GetOrganizationContact repository method**
  In `OrganizationsRepository.cs`, add:
  ```csharp
  public async Task<OrganizationContactResponse?> GetContactAsync(int organizationId)
  {
      const string sql = @"SELECT CompanyLegalName, TaxId, Phone, Email, Address,
                                  City, State, PostalCode, Country, Website
                           FROM Organizations WHERE ItemID = @id";
      return await _connection.QueryFirstOrDefaultAsync<OrganizationContactResponse>(sql, new { id = organizationId });
  }
  ```

- [x] **Step 4: Add UpdateOrganizationContact repository method**
  ```csharp
  public async Task UpdateContactAsync(int organizationId, OrganizationContactRequest req)
  {
      const string sql = @"UPDATE Organizations SET
          CompanyLegalName = @CompanyLegalName, TaxId = @TaxId,
          Phone = @Phone, Email = @Email, Address = @Address,
          City = @City, State = @State, PostalCode = @PostalCode,
          Country = @Country, Website = @Website
          WHERE ItemID = @id";
      await _connection.ExecuteAsync(sql, new { req.CompanyLegalName, req.TaxId, req.Phone,
          req.Email, req.Address, req.City, req.State, req.PostalCode, req.Country, req.Website,
          id = organizationId });
  }
  ```

- [x] **Step 5: Register the two new endpoints**
  In `OrganizationsEndpoints.cs`, add the GET and PUT routes following existing auth and validation patterns. Return 404 if org not found, 200 on success.

- [x] **Step 6: Build and smoke test**
  ```bash
  cd /c/claude/fusecp-enterprise
  dotnet build --no-restore 2>&1 | tail -10
  # Test with curl after starting the server:
  # curl -sk -H "X-Api-Key: fusecp-admin-key-2026" "http://localhost:5010/api/organizations/1/contact"
  ```

- [x] **Step 7: Commit**
  ```bash
  git add src/FuseCP.EnterpriseServer/Endpoints/OrganizationsEndpoints.cs \
          src/FuseCP.EnterpriseServer/Services/OrganizationsRepository.cs
  git commit -m "feat(api): add GET/PUT /organizations/{id}/contact endpoints

  New endpoints for the 10 contact fields added in the DB migration.
  FR #36

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

### Task 8: Add Contact Fields Section to OrganizationEdit.razor

**Agent:** component-designer

**Files:**
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.Portal\Components\Pages\Admin\OrganizationEdit.razor`
- Reference (read-only): `C:/claude/fusecp-enterprise/tmp/group-b-playground.html`

**Context:**
`OrganizationEdit.razor` manages the editing form for an organization. A new "Contact Information" accordion section needs to be added (same design system as Phase 1) with the 10 new contact fields. The section loads data from the new `GET /organizations/{id}/contact` endpoint and saves via `PUT`.

- [x] **Step 1: Read OrganizationEdit.razor in full**
  Understand the current form layout, how existing fields are bound, how the save button works, and whether accordion CSS is already loaded (from Phase 1) or needs to be added.

- [x] **Step 2: Read group-b playground**
  Extract the org contact section visual design: field layout, section icon, badge color, field labels.

- [x] **Step 3: Add IOrganizationsApiClient contact methods if not present**
  If `IOrganizationsApiClient` does not yet have `GetContactAsync` / `UpdateContactAsync`, add interface declarations and implementations calling the new endpoints.

- [x] **Step 4: Add contact state variables in @code**
  ```csharp
  private OrganizationContactResponse? _contact;
  private bool _contactSectionOpen = true;

  protected override async Task OnInitializedAsync()
  {
      // ... existing init ...
      _contact = await OrganizationsApiClient.GetContactAsync(OrganizationId);
  }
  ```

- [x] **Step 5: Add Contact Information accordion section to form**
  Below the existing form sections, add:
  ```razor
  <div class="section-card">
      <div class="section-header @(_contactSectionOpen ? "open" : "")"
           @onclick="() => _contactSectionOpen = !_contactSectionOpen">
          <span class="section-icon">📞</span>
          <span class="section-title">Contact Information</span>
          <span class="badge badge-green">FR #36</span>
          <span class="chevron">›</span>
      </div>
      <div class="section-body" style="max-height: @(_contactSectionOpen ? "350px" : "0")">
          <div class="section-body-inner">
              <div class="field-row">
                  <label class="field-label">Legal Name</label>
                  <input class="field-input" @bind="_contact!.CompanyLegalName" />
              </div>
              <!-- ... remaining 9 fields ... -->
          </div>
      </div>
  </div>
  ```
  Bind all 10 fields from `_contact`. Include null guard since `_contact` may be null while loading.

- [x] **Step 6: Wire save to include contact update**
  In the save handler, after the existing org save call, also call:
  ```csharp
  if (_contact != null)
      await OrganizationsApiClient.UpdateContactAsync(OrganizationId,
          new OrganizationContactRequest(_contact.CompanyLegalName, /* ... */));
  ```

- [x] **Step 7: Build and verify**
  ```bash
  dotnet build src/FuseCP.Portal/FuseCP.Portal.csproj --no-restore 2>&1 | tail -10
  ```

- [x] **Step 8: Commit**
  ```bash
  git add src/FuseCP.Portal/Components/Pages/Admin/OrganizationEdit.razor
  git commit -m "feat(portal): add Contact Information section to OrganizationEdit

  New accordion section with 10 contact fields (CompanyLegalName, TaxId,
  Phone, Email, Address, City, State, PostalCode, Country, Website).
  Loads from and saves to new /organizations/{id}/contact endpoints.

  FR #36

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

### Task 9: Add thumbnailPhoto Read/Write to AD Provider

**Agent:** modular-builder

**Files:**
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.Providers.AD\AdProvider.cs`
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.Providers.AD\Models\AdUser.cs`
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.EnterpriseServer\Endpoints\ADEndpoints.cs`

**Context:**
AD stores `thumbnailPhoto` as a byte array (JPEG). Max size enforced by AD is ~100KB. The provider needs two new operations: read the thumbnail (return as base64 string) and write it (accept base64, validate size, write byte array to AD). These will be exposed as new API endpoints: `GET /ad/users/{identity}/photo` and `PUT /ad/users/{identity}/photo`.

- [x] **Step 1: Read AdProvider.cs lines 71-150 and AdUser.cs**
  Understand `UpdateUserAsync()` and how DirectoryEntry attribute writes work. Check whether `GetUserAsync()` already reads `thumbnailPhoto`.

- [x] **Step 2: Add ThumbnailPhotoBase64 to AdUser**
  ```csharp
  public string? ThumbnailPhotoBase64 { get; set; }
  ```
  Optional — `null` means no photo or not loaded.

- [x] **Step 3: Add GetUserPhotoAsync to AdProvider**
  ```csharp
  public async Task<string?> GetUserPhotoAsync(string identity)
  {
      using var entry = GetDirectoryEntry(identity);
      var photo = entry.Properties["thumbnailPhoto"].Value as byte[];
      if (photo == null || photo.Length == 0) return null;
      return Convert.ToBase64String(photo);
  }
  ```

- [x] **Step 4: Add SetUserPhotoAsync to AdProvider**
  ```csharp
  public async Task SetUserPhotoAsync(string identity, string? base64Photo)
  {
      using var entry = GetDirectoryEntry(identity);
      if (string.IsNullOrEmpty(base64Photo))
      {
          entry.Properties["thumbnailPhoto"].Clear();
      }
      else
      {
          var bytes = Convert.FromBase64String(base64Photo);
          if (bytes.Length > 100 * 1024)
              throw new ArgumentException("Photo exceeds 100KB AD limit");
          entry.Properties["thumbnailPhoto"].Value = bytes;
      }
      entry.CommitChanges();
  }
  ```

- [x] **Step 5: Add GET /ad/users/{identity}/photo and PUT endpoints**
  In `ADEndpoints.cs`, add:
  - `GET /ad/users/{identity}/photo` → returns `{ "photoBase64": "..." }` or 404 if no photo
  - `PUT /ad/users/{identity}/photo` → accepts `{ "photoBase64": "..." }` (null = clear photo)

- [x] **Step 6: Build and verify**
  ```bash
  dotnet build --no-restore 2>&1 | tail -10
  ```

- [x] **Step 7: Commit**
  ```bash
  git add src/FuseCP.Providers.AD/AdProvider.cs \
          src/FuseCP.Providers.AD/Models/AdUser.cs \
          src/FuseCP.EnterpriseServer/Endpoints/ADEndpoints.cs
  git commit -m "feat(ad): add thumbnailPhoto read/write to AD provider

  New GetUserPhotoAsync / SetUserPhotoAsync methods. 100KB size limit
  enforced. Exposed as GET/PUT /ad/users/{identity}/photo endpoints.

  FR #37

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

### Task 10: Add Circular Avatar to MailboxGeneralTab.razor Header

**Agent:** component-designer

**Files:**
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.Portal\Components\Pages\Exchange\Tabs\MailboxGeneralTab.razor`
- Reference (read-only): `C:/claude/fusecp-enterprise/tmp/group-b-playground.html`

**Context:**
The mailbox tab header (above the accordion sections added in Task 3) should show a circular user avatar. If a `thumbnailPhoto` exists in AD, display it. Otherwise, show initials-based fallback (e.g., first letter of FirstName + first letter of LastName on a colored circle). Include an Upload Photo button and a Clear Photo button below the avatar. Photo uploads go to the `PUT /ad/users/{identity}/photo` endpoint.

- [x] **Step 1: Read current MailboxGeneralTab.razor (as modified in Task 3)**
  Understand the header area layout and where the avatar should be positioned (above the first accordion section).

- [x] **Step 2: Read group-b playground for avatar design**
  Extract: circle dimensions (96px recommended), border, shadow, initials font size, upload button style, accepted file types, size validation client-side.

- [x] **Step 3: Add photo state and loading**
  ```csharp
  private string? _photoBase64;
  private bool _photoLoaded = false;

  // Called during OnInitializedAsync / OnParametersSetAsync
  private async Task LoadPhotoAsync()
  {
      _photoBase64 = await AdApiClient.GetUserPhotoAsync(Identity);
      _photoLoaded = true;
  }

  private string AvatarInitials =>
      $"{(Settings?.FirstName?.FirstOrDefault())}{(Settings?.LastName?.FirstOrDefault())}".ToUpper();
  ```

- [x] **Step 4: Add avatar CSS**
  ```css
  .avatar-container { display: flex; flex-direction: column; align-items: center; gap: 12px; margin-bottom: 24px; }
  .avatar-circle { width: 96px; height: 96px; border-radius: 50%; border: 3px solid var(--border); overflow: hidden; background: var(--bg-card); display: flex; align-items: center; justify-content: center; }
  .avatar-img { width: 100%; height: 100%; object-fit: cover; }
  .avatar-initials { font-size: 32px; font-weight: 700; color: var(--accent-blue); font-family: 'DM Sans', sans-serif; }
  .avatar-actions { display: flex; gap: 8px; }
  ```

- [x] **Step 5: Add avatar markup above first accordion section**
  ```razor
  <div class="avatar-container">
      <div class="avatar-circle">
          @if (!string.IsNullOrEmpty(_photoBase64))
          {
              <img class="avatar-img" src="data:image/jpeg;base64,@_photoBase64" alt="User photo" />
          }
          else
          {
              <span class="avatar-initials">@AvatarInitials</span>
          }
      </div>
      <div class="avatar-actions">
          <label class="btn btn-secondary" style="cursor: pointer;">
              Upload Photo
              <InputFile OnChange="HandlePhotoUpload" accept=".jpg,.jpeg,.png" style="display:none" />
          </label>
          @if (!string.IsNullOrEmpty(_photoBase64))
          {
              <button class="btn btn-danger" @onclick="ClearPhoto">Clear</button>
          }
      </div>
  </div>
  ```

- [x] **Step 6: Add HandlePhotoUpload and ClearPhoto handlers**
  ```csharp
  private async Task HandlePhotoUpload(InputFileChangeEventArgs e)
  {
      var file = e.File;
      if (file.Size > 100 * 1024) { /* show error: photo too large */ return; }
      using var stream = file.OpenReadStream(maxAllowedSize: 100 * 1024);
      var bytes = new byte[file.Size];
      await stream.ReadExactlyAsync(bytes);
      _photoBase64 = Convert.ToBase64String(bytes);
      await AdApiClient.SetUserPhotoAsync(Identity, _photoBase64);
  }

  private async Task ClearPhoto()
  {
      _photoBase64 = null;
      await AdApiClient.SetUserPhotoAsync(Identity, null);
  }
  ```

- [x] **Step 7: Build and verify**
  ```bash
  dotnet build src/FuseCP.Portal/FuseCP.Portal.csproj --no-restore 2>&1 | tail -10
  ```

- [x] **Step 8: Commit**
  ```bash
  git add src/FuseCP.Portal/Components/Pages/Exchange/Tabs/MailboxGeneralTab.razor
  git commit -m "feat(portal): add circular avatar with photo upload to MailboxGeneralTab

  Circular avatar in tab header: shows thumbnailPhoto from AD or initials
  fallback. Upload (100KB max) and Clear buttons. Uses PUT /ad/users/photo.

  FR #37

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

### Task 11: Test Phase 2 End-to-End

**Agent:** test-coverage

**Files:**
- Test: `C:\claude\fusecp-enterprise\tests\FuseCP.EnterpriseServer.Tests\Organizations\OrganizationContactTests.cs`
- Test: `C:\claude\fusecp-enterprise\tests\FuseCP.EnterpriseServer.Tests\AD\UserPhotoTests.cs`

- [x] **Step 1: Write organization contact API tests**
  - `GET /organizations/{id}/contact` returns all 10 nullable fields
  - `PUT /organizations/{id}/contact` updates fields and round-trips on GET
  - `GET` for non-existent org returns 404
  - All 10 fields accept null (nullable columns)

- [x] **Step 2: Write AD photo API tests**
  - `GET /ad/users/{identity}/photo` returns null for user with no photo
  - `PUT /ad/users/{identity}/photo` with valid base64 succeeds
  - `PUT` with base64 exceeding 100KB returns 400/validation error
  - `PUT` with null clears the photo (subsequent GET returns null)

- [x] **Step 3: Run tests**
  ```bash
  cd /c/claude/fusecp-enterprise
  dotnet test tests/ --filter "OrganizationContact|UserPhoto" 2>&1 | tail -20
  ```

- [x] **Step 4: Commit tests**
  ```bash
  git add tests/
  git commit -m "test(phase2): add org contact and AD photo endpoint tests

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

## Final Review & Cleanup

---

### Task 12: Post-Implementation Cleanup and Review

**Agent:** post-task-cleanup

**Files:**
- Review all modified files across Phases 1-4

**Context:**
After all 11 implementation tasks are complete, perform a full hygiene pass to ensure code quality, remove any dead code introduced, verify no accidental changes to SolidCP-compatible tables, and confirm the accordion design system is consistent across all three UI phases.

- [x] **Step 1: Scan for unused variables, dead code, commented-out blocks**
  Review all modified `.razor`, `.cs`, and `.sql` files for:
  - Unused C# variables or properties
  - Commented-out old forwarding TextInput code in MailboxMailFlowTab
  - Any `TODO` comments without implementations
  - Duplicate CSS definitions across tabs

- [x] **Step 2: Verify accordion CSS consistency**
  Confirm that all three UI files (MailboxGeneralTab, MailboxMailFlowTab, OrganizationEdit) use identical variable names, class names, and animation values for the accordion system. If any tab defines its own local copy, check whether a shared stylesheet or CSS include could consolidate them.

- [x] **Step 3: Verify all DB changes are ADDITIVE**
  Run:
  ```bash
  sqlcmd -S "(local)\SQLEXPRESS" -d FuseCPLab -Q "
    SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME IN ('Organizations')
    AND COLUMN_NAME IN ('CompanyLegalName','TaxId','Phone','Email','Address','City','State','PostalCode','Country','Website')
    ORDER BY COLUMN_NAME"
  ```
  Confirm all 10 new columns exist and are NULLABLE.

- [x] **Step 4: Full build and test run**
  ```bash
  cd /c/claude/fusecp-enterprise
  dotnet build 2>&1 | tail -10
  dotnet test tests/ 2>&1 | tail -30
  ```
  All builds and tests must pass.

- [x] **Step 5: Run make check if applicable**
  ```bash
  cd /c/claude/fusecp-enterprise
  make check 2>&1 | tail -20
  ```

- [x] **Step 6: Final commit for any cleanup changes**
  ```bash
  git add .
  git commit -m "chore: post-implementation cleanup for Phases 1-4

  Remove dead code, consolidate accordion CSS, verify DB additivity.

  🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

  Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
  ```

---

## Summary Table

| Task | Phase | Agent | Files | FR |
|------|-------|-------|-------|-----|
| 1 | Phase 4 | bug-hunter | `OperationsLoggingMiddleware.cs` | #48 |
| 2 | Phase 1 | modular-builder | `MailboxSettings.cs`, `ExchangeEndpoints.cs` | #44 #42 #38 |
| 3 | Phase 1 | component-designer | `MailboxGeneralTab.razor` | #44 #42 #38 |
| 4 | Phase 1 | test-coverage | `MailboxGeneralTests.cs` | #44 #42 #38 |
| 5 | Phase 3 | component-designer | `MailboxMailFlowTab.razor` | #33 |
| 6 | Phase 2 | database-architect | `V0XX__AddOrganizationContactFields.sql`, `Organization.cs` | #36 |
| 7 | Phase 2 | modular-builder | `OrganizationsEndpoints.cs`, `OrganizationsRepository.cs` | #36 |
| 8 | Phase 2 | component-designer | `OrganizationEdit.razor` | #36 |
| 9 | Phase 2 | modular-builder | `AdProvider.cs`, `AdUser.cs`, `ADEndpoints.cs` | #37 |
| 10 | Phase 2 | component-designer | `MailboxGeneralTab.razor` | #37 |
| 11 | Phase 2 | test-coverage | `OrganizationContactTests.cs`, `UserPhotoTests.cs` | #36 #37 |
| 12 | All | post-task-cleanup | All modified files | — |

**Total tasks: 12**
