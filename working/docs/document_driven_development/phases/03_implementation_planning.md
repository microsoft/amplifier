# Phase 3: Implementation Planning

**Create detailed plan for making code match documentation exactly**

---

## Goal

Create comprehensive plan showing how code will match documentation. Understand full scope before coding.

**Why plan first**: Reveals dependencies, complexity, proper sequencing. Prevents mid-implementation surprises.

---

## The Steps

### Step 1: Code Reconnaissance

Use [file crawling](../core_concepts/file_crawling.md) to understand current state:

```bash
# Generate index of code files
find amplifier-core amplifier-app-cli -type f -name "*.py" \
  ! -path "*/__pycache__/*" ! -path "*/.venv/*" \
  > /tmp/code_files.txt

# Process systematically
# For each file: read, understand, note changes needed
```

**If conflicts detected** between docs and code:

**⚠️ PAUSE**: Present to human with options. See [context poisoning detection](../core_concepts/context_poisoning.md#detection-and-resolution).

### Step 2: Create Implementation Specification

Document exactly what needs to change:

```markdown
# Implementation Plan - [Feature Name]

## Current State
- ✅ What exists and works
- ❌ What's missing
- ⚠️ What needs modification

## Changes Required

### Core Classes
**File**: path/to/file.py
**Purpose**: What it does
**Methods**: List of methods
**Dependencies**: What it needs
**Estimated lines**: ~150
**Philosophy check**: Mechanism/policy alignment

[... detailed breakdown ...]

## Dependencies Between Changes
1. X depends on Y (build Y first)
2. Z requires X and Y (build last)

## Proper Sequencing
Phase 1: Core classes (foundation)
Phase 2: Commands (builds on core)
Phase 3: Tests (validates)

## Complexity Check
- New abstractions: 2
- Justification: Why needed
- Alternative: What else considered
- Why chosen: Reasoning

## Estimated Effort
- Component A: 2-3 hours
- Component B: 1-2 hours
Total: 8-11 hours, +850 lines

## Philosophy Compliance
- ✅ Ruthless simplicity
- ✅ Bricks and studs
- ✅ Right-sized modules
```

### Step 3: Right-Sizing Check

Each chunk should:
- ✅ Fit in AI context window (~4000-8000 lines)
- ✅ Have clear boundaries
- ✅ Be independently testable
- ✅ Be regeneratable from spec

**If too large**: Break into smaller modules with clear interfaces.

---

## Output of Phase 3

When complete:
- ✅ Detailed implementation plan documented
- ✅ Work properly right-sized
- ✅ Dependencies identified
- ✅ Sequencing determined
- ✅ Conflicts resolved
- ✅ Philosophy alignment verified

**Ready for**: [Phase 4: Code Implementation](04_code_implementation.md)

---

**Return to**: [Phases](README.md) | [Main Index](../README.md)

**Prerequisites**: [Phase 2: Approval Gate](02_approval_gate.md)

**Core Techniques**: [File Crawling](../core_concepts/file_crawling.md)

**Philosophy**: [MODULAR_DESIGN_PHILOSOPHY.md](../../ai_context/MODULAR_DESIGN_PHILOSOPHY.md)
