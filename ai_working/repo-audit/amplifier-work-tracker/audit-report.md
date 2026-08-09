# Repository Audit Report: microsoft/amplifier-work-tracker

**Audit Date**: 2026-08-09
**Repository URL**: https://github.com/microsoft/amplifier-work-tracker

## Summary

| Check | Status | Severity |
|-------|--------|----------|
| Listed in MODULES.md | Recommendation | recommendation |
| CODE_OF_CONDUCT.md | Mismatch | error |
| SECURITY.md | Mismatch | error |
| SUPPORT.md | Mismatch | error |
| LICENSE | Mismatch | error |
| README Contributing | Mismatch | warning |
| README Trademarks | Mismatch | warning |
| GitHub Issues | Disabled | pass |
| Wiki | Disabled | pass |
| Projects | Disabled | pass |
| Branch Protection | Misconfigured | error |
| Bypass Actors | N-A | warning |
| PR Rule Strictness | Deviates | warning |
| Dependabot PRs | 0 open — see below | pass |

**Overall Status**: CRITICAL
- Critical issues (errors): 5
- Warnings: 3
- Recommendations: 1

## Detailed Findings

### 1. MODULES.md Listing — Recommendation

The repository is **not listed** in `amplifier/docs/MODULES.md`. Adding it improves ecosystem discoverability so contributors and agents can find the work tracker through the canonical module catalog rather than by chance.

### 2. Boilerplate Files — 4 Errors

All four required boilerplate files are **present but do not match** the Microsoft canonical templates:

| File | Status | Match |
|------|--------|-------|
| `CODE_OF_CONDUCT.md` | present | ✗ differs from template |
| `SECURITY.md` | present | ✗ differs from template |
| `SUPPORT.md` | present | ✗ differs from template |
| `LICENSE` | present | ✗ differs from template |

Content drift in these files is a compliance concern, not a stylistic one. `SECURITY.md` in particular governs how vulnerability reports reach MSRC — a divergent version can route reports incorrectly. `LICENSE` divergence has legal implications and should be treated as the highest-priority item in this group.

### 3. README.md Sections — 2 Warnings

`README.md` exists and contains both a Contributing section and a Trademarks section, but neither matches the verbatim template text. The sections are present (so the structural requirement is met), which is why these are warnings rather than errors. Verbatim text matters here because the CLA bot language and the Microsoft trademark guidance URL are both load-bearing.

### 4. GitHub Issues — Pass

Issues are disabled. This is the recommended configuration for non-primary repositories in the ecosystem; issue intake is centralized.

### 5. Wiki — Pass

Wiki is disabled, as required.

### 6. Projects — Pass

Projects is disabled, as required.

### 7. Branch Protection — Error

A repository ruleset **is** present on the default branch (`main`), but **no `pull_request` rule requires approving reviews**. The practical effect: a PR can be merged into `main` with zero human review. The ruleset gives the appearance of protection without the substance of it — this is more dangerous than no ruleset at all, because it can pass a superficial "is protection configured?" check.

### 8. Bypass Actors — Warning

Bypass actors **cannot be evaluated** because the required-review rule that would be bypassed does not exist yet (see Branch Protection above). This check is blocked, not passing. Re-run the audit after the ruleset is corrected to get a real verdict on bypass configuration.

### 9. PR Rule Strictness — Warning

The PR rule configuration on `main` deviates from the canonical `amplifier-*` pattern. Missing:

- `dismiss_stale_reviews_on_push = true` — without this, an approval survives subsequent pushes, so reviewed code and merged code can differ
- `required_review_thread_resolution = true` — without this, unresolved review conversations do not block merge
- `required_linear_history` rule — absent, so merge commits can enter `main`

Canonical pattern for reference: `dismiss_stale_reviews_on_push=true`, `required_review_thread_resolution=true`, `required_linear_history` rule present.

### 10. Dependabot — Pass

No open Dependabot PRs, and no open security-update PRs.

## Repository Activity

- **Open PRs**: 0
- **Recent commits (7d)**: 4
- **Last push**: 2026-08-09T23:25:54Z

The repository is actively developed (4 commits in the last 7 days) with no open PRs. Combined with the missing required-review rule, this means recent commits may have landed on `main` without review — worth confirming during remediation.

## Dependabot Pull Requests

No open Dependabot PRs.

Recommendations are advisory — a human decides and performs any merge. This recipe does not merge PRs.

## Remediation Steps

Ordered by severity and blast radius.

### Priority 1 — Branch protection (error, blocks #8)

Update the existing ruleset on `main` to add a `pull_request` rule requiring at least 1 approving review. In the same edit, close the strictness gaps from check #9 so the ruleset only has to be touched once:

```
Repository → Settings → Rules → Rulesets → [existing ruleset on main] → Edit

Enable "Require a pull request before merging":
  ☑ Required approvals: 1
  ☑ Dismiss stale pull request approvals when new commits are pushed
  ☑ Require conversation resolution before merging

Add rule:
  ☑ Require linear history
```

Or via the API:

```bash
gh api -X PUT repos/microsoft/amplifier-work-tracker/rulesets/<ruleset-id> \
  --input ruleset.json
```

where `ruleset.json` sets `rules[].type: "pull_request"` with `required_approving_review_count: 1`, `dismiss_stale_reviews_on_push: true`, `required_review_thread_resolution: true`, plus a `rules[].type: "required_linear_history"` entry.

### Priority 2 — LICENSE (error)

Replace `LICENSE` with the canonical Microsoft MIT license text. Legal implications make this the highest-priority boilerplate item. Diff the current file against the template before replacing to confirm the divergence is unintentional (a deliberate license choice would be a decision to escalate, not a file to overwrite).

### Priority 3 — SECURITY.md (error)

Replace with the canonical Microsoft `SECURITY.md`. This file directs vulnerability reports to MSRC; divergence risks misrouted security disclosures.

### Priority 4 — CODE_OF_CONDUCT.md and SUPPORT.md (errors)

Replace both with the canonical Microsoft templates.

### Priority 5 — README sections (warnings)

Replace the Contributing and Trademarks sections with the verbatim template text, preserving the rest of the README. The CLA bot instructions and the trademark guidance link must match exactly.

### Priority 6 — MODULES.md listing (recommendation)

Add an entry for `amplifier-work-tracker` in `amplifier/docs/MODULES.md` with a one-line description ("Work Tracker for the Amplifier project") and repository URL.

### Verification

After remediation, re-run this audit. Check #8 (Bypass Actors) will produce a real verdict only once the required-review rule exists — treat it as an open item until that re-run completes, not as resolved by the Priority 1 fix alone.

---
*Generated by Amplifier repo-audit recipe v1.8.0*
