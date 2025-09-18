# Creating Your First Recipe in 5 Minutes

## The Fast Path to Recipe Creation

You don't need to understand the deep theory of metacognitive recipes to create one. This guide gets you from idea to working recipe in under 5 minutes.

## The Magic Command

```bash
/create-recipe "domain" "what you do"
```

That's it. The system takes over from there.

## Example: Creating a Content Fetcher Recipe

### Step 1: Start the Command
```bash
/create-recipe "content-fetch" "I investigate websites and build API fetchers"
```

### Step 2: Answer 5 Quick Questions

The system asks only what it MUST know:

```
Q1: What triggers this process to start?
> "I need content from a new website"

Q2: What's the very first thing you do?
> "Open browser DevTools to watch network traffic"

Q3: What's the main decision you make?
> "Figuring out if it's REST, GraphQL, or something custom"

Q4: How do you know it worked?
> "I can successfully fetch and parse articles"

Q5: Can you show me one example?
> "Medium uses GraphQL with cookie auth, found in DevTools"
```

### Step 3: Recipe Generated!

The system creates a complete recipe with:
- **Hooks** that trigger at the right moments
- **Commands** you can invoke
- **Agents** that think like you
- **Orchestration** that follows your process

### Step 4: Test Immediately

```bash
/fetch-content "linkedin.com"
```

Your recipe is now investigating LinkedIn just like you would!

## What Just Happened?

The recipe creator:
1. **Captured your thinking** from just 5 answers
2. **Generated the implementation** from templates
3. **Tested it worked** with minimal validation
4. **Deployed instantly** for immediate use

## Common Recipe Types (With Examples)

### Analysis Recipe
```bash
/create-recipe "analysis" "I analyze code for patterns and improvements"
> Trigger: "Need to understand codebase quality"
> First step: "Run static analysis tools"
> Decision: "Focus on performance or maintainability?"
> Success: "Actionable improvements identified"
> Example: "Found 10 unnecessary abstractions in last review"
```

### Automation Recipe
```bash
/create-recipe "automation" "I automate repetitive deployment tasks"
> Trigger: "New code ready for production"
> First step: "Run test suite"
> Decision: "All tests green?"
> Success: "Deployed without manual intervention"
> Example: "Deploy API involves: test, build, push, verify"
```

### Research Recipe
```bash
/create-recipe "research" "I research technologies before adoption"
> Trigger: "Team considering new tool/framework"
> First step: "Check official documentation"
> Decision: "Does it solve our specific problem?"
> Success: "Clear recommendation with evidence"
> Example: "Evaluated Rust for service: too complex for team"
```

### Creative Recipe
```bash
/create-recipe "creative" "I create technical documentation"
> Trigger: "New feature needs documentation"
> First step: "Understand the feature completely"
> Decision: "Tutorial or reference style?"
> Success: "Users can follow without help"
> Example: "API docs include: overview, examples, reference"
```

## Tips for Better Recipes

### Be Specific About Triggers
❌ "When needed"
✅ "When PR is approved"
✅ "Every Monday morning"
✅ "When error rate exceeds 1%"

### Describe Observable First Steps
❌ "Think about the problem"
✅ "Open the error logs"
✅ "Run the diagnostic command"
✅ "Check the monitoring dashboard"

### Make Decisions Explicit
❌ "Decide what to do"
✅ "If errors > 10, investigate; else monitor"
✅ "Choose fastest solution if urgent, best if not"
✅ "Pick Python for data, Rust for systems"

### Define Measurable Success
❌ "It works"
✅ "All tests pass"
✅ "Response time < 100ms"
✅ "Customer confirms issue resolved"

## When Your Recipe Needs Refinement

If the recipe doesn't work perfectly:

1. **Run it and observe** - Where does it diverge from your process?
2. **Use `/refine-recipe`** - Tell it what was different
3. **It adjusts and retries** - Usually works on second attempt

Example refinement:
```bash
/refine-recipe "content-fetch"
> "It didn't check for authentication requirements first"
[Recipe updates to check auth before attempting fetch]
```

## The Power of Templates

Your recipes can be created from templates for common patterns:

### Investigation Template
```bash
/create-recipe --template="investigation" "security" "I investigate security vulnerabilities"
```

### Builder Template
```bash
/create-recipe --template="builder" "features" "I build new features test-first"
```

### Reviewer Template
```bash
/create-recipe --template="reviewer" "code" "I review code for team standards"
```

## Sharing Your Recipes

Once created, recipes can be:
- **Shared with team**: Others can use your thinking
- **Exported as files**: Version control your cognitive patterns
- **Composed together**: Build complex recipes from simple ones
- **Improved over time**: They learn from usage

## Advanced: The 1-Minute Recipe

For true speed, provide everything upfront:

```bash
/create-recipe "quick-fix" \
  --trigger="Bug reported" \
  --first="Reproduce locally" \
  --decision="Can fix in 10 min?" \
  --success="Bug no longer reproduces" \
  --example="Fixed null check in API handler"
```

Recipe created instantly!

## Debugging Recipes

If a recipe isn't thinking like you:

```bash
/debug-recipe "recipe-name"
```

This shows:
- What triggered each decision
- Why it chose each path
- Where it differs from your thinking
- How to adjust it

## The Meta-Recipe: Creating Recipe Creators

You can even create a recipe for creating recipes:

```bash
/create-recipe "recipe-creation" "I create recipes by interviewing users"
```

Now your recipe can create other recipes!

## Next Steps

1. **Create your first recipe** - Pick something you do often
2. **Use it immediately** - Test on real work
3. **Refine if needed** - One or two adjustments usually enough
4. **Share with team** - Multiply your impact

Remember: The goal isn't perfection, it's capturing enough of your thinking to be useful. Start simple, improve iteratively.

---

*"The best recipe is the one that exists and works, not the perfect one you haven't created yet."*