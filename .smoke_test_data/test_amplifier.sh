#!/bin/bash

# Amplifier Quick Test Suite
# Validates core functionality is working

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo "========================================"
echo "    AMPLIFIER QUICK TEST SUITE"
echo "========================================"
echo ""

FAILURES=0

# Function to test a command
test_cmd() {
    local name="$1"
    local cmd="$2"
    local expected="$3"
    
    echo -n "Testing $name... "
    if output=$($cmd 2>&1); then
        if [[ -z "$expected" ]] || echo "$output" | grep -q "$expected"; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}✗${NC} (pattern not found: $expected)"
            FAILURES=$((FAILURES + 1))
        fi
    else
        echo -e "${RED}✗${NC} (command failed)"
        FAILURES=$((FAILURES + 1))
    fi
}

# Core functionality tests
test_cmd "amplifier --version" "amplifier --version" "Amplifier v0.2.0"
test_cmd "amplifier doctor" "amplifier doctor" "Python 3.11"
test_cmd "Python CLI exists" "test -f .venv/bin/amplifier && echo OK" "OK"
test_cmd "Unified wrapper" "test -f ~/bin/amplifier && echo OK" "OK"
test_cmd "Cache module" "python -c 'from amplifier.utils.cache import ArtifactCache; print(\"OK\")'" "OK"
test_cmd "Event module" "python -c 'from amplifier.utils.events import EventLogger; print(\"OK\")'" "OK"
test_cmd "CLI module" "python -c 'from amplifier.cli import cli; print(\"OK\")'" "OK"
test_cmd "Package installed" "python -c 'import amplifier; print(\"OK\")'" "OK"

# Performance test (if file exists)
if [ -f test_cache_performance.py ]; then
    echo -n "Testing cache performance... "
    if timeout 10 python test_cache_performance.py 2>&1 | grep -q "Speedup: [0-9]*x"; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        FAILURES=$((FAILURES + 1))
    fi
fi

echo ""
echo "========================================"
if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo "Amplifier is working correctly."
else
    echo -e "${RED}❌ $FAILURES TEST(S) FAILED${NC}"
    echo "Please check the failures above."
fi
echo "========================================"

exit $FAILURES
