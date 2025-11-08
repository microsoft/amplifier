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

This section outlines the core implementation philosophy and guidelines for software development projects. It serves as a central reference for decision-making and development approach throughout the project.

### Core Philosophy

Embodies a Zen-like minimalism that values simplicity and clarity above all. This approach reflects:

- **Wabi-sabi philosophy**: Embracing simplicity and the essential. Each line serves a clear purpose without unnecessary embellishment.
- **Occam's Razor thinking**: The solution should be as simple as possible, but no simpler.
- **Trust in emergence**: Complex systems work best when built from simple, well-defined components that do one thing well.
- **Present-moment focus**: The code handles what's needed now rather than anticipating every possible future scenario.
- **Pragmatic trust**: The developer trusts external systems enough to interact with them directly, handling failures as they occur rather than assuming they'll happen.

This development philosophy values clear documentation, readable code, and belief that good architecture emerges from simplicity rather than being imposed through complexity.

### Core Design Principles

#### 1. Ruthless Simplicity

- **KISS principle taken to heart**: Keep everything as simple as possible, but no simpler
- **Minimize abstractions**: Every layer of abstraction must justify its existence
- **Start minimal, grow as needed**: Begin with the simplest implementation that meets current needs
- **Avoid future-proofing**: Don't build for hypothetical future requirements
- **Question everything**: Regularly challenge complexity in the codebase

#### 2. Architectural Integrity with Minimal Implementation

- **Preserve key architectural patterns**: Example: MCP for service communication, SSE for events, separate I/O channels, etc.
- **Simplify implementations**: Maintain pattern benefits with dramatically simpler code
- **Scrappy but structured**: Lightweight implementations of solid architectural foundations
- **End-to-end thinking**: Focus on complete flows rather than perfect components

#### 3. Library Usage Philosophy

- **Use libraries as intended**: Minimal wrappers around external libraries
- **Direct integration**: Avoid unnecessary adapter layers
- **Selective dependency**: Add dependencies only when they provide substantial value
- **Understand what you import**: No black-box dependencies

### Technical Implementation Guidelines

#### API Layer

- Implement only essential endpoints
- Minimal middleware with focused validation
- Clear error responses with useful messages
- Consistent patterns across endpoints

#### Database & Storage

- Simple schema focused on current needs
- Use TEXT/JSON fields to avoid excessive normalization early
- Add indexes only when needed for performance
- Delay complex database features until required

#### MCP Implementation

- Streamlined MCP client with minimal error handling
- Utilize FastMCP when possible, falling back to lower-level only when necessary
- Focus on core functionality without elaborate state management
- Simplified connection lifecycle with basic error recovery
- Implement only essential health checks

#### SSE & Real-time Updates

- Basic SSE connection management
- Simple resource-based subscriptions
- Direct event delivery without complex routing
- Minimal state tracking for connections

### #Event System

- Simple topic-based publisher/subscriber
- Direct event delivery without complex pattern matching
- Clear, minimal event payloads
- Basic error handling for subscribers

#### LLM Integration

- Direct integration with PydanticAI
- Minimal transformation of responses
- Handle common error cases only
- Skip elaborate caching initially

#### Message Routing

- Simplified queue-based processing
- Direct, focused routing logic
- Basic routing decisions without excessive action types
- Simple integration with other components

### Development Approach

#### Vertical Slices

- Implement complete end-to-end functionality slices
- Start with core user journeys
- Get data flowing through all layers early
- Add features horizontally only after core flows work

#### Iterative Implementation

- 80/20 principle: Focus on high-value, low-effort features first
- One working feature > multiple partial features
- Validate with real usage before enhancing
- Be willing to refactor early work as patterns emerge

#### Testing Strategy

- Emphasis on integration and end-to-end tests
- Manual testability as a design goal
- Focus on critical path testing initially
- Add unit tests for complex logic and edge cases
- Testing pyramid: 60% unit, 30% integration, 10% end-to-end

#### Error Handling

- Handle common errors robustly
- Log detailed information for debugging
- Provide clear error messages to users
- Fail fast and visibly during development

#### Problem Analysis Before Implementation

When tackling complex problems or new features, follow the "Analyze First, Don't Code" pattern:

##### The Pattern

1. **Initial Analysis Phase**

   - When given a complex task, FIRST respond with: "Let me analyze this problem before implementing"
   - Break down the problem into components
   - Identify potential challenges and edge cases
   - Consider multiple implementation approaches
   - Map out dependencies and impacts

2. **Structured Analysis Output**
   Before writing any code, provide:

   - **Problem decomposition**: Break complex problems into smaller, manageable pieces
   - **Approach options**: List 2-3 different ways to solve the problem
   - **Trade-offs**: Clearly state pros/cons of each approach
   - **Recommendation**: Choose the best approach with justification
   - **Implementation plan**: Step-by-step plan for the chosen approach

3. **Benefits of Analysis-First**
   - Prevents premature implementation that might need major refactoring
   - Identifies blockers and dependencies early
   - Results in cleaner, more maintainable code
   - Reduces the likelihood of missing requirements
   - Creates natural documentation of decision-making

##### When to Use This Pattern

**Always use for:**

- New feature implementation
- Complex refactoring tasks
- Performance optimization problems
- Integration with external systems
- Architecture decisions
- Bug fixes in unfamiliar code

**Skip for:**

- Simple typo fixes
- Straightforward CRUD operations
- Well-defined, isolated changes
- Tasks with clear, unambiguous requirements

##### Example Prompts That Trigger Analysis

Good prompts that should trigger analysis-first:

- "Implement a caching system for the API"
- "Optimize the database queries in the user service"
- "Add real-time notifications to the application"
- "Refactor the authentication flow"

Response pattern:

```
"Let me analyze this caching system requirement first:

1. Problem Analysis:
   - Current performance bottlenecks
   - Data freshness requirements
   - Cache invalidation needs

2. Implementation Options:
   - In-memory caching (Redis)
   - Application-level caching
   - CDN/edge caching

3. Recommendation: Redis because...

4. Implementation Plan:
   - Step 1: Set up Redis connection
   - Step 2: Implement cache wrapper
   - Step 3: Add invalidation logic
   ..."
```

##### Auxiliary Analysis Techniques

Combine with these complementary patterns:

- **Test-First Thinking**: Define test cases during analysis
- **Error-First Design**: Identify failure modes before success paths
- **Interface-First Development**: Define contracts before implementation
- **Documentation-While-Analyzing**: Write docs as you analyze

### Decision-Making Framework

When faced with implementation decisions, ask these questions:

1. **Necessity**: "Do we actually need this right now?"
2. **Simplicity**: "What's the simplest way to solve this problem?"
3. **Directness**: "Can we solve this more directly?"
4. **Value**: "Does the complexity add proportional value?"
5. **Maintenance**: "How easy will this be to understand and change later?"

### Areas to Embrace Complexity

Some areas justify additional complexity:

1. **Security**: Never compromise on security fundamentals
2. **Data integrity**: Ensure data consistency and reliability
3. **Core user experience**: Make the primary user flows smooth and reliable
4. **Error visibility**: Make problems obvious and diagnosable

### Areas to Aggressively Simplify

Push for extreme simplicity in these areas:

1. **Internal abstractions**: Minimize layers between components
2. **Generic "future-proof" code**: Resist solving non-existent problems
3. **Edge case handling**: Handle the common cases well first
4. **Framework usage**: Use only what you need from frameworks
5. **State management**: Keep state simple and explicit

### Practical Examples

#### Good Example: Direct SSE Implementation

```python
# Simple, focused SSE manager that does exactly what's needed
class SseManager:
    def __init__(self):
        self.connections = {}  # Simple dictionary tracking

    async def add_connection(self, resource_id, user_id):
        """Add a new SSE connection"""
        connection_id = str(uuid.uuid4())
        queue = asyncio.Queue()
        self.connections[connection_id] = {
            "resource_id": resource_id,
            "user_id": user_id,
            "queue": queue
        }
        return queue, connection_id

    async def send_event(self, resource_id, event_type, data):
        """Send an event to all connections for a resource"""
        # Direct delivery to relevant connections only
        for conn_id, conn in self.connections.items():
            if conn["resource_id"] == resource_id:
                await conn["queue"].put({
                    "event": event_type,
                    "data": data
                })
```

#### Bad Example: Over-engineered SSE Implementation

```python
# Overly complex with unnecessary abstractions and state tracking
class ConnectionRegistry:
    def __init__(self, metrics_collector, cleanup_interval=60):
        self.connections_by_id = {}
        self.connections_by_resource = defaultdict(list)
        self.connections_by_user = defaultdict(list)
        self.metrics_collector = metrics_collector
        self.cleanup_task = asyncio.create_task(self._cleanup_loop(cleanup_interval))

    # [50+ more lines of complex indexing and state management]
```

### Remember

- It's easier to add complexity later than to remove it
- Code you don't write has no bugs
- Favor clarity over cleverness
- The best code is often the simplest

This philosophy section serves as the foundational guide for all implementation decisions in the project.

## Modular Design Philosophy

This section outlines the modular design philosophy that guides the development of our software. It emphasizes the importance of creating a modular architecture that promotes reusability, maintainability, and scalability all optimized for use with LLM-based AI tools for working with "right-sized" tasks that the models can _easily_ accomplish (vs pushing their limits), allow working within single requests that fit entirely with context windows, and allow for the use of LLMs to help with the design and implementation of the modules themselves.

To achieve this, we follow a set of principles and practices that ensure our codebase remains clean, organized, and easy to work with. This modular design philosophy is particularly important as we move towards a future where AI tools will play a significant role in software development. The goal is to create a system that is not only easy for humans to understand and maintain but also one that can be easily interpreted and manipulated by AI agents. Use the following guidelines to support this goal:

_(how the agent structures work so modules can later be auto-regenerated)_

1. **Think “bricks & studs.”**

   - A _brick_ = a self-contained directory (or file set) that delivers one clear responsibility.
   - A _stud_ = the public contract (function signatures, CLI, API schema, or data model) other bricks latch onto.

2. **Always start with the contract.**

   - Create or update a short `README` or top-level docstring inside the brick that states: _purpose, inputs, outputs, side-effects, dependencies_.
   - Keep it small enough to hold in one prompt; future code-gen tools will rely on this spec.

3. **Build the brick in isolation.**

   - Put code, tests, and fixtures inside the brick’s folder.
   - Expose only the contract via `__all__` or an interface file; no other brick may import internals.

4. **Verify with lightweight tests.**

   - Focus on behaviour at the contract level; integration tests live beside the brick.

5. **Regenerate, don’t patch.**

   - When a change is needed _inside_ a brick, rewrite the whole brick from its spec instead of line-editing scattered files.
   - If the contract itself must change, locate every brick that consumes that contract and regenerate them too.

6. **Parallel variants are allowed but optional.**

   - To experiment, create sibling folders like `auth_v2/`; run tests to choose a winner, then retire the loser.

7. **Human ↔️ AI handshake.**

   - **Human (architect/QA):** writes or tweaks the spec, reviews behaviour.
   - **Agent (builder):** generates the brick, runs tests, reports results. Humans rarely need to read the code unless tests fail.

_By following this loop—spec → isolated build → behaviour test → regenerate—you produce code that stays modular today and is ready for automated regeneration tomorrow._
