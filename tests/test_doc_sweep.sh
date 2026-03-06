#!/bin/bash
# Verification tests for task-15: Main Repo Documentation Sweep
# These tests verify the acceptance criteria for GPT model name updates.

set -e
cd "$(dirname "$0")/.."

PASS=0
FAIL=0

check() {
    local desc="$1"
    local cmd="$2"
    local expect_empty="$3"  # "empty" means grep should find nothing (exit 1)

    if [ "$expect_empty" = "empty" ]; then
        if eval "$cmd" > /dev/null 2>&1; then
            echo "FAIL: $desc"
            echo "  Command found matches when none expected: $cmd"
            eval "$cmd" 2>&1 | head -5
            FAIL=$((FAIL + 1))
        else
            echo "PASS: $desc"
            PASS=$((PASS + 1))
        fi
    else
        # expect_empty = "nonempty" means grep should find matches
        if eval "$cmd" > /dev/null 2>&1; then
            echo "PASS: $desc"
            PASS=$((PASS + 1))
        else
            echo "FAIL: $desc"
            echo "  Command found no matches when some expected: $cmd"
            FAIL=$((FAIL + 1))
        fi
    fi
}

echo "=== Task 15: Main Repo Documentation Sweep - Verification ==="
echo ""

# README.md checks
check "README.md has no gpt-5.1 references" \
    'grep -n "gpt-5\.1" README.md' "empty"

check "README.md has no gpt-5.2 references" \
    'grep -n "gpt-5\.2" README.md' "empty"

check "README.md has gpt-5.4 references (replacements applied)" \
    'grep -n "gpt-5\.4" README.md' "nonempty"

# USER_GUIDE.md checks
check "USER_GUIDE.md has no gpt-5.1 references" \
    'grep -n "gpt-5\.1" docs/USER_GUIDE.md' "empty"

check "USER_GUIDE.md has gpt-5.4 references (replacements applied)" \
    'grep -n "gpt-5\.4" docs/USER_GUIDE.md' "nonempty"

# document-generation.yaml checks
check "document-generation.yaml has no gpt-4o references" \
    'grep -n "gpt-4o" recipes/document-generation.yaml' "empty"

check "document-generation.yaml has gpt-5.4 references" \
    'grep -n "gpt-5\.4" recipes/document-generation.yaml' "nonempty"

check "document-generation.yaml has gpt-5-mini references (correct replacement)" \
    'grep -n "gpt-5-mini" recipes/document-generation.yaml' "nonempty"

check "document-generation.yaml does NOT have gpt-5.4-mini (wrong order would create this)" \
    'grep -n "gpt-5\.4-mini" recipes/document-generation.yaml' "empty"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="

if [ $FAIL -gt 0 ]; then
    exit 1
else
    echo "All checks passed!"
    exit 0
fi
