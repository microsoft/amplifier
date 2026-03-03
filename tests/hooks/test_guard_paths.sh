#!/bin/bash
# Smoke tests for guard-paths.sh
# Run: bash tests/hooks/test_guard_paths.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
. "$REPO_ROOT/scripts/lib/platform.sh"

# Use platform-appropriate guard script
if [ "$AMPLIFIER_PLATFORM" = "linux" ]; then
    GUARD="$AMPLIFIER_HOME/scripts/guard-paths-linux.sh"
else
    GUARD="$AMPLIFIER_HOME/scripts/guard-paths.sh"
fi
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

if [ "$AMPLIFIER_PLATFORM" = "linux" ]; then
    # Linux test cases
    run_test "Allow Write to /opt/amplifier/test.py" \
        '{"tool_name":"Write","tool_input":{"file_path":"/opt/amplifier/test.py"}}' 0

    run_test "Allow Write to $HOME/file.txt" \
        "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$HOME/file.txt\"}}" 0

    run_test "Block Write to /etc/passwd" \
        '{"tool_name":"Write","tool_input":{"file_path":"/etc/passwd"}}' 2

    run_test "Block Write to /usr/local/file.txt" \
        '{"tool_name":"Write","tool_input":{"file_path":"/usr/local/file.txt"}}' 2

    run_test "Allow Bash mkdir under /opt" \
        '{"tool_name":"Bash","tool_input":{"command":"mkdir -p /opt/amplifier/tmp/test"}}' 0

    run_test "Block Bash mkdir under /etc" \
        '{"tool_name":"Bash","tool_input":{"command":"mkdir /etc/badpath"}}' 2

    run_test "Allow Bash redirect to /opt" \
        '{"tool_name":"Bash","tool_input":{"command":"echo hi > /opt/amplifier/test.txt"}}' 0

    run_test "Block Bash redirect to /usr" \
        '{"tool_name":"Bash","tool_input":{"command":"echo hi > /usr/badpath/test.txt"}}' 2

    run_test "Allow Read tool (passthrough)" \
        '{"tool_name":"Read","tool_input":{"file_path":"/anywhere/file.txt"}}' 0
else
    # Windows test cases (original)
    run_test "Allow Write to C:\\claude\\amplifier\\test.py" \
        '{"tool_name":"Write","tool_input":{"file_path":"C:\\claude\\amplifier\\test.py"}}' 0

    run_test "Allow Write to C:\\Users\\test\\file.txt" \
        '{"tool_name":"Write","tool_input":{"file_path":"C:\\Users\\test\\file.txt"}}' 0

    run_test "Block Write to C:\\Windows\\test.txt" \
        '{"tool_name":"Write","tool_input":{"file_path":"C:\\Windows\\test.txt"}}' 2

    run_test "Block Write to C:\\random\\file.txt" \
        '{"tool_name":"Write","tool_input":{"file_path":"C:\\random\\file.txt"}}' 2

    run_test "Allow Bash mkdir under /c/claude" \
        '{"tool_name":"Bash","tool_input":{"command":"mkdir -p /c/claude/tmp/test"}}' 0

    run_test "Block Bash mkdir under /c/badpath" \
        '{"tool_name":"Bash","tool_input":{"command":"mkdir /c/badpath"}}' 2

    run_test "Allow Bash redirect to /c/claude" \
        '{"tool_name":"Bash","tool_input":{"command":"echo hi > /c/claude/test.txt"}}' 0

    run_test "Block Bash redirect to /c/badpath" \
        '{"tool_name":"Bash","tool_input":{"command":"echo hi > /c/badpath/test.txt"}}' 2

    run_test "Allow Read tool (passthrough)" \
        '{"tool_name":"Read","tool_input":{"file_path":"C:\\anywhere\\file.txt"}}' 0
fi

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
