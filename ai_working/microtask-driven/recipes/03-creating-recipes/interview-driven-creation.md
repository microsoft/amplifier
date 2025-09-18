# Interview-Driven Recipe Creation

## The Conversational Path to Cognitive Capture

Not all recipes start with complete clarity. Sometimes the best way to create a recipe is through intelligent conversation - where the system interviews you to extract your cognitive patterns.

## Why Interview-Driven Creation?

### The Expertise Paradox

Experts often can't articulate what they know because:
- **Unconscious competence** - They just "know" what to do
- **Contextual knowledge** - Decisions depend on subtle cues
- **Internalized patterns** - Steps have become automatic
- **Tacit knowledge** - Some things are felt, not explained

### The Solution: Intelligent Interviewing

The system acts as a skilled interviewer who:
- Asks targeted questions to surface hidden knowledge
- Probes for examples to understand patterns
- Identifies gaps and requests clarification
- Builds a cognitive model through dialogue

## The Interview Process

### Phase 1: Domain Discovery

The system starts broad to understand context:

```
System: "What type of work does this recipe apply to?"
User: "API integration"

System: "Is this for a specific API or a general approach?"
User: "General - I do this for many different APIs"

System: "What makes you particularly good at this?"
User: "I can usually figure out undocumented APIs"
```

### Phase 2: Process Excavation

Next, it uncovers your actual process:

```
System: "Walk me through the last time you did this"
User: "I was trying to get data from LinkedIn..."

System: "What was the very first thing you did?"
User: "Opened Chrome DevTools"

System: "Why DevTools first? What were you looking for?"
User: "Network requests - to see their API calls"

System: "What told you that you found the right endpoint?"
User: "The response had the data I could see on screen"
```

### Phase 3: Decision Point Mapping

The system identifies where and how you make choices:

```
System: "When you saw it was GraphQL, what did that tell you?"
User: "I'd need to understand their schema"

System: "How did you figure out the schema without documentation?"
User: "I captured multiple queries and reverse-engineered it"

System: "What if it had been REST instead?"
User: "Easier - I'd just copy the curl command from DevTools"
```

### Phase 4: Adaptation Strategy Discovery

Understanding how you handle variations:

```
System: "What happens when authentication is required?"
User: "I check for cookies first, then headers, then OAuth"

System: "How do you know which one they're using?"
User: "401 errors point to auth issues, then I check request headers"

System: "Has this approach ever failed?"
User: "Yes, with websocket APIs - completely different pattern"
```

### Phase 5: Success Criteria Definition

Clarifying what "done" means:

```
System: "How do you know when you've succeeded?"
User: "I can reliably fetch the data I need"

System: "What does 'reliably' mean to you?"
User: "Works multiple times, handles errors, doesn't break easily"

System: "How do you test reliability?"
User: "Run it 10 times, try edge cases, test with bad data"
```

## Interview Strategies

### The Funnel Approach

Start broad, narrow down:
1. **Context** - What domain/area?
2. **Process** - What are the main steps?
3. **Details** - How exactly do you do each step?
4. **Exceptions** - What about edge cases?
5. **Validation** - How do you verify success?

### The Example-Driven Method

Learn from specific instances:

```
System: "Tell me about a particularly challenging case"
System: "What made it challenging?"
System: "How did you solve it?"
System: "Would you do it differently now?"
System: "What did this teach you?"
```

### The Comparison Technique

Understanding through contrast:

```
System: "How is this different from [similar process]?"
System: "When would you use this approach vs. another?"
System: "What would a beginner do wrong?"
System: "What shortcuts do you take that others might not know?"
```

### The Failure Analysis

Learning from what doesn't work:

```
System: "When has this process failed?"
System: "What were the warning signs?"
System: "How did you recover?"
System: "What did you change afterward?"
```

## Intelligent Probing

The system knows when to dig deeper:

### Surface Indicator → Deeper Question

| What You Say | What System Asks |
|-------------|------------------|
| "I just know" | "What are you looking for that tells you?" |
| "It depends" | "What does it depend on? Give me two scenarios" |
| "Usually" | "What's the usual case? What's unusual?" |
| "I check if it's good" | "What specific things indicate 'good'?" |
| "I fix it" | "Walk me through the fixing process" |

### Pattern Recognition

The system identifies patterns in your answers:

- **Sequence patterns**: "You always do X before Y"
- **Decision patterns**: "You choose A when B is true"
- **Quality patterns**: "You verify by checking C"
- **Recovery patterns**: "When D fails, you try E"

## Building Cognitive Models from Interviews

### From Answers to Architecture

The system transforms interview responses into recipe components:

```python
Interview Response → Recipe Component

"I always check auth first" 
→ Hook: pre_api_call { verify_auth() }

"If it's GraphQL, I need the schema"
→ Decision: if is_graphql() { extract_schema() }

"I know it works when I get data back"
→ Validator: assert response.has_data()

"I explore APIs to understand them"
→ Agent: api_explorer with exploration strategies
```

### Confidence Calibration

The system tracks confidence in different parts:

```yaml
High Confidence (you were very specific):
  - Authentication check process
  - GraphQL detection method
  - Success criteria

Medium Confidence (some ambiguity):
  - Schema extraction approach
  - Error handling strategy

Low Confidence (need more info):
  - Websocket handling
  - Rate limit management
```

## Interactive Refinement

### The Clarification Loop

When the system needs more information:

```
System: "I generated a recipe but I'm uncertain about the error handling.
         When you said 'handle errors gracefully', what does that mean?"

User: "Retry 3 times with exponential backoff, then log and alert"

System: "Got it. Updating the recipe with specific error handling..."
```

### The Validation Dialogue

Testing cognitive fidelity through conversation:

```
System: "Your recipe would choose REST over GraphQL here. Is that right?"
User: "No, I'd pick GraphQL if there's nested data"
System: "Adjusting decision criteria..."
```

## Advanced Interview Techniques

### The Socratic Method

Leading you to articulate your knowledge:

```
System: "Why do you think that approach works?"
System: "What assumption are you making?"
System: "How would you test that assumption?"
System: "What would convince you otherwise?"
```

### The Variation Exercise

Exploring the boundary conditions:

```
System: "Make it work with 10x more data"
System: "Now with unreliable network"
System: "What if you had 5 seconds instead of 5 minutes?"
System: "How would an expert do it differently?"
```

### The Teaching Test

If you can teach it, you understand it:

```
System: "How would you teach this to a junior developer?"
System: "What would you emphasize?"
System: "What mistakes would they likely make?"
System: "What's the one key insight?"
```

## Benefits of Interview-Driven Creation

### For the User
- **No recipe expertise required** - Just answer questions
- **Discovers your own patterns** - Learn about your process
- **Quick and natural** - Like explaining to a colleague
- **Iterative improvement** - Refine through dialogue

### For the Recipe
- **Higher fidelity** - Captures nuanced thinking
- **Better coverage** - Uncovers edge cases
- **Validated understanding** - Confirms interpretation
- **Richer context** - Includes the "why" not just "what"

## When to Use Interview-Driven Creation

### Perfect For:
- **Complex cognitive processes** - Multi-step reasoning
- **Tacit knowledge** - Things you "just know"
- **Adaptive processes** - Lots of "it depends"
- **Expert intuition** - Pattern recognition tasks
- **First-time recipe creators** - Don't know where to start

### Less Suitable For:
- **Simple linear processes** - Step 1, 2, 3, done
- **Well-documented procedures** - Already written down
- **Pure automation** - No decisions involved
- **Time-critical creation** - Need recipe NOW

## Tips for Better Interviews

### As the Interviewee:
1. **Be specific** - Use concrete examples
2. **Think aloud** - Explain your reasoning
3. **Admit uncertainty** - "I'm not sure" is valuable
4. **Share failures** - What didn't work teaches too
5. **Question back** - Ask for clarification

### For the System:
1. **Start with examples** - Concrete is easier than abstract
2. **Use analogies** - "Is it like...?"
3. **Confirm understanding** - "So you mean...?"
4. **Identify patterns** - "I notice you always..."
5. **Test edge cases** - "What if...?"

## The Future: Conversational Recipe Evolution

Imagine recipes that improve through ongoing dialogue:

```
Recipe: "I handled that case differently than you would. Why?"
User: "The new API version changed the auth flow"
Recipe: "Understood. Updating my patterns..."
```

This creates truly adaptive digital teammates that learn and evolve through conversation.

---

*"The best recipes emerge from dialogue - where human expertise meets systematic extraction."*