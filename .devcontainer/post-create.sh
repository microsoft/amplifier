#!/usr/bin/env bash
set -euo pipefail

# echo "📦  Ensuring git-collector is available…"
# if command -v git-collector >/dev/null 2>&1; then
#   echo "    git-collector already installed; skipping."
# else
#   npm install -g git-collector
# fi

echo "🔧  Configuring Git to auto-create upstream on first push…"
git config --global push.autoSetupRemote true

echo "✅  Post-create tasks complete."
