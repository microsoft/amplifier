#!/bin/bash
# Smoke tests for session-end-index.sh
# Run: bash tests/hooks/test_session_end_index.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
. "$REPO_ROOT/scripts/lib/platform.sh"

HOOK="$AMPLIFIER_HOME/.claude/hooks/session-end-index.sh"
PASS=0
FAIL=0

echo "=== session-end-index.sh smoke tests ==="

# Test 1: Script is syntactically valid
bash -n "$HOOK" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "  PASS: Script syntax is valid"
    PASS=$((PASS + 1))
else
    echo "  FAIL: Script has syntax errors"
    FAIL=$((FAIL + 1))
fi

# Test 2: Script references existing Python scripts
for script in "scripts/recall/extract-sessions.py" "scripts/recall/extract-docs.py" "scripts/recall/generate-doc-registry.py"; do
    if [ -f "$AMPLIFIER_HOME/$script" ]; then
        echo "  PASS: Referenced script exists: $script"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: Referenced script missing: $script"
        FAIL=$((FAIL + 1))
    fi
done

# Test 3: extract-sessions.py is importable
cd "$AMPLIFIER_HOME"
uv run python -c "import scripts.recall.extract_sessions" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "  PASS: extract-sessions.py is importable"
    PASS=$((PASS + 1))
else
    # It may not be importable as a module — test via syntax check
    uv run python -m py_compile scripts/recall/extract-sessions.py 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "  PASS: extract-sessions.py compiles cleanly"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: extract-sessions.py has syntax errors"
        FAIL=$((FAIL + 1))
    fi
fi

# Test 4: extract-docs.py --recent 0 runs without error (no files to index)
cd "$AMPLIFIER_HOME"
uv run python scripts/recall/extract-docs.py --recent 0 > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  PASS: extract-docs.py --recent 0 runs cleanly"
    PASS=$((PASS + 1))
else
    echo "  FAIL: extract-docs.py --recent 0 failed"
    FAIL=$((FAIL + 1))
fi

# Test 5: generate-doc-registry.py runs without error
cd "$AMPLIFIER_HOME"
uv run python scripts/recall/generate-doc-registry.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  PASS: generate-doc-registry.py runs cleanly"
    PASS=$((PASS + 1))
else
    echo "  FAIL: generate-doc-registry.py failed"
    FAIL=$((FAIL + 1))
fi

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
