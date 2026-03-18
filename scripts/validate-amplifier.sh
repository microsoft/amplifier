#!/usr/bin/env bash
# validate-amplifier.sh — Amplifier health check
# Validates commands, hooks, agents, and config integrity.
# No -e: arithmetic ((PASS++)) returns exit code 1 when PASS was 0, which would abort
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$REPO_ROOT"

PASS=0
FAIL=0
WARN=0

check() {
    local label="$1" result="$2"
    if [[ "$result" == "pass" ]]; then
        echo "  PASS: $label"
        ((PASS++))
    elif [[ "$result" == "warn" ]]; then
        echo "  WARN: $label"
        ((WARN++))
    else
        echo "  FAIL: $label"
        ((FAIL++))
    fi
}

echo "=== Amplifier Health Check ==="
echo ""

# 1. Commands have valid frontmatter
echo "--- Commands ---"
for cmd in "$HOME/.claude/plugins/marketplaces/amplifier-marketplace/amplifier-core/commands/"*.md; do
    name=$(basename "$cmd" .md)
    if head -1 "$cmd" | grep -q "^---"; then
        check "$name: frontmatter present" "pass"
    else
        check "$name: missing frontmatter (---)" "warn"
    fi
done
echo ""

# 2. Hook scripts exist (use process substitution to avoid subshell counter loss)
echo "--- Hook Scripts ---"
while read -r script; do
    # Extract just the script path (after bash or cd commands)
    script_path=$(echo "$script" | sed 's/^bash //' | sed "s/^bash -c '.*//")
    # Skip empty lines or inline bash -c commands
    [[ -z "$script_path" || "$script_path" == *"-c "* ]] && continue
    if [[ -f "$script_path" ]]; then
        check "$(basename "$script_path"): exists" "pass"
    else
        check "$(basename "$script_path"): NOT FOUND ($script_path)" "fail"
    fi
done < <(grep -oE '"command": "[^"]*"' .claude/settings.json | sed 's/"command": "//;s/"$//' | grep -v "uv run\|callback" | sed 's/.*&& //')
echo ""

# 3. Routing matrix
echo "--- Routing Matrix ---"
if [[ -f "config/routing-matrix.yaml" ]]; then
    check "routing-matrix.yaml exists" "pass"
    AGENT_COUNT=$(grep -cE "^  [a-z].*: [a-z]" config/routing-matrix.yaml || echo "0")
    check "agents mapped: $AGENT_COUNT" "pass"
else
    check "routing-matrix.yaml missing" "fail"
fi
echo ""

# 4. MCP servers
echo "--- MCP Servers ---"
if [[ -f ".mcp.json" ]]; then
    SERVERS=$(grep -oE '"[a-z]+":' .mcp.json | tr -d '":' | grep -v mcpServers)
    echo "$SERVERS" | while read -r server; do
        check "MCP server: $server" "pass"
    done
else
    check ".mcp.json missing" "fail"
fi
echo ""

# 5. Observer scripts
echo "--- Observers ---"
for obs in scripts/observers/*.sh; do
    if [[ -f "$obs" ]]; then
        name=$(basename "$obs")
        if head -5 "$obs" | grep -q "jq"; then
            if command -v jq &>/dev/null; then
                check "$name: jq available" "pass"
            else
                check "$name: jq NOT installed (observer disabled)" "warn"
            fi
        else
            check "$name: no jq dependency" "pass"
        fi
    fi
done
echo ""

# Summary
TOTAL=$((PASS + FAIL + WARN))
echo "=== Summary ==="
echo "Health: $PASS/$TOTAL checks pass ($WARN warnings, $FAIL failures)"

if [[ "$FAIL" -gt 0 ]]; then
    exit 1
fi
