#!/usr/bin/env python3
"""Generate OpenCode agents/*/SKILL.md from canonical .claude/agents/*.md.

Reads each agent definition from .claude/agents/, parses the YAML frontmatter,
adds OpenCode-specific fields (recommended_model, tools), and writes to
agents/{name}/SKILL.md.

This keeps .claude/agents/ as the single source of truth for agent definitions.
Run this script whenever agents are updated to sync the OpenCode format.

Usage:
    python scripts/sync-agents-to-opencode.py [--dry-run]
"""

import os
import re
import sys
from pathlib import Path

# Agent → recommended Gemini model mapping
# Design/architecture agents use 'pro', implementation/utility agents use 'flash'
MODEL_MAP = {
    # Pro (design, architecture, analysis, knowledge)
    "ambiguity-guardian": "pro",
    "amplifier-cli-architect": "pro",
    "analysis-engine": "pro",
    "api-contract-designer": "pro",
    "art-director": "pro",
    "concept-extractor": "pro",
    "content-researcher": "pro",
    "contract-spec-author": "pro",
    "database-architect": "pro",
    "design-system-architect": "pro",
    "graph-builder": "pro",
    "insight-synthesizer": "pro",
    "knowledge-archaeologist": "pro",
    "layout-architect": "pro",
    "module-intent-architect": "pro",
    "pattern-emergence": "pro",
    "responsive-strategist": "pro",
    "subagent-architect": "pro",
    "visualization-architect": "pro",
    "voice-strategist": "pro",
    "zen-architect": "pro",
    # Flash (implementation, debugging, testing, cleanup)
    "animation-choreographer": "flash",
    "bug-hunter": "flash",
    "component-designer": "flash",
    "integration-specialist": "flash",
    "modular-builder": "flash",
    "performance-optimizer": "flash",
    "post-task-cleanup": "flash",
    "security-guardian": "flash",
    "test-coverage": "flash",
}

# Default tools for agents that need them (OpenCode uses this for tool access)
# Agents without explicit tools get all tools by default in OpenCode
TOOLS_MAP = {
    "ambiguity-guardian": "Glob, Grep, LS, Read, WebFetch, TodoWrite, WebSearch, BashOutput, KillBash",
    "amplifier-cli-architect": "Glob, Grep, LS, Read, WebFetch, TodoWrite, WebSearch, BashOutput, KillBash",
    "analysis-engine": "Glob, Grep, LS, Read, WebFetch, TodoWrite, WebSearch, BashOutput, KillBash, Bash",
    "api-contract-designer": "Glob, Grep, LS, Read, WebFetch, TodoWrite, WebSearch, BashOutput, KillBash, Bash",
    "content-researcher": "Glob, Grep, LS, Read, WebFetch, TodoWrite, WebSearch, BashOutput, KillBash, Bash",
    "database-architect": "Glob, Grep, LS, Read, WebFetch, TodoWrite, WebSearch, BashOutput, KillBash, Bash",
    "post-task-cleanup": "Glob, Grep, LS, Read, WebFetch, TodoWrite, WebSearch, BashOutput, KillBash, Bash",
    "security-guardian": "Glob, Grep, LS, Read, WebFetch, TodoWrite, WebSearch, BashOutput, KillBash, Bash",
}


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter and body from a markdown file.

    Returns:
        Tuple of (frontmatter_dict, body_text)
    """
    match = re.match(r"^---\n(.*?)\n---\n?(.*)", content, re.DOTALL)
    if not match:
        return {}, content

    fm_text = match.group(1)
    body = match.group(2)

    # Simple YAML parsing for our known frontmatter structure
    fm = {}
    current_key = None
    current_value = []

    for line in fm_text.split("\n"):
        # Key: value line
        kv_match = re.match(r"^(\w+):\s*(.*)", line)
        if kv_match and not line.startswith("  "):
            # Save previous key if accumulating
            if current_key and current_value:
                fm[current_key] = "\n".join(current_value)
            elif current_key:
                pass  # Already set

            key = kv_match.group(1)
            value = kv_match.group(2).strip()

            if value == "|":
                current_key = key
                current_value = []
            else:
                fm[key] = value
                current_key = None
                current_value = []
        elif current_key is not None:
            # Continuation of block scalar
            current_value.append(line)

    # Save last accumulated value
    if current_key and current_value:
        fm[current_key] = "\n".join(current_value)

    return fm, body


def generate_skill_md(
    fm: dict, body: str, agent_name: str, frozen_header: str = ""
) -> str:
    """Generate OpenCode SKILL.md content from parsed frontmatter and body."""
    recommended_model = MODEL_MAP.get(agent_name, "pro")
    tools = TOOLS_MAP.get(agent_name, "")

    # Build frontmatter
    lines = ["---"]
    lines.append(f"recommended_model: {recommended_model}")
    lines.append(f"name: {fm.get('name', agent_name)}")

    # Description as block scalar (preserve original indentation from source)
    desc = fm.get("description", "")
    if desc:
        lines.append("description: |")
        for desc_line in desc.split("\n"):
            # Source lines already have 2-space indent; pass through as-is
            lines.append(desc_line if desc_line.strip() else "")
    if tools:
        lines.append(f"tools: {tools}")
    lines.append(f"model: {fm.get('model', 'inherit')}")
    lines.append("---")

    # Inject Frozen Zone if provided
    content = "\n".join(lines) + "\n"
    if frozen_header:
        content += (
            f"<!-- FROZEN ZONE START -->\n{frozen_header}\n<!-- FROZEN ZONE END -->\n\n"
        )

    return content + body


def main():
    dry_run = "--dry-run" in sys.argv

    repo_root = Path(__file__).parent.parent
    agents_src = repo_root / ".claude" / "agents"
    agents_dst = repo_root / "agents"

    if not agents_src.is_dir():
        print(f"Error: Source directory not found: {agents_src}")
        sys.exit(1)

    agent_files = sorted(agents_src.glob("*.md"))
    if not agent_files:
        print("No agent files found in .claude/agents/")
        sys.exit(1)

    # Read Frozen Header
    frozen_header_path = repo_root / ".claude" / "context" / "frozen_header.md"
    frozen_header = ""
    if frozen_header_path.exists():
        frozen_header = frozen_header_path.read_text(encoding="utf-8").strip()
        print(f"Loaded Frozen Header ({len(frozen_header)} chars)")
    else:
        print(f"Warning: Frozen Header not found at {frozen_header_path}")

    print(f"Syncing {len(agent_files)} agents from .claude/agents/ to agents/")

    synced = 0
    for src_file in agent_files:
        agent_name = src_file.stem
        content = src_file.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(content)

        if not fm.get("name"):
            print(f"  SKIP {agent_name} (no frontmatter)")
            continue

        skill_content = generate_skill_md(fm, body, agent_name, frozen_header)
        dst_dir = agents_dst / agent_name
        dst_file = dst_dir / "SKILL.md"

        if dry_run:
            print(f"  WOULD write: {dst_file}")
        else:
            dst_dir.mkdir(parents=True, exist_ok=True)
            dst_file.write_text(skill_content, encoding="utf-8")
            print(f"  WROTE: {dst_file}")

        synced += 1

    print(f"\n{'Would sync' if dry_run else 'Synced'} {synced} agents")


if __name__ == "__main__":
    main()
