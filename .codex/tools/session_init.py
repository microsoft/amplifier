#!/usr/bin/env python3
"""
Codex session initialization script - loads relevant memories before starting a session.
Standalone script that detects context and writes output to files.
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add amplifier to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from amplifier.memory import MemoryStore
    from amplifier.search import MemorySearcher
except ImportError as e:
    print(f"Failed to import amplifier modules: {e}", file=sys.stderr)
    # Exit gracefully to not break wrapper
    sys.exit(0)


class SessionLogger:
    """Simple logger for session init script"""

    def __init__(self, log_name: str):
        self.log_name = log_name
        self.log_dir = Path(__file__).parent.parent / "logs"
        self.log_dir.mkdir(exist_ok=True)
        today = datetime.now().strftime("%Y%m%d")
        self.log_file = self.log_dir / f"{log_name}_{today}.log"

    def _write(self, level: str, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted = f"[{timestamp}] [{self.log_name}] [{level}] {message}"
        print(formatted, file=sys.stderr)
        try:
            with open(self.log_file, "a") as f:
                f.write(formatted + "\n")
        except Exception as e:
            print(f"Failed to write to log file: {e}", file=sys.stderr)

    def info(self, message: str):
        self._write("INFO", message)

    def debug(self, message: str):
        self._write("DEBUG", message)

    def error(self, message: str):
        self._write("ERROR", message)

    def warning(self, message: str):
        self._write("WARN", message)

    def exception(self, message: str, exc=None):
        import traceback

        if exc:
            self.error(f"{message}: {exc}")
            self.error(f"Traceback:\n{traceback.format_exc()}")
        else:
            self.error(message)
            self.error(f"Traceback:\n{traceback.format_exc()}")

    def cleanup_old_logs(self, days_to_keep: int = 7):
        try:
            from datetime import date
            from datetime import timedelta

            today = datetime.now().date()
            cutoff = today - timedelta(days=days_to_keep)
            for log_file in self.log_dir.glob(f"{self.log_name}_*.log"):
                try:
                    date_str = log_file.stem.split("_")[-1]
                    year = int(date_str[0:4])
                    month = int(date_str[4:6])
                    day = int(date_str[6:8])
                    file_date = date(year, month, day)
                    if file_date < cutoff:
                        log_file.unlink()
                        self.info(f"Deleted old log file: {log_file.name}")
                except (ValueError, IndexError):
                    continue
        except Exception as e:
            self.warning(f"Failed to cleanup old logs: {e}")


logger = SessionLogger("session_init")


def parse_args():
    parser = argparse.ArgumentParser(description="Initialize Codex session with memory context")
    parser.add_argument("--prompt", help="Explicit context for memory search")
    parser.add_argument("--output", default=".codex/session_context.md", help="Output file for context")
    parser.add_argument("--limit", type=int, default=5, help="Number of memories to retrieve")
    parser.add_argument("--verbose", action="store_true", help="Enable detailed logging")
    return parser.parse_args()


async def main():
    args = parse_args()
    logger.info("Starting session initialization")
    logger.cleanup_old_logs()

    try:
        # Memory system check
        memory_enabled = os.getenv("MEMORY_SYSTEM_ENABLED", "true").lower() in ["true", "1", "yes"]
        if not memory_enabled:
            logger.info("Memory system disabled via MEMORY_SYSTEM_ENABLED env var")
            print("Memory system disabled, skipping initialization")
            # Create empty context file
            context_file = Path(args.output)
            context_file.parent.mkdir(exist_ok=True)
            context_file.write_text("")
            # Write metadata
            metadata_file = Path(".codex/session_init_metadata.json")
            metadata_file.parent.mkdir(exist_ok=True)
            metadata = {
                "memoriesLoaded": 0,
                "relevantCount": 0,
                "recentCount": 0,
                "source": "disabled",
                "contextFile": str(context_file),
                "timestamp": datetime.now().isoformat(),
            }
            metadata_file.write_text(json.dumps(metadata, indent=2))
            print("✓ Session initialized (memory system disabled)")
            return

        # Context detection
        context = None
        context_source = None

        if args.prompt:
            context = args.prompt
            context_source = "command_line"
            logger.info(f"Using context from command line: {context[:50]}...")
        else:
            # Check environment variable
            env_context = os.getenv("CODEX_SESSION_CONTEXT")
            if env_context:
                context = env_context
                context_source = "environment"
                logger.info(f"Using context from CODEX_SESSION_CONTEXT: {context[:50]}...")
            else:
                # Check file
                context_file_path = Path(".codex/session_context.txt")
                if context_file_path.exists():
                    context = context_file_path.read_text().strip()
                    if context:
                        context_source = "file"
                        logger.info(f"Using context from file: {context[:50]}...")
                    else:
                        logger.warning("Context file exists but is empty")
                else:
                    logger.info("No explicit context provided, using default")

        if not context:
            context = "Recent work on this project"
            context_source = "default"
            logger.info("Using default context: Recent work on this project")

        logger.info(f"Context source: {context_source}")

        # Memory retrieval
        logger.info("Initializing store and searcher")
        store = MemoryStore()
        searcher = MemorySearcher()

        logger.debug(f"Data directory: {store.data_dir}")
        logger.debug(f"Data file: {store.data_file}")
        logger.debug(f"Data file exists: {store.data_file.exists()}")

        all_memories = store.get_all()
        logger.info(f"Total memories in store: {len(all_memories)}")

        logger.info("Searching for relevant memories")
        search_results = searcher.search(context, all_memories, limit=args.limit)
        logger.info(f"Found {len(search_results)} relevant memories")

        recent = store.search_recent(limit=3)
        logger.info(f"Found {len(recent)} recent memories")

        # Context formatting
        context_parts = []
        if search_results or recent:
            context_parts.append("## Relevant Context from Memory System\n")

            if search_results:
                context_parts.append("### Relevant Memories")
                for result in search_results[:3]:
                    content = result.memory.content
                    category = result.memory.category
                    score = result.score
                    context_parts.append(f"- **{category}** (relevance: {score:.2f}): {content}")

            seen_ids = {r.memory.id for r in search_results}
            unique_recent = [m for m in recent if m.id not in seen_ids]
            if unique_recent:
                context_parts.append("\n### Recent Context")
                for mem in unique_recent[:2]:
                    context_parts.append(f"- {mem.category}: {mem.content}")

        context_md = "\n".join(context_parts) if context_parts else ""

        # Output generation
        context_file = Path(args.output)
        context_file.parent.mkdir(exist_ok=True)
        context_file.write_text(context_md)

        memories_loaded = len(search_results)
        if search_results:
            seen_ids = {r.memory.id for r in search_results}
            unique_recent_count = len([m for m in recent if m.id not in seen_ids])
            memories_loaded += unique_recent_count
        else:
            memories_loaded += len(recent)

        relevant_count = len(search_results)
        recent_count = memories_loaded - relevant_count

        metadata = {
            "memoriesLoaded": memories_loaded,
            "relevantCount": relevant_count,
            "recentCount": recent_count,
            "source": "amplifier_memory",
            "contextFile": str(context_file),
            "timestamp": datetime.now().isoformat(),
        }

        metadata_file = Path(".codex/session_init_metadata.json")
        metadata_file.parent.mkdir(exist_ok=True)
        metadata_file.write_text(json.dumps(metadata, indent=2))

        print(f"✓ Loaded {memories_loaded} memories from previous sessions")
        logger.info(f"Wrote context to {context_file} and metadata to {metadata_file}")

    except Exception as e:
        logger.exception("Error during session initialization", e)
        print("⚠ Session initialization failed, but continuing...")
        # Create empty files so wrapper doesn't fail
        context_file = Path(args.output)
        context_file.parent.mkdir(exist_ok=True)
        context_file.write_text("")
        metadata_file = Path(".codex/session_init_metadata.json")
        metadata_file.parent.mkdir(exist_ok=True)
        metadata = {
            "memoriesLoaded": 0,
            "relevantCount": 0,
            "recentCount": 0,
            "source": "error",
            "contextFile": str(context_file),
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }
        metadata_file.write_text(json.dumps(metadata, indent=2))
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
