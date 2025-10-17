# Command Reference

This guide documents all custom commands available in this AI code template.

## 🧠 Core Commands

### `/prime` - Philosophy-Aligned Environment Setup

**Purpose**: Initialize your project with the right environment and philosophical grounding.

**What it does**:

1. Installs all dependencies (`make install`)
2. Activates virtual environment
3. Runs quality checks (`make check`)
4. Runs tests (`make test`)
5. Loads philosophy documents
6. Prepares AI assistant for aligned development

**Usage**:

```
/prime
```

**When to use**:

- Starting a new project
- After cloning the template
- Beginning a new AI assistant session
- When you want to ensure philosophical alignment

---

### `/ultrathink-task` - Multi-Agent Deep Analysis

**Purpose**: Solve complex problems through orchestrated AI collaboration.

**Architecture**:

```
Coordinator Agent
├── Architect Agent - Designs approach
├── Research Agent - Gathers knowledge
├── Coder Agent - Implements solution
└── Tester Agent - Validates results
```

**Usage**:

```
/ultrathink-task <detailed task description>
```

**Examples**:

```
/ultrathink-task Build a REST API with:
- User authentication using JWT
- Rate limiting
- Comprehensive error handling
- OpenAPI documentation
- Full test coverage

/ultrathink-task Debug this complex issue:
[paste error trace]
The error happens when users upload files larger than 10MB.
Check our patterns in IMPLEMENTATION_PHILOSOPHY.md
```

**When to use**:

- Complex features requiring architecture
- Problems needing research and implementation
- Tasks benefiting from multiple perspectives
- When you want systematic, thorough solutions

---

### `/test-webapp-ui` - Automated UI Testing

**Purpose**: Automatically discover and test web applications with visual validation.

**Features**:

- Auto-discovers running web apps
- Starts static servers if needed
- Tests functionality and aesthetics
- Manages server lifecycle
- Cross-browser support via MCP

**Usage**:

```
/test-webapp-ui <url_or_description> [test-focus]
```

**Examples**:

```
/test-webapp-ui http://localhost:3000

/test-webapp-ui "the React dashboard in examples/dashboard"

/test-webapp-ui http://localhost:8080 "focus on mobile responsiveness"
```

**Server Patterns Supported**:

- Running applications (auto-detected via `lsof`)
- Static HTML sites (auto-served)
- Node.js apps (`npm start`, `npm run dev`)
- Python apps (Flask, Django, FastAPI)
- Docker containers

---

## 📋 Planning Commands

### `/create-plan` - Strategic Planning

**Purpose**: Create structured implementation plans for complex features.

**Usage**:

```
/create-plan <feature description>
```

**Output**: Detailed plan with:

- Architecture decisions
- Implementation steps
- Testing strategy
- Potential challenges
- Success criteria

---

### `/execute-plan` - Plan Execution

**Purpose**: Execute a previously created plan systematically.

**Usage**:

```
/execute-plan
```

**Behavior**:

- Reads the most recent plan
- Executes steps in order
- Tracks progress
- Handles errors gracefully
- Reports completion status

---

## 🔍 Review Commands

### `/review-changes` - Comprehensive Change Review

**Purpose**: Review all recent changes for quality and consistency.

**What it reviews**:

- Code style compliance
- Philosophy alignment
- Test coverage
- Documentation updates
- Security considerations

**Usage**:

```
/review-changes
```

---

### `/review-code-at-path` - Targeted Code Review

**Purpose**: Deep review of specific files or directories.

**Usage**:

```
/review-code-at-path <file_or_directory>
```

**Examples**:

```
/review-code-at-path src/api/auth.py

/review-code-at-path components/Dashboard/
```

---

## 🛠️ Creating Custom Commands

### Claude Code

#### Command Structure

Create a new file in `.claude/commands/your-command.md`:

```markdown
## Usage

`/your-command <required-arg> [optional-arg]`

## Context

- Brief description of what the command does
- When and why to use it
- Any important notes or warnings

### Process

1. First step with clear description
2. Second step with details
3. Continue for all steps
4. Include decision points
5. Handle edge cases

## Output Format

Describe what the user will see:

- Success messages
- Error handling
- Next steps
- Any generated artifacts
```

### Gemini CLI

#### Command Structure

Create a new file in `.gemini/commands/your-command.toml`:

```toml
description = "Brief description of the command"
prompt = """## Usage

`/your-command <required-arg> [optional-arg]`

## Context

- Brief description of what the command does
- When and why to use it
- Any important notes or warnings

## Process

1. First step with clear description
2. Second step with details
3. Continue for all steps
4. Include decision points
5. Handle edge cases

## Output Format

Describe what the user will see:
- Success messages
- Error handling
- Next steps
- Any generated artifacts
"""
```

### Best Practices

1. **Clear Usage**: Show exact syntax with examples
2. **Context Section**: Explain when and why to use
3. **Detailed Process**: Step-by-step instructions
4. **Error Handling**: What to do when things go wrong
5. **Output Format**: Set clear expectations

### Advanced Features

#### Sub-Agent Orchestration

```markdown
## Process

1. **Architect Agent**: Design the approach

   - Consider existing patterns
   - Plan component structure

2. **Implementation Agent**: Build the solution

   - Follow architecture plan
   - Apply coding standards

3. **Testing Agent**: Validate everything
   - Unit tests
   - Integration tests
   - Manual verification
```

#### Conditional Logic

```markdown
## Process

1. Check if Docker is running

   - If yes: Use containerized approach
   - If no: Use local development

2. Determine project type
   - Node.js: Use npm/yarn commands
   - Python: Use pip/poetry/uv
   - Go: Use go modules
```

#### File Operations

```markdown
## Process

1. Read configuration: @config/settings.json
2. Generate based on template: @templates/component.tsx
3. Write to destination: src/components/NewComponent.tsx
4. Update index: @src/components/index.ts
```

## 🎯 Command Combinations

### Power Workflows

**Full Feature Development**:

```
/prime
/create-plan "user authentication system"
/execute-plan
/test-webapp-ui
/review-changes
```

**Rapid Prototyping**:

```
/ultrathink-task "create a dashboard mockup"
/test-webapp-ui "check the dashboard"
[iterate with natural language]
```

**Debug Session**:

```
/prime
[paste error]
/ultrathink-task "debug this error: [details]"
[test fix]
/review-code-at-path [changed files]
```

## 🚀 Tips for Effective Command Usage

1. **Start with `/prime`**: Always ensure philosophical alignment
2. **Use `/ultrathink-task` for complexity**: Let multiple agents collaborate
3. **Iterate naturally**: Commands start workflows, natural language refines
4. **Combine commands**: They're designed to work together
5. **Trust the process**: Let commands handle the details

## 📝 Command Development Guidelines

When creating new commands:

1. **Single Responsibility**: Each command does one thing well
2. **Composable**: Design to work with other commands
3. **Progressive**: Simple usage, advanced options
4. **Documented**: Clear examples and edge cases
5. **Tested**: Include validation in the process

## 🔗 Related Documentation

- [Automation Guide](automation.md) - Hooks and triggers
- [Philosophy Guide](philosophy.md) - Guiding principles
