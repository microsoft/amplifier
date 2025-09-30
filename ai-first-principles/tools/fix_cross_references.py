#!/usr/bin/env python3
"""
Fix incorrect cross-reference titles in principle specifications.

This script scans all principle files and validates that cross-reference
titles match the actual principle titles.
"""

import re
from pathlib import Path

# The correct principle titles based on actual files
CORRECT_TITLES = {
    1: "Small AI-First Working Groups",
    2: "Strategic Human Touchpoints Only",
    3: "Prompt Engineering as Core Skill",
    4: "Test-Based Verification Over Code Review",
    5: "Conversation-Driven Development",
    6: "Human Escape Hatches Always Available",
    7: "Regenerate, Don't Edit",
    8: "Contract-First Everything",
    9: "Tests as the Quality Gate",
    10: "Git as Safety Net",
    11: "Continuous Validation with Fast Feedback",
    12: "Incremental Processing as Default",
    13: "Parallel Exploration by Default",
    14: "Context Management as Discipline",
    15: "Git-Based Everything",
    16: "Docs Define, Not Describe",
    17: "Prompt Versioning and Testing",
    18: "Contract Evolution with Migration Paths",
    19: "Cost and Token Budgeting",
    20: "Self-Modifying AI-First Codebase",
    21: "Limited and Domain-Specific by Design",
    22: "Separation of Concerns Through Layered Virtualization",
    23: "Protected Self-Healing Kernel",
    24: "Long-Running Agent Processes",
    25: "Simple Interfaces by Design",
    26: "Stateless by Default",
    27: "Disposable Components Everywhere",
    28: "CLI-First Design",
    29: "Tool Ecosystems as Extensions",
    30: "Observability Baked In",
    31: "Idempotency by Design",
    32: "Error Recovery Patterns Built In",
    33: "Graceful Degradation by Design",
    34: "Feature Flags as Deployment Strategy",
    35: "Least-Privilege Automation with Scoped Permissions",
    36: "Dependency Pinning and Security Scanning",
    37: "Declarative Over Imperative",
    38: "Access Control and Compliance as First-Class",
    39: "Metrics and Evaluation Everywhere",
    40: "Knowledge Stewardship and Institutional Memory",
    41: "Adaptive Sandboxing with Explicit Approvals",
    42: "Data Governance and Privacy Controls",
    43: "Model Lifecycle Management",
    44: "Self-Serve Recovery with Known-Good Snapshots",
}


def get_principle_files():
    """Get all principle markdown files."""
    root = Path(__file__).parent.parent / "principles"
    return list(root.glob("**/*.md"))


def extract_cross_references(content):
    """Extract all principle cross-references from content."""
    # Pattern to match: - **[Principle #N - Title](path)**
    pattern = r"\*\*\[Principle #(\d+) - ([^\]]+)\]\(([^\)]+)\)\*\*"
    matches = re.findall(pattern, content)
    return [(int(num), title, path) for num, title, path in matches]


def check_and_fix_file(filepath, fix=False):
    """Check and optionally fix cross-references in a file."""
    content = filepath.read_text(encoding="utf-8")
    references = extract_cross_references(content)

    if not references:
        return 0, 0

    issues = []
    fixed_content = content

    for num, found_title, path in references:
        if num in CORRECT_TITLES:
            correct_title = CORRECT_TITLES[num]
            if found_title != correct_title:
                issues.append({"number": num, "found": found_title, "correct": correct_title, "path": path})

                if fix:
                    # Replace the incorrect title with correct one
                    old_ref = f"**[Principle #{num} - {found_title}]({path})**"
                    new_ref = f"**[Principle #{num} - {correct_title}]({path})**"
                    fixed_content = fixed_content.replace(old_ref, new_ref)

    if issues:
        print(f"\n{filepath.name}:")
        for issue in issues:
            print(f"  ❌ #{issue['number']}: '{issue['found']}' → '{issue['correct']}'")

        if fix and fixed_content != content:
            filepath.write_text(fixed_content, encoding="utf-8")
            print(f"  ✅ Fixed {len(issues)} incorrect references")

    return len(issues), len(issues) if fix else 0


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="Fix incorrect cross-reference titles")
    parser.add_argument("--fix", action="store_true", help="Fix issues (otherwise dry-run)")
    args = parser.parse_args()

    files = get_principle_files()
    total_issues = 0
    total_fixed = 0

    print("Scanning for incorrect cross-reference titles...")
    if not args.fix:
        print("(Dry run - use --fix to apply corrections)\n")

    for filepath in sorted(files):
        issues, fixed = check_and_fix_file(filepath, args.fix)
        total_issues += issues
        total_fixed += fixed

    print(f"\n{'=' * 60}")
    print(f"Total issues found: {total_issues}")
    if args.fix:
        print(f"Total issues fixed: {total_fixed}")
    else:
        print("Run with --fix flag to correct these issues")


if __name__ == "__main__":
    main()
