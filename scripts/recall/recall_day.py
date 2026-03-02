"""Importable module — re-exports recall-day.py functions.

session-graph.py imports from recall_day (Python module name),
but the main script is recall-day.py (CLI name with dash).
This shim bridges the two naming conventions.
"""

# The functions are defined in recall-day.py which has a dash in the name.
# Python can't import dashes, so we duplicate the key functions here.
# To keep DRY, recall-day.py is the source of truth for CLI usage,
# and this file re-exports the shared functions.

import re
from datetime import date, timedelta
from pathlib import Path

CLAUDE_PROJECTS = Path.home() / ".claude" / "projects"

STRIP_PATTERNS = [
    re.compile(r"<system-reminder>.*?</system-reminder>", re.DOTALL),
    re.compile(r"<local-command-caveat>.*?</local-command-caveat>", re.DOTALL),
    re.compile(r"<local-command-stdout>.*?</local-command-stdout>", re.DOTALL),
    re.compile(
        r"<command-name>.*?</command-name>\s*<command-message>.*?</command-message>\s*(?:<command-args>.*?</command-args>)?",
        re.DOTALL,
    ),
    re.compile(r"<command-message>.*?</command-message>", re.DOTALL),
    re.compile(r"<command-name>.*?</command-name>", re.DOTALL),
    re.compile(r"<command-args>.*?</command-args>", re.DOTALL),
    re.compile(r"<task-notification>.*?</task-notification>", re.DOTALL),
    re.compile(r"<teammate-message[^>]*>.*?</teammate-message>", re.DOTALL),
]


def clean_content(text: str) -> str:
    """Strip system tags."""
    if not isinstance(text, str):
        return ""
    for pat in STRIP_PATTERNS:
        text = pat.sub("", text)
    return text.strip()


def extract_text(content) -> str:
    """Extract text from message content (string or list of content blocks)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    return ""


def parse_date_expr(expr: str) -> tuple[date, date]:
    """Parse a natural language date expression into (start_date, end_date) inclusive."""
    expr = expr.strip().lower()
    today = date.today()

    if expr == "today":
        return today, today
    if expr == "yesterday":
        d = today - timedelta(days=1)
        return d, d

    try:
        d = date.fromisoformat(expr)
        return d, d
    except ValueError:
        pass

    m = re.match(r"(\d+)\s+days?\s+ago", expr)
    if m:
        d = today - timedelta(days=int(m.group(1)))
        return d, d

    m = re.match(r"last\s+(\d+)\s+days?", expr)
    if m:
        start = today - timedelta(days=int(m.group(1)))
        return start, today

    if expr == "this week":
        start = today - timedelta(days=today.weekday())
        return start, today

    if expr == "last week":
        start = today - timedelta(days=today.weekday() + 7)
        end = start + timedelta(days=6)
        return start, end

    day_names = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6,
    }
    m = re.match(r"last\s+(\w+)", expr)
    if m and m.group(1) in day_names:
        target = day_names[m.group(1)]
        days_back = (today.weekday() - target) % 7
        if days_back == 0:
            days_back = 7
        d = today - timedelta(days=days_back)
        return d, d

    raise ValueError(f"Cannot parse date expression: '{expr}'")


def get_project_dirs(all_projects: bool) -> list[Path]:
    """Get project directories to scan."""
    if all_projects:
        return [d for d in CLAUDE_PROJECTS.iterdir() if d.is_dir()]
    amplifier = CLAUDE_PROJECTS / "C--claude-amplifier"
    if amplifier.exists():
        return [amplifier]
    return [d for d in CLAUDE_PROJECTS.iterdir() if d.is_dir()]
