# Git Workflow Guide

On-demand reference for git commit messages, PR policy, Gitea workflow, and branch protection. Retrieved via `/docs search git workflow`.

---

## Git Commit Message Guidelines

When creating git commit messages, always insert the following at the end of your commit message:

```
🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>
```

---

## PR-First Policy (CRITICAL)

**All completed work MUST go through a Pull Request. Never commit directly to main/master.**

### Rules

1. **Start on a feature branch** — Before any implementation work, create or verify you're on a feature branch (`feature/<name>`, `fix/<name>`, etc.). Never start work on main.
2. **End with a PR** — When work is complete, push the branch and create a PR. This is the default, not an option to choose.
3. **Never push to main** — Direct pushes to main are prohibited. If you find yourself on main with uncommitted work, create a branch first.
4. **Never merge without user confirmation** — Present the PR URL and wait for the user to approve the merge.

### Enforcement Points

- `/subagent-dev` has a **Branch Gate** that blocks execution on main
- `/finish-branch` defaults to creating a PR (no menu of options)
- `/brainstorm` → `/create-plan` → `/worktree` flow ensures a feature branch exists before implementation

### Recovery (if work accidentally lands on main)

```bash
git branch feature/<name>
git reset --hard <pre-work-commit>
git push -u origin feature/<name>
tea pr create --repo admin/<repo> --title "feat: <name>" --head feature/<name>
```

---

## Gitea CLI: tea (Preferred Tool)

**Always prefer `tea` over direct API calls for Gitea operations.** The `tea` CLI handles authentication, SSL, and JSON formatting automatically.

### Setup
- Binary: `C:\claude\tools\tea.exe` (v0.12.0)
- Login: `gitea` → `https://gitea.ergonet.pl:3001` (token-based)
- Default login set: `tea login default gitea`

### Common Operations

```bash
# List repos
tea repos ls

# Create PR
tea pr create --repo admin/<repo> --title "feat: my change" --head feature/branch --base main --description "Details"

# List PRs
tea pr ls --repo admin/<repo>
tea pr ls --repo admin/<repo> --state closed   # show merged/closed

# View PR details
tea pr view --repo admin/<repo> <number>

# Merge PR
tea pr merge --repo admin/<repo> <number>
tea pr merge --repo admin/<repo> --style squash <number>   # squash merge

# Comment on PR/issue
tea comment --repo admin/<repo> <number> "Review feedback here"
```

### When to Fall Back to API

Only use direct REST API calls when tea doesn't support a specific operation (rare). Never use PowerShell `Invoke-RestMethod` or `curl` for routine PR operations — tea is simpler and cross-platform.

---

## Git Workflow — Gitea-First (Two-Stage)

**PRIMARY remote**: Gitea at https://gitea.ergonet.pl:3001/ (HTTPS, port 3001)
**BACKUP remote**: GitHub at https://github.com/psklarkins/ (push mirror, auto-syncs on commit)

### Remote Layout (all locally cloned repos)
- `origin` → Gitea (primary, all day-to-day pushes go here)
- `github` → GitHub (backup, never push manually — Gitea mirrors automatically)

### Daily Workflow
1. Work and commit locally as usual
2. Push to `origin` (Gitea): `git push origin feature/my-feature`
3. Open PR on Gitea: https://gitea.ergonet.pl:3001/admin/{repo}/pulls
4. Merge PR on Gitea — push mirror triggers GitHub backup automatically
5. Never push directly to `main`/`master`/`develop` — branch protection enforced

### Branch Protection Rules (all 19 repos)
- Direct push to default branch is BLOCKED
- PR is required to merge
- 0 approvals required (solo dev)
- Status checks: disabled (no CI configured on Gitea yet)

### GitHub Actions
- GitHub Actions runner at C:\actions-runner\ still runs CI on GitHub
- When Gitea push mirror syncs, GitHub Actions fires on the mirrored commits
- This provides CI coverage without needing Gitea Actions
