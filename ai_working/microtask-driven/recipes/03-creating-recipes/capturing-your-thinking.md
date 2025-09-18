# Capturing Your Thinking: From Mind to Recipe

## The Art of Making Implicit Knowledge Explicit

Most of our expertise lives in the implicit realm - the unconscious competence we've developed through experience. Creating a recipe requires surfacing this hidden knowledge, making the implicit explicit, and capturing not just what you do, but **how and why you think** through problems.

## The Challenge of Self-Observation

When you're an expert at something, you often don't notice what you're doing. You just "know" that:
- This error probably means that
- This pattern suggests that approach
- This situation calls for that response

Creating recipes requires becoming a detective of your own thinking.

## The Capture Process

### Step 1: Record Everything (Raw Capture)

Start by documenting everything you do, without filtering:

```markdown
# API Exploration Session - Raw Notes

1. Opened the API docs
2. Searched for "authentication" (always my first search)
3. Didn't find auth section immediately
4. Checked table of contents for "getting started"
5. Found auth buried in "prerequisites"
6. Noticed they use Bearer tokens (good, familiar)
7. Looked for how to get a token
8. Found OAuth flow docs
9. Thought "this looks overcomplicated for basic use"
10. Searched for "API key" as alternative
11. Found simpler API key method in different section
12. Decided to try API key first (simpler to test)
13. Made test request with curl
14. Got 401 error
15. Checked if I formatted the header correctly
16. Realized they want "X-API-Key" not "Authorization"
17. Fixed header, request worked
18. Made note: "non-standard header name"
```

### Step 2: Identify Patterns (Pattern Extraction)

Look for recurring themes in your raw capture:

```markdown
# Patterns I Notice

## Search Patterns
- Always search for "authentication" first
- If complex auth, look for simpler alternatives
- Check "getting started" when lost

## Decision Patterns
- Prefer simple over complex for initial testing
- Choose familiar patterns when available
- Test with minimal examples first

## Debugging Patterns
- When 401 error, check header format first
- Look for non-standard implementations
- Test assumptions with curl

## Meta Patterns
- I give up on docs and reverse-engineer after 10 minutes
- I always check multiple sections (docs often inconsistent)
- I make notes about gotchas for future reference
```

### Step 3: Extract Decision Criteria

Identify how you make choices:

```markdown
# How I Make Decisions

## Choosing Authentication Method
Priority Order:
1. API Key (simplest)
2. Bearer Token (standard)
3. OAuth (if required)
4. Custom (last resort)

Factors I Consider:
- Setup complexity
- Long-term maintenance
- Security requirements
- Team familiarity

Trade-offs I Make:
- Simplicity > Security (for development)
- Security > Simplicity (for production)
- Standard > Custom (always)
```

### Step 4: Document Adaptation Strategies

Capture how you handle the unexpected:

```markdown
# How I Adapt

## When Documentation is Wrong
1. Test the opposite of what docs say
2. Look for examples in different language
3. Check GitHub for working implementations
4. Try common patterns from similar APIs

## When Things Don't Work
1. Simplify to absolute minimum
2. Add complexity back gradually
3. Compare with working example
4. Question every assumption

## When Stuck
1. Take a break (seriously, this works)
2. Explain problem to rubber duck
3. Try completely different approach
4. Ask someone with fresh eyes
```

## Advanced Capture Techniques

### The Think-Aloud Protocol

Narrate your thinking as you work:

```markdown
"Okay, looking at this API... first thing I always check is auth because 
if I can't authenticate, nothing else matters. Hmm, no obvious auth section, 
that's a red flag. Let me check getting started... there we go, buried in 
prerequisites. Classic poor documentation structure. 

They're using OAuth, but wait... this seems overkill for what I need. Let me 
see if they have API keys... I bet they do but didn't document it prominently 
because OAuth is more 'enterprise'... 

Aha! Found it. API keys in a different section. This is why I always check 
multiple places - docs are rarely consistent."
```

### The Decision Journal

Document significant decisions and why you made them:

```markdown
# Decision Log

## Decision: Use API Key over OAuth
Context: Need to quickly test API functionality
Options Considered:
1. OAuth - More secure, but complex setup
2. API Key - Less secure, but immediate testing
3. Skip auth - Not possible, all endpoints protected

Chosen: API Key
Reasoning: 
- Testing phase, not production
- Need quick feedback loop
- Can switch to OAuth later
- Team familiar with API keys

Expected Outcomes:
- Faster initial development
- Possible security review later
- May need migration plan

Actual Outcome: [Fill in later]
Lessons: [Fill in later]
```

### The Mistake Catalog

Document errors and recoveries:

```markdown
# Mistakes and Recoveries

## Mistake: Assumed Standard Authorization Header
What Happened: Used "Authorization: Bearer <key>"
Why It Failed: API expects "X-API-Key: <key>"
How I Discovered: Read error message carefully
How I Fixed: Changed header format
Lesson: Don't assume standards, test minimal example
Recipe Rule: Always test auth with curl first
```

### The Heuristic Hunter

Identify your rules of thumb:

```markdown
# My Heuristics

## API Exploration Heuristics
- "If auth takes > 10 minutes, something's wrong"
- "Good APIs have curl examples on page 1"
- "If no rate limit docs, assume 100/minute"
- "Error messages lie, test everything"
- "When docs conflict, code wins"

## Problem-Solving Heuristics
- "Works locally but not in production = environment"
- "Intermittent failures = race condition"
- "Suddenly broken = check what changed"
- "Too complex = step back and rethink"
```

## Turning Observations into Recipe Components

### From Patterns to Hooks

```yaml
Pattern: "Always check authentication first"
↓
Hook: PreAPIExploration
Action: Force authentication verification
Code: |
  async function verifyAuthenticationFirst() {
    // This runs before any API exploration
    const authMethods = await findAuthenticationDocs();
    if (!authMethods) {
      throw new Error("Cannot proceed without understanding auth");
    }
    return selectAuthMethod(authMethods);
  }
```

### From Decisions to Agents

```yaml
Decision Process: "Choose simplest auth method"
↓
Agent: auth-method-selector
Thinking: |
  You prefer authentication methods in this order:
  1. API Key (simplest setup)
  2. Bearer Token (industry standard)
  3. OAuth (when required)
  Consider security needs vs development speed
  Always choose familiar over novel
```

### From Adaptations to Orchestration

```yaml
Adaptation: "When stuck, try different approach"
↓
Orchestration:
  try:
    - Attempt standard approach
  catch:
    - Log what failed
    - Switch to alternative approach
    - If still stuck: escalate to human
```

## Self-Observation Exercises

### Exercise 1: The Shadow

Have someone watch you work and note:
- What you do first
- Where you pause to think
- What you check repeatedly
- When you change approaches
- What frustrates you
- What delights you

### Exercise 2: The Time Machine

Work on a problem, then immediately after:
1. Write down what you did
2. Write down why you did it
3. Write down what you were thinking
4. Write down what you learned

### Exercise 3: The Teacher

Explain to someone else how to do what you do:
- What would you tell them to do first?
- What warnings would you give?
- What shortcuts would you share?
- What mistakes would you help them avoid?

### Exercise 4: The Comparison

Do the same task three times:
1. Your normal way
2. Strictly following documentation
3. How you'd teach a junior

Compare the approaches and note differences.

## Common Patterns to Look For

### Initialization Patterns
- What you always do first
- How you set up your environment
- What you verify before starting

### Exploration Patterns
- How you learn new systems
- What you look for first
- How you build mental models

### Problem-Solving Patterns
- How you approach unknowns
- Your debugging methodology
- Your escalation triggers

### Quality Patterns
- What you always check
- Your definition of "done"
- Your review process

### Learning Patterns
- What you pay attention to
- What you document
- What you remember

## The Iterative Refinement Process

### Version 1: Capture the Observable
Just document what you do

### Version 2: Add the Why
Explain your reasoning

### Version 3: Extract the Patterns
Identify recurring themes

### Version 4: Codify the Thinking
Transform into recipe components

### Version 5: Test and Refine
Verify the recipe thinks like you

## Making Your Thinking Transferable

### Use Clear Language
- Avoid jargon only you understand
- Explain domain-specific knowledge
- Define your terms
- Give examples

### Provide Context
- When this approach works
- When it doesn't
- Prerequisites needed
- Assumptions made

### Include Meta-Cognition
- How you know when you're stuck
- How you recognize patterns
- How you build intuition
- How you learn from mistakes

## The Final Test: Would You Trust It?

Ask yourself:
- Would I delegate this to the recipe?
- Does it make decisions like I would?
- Does it handle problems like I would?
- Would I be comfortable with others using it?
- Does it represent my expertise well?

If yes, you've successfully captured your thinking. If no, observe yourself more carefully and iterate.

---

*"The expert knows more than they can say, and they can say more than they can write. The art of recipe creation is bridging that gap."*

## Next Steps

1. Choose a task you do regularly
2. Document yourself doing it
3. Extract patterns and decisions
4. Transform into recipe components
5. Test and refine until it thinks like you

Your thinking is valuable. Capture it. Share it. Amplify it.