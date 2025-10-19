# Checklists

**Phase-by-phase verification checklists for Document-Driven Development**

---

## Overview

Use these checklists to verify completion of each phase. Check off items as you complete them to ensure nothing is missed.

---

## Phase 0: Planning & Alignment

- [ ] Problem clearly framed with scope and success criteria
- [ ] Reconnaissance complete ([file crawling](../core_concepts/file_crawling.md) if large)
- [ ] Multiple proposals considered (2-3 options)
- [ ] Trade-offs discussed openly
- [ ] Shared understanding achieved and verified
- [ ] AI can articulate plan back accurately
- [ ] Master plan captured (TodoWrite or ai_working/ file)
- [ ] Philosophy alignment verified
- [ ] **User explicitly approves proceeding**

**Ready for**: [Phase 1](../phases/01_documentation_retcon.md)

---

## Phase 1: Documentation Retcon

- [ ] File index generated programmatically
- [ ] [File crawling](../core_concepts/file_crawling.md) approach used systematically
- [ ] Each file processed individually (not batch marked)
- [ ] Full file content read before changes
- [ ] [Retcon writing rules](../core_concepts/retcon_writing.md) followed strictly
- [ ] Maximum DRY enforced (duplicates deleted)
- [ ] Global replacements used as helper only (not substitute)
- [ ] Conflicts detected and resolved (if any)
- [ ] Progressive organization applied
- [ ] Verification pass complete
- [ ] **NOT committed yet** - ready for approval
- [ ] All files in checklist marked `[x]`

**Ready for**: [Phase 2](../phases/02_approval_gate.md)

---

## Phase 2: Approval Gate

- [ ] Human reviewed all documentation
- [ ] Design verified correct and complete
- [ ] Terminology verified accurate and canonical
- [ ] Complexity captured honestly
- [ ] Examples verified realistic and correct
- [ ] Philosophy compliance confirmed
- [ ] No duplication or [context poisoning](../core_concepts/context_poisoning.md) sources
- [ ] Progressive organization makes sense
- [ ] Human-readable and clear
- [ ] **Iterate with human until approved**
- [ ] User explicitly approves: "proceed to implementation"
- [ ] **NOW commit documentation** with approval note
- [ ] **NOT pushed yet** - implementation next

**Ready for**: [Phase 3](../phases/03_implementation_planning.md)

---

## Phase 3: Implementation Planning

- [ ] Code reconnaissance complete ([file crawling](../core_concepts/file_crawling.md))
- [ ] Conflicts between docs and code resolved
- [ ] Implementation plan documented in detail
- [ ] Work properly right-sized (fits in context window)
- [ ] Dependencies identified
- [ ] Proper sequencing determined
- [ ] Complexity check performed
- [ ] Effort estimated
- [ ] Philosophy alignment verified

**Ready for**: [Phase 4](../phases/04_code_implementation.md)

---

## Phase 4: Code Implementation

- [ ] [File crawling](../core_concepts/file_crawling.md) approach used for large changes
- [ ] Full context loaded before each subtask
- [ ] Related docs, code, and tests read first
- [ ] Conflicts detected and paused on (if any)
- [ ] Code matches docs exactly
- [ ] No deviation without doc update first
- [ ] Changes committed incrementally by logical feature
- [ ] Clear commit messages
- [ ] All implementation checklist items marked complete

**Ready for**: [Phase 5](../phases/05_testing_and_verification.md)

---

## Phase 5: Testing & Verification

- [ ] All documented examples tested
- [ ] Examples work when copy-pasted
- [ ] **User testing complete** (AI tested as actual user)
- [ ] **User testing report created** (detailed in ai_working/)
- [ ] **Recommended smoke tests provided** (for human)
- [ ] Output matches documentation descriptions
- [ ] Error handling tested (invalid inputs, edge cases)
- [ ] Cross-cutting scenarios tested
- [ ] All code-based tests passing: `make test`
- [ ] All checks passing: `make check`
- [ ] Performance acceptable
- [ ] **Critical issues resolved** or documented
- [ ] Docs updated if mismatches found (with approval)

**Ready for**: [Phase 6](../phases/06_cleanup_and_push.md)

---

## Phase 6: Cleanup & Push

- [ ] Temporary files removed or archived
- [ ] ai_working/ reviewed and cleaned
- [ ] All tests passing
- [ ] All checks passing
- [ ] Documentation and code in perfect sync
- [ ] No temporary/debug code
- [ ] Commit messages clear
- [ ] Philosophy principles followed throughout
- [ ] Final verification complete
- [ ] **Changes pushed to remote**

**DDD Cycle Complete!**

---

## Quick Verification Commands

### Check Documentation Consistency

```bash
# No old terminology
grep -rn "old-term" docs/

# No historical references
grep -rn "previously\|used to\|old way" docs/

# No future tense
grep -rn "will be\|coming soon" docs/

# No duplicate concepts
grep -rn "concept definition" docs/  # Should be single location
```

### Check Implementation Quality

```bash
# Run tests
make test

# Run checks
make check

# Verify no debug code
grep -rn "print(\|console.log\|debugger" --include="*.py" --include="*.js"

# Check git status
git status  # Should be clean
```

### Check Context Poisoning

```bash
# No duplicate documentation
# Each concept in ONE place

# Verify with:
grep -r "term-to-check" docs/  # Should return single canonical location
```

---

## Master Checklist (All Phases)

Use this for complete DDD cycle verification:

**Planning**: Phase 0 complete
**Documentation**: Phase 1 complete, Phase 2 approved & committed
**Implementation**: Phase 3 planned, Phase 4 implemented & committed
**Verification**: Phase 5 tested (user + code)
**Completion**: Phase 6 cleaned & pushed

**Success criteria**:
- ✅ Documentation and code never diverged
- ✅ Zero context poisoning
- ✅ All tests passing
- ✅ Clean git history
- ✅ Philosophy principles followed
- ✅ User testing complete
- ✅ Ready for human review

---

**Return to**: [Reference](README.md) | [Main Index](../README.md)

**See Also**: [Tips for Success](tips_for_success.md) | [Common Pitfalls](common_pitfalls.md)
