#!/bin/bash
# Smoke tests for guard-paths.sh
# Run: bash tests/hooks/test_guard_paths.sh

GUARD="C:/claude/scripts/guard-paths.sh"
PASS=0
FAIL=0

run_test() {
    local desc="$1"
    local input="$2"
    local expect_exit="$3"  # 0=allow, 2=block

    actual_exit=0
    echo "$input" | bash "$GUARD" > /dev/null 2>&1 || actual_exit=$?

    if [ "$actual_exit" -eq "$expect_exit" ]; then
        echo "  PASS: $desc"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $desc (expected exit=$expect_exit, got exit=$actual_exit)"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== guard-paths.sh smoke tests ==="

# Write tool tests
run_test "Allow Write to C:\\claude\\amplifier\\test.py" \
    '{"tool_name":"Write","tool_input":{"file_path":"C:\\claude\\amplifier\\test.py"}}' 0

run_test "Allow Write to C:\\Users\\test\\file.txt" \
    '{"tool_name":"Write","tool_input":{"file_path":"C:\\Users\\test\\file.txt"}}' 0

run_test "Block Write to C:\\Windows\\test.txt" \
    '{"tool_name":"Write","tool_input":{"file_path":"C:\\Windows\\test.txt"}}' 2

run_test "Block Write to C:\\random\\file.txt" \
    '{"tool_name":"Write","tool_input":{"file_path":"C:\\random\\file.txt"}}' 2

# Bash tool tests — mkdir
run_test "Allow Bash mkdir under /c/claude" \
    '{"tool_name":"Bash","tool_input":{"command":"mkdir -p /c/claude/tmp/test"}}' 0

run_test "Block Bash mkdir under /c/badpath" \
    '{"tool_name":"Bash","tool_input":{"command":"mkdir /c/badpath"}}' 2

# Bash tool tests — redirect
run_test "Allow Bash redirect to /c/claude" \
    '{"tool_name":"Bash","tool_input":{"command":"echo hi > /c/claude/test.txt"}}' 0

run_test "Block Bash redirect to /c/badpath" \
    '{"tool_name":"Bash","tool_input":{"command":"echo hi > /c/badpath/test.txt"}}' 2

# Other tools pass through
run_test "Allow Read tool (passthrough)" \
    '{"tool_name":"Read","tool_input":{"file_path":"C:\\anywhere\\file.txt"}}' 0

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
