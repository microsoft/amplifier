# Tips for Success

**Best practices for humans and AI assistants using Document-Driven Development**

---

## For Humans

### Planning Phase (Phase 0)

1. **Be patient** - Get shared understanding right before any work
2. **Challenge assumptions** - AI doesn't know your context
3. **Provide clear direction** - Be explicit about success criteria
4. **Approve explicitly** - Don't assume alignment

### Documentation Phase (Phase 1-2)

5. **Review docs thoroughly** - Cheapest checkpoint for catching issues
6. **Iterate until right** - Don't approve until actually right
7. **Insist on DRY** - Delete duplicates aggressively
8. **Don't commit before approval** - Prevents git thrashing

### Implementation Phase (Phase 3-4)

9. **Trust the process** - Resist urge to code before docs approved
10. **Provide clear decisions** - When AI pauses for conflicts
11. **Question over-complexity** - Challenge deviations from simplicity

### Testing Phase (Phase 5)

12. **Review user testing reports** - AI's findings are valuable
13. **Run recommended smoke tests** - Quick verification as actual user
14. **Test on your environment** - AI tested on one environment
15. **Trust but verify** - AI is good QA, not perfect

---

## For AI Assistants

### General Principles

1. **Use TodoWrite religiously** - Track all multi-step work
2. **Be honest about limitations** - Say "I don't know" rather than guess
3. **Show your work** - Explain reasoning, not just results
4. **Ask early** - Better to clarify than implement wrong

### File Processing

5. **Use [file crawling](../core_concepts/file_crawling.md) for 10+ files** - Don't try to hold all in context
6. **Process one file at a time** - No shortcuts, no batching
7. **Read complete files** - No skimming before changes
8. **Mark complete honestly** - Only after full individual review
9. **Show progress periodically** - Keep human informed

### Documentation

10. **Follow [retcon writing](../core_concepts/retcon_writing.md) strictly** - Write as if already exists
11. **PAUSE on conflicts** - Never guess, always ask
12. **Delete duplicates** - Suggest deletion, not update
13. **Global replacements are helpers** - Never substitutes for review

### Implementation

14. **Load full context first** - Read all related files before coding
15. **PAUSE when docs conflict** - Don't proceed with inconsistency
16. **Code matches docs exactly** - No deviation without doc update
17. **Commit incrementally** - Don't wait for everything complete

### Testing

18. **Test as actual user** - Not just unit tests
19. **Document thoroughly** - Create detailed user testing reports
20. **Be honest about issues** - Don't hide problems found
21. **Guide human testing** - Recommend specific scenarios

---

## Universal Tips

### For Both Humans and AI

**Communication**:
- Be explicit and clear
- Ask when uncertain
- Confirm understanding
- Document decisions

**Quality**:
- Follow [philosophy principles](../../ai_context/IMPLEMENTATION_PHILOSOPHY.md)
- Verify against [checklists](checklists.md)
- Test thoroughly
- Iterate until right

**Efficiency**:
- Use systematic approaches ([file crawling](../core_concepts/file_crawling.md))
- Catch issues early (approval gates)
- Don't skip steps
- Trust the process

---

## Red Flags to Watch For

**For Humans**:
- ❌ AI says "done" but you suspect files missed
- ❌ AI doesn't pause when you see conflicts
- ❌ AI marks files complete after global replace only
- ❌ AI proceeding without shared understanding

**For AI**:
- ❌ Human seems confused by your explanation
- ❌ You found conflicts but continued anyway
- ❌ You marked files done without reading them
- ❌ You're guessing at resolutions

**If any red flags**: STOP and address before continuing.

---

## Success Patterns

### Healthy Collaboration

✅ Clear back-and-forth in planning
✅ AI pauses appropriately for conflicts
✅ Human provides clear decisions
✅ Both aligned on approach
✅ Systematic progress visible
✅ Issues caught early
✅ Quality maintained throughout

### Efficient Process

✅ File crawling used for large sets
✅ One file at a time processing
✅ Progress visible and trackable
✅ Conflicts resolved before continuing
✅ Documentation approved before implementation
✅ Testing thorough (code + user)

---

**Return to**: [Reference](README.md) | [Main Index](../README.md)

**See Also**: [Common Pitfalls](common_pitfalls.md) | [FAQ](faq.md) | [Checklists](checklists.md)
