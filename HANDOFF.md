# Amplifier Cowork — Task Handoff

## Dispatch Status: WAITING_FOR_GEMINI

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
**Branch:** `feature/browser-integration-tests`
**Priority:** normal

### Objective
Create browser-based integration tests using Playwright + Chrome that mirror FuseCP's existing API integration tests, run them against the live portal at https://fusecp.ergonet.pl, and produce a detailed report showing API ↔ frontend parity, discrepancies, and UI bugs.

### Spec

**Goal:** Verify 1:1 parity between API responses and portal UI display. Report any discrepancy.

**API → Portal Page Mapping:**

| API Test | API Endpoint | Portal Page | What to verify |
|----------|-------------|-------------|----------------|
| List Organizations | GET /api/exchange/organizations | /organizations | Same org count and names |
| Org Details | GET /api/exchange/organizations/{id} | /organizations/{id} | Details match API |
| List Mailboxes | GET /api/exchange/organizations/{id}/mailboxes | /organizations/{id} (mailbox tab) | Same mailbox count and emails |
| Mailbox Details | GET /api/exchange/mailboxes/{id} | Click mailbox row | Same settings shown |
| List VMs | GET /api/hyperv/{host}/vms | /vms | Same VM names and states |
| DNS Zones | GET /api/dns/zones | /dns/zones | Same zone list |
| DNS Records | GET /api/dns/zones/{name}/records | /dns/zones/{name}/records | Same record list |
| AD Groups | GET /api/ad/groups | /ad/groups | Same groups shown |
| AD Statistics | GET /api/ad/statistics | /ad/statistics | Same counts |
| Plans | GET /api/plans | /settings/plans | Same plan list |
| Audit Logs | GET /api/admin/audit/logs | /admin/audit/dashboard | Logs visible and matching |
| Admin Dashboard | — | /admin/dashboard | Page loads without errors |
| Bug Reports | — | /admin/bugs | Page loads without errors |
| Operations Log | — | /admin/operations | Page loads without errors |
| Servers | GET /api/servers | /settings/servers | Server list matches |

**Test approach:**
1. For each API endpoint: call API via curl/fetch with admin key, capture JSON response
2. Navigate to corresponding portal page in Chrome (logged in)
3. Extract visible data from the page (element text, table rows, counts)
4. Compare: count of items, names, key field values
5. Flag: PASS (match), MISMATCH (data differs), MISSING (feature absent in UI), BUG (UI error/crash)

**Portal credentials for browser tests:**
- URL: https://fusecp.ergonet.pl/login
- User: `Agnieszka`
- Password: `Kaja@2015`

**API credentials for comparison calls:**
- Base URL: http://localhost:5010
- Admin key: `fusecp-admin-key-2026` (header: X-Api-Key)

**Report format:** Markdown file with:
- Summary table: page name, API status, UI status, verdict (PASS/MISMATCH/MISSING/BUG)
- Details section per discrepancy: what differs, expected vs actual
- Bug list: description, severity, page, steps to reproduce
- Overall statistics: total pages tested, pass rate, bug count

### Context Loading (use your full 1M context)
Load these files completely before starting:
- `C:\claude\fusecp-enterprise\scripts\api-tests\Common-TenantTestVariables.ps1` — test infrastructure, API helpers, assertion functions
- `C:\claude\fusecp-enterprise\scripts\api-tests\Run-TenantIntegrationTests.ps1` — master test runner pattern
- `C:\claude\fusecp-enterprise\scripts\api-tests\Test-TenantAccess.ps1` — tenant access test examples
- `C:\claude\fusecp-enterprise\scripts\api-tests\Test-TenantAdminDenial.ps1` — admin denial test examples
- `C:\claude\fusecp-enterprise\scripts\api-tests\Run-CrudIntegrationTests.ps1` — CRUD test examples
- `C:\claude\fusecp-enterprise\scripts\api-tests\Test-ExchangeCrud.ps1` — Exchange CRUD operations
- `C:\claude\fusecp-enterprise\scripts\api-tests\Test-AdCrud.ps1` — AD CRUD operations
- `C:\claude\amplifier\COWORK.md` — refresh protocol understanding
- This task section of HANDOFF.md

### Files YOU May Modify
- `C:\claude\fusecp-enterprise\scripts\browser-tests\*` (new directory — create test scripts here)
- `C:\claude\fusecp-enterprise\docs\reports\*` (new directory — write report here)

### Files You Must NOT Modify
- `.claude/*` (always)
- `CLAUDE.md` (always)
- `C:\FuseCP\*` (always)
- `C:\Przemek\OPENCODE.md` (always)
- Any existing files in `scripts\api-tests\` (read-only reference)
- Any `.razor` files (portal source — read-only reference)

### Acceptance Criteria
- [ ] Browser test script(s) created that cover each portal page in the mapping table
- [ ] Each test: calls API endpoint AND navigates portal page, compares results
- [ ] Tests run successfully against live portal (https://fusecp.ergonet.pl)
- [ ] Detailed markdown report with: summary table, per-page results, discrepancy details, bug list
- [ ] Report clearly uses verdicts: PASS, MISMATCH, MISSING, BUG
- [ ] Any UI bugs documented with description and severity
- [ ] Code committed to `feature/browser-integration-tests` branch
- [ ] PR created targeting main

### Agent Tier Unlocks
- `test-coverage` (primary) — test strategy and coverage
- `bug-hunter` (primary) — investigating discrepancies
- `analysis-engine` (knowledge) — report synthesis
- `security-guardian` (senior-review) — if auth/access issues found during testing

---

## History

| Date | Direction | Task | PR | Result |
|------|-----------|------|-----|--------|
| 2026-02-16 | Gemini → Claude | Initial cowork setup | — | Agents synced, protocol established |
