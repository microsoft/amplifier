#!/usr/bin/env bash
# validate-routing-matrix.sh — Cross-check routing matrix against agent catalog and agent files
set -euo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$REPO_ROOT"

MATRIX="config/routing-matrix.yaml"
CATALOG=".claude/AGENTS_CATALOG.md"
AGENTS_DIR="$HOME/.claude/plugins/marketplaces/amplifier-marketplace/amplifier-core/agents"
ERRORS=0
WARNINGS=0

echo "=== Routing Matrix Validation ==="
echo ""

# 1. Check matrix exists
if [[ ! -f "$MATRIX" ]]; then
    echo "FAIL: $MATRIX not found"
    exit 1
fi

# 2. Extract agents from routing matrix (only lines after "agents:" section, skip role definitions)
MATRIX_AGENTS=$(sed -n '/^agents:/,$ p' "$MATRIX" | grep -E "^  [a-z]" | sed 's/:.*//' | tr -d ' ' | sort)

# 3. Extract agents from catalog (backtick-wrapped names from agent tables, skip Model Tier Mapping)
CATALOG_AGENTS=$(sed '/## Model Tier Mapping/,$ d' "$CATALOG" | grep -E '^\| `[a-z]' | sed 's/.*`\([a-z][a-z_-]*\)`.*/\1/' | sed 's/ .*//' | sort -u)

# 4. Extract agent definition files
if [[ -d "$AGENTS_DIR" ]]; then
    FILE_AGENTS=$(ls "$AGENTS_DIR"/*.md 2>/dev/null | xargs -I{} basename {} .md | sort)
else
    FILE_AGENTS=""
fi

# 5. Check: agents in catalog but not in matrix
echo "--- Agents in catalog but NOT in routing matrix ---"
MISSING=$(comm -23 <(echo "$CATALOG_AGENTS") <(echo "$MATRIX_AGENTS"))
if [[ -n "$MISSING" ]]; then
    echo "$MISSING" | while read -r agent; do
        echo "  WARN: $agent (in catalog, missing from matrix)"
        ((WARNINGS++)) || true
    done
else
    echo "  (none — all catalog agents are in matrix)"
fi
echo ""

# 6. Check: agents in matrix but not in catalog
echo "--- Agents in routing matrix but NOT in catalog ---"
EXTRA=$(comm -13 <(echo "$CATALOG_AGENTS") <(echo "$MATRIX_AGENTS"))
if [[ -n "$EXTRA" ]]; then
    echo "$EXTRA" | while read -r agent; do
        echo "  WARN: $agent (in matrix, missing from catalog)"
        ((WARNINGS++)) || true
    done
else
    echo "  (none — all matrix agents are in catalog)"
fi
echo ""

# 7. Check: agent files without matrix entry
if [[ -n "$FILE_AGENTS" ]]; then
    echo "--- Agent files without routing matrix entry ---"
    UNMATCHED=$(comm -23 <(echo "$FILE_AGENTS") <(echo "$MATRIX_AGENTS"))
    if [[ -n "$UNMATCHED" ]]; then
        echo "$UNMATCHED" | while read -r agent; do
            echo "  INFO: $agent (has .md file, not in matrix)"
        done
    else
        echo "  (none — all agent files have matrix entries)"
    fi
    echo ""
fi

# 8. Check: roles referenced by agents exist in roles section
echo "--- Role validation ---"
DEFINED_ROLES=$(grep -E "^  [a-z].*:" "$MATRIX" | head -20 | sed 's/:.*//' | tr -d ' ' | grep -v "^agents$" | sort)
USED_ROLES=$(grep -E "^  [a-z].*: [a-z]" "$MATRIX" | sed 's/.*: //' | sed 's/ .*//' | sort -u)
INVALID_ROLES=$(comm -23 <(echo "$USED_ROLES") <(echo "$DEFINED_ROLES"))
if [[ -n "$INVALID_ROLES" ]]; then
    echo "$INVALID_ROLES" | while read -r role; do
        echo "  ERROR: role '$role' used but not defined"
        ((ERRORS++)) || true
    done
else
    echo "  (all roles valid)"
fi
echo ""

# Summary
TOTAL_MATRIX=$(echo "$MATRIX_AGENTS" | wc -l | tr -d ' ')
TOTAL_CATALOG=$(echo "$CATALOG_AGENTS" | wc -l | tr -d ' ')
echo "=== Summary ==="
echo "Matrix agents: $TOTAL_MATRIX"
echo "Catalog agents: $TOTAL_CATALOG"
echo "Errors: $ERRORS | Warnings: $WARNINGS"

if [[ "$ERRORS" -gt 0 ]]; then
    exit 1
fi
