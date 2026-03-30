#!/bin/bash
# Verification tests for task-12: Create ecosystem-getting-started skill
# Tests acceptance criteria from the spec.

set -e
cd "$(dirname "$0")/.."

PASS=0
FAIL=0

check() {
    local desc="$1"
    local expect="$2"  # "pass" means command exits 0, "fail" means exits non-zero
    shift 2

    if "$@" > /dev/null 2>&1; then
        result="pass"
    else
        result="fail"
    fi

    if [ "$result" = "$expect" ]; then
        echo "PASS: $desc"
        PASS=$((PASS + 1))
    else
        echo "FAIL: $desc"
        echo "  Expected: $expect | Got: $result"
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
    actual_count=$(grep -c "$pattern" "$file" 2>/dev/null || echo "0")

    if [ "$actual_count" = "$expected_count" ]; then
        echo "PASS: $desc (count=$actual_count)"
        PASS=$((PASS + 1))
    else
        echo "FAIL: $desc"
        echo "  Expected count: $expected_count | Got: $actual_count"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== Task 12: Create ecosystem-getting-started skill - Verification ==="
echo ""

SKILL_FILE="skills/ecosystem-getting-started/SKILL.md"

# AC1: File exists
check "SKILL.md file exists at skills/ecosystem-getting-started/SKILL.md" \
    "pass" test -f "$SKILL_FILE"

# AC2: head -4 shows YAML frontmatter with 'name: ecosystem-getting-started'
check "head -4 contains 'name: ecosystem-getting-started'" \
    "pass" grep -q "name: ecosystem-getting-started" <(head -4 "$SKILL_FILE" 2>/dev/null)

# AC3: grep -c 'For Users' returns 1
check_count "grep -c 'For Users' returns 1" "1" "$SKILL_FILE" "For Users"

# AC4: grep -c 'Deep Dives' returns 1
check_count "grep -c 'Deep Dives' returns 1" "1" "$SKILL_FILE" "Deep Dives"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="

if [ $FAIL -gt 0 ]; then
    exit 1
else
    echo "All checks passed!"
    exit 0
fi
