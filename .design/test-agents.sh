#!/bin/bash

# Agent Testing Script
# Quick validation of /designer agent functionality

set -e

echo "🧪 Amplified Design Agent Test Suite"
echo "===================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
PASSED=0
FAILED=0
WARNINGS=0

# Test functions
test_passed() {
  echo -e "${GREEN}✓${NC} $1"
  ((PASSED++))
}

test_failed() {
  echo -e "${RED}✗${NC} $1"
  ((FAILED++))
}

test_warning() {
  echo -e "${YELLOW}⚠${NC} $1"
  ((WARNINGS++))
}

test_info() {
  echo -e "${BLUE}ℹ${NC} $1"
}

# Test 1: Design System Files Exist
echo "📋 Test 1: Design System Files"
echo "------------------------------"

if [ -f "FRAMEWORK.md" ]; then
  test_passed "FRAMEWORK.md exists"
else
  test_failed "FRAMEWORK.md missing"
fi

if [ -f "PHILOSOPHY.md" ]; then
  test_passed "PHILOSOPHY.md exists"
else
  test_failed "PHILOSOPHY.md missing"
fi

if [ -f ".design/COMPONENT-CREATION-PROTOCOL.md" ]; then
  test_passed "COMPONENT-CREATION-PROTOCOL.md exists"
else
  test_failed "COMPONENT-CREATION-PROTOCOL.md missing"
fi

if [ -f ".design/PROACTIVE-DESIGN-PROTOCOL.md" ]; then
  test_passed "PROACTIVE-DESIGN-PROTOCOL.md exists"
else
  test_failed "PROACTIVE-DESIGN-PROTOCOL.md missing"
fi

if [ -f ".design/DESIGN-SYSTEM-ENFORCEMENT.md" ]; then
  test_passed "DESIGN-SYSTEM-ENFORCEMENT.md exists"
else
  test_failed "DESIGN-SYSTEM-ENFORCEMENT.md missing"
fi

echo ""

# Test 2: Agent Files Exist
echo "🤖 Test 2: Agent Configuration"
echo "------------------------------"

if [ -f ".claude/commands/designer.md" ]; then
  test_passed "/designer command exists"
else
  test_failed "/designer command missing"
fi

if [ -f ".claude/agents/design-system-architect.md" ]; then
  test_passed "design-system-architect agent exists"
else
  test_failed "design-system-architect agent missing"
fi

if [ -f ".claude/agents/component-designer.md" ]; then
  test_passed "component-designer agent exists"
else
  test_failed "component-designer agent missing"
fi

if [ -f ".claude/agents/animation-choreographer.md" ]; then
  test_passed "animation-choreographer agent exists"
else
  test_failed "animation-choreographer agent missing"
fi

echo ""

# Test 3: Design Tokens
echo "🎨 Test 3: Design Token System"
echo "------------------------------"

if [ -f "studio-interface/app/globals.css" ]; then
  test_passed "globals.css exists"

  # Check for key semantic tokens
  if grep -q "\-\-background:" studio-interface/app/globals.css; then
    test_passed "Background tokens defined"
  else
    test_failed "Missing background tokens"
  fi

  if grep -q "\-\-text:" studio-interface/app/globals.css; then
    test_passed "Text tokens defined"
  else
    test_failed "Missing text tokens"
  fi

  if grep -q "\-\-border:" studio-interface/app/globals.css; then
    test_passed "Border tokens defined"
  else
    test_failed "Missing border tokens"
  fi

  if grep -q "prefers-color-scheme: dark" studio-interface/app/globals.css; then
    test_passed "Dark mode tokens defined"
  else
    test_failed "Missing dark mode tokens"
  fi
else
  test_failed "globals.css missing"
fi

echo ""

# Test 4: Validation Scripts
echo "✅ Test 4: Validation Scripts"
echo "-----------------------------"

if [ -f "package.json" ]; then
  test_passed "package.json exists"

  if grep -q "validate:tokens" package.json; then
    test_passed "validate:tokens script defined"
  else
    test_warning "validate:tokens script not found (recommended)"
  fi
else
  test_failed "package.json missing"
fi

echo ""

# Test 5: Hardcoded Values Audit
echo "🔍 Test 5: Hardcoded Values Check"
echo "---------------------------------"

if [ -d "studio-interface/components" ]; then
  test_info "Scanning components for hardcoded values..."

  HARDCODED=$(grep -r "rgba\|#[0-9A-Fa-f]\{6\}" studio-interface/components/ 2>/dev/null | grep -v "var(--" | wc -l)

  if [ "$HARDCODED" -eq 0 ]; then
    test_passed "No hardcoded color values found"
  else
    test_warning "Found $HARDCODED potential hardcoded values"
    test_info "Run: grep -r \"rgba\\|#[0-9A-Fa-f]\" studio-interface/components/ | grep -v \"var(--\""
  fi
else
  test_info "Components directory not found (skipping hardcoded check)"
fi

echo ""

# Test 6: Validation Test
echo "🏗️ Test 6: Build & Validation"
echo "-----------------------------"

if command -v npm &> /dev/null; then
  test_passed "npm available"

  # Test if validation script exists and runs
  if grep -q "validate:tokens" package.json 2>/dev/null; then
    test_info "Testing validation script..."
    if npm run validate:tokens &>/dev/null; then
      test_passed "validate:tokens passes"
    else
      test_failed "validate:tokens fails (run: npm run validate:tokens)"
    fi
  fi

  # Test TypeScript check
  if command -v npx &> /dev/null; then
    test_info "Testing TypeScript compilation..."
    if npx tsc --noEmit &>/dev/null; then
      test_passed "TypeScript check passes"
    else
      test_warning "TypeScript check fails (run: npx tsc --noEmit)"
    fi
  fi
else
  test_warning "npm not available (skipping validation tests)"
fi

echo ""

# Summary
echo "📊 Test Summary"
echo "==============="
echo -e "Tests Passed:  ${GREEN}$PASSED${NC}"
echo -e "Tests Failed:  ${RED}$FAILED${NC}"
echo -e "Warnings:      ${YELLOW}$WARNINGS${NC}"
echo ""

TOTAL=$((PASSED + FAILED + WARNINGS))
SCORE=$((PASSED * 100 / TOTAL))

echo "Health Score: $SCORE%"
echo ""

if [ $SCORE -ge 90 ]; then
  echo -e "${GREEN}✓ Excellent - Agents are production ready${NC}"
  exit 0
elif [ $SCORE -ge 80 ]; then
  echo -e "${YELLOW}⚠ Good - Minor tuning recommended${NC}"
  exit 0
elif [ $SCORE -ge 70 ]; then
  echo -e "${YELLOW}⚠ Fair - Review agent configuration${NC}"
  exit 1
else
  echo -e "${RED}✗ Poor - Major investigation needed${NC}"
  exit 1
fi
