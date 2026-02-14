# AI Assistant Guidance

This file provides guidance to AI assistants when working with code in this repository.

---

## 💎 CRITICAL: Respect User Time - Test Before Presenting

**The user's time is their most valuable resource.** When you present work as "ready" or "done", you must have:

1. **Tested it yourself thoroughly** - Don't make the user your QA
2. **Fixed obvious issues** - Syntax errors, import problems, broken logic
3. **Verified it actually works** - Run tests, check structure, validate logic
4. **Only then present it** - "This is ready for your review" means YOU'VE already validated it

**User's role:** Strategic decisions, design approval, business context, stakeholder judgment
**Your role:** Implementation, testing, debugging, fixing issues before engaging user

**Anti-pattern**: "I've implemented X, can you test it and let me know if it works?"
**Correct pattern**: "I've implemented and tested X. Tests pass, structure verified, logic validated. Ready for your review. Here is how you can verify."

**Remember**: Every time you ask the user to debug something you could have caught, you're wasting their time on non-stakeholder work. Be thorough BEFORE engaging them.

---

## Git Commit Message Guidelines

When creating git commit messages, always insert the following at the end of your commit message:

```
🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>
```

---

## Important: Consult DISCOVERIES.md

Before implementing solutions to complex problems:

1. **Check DISCOVERIES.md** for similar issues that have already been solved
2. **Update DISCOVERIES.md** when you:
   - Encounter non-obvious problems that require research or debugging
   - Find conflicts between tools or libraries
   - Discover framework-specific patterns or limitations
   - Solve issues that future developers might face again
3. **Format entries** with: Date, Issue, Root Cause, Solution, and Prevention sections

## Sub-Agent Optimization Strategy

**IMPORTANT**: Always proactively use sub-agents for tasks that match their expertise. Don't wait to be asked.

When working on complex tasks, always evaluate if a specialized sub-agent would improve outcomes:

1. **Before starting work** - Consider if existing agents fit the task
2. **During challenges** - If struggling, propose a new specialized agent
3. **After completion** - Reflect on where an agent could have helped
4. **Agent creation is cheap** - Better to have specialized tools than struggle with generic ones

If a new agent would help, pause work and create it first. This investment pays off immediately.

### Available Specialized Agents

The project includes specialized agents for various tasks (see `.claude/AGENTS_CATALOG.md` for full details):

- **Development**: zen-code-architect, architecture-reviewer, bug-hunter, test-coverage, modular-builder, refactor-architect, integration-specialist
- **Knowledge Synthesis**: triage-specialist, analysis-expert, synthesis-master, content-researcher
- **Knowledge Synthesis System**: concept-extractor, insight-synthesizer, tension-keeper, uncertainty-navigator, knowledge-archaeologist, visualization-architect
- **Meta**: subagent-architect (creates new agents)

Use these agents proactively when their expertise matches your task.

## Subagent Resilience Protocol

Subagents launched via the Task tool have their own context windows that can fill up during execution. When this happens, agents either stop abruptly with partial results or shift into "summary mode" instead of completing actual work. This protocol prevents both failure modes.

### Turn Budgets

Every Task dispatch must include a `max_turns` parameter. Use these starting values:

| Agent Role | max_turns | Examples |
|------------|-----------|----------|
| Quick tasks | 5-8 | Haiku scouts, context gathering, file searches |
| Research / exploration | 8-10 | Codebase exploration, documentation lookup |
| Review | 10-12 | test-coverage, security-guardian, code review |
| Analysis | 12-15 | zen-architect, bug-hunter, design analysis |
| Implementation | 15-20 | modular-builder, file creation and editing |

These values are tuned through observation. If an agent consistently needs resume cycles, increase its budget. If it finishes well under budget, decrease it.

### Resume Protocol

When an agent returns, the orchestrator evaluates completeness and resumes if needed:

1. **Dispatch** the agent with `max_turns=N`
2. **Receive** the result and `agent_id`
3. **Evaluate** completeness:
   - **Complete**: Files written, conclusions stated, explicit "done" markers → use the result
   - **Incomplete**: Trailing "I'll now...", partial lists, no conclusion, mid-sentence stops → resume
4. **Resume** with `resume=agent_id` and prompt: "Continue your work. You were stopped due to turn limits. Focus on completing the remaining items."
5. **Limit** to 3 resume cycles maximum, then escalate to the user

The agent does not need to know about this pattern. It gets stopped, gets resumed with full prior context, and continues. Each resume gets a fresh output budget.

### Task Decomposition Guidelines

Right-size tasks before dispatch to prevent context exhaustion upstream:

| Dimension | Guideline |
|-----------|-----------|
| Files to read | 3-5 per agent |
| Files to modify | 1-3 per agent |
| Objectives | 1 per agent — single clear deliverable |
| Output scope | One component, module, or focused concern |

**Decompose large tasks:**
- "Implement the authentication system" → 4 agents: token generation, middleware, login endpoint, session storage
- "Review all changed files" → 2 agents by concern: "review auth changes", "review API changes"

**Indivisible tasks** (single large file, atomic refactor): Accept them with generous `max_turns` and rely on the resume protocol.

**Where these rules apply:**
- `writing-plans` skill — each plan step must pass the sizing test
- `subagent-driven-development` — validate sizing before dispatch
- `dispatching-parallel-agents` — each parallel agent gets one focused task
- Any manual Task dispatch from the main conversation

## Incremental Processing Pattern

When building batch processing systems, always save progress after every item processed:

- **Save continuously**: Write results after each item, not at intervals or only at completion
- **Fixed filenames**: Use consistent filenames (e.g., `results.json`) that overwrite, not timestamps
- **Enable interruption**: Users can abort anytime without losing processed items
- **Support incremental updates**: New items can be added without reprocessing existing ones

The bottleneck is always the processing (LLM APIs, network calls), never disk I/O.

## Partial Failure Handling Pattern

This should not be the default approach, but should be used when appropriate. When building systems for processing large batches with multiple sub-processors where it is more important for as much progress as possible to be made while unattended is more important than complete success, implement graceful degradation:

- **Continue on failure**: Don't stop the entire batch when individual processors fail
- **Save partial results**: Store whatever succeeded - better than nothing
- **Track failure reasons**: Distinguish between "legitimately empty" and "extraction failed"
- **Support selective retry**: Re-run only failed processors, not entire items
- **Report comprehensively**: Show success rates per processor and items needing attention

This approach maximizes value from long-running batch processes. A 4-hour unattented run that completes
with partial results is better than one that fails early with nothing to show. Users can then
fix issues and retry only what failed.

## Decision Tracking System

Significant architectural and implementation decisions are documented in `ai_working/decisions/`. This preserves context across AI sessions and prevents uninformed reversals of past choices.

### When to Consult Decision Records

1. **Before proposing major changes** - Check if relevant decisions exist
2. **When questioning existing patterns** - Understand the original rationale
3. **During architecture reviews** - Reference historical context
4. **When choosing between approaches** - Learn from past trade-offs

### When to Create Decision Records

Create a new decision record for:

- Architectural choices affecting system structure
- Selection between multiple viable approaches
- Adoption of new patterns, tools, or libraries
- Reversal or significant modification of previous decisions

### Format

See `ai_working/decisions/README.md` for the decision record template. Each decision includes context, rationale, alternatives considered, and review triggers.

### Remember

Decisions CAN change, but should change with full understanding of why they were originally made. This prevents cycling through the same alternatives without learning.

## Configuration Management: Single Source of Truth

### Principle

Every configuration setting should have exactly ONE authoritative location. All other uses should reference or derive from that single source.

### Implementation Guidelines

1. **Tool Configuration Hierarchy**:

   - `pyproject.toml` - Python project settings (primary)
   - `ruff.toml` - Ruff-specific settings only if not in pyproject.toml
   - `.vscode/settings.json` - IDE settings that reference project config
   - `Makefile` - Commands that use project config, not duplicate it

2. **Common Configuration Locations**:

   - **Python dependencies**: `pyproject.toml` only (managed by uv)
   - **Code exclusions**: `pyproject.toml` [tool.pyright] exclude
   - **Formatting rules**: `ruff.toml` or `pyproject.toml` [tool.ruff]
   - **Type checking**: `pyproject.toml` [tool.pyright]

3. **Reading Configuration in Tools**:

   ```python
   # Good: Read from authoritative source
   config = tomllib.load(open("pyproject.toml", "rb"))
   excludes = config["tool"]["pyright"]["exclude"]

   # Bad: Hardcode the same values
   excludes = [".venv", "__pycache__", "node_modules"]
   ```

4. **When Duplication is Acceptable**:
   - Performance-critical paths where reading config is too slow
   - Build scripts that must work before dependencies are installed
   - Emergency fallbacks when config files are corrupted

### Benefits

- Changes propagate automatically
- Reduces maintenance burden
- Prevents configuration drift
- Makes the codebase more maintainable

### Example Application

Instead of:

- `check_stubs.py` hardcoding: `{".venv", "__pycache__", ".git"}`
- `pyproject.toml` having: `exclude = [".venv", "__pycache__", "node_modules"]`
- `make check` skipping: `--exclude .venv --exclude __pycache__`

We have:

- `pyproject.toml` as the single source: `exclude = [...]`
- All tools read from pyproject.toml
- Makefile references the config: `make check` uses settings from pyproject.toml

## Response Authenticity Guidelines

### Professional Communication Without Sycophancy

**CRITICAL**: Maintain professional, authentic communication. Avoid sycophantic language that undermines trust.

**NEVER use phrases like:**

- "You're absolutely right!"
- "That's a brilliant idea/observation!"
- "What an excellent point!"
- "I completely agree!"
- "That's exactly right!"

**INSTEAD, engage substantively:**

- Analyze the actual merit of ideas
- Point out trade-offs and considerations
- Provide honest technical assessment
- Disagree constructively when appropriate
- Focus on the code and problem, not praising the person

**Examples of appropriate responses:**

- "Let me analyze that approach..." (then actually analyze)
- "That has trade-offs to consider..." (then discuss them)
- "Here's what that would involve..." (then explain implications)
- "There might be issues with..." (then explain concerns)

**Remember:** You're a professional tool, not a cheerleader. Users value honest, direct feedback over empty agreement.

## Zero-BS Principle: No Unnecessary Stubs or Placeholders

**CRITICAL**: Build working code. Avoid placeholders that serve no purpose.

### Patterns to Avoid

**NEVER write these without immediate implementation:**

- `raise NotImplementedError` (except in abstract base classes)
- `TODO` comments without accompanying code
- `pass` as a placeholder (except for legitimate Python patterns)
- Mock/fake/dummy functions that don't work
- `return {}  # stub` or similar placeholder returns
- Coming soon features
- `...` as implementation

### Legitimate Uses of These Patterns

**Some examples of acceptable patterns:**

- `@click.group()` with `pass` body (required by Click framework)
- `except: pass` for graceful degradation when errors are expected
- `@abstractmethod` with `raise NotImplementedError` (Python ABC pattern)
- `pass` in protocol definitions or type stubs
- Empty `__init__.py` files (Python package markers)

_Note: These are illustrative examples to help define the philosophy. Use judgment to identify similar legitimate patterns vs actual stubs._

### Required Approach

**When requirements are vague:**

- Ask for specific details
- Implement only what you can make work
- Reduce scope to achievable functionality

**When facing external dependencies:**

- Use file-based storage instead of databases
- Use local processing instead of external APIs
- Build the simplest working version

**YAGNI (You Aren't Gonna Need It):**

- Don't create unused parameters
- Don't build for hypothetical futures
- Don't add interfaces without implementations

### The Test

Ask yourself: "Does this code DO something useful right now?"

- If yes: Keep it
- If no: Either implement it fully or remove it

### Examples

**BAD (stub):**

```python
def process_payment(amount):
    # TODO: Implement Stripe integration
    raise NotImplementedError("Payment processing coming soon")
```

**GOOD (working):**

```python
def process_payment(amount, payments_file="payments.json"):
    """Record payment to local file - fully functional."""
    payment = {"amount": amount, "timestamp": datetime.now().isoformat()}

    # Load existing payments
    if Path(payments_file).exists():
        with open(payments_file) as f:
            payments = json.load(f)
    else:
        payments = []

    # Add and save
    payments.append(payment)
    with open(payments_file, 'w') as f:
        json.dump(payments, f)

    return payment
```

Every function must work or not exist. Every file must be complete or not created.

## Build/Test/Lint Commands

- Install dependencies: `make install` (uses uv)
- Add new dependencies: `uv add package-name` (in the specific project directory)
- Add development dependencies: `uv add --dev package-name`
- Run all checks: `make check` (runs lint, format, type check)
- Run all tests: `make test` or `make pytest`
- Run a single test: `uv run pytest tests/path/to/test_file.py::TestClass::test_function -v`
- Upgrade dependency lock: `make lock-upgrade`

## Dependency Management

- **ALWAYS use `uv`** for Python dependency management in this project
- To add dependencies: `cd` to the specific project directory and run `uv add <package>`
- This ensures proper dependency resolution and updates both `pyproject.toml` and `uv.lock`
- Never manually edit `pyproject.toml` dependencies - always use `uv add`

## Code Style Guidelines

- Use Python type hints consistently including for self in class methods
- Import statements at top of files, organized by standard lib, third-party, local
- Use descriptive variable/function names (e.g., `get_workspace` not `gw`)
- Use `Optional` from typing for optional parameters
- Initialize variables outside code blocks before use
- All code must work with Python 3.11+
- Use Pydantic for data validation and settings

## Formatting Guidelines

- Line length: 120 characters (configured in ruff.toml)
- Use `# type: ignore` for Reflex dynamic methods
- For complex type ignores, use `# pyright: ignore[specificError]`
- When working with Reflex state setters in lambdas, keep them on one line to avoid pyright errors
- The project uses ruff for formatting and linting - settings in `ruff.toml`
- VSCode is configured to format on save with ruff
- **IMPORTANT**: All files must end with a newline character (add blank line at EOF)

## File Organization Guidelines

- **IMPORTANT: Do NOT add files to the `/tools` directory** - This directory has a specific purpose that the project owner manages. Place new utilities in appropriate module directories instead.
- Organize code into proper module directories.
- Keep utility scripts with their related modules, not in a generic tools folder
- The `/tools` directory is reserved for specific build and development tools chosen by the project maintainer

### Amplifier CLI Tool Organization

**For detailed guidance on organizing amplifier CLI tools, consult the `amplifier-cli-architect` agent.**

This specialized agent has comprehensive context on:

- Progressive Maturity Model (scenarios/ vs ai_working/ vs amplifier/)
- Tool creation patterns and templates
- Documentation requirements
- Philosophy alignment (@scenarios/README.md)
- THE exemplar to model after: @scenarios/blog_writer/

When creating amplifier CLI tools:

1. Delegate to `amplifier-cli-architect` in GUIDE mode for complete guidance
2. When in doubt about tool organization, consult `amplifier-cli-architect` and validate against @scenarios/blog_writer/ implementation

## Dev Environment Tips

- Run `make` to create a virtual environment and install dependencies.
- Activate the virtual environment with `source .venv/bin/activate` (Linux/Mac) or `.venv\Scripts\activate` (Windows).

## Testing Instructions

- Run `make check` to run all checks including linting, formatting, and type checking.
- Run `make test` to run the tests.

## IMPORTANT: Service Testing After Code Changes

After making code changes, you MUST:

1. **Run `make check`** - This catches syntax, linting, and type errors
2. **Start the affected service** - This catches runtime errors and invalid API usage
3. **Test basic functionality** - Send a test request or verify the service starts cleanly
4. **Stop the service** - Use Ctrl+C or kill the process
   - IMPORTANT: Always stop services you start to free up ports

### Common Runtime Errors Not Caught by `make check`

- Invalid API calls to external libraries
- Import errors from circular dependencies
- Configuration or environment errors
- Port conflicts if services weren't stopped properly

## Documentation for External Libraries

### DeepWiki MCP Server

For GitHub repository documentation and codebase understanding:

- **Use `ask_question` tool exclusively** - Direct questions get focused answers with code examples
- **Don't use `read_wiki_contents`** - It exceeds token limits for all real repositories
- **Be specific with questions** - "How does the CSS theming system work?" beats "Tell me about this repo"
- **Examples of effective queries:**
  - "What plugins are available and how do you use them?"
  - "How do you create a basic presentation with HTML structure?"
  - "What is the core architecture including controllers and event handling?"

This follows our ruthless simplicity principle: use what works (targeted questions), skip what doesn't (bulk content fetching).

### Context7 MCP Server

For general library documentation:

- Use as first tool for searching up-to-date documentation on external libraries
- Provides simple interface to search through documentation quickly
- Fall back to web search if Context7 doesn't have the information needed

## Implementation Philosophy

See `@ai_context/IMPLEMENTATION_PHILOSOPHY.md` for the full implementation philosophy (already loaded via CLAUDE.md @imports).

## Modular Design Philosophy

See `@ai_context/MODULAR_DESIGN_PHILOSOPHY.md` for the modular design philosophy (already loaded via CLAUDE.md @imports).
