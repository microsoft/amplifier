#!/usr/bin/env python3
"""
AI-First Principles Builder Tool (Improved Version)

A CLI tool for creating, validating, and managing AI-first principle specifications.
Demonstrates Principle #28 (CLI-First Design) and #29 (Tool Ecosystems as Extensions).

This version includes:
- Security fixes for path traversal
- Proper error handling and recovery
- Idempotent operations
- Input validation
- Better type hints
"""

import argparse
import json
import logging
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Principle categories and their ranges
CATEGORIES = {
    "people": (1, 6),
    "process": (7, 19),
    "technology": (20, 37),
    "governance": (38, 44),
}

# Constants
MIN_PRINCIPLE = 1
MAX_PRINCIPLE = 44


def get_project_root() -> Path:
    """Get the ai-first-principles directory root."""
    return Path(__file__).parent.parent


def validate_principle_number(number: int) -> int:
    """Validate principle number is within valid range.

    Args:
        number: Principle number to validate

    Returns:
        The validated number

    Raises:
        ValueError: If number is outside valid range
    """
    if not MIN_PRINCIPLE <= number <= MAX_PRINCIPLE:
        raise ValueError(f"Principle number must be between {MIN_PRINCIPLE} and {MAX_PRINCIPLE}, got: {number}")
    return number


def validate_principle_name(name: str) -> str:
    """Validate and sanitize principle name to prevent security issues.

    Args:
        name: Principle name to validate

    Returns:
        The sanitized name in lowercase

    Raises:
        ValueError: If name contains invalid characters
    """
    # Only allow alphanumeric, hyphens, and underscores
    if not re.match(r"^[a-z0-9-_]+$", name, re.IGNORECASE):
        raise ValueError(f"Invalid principle name: {name}. Use only alphanumeric characters, hyphens, and underscores.")

    # Prevent path traversal
    if ".." in name or "/" in name or "\\" in name:
        raise ValueError(f"Invalid principle name: {name}. Path separators not allowed.")

    # Limit length to prevent filesystem issues
    if len(name) > 100:
        raise ValueError(f"Principle name too long (max 100 characters): {name}")

    return name.lower()


def safe_read_file(path: Path) -> str:
    """Safely read file with proper error handling.

    Args:
        path: Path to file to read

    Returns:
        File contents as string

    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If lacking read permissions
        ValueError: If file is not valid UTF-8
    """
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {path}")
    except PermissionError:
        raise PermissionError(f"Permission denied reading: {path}")
    except UnicodeDecodeError:
        raise ValueError(f"File is not valid UTF-8: {path}")


def safe_write_file(path: Path, content: str, force: bool = False) -> None:
    """Atomically write file with proper error handling.

    Args:
        path: Path to write to
        content: Content to write
        force: Whether to overwrite existing files

    Raises:
        FileExistsError: If file exists and force=False
        PermissionError: If lacking write permissions
    """
    # Check if file exists (idempotency)
    if path.exists() and not force:
        raise FileExistsError(f"File already exists: {path}. Use --force to overwrite.")

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write atomically using temp file
    temp_path = path.with_suffix(".tmp")
    try:
        temp_path.write_text(content, encoding="utf-8")
        temp_path.replace(path)  # Atomic on POSIX systems
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def get_category_from_number(number: int) -> str | None:
    """Determine category from principle number.

    Args:
        number: Principle number

    Returns:
        Category name or None if invalid number
    """
    for category, (start, end) in CATEGORIES.items():
        if start <= number <= end:
            return category
    return None


def get_principle_path(number: int) -> Path | None:
    """Get the file path for a principle specification.

    Args:
        number: Principle number

    Returns:
        Path to principle file or None if not found
    """
    category = get_category_from_number(number)
    if not category:
        return None

    root = get_project_root()
    category_dir = root / "principles" / category
    if not category_dir.exists():
        return None

    # Find the file - try to match by number prefix
    for file in category_dir.glob(f"{number:02d}-*.md"):
        return file

    return None


def validate_principle(number: int) -> dict[str, Any]:
    """Validate a principle specification against quality standards.

    Args:
        number: Principle number to validate

    Returns:
        Dictionary with validation results
    """
    try:
        number = validate_principle_number(number)
    except ValueError as e:
        return {"valid": False, "errors": [str(e)], "warnings": []}

    path = get_principle_path(number)
    if not path or not path.exists():
        return {"valid": False, "errors": [f"Principle #{number} not found"], "warnings": []}

    try:
        content = safe_read_file(path)
    except Exception as e:
        return {"valid": False, "errors": [f"Error reading file: {e}"], "warnings": []}

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
    """List all principle specifications with their status.

    Args:
        category: Optional category filter
        status: Optional status filter ('complete' or 'incomplete')

    Returns:
        List of principle dictionaries
    """
    root = get_project_root()
    principles = []

    categories_to_check = [category] if category else CATEGORIES.keys()

    for cat in categories_to_check:
        category_dir = root / "principles" / cat
        if not category_dir.exists():
            continue

        for file in sorted(category_dir.glob("*.md")):
            try:
                # Extract number from filename
                number = int(file.stem.split("-")[0])
                name = file.stem[3:]  # Remove "NN-" prefix

                # Check if complete
                content = safe_read_file(file)
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
            except (ValueError, FileNotFoundError) as e:
                logger.warning(f"Skipping file {file}: {e}")

    return principles


def update_progress() -> dict[str, Any]:
    """Calculate current completion statistics.

    Returns:
        Dictionary with progress statistics
    """
    root = get_project_root()

    # Count completed principles by category
    stats = {cat: {"complete": 0, "total": end - start + 1} for cat, (start, end) in CATEGORIES.items()}

    for cat in CATEGORIES:
        category_dir = root / "principles" / cat
        if not category_dir.exists():
            continue

        for file in category_dir.glob("*.md"):
            try:
                content = safe_read_file(file)
                if "**Status**: Complete" in content:
                    stats[cat]["complete"] += 1
            except Exception as e:
                logger.warning(f"Error reading {file}: {e}")

    total_complete = sum(s["complete"] for s in stats.values())
    total_specs = sum(s["total"] for s in stats.values())

    return {
        "total_complete": total_complete,
        "total_specs": total_specs,
        "percentage": (total_complete / total_specs * 100) if total_specs > 0 else 0,
        "by_category": stats,
    }


def check_quality(number: int) -> dict[str, Any]:
    """Perform comprehensive quality check on a principle.

    Args:
        number: Principle number to check

    Returns:
        Dictionary with quality check results
    """
    validation = validate_principle(number)
    if not validation["valid"]:
        return validation

    path = get_principle_path(number)
    try:
        content = safe_read_file(path)
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Error reading file: {e}"],
            "warnings": [],
            "quality_score": 0,
        }

    quality_checks = {
        "structure": validation["valid"],
        "examples": content.count("### Example") >= 5,
        "code_blocks": content.count("```") >= 10,
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


def create_principle_stub(
    number: int, name: str, category: str | None = None, force: bool = False, dry_run: bool = False
) -> Path:
    """Create a new principle stub from the template.

    Args:
        number: Principle number
        name: Principle name (will be sanitized)
        category: Optional category override
        force: Whether to overwrite existing files
        dry_run: Whether to simulate without creating files

    Returns:
        Path to created/would-be-created file

    Raises:
        ValueError: If inputs are invalid
        FileNotFoundError: If template is missing
        FileExistsError: If file exists and force=False
    """
    # Validate inputs
    number = validate_principle_number(number)
    name = validate_principle_name(name)

    if not category:
        category = get_category_from_number(number)

    if not category:
        raise ValueError(f"Invalid principle number: {number}")

    root = get_project_root()
    template_path = root / "TEMPLATE.md"

    if not template_path.exists():
        raise FileNotFoundError("TEMPLATE.md not found")

    # Read template
    template = safe_read_file(template_path)

    # Replace placeholders
    stub = template.replace("{number}", str(number))
    stub = stub.replace("{Full Name}", name.replace("-", " ").title())
    stub = stub.replace("{People | Process | Technology | Governance}", category.title())
    stub = stub.replace("{1-44}", str(number))
    stub = stub.replace("{Draft | Review | Complete}", "Draft")
    stub = stub.replace("{YYYY-MM-DD}", date.today().isoformat())
    stub = stub.replace("{1.0, 1.1, etc.}", "1.0")

    # Create file
    filename = f"{number:02d}-{name}.md"
    output_path = root / "principles" / category / filename

    if dry_run:
        logger.info(f"[DRY RUN] Would create: {output_path}")
        return output_path

    safe_write_file(output_path, stub, force=force)
    return output_path


def validate_all_principles() -> dict[int, dict]:
    """Validate all principles and return summary.

    Returns:
        Dictionary mapping principle numbers to validation results
    """
    results = {}
    for number in range(MIN_PRINCIPLE, MAX_PRINCIPLE + 1):
        results[number] = validate_principle(number)
    return results


def export_to_json(output_path: Path) -> None:
    """Export all principles to JSON format.

    Args:
        output_path: Path to write JSON output
    """
    principles = list_principles()
    safe_write_file(output_path, json.dumps(principles, indent=2), force=True)


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
    create_parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    create_parser.add_argument("--dry-run", action="store_true", help="Simulate without creating files")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a principle")
    validate_parser.add_argument("number", type=int, help="Principle number")

    # Validate all command
    subparsers.add_parser("validate-all", help="Validate all principles")

    # List command
    list_parser = subparsers.add_parser("list", help="List principles")
    list_parser.add_argument("--category", choices=CATEGORIES.keys(), help="Filter by category")
    list_parser.add_argument("--status", choices=["complete", "incomplete"], help="Filter by status")

    # Update progress command
    subparsers.add_parser("update-progress", help="Calculate progress statistics")

    # Check quality command
    quality_parser = subparsers.add_parser("check-quality", help="Check principle quality")
    quality_parser.add_argument("number", type=int, help="Principle number")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export principles to JSON")
    export_parser.add_argument("output", type=Path, help="Output file path")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "create":
            path = create_principle_stub(args.number, args.name, args.category, force=args.force, dry_run=args.dry_run)
            if not args.dry_run:
                logger.info(f"✅ Created principle stub: {path}")
                logger.info("📝 Edit the file and fill in all sections following TEMPLATE.md")

        elif args.command == "validate":
            result = validate_principle(args.number)
            if result["valid"]:
                logger.info(f"✅ Principle #{args.number} is valid")
                if result["warnings"]:
                    logger.info("\n⚠️  Warnings:")
                    for warning in result["warnings"]:
                        logger.info(f"  - {warning}")
            else:
                logger.error(f"❌ Principle #{args.number} has errors:")
                for error in result["errors"]:
                    logger.error(f"  - {error}")
                sys.exit(1)

        elif args.command == "validate-all":
            results = validate_all_principles()
            valid_count = sum(1 for r in results.values() if r["valid"])
            total = len(results)

            logger.info(f"\n📋 Validation Results: {valid_count}/{total} valid")

            # Show invalid principles
            invalid = [num for num, r in results.items() if not r["valid"]]
            if invalid:
                logger.info("\n❌ Invalid principles:")
                for num in invalid:
                    logger.info(f"  - Principle #{num}")
                    for error in results[num]["errors"]:
                        logger.info(f"    • {error}")

        elif args.command == "list":
            principles = list_principles(args.category, args.status)
            logger.info(f"\n📋 Found {len(principles)} principles:\n")
            for p in principles:
                status_icon = "✅" if p["status"] == "complete" else "⏳"
                logger.info(f"{status_icon} #{p['number']:02d} - {p['name']} ({p['category']})")

        elif args.command == "update-progress":
            stats = update_progress()
            logger.info("\n📊 Progress Update:")
            logger.info(
                f"✅ {stats['total_complete']}/{stats['total_specs']} "
                f"specifications complete ({stats['percentage']:.1f}%)"
            )
            logger.info("\nBy category:")
            for cat, data in stats["by_category"].items():
                logger.info(f"  {cat.title()}: {data['complete']}/{data['total']}")

        elif args.command == "check-quality":
            result = check_quality(args.number)
            logger.info(f"\n🎯 Quality Check for Principle #{args.number}:")
            logger.info(f"Score: {result['quality_score']:.1f}%")
            logger.info("\nChecks:")
            for check, passed in result["checks"].items():
                icon = "✅" if passed else "❌"
                logger.info(f"  {icon} {check.replace('_', ' ').title()}")

            if result["warnings"]:
                logger.info("\n⚠️  Warnings:")
                for warning in result["warnings"]:
                    logger.info(f"  - {warning}")

        elif args.command == "export":
            export_to_json(args.output)
            logger.info(f"✅ Exported principles to: {args.output}")

    except FileNotFoundError as e:
        logger.error(f"❌ File not found: {e}")
        sys.exit(1)
    except PermissionError as e:
        logger.error(f"❌ Permission denied: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"❌ Invalid input: {e}")
        sys.exit(1)
    except FileExistsError as e:
        logger.error(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e.__class__.__name__}: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
