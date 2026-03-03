#!/usr/bin/env bash
# Create a PR on Gitea using tea CLI.
# Usage: bash gitea-create-pr.sh --title "feat: my change" --head "feature/branch" [--base main] [--body "description"] [--repo owner/repo]
#
# Replaces the former PowerShell gitea-create-pr.ps1 script.
# Requires: tea CLI installed and configured (`tea login add`)

set -euo pipefail

REPO=""
TITLE=""
HEAD=""
BASE="main"
BODY=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --title|-t) TITLE="$2"; shift 2 ;;
    --head|-h)  HEAD="$2"; shift 2 ;;
    --base|-b)  BASE="$2"; shift 2 ;;
    --body|-d)  BODY="$2"; shift 2 ;;
    --repo|-r)  REPO="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$TITLE" || -z "$HEAD" ]]; then
  echo "Usage: gitea-create-pr.sh --title \"PR title\" --head \"branch-name\" [--base main] [--body \"desc\"] [--repo owner/repo]" >&2
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

# Build tea command
CMD=(tea pr create --repo "$REPO" --title "$TITLE" --head "$HEAD" --base "$BASE")
if [[ -n "$BODY" ]]; then
  CMD+=(--description "$BODY")
fi

"${CMD[@]}"
