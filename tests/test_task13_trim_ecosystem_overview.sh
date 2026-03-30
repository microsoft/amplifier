#!/bin/bash
# Verification tests for task-13: Trim ecosystem-overview.md
# Tests acceptance criteria from the spec.

cd "$(dirname "$0")/.."

PASS=0
FAIL=0

check() {
    local desc="$1"
    local expect="$2"  # 0 means command exits 0 (success), 1 means exits non-zero
    local result
    shift 2

    if "$@" > /dev/null 2>&1; then
        result=0
    else
        result=1
    fi

    if [ "$result" = "$expect" ]; then
        echo "PASS: $desc"
        PASS=$((PASS + 1))
    else
        echo "FAIL: $desc"
        echo "  Expected exit: $expect | Got: $result"
        echo "  Command: $*"
        FAIL=$((FAIL + 1))
    fi
}

check_count() {
    local desc="$1"
    local expected_count="$2"
    local file="$3"
    local pattern="$4"

    local actual_count
    actual_count=$(grep -c "$pattern" "$file" 2>/dev/null) || actual_count="0"

    if [ "$actual_count" -eq "$expected_count" ]; then
        echo "PASS: $desc (count=$actual_count)"
        PASS=$((PASS + 1))
    else
        echo "FAIL: $desc"
        echo "  Expected count: $expected_count | Got: $actual_count"
        echo "  Pattern: $pattern"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== Task 13: Trim ecosystem-overview.md - Verification ==="
echo ""

FILE="context/ecosystem-overview.md"

# AC1: grep -c 'anthropic, openai, azure' returns 0 (module type table removed)
check_count "grep -c 'anthropic, openai, azure' returns 0" "0" "$FILE" "anthropic, openai, azure"

# AC2: grep 'Foundation Awareness Index' shows replacement one-liner
check "grep 'Foundation Awareness Index' finds replacement one-liner" \
    0 grep -q "Foundation Awareness Index" "$FILE"

# AC3: grep -c 'Getting Started Paths' returns 0 (old section removed)
check_count "grep -c 'Getting Started Paths' returns 0" "0" "$FILE" "Getting Started Paths"

# AC4: grep 'load_skill.*ecosystem-getting-started' shows skill pointer
check "grep 'load_skill.*ecosystem-getting-started' shows skill pointer" \
    0 grep -q "load_skill.*ecosystem-getting-started" "$FILE"

# AC5: grep -c 'What is Amplifier' returns 1 (preserved)
check_count "grep -c 'What is Amplifier' returns 1" "1" "$FILE" "What is Amplifier"

# AC6: grep -c 'Mechanism, Not Policy' returns 1 (preserved)
check_count "grep -c 'Mechanism, Not Policy' returns 1" "1" "$FILE" "Mechanism, Not Policy"

# AC7: grep -c 'Ecosystem Activity Report' returns 1 (preserved)
check_count "grep -c 'Ecosystem Activity Report' returns 1" "1" "$FILE" "Ecosystem Activity Report"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="

if [ $FAIL -gt 0 ]; then
    exit 1
else
    echo "All checks passed!"
    exit 0
fi
