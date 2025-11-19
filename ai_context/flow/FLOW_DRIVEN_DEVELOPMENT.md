# Flow-Driven Development

## The Problem

AI code generation is fundamentally non-deterministic. We cannot blindly trust generated code. Additionally:

- **Vertical slicing** (across all layers) creates disjoint code and unnatural user journeys
- **Horizontal slicing** (by layer) leads to over/under-engineering without full context
- Agents lack real feedback loops beyond syntax checking
- Large commands like `/ultrathink-task` can generate massive amounts of code that needs guardrails

## The Solution: Validate Real User Flows

**Agents must PROVE to themselves that their code actually works** by validating real user flows as they go.

This is NOT about unit/integration tests (which validate consistently over time). This is about **immediate sanity checking** - like a developer opening a browser to see if their UI changes actually work.

## Core Principles

1. **Validate after each chunk of work** - Don't wait until the end
2. **Test real user behavior** - As close to actual user experience as possible
3. **All source code changes** require flow validation
4. **Record core flows** - If it breaks, the app is broken
5. **Keep it lightweight** - Verification scripts are ephemeral unless told otherwise

## What to Validate

**DO validate:**
- User experience - does it actually work as intended?
- Web apps: Use Playwright MCP to simulate user behavior
- Backend: Use curl or lightweight validation scripts

**DON'T validate:**
- Documentation
- Linters, formatters, TypeScript, code analysis
- (These are handled by tooling, not user flows)

---

## Writing User Flows

User flows should be written in natural language with arrow notation showing the sequence:

### Example Flow Format

```
Flow: Create New Project
Navigate to home page
  → Click "Create Project" button
  → Verify project page appears with project details and canvas visible
```

### Flow Format with Branching

When flows have conditional paths, use natural language to describe branches:

```
Flow: Add Widget to Project
Navigate to project page
  → Click "Add Widget" button
  → Try creating widget with name "Test Widget"
     If successful: verify it appears on canvas with correct styling
     If error: verify error message explains what went wrong
  → Test interaction with widget
     Click widget to select
     Verify selection highlight appears
```

### Dynamic Flow Cases

Flows should be **resilient to underlying UX changes**. Write them dynamically:

**❌ Bad (Brittle):**
```
Click button with ID "create-btn-123"
Verify div with class "project-card-container-main" exists
```

**✅ Good (Resilient):**
```
Click "Create Project" button (by text or role)
Verify project page shows project details and canvas
```

---

## Integration with Large Code Generation

When using `/ultrathink-task` or generating large amounts of code:

1. **After each chunk of code is generated**, pause and validate
2. **Identify which flow(s)** are affected by the changes
3. **Run flow validation** using Playwright MCP (for web) or curl (for backend)
4. **Only proceed** if validation passes
5. **Document new flows** if the chunk introduces core UX that doesn't exist yet

### Flow Validation Guidelines

**For Web Apps** (Natural language to Playwright MCP):

*Note: If Playwright MCP isn't installed, you can add it for Claude Code with:*
```bash
claude mcp add playwright npx @playwright/mcp@latest --scope user
```
*Then restart Claude Code for the changes to take effect. See the [Playwright MCP guide](https://github.com/microsoft/playwright-mcp) for more details.*

```
Navigate to http://localhost:3000
  → Click the 'Create Project' button
  → Verify that 'Project Details' text is visible on the page
  → Click into the project, verify that the canvas element appears
  → Try adding a test widget
     If successful: verify it shows up on canvas with correct styling
     If error: verify error message explains what went wrong
  → Test drag-and-drop interaction
     Drag widget to new position
     Verify position updates in real-time
```

**For Backend** (Quick flow validation with curl):
```bash
# Create project
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Project"}'

# Verify response: should see 201 status and project data

# Get project to confirm persistence
curl http://localhost:8000/api/projects/1

# Verify response: should see project with name "Test Project"
```

---

## Error Handling Flows

Always consider **unhappy paths** when validating flows.

Examples:
- What happens when user tries to create a project with no name?
- What happens when network fails during widget creation?
- What happens when user tries to modify a deleted widget?

**Always consider error cases** when implementing new features.

---

## Example Flow Validation Workflow

### Scenario: Implementing "Create Project" Feature

1. **Identify flow**: User described "click button to create project"
2. **Implement feature**: Generate React components, API endpoints, etc.
3. **Validate flow immediately**:
   - Use Playwright MCP
   - Navigate to home page
   - Click "Create Project"
   - Verify project page appears with expected elements
4. **If validation fails**: Fix immediately, don't move forward
5. **If validation passes**: Move to next chunk of work

---

## Remember

> **"If you can't verify the user flow works, don't ship it."**

This philosophy exists because AI-generated code cannot be trusted blindly. Flow validation isn't overhead - it's the core feedback loop that makes AI coding reliable.
