"""
Plan Cache — store, lookup, update, evict, and report on cached plans.

Usage:
    python plan-cache.py store  --plan <path> --prompt "<text>"
    python plan-cache.py lookup --prompt "<text>"
    python plan-cache.py update --hash <sha256> --outcome pass|partial|fail
    python plan-cache.py evict
    python plan-cache.py stats

Environment:
    CLAUDE_PLUGIN_DATA  Base directory for plugin data.  Defaults to
                        ~/.claude/plugin-data/amplifier-core

Index file:
    ${CLAUDE_PLUGIN_DATA}/plan-cache/index.json

Each entry in the index:
    hash            SHA-256 of first 500 chars of prompt + sorted file list
    prompt_keywords Sorted list of lowercase word tokens from the prompt
    plan_path       Path to the plan markdown file
    created         ISO-8601 UTC timestamp
    success_rate    Float 0.0–1.0 (updated via "update" command)
    times_reused    Number of times this plan was returned by "lookup"
    task_count      Number of tasks in the plan (0 if unknown)
    outcomes        List of raw outcome strings for audit ("pass"/"partial"/"fail")
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
EVICT_DAYS = 30
EVICT_MIN_RATE = 0.6
SIMILARITY_THRESHOLD = 0.70

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _data_dir() -> Path:
    base = os.environ.get("CLAUDE_PLUGIN_DATA")
    if base:
        root = Path(base)
    else:
        root = Path.home() / ".claude" / "plugin-data" / "amplifier-core"
    return root / "plan-cache"


def _index_path() -> Path:
    return _data_dir() / "index.json"


def _load_index() -> dict:
    idx = _index_path()
    if idx.exists():
        try:
            return json.loads(idx.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"plans": []}


def _save_index(index: dict) -> None:
    idx = _index_path()
    idx.parent.mkdir(parents=True, exist_ok=True)
    idx.write_text(json.dumps(index, indent=2), encoding="utf-8")


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _compute_hash(prompt: str, file_list: list[str] | None = None) -> str:
    snippet = prompt[:500]
    sorted_files = sorted(file_list or [])
    raw = snippet + "|" + ",".join(sorted_files)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    stopwords = {
        "the", "a", "an", "and", "or", "in", "on", "at", "to", "for",
        "of", "with", "is", "it", "this", "that", "be", "as", "by",
        "are", "was", "were", "will", "we", "i", "you", "he", "she",
    }
    return sorted(set(w for w in words if w not in stopwords and len(w) > 1))


def _jaccard(a: list[str], b: list[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_store(args: argparse.Namespace) -> int:
    prompt = args.prompt
    plan_path = args.plan
    file_list = args.files or []

    h = _compute_hash(prompt, file_list)
    keywords = _tokenize(prompt)

    # Count tasks by looking for markdown task lines if file exists
    task_count = 0
    p = Path(plan_path)
    if p.exists():
        text = p.read_text(encoding="utf-8", errors="replace")
        task_count = len(re.findall(r"^\s*[-*]\s+\*\*Task", text, re.MULTILINE))

    index = _load_index()

    # Overwrite existing entry with same hash
    index["plans"] = [e for e in index["plans"] if e.get("hash") != h]

    entry = {
        "hash": h,
        "prompt_keywords": keywords,
        "plan_path": str(plan_path),
        "created": _now_iso(),
        "success_rate": 1.0,
        "times_reused": 0,
        "task_count": task_count,
        "outcomes": [],
    }
    index["plans"].append(entry)
    _save_index(index)

    print(json.dumps({"status": "stored", "hash": h, "task_count": task_count}))
    return 0


def cmd_lookup(args: argparse.Namespace) -> int:
    prompt = args.prompt
    file_list = args.files or []

    h = _compute_hash(prompt, file_list)
    keywords = _tokenize(prompt)

    index = _load_index()
    plans = index.get("plans", [])

    # Exact match first
    for entry in plans:
        if entry.get("hash") == h:
            entry["times_reused"] = entry.get("times_reused", 0) + 1
            _save_index(index)
            print(json.dumps({"match": "exact", "entry": entry}))
            return 0

    # Similarity match
    best_score = 0.0
    best_entry = None
    for entry in plans:
        score = _jaccard(keywords, entry.get("prompt_keywords", []))
        if score > best_score:
            best_score = score
            best_entry = entry

    if best_entry and best_score >= SIMILARITY_THRESHOLD:
        best_entry["times_reused"] = best_entry.get("times_reused", 0) + 1
        _save_index(index)
        print(json.dumps({"match": "similar", "score": round(best_score, 3), "entry": best_entry}))
        return 0

    print(json.dumps({"match": "none", "score": round(best_score, 3) if best_entry else 0.0}))
    return 1


def cmd_update(args: argparse.Namespace) -> int:
    h = args.hash
    outcome = args.outcome  # pass | partial | fail

    if outcome not in ("pass", "partial", "fail"):
        print(f"Error: outcome must be pass, partial, or fail (got {outcome!r})", file=sys.stderr)
        return 2

    index = _load_index()
    for entry in index.get("plans", []):
        if entry.get("hash") == h:
            outcomes = entry.setdefault("outcomes", [])
            outcomes.append(outcome)
            # Recompute rate: pass=1.0, partial=0.5, fail=0.0
            weights = {"pass": 1.0, "partial": 0.5, "fail": 0.0}
            total = sum(weights[o] for o in outcomes)
            entry["success_rate"] = round(total / len(outcomes), 4)
            _save_index(index)
            print(json.dumps({"status": "updated", "hash": h, "success_rate": entry["success_rate"]}))
            return 0

    print(json.dumps({"status": "not_found", "hash": h}))
    return 1


def cmd_evict(args: argparse.Namespace) -> int:
    index = _load_index()
    plans = index.get("plans", [])
    now = datetime.now(timezone.utc)
    kept = []
    evicted = []

    for entry in plans:
        try:
            created = datetime.fromisoformat(entry["created"].replace("Z", "+00:00"))
        except (KeyError, ValueError):
            evicted.append(entry.get("hash", "?"))
            continue

        age_days = (now - created).days
        rate = entry.get("success_rate", 1.0)

        if age_days > EVICT_DAYS or rate < EVICT_MIN_RATE:
            evicted.append(entry.get("hash", "?"))
        else:
            kept.append(entry)

    index["plans"] = kept
    _save_index(index)
    print(json.dumps({"evicted": len(evicted), "kept": len(kept), "hashes_evicted": evicted}))
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    index = _load_index()
    plans = index.get("plans", [])

    if not plans:
        print(json.dumps({"total": 0}))
        return 0

    rates = [e.get("success_rate", 1.0) for e in plans]
    reuses = [e.get("times_reused", 0) for e in plans]
    tasks = [e.get("task_count", 0) for e in plans]

    stats = {
        "total": len(plans),
        "avg_success_rate": round(sum(rates) / len(rates), 4),
        "total_reuses": sum(reuses),
        "avg_task_count": round(sum(tasks) / len(tasks), 1),
        "oldest": min((e.get("created", "") for e in plans), default=""),
        "newest": max((e.get("created", "") for e in plans), default=""),
        "index_path": str(_index_path()),
    }
    print(json.dumps(stats, indent=2))
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="plan-cache",
        description="Cache and reuse plans across Claude sessions.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # store
    p_store = sub.add_parser("store", help="Store a plan in the cache")
    p_store.add_argument("--plan", required=True, help="Path to the plan file")
    p_store.add_argument("--prompt", required=True, help="The spec/prompt used to generate the plan")
    p_store.add_argument("--files", nargs="*", help="Optional list of relevant file paths")

    # lookup
    p_lookup = sub.add_parser("lookup", help="Look up a cached plan by prompt similarity")
    p_lookup.add_argument("--prompt", required=True, help="The spec/prompt to match against")
    p_lookup.add_argument("--files", nargs="*", help="Optional list of relevant file paths")

    # update
    p_update = sub.add_parser("update", help="Record outcome for a cached plan")
    p_update.add_argument("--hash", required=True, help="SHA-256 hash of the plan entry")
    p_update.add_argument("--outcome", required=True, choices=["pass", "partial", "fail"])

    # evict
    sub.add_parser("evict", help="Remove stale or low-quality plans from the cache")

    # stats
    sub.add_parser("stats", help="Print cache statistics")

    args = parser.parse_args()
    dispatch = {
        "store": cmd_store,
        "lookup": cmd_lookup,
        "update": cmd_update,
        "evict": cmd_evict,
        "stats": cmd_stats,
    }
    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
