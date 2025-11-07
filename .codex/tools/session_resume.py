#!/usr/bin/env python3
"""
Codex session resume script - resumes a previous session by loading its context.
Standalone script that loads context from previous sessions and sets up the environment.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add amplifier to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from amplifier.memory.core import MemoryStore
    from amplifier.search.core import MemorySearcher
except ImportError as e:
    print(f"Failed to import amplifier modules: {e}", file=sys.stderr)
    # Exit gracefully to not break wrapper
    sys.exit(0)


class SessionLogger:
    """Simple logger for session resume script"""

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


logger = SessionLogger("session_resume")


def parse_args():
    parser = argparse.ArgumentParser(description="Resume a previous Codex session")
    parser.add_argument("--session-id", help="Specific session ID to resume")
    parser.add_argument("--list", action="store_true", help="List available sessions to resume")
    parser.add_argument("--output", default=".codex/session_context.md", help="Output file for context")
    parser.add_argument("--limit", type=int, default=10, help="Number of memories to retrieve")
    parser.add_argument("--verbose", action="store_true", help="Enable detailed logging")
    return parser.parse_args()


def find_available_sessions():
    """Find all available sessions that can be resumed"""
    sessions = []

    # Check agent contexts directory
    agent_contexts_dir = Path(".codex/agent_contexts")
    if agent_contexts_dir.exists():
        for context_file in agent_contexts_dir.glob("*.md"):
            try:
                # Parse session info from filename
                # Format: agent_name_timestamp.md
                parts = context_file.stem.split("_")
                if len(parts) >= 2:
                    agent_name = parts[0]
                    timestamp_str = "_".join(parts[1:])
                    # Try to parse timestamp
                    try:
                        # Handle different timestamp formats
                        if len(timestamp_str) == 15:  # YYYYMMDD_HHMMSS
                            year = int(timestamp_str[0:4])
                            month = int(timestamp_str[4:6])
                            day = int(timestamp_str[6:8])
                            hour = int(timestamp_str[9:11])
                            minute = int(timestamp_str[11:13])
                            second = int(timestamp_str[13:15])
                            timestamp = datetime(year, month, day, hour, minute, second)  # noqa: DTZ001
                        else:
                            # Try ISO format or skip
                            continue

                        sessions.append(
                            {
                                "id": context_file.stem,
                                "agent": agent_name,
                                "timestamp": timestamp,
                                "file": context_file,
                                "type": "agent_context",
                            }
                        )
                    except (ValueError, IndexError):
                        continue
            except Exception as e:
                logger.warning(f"Failed to parse session file {context_file}: {e}")
                continue

    # Check agent results directory
    agent_results_dir = Path(".codex/agent_results")
    if agent_results_dir.exists():
        for result_file in agent_results_dir.glob("*.json"):
            try:
                with open(result_file) as f:
                    data = json.load(f)

                session_id = data.get("session_id", result_file.stem)
                timestamp_str = data.get("timestamp", "")
                agent_name = data.get("agent", "unknown")

                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    timestamp = datetime.now()  # fallback

                sessions.append(
                    {
                        "id": session_id,
                        "agent": agent_name,
                        "timestamp": timestamp,
                        "file": result_file,
                        "type": "agent_result",
                        "data": data,
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to parse result file {result_file}: {e}")
                continue

    # Sort by timestamp (newest first)
    sessions.sort(key=lambda s: s["timestamp"], reverse=True)

    return sessions


def load_session_context(session_id: str, sessions: list):
    """Load context from a specific session"""
    session = next((s for s in sessions if s["id"] == session_id), None)
    if not session:
        return None

    context_parts = []
    context_parts.append(
        f"## Resumed Session: {session['agent']} ({session['timestamp'].strftime('%Y-%m-%d %H:%M:%S')})\n"
    )

    try:
        if session["type"] == "agent_context":
            # Load markdown context
            with open(session["file"]) as f:
                content = f.read()
                context_parts.append("### Session Context\n")
                context_parts.append(content)

        elif session["type"] == "agent_result":
            # Load JSON result data
            data = session["data"]
            context_parts.append("### Session Results\n")

            if "task" in data:
                context_parts.append(f"**Task**: {data['task']}\n")

            if "result" in data:
                context_parts.append(f"**Result**: {data['result']}\n")

            if "metadata" in data:
                context_parts.append("**Metadata**:\n")
                for key, value in data["metadata"].items():
                    context_parts.append(f"- {key}: {value}")

    except Exception as e:
        logger.error(f"Failed to load session context: {e}")
        return None

    return "\n".join(context_parts)


def main():
    args = parse_args()
    logger.info("Starting session resume")
    logger.cleanup_old_logs()

    try:
        # Find available sessions
        sessions = find_available_sessions()
        logger.info(f"Found {len(sessions)} available sessions")

        if args.list:
            # List available sessions
            print("Available sessions to resume:")
            print("-" * 50)
            for session in sessions[:10]:  # Show last 10
                print(f"ID: {session['id']}")
                print(f"Agent: {session['agent']}")
                print(f"Time: {session['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Type: {session['type']}")
                print("-" * 30)
            return

        # Resume specific session
        if not args.session_id:
            if sessions:
                # Resume most recent session
                args.session_id = sessions[0]["id"]
                logger.info(f"No session specified, resuming most recent: {args.session_id}")
            else:
                print("No sessions available to resume")
                return

        # Load session context
        context_md = load_session_context(args.session_id, sessions)
        if not context_md:
            print(f"Failed to load context for session: {args.session_id}")
            return

        # Load additional memories if available
        memory_context = ""
        try:
            memory_enabled = os.getenv("MEMORY_SYSTEM_ENABLED", "true").lower() in ["true", "1", "yes"]
            if memory_enabled:
                store = MemoryStore()
                searcher = MemorySearcher()

                # Search for memories related to the session
                session_query = f"session {args.session_id} {sessions[0]['agent'] if sessions else 'work'}"
                search_results = searcher.search(session_query, store.get_all(), limit=args.limit)

                if search_results:
                    memory_context = "\n### Related Memories\n"
                    for result in search_results:
                        memory_context += f"- **{result.memory.category}**: {result.memory.content}\n"
        except Exception as e:
            logger.warning(f"Failed to load memory context: {e}")

        # Combine contexts
        full_context = context_md + memory_context

        # Write context file
        context_file = Path(args.output)
        context_file.parent.mkdir(exist_ok=True)
        context_file.write_text(full_context)

        # Write metadata to dedicated session resume metadata file
        # Note: Session metadata files are now separated by component:
        # - session_memory_init_metadata.json: Memory loading during session init
        # - session_memory_cleanup_metadata.json: Memory extraction during session cleanup
        # - session_resume_metadata.json: Session resume operations
        metadata = {
            "sessionResumed": args.session_id,
            "contextLoaded": True,
            "memoriesIncluded": bool(memory_context.strip()),
            "source": "session_resume",
            "contextFile": str(context_file),
            "timestamp": datetime.now().isoformat(),
        }

        metadata_file = Path(".codex/session_resume_metadata.json")
        metadata_file.parent.mkdir(exist_ok=True)
        metadata_file.write_text(json.dumps(metadata, indent=2))

        print(f"✓ Resumed session {args.session_id}")
        logger.info(f"Wrote resumed context to {context_file}")

    except Exception as e:
        logger.exception("Error during session resume", e)
        print("⚠ Session resume failed, but continuing...")
        # Create empty files so wrapper doesn't fail
        context_file = Path(args.output)
        context_file.parent.mkdir(exist_ok=True)
        context_file.write_text("")
        metadata_file = Path(".codex/session_resume_metadata.json")
        metadata_file.parent.mkdir(exist_ok=True)
        metadata = {
            "sessionResumed": args.session_id if args.session_id else None,
            "contextLoaded": False,
            "source": "error",
            "contextFile": str(context_file),
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }
        metadata_file.write_text(json.dumps(metadata, indent=2))
        sys.exit(0)


if __name__ == "__main__":
    main()
