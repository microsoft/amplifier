# Phase 0: Planning & Alignment

**Achieve shared understanding between human and AI before any work begins**

---

## Goal

Establish clear, shared understanding of what will be built before touching any files.

**Why critical**: Misaligned understanding is expensive. An hour in planning saves days of rework.

---

## The Steps

### Step 1: Problem Framing

**Human presents**:
- High-level problem or requirement
- Scope and constraints
- Success criteria
- Relevant context

**Be explicit**: Don't assume AI knows your context.

### Step 2: Reconnaissance

**AI performs reconnaissance**:
- "What's the current state of X in the codebase?"
- "What files would be affected?"
- "What patterns exist to follow?"

**Use [file crawling](../core_concepts/file_crawling.md) if large scope**.

### Step 3: Brainstorming & Proposals

**AI generates 2-3 options**:
- Different approaches
- Trade-offs for each
- Complexity assessment
- Philosophy alignment

**Iterate together**:
- Human injects domain knowledge
- AI identifies technical constraints
- Discuss and refine

### Step 4: Shared Understanding Check

**Verification**:
- Ask AI to articulate the plan back
- Does AI's explanation match your mental model?
- Are there any gaps or misunderstandings?

**Red flag**: If explanation doesn't match expectations, keep iterating.

### Step 5: Capture the Plan

**For within-turn work**:
- AI uses TodoWrite to track steps
- System enforces completion
- AI can modify as discoveries made

**For multi-turn work**:
- Create file in `ai_working/` directory
- Track phases and blockers
- Update as work progresses
- Clean up when done

**Why**: AI is "easily distracted and forgetful." External tracking keeps focus.

---

## Output of Phase 0

When complete:
- ✅ Shared mental model established
- ✅ Plan captured (TodoWrite or ai_working/ file)
- ✅ Reconnaissance complete
- ✅ Trade-offs understood
- ✅ Philosophy alignment verified
- ✅ Human explicitly approves proceeding

**Ready for**: [Phase 1: Documentation Retcon](01_documentation_retcon.md)

---

## Tips

**For Humans**:
- Be patient - get this right before proceeding
- Challenge AI's assumptions
- Provide clear direction
- Approve explicitly when aligned

**For AI**:
- Show your reconnaissance findings
- Present multiple options
- Be honest about trade-offs
- Ask clarifying questions
- Don't proceed without alignment

---

**Return to**: [Phases](README.md) | [Main Index](../README.md)

**Next Phase**: [Phase 1: Documentation Retcon](01_documentation_retcon.md)
