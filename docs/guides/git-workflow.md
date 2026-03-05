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

## Gitea MCP Tools (Preferred)

**Use Gitea MCP tools (`mcp__gitea__*`) for all Gitea operations.** MCP tools are native tool calls — they support parallel execution, work in subagents without Bash, and return structured data.

### Common Operations

| Operation | MCP Tool |
|-----------|----------|
| Create PR | `mcp__gitea__create_pull_request(owner, repo, title, body, head, base)` |
| List PRs | `mcp__gitea__list_repo_pull_requests(owner, repo, state)` |
| View PR | `mcp__gitea__get_pull_request_by_index(owner, repo, index)` |
| PR diff | `mcp__gitea__get_pull_request_diff(owner, repo, index)` |
| Merge PR | `mcp__gitea__merge_pull_request(owner, repo, index, Do)` |
| PR review | `mcp__gitea__create_pull_request_review(owner, repo, index, body, state)` |
| Create issue | `mcp__gitea__create_issue(owner, repo, title, body)` |
| List issues | `mcp__gitea__list_repo_issues(owner, repo, state)` |
| Comment | `mcp__gitea__create_issue_comment(owner, repo, index, body)` |
| Labels | `mcp__gitea__add_issue_labels(owner, repo, index, labels)` |
| Milestones | `mcp__gitea__list_milestones(owner, repo)` |
| List repos | `mcp__gitea__list_my_repos()` |

All `owner` params = `"admin"` for our repos. `Do` param for merge: `"merge"`, `"squash"`, or `"rebase"`.

### Fallback: tea CLI

Use `tea` CLI when MCP is unavailable (e.g., MCP server down, interactive terminal use).

- Binary: `C:\claude\tools\tea.exe` (v0.12.0)
- Login: `claude-gitea` → `https://gitea.ergonet.pl:3001` (token-based)

```bash
tea pr create --repo admin/<repo> --title "feat: my change" --head feature/branch --base main --description "Details"
tea pr ls --repo admin/<repo>
tea pr merge --repo admin/<repo> --style squash <number>
tea comment --repo admin/<repo> <number> "Review feedback here"
```

Never use PowerShell `Invoke-RestMethod` or `curl` for routine Gitea operations.

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
