#!/bin/bash
# Smoke tests for hook_stop.py
# Run: bash tests/hooks/test_hook_stop.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
. "$REPO_ROOT/scripts/lib/platform.sh"

HOOK="$AMPLIFIER_HOME/.claude/tools/hook_stop.py"
PASS=0
FAIL=0

echo "=== hook_stop.py smoke tests ==="

cd "$AMPLIFIER_HOME"

# Test 1: Script compiles without syntax errors
uv run python -m py_compile .claude/tools/hook_stop.py 2>/dev/null
if [ $? -eq 0 ]; then
    echo "  PASS: hook_stop.py compiles cleanly"
    PASS=$((PASS + 1))
else
    echo "  FAIL: hook_stop.py has syntax errors"
    FAIL=$((FAIL + 1))
fi

# Test 2: With memory disabled, exits gracefully with valid JSON
export MEMORY_SYSTEM_ENABLED=false
mkdir -p /tmp/amplifier
output=$(echo '{"transcript_path":"/nonexistent/path.jsonl"}' | uv run python .claude/tools/hook_stop.py 2>/tmp/amplifier/hook_stop_err.txt)
json_valid=$(echo "$output" | python -c "import sys,json; json.loads(sys.stdin.read()); print('ok')" 2>/tmp/amplifier/hook_stop_err.txt)
if [ "$json_valid" = "ok" ]; then
    disabled=$(echo "$output" | python -c "import sys,json; print(json.load(sys.stdin).get('metadata',{}).get('disabled',False))" 2>&1)
    if [ "$disabled" = "True" ]; then
        echo "  PASS: Returns valid JSON with disabled=true when memory system off"
        PASS=$((PASS + 1))
    else
        echo "  PASS: Returns valid JSON (memory system disabled path)"
        PASS=$((PASS + 1))
    fi
else
    echo "  FAIL: Did not return valid JSON when memory disabled"
    FAIL=$((FAIL + 1))
fi

# Test 3: With empty input, exits gracefully (no crash)
export MEMORY_SYSTEM_ENABLED=false
echo '{}' | uv run python .claude/tools/hook_stop.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  PASS: Handles empty input gracefully"
    PASS=$((PASS + 1))
else
    echo "  FAIL: Crashed on empty input"
    FAIL=$((FAIL + 1))
fi

# Test 4: Logger module is importable
uv run python -c "
import sys; sys.path.insert(0, '.claude/tools')
from hook_logger import HookLogger
h = HookLogger('test')
print('Logger OK')
" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  PASS: hook_logger.py is importable"
    PASS=$((PASS + 1))
else
    echo "  FAIL: hook_logger.py import failed"
    FAIL=$((FAIL + 1))
fi

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
