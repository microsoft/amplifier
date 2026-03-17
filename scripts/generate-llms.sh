#!/usr/bin/env bash
# Generate llms-full.txt from project documentation
# Run from repo root: bash scripts/generate-llms.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT="$REPO_ROOT/llms-full.txt"

# Files to include (order matters — most important first)
FILES=(
  "CLAUDE.md"
  "AGENTS.md"
  "ai_context/IMPLEMENTATION_PHILOSOPHY.md"
  "ai_context/MODULAR_DESIGN_PHILOSOPHY.md"
  "ai_context/DESIGN-PHILOSOPHY.md"
  "ai_context/DESIGN-PRINCIPLES.md"
  "ai_context/design/DESIGN-FRAMEWORK.md"
  "ai_context/design/DESIGN-VISION.md"
  ".claude/AGENTS_CATALOG.md"
  "docs/DEVELOPER.md"
  "docs/LOCAL_DEVELOPMENT.md"
  "docs/MODULE_DEVELOPMENT.md"
  "docs/MODULES.md"
  "docs/TESTING_GUIDE.md"
  "docs/USER_GUIDE.md"
  "docs/USER_ONBOARDING.md"
  "docs/REPOSITORY_RULES.md"
  "ai_context/claude_code/CLAUDE_CODE_SUBAGENTS.md"
  "ai_context/claude_code/CLAUDE_CODE_HOOKS.md"
  "ai_context/claude_code/CLAUDE_CODE_SETTINGS.md"
  "ai_context/claude_code/CLAUDE_CODE_CLI_REFERENCE.md"
  "ai_context/claude_code/CLAUDE_CODE_COMMON_WORKFLOWS.md"
  "ai_context/claude_code/sdk/CLAUDE_CODE_SDK_OVERVIEW.md"
  "context/ecosystem-overview.md"
  "context/development-hygiene.md"
  "context/recipes-usage.md"
  ".claude/skills/frontend-design/PRINCIPLES.md"
  "ai_context/design/WEB-CODE-ANTIPATTERNS.md"
  "ai_context/design/COLOR-STRATEGY.md"
  "ai_context/design/FONT-PAIRINGS.md"
  "ai_context/design/UX-REVIEW-CHECKLIST.md"
  "config/routing-matrix.yaml"
  "docs/guides/git-workflow.md"
  "README.md"
)

echo "Generating llms-full.txt..."

{
  echo "# Amplifier — Complete Documentation"
  echo ""
  echo "> Auto-generated from project docs. Do not edit manually."
  echo "> Generated: $(date -u '+%Y-%m-%d %H:%M UTC')"
  echo ""

  included=0
  skipped=0

  for file in "${FILES[@]}"; do
    filepath="$REPO_ROOT/$file"
    if [[ -f "$filepath" ]]; then
      echo "---"
      echo ""
      echo "## Source: $file"
      echo ""
      cat "$filepath"
      echo ""
      echo ""
      included=$((included + 1))
    else
      echo "<!-- SKIPPED: $file (not found) -->"
      skipped=$((skipped + 1))
    fi
  done

  echo "---"
  echo ""
  echo "<!-- $included files included, $skipped skipped -->"
} > "$OUTPUT"

size=$(wc -c < "$OUTPUT")
echo "Done: $OUTPUT ($included files, ${size} bytes)"
