# Claude Code Documentation Context

This directory contains documentation pages from [Anthropic's Claude Code documentation](https://docs.anthropic.com/) that have been downloaded for AI context and reference.

## Purpose

These files serve as authoritative documentation for Claude Code features, allowing AI assistants to provide accurate information about Claude Code capabilities, settings, and usage patterns without needing to access the web for common queries.

## File Naming Convention

Files are named based on their URL path from the docs site:

- URL: `https://docs.anthropic.com/en/docs/claude-code/settings#tools-available-to-claude`
- Filename: `CLAUDE_CODE_SETTINGS.md`

The naming follows these rules:

- Convert path segments to uppercase
- Replace `/` with `_`
- Remove language prefixes (`/en/docs/`)
- Ignore URL anchors (the `#` portion)
- Use `.md` extension

## How to Add New Documentation

1. Navigate to the desired page on https://docs.anthropic.com/
2. Click the "Copy page" button in the top right corner
3. Select "Copy page as Markdown for LLMs"
4. Create a new file in this directory following the naming convention
5. Paste the copied content into the file

## For AI Assistants

When using these files:

- Treat content as current, valid Claude Code documentation
- All relative URLs in the files are relative to `https://docs.anthropic.com/`
- If you encounter a relative link to documentation not yet downloaded:
  1. First check if the file exists using the naming convention above
  2. If not found, attempt to retrieve using available tools

**Note to AI:** Please update this section with the most effective method for retrieving missing documentation pages (web fetch tools vs browser-use MCP server) once you've determined which works best through testing.

## Maintenance

Periodically check for updates to the documentation on the Anthropic site, as these local copies may become outdated. The "Copy page" feature ensures we get the most LLM-friendly format of the documentation.
