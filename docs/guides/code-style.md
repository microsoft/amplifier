# Code Style Guide

On-demand reference for Python code style, formatting, file organization, dev environment, service testing, and external library documentation. Retrieved via `/docs search code style`.

---

## Python Code Style

- Use Python type hints consistently, including for `self` in class methods
- Import statements at top of files, organized: standard lib → third-party → local
- Use descriptive variable/function names (e.g., `get_workspace` not `gw`)
- Use `Optional` from typing for optional parameters
- Initialize variables outside code blocks before use
- All code must work with Python 3.11+
- Use Pydantic for data validation and settings

## Formatting

- Line length: 120 characters (configured in `ruff.toml`)
- Use `# type: ignore` for Reflex dynamic methods
- For complex type ignores, use `# pyright: ignore[specificError]`
- When working with Reflex state setters in lambdas, keep them on one line to avoid pyright errors
- The project uses ruff for formatting and linting — settings in `ruff.toml`
- VSCode is configured to format on save with ruff
- All files must end with a newline character (add blank line at EOF)

## File Organization

- **Do NOT add files to the `/tools` directory** — this directory has a specific purpose that the project owner manages. Place new utilities in appropriate module directories instead.
- Organize code into proper module directories
- Keep utility scripts with their related modules, not in a generic tools folder

### Amplifier CLI Tool Organization

For detailed guidance on organizing amplifier CLI tools, consult the `amplifier-cli-architect` agent. It has context on:

- Progressive Maturity Model (scenarios/ vs ai_working/ vs amplifier/)
- Tool creation patterns and templates
- Philosophy alignment (`@scenarios/README.md`)
- The exemplar to model after: `@scenarios/blog_writer/`

## Dev Environment

- Run `make` to create a virtual environment and install dependencies
- Activate the virtual environment:
  - Linux/Mac: `source .venv/bin/activate`
  - Windows: `.venv\Scripts\activate`
- Python managed via UV; Node.js v24

## Service Testing After Code Changes

After making code changes, you MUST:

1. **Run `make check`** — catches syntax, linting, and type errors
2. **Start the affected service** — catches runtime errors and invalid API usage
3. **Test basic functionality** — send a test request or verify the service starts cleanly
4. **Stop the service** — always stop services you start to free up ports

### Common Runtime Errors Not Caught by `make check`

- Invalid API calls to external libraries
- Import errors from circular dependencies
- Configuration or environment errors
- Port conflicts if services weren't stopped properly

## External Library Documentation

### DeepWiki MCP Server

For GitHub repository documentation and codebase understanding:

- **Use `ask_question` tool exclusively** — direct questions get focused answers with code examples
- **Don't use `read_wiki_contents`** — it exceeds token limits for all real repositories
- **Be specific with questions** — "How does the CSS theming system work?" beats "Tell me about this repo"
- Examples of effective queries:
  - "What plugins are available and how do you use them?"
  - "How do you create a basic presentation with HTML structure?"
  - "What is the core architecture including controllers and event handling?"

### Context7 MCP Server

For general library documentation:

- Use as first tool for searching up-to-date documentation on external libraries
- Provides simple interface to search through documentation quickly
- Fall back to web search if Context7 doesn't have the information needed
