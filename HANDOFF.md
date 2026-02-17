# Amplifier Cowork — Task Handoff

## Dispatch Status: PR_READY

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

**From:** Gemini → Claude
**Branch:** feature/exchange-tenant-isolation-audit
**Priority:** normal
**Repository:** C:\claude\fusecp-enterprise
**Working Directory:** C:\claude\fusecp-enterprise
**PR Target:** master on psklarkins/fusecp-enterprise
**PR Link:** https://github.com/psklarkins/fusecp-enterprise/pull/76

### Objective
Audit ALL remaining Exchange Portal pages for tenant isolation violations and fix any pages missing org-scoping, org-slug filtering, or ownership verification.

### Detailed Requirements

Claude just completed tenant isolation fixes for 6 Exchange pages. Your job is to audit and fix the **remaining 13 pages** using the same patterns.

**Already fixed (DO NOT MODIFY these — use as reference patterns):**
- `src/FuseCP.Portal/Components/Shared/DomainSelector.razor` — uses `GetOrganizationDomainsAsync(OrganizationId)`
- `src/FuseCP.Portal/Components/Pages/Exchange/AcceptedDomains.razor` — `_isOrgContext` branching, read-only in org context
- `src/FuseCP.Portal/Components/Pages/Exchange/ActiveSyncPolicies.razor` — org slug prefix filtering + write guards
- `src/FuseCP.Portal/Components/Pages/Exchange/AddressBookPolicies.razor` — org slug prefix filtering + write guards
- `src/FuseCP.Portal/Components/Pages/Exchange/MailboxDetail.razor` — ownership check `_mailbox.ItemID != OrganizationId`
- `src/FuseCP.Portal/Components/Pages/Exchange/MailboxEdit.razor` — ownership check with legacy route denial

**Pages to audit and fix (if violations found):**
1. `DistributionLists.razor` — Does it filter DLs by org? Does it have org route?
2. `DistributionListEdit.razor` — Does it verify DL belongs to current org?
3. `Contacts.razor` — Does it filter contacts by org?
4. `PublicFolders.razor` — Does it filter PFs by org?
5. `ResourceMailboxes.razor` — Does it filter resource mailboxes by org?
6. `MailboxPlans.razor` — Does it filter plans by org?
7. `RetentionPolicies.razor` — Does it filter retention policies by org?
8. `Disclaimers.razor` — Does it filter disclaimers by org?
9. `StorageUsage.razor` — Does it scope storage stats to org?
10. `Mailboxes.razor` — Does it filter mailbox list by org?
11. `Tabs/MailboxGeneralTab.razor` — Does it verify org context?
12. `Tabs/MailboxEmailAddressesTab.razor` — Does it verify org context?
13. `Tabs/MailboxArchiveTab.razor`, `MailboxLitigationHoldTab.razor`, `MailboxMailFlowTab.razor`, `MailboxAutoReplyTab.razor`, `MailboxMobileDevicesTab.razor`, `MailboxPermissionsTab.razor`, `MailboxStatisticsTab.razor` — Do they verify org context?

**Tenant isolation patterns to check for:**

Pattern A — **Org-scoped route**: Page should have `@page "/exchange/feature/{OrganizationId:int}"` in addition to any base route.

Pattern B — **Org resolver**: Page should inject `IOrganizationResolver` and resolve org from `PackageId` or `OrganizationId` parameter.

Pattern C — **Data filtering**: Lists should filter data to only show items belonging to the current org. For Exchange server-wide resources (policies, disclaimers), filter by `Name.StartsWith($"{orgSlug}-")`. For org-owned data (mailboxes, DLs, contacts), use org-scoped API calls.

Pattern D — **Ownership verification**: Detail/edit pages should verify the loaded item belongs to the current org (e.g., `_mailbox.ItemID != OrganizationId`).

Pattern E — **Write operation guards**: In org context, create/edit/delete operations should enforce org ownership (auto-prefix names, verify before delete).

**For each page, produce a report line:**
```
| Page | Has Org Route | Uses OrgResolver | Filters Data | Ownership Check | Write Guards | Verdict |
```

Where Verdict is: PASS (already correct), NEEDS_FIX (violation found), or N/A (page doesn't need isolation).

**For pages that NEED_FIX:** Implement the fix following the exact patterns in the reference files. Read AcceptedDomains.razor and ActiveSyncPolicies.razor thoroughly before implementing — they are the canonical examples.

### Spec
Inline — see Objective and Detailed Requirements above.

### Context Loading (use your full 1M context)
Load ALL these files completely before starting:
- `COWORK.md` — refresh protocol understanding
- This task section of `HANDOFF.md`
- ALL 6 already-fixed pages (read fully to understand patterns):
  - `src/FuseCP.Portal/Components/Shared/DomainSelector.razor`
  - `src/FuseCP.Portal/Components/Pages/Exchange/AcceptedDomains.razor`
  - `src/FuseCP.Portal/Components/Pages/Exchange/ActiveSyncPolicies.razor`
  - `src/FuseCP.Portal/Components/Pages/Exchange/AddressBookPolicies.razor`
  - `src/FuseCP.Portal/Components/Pages/Exchange/MailboxDetail.razor`
  - `src/FuseCP.Portal/Components/Pages/Exchange/MailboxEdit.razor`
- ALL 13 remaining pages (read fully to audit):
  - `src/FuseCP.Portal/Components/Pages/Exchange/DistributionLists.razor`
  - `src/FuseCP.Portal/Components/Pages/Exchange/DistributionListEdit.razor`
  - `src/FuseCP.Portal/Components/Pages/Exchange/Contacts.razor`
  - `src/FuseCP.Portal/Components/Pages/Exchange/PublicFolders.razor`
  - `src/FuseCP.Portal/Components/Pages/Exchange/ResourceMailboxes.razor`
  - `src/FuseCP.Portal/Components/Pages/Exchange/MailboxPlans.razor`
  - `src/FuseCP.Portal/Components/Pages/Exchange/RetentionPolicies.razor`
  - `src/FuseCP.Portal/Components/Pages/Exchange/Disclaimers.razor`
  - `src/FuseCP.Portal/Components/Pages/Exchange/StorageUsage.razor`
  - `src/FuseCP.Portal/Components/Pages/Exchange/Mailboxes.razor`
  - `src/FuseCP.Portal/Components/Pages/Exchange/Tabs/MailboxGeneralTab.razor`
  - `src/FuseCP.Portal/Components/Pages/Exchange/Tabs/MailboxEmailAddressesTab.razor`
  - All remaining Tabs/*.razor files
- Key service interfaces for understanding API patterns:
  - `src/FuseCP.Portal/Services/IExchangeApiClient.cs`
  - `src/FuseCP.Portal/Services/ExchangeApiClient.cs`

### Files YOU May Modify
- `src/FuseCP.Portal/Components/Pages/Exchange/DistributionLists.razor`
- `src/FuseCP.Portal/Components/Pages/Exchange/DistributionListEdit.razor`
- `src/FuseCP.Portal/Components/Pages/Exchange/Contacts.razor`
- `src/FuseCP.Portal/Components/Pages/Exchange/PublicFolders.razor`
- `src/FuseCP.Portal/Components/Pages/Exchange/ResourceMailboxes.razor`
- `src/FuseCP.Portal/Components/Pages/Exchange/MailboxPlans.razor`
- `src/FuseCP.Portal/Components/Pages/Exchange/RetentionPolicies.razor`
- `src/FuseCP.Portal/Components/Pages/Exchange/Disclaimers.razor`
- `src/FuseCP.Portal/Components/Pages/Exchange/StorageUsage.razor`
- `src/FuseCP.Portal/Components/Pages/Exchange/Mailboxes.razor`
- `src/FuseCP.Portal/Components/Pages/Exchange/Tabs/*.razor`

### Files You Must NOT Modify
- .claude/* (always)
- CLAUDE.md (always)
- C:\FuseCP\* (always)
- C:\Przemek\OPENCODE.md (always)
- The 6 already-fixed pages listed above (reference only)
- `src/FuseCP.Portal/Services/IExchangeApiClient.cs` (read-only reference)
- `src/FuseCP.Portal/Services/ExchangeApiClient.cs` (read-only reference)

### Acceptance Criteria
- [x] All 13+ remaining Exchange pages audited with report table
- [x] All pages with NEEDS_FIX verdict have been fixed
- [x] Fixes follow exact same patterns as the 6 reference pages
- [x] No regressions — pages that already work correctly are not broken
- [x] Build passes: `dotnet build --no-incremental` from repo root
- [x] All tests pass: `dotnet test --no-build --verbosity quiet`
- [x] Code committed to feature branch with clear messages
- [x] PR description includes the full audit report table

### Build & Verify (MUST complete before creating PR)

```bash
cd /c/claude/fusecp-enterprise && dotnet build --no-incremental 2>&1 | tail -5
```

Expected: Build succeeded, 0 errors.

```bash
cd /c/claude/fusecp-enterprise && dotnet test --no-build --verbosity quiet 2>&1 | tail -15
```

Expected: All pass except 1 pre-existing HyperV failure (ResourceMailboxTests).

### Agent Assignments (MANDATORY — use subagents for implementation)

You MUST use your agents at `C:\Przemek\agents\` for this task. Do NOT implement everything in your main context — delegate to specialized agents.

| Task | Agent | What to delegate |
|------|-------|-----------------|
| Read all 19 Exchange pages and produce audit report table | agentic-search | Load all .razor files, check each for patterns A-E, produce structured report |
| Fix DistributionLists + DistributionListEdit | bug-hunter | Add org route, OrgResolver, ownership filtering following AcceptedDomains pattern |
| Fix Contacts, PublicFolders, ResourceMailboxes | bug-hunter | Add org-scoped filtering for each, following existing patterns |
| Fix RetentionPolicies, Disclaimers, MailboxPlans | bug-hunter | Add org slug filtering for server-wide Exchange resources |
| Fix StorageUsage, Mailboxes (if needed) | bug-hunter | Add org scoping if missing |
| Audit Tabs/*.razor (likely already scoped via parent) | agentic-search | Verify tabs inherit org context from parent MailboxDetail/MailboxEdit |
| Build and test verification | test-coverage | Run build + tests, verify no regressions |

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
| 2026-02-17 | Gemini → Claude | Exchange Tenant Isolation Audit | PR#76 | Audit complete: 4 pages needed defensive checks, 1 page needed compilation fix. All fixed and verified. Build passes. |
