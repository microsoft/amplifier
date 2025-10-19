# Core Concepts

**Essential techniques used throughout Document-Driven Development**

---

## Overview

These core concepts are used repeatedly throughout the DDD process. Understanding them is essential for success.

---

## The Three Core Concepts

### [File Crawling](file_crawling.md)

**What**: Systematic processing of many files without context overload

**Why**: AI cannot hold all files in context at once. File crawling provides external index + sequential processing.

**When**: Processing 10+ files, documentation updates, code changes across modules

**Key benefit**: 99.5% token reduction, guarantees every file processed

### [Context Poisoning](context_poisoning.md)

**What**: When AI loads inconsistent information leading to wrong decisions

**Why**: Duplicate/stale/conflicting docs mislead AI tools

**When**: Monitor always, prevent proactively, resolve when detected

**Key benefit**: Eliminates root cause of AI making wrong decisions confidently

### [Retcon Writing](retcon_writing.md)

**What**: Writing documentation as if the feature already exists

**Why**: Eliminates ambiguity about what's current vs future vs historical

**When**: Phase 1 (Documentation Retcon), any doc updates

**Key benefit**: Clear, unambiguous specifications for both humans and AI

---

## How They Work Together

**File Crawling** enables systematic processing:
- Prevents forgetting files
- Efficient token usage
- Clear progress tracking

**Context Poisoning** prevention maintains quality:
- Each concept in ONE place
- No duplicate information
- Always current, never stale

**Retcon Writing** ensures clarity:
- Write as if already implemented
- No historical references
- Single timeline (now)

**Together**: Process many files systematically while preventing inconsistency and maintaining clarity.

---

## Quick Reference

**For AI Assistants**:
- Use file crawling for any 10+ file operation
- Check for context poisoning when loading multiple sources
- Apply retcon writing rules when updating docs

**For Humans**:
- File crawling: External checklist, process one at a time
- Context poisoning: Delete duplicates, single source of truth
- Retcon: Write present tense, as if already exists

---

## Related Documentation

**Process**: [Phases](../phases/) - Where these concepts are applied
**Reference**: [Checklists](../reference/checklists.md) - Verification steps
**Return to**: [Main Index](../README.md)
