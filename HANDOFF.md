# Amplifier Cowork — Task Handoff

## Dispatch Status: WAITING_FOR_GEMINI

> **Protocol:** Only the designated receiver should act.
> - Claude acts on: `IDLE`, `PR_READY`, `REVIEWING`, `DEPLOYING`, `WAITING_FOR_CLAUDE`
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
**Branch:** feature/mailbox-general-tab-redesign
**Priority:** normal
**Repository:** C:\claude\fusecp-enterprise
**Working Directory:** C:\claude\fusecp-enterprise
**PR Target:** master on psklarkins/fusecp-enterprise

### Objective
Redesign the Mailbox General Tab with AD contact fields integration and 5-section accordion layout (Phase 1 of Feature Requests plan — Tasks 2, 3, 4).

### Detailed Requirements

This task implements Phase 1 of the feature requests plan. It involves three coordinated changes:

#### Task 2: Extend MailboxGeneralSettings DTO

File: `src/FuseCP.Providers.Exchange/Models/MailboxSettings.cs`

Add an `AdContactFields` record to hold AD contact data. The existing `MailboxGeneralSettings` record currently has: DisplayName, FirstName, LastName, Initials, Alias, HiddenFromAddressLists, Database, MailboxType.

**Add this new record** (after the existing `MailboxGeneralSettings` record):

```csharp
public record AdContactFields(
    string? TelephoneNumber,
    string? MobilePhone,
    string? FacsimileTelephoneNumber,
    string? HomePhone,
    string? Pager,
    string? IpPhone,
    string? JobTitle,
    string? Department,
    string? Company,
    string? Manager,
    string? StreetAddress,
    string? City,
    string? State,
    string? PostalCode,
    string? Country,
    string? Notes,
    string? WebPage
);
```

**Extend MailboxGeneralSettings** — add a single property:
```csharp
AdContactFields? ContactFields
```

This follows the existing pattern where MailboxSettings.cs contains all Exchange-related DTOs.

**Reference the AD field names from:** `src/FuseCP.Providers.AD/Models/AdUser.cs` (lines 3-23) — the `AdUser` record already has all 17 contact fields with identical names. The new `AdContactFields` record mirrors those field names exactly.

#### Task 3: Redesign MailboxGeneralTab.razor

File: `src/FuseCP.Portal/Components/Pages/Exchange/Tabs/MailboxGeneralTab.razor`

Replace the current flat form layout with a 5-section accordion using the existing FuseCP accordion pattern.

**The 5 accordion sections:**

1. **General** (expanded by default) — DisplayName, FirstName, LastName, Initials, Alias, HiddenFromAddressLists
2. **Contact Information** — TelephoneNumber, MobilePhone, FacsimileTelephoneNumber, HomePhone, Pager, IpPhone
3. **Organization** — JobTitle, Department, Company, Manager
4. **Address** — StreetAddress, City, State, PostalCode, Country
5. **Notes** — Notes, WebPage

**Accordion pattern to follow** — use the same HTML/CSS pattern already used in FuseCP. Look at existing accordion implementations in the Portal codebase:
- Search for `accordion` in `src/FuseCP.Portal/Components/` for existing patterns
- If no existing accordion pattern exists, use standard Bootstrap 5 accordion (`accordion`, `accordion-item`, `accordion-header`, `accordion-body`, `accordion-collapse`)

**Form field pattern** — follow the existing `.input` and `.label` classes used throughout the portal (standardized in Phase 6.3b). Example:
```html
<div class="mb-3">
    <label class="label">@Loc["exchange.display_name"]</label>
    <input type="text" class="input" @bind="Model.DisplayName" />
</div>
```

**i18n keys** — Use the `exchange.*` namespace for all new field labels. The keys should be:
- `exchange.contact_information` (section header)
- `exchange.organization` (section header)
- `exchange.address` (section header)
- `exchange.notes` (section header)
- `exchange.telephone_number`, `exchange.mobile_phone`, `exchange.fax`, `exchange.home_phone`, `exchange.pager`, `exchange.ip_phone`
- `exchange.job_title`, `exchange.department`, `exchange.company`, `exchange.manager`
- `exchange.street_address`, `exchange.city`, `exchange.state`, `exchange.postal_code`, `exchange.country`
- `exchange.notes_field`, `exchange.web_page`

**Create a SQL migration** for these i18n keys (both EN and PL) at:
`src/FuseCP.Database/Migrations/092_AddMailboxGeneralTabTranslations.sql`

Follow the MERGE pattern from migration 091 (`src/FuseCP.Database/Migrations/091_AddDashboardAndMissingTranslations.sql`).

Also create a PowerShell execution script at `scripts/bugfix/run-migration-092.ps1` following the same pattern as `scripts/bugfix/run-migration-091.ps1` (ADO.NET with proper Unicode handling for Polish diacritics).

#### Task 4: Write Tests

Add tests for the new DTO and verify the accordion renders correctly.

File: `tests/FuseCP.Tests/Exchange/MailboxGeneralSettingsTests.cs` (new file)

Test coverage:
- `AdContactFields` record can be created with all fields
- `AdContactFields` record handles null fields correctly
- `MailboxGeneralSettings` includes `ContactFields` property
- `ContactFields` can be null (backward compatible)

### Spec
Inline — see Objective and Detailed Requirements above.
Full plan at: `C:\claude\amplifier\docs\plans\2026-02-21-feature-requests-phases1-4.md` (Tasks 2-4)

### Context Loading (use your full 1M context)
Load these files completely before starting:
- `C:\claude\fusecp-enterprise\src\FuseCP.Providers.Exchange\Models\MailboxSettings.cs` — current DTO to extend
- `C:\claude\fusecp-enterprise\src\FuseCP.Providers.AD\Models\AdUser.cs` — reference for AD contact field names
- `C:\claude\fusecp-enterprise\src\FuseCP.Portal\Components\Pages\Exchange\Tabs\MailboxGeneralTab.razor` — page to redesign
- `C:\claude\fusecp-enterprise\src\FuseCP.Database\Migrations\091_AddDashboardAndMissingTranslations.sql` — migration pattern
- `C:\claude\fusecp-enterprise\scripts\bugfix\run-migration-091.ps1` — PowerShell migration pattern
- `C:\claude\fusecp-enterprise\src\FuseCP.Portal\Components\Pages\Exchange\MailboxEdit.razor` — parent page for context
- `C:\claude\fusecp-enterprise\tmp\mailbox-general-tab-playground.html` — design reference for the accordion layout
- COWORK.md — refresh protocol understanding
- This task section of HANDOFF.md

### Files YOU May Modify
- `src/FuseCP.Providers.Exchange/Models/MailboxSettings.cs` — extend with AdContactFields
- `src/FuseCP.Portal/Components/Pages/Exchange/Tabs/MailboxGeneralTab.razor` — redesign layout
- `src/FuseCP.Database/Migrations/092_AddMailboxGeneralTabTranslations.sql` — new migration
- `scripts/bugfix/run-migration-092.ps1` — new PowerShell migration script
- `tests/FuseCP.Tests/Exchange/MailboxGeneralSettingsTests.cs` — new test file

### Files You Must NOT Modify
- .claude/* (always)
- CLAUDE.md (always)
- C:\FuseCP\* (always)
- C:\Przemek\OPENCODE.md (always)
- `src/FuseCP.Providers.AD/Models/AdUser.cs` — read-only reference
- `src/FuseCP.EnterpriseServer/Endpoints/ExchangeEndpoints.cs` — do NOT modify API endpoints in this task

### Acceptance Criteria
- [ ] `AdContactFields` record added with all 17 fields matching AdUser.cs field names
- [ ] `MailboxGeneralSettings` extended with nullable `ContactFields` property
- [ ] MailboxGeneralTab.razor uses 5-section accordion layout
- [ ] General section expanded by default, other 4 collapsed
- [ ] All form fields use `.input` and `.label` classes
- [ ] All labels use `@Loc["exchange.*"]` i18n keys
- [ ] Migration 092 creates all new i18n keys (EN + PL)
- [ ] PowerShell migration script handles Polish diacritics correctly
- [ ] Tests verify DTO creation and null handling
- [ ] All tests pass
- [ ] No lint errors
- [ ] Code committed to feature branch with clear messages

### Build & Verify (MUST complete before creating PR)

Run these commands and confirm they pass. Do NOT create a PR until all pass:

```bash
cd /c/claude/fusecp-enterprise && dotnet build --no-incremental 2>&1 | tail -5
```

Expected: Build succeeded, 0 errors.

```bash
cd /c/claude/fusecp-enterprise && dotnet test --no-build --verbosity quiet 2>&1 | tail -10
```

Expected: All tests pass (1 pre-existing HyperV test failure is acceptable).

If build fails, fix the errors before proceeding. Include build output summary in PR description.

### Agent Assignments (MANDATORY — use subagents for implementation)

You MUST use your agents at `C:\Przemek\agents\` for this task. Do NOT implement everything in your main context — delegate to specialized agents.

| Task | Agent | What to delegate |
|------|-------|-----------------|
| Extend MailboxSettings.cs with AdContactFields record | modular-builder | Add AdContactFields record and extend MailboxGeneralSettings with ContactFields property |
| Redesign MailboxGeneralTab.razor with accordion | component-designer | Build 5-section accordion layout with all form fields and i18n keys |
| Create migration 092 SQL + PowerShell scripts | database-architect | Write MERGE-based SQL migration and ADO.NET PowerShell script for Unicode handling |
| Write DTO tests | test-coverage | Create MailboxGeneralSettingsTests.cs with record creation and null handling tests |

**How to use agents:** For each row above, dispatch the agent as a subagent with a focused prompt describing exactly what to implement. The agent will do the work and return results. Review the output, fix any issues, then move to the next task.

**Agent tier unlocks:** primary + knowledge

---

## History

| Date | Direction | Task | PR | Result |
|------|-----------|------|-----|--------|
| 2026-02-16 | Gemini → Claude | Initial cowork setup | — | Agents synced, protocol established |
| 2026-02-17 | Claude → Gemini | Browser integration tests (API-UI parity) | PR#221 (closed, wrong repo) | Gemini created tests in fusecp-enterprise. Claude fixed runner (timeouts, verdict logic), ran suite. Initial: 4 PASS (36%). |
| 2026-02-17 | Claude | Fix all integration issues | — | Fixed HyperV connection string bug (500→200), AuditLog error handling, rewrote test suite to be Blazor-aware. Final: 11/11 PASS (100%). Report: `fusecp-enterprise/docs/reports/integration-report.md` |
| 2026-02-17 | Claude → Gemini | LoadingSpinner + shared Pagination for log pages | PR#74 | Success. Gemini: correct implementation, build passed, right repo. Claude: fixed 4 review issues (loading UX consistency, error handling, null-coalescing, missing @using). First successful improved handoff. |
| 2026-02-17 | Claude → Gemini | DNS server config + record templates | PR#75 | Success. Spec compliance 12/12 PASS, clean code quality. Claude: removed 23 junk files post-merge, updated .gitignore. DB migration + deploy verified. |
| 2026-02-17 | Claude → Gemini | Oscars 2026 — all 24 categories + voter ID | PR#1 (oscars repo) | Success. Spec 12/12 PASS. Claude fixed 3 issues: Change Name vote-clearing scope, alert→modal, deprecated pageYOffset. Deployed to oscars.ergonet.pl. |
| 2026-02-17 | Claude → Gemini | JSON voter database + voters page + Node.js API | PR#2 (oscars repo) | Success. Claude fixed 2 issues: GET /api/votes response format (array→object), voters.html API parsing. Added IIS reverse proxy (web.config) + scheduled task for Node.js persistence. Deployed to oscars.ergonet.pl. |
| 2026-02-17 | Claude → Gemini | Movie poster images for Oscar nominees | PR#3 (oscars repo) | Success. 15 unique TMDB poster URLs, all verified HTTP 200. Clean implementation, no fixes needed. Deployed to oscars.ergonet.pl. |
| 2026-02-17 | Gemini → Claude | BLOCKED: Permission denied accessing fusecp-enterprise repo | — | Cannot access external directory C:\claude\fusecp-enterprise despite allowed rules. Handoff updated to WAITING_FOR_CLAUDE. |
| 2026-02-17 | Gemini → Claude | Exchange Tenant Isolation Audit | PR#76 | Success. Gemini audited 13 pages, fixed 5. Claude merged + fixed 4 review issues (2 Critical: empty orgSlug/null orgOu bypass, 2 Important: guard logic inversion + toast count). Deployed to Portal. |
| 2026-02-17 | Claude → Gemini | Semantic Color Token Migration (Phase 6.2) | PR#77 | Success. Migration was already ~95% done. Gemini fixed remaining 3 files (sky→primary, text-white→text-button-secondary). Claude fixed 2 more (text-invert on surface-invert, missed secondary button). Verified 0 hardcoded slate/bg-white remaining. |
| 2026-02-18 | Claude → Gemini | PageHeader Component Migration (Phase 6.3a) | PR#78 | Success. Gemini migrated 48/50 pages, Claude review caught 2 missed (MailboxEdit, DistributionListEdit). Gemini fixed in follow-up commit. Claude fixed orphaned `</div>` formatting post-merge. 50 pages now use PageHeader. Deployed to Portal. |
| 2026-02-18 | Claude → Gemini | Form Standardization (.input/.label classes) (Phase 6.3b) | PR#79 | Success. Gemini standardized 42+ pages. Claude resolved merge conflicts with master (Bug #18 type selector), fixed CI formatting (DnsSettingsRepository whitespace), fixed 15+ test failures (Bug #18 Set-Mailbox capture pattern). All 2789 tests pass. Deployed to Portal + API.
| 2026-02-18 | Claude → Gemini | CSS utility class migrations (Phase 6.3c) | PR#80 | Success. Gemini migrated 40+ pages to use new `page-content`, `section-title`, `card-section`, and `section-group` utility classes. Build succeeded with 0 errors. |
| 2026-02-19 | Claude → Gemini | EmptyState component migration (Phase 6.3d) | PR#81 | Closed without merge. Build succeeded but PR was not merged to master. |
| 2026-02-19 | Claude → Gemini | LoadingSpinner migration (Phase 6.3e) | PR#82-85 | 4 attempts, all closed without merge. Build succeeded each time but none merged to master. Re-dispatching as v2. |
| 2026-02-19 | Gemini → Claude | LoadingSpinner migration (Phase 6.3e) v2 | PR#86 | Success. 6 spinners in 4 files. Merged + deployed to Portal. No fixes needed. |
| 2026-02-19 | Gemini → Claude | EmptyState migration (Phase 6.3d) v2 | PR#87 | Success. 11 empty states in 9 files. Build 0 errors. Merged + deployed to Portal. No fixes needed. |
| 2026-02-20 | Claude → Gemini | P6.4 Component Library Polish — semantic tokens + shared components | PR#95 | Success. 15 files, +162/-300 lines. Claude fixed 2 review issues post-merge: Settings/Index.razor link regression, OperationsLog category color collision. Deployed to Portal. |
| 2026-02-20 | Gemini → Claude | Fix missing i18n translations (dashboard, DNS templates) | PR#96 | Success. Added migration 084 with 40+ missing keys. |
