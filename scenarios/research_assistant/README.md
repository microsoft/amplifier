# Research Assistant

An interactive CLI tool for conducting comprehensive web research with AI-powered analysis.

## Features

- **Interactive question clarification** - Refines vague research questions through dialogue
- **Automated web research** - Performs preliminary and deep research via web scraping
- **Credibility assessment** - Evaluates source quality and reliability
- **Fact verification** - Cross-checks claims against sources
- **Theme extraction** - Identifies key themes and patterns in research
- **Interactive theme refinement** - Collaborates with user to focus research
- **Report generation** - Synthesizes findings into comprehensive reports
- **Progress checkpointing** - Resume interrupted research sessions

## Usage

### Basic Research

```bash
make research-assistant Q="What are the latest trends in AI agent architectures?"
```

### Resume Interrupted Session

```bash
make research-assistant-resume
```

## Workflow

1. **Question Clarification** - Tool asks clarifying questions about:
   - Research type (pricing, product comparison, positioning, etc.)
   - Persona/lens (product manager, strategist, etc.)
   - Research depth (quick overview vs deep analysis)

2. **Preliminary Research** - Automated phase:
   - Web searches for relevant sources
   - Scrapes and reads articles
   - Assesses source credibility
   - Extracts initial themes
   - Verifies facts against sources

3. **Theme Refinement** - Interactive phase:
   - Presents extracted themes with recommendations
   - User provides feedback
   - Refines theme list based on input

4. **Deep Research** - Automated phase:
   - Focused research on refined themes
   - More detailed source analysis
   - Additional fact verification

5. **Report Generation** - Interactive phase:
   - Generates draft report
   - User provides feedback
   - Iteratively refines report
   - Outputs final document

## Session Management

Research sessions are saved in `.data/research_assistant/{session_id}/`:
- `research_context.json` - Question and research parameters
- `preliminary_findings.json` - Initial research results
- `themes.json` - Extracted and refined themes
- `deep_research.json` - Detailed research findings
- `report_draft.md` - Draft report
- `final_report.md` - Final research report

## Architecture

Built using the Amplifier CLI Tool pattern:
- **Code for structure** - Reliable iteration, state management, HTTP scraping
- **AI for intelligence** - Credibility assessment, theme extraction, synthesis
- **Progressive phases** - Clear workflow stages with checkpoints
- **Resume capability** - Can interrupt and continue at any phase

## Implementation Notes

- Uses HTTP + BeautifulSoup for web scraping (simple, sufficient for most research)
- Claude Code SDK for AI analysis tasks
- File-based state management for progress persistence
- Interactive CLI prompts for user dialogue (not file-based editing)
