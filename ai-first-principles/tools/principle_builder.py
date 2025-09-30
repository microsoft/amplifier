#!/usr/bin/env python3
"""
AI-First Principles Builder Tool

A CLI tool for creating, validating, and managing AI-first principle specifications.
Demonstrates Principle #28 (CLI-First Design) and #29 (Tool Ecosystems as Extensions).

Usage:
    python principle_builder.py create <number> <name> [--category CATEGORY]
    python principle_builder.py validate <number>
    python principle_builder.py list [--category CATEGORY] [--status STATUS]
    python principle_builder.py update-progress
    python principle_builder.py check-quality <number>
"""

import argparse
import sys
from pathlib import Path

# Principle categories and their ranges
CATEGORIES = {
    "people": (1, 6),
    "process": (7, 19),
    "technology": (20, 37),
    "governance": (38, 44),
}


def get_project_root() -> Path:
    """Get the ai-first-principles directory root."""
    return Path(__file__).parent.parent


def get_category_from_number(number: int) -> str | None:
    """Determine category from principle number."""
    for category, (start, end) in CATEGORIES.items():
        if start <= number <= end:
            return category
    return None


def get_principle_path(number: int) -> Path | None:
    """Get the file path for a principle specification."""
    category = get_category_from_number(number)
    if not category:
        return None

    root = get_project_root()
    # Find the file - try to match by number prefix
    category_dir = root / "principles" / category
    if not category_dir.exists():
        return None

    for file in category_dir.glob(f"{number:02d}-*.md"):
        return file

    return None


def validate_principle(number: int) -> dict[str, any]:
    """Validate a principle specification against quality standards."""
    path = get_principle_path(number)
    if not path or not path.exists():
        return {"valid": False, "errors": [f"Principle #{number} not found"], "warnings": []}

    content = path.read_text()
    errors = []
    warnings = []

    # Check required sections
    required_sections = [
        "## Plain-Language Definition",
        "## Why This Matters for AI-First Development",
        "## Implementation Approaches",
        "## Good Examples vs Bad Examples",
        "## Related Principles",
        "## Common Pitfalls",
        "## Tools & Frameworks",
        "## Implementation Checklist",
        "## Metadata",
    ]

    for section in required_sections:
        if section not in content:
            errors.append(f"Missing required section: {section}")

    # Check for minimum content in key sections
    if "### Example 1:" not in content:
        warnings.append("May be missing example pairs")

    if "- [x]" not in content and "- [ ]" not in content:
        warnings.append("May be missing checklist items")

    # Check metadata completeness
    if "**Category**:" not in content:
        errors.append("Missing Category in metadata")

    if "**Status**: Complete" not in content:
        warnings.append("Specification may not be marked as complete")

    # Count examples (should be 5 pairs)
    example_count = content.count("### Example")
    if example_count < 5:
        warnings.append(f"Only {example_count} examples found, should have 5")

    # Count related principles (should be 6)
    related_count = content.count("- **[Principle #")
    if related_count < 6:
        warnings.append(f"Only {related_count} related principles found, should have 6")

    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings, "path": str(path)}


def list_principles(category: str | None = None, status: str | None = None) -> list[dict]:
    """List all principle specifications with their status."""
    root = get_project_root()
    principles = []

    categories_to_check = [category] if category else CATEGORIES.keys()

    for cat in categories_to_check:
        category_dir = root / "principles" / cat
        if not category_dir.exists():
            continue

        for file in sorted(category_dir.glob("*.md")):
            # Extract number from filename
            number = int(file.stem.split("-")[0])
            name = file.stem[3:]  # Remove "NN-" prefix

            # Check if complete
            content = file.read_text()
            is_complete = "**Status**: Complete" in content

            if status == "complete" and not is_complete:
                continue
            if status == "incomplete" and is_complete:
                continue

            principles.append(
                {
                    "number": number,
                    "name": name,
                    "category": cat,
                    "status": "complete" if is_complete else "incomplete",
                    "path": str(file),
                }
            )

    return principles


def update_progress() -> dict[str, any]:
    """Update PROGRESS.md with current completion status."""
    root = get_project_root()
    progress_file = root / "PROGRESS.md"

    # Count completed principles by category
    stats = {cat: {"complete": 0, "total": end - start + 1} for cat, (start, end) in CATEGORIES.items()}

    for cat in CATEGORIES:
        category_dir = root / "principles" / cat
        if not category_dir.exists():
            continue

        for file in category_dir.glob("*.md"):
            content = file.read_text()
            if "**Status**: Complete" in content:
                stats[cat]["complete"] += 1

    total_complete = sum(s["complete"] for s in stats.values())
    total_specs = sum(s["total"] for s in stats.values())

    return {
        "total_complete": total_complete,
        "total_specs": total_specs,
        "percentage": (total_complete / total_specs * 100) if total_specs > 0 else 0,
        "by_category": stats,
    }


def check_quality(number: int) -> dict[str, any]:
    """Perform comprehensive quality check on a principle."""
    validation = validate_principle(number)
    if not validation["valid"]:
        return validation

    path = get_principle_path(number)
    content = path.read_text()

    quality_checks = {
        "structure": validation["valid"],
        "examples": content.count("### Example") >= 5,
        "code_blocks": content.count("```") >= 10,  # At least 10 code blocks (5 good/bad pairs)
        "related_principles": content.count("- **[Principle #") >= 6,
        "checklist_items": content.count("- [ ]") >= 8,
        "common_pitfalls": content.count("**Pitfall") >= 5 or content.count(". **") >= 5,
        "tools_section": "## Tools & Frameworks" in content,
        "metadata_complete": all(
            field in content for field in ["**Category**:", "**Principle Number**:", "**Status**:"]
        ),
    }

    score = sum(quality_checks.values()) / len(quality_checks) * 100

    return {
        "valid": validation["valid"],
        "quality_score": score,
        "checks": quality_checks,
        "errors": validation["errors"],
        "warnings": validation["warnings"],
    }


def create_principle_stub(number: int, name: str, category: str | None = None) -> Path:
    """Create a new principle stub from the template."""
    if not category:
        category = get_category_from_number(number)

    if not category:
        raise ValueError(f"Invalid principle number: {number}")

    root = get_project_root()
    template_path = root / "TEMPLATE.md"

    if not template_path.exists():
        raise FileNotFoundError("TEMPLATE.md not found")

    # Read template
    template = template_path.read_text()

    # Replace placeholders
    stub = template.replace("{number}", str(number))
    stub = stub.replace("{Full Name}", name.replace("-", " ").title())
    stub = stub.replace("{People | Process | Technology | Governance}", category.title())
    stub = stub.replace("{1-44}", str(number))
    stub = stub.replace("{Draft | Review | Complete}", "Draft")
    stub = stub.replace("{YYYY-MM-DD}", "2025-09-30")
    stub = stub.replace("{1.0, 1.1, etc.}", "1.0")

    # Create file
    filename = f"{number:02d}-{name}.md"
    output_path = root / "principles" / category / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(stub)

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="AI-First Principles Builder Tool", formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new principle stub")
    create_parser.add_argument("number", type=int, help="Principle number (1-44)")
    create_parser.add_argument("name", help="Principle name (kebab-case)")
    create_parser.add_argument("--category", choices=CATEGORIES.keys(), help="Force category")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a principle")
    validate_parser.add_argument("number", type=int, help="Principle number")

    # List command
    list_parser = subparsers.add_parser("list", help="List principles")
    list_parser.add_argument("--category", choices=CATEGORIES.keys(), help="Filter by category")
    list_parser.add_argument("--status", choices=["complete", "incomplete"], help="Filter by status")

    # Update progress command
    subparsers.add_parser("update-progress", help="Update PROGRESS.md")

    # Check quality command
    quality_parser = subparsers.add_parser("check-quality", help="Check principle quality")
    quality_parser.add_argument("number", type=int, help="Principle number")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "create":
            path = create_principle_stub(args.number, args.name, args.category)
            print(f"✅ Created principle stub: {path}")
            print("📝 Edit the file and fill in all sections following TEMPLATE.md")

        elif args.command == "validate":
            result = validate_principle(args.number)
            if result["valid"]:
                print(f"✅ Principle #{args.number} is valid")
                if result["warnings"]:
                    print("\n⚠️  Warnings:")
                    for warning in result["warnings"]:
                        print(f"  - {warning}")
            else:
                print(f"❌ Principle #{args.number} has errors:")
                for error in result["errors"]:
                    print(f"  - {error}")
                sys.exit(1)

        elif args.command == "list":
            principles = list_principles(args.category, args.status)
            print(f"\n📋 Found {len(principles)} principles:\n")
            for p in principles:
                status_icon = "✅" if p["status"] == "complete" else "⏳"
                print(f"{status_icon} #{p['number']:02d} - {p['name']} ({p['category']})")

        elif args.command == "update-progress":
            stats = update_progress()
            print("\n📊 Progress Update:")
            print(
                f"✅ {stats['total_complete']}/{stats['total_specs']} specifications complete ({stats['percentage']:.1f}%)"
            )
            print("\nBy category:")
            for cat, data in stats["by_category"].items():
                print(f"  {cat.title()}: {data['complete']}/{data['total']}")

        elif args.command == "check-quality":
            result = check_quality(args.number)
            print(f"\n🎯 Quality Check for Principle #{args.number}:")
            print(f"Score: {result['quality_score']:.1f}%")
            print("\nChecks:")
            for check, passed in result["checks"].items():
                icon = "✅" if passed else "❌"
                print(f"  {icon} {check.replace('_', ' ').title()}")

            if result["warnings"]:
                print("\n⚠️  Warnings:")
                for warning in result["warnings"]:
                    print(f"  - {warning}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
