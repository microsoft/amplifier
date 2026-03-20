#!/usr/bin/env python3
"""Review history reporter — aggregates JSONL review data for /retro and dashboard.

Reads ${CLAUDE_PLUGIN_DATA}/reviews/history.jsonl and outputs formatted stats.

Usage:
    python scripts/review-report.py                  # last 7 days
    python scripts/review-report.py --days 1         # last 24 hours
    python scripts/review-report.py --days 30        # last 30 days
    python scripts/review-report.py --json            # machine-readable output
    python scripts/review-report.py --engine codex   # filter by engine
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path


def get_plugin_data():
    return Path(os.environ.get(
        "CLAUDE_PLUGIN_DATA",
        Path.home() / ".claude" / "plugin-data" / "amplifier-core"
    ))


def load_jsonl(path, days=7):
    """Load JSONL entries from the last N days."""
    if not path.exists():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    entries = []
    for line in path.read_text(encoding="utf-8").strip().splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
            ts = entry.get("timestamp", "")
            if ts:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if dt >= cutoff:
                    entries.append(entry)
            else:
                entries.append(entry)  # no timestamp = include
        except (json.JSONDecodeError, ValueError):
            continue
    return entries


def report_reviews(entries, engine_filter=None):
    """Generate review stats from history entries."""
    if engine_filter:
        entries = [e for e in entries if e.get("engine") == engine_filter]

    if not entries:
        return {"total": 0, "pass": 0, "fail": 0, "pass_rate": 0,
                "by_engine": {}, "findings": {"p1": 0, "p2": 0, "p3": 0}}

    total = len(entries)
    passes = sum(1 for e in entries if e.get("verdict", "").upper() == "PASS")
    fails = total - passes
    pass_rate = round(passes / total * 100) if total else 0

    by_engine = Counter(e.get("engine", "unknown") for e in entries)

    p1 = sum(e.get("findings", {}).get("p1", 0) for e in entries)
    p2 = sum(e.get("findings", {}).get("p2", 0) for e in entries)
    p3 = sum(e.get("findings", {}).get("p3", 0) for e in entries)

    return {
        "total": total, "pass": passes, "fail": fails,
        "pass_rate": pass_rate, "by_engine": dict(by_engine),
        "findings": {"p1": p1, "p2": p2, "p3": p3},
    }


def report_failures(entries):
    """Generate failure stats."""
    if not entries:
        return {"total": 0, "by_type": {}}
    by_type = Counter(e.get("error_type", "unknown") for e in entries)
    return {"total": len(entries), "by_type": dict(by_type)}


def format_text(reviews, failures, days):
    """Format as CLI text output."""
    lines = [
        f"AMPLIFIER METRICS (last {days} day{'s' if days != 1 else ''})",
        "=" * 50,
    ]

    r = reviews
    if r["total"] > 0:
        engine_str = " | ".join(f"{k}: {v}" for k, v in sorted(r["by_engine"].items()))
        lines.extend([
            f"Reviews:    {r['total']} total | {r['pass']} PASS | {r['fail']} FAIL ({r['pass_rate']}% pass rate)",
            f"  By engine: {engine_str}",
            f"  Findings:  {r['findings']['p1']} P1 | {r['findings']['p2']} P2 | {r['findings']['p3']} P3",
        ])
    else:
        lines.append("Reviews:    no reviews in this period")

    f = failures
    if f["total"] > 0:
        type_str = " | ".join(f"{v} {k}" for k, v in sorted(f["by_type"].items()))
        lines.append(f"Failures:   {type_str}")
    else:
        lines.append("Failures:   none")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Amplifier review history report")
    parser.add_argument("--days", type=int, default=7, help="Time window in days")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--engine", help="Filter by engine (sonnet/codex/gemini)")
    args = parser.parse_args()

    plugin_data = get_plugin_data()

    review_entries = load_jsonl(plugin_data / "reviews" / "history.jsonl", args.days)
    failure_entries = load_jsonl(plugin_data / "failures.jsonl", args.days)

    reviews = report_reviews(review_entries, args.engine)
    failures = report_failures(failure_entries)

    if args.json:
        print(json.dumps({"reviews": reviews, "failures": failures, "days": args.days}, indent=2))
    else:
        print(format_text(reviews, failures, args.days))


if __name__ == "__main__":
    main()
