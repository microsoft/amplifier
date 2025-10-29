#!/usr/bin/env python3
"""
Agent conversion script for converting Claude Code agents to Codex format.

This script parses Claude Code agent definitions, transforms them for Codex
compatibility, and generates converted agents in .codex/agents/.
"""

import argparse
import logging
import re
import sys
from pathlib import Path

import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
CLAUDE_AGENTS_DIR = Path(".claude/agents")
CODEX_AGENTS_DIR = Path(".codex/agents")
CLAUDE_TOOLS = ["Task", "TodoWrite", "WebFetch", "WebSearch", "SlashCommand"]


def preprocess_frontmatter(frontmatter_text: str) -> str:
    """Preprocess frontmatter to fix unquoted description fields with colons."""

    def process_description(value: str) -> str:
        stripped = value.strip()
        if stripped.startswith(("|", ">", '"', "'")):
            return value
        # Wrap in YAML literal block scalar
        lines = stripped.split("\n")
        indented = "\n".join("  " + line for line in lines)
        return f"|\n{indented}"

    try:
        # Match description: followed by value until next key or end
        pattern = r"(description:\s*)(.*?)(?=\n\w+:|\n---|\Z)"
        processed = re.sub(
            pattern, lambda m: m.group(1) + process_description(m.group(2)), frontmatter_text, flags=re.DOTALL
        )
        return processed
    except Exception as e:
        logger.warning(f"Regex preprocessing failed: {e}, returning original")
        return frontmatter_text


def parse_agent_file(file_path: Path) -> tuple[dict, str]:
    """Parse agent markdown file into frontmatter and content."""
    try:
        content = file_path.read_text()
        if not content.startswith("---"):
            raise ValueError("Agent file must start with YAML frontmatter")
        parts = content.split("---", 2)
        if len(parts) < 3:
            raise ValueError("Invalid agent file format")
        frontmatter_text = parts[1]
        try:
            processed_frontmatter = preprocess_frontmatter(frontmatter_text)
        except Exception as e:
            logger.warning(f"Preprocessing failed for {file_path}: {e}, using original")
            processed_frontmatter = frontmatter_text
        frontmatter = yaml.safe_load(processed_frontmatter)
        markdown_content = parts[2].strip()
        return frontmatter, markdown_content
    except Exception as e:
        logger.error(f"Error parsing agent file {file_path}: {e}")
        raise


def convert_frontmatter(claude_frontmatter: dict) -> dict:
    """Convert Claude frontmatter to Codex format."""
    codex_frontmatter = {}

    # Keep fields
    if "name" in claude_frontmatter:
        codex_frontmatter["name"] = claude_frontmatter["name"]
    if "description" in claude_frontmatter:
        desc = claude_frontmatter["description"]
        # Simplify description
        desc = re.sub(r"Use PROACTIVELY", "", desc, flags=re.IGNORECASE)
        desc = re.sub(r"Task tool", "", desc, flags=re.IGNORECASE)
        desc = re.sub(r"slash commands?", "", desc, flags=re.IGNORECASE)
        codex_frontmatter["description"] = desc.strip()
    if "model" in claude_frontmatter:
        codex_frontmatter["model"] = claude_frontmatter["model"]

    # Convert tools
    if "tools" in claude_frontmatter:
        tools_str = claude_frontmatter["tools"]
        if isinstance(tools_str, str):
            tools_list = [t.strip() for t in tools_str.split(",") if t.strip()]
        else:
            tools_list = tools_str if isinstance(tools_str, list) else []
        # Remove Claude-specific tools
        tools_list = [t for t in tools_list if t not in CLAUDE_TOOLS]
        if not tools_list:
            tools_list = ["Read", "Grep", "Glob"]
        codex_frontmatter["tools"] = tools_list

    return codex_frontmatter


def remove_additional_instructions(content: str) -> str:
    """Remove Additional Instructions section."""
    pattern = r"# Additional Instructions.*$"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if match:
        content = content[: match.start()].strip()
    return content


def adapt_tool_references(content: str) -> str:
    """Adapt tool references for Codex."""
    content = re.sub(r"use the Task tool", "delegate to a specialized agent", content, flags=re.IGNORECASE)
    content = re.sub(r"use TodoWrite", "track progress", content, flags=re.IGNORECASE)
    content = re.sub(r"WebFetch|WebSearch", "research", content, flags=re.IGNORECASE)
    content = re.sub(r"spawn sub-agent via Task tool", "invoke specialized agent", content, flags=re.IGNORECASE)
    return content


def adapt_agent_spawning_examples(content: str) -> str:
    """Adapt agent spawning examples."""
    content = re.sub(r"I'll use the Task tool to spawn the (\w+) agent", r"I'll delegate to the \1 agent", content)
    content = re.sub(r"Task\((\w+),\s*([^)]+)\)", r"delegate to \1 agent for \2", content)
    return content


def remove_claude_specific_sections(content: str) -> str:
    """Remove Claude-specific sections."""
    content = re.sub(r"# Hooks.*?(?=# |\Z)", "", content, flags=re.MULTILINE | re.DOTALL)
    content = re.sub(r"/[^\s]+", "", content)
    content = re.sub(r"VS Code", "", content, flags=re.IGNORECASE)
    content = re.sub(r"Claude Code SDK", "", content, flags=re.IGNORECASE)
    return content


def preserve_core_methodology(content: str) -> str:
    """Ensure core methodology is preserved."""
    return content


def convert_agent(input_path: Path, output_path: Path, dry_run: bool = False) -> dict:
    """Convert a single agent."""
    frontmatter, content = parse_agent_file(input_path)
    new_frontmatter = convert_frontmatter(frontmatter)
    content = remove_additional_instructions(content)
    content = adapt_tool_references(content)
    content = adapt_agent_spawning_examples(content)
    content = remove_claude_specific_sections(content)
    content = preserve_core_methodology(content)

    yaml_str = yaml.dump(new_frontmatter, default_flow_style=False)
    full_content = f"---\n{yaml_str}---\n{content}"

    if not dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(full_content)

    changes = []
    return {"success": True, "input": str(input_path), "output": str(output_path), "changes": changes}


def convert_all_agents(dry_run: bool = False, verbose: bool = False) -> dict:
    """Convert all agents."""
    if not CLAUDE_AGENTS_DIR.exists():
        return {"total": 0, "succeeded": 0, "failed": 0, "agents": []}

    agents = []
    total = 0
    succeeded = 0
    failed = 0

    for file_path in CLAUDE_AGENTS_DIR.glob("*.md"):
        total += 1
        output_path = CODEX_AGENTS_DIR / file_path.name
        try:
            result = convert_agent(file_path, output_path, dry_run)
            agents.append(result)
            succeeded += 1
            if verbose:
                logger.info(f"Converted {file_path.name}")
        except Exception as e:
            failed += 1
            agents.append({"success": False, "input": str(file_path), "error": str(e)})
            if verbose:
                logger.error(f"Failed to convert {file_path.name}: {e}")

    return {"total": total, "succeeded": succeeded, "failed": failed, "agents": agents}


def validate_converted_agent(agent_path: Path) -> dict:
    """Validate a converted agent."""
    try:
        frontmatter, content = parse_agent_file(agent_path)
        errors = []
        warnings = []

        if "name" not in frontmatter:
            errors.append("Missing 'name' field")
        if "description" not in frontmatter:
            errors.append("Missing 'description' field")
        if "tools" in frontmatter:
            tools = frontmatter["tools"]
            if not isinstance(tools, list):
                errors.append("'tools' field must be an array")

        for tool in CLAUDE_TOOLS:
            if tool in content:
                errors.append(f"Claude-specific tool '{tool}' still present")

        if "Additional Instructions" in content:
            errors.append("'Additional Instructions' section still present")

        size = agent_path.stat().st_size
        if size == 0:
            errors.append("File is empty")
        elif size > 1000000:
            warnings.append("File is very large")

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}
    except Exception as e:
        return {"valid": False, "errors": [str(e)], "warnings": []}


def validate_all_converted_agents() -> dict:
    """Validate all converted agents."""
    if not CODEX_AGENTS_DIR.exists():
        return {"total": 0, "valid": 0, "invalid": 0, "agents": []}

    agents = []
    total = 0
    valid = 0
    invalid = 0

    for file_path in CODEX_AGENTS_DIR.glob("*.md"):
        total += 1
        result = validate_converted_agent(file_path)
        agents.append({"path": str(file_path), **result})
        if result["valid"]:
            valid += 1
        else:
            invalid += 1

    return {"total": total, "valid": valid, "invalid": invalid, "agents": agents}


def generate_conversion_report(results: dict, output_file: Path):
    """Generate conversion report."""
    content = "# Conversion Report\n\n"
    content += f"Total agents: {results['total']}\n"
    content += f"Succeeded: {results['succeeded']}\n"
    content += f"Failed: {results['failed']}\n\n"

    for agent in results["agents"]:
        content += f"## {agent['input']}\n"
        content += f"Success: {agent['success']}\n"
        if "changes" in agent:
            content += f"Changes: {agent['changes']}\n"
        content += "\n"

    output_file.write_text(content)


def test_conversion(agent_name: str):
    """Test conversion for a single agent."""
    input_path = CLAUDE_AGENTS_DIR / f"{agent_name}.md"
    output_path = CODEX_AGENTS_DIR / f"{agent_name}.md"
    result = convert_agent(input_path, output_path, dry_run=True)
    validation = validate_converted_agent(output_path) if output_path.exists() else {"valid": False}
    print(f"Test conversion for {agent_name}: {result}")
    print(f"Validation: {validation}")
    print("Diff not implemented")


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Convert Claude Code agents to Codex format")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing files")
    parser.add_argument("--agent", help="Convert single agent by name")
    parser.add_argument("--validate", action="store_true", help="Validate converted agents")
    parser.add_argument("--verbose", action="store_true", help="Enable detailed logging")
    parser.add_argument("--output-dir", type=Path, default=CODEX_AGENTS_DIR, help="Custom output directory")
    parser.add_argument("--force", action="store_true", help="Overwrite existing converted agents")

    subparsers = parser.add_subparsers(dest="subcommand")
    subparsers.add_parser("convert", help="Convert agents")
    subparsers.add_parser("validate", help="Validate converted agents")
    subparsers.add_parser("list", help="List available agents")
    subparsers.add_parser("diff", help="Show differences between Claude and Codex versions")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.subcommand == "validate" or args.validate:
        results = validate_all_converted_agents()
        print(f"Validation results: {results['valid']}/{results['total']} valid")
        for agent in results["agents"]:
            if not agent["valid"]:
                print(f"Invalid: {agent['path']} - {agent['errors']}")
    elif args.subcommand == "list":
        if CLAUDE_AGENTS_DIR.exists():
            print("Claude agents:")
            for f in CLAUDE_AGENTS_DIR.glob("*.md"):
                print(f"  {f.stem}")
        if CODEX_AGENTS_DIR.exists():
            print("Codex agents:")
            for f in CODEX_AGENTS_DIR.glob("*.md"):
                print(f"  {f.stem}")
    elif args.subcommand == "diff":
        print("Diff functionality not implemented yet")
    else:
        if args.agent:
            input_path = CLAUDE_AGENTS_DIR / f"{args.agent}.md"
            output_path = args.output_dir / f"{args.agent}.md"
            if not input_path.exists():
                print(f"Agent {args.agent} not found")
                sys.exit(1)
            result = convert_agent(input_path, output_path, args.dry_run)
            print(f"Converted {args.agent}: {result}")
        else:
            results = convert_all_agents(args.dry_run, args.verbose)
            print(f"Conversion summary: {results['succeeded']}/{results['total']} succeeded")


if __name__ == "__main__":
    main()
