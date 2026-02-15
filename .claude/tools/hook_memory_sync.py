#!/usr/bin/env python3
"""SessionStart hook: Sync git-notes memory from origin."""

import json
import subprocess
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hook_logger import HookLogger
from platform_detect import SUPERPOWERS_FALLBACK

logger = HookLogger("memory_sync")

SUPERPOWERS_DIR = os.path.expanduser(
    "~/.claude/plugins/cache/superpowers-marketplace/superpowers"
)
if not os.path.isdir(os.path.join(SUPERPOWERS_DIR, ".git")):
    SUPERPOWERS_DIR = SUPERPOWERS_FALLBACK

NOTES_REF = "refs/notes/superpowers"


def run(cmd, cwd=None):
    """Run a command and return stdout."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=cwd, timeout=15
        )
        return result.stdout.strip()
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ) as e:
        logger.warning(f"Command failed: {' '.join(cmd)}: {e}")
        return ""


def main():
    """Fetch git notes and output memory summary."""
    try:
        logger.info("Memory sync hook started")

        raw_input = sys.stdin.read()
        logger.info(f"Received input length: {len(raw_input)}")

        if not os.path.isdir(SUPERPOWERS_DIR):
            logger.warning(f"Superpowers directory not found: {SUPERPOWERS_DIR}")
            json.dump({}, sys.stdout)
            return

        git_dir = os.path.join(SUPERPOWERS_DIR, ".git")
        if not os.path.isdir(git_dir):
            logger.warning(f"Not a git repo: {SUPERPOWERS_DIR}")
            json.dump({}, sys.stdout)
            return

        logger.info("Fetching git notes from origin...")
        fetch_result = run(
            ["git", "fetch", "origin", f"{NOTES_REF}:{NOTES_REF}"], cwd=SUPERPOWERS_DIR
        )
        logger.info(f"Fetch result: {fetch_result or '(empty - may be up to date)'}")

        state_json = run(
            ["git", "notes", "--ref", NOTES_REF, "show"], cwd=SUPERPOWERS_DIR
        )

        if not state_json:
            logger.info("No git notes found (fresh state)")
            json.dump({}, sys.stdout)
            return

        try:
            state = json.loads(state_json)
        except json.JSONDecodeError:
            logger.warning("Git notes exist but contain invalid JSON")
            json.dump({}, sys.stdout)
            return

        kb = state.get("knowledge_base", {})
        decisions = kb.get("decisions", [])
        patterns = kb.get("patterns", [])
        glossary = kb.get("glossary", {})

        parts = []
        if decisions:
            parts.append(f"{len(decisions)} decisions")
        if patterns:
            parts.append(f"{len(patterns)} patterns")
        if glossary:
            parts.append(f"{len(glossary)} glossary terms")

        last_agent = state.get("metadata", {}).get("last_agent", "unknown")

        if parts:
            summary = f"Git memory synced: {', '.join(parts)} (last: {last_agent})"
        else:
            summary = f"Git memory synced: empty state (last: {last_agent})"

        logger.info(summary)

        context_parts = ["## Cross-Platform Memory (git-notes)\n"]
        context_parts.append(f"Last updated by: {last_agent}")

        if decisions:
            context_parts.append(f"\n### Decisions ({len(decisions)})")
            for d in decisions[-3:]:
                title = d.get("title", "untitled")
                status = d.get("status", "unknown")
                context_parts.append(f"- [{status}] {title}")

        if patterns:
            context_parts.append(f"\n### Patterns ({len(patterns)})")
            for p in patterns[-3:]:
                name = p.get("name", p) if isinstance(p, dict) else str(p)
                context_parts.append(f"- {name}")

        if glossary:
            context_parts.append(f"\n### Glossary ({len(glossary)} terms)")
            for term in list(glossary.keys())[:5]:
                context_parts.append(f"- **{term}**: {glossary[term]}")

        context = "\n".join(context_parts)

        output = {}
        if context:
            output = {
                "additionalContext": context,
                "metadata": {
                    "memorySynced": True,
                    "decisions": len(decisions),
                    "patterns": len(patterns),
                    "glossaryTerms": len(glossary),
                    "lastAgent": last_agent,
                },
            }

        json.dump(output, sys.stdout)
        logger.info("Memory sync hook completed")

    except Exception as e:
        logger.exception("Error in memory sync hook", e)
        json.dump({}, sys.stdout)


if __name__ == "__main__":
    main()
