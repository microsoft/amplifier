#!/bin/bash
# Verification tests for task-15: Main Repo Documentation Sweep
# These tests verify the acceptance criteria for GPT model name updates.

set -e
cd "$(dirname "$0")/.."

PASS=0
FAIL=0

check() {
    local desc="$1"
    local expect_empty="$2"  # "empty" means grep should find nothing (exit 1)
    shift 2
    # Remaining arguments are the command to execute directly (no eval)

    if [ "$expect_empty" = "empty" ]; then
        if "$@" > /dev/null 2>&1; then
            echo "FAIL: $desc"
            echo "  Command found matches when none expected: $*"
            "$@" 2>&1 | head -5
            FAIL=$((FAIL + 1))
        else
            echo "PASS: $desc"
            PASS=$((PASS + 1))
        fi
    else
        # expect_empty = "nonempty" means grep should find matches
        if "$@" > /dev/null 2>&1; then
            echo "PASS: $desc"
            PASS=$((PASS + 1))
        else
            echo "FAIL: $desc"
            echo "  Command found no matches when some expected: $*"
            FAIL=$((FAIL + 1))
        fi
    fi
}

echo "=== Task 15: Main Repo Documentation Sweep - Verification ==="
echo ""

# README.md checks
check "README.md has no gpt-5.1 references" \
    "empty" grep -n "gpt-5\.1" README.md

check "README.md has no gpt-5.2 references" \
    "empty" grep -n "gpt-5\.2" README.md

check "README.md has gpt-5.4 references (replacements applied)" \
    "nonempty" grep -n "gpt-5\.4" README.md

# USER_GUIDE.md checks
check "USER_GUIDE.md has no gpt-5.1 references" \
    "empty" grep -n "gpt-5\.1" docs/USER_GUIDE.md

check "USER_GUIDE.md has gpt-5.4 references (replacements applied)" \
    "nonempty" grep -n "gpt-5\.4" docs/USER_GUIDE.md

# document-generation.yaml checks
check "document-generation.yaml has no gpt-4o references" \
    "empty" grep -n "gpt-4o" recipes/document-generation.yaml

check "document-generation.yaml has gpt-5.4 references" \
    "nonempty" grep -n "gpt-5\.4" recipes/document-generation.yaml

check "document-generation.yaml has gpt-5-mini references (correct replacement)" \
    "nonempty" grep -n "gpt-5-mini" recipes/document-generation.yaml

check "document-generation.yaml does NOT have gpt-5.4-mini (wrong order would create this)" \
    "empty" grep -n "gpt-5\.4-mini" recipes/document-generation.yaml

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="

if [ $FAIL -gt 0 ]; then
    exit 1
else
    echo "All checks passed!"
    exit 0
fi
