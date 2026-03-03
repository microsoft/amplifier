# Gitea Project Management Design Spec

**Date:** 2026-03-03
**Status:** Approved
**Author:** Claude (validated design)

---

## Problem

FuseCP-Enterprise has no structured project management. Work is tracked across 80+ timestamped markdown files in `docs/plans/`. No labels, milestones, project boards, or PR templates exist on the Gitea repository. There is no single dashboard view of what is open, in-progress, or done for features and planning.

Bugs are already handled by a complete custom system (BugReports API + `/fix-bugs` autonomous pipeline) and must NOT be duplicated in Gitea Issues.

---

## Goal

Use Gitea's built-in project management features — labels, issue templates, PR template, and milestones — to track features, enhancements, and planning work. This complements the existing bug system without replacing it.

Secondary goals:
- Provide a single dashboard view of all planned features, their status, and release targets.
- Migrate active plan docs from `docs/plans/` into Gitea Issues with correct labels and milestone assignments.
- Establish a repeatable workflow: plan as Issue → milestone → feature branch → PR with template → merge.

---

## Approach: Foundation-First (Layered)

Set up in this order to avoid forward-dependency issues:

1. Labels (required by templates and issues)
2. Issue templates (reference label names)
3. PR template (standalone)
4. Milestones (required by issue migration)
5. Selective migration of active plan docs

---

## Changes

### 1. Label Taxonomy

All 18 labels are created on the FuseCP-Enterprise Gitea repository via the setup script at `scripts/gitea/setup-labels.sh`.

#### Type Labels (6)

| Label | Color (hex) | Description |
|-------|-------------|-------------|
| `feature` | `#0e8a16` | New functionality |
| `enhancement` | `#1d76db` | Improve existing functionality |
| `refactor` | `#5319e7` | Code quality, no behavior change |
| `security` | `#d93f0b` | Security-related |
| `docs` | `#c5def5` | Documentation only |
| `infrastructure` | `#0075ca` | Build, deploy, CI/CD |

#### Priority Labels (4)

| Label | Color (hex) | Description |
|-------|-------------|-------------|
| `P0-critical` | `#b60205` | Production broken, data at risk |
| `P1-high` | `#d93f0b` | Blocks release or major workflow |
| `P2-medium` | `#fbca04` | Should fix this release |
| `P3-low` | `#c5def5` | Nice to have |

#### Component Labels (8)

| Label | Color (hex) | Description |
|-------|-------------|-------------|
| `portal` | `#bfd4f2` | Blazor UI |
| `api` | `#d4c5f9` | EnterpriseServer API |
| `exchange` | `#fef2c0` | Exchange provider |
| `dns` | `#f9d0c4` | DNS provider |
| `ad` | `#c2e0c6` | Active Directory provider |
| `hyperv` | `#e6e6e6` | Hyper-V provider |
| `database` | `#bfdadc` | Schema, migrations, queries |
| `auth` | `#d73a4a` | Authentication, API keys, tenant isolation |

---

### 2. Issue Templates

Directory: `.gitea/issue_template/` in the FuseCP-Enterprise repository.

#### `feature-request.yaml`

- **Name:** Feature Request
- **About:** Propose new functionality
- **Labels applied automatically:** `feature`
- **Body fields:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| Description | textarea | Yes | What is being built |
| Use Case | textarea | Yes | Who needs this and why |
| Component | dropdown | Yes | Portal, API, Exchange, DNS, AD, HyperV, Database, Auth |
| Priority | dropdown | Yes | P0-critical, P1-high, P2-medium, P3-low |
| Acceptance Criteria | textarea | No | How to confirm this is done |
| Tenant Isolation Notes | textarea | No | How this affects multi-tenant isolation |

#### `security-issue.yaml`

- **Name:** Security Issue
- **About:** Report a security concern (non-sensitive details only — communicate sensitive details out-of-band; Gitea has no private security advisories)
- **Labels applied automatically:** `security`
- **Body fields:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| Description | textarea | Yes | What the concern is |
| Attack Vector | textarea | No | How an attacker could exploit this |
| Affected Component | dropdown | Yes | Portal, API, Exchange, DNS, AD, HyperV, Database, Auth |
| Tenant Isolation Impact | dropdown | Yes | None, Single tenant, Cross-tenant, All tenants |
| Severity | dropdown | Yes | Critical, High, Medium, Low |

---

### 3. PR Template

File: `.gitea/pull_request_template.md`

```markdown
## What changed
<!-- Brief description -->

## Why
<!-- Problem solved. Link issue: closes #123 -->

## How to test
<!-- Verification steps -->

## Checklist
- [ ] Tests pass (`dotnet test`)
- [ ] No breaking DB schema changes (additive only)
- [ ] Tenant isolation verified (scoped by PackageId/OrganizationId)
- [ ] Security validated at API layer (not just UI)
- [ ] No hardcoded credentials or connection strings
```

This template auto-populates when any new PR is opened against the repository.

---

### 4. Milestones

Three milestones are created via `scripts/gitea/setup-milestones.sh`:

| Milestone | Purpose |
|-----------|---------|
| `v1.0 — Production Ready` | Core features required for the 2,500-user production deployment |
| `v1.1 — Post-Launch` | Improvements and enhancements planned after initial rollout |
| `Backlog` | Unscheduled ideas and enhancements with no target release |

---

### 5. Selective Migration of Plan Docs

Script: `scripts/gitea/migrate-plans.sh`

The script scans `docs/plans/` and converts active, incomplete feature docs to Gitea Issues. Migration rules:

- **Include:** Docs that describe features not yet fully implemented (detected by absence of a "Completed" or "Done" marker in the document body).
- **Exclude:** Docs marked as completed — they remain as historical references in `docs/plans/`.
- **Exclude:** Vague or exploratory docs with no concrete implementation scope.

Each migrated issue receives:
- One type label (`feature`, `enhancement`, or `refactor`)
- One priority label (`P0-critical` through `P3-low`)
- One or more component labels
- Milestone assignment (`v1.0`, `v1.1`, or `Backlog`)
- The original plan doc content in the issue body, with a reference link to the source file

---

## Files Changed

| File | Change |
|------|--------|
| `.gitea/issue_template/feature-request.yaml` | New — feature request issue template |
| `.gitea/issue_template/security-issue.yaml` | New — security issue template |
| `.gitea/pull_request_template.md` | New — PR checklist |
| `scripts/gitea/setup-labels.sh` | New — creates all 18 labels via Gitea API |
| `scripts/gitea/setup-milestones.sh` | New — creates 3 milestones via Gitea API |
| `scripts/gitea/migrate-plans.sh` | New — scans `docs/plans/` and creates issues via Gitea API |

All files are created in the `fusecp-enterprise` repository at `C:\claude\fusecp-enterprise\`.

---

## Agent Allocation

| Phase | Agent | Responsibility |
|-------|-------|---------------|
| Codebase Research | `agentic-search` (read-only) | Scan `docs/plans/` for migration candidates; classify each as include/exclude and determine label assignments |
| Implementation | `modular-builder` | Create label script, milestone script, issue templates, PR template, and migration script |
| Cleanup | `post-task-cleanup` | Verify labels, templates, and milestones appear correctly on Gitea; verify migration script output |

Turn budgets: `agentic-search` = 10 turns, `modular-builder` = 18 turns, `post-task-cleanup` = 8 turns.

---

## Impact

- **No impact on the existing bug system.** Bugs remain in the custom BugReports API + `/fix-bugs` autonomous pipeline. Gitea Issues are for features, enhancements, and planning only.
- **New feature workflow:** Plan feature as Gitea Issue → assign to milestone → implement on `feature/*` branch → open PR with checklist → merge via Gitea PR.
- **Visibility:** Single dashboard at the Gitea repo's Issues and Milestones pages shows all planned features grouped by release target.

---

## Test Plan

- [ ] All 18 labels visible on Gitea: repo → Issues → Labels
- [ ] Feature Request template appears in "New Issue" dropdown
- [ ] Security Issue template appears in "New Issue" dropdown
- [ ] PR template auto-loads body when creating a new PR
- [ ] Three milestones visible at repo → Milestones
- [ ] Migrated issues have correct type, priority, and component labels
- [ ] Migrated issues are assigned to the correct milestone
- [ ] Completed plan docs are NOT migrated to issues

---

## Acceptance Criteria

1. All 18 labels created on the Gitea repository (6 type + 4 priority + 8 component), verified via the Labels page.
2. Both issue templates render correctly in the New Issue form — fields appear in the specified order with the correct types (textarea, dropdown).
3. PR template auto-populates the PR body on every new pull request.
4. Three milestones exist (`v1.0 — Production Ready`, `v1.1 — Post-Launch`, `Backlog`), visible on the Milestones page.
5. Every active, incomplete plan doc in `docs/plans/` is migrated as a Gitea Issue with at least one type label, one priority label, one component label, and a milestone assignment.
6. No completed plan docs are migrated.
7. No bug-related items are created in Gitea Issues (bugs remain in the BugReports API system).
