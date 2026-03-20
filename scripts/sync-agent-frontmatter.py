#!/usr/bin/env python3
"""Sync agent and command frontmatter with routing-matrix.yaml.

Reads the routing matrix to derive effort, maxTurns, and disallowedTools
for each agent, and effort for each command. Updates YAML frontmatter
in-place, preserving all non-frontmatter content.

Usage:
    python scripts/sync-agent-frontmatter.py [--dry-run] [--agents-dir PATH] [--commands]
    python scripts/sync-agent-frontmatter.py --commands [--dry-run] [--commands-dir PATH]
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
ROUTING_MATRIX = REPO_ROOT / "config" / "routing-matrix.yaml"

DEFAULT_AGENTS_DIR = (
    Path.home()
    / ".claude"
    / "plugins"
    / "marketplaces"
    / "amplifier-marketplace"
    / "amplifier-core"
    / "agents"
)

DEFAULT_COMMANDS_DIR = (
    Path.home()
    / ".claude"
    / "plugins"
    / "marketplaces"
    / "amplifier-marketplace"
    / "amplifier-core"
    / "commands"
)

# Roles that should have disallowedTools (read-only agents)
READ_ONLY_ROLES = {"scout", "research"}
DISALLOWED_TOOLS = ["Edit", "Write", "Bash", "NotebookEdit"]

# Command effort assignments
COMMAND_EFFORT = {
    "high": [
        "brainstorm", "create-plan", "debug", "design-interface",
        "second-opinion", "frontend-design", "solve", "worktree",
    ],
    "low": [
        "guard", "platform", "prime", "recall", "docs", "commit",
        "retro", "techdebt", "transcripts",
    ],
    # Everything else defaults to "medium"
}


def load_routing_matrix():
    """Load routing-matrix.yaml and build role/agent mappings."""
    with open(ROUTING_MATRIX, encoding="utf-8") as f:
        matrix = yaml.safe_load(f)

    roles = matrix.get("roles", {})
    agents = matrix.get("agents", {})

    # Build role → frontmatter mapping
    role_map = {}
    for role_name, role_def in roles.items():
        turns = role_def.get("turns", {})
        role_map[role_name] = {
            "effort": role_def.get("effort", "medium"),
            "maxTurns": turns.get("default", 15),
            "disallowedTools": DISALLOWED_TOOLS if role_name in READ_ONLY_ROLES else None,
        }

    # Build agent-name → role mapping (strip "amplifier-core:" prefix)
    agent_roles = {}
    for agent_key, role_name in agents.items():
        name = agent_key.replace("amplifier-core:", "")
        agent_roles[name] = role_name

    return role_map, agent_roles


def parse_frontmatter(content):
    """Split content into frontmatter dict and body text."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
    if not match:
        return None, content
    fm_text = match.group(1)
    body = match.group(2)
    try:
        fm = yaml.safe_load(fm_text)
    except yaml.YAMLError:
        return None, content
    return fm or {}, body


def serialize_frontmatter(fm, body):
    """Rebuild file content from frontmatter dict and body."""
    # Custom serialization to keep it clean
    lines = ["---"]
    for key, value in fm.items():
        if key == "disallowedTools":
            if value:
                items = ", ".join(value)
                lines.append(f"disallowedTools: [{items}]")
        elif key == "description" and isinstance(value, str) and "\n" in value:
            lines.append(f"description: |")
            for desc_line in value.rstrip().split("\n"):
                lines.append(f"  {desc_line}")
        elif key == "tools" and isinstance(value, list):
            items = ", ".join(value)
            lines.append(f"tools: [{items}]")
        else:
            if isinstance(value, str) and any(c in value for c in ":#{}[]|>&"):
                lines.append(f'{key}: "{value}"')
            else:
                lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n" + body


def sync_agents(agents_dir, dry_run=False):
    """Update agent frontmatter with effort, maxTurns, disallowedTools."""
    role_map, agent_roles = load_routing_matrix()

    md_files = sorted(agents_dir.glob("*.md"))
    if not md_files:
        print(f"No .md files found in {agents_dir}")
        return False

    changed = 0
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(content)
        if fm is None:
            print(f"  SKIP {md_file.name}: no valid frontmatter")
            continue

        agent_name = fm.get("name", md_file.stem)
        role_name = agent_roles.get(agent_name, "implement")
        role_def = role_map.get(role_name, role_map.get("implement", {}))

        # Track what changed
        changes = []

        # Update effort
        old_effort = fm.get("effort")
        new_effort = role_def["effort"]
        if old_effort != new_effort:
            changes.append(f"effort={new_effort}")
        fm["effort"] = new_effort

        # Update maxTurns
        old_turns = fm.get("maxTurns")
        new_turns = role_def["maxTurns"]
        if old_turns != new_turns:
            changes.append(f"maxTurns={new_turns}")
        fm["maxTurns"] = new_turns

        # Update disallowedTools
        old_disallowed = fm.get("disallowedTools")
        new_disallowed = role_def["disallowedTools"]
        if new_disallowed:
            if old_disallowed != new_disallowed:
                changes.append("+disallowedTools")
            fm["disallowedTools"] = new_disallowed
        else:
            if old_disallowed:
                changes.append("-disallowedTools")
            fm.pop("disallowedTools", None)

        if changes:
            new_content = serialize_frontmatter(fm, body)
            if not dry_run:
                md_file.write_text(new_content, encoding="utf-8")
            changed += 1
            prefix = "[DRY RUN] " if dry_run else ""
            print(f"  {prefix}{agent_name} ({role_name}): {', '.join(changes)}")
        else:
            print(f"  {agent_name} ({role_name}): (no change)")

    print(f"\n{'Would update' if dry_run else 'Updated'} {changed}/{len(md_files)} agents")
    return changed > 0


def sync_commands(commands_dir, dry_run=False):
    """Update command frontmatter with effort field."""
    # Build command → effort map
    effort_map = {}
    for effort_level, commands in COMMAND_EFFORT.items():
        for cmd in commands:
            effort_map[cmd] = effort_level

    md_files = sorted(commands_dir.glob("*.md"))
    if not md_files:
        print(f"No .md files found in {commands_dir}")
        return False

    changed = 0
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(content)
        if fm is None:
            print(f"  SKIP {md_file.name}: no valid frontmatter")
            continue

        cmd_name = md_file.stem
        new_effort = effort_map.get(cmd_name, "medium")
        old_effort = fm.get("effort")

        if old_effort != new_effort:
            fm["effort"] = new_effort
            new_content = serialize_frontmatter(fm, body)
            if not dry_run:
                md_file.write_text(new_content, encoding="utf-8")
            changed += 1
            prefix = "[DRY RUN] " if dry_run else ""
            print(f"  {prefix}/{cmd_name}: effort={new_effort}")
        else:
            print(f"  /{cmd_name}: (no change)")

    print(f"\n{'Would update' if dry_run else 'Updated'} {changed}/{len(md_files)} commands")
    return changed > 0


def main():
    parser = argparse.ArgumentParser(description="Sync agent/command frontmatter with routing-matrix")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    parser.add_argument("--agents-dir", type=Path, default=DEFAULT_AGENTS_DIR)
    parser.add_argument("--commands-dir", type=Path, default=DEFAULT_COMMANDS_DIR)
    parser.add_argument("--commands", action="store_true", help="Also sync command effort frontmatter")
    parser.add_argument("--commands-only", action="store_true", help="Only sync commands, skip agents")
    args = parser.parse_args()

    if not ROUTING_MATRIX.exists():
        print(f"ERROR: routing-matrix.yaml not found at {ROUTING_MATRIX}")
        sys.exit(1)

    if not args.commands_only:
        print(f"=== Syncing Agent Frontmatter ===")
        print(f"Source: {ROUTING_MATRIX}")
        print(f"Target: {args.agents_dir}")
        print()
        if not args.agents_dir.exists():
            print(f"ERROR: agents directory not found: {args.agents_dir}")
            sys.exit(1)
        sync_agents(args.agents_dir, args.dry_run)

    if args.commands or args.commands_only:
        print(f"\n=== Syncing Command Effort ===")
        print(f"Target: {args.commands_dir}")
        print()
        if not args.commands_dir.exists():
            print(f"ERROR: commands directory not found: {args.commands_dir}")
            sys.exit(1)
        sync_commands(args.commands_dir, args.dry_run)


if __name__ == "__main__":
    main()
