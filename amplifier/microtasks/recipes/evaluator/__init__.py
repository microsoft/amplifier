"""Philosophy evaluator for generated tools - ensures alignment with principles and user ask."""

import re
from pathlib import Path
from typing import Any


def evaluate_alignment(output: str, ask: str, philosophy_path: Path | None = None) -> dict[str, Any]:
    """Check if generated output matches user ask and philosophy principles.

    Args:
        output: Generated tool code
        ask: Original user request
        philosophy_path: Path to TOOL_GENERATION_PHILOSOPHY.md

    Returns:
        Dict with 'passed' bool, 'issues' list, and 'feedback' str
    """
    issues = []

    # Check critical requirements
    critical_issues = check_critical_requirements(output)
    issues.extend(critical_issues)

    # Check ask alignment (basic semantic check)
    ask_lower = ask.lower()
    output_lower = output.lower()

    # Check if key concepts from ask appear in output
    ask_keywords = extract_keywords(ask_lower)
    missing_concepts = []
    for keyword in ask_keywords:
        if keyword not in output_lower and not any(syn in output_lower for syn in get_synonyms(keyword)):
            missing_concepts.append(keyword)

    if missing_concepts:
        issues.append(f"Missing concepts from ask: {', '.join(missing_concepts)}")

    # Generate feedback
    feedback = generate_feedback(issues)

    return {"passed": len(issues) == 0, "issues": issues, "feedback": feedback}


def check_critical_requirements(code: str) -> list[str]:
    """Verify critical requirements from philosophy.

    Args:
        code: Generated Python code

    Returns:
        List of critical issues found
    """
    issues = []

    # 1. Check for 120-second timeout (NON-NEGOTIABLE)
    timeout_pattern = r"asyncio\.timeout\((\d+)\)"
    timeouts = re.findall(timeout_pattern, code)

    for timeout in timeouts:
        if int(timeout) < 120:
            issues.append(f"CRITICAL: SDK timeout {timeout}s < 120s minimum. Must use asyncio.timeout(120)")

    if "ClaudeSDKClient" in code and not timeouts:
        issues.append("CRITICAL: Claude SDK usage without timeout. Must use asyncio.timeout(120)")

    # 2. Check for incremental saves
    has_loop = bool(re.search(r"for .+ in .+:", code))
    has_save_in_loop = bool(re.search(r"for .+ in .+:.*?(?:write_json|write_text|dump|save)", code, re.DOTALL))

    if has_loop and not has_save_in_loop:
        # Look more carefully for saves within loop
        loop_blocks = re.findall(r"for .+ in .+:.*?(?=\nfor|\ndef|\nclass|\Z)", code, re.DOTALL)
        has_save = False
        for block in loop_blocks:
            if any(save_word in block for save_word in ["write", "save", "dump", "flush"]):
                has_save = True
                break

        if not has_save:
            issues.append("CRITICAL: Processing loop without incremental saves. Must save after each item")

    # 3. Check for resume capability
    has_exists_check = bool(re.search(r"(?:exists\(\)|in existing|in results|in processed)", code))
    has_skip = bool(re.search(r"(?:continue|skip|return)", code))

    if has_loop and not (has_exists_check and has_skip):
        issues.append("CRITICAL: No resume capability. Must check existing results and skip processed items")

    # 4. Check for file I/O patterns
    uses_utils = bool(re.search(r"(?:write_json|read_json|write_file|read_file)", code))

    # Allow Path operations but prefer utils for JSON
    json_without_utils = bool(re.search(r"json\.(?:dump|load)\s*\(", code)) and not uses_utils

    if json_without_utils:
        issues.append("WARNING: Direct JSON operations without retry utilities. Prefer write_json/read_json")

    # 5. Check for progress indicators
    has_print = bool(re.search(r"print\s*\(", code))
    has_progress = bool(re.search(r"(?:\d+/\d+|\[.*?\]|Processing|Completed|✓|✔|▶)", code))

    if has_loop and not (has_print and has_progress):
        issues.append("WARNING: No progress indicators. Users need visibility into long-running operations")

    return issues


def extract_keywords(text: str) -> list[str]:
    """Extract key concept words from text.

    Args:
        text: Input text

    Returns:
        List of important keywords
    """
    # Remove common words
    stop_words = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "as",
        "is",
        "was",
        "are",
        "were",
        "been",
        "be",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "can",
        "each",
        "every",
        "that",
        "this",
        "these",
        "those",
        "it",
        "its",
        "them",
        "they",
    }

    # Extract words
    words = re.findall(r"\b[a-z]+\b", text)

    # Filter keywords
    keywords = []
    for word in words:
        if len(word) > 3 and word not in stop_words and word not in keywords:
            keywords.append(word)

    return keywords[:10]  # Top 10 keywords


def get_synonyms(keyword: str) -> list[str]:
    """Get common synonyms for a keyword.

    Args:
        keyword: Word to find synonyms for

    Returns:
        List of synonyms
    """
    synonyms = {
        "process": ["processing", "handle", "analyze", "transform"],
        "file": ["document", "path", "item", "content"],
        "files": ["documents", "paths", "items", "contents"],
        "summarize": ["summary", "synthesize", "condense", "extract"],
        "idea": ["concept", "insight", "thought", "notion"],
        "ideas": ["concepts", "insights", "thoughts", "notions"],
        "combine": ["merge", "synthesize", "aggregate", "join"],
        "extract": ["pull", "get", "retrieve", "parse"],
        "analyze": ["analysis", "examine", "process", "evaluate"],
    }

    return synonyms.get(keyword, [])


def generate_feedback(issues: list[str]) -> str:
    """Generate specific corrective feedback for issues.

    Args:
        issues: List of identified issues

    Returns:
        Formatted feedback string
    """
    if not issues:
        return "✅ All checks passed! Tool aligns with philosophy and requirements."

    feedback = "## Issues Found\n\n"
    feedback += "The generated tool has the following issues that must be fixed:\n\n"

    critical_issues = [i for i in issues if i.startswith("CRITICAL:")]
    warning_issues = [i for i in issues if i.startswith("WARNING:")]
    other_issues = [i for i in issues if not i.startswith(("CRITICAL:", "WARNING:"))]

    if critical_issues:
        feedback += "### 🔴 Critical Issues (MUST FIX)\n"
        for issue in critical_issues:
            feedback += f"- {issue}\n"
        feedback += "\n"

    if warning_issues:
        feedback += "### 🟡 Warnings (SHOULD FIX)\n"
        for issue in warning_issues:
            feedback += f"- {issue}\n"
        feedback += "\n"

    if other_issues:
        feedback += "### ℹ️ Other Issues\n"
        for issue in other_issues:
            feedback += f"- {issue}\n"
        feedback += "\n"

    feedback += "## Required Fixes\n\n"

    # Add specific fix instructions
    for issue in issues:
        if "timeout" in issue.lower():
            feedback += "- Replace ALL Claude SDK calls with: `async with asyncio.timeout(120):`\n"
        elif "incremental saves" in issue.lower():
            feedback += "- Add save operation immediately after processing each item in the loop\n"
        elif "resume capability" in issue.lower():
            feedback += "- Check if item already processed before processing: `if item_id in existing: continue`\n"
        elif "retry utilities" in issue.lower():
            feedback += "- Use `write_json()` and `read_json()` from amplifier.utils.file_io\n"
        elif "progress indicators" in issue.lower():
            feedback += "- Add print statements showing: `[current/total] Processing item_name...`\n"

    return feedback
