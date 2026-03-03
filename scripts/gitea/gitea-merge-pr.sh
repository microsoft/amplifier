#!/usr/bin/env bash
# Merge a PR on Gitea using tea CLI.
# Usage: bash gitea-merge-pr.sh <pr-number> [--style merge|squash|rebase] [--repo owner/repo]
#
# Replaces the former PowerShell gitea-merge-pr.ps1 script.
# Requires: tea CLI installed and configured (`tea login add`)

set -euo pipefail

PR_NUMBER=""
STYLE="merge"
REPO=""

# Parse args
while [[ $# -gt 0 ]]; do
  case $1 in
    --style|-s) STYLE="$2"; shift 2 ;;
    --repo|-r)  REPO="$2"; shift 2 ;;
    [0-9]*)     PR_NUMBER="$1"; shift ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$PR_NUMBER" ]]; then
  echo "Usage: gitea-merge-pr.sh <pr-number> [--style merge|squash|rebase] [--repo owner/repo]" >&2
  exit 1
fi

# Auto-detect repo from git remote if not provided
if [[ -z "$REPO" ]]; then
  REMOTE_URL=$(git remote get-url origin 2>/dev/null || true)
  if [[ "$REMOTE_URL" =~ gitea\.ergonet\.pl:3001/(.+?)(\.git)?$ ]]; then
    REPO="${BASH_REMATCH[1]}"
    echo "Auto-detected repo: $REPO"
  else
    echo "ERROR: Could not detect Gitea repo from origin remote. Pass --repo owner/repo" >&2
    exit 1
  fi
fi

tea pr merge --repo "$REPO" --style "$STYLE" "$PR_NUMBER"
echo "PR #$PR_NUMBER merged successfully ($STYLE)"
