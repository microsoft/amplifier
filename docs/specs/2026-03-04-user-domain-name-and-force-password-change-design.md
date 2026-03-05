# User Domain Name and Force Password Change Design Spec

**Date:** 2026-03-04
**Status:** Approved
**Author:** Claude (validated design)
**Features:** #90 (User Domain Name on Mailbox Card), #88 (Force Password Change at Next Logon)

---

## Problem

### Feature #90 — User Domain Name on Mailbox Card

The mailbox card does not display the `DOMAIN\username` format required for configuring phones, printers, and other devices that authenticate against Active Directory. Users must manually derive this from separate fields (email address and SAM account name), which is error-prone and adds unnecessary friction during device setup.

### Feature #88 — Force Password Change at Next Logon

There is no option to force a password change at the next logon, either during mailbox creation or during a password reset. The `MustChangePasswordAtNextLogon` field already exists in `CreateAdUserRequest` but is silently ignored — it is not wired through the AD provider, API layers, or UI. This means administrators cannot enforce password rotation for new accounts or after a manual reset, which is a common security requirement.

---

## Goal

### Feature #90

Display the derived `DOMAIN\username` string as a read-only field on the mailbox detail view and the mailbox general settings tab. No new API calls, no database changes, no new data model fields — this is a pure UI derivation from existing UPN and SAM account name data.

### Feature #88

**A. Creation flow:** Wire the existing dead `MustChangePasswordAtNextLogon` field through the full stack so that when checked during mailbox creation, Active Directory sets `ChangePasswordAtLogon = $true` on the newly created user.

**B. Reset flow:** Add `MustChangePasswordAtNextLogon` to the reset password request, so that when a password reset is performed, the same AD flag is set. The checkbox in the reset modal defaults to checked to encourage secure practice.

---

## Changes

### Feature #90 — User Domain Name derivation

The `DOMAIN\username` string is derived client-side with no backend changes. The domain portion is the first DNS label of the UPN domain, uppercased:

```
john.smith@contoso.lab.ergonet.pl  →  CONTOSO\john.smith
```

Helper method placed in each consuming Razor component:

```csharp
private static string GetUserDomainName(string? upn, string? sam)
{
    if (string.IsNullOrEmpty(upn) || string.IsNullOrEmpty(sam)) return string.Empty;
    var atIndex = upn.IndexOf('@');
    if (atIndex < 0) return sam;
    var domain = upn[(atIndex + 1)..];
    var dotIndex = domain.IndexOf('.');
    var netbios = dotIndex > 0 ? domain[..dotIndex] : domain;
    return $"{netbios.ToUpperInvariant()}\\{sam}";
}
```

The field is displayed below "Account Name" in the Mailbox Details card and below "SAM Account Name" in the Account Information section. It is read-only — no edit interaction.

### Feature #88 — Password change flag wiring

**Creation flow:**

- `AdProvider.CreateUserAsync` calls `Set-ADUser -Identity <sam> -ChangePasswordAtLogon $true` after successful user creation when the flag is set.
- `MustChangePasswordAtNextLogon` is already present in `CreateAdUserRequest`; it is passed through `ExchangeEndpoints.cs` → `IAdApiClient` → `AdApiClient` → `AdEndpoints.cs` → `IAdProvider` → `AdProvider`.
- The create mailbox UI gains a checkbox labelled "Force password change at next logon", unchecked by default.

**Reset flow:**

- `ResetPasswordApiRequest` gains a `MustChangePasswordAtNextLogon` boolean field.
- `AdProvider.ResetPasswordAsync` calls `Set-ADUser -Identity <sam> -ChangePasswordAtLogon $true` after `Set-ADAccountPassword` when the flag is set.
- The reset password modal in `MailboxGeneralTab.razor` gains a checkbox labelled "Force password change at next logon", checked by default.
- The flag passes through: modal → `IAdApiClient.ResetPasswordAsync` → `AdApiClient` → `AdEndpoints.cs` → `IAdProvider.ResetPasswordAsync` → `AdProvider`.

---

## Impact

- **No database migrations.** Neither feature requires schema changes.
- **No new API endpoints.** Feature #90 is client-side only. Feature #88 extends existing request DTOs.
- **No breaking changes.** The new boolean fields on request DTOs default to `false`; existing callers that do not send the field receive unchanged behavior.
- **Tenant isolation:** Not affected — the changes operate on individual mailboxes already scoped by the calling tenant's PackageId.
- **Security boundary:** Password change enforcement is applied at the Active Directory layer via `Set-ADUser`, not at the API or UI layer. The API layer passes the flag; AD enforces it.
- **Translations:** Both features require new label keys in the EN and PL translation migration (Migration 119).

---

## Files Changed

| # | File | Feature | Change |
|---|------|---------|--------|
| 1 | `MailboxDetail.razor` | #90 | Add read-only "User Domain Name" field below "Account Name" in the Mailbox Details card |
| 2 | `MailboxGeneralTab.razor` | #90, #88 | Add read-only "User Domain Name" field below "SAM Account Name"; add "Force password change at next logon" checkbox to reset password modal |
| 3 | `AdProvider.cs` | #88 | Wire `ChangePasswordAtLogon` for create flow (`CreateUserAsync`) and reset flow (`ResetPasswordAsync`) |
| 4 | `IAdProvider.cs` | #88 | Add `mustChangePasswordAtNextLogon` parameter to `ResetPasswordAsync` signature |
| 5 | `AdEndpoints.cs` | #88 | Add `MustChangePasswordAtNextLogon` to `ResetPasswordApiRequest`; pass flag to `IAdProvider.ResetPasswordAsync` |
| 6 | `IAdApiClient.cs` | #88 | Add `mustChangePasswordAtNextLogon` parameter to `ResetPasswordAsync` method signature |
| 7 | `AdApiClient.cs` | #88 | Include `MustChangePasswordAtNextLogon` in the POST body of the reset password request |
| 8 | `ExchangeEndpoints.cs` | #88 | Pass `MustChangePasswordAtNextLogon` from create mailbox request through to the AD creation call |
| 9 | `IExchangeApiClient.cs` | #88 | Add `MustChangePasswordAtNextLogon` field to the create mailbox DTO |
| 10 | Create mailbox UI (`.razor`) | #88 | Add "Force password change at next logon" checkbox (unchecked by default) |
| 11 | Migration 119 | #90, #88 | Add EN and PL translation keys: `UserDomainName`, `ForcePasswordChange`, `ForcePasswordChangeHint` |

All files are in the `fusecp-enterprise` repository at `C:\claude\fusecp-enterprise\`.

---

## Agent Allocation

| Phase | Agent | Responsibility |
|-------|-------|---------------|
| Implementation | `modular-builder` | All code changes across files 1–11 |
| Review | `pr-review-toolkit:code-reviewer` | Pre-merge code review |
| Cleanup | `post-task-cleanup` | Final hygiene pass |

Turn budgets: `modular-builder` = 20 turns (11 files across two features), `pr-review-toolkit:code-reviewer` = 12 turns, `post-task-cleanup` = 8 turns.

---

## Test Plan

### Feature #90 — User Domain Name

- [ ] Open a mailbox with UPN `john.smith@contoso.lab.ergonet.pl` and SAM `john.smith` — "User Domain Name" displays `CONTOSO\john.smith`
- [ ] "User Domain Name" appears in the Mailbox Details card below "Account Name"
- [ ] "User Domain Name" appears in the Account Information section of the General tab below "SAM Account Name"
- [ ] Field is read-only — no edit control is rendered
- [ ] UPN with a single-label domain (no dot) — the full domain uppercased is used: `john@contoso` → `CONTOSO\john`
- [ ] Mailbox with null or empty UPN — field renders empty without throwing an exception
- [ ] EN label renders as "User Domain Name"; PL label renders correctly from migration 119

### Feature #88 — Force Password Change

#### Creation flow

- [ ] "Force password change at next logon" checkbox appears on the create mailbox form, unchecked by default
- [ ] Create a mailbox with the checkbox checked — the new AD user has `ChangePasswordAtLogon = True` (verify via `Get-ADUser -Properties PasswordExpired` or first logon prompt)
- [ ] Create a mailbox with the checkbox unchecked — `ChangePasswordAtLogon = False` (existing behavior preserved)

#### Reset flow

- [ ] "Force password change at next logon" checkbox appears in the reset password modal, checked by default
- [ ] Reset password with the checkbox checked — `ChangePasswordAtLogon = True` is set on the AD user
- [ ] Reset password with the checkbox unchecked — `ChangePasswordAtLogon` is not set (AD user state unchanged for this flag)
- [ ] Existing callers that send a reset request without the new field receive unchanged behavior (field defaults to `false`)
- [ ] EN label renders as "Force password change at next logon"; PL label renders correctly from migration 119

---

## Acceptance Criteria

1. `DOMAIN\username` is visible as a read-only field in both `MailboxDetail.razor` and `MailboxGeneralTab.razor`, correctly derived from UPN + SAM for all mailboxes.
2. The derivation handles edge cases without exceptions: null UPN, empty SAM, single-label domain.
3. A checkbox for "Force password change at next logon" exists on the create mailbox form (unchecked by default) and wires through to `Set-ADUser -ChangePasswordAtLogon $true` in `AdProvider.CreateUserAsync`.
4. A checkbox for "Force password change at next logon" exists in the reset password modal (checked by default) and wires through to `Set-ADUser -ChangePasswordAtLogon $true` in `AdProvider.ResetPasswordAsync`.
5. Resetting a password without checking the box does not alter the `ChangePasswordAtLogon` flag on the AD user.
6. All new UI labels are present in both EN and PL translations via Migration 119.
7. No existing tests are broken; no new nullable reference warnings introduced.
