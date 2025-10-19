# Phase 2: Approval Gate

**Human reviews and approves design. Iterate until right. THEN commit.**

---

## Goal

Human reviews and approves the design as expressed in documentation. Iterate with AI until design is correct. Only then commit documentation.

**Why this gate is critical**: Last checkpoint before expensive implementation. Design flaws caught here save days of rework. Committing before approval thrashes git log with wrong commits.

---

## The Process

### Review Checklist

Human reviews uncommitted documentation:

- [ ] Design is correct and complete
- [ ] Terminology is accurate and canonical
- [ ] Complexity captured honestly
- [ ] Examples are realistic and will work
- [ ] Philosophy principles followed
- [ ] No duplication or [context poisoning](../core_concepts/context_poisoning.md) sources
- [ ] Progressive organization makes sense
- [ ] Human-readable and clear

### Review Questions

**Ask yourself**:
- Can I understand this without reading code?
- Would this guide someone to build the right thing?
- Are examples realistic? Will they work?
- Is anything over-complex?
- Is anything missing?
- Does this align with project philosophy?

---

## Iteration Cycle

### If Issues Found

1. **Provide feedback** to AI
2. **AI fixes issues** in documentation
3. **Return to Phase 1** for affected files
4. **Return to review**
5. **Do NOT commit** - keep iterating

**Iterate until right** - No commits during iteration.

**Why**: Prevents git log thrashing with wrong versions.

### If Approved

1. **Explicitly approve**: "This looks good, proceed to implementation"
2. **AI commits documentation**:

```bash
git add docs/ README.md *.md
git commit -m "docs: Complete [feature name] documentation retcon

- Updated all docs to reflect target state
- Deleted duplicate documentation (DRY principle)
- Fixed terminology: [old] → [new]
- Organized for progressive learning

Following Document-Driven Development approach.
Documentation is specification - code implementation follows.

Reviewed and approved by: [human name]"
```

3. **Documentation is now the specification**
4. **No code changes without doc changes from this point**

---

## Why Wait Until Approval

**Prevents**:
- Git log thrashing with wrong commits
- Implementing against flawed design
- Wasted iteration time

**Ensures**:
- Clean git history (only approved designs)
- Design is right before implementation
- Documentation remains authoritative

---

## Output of Phase 2

When complete:
- ✅ Documentation reviewed by human
- ✅ Design approved
- ✅ **Documentation committed** (with approval note)
- ✅ Specification locked
- ⚠️ **NOT pushed yet** - implementation next

**Ready for**: [Phase 3: Implementation Planning](03_implementation_planning.md)

---

## Tips

**For Humans**:
- Review thoroughly - cheapest checkpoint
- Iterate until right before approving
- Be specific about what needs changing
- Approve explicitly when satisfied

**For AI**:
- Don't commit until explicit approval
- Apply feedback systematically
- Return to Phase 1 process for fixes
- Wait patiently for approval

---

**Return to**: [Phases](README.md) | [Main Index](../README.md)

**Prerequisites**: [Phase 1: Documentation Retcon](01_documentation_retcon.md)

**Next Phase**: [Phase 3: Implementation Planning](03_implementation_planning.md)
