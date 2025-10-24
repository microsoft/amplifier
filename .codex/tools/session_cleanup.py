#!/usr/bin/env python3
"""
Codex Session Cleanup - Standalone script for post-session memory extraction and transcript export.

This script replicates hook_stop.py functionality but as a standalone tool that detects
Codex sessions from the filesystem and processes them.
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Any
import argparse

# Add amplifier to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import transcript exporter
sys.path.append(str(Path(__file__).parent.parent.parent / "tools"))

try:
    from codex_transcripts_builder import SESSIONS_DEFAULT, HISTORY_DEFAULT
    from transcript_exporter import CodexTranscriptExporter
except ImportError as e:
    print(f"Error importing transcript exporter: {e}", file=sys.stderr)
    sys.exit(0)

try:
    from amplifier.extraction import MemoryExtractor
    from amplifier.memory import MemoryStore
except ImportError as e:
    print(f"Failed to import amplifier modules: {e}", file=sys.stderr)
    # Exit gracefully to not break wrapper
    sys.exit(0)


class SessionCleanupLogger:
    """Simple logger that writes to both file and stderr"""

    def __init__(self, script_name: str):
        """Initialize logger for a specific script"""
        self.script_name = script_name

        # Create logs directory
        self.log_dir = Path(__file__).parent / "logs"
        self.log_dir.mkdir(exist_ok=True)

        # Create log file with today's date
        today = datetime.now().strftime("%Y%m%d")
        self.log_file = self.log_dir / f"{script_name}_{today}.log"

        # Log initialization
        self.info(f"Logger initialized for {script_name}")

    def _format_message(self, level: str, message: str) -> str:
        """Format a log message with timestamp and level"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        return f"[{timestamp}] [{self.script_name}] [{level}] {message}"

    def _write(self, level: str, message: str):
        """Write to both file and stderr"""
        formatted = self._format_message(level, message)

        # Write to stderr (existing behavior)
        print(formatted, file=sys.stderr)

        # Write to file
        try:
            with open(self.log_file, "a") as f:
                f.write(formatted + "\n")
        except Exception as e:
            # If file writing fails, just log to stderr
            print(f"Failed to write to log file: {e}", file=sys.stderr)

    def info(self, message: str):
        """Log info level message"""
        self._write("INFO", message)

    def debug(self, message: str):
        """Log debug level message"""
        self._write("DEBUG", message)

    def error(self, message: str):
        """Log error level message"""
        self._write("ERROR", message)

    def warning(self, message: str):
        """Log warning level message"""
        self._write("WARN", message)

    def json_preview(self, label: str, data: Any, max_length: int = 500):
        """Log a preview of JSON data"""
        try:
            json_str = json.dumps(data, default=str)
            if len(json_str) > max_length:
                json_str = json_str[:max_length] + "..."
            self.debug(f"{label}: {json_str}")
        except Exception as e:
            self.error(f"Failed to serialize {label}: {e}")

    def structure_preview(self, label: str, data: dict):
        """Log structure of a dict without full content"""
        structure = {}
        for key, value in data.items():
            if isinstance(value, list):
                structure[key] = f"list[{len(value)}]"
            elif isinstance(value, dict):
                structure[key] = (
                    f"dict[{list(value.keys())[:3]}...]" if len(value.keys()) > 3 else f"dict[{list(value.keys())}]"
                )
            elif isinstance(value, str):
                structure[key] = f"str[{len(value)} chars]"
            else:
                structure[key] = type(value).__name__
        self.debug(f"{label}: {json.dumps(structure)}")

    def exception(self, message: str, exc: Exception | None = None):
        """Log exception with traceback"""
        import traceback

        if exc:
            self.error(f"{message}: {exc}")
            self.error(f"Traceback:\n{traceback.format_exc()}")
        else:
            self.error(message)
            self.error(f"Traceback:\n{traceback.format_exc()}")

    def cleanup_old_logs(self, max_files: int = 10):
        """Clean up log files, keeping the most recent max_files"""
        try:
            # Get all log files for this script
            log_files = list(self.log_dir.glob(f"{self.script_name}_*.log"))
            
            if len(log_files) <= max_files:
                return
            
            # Sort by modification time, newest first
            log_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Delete older files
            for old_file in log_files[max_files:]:
                old_file.unlink()
                self.info(f"Deleted old log file: {old_file.name}")
        except Exception as e:
            self.warning(f"Failed to cleanup old logs: {e}")


logger = SessionCleanupLogger("session_cleanup")


def detect_session(sessions_root: Path, project_dir: Path, session_id_arg: str | None) -> str | None:
    """Detect which session to process"""
    if session_id_arg:
        logger.info(f"Using explicit session ID: {session_id_arg}")
        return session_id_arg
    
    # Check environment variable
    env_session = os.getenv("CODEX_SESSION_ID")
    if env_session:
        logger.info(f"Using session ID from environment: {env_session}")
        return env_session
    
    # Find most recent session for current project
    try:
        exporter = CodexTranscriptExporter(sessions_root=sessions_root, verbose=False)
        project_sessions = exporter.get_project_sessions(project_dir)
        
        if not project_sessions:
            logger.warning("No sessions found for current project")
            return None
        
        # Get the most recent by checking session directory mtime
        latest_session = None
        latest_mtime = 0
        
        for session_id in project_sessions:
            session_dir = sessions_root / session_id
            if session_dir.exists():
                mtime = session_dir.stat().st_mtime
                if mtime > latest_mtime:
                    latest_mtime = mtime
                    latest_session = session_id
        
        if latest_session:
            logger.info(f"Detected latest project session: {latest_session}")
        return latest_session
    except Exception as e:
        logger.error(f"Error detecting session: {e}")
        return None


def load_messages_from_history(session_dir: Path) -> list[dict]:
    """Load and parse messages from history.jsonl"""
    history_file = session_dir / "history.jsonl"
    messages = []
    
    if not history_file.exists():
        logger.warning(f"History file not found: {history_file}")
        return messages
    
    try:
        with open(history_file) as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                    # Filter and extract actual conversation messages
                    if msg.get("type") in ["summary", "meta", "system"]:
                        continue

                    if "message" in msg and isinstance(msg["message"], dict):
                        inner_msg = msg["message"]
                        if inner_msg.get("role") in ["user", "assistant"]:
                            content = inner_msg.get("content", "")
                            if isinstance(content, list):
                                text_parts = []
                                for item in content:
                                    if isinstance(item, dict) and item.get("type") == "text":
                                        text_parts.append(item.get("text", ""))
                                content = " ".join(text_parts)

                            if content:
                                messages.append({"role": inner_msg["role"], "content": content})
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing line {line_num}: {e}")
    except Exception as e:
        logger.error(f"Error reading history file: {e}")
    
    logger.info(f"Loaded {len(messages)} conversation messages")
    return messages


async def main():
    """Main cleanup logic"""
    parser = argparse.ArgumentParser(description="Codex session cleanup - extract memories and export transcript")
    parser.add_argument("--session-id", help="Explicit session ID to process")
    parser.add_argument("--no-memory", action="store_true", help="Skip memory extraction")
    parser.add_argument("--no-transcript", action="store_true", help="Skip transcript export")
    parser.add_argument("--output-dir", type=Path, default=Path(".codex/transcripts"), help="Transcript output directory")
    parser.add_argument("--format", choices=["standard", "extended", "both", "compact"], default="both", help="Transcript format")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    try:
        # Check memory system
        memory_enabled = os.getenv("MEMORY_SYSTEM_ENABLED", "true").lower() in ["true", "1", "yes"]
        if not memory_enabled:
            logger.info("Memory system disabled via MEMORY_SYSTEM_ENABLED env var")
        
        logger.info("Starting session cleanup")
        logger.cleanup_old_logs()
        
        # Detect session
        sessions_root = Path(SESSIONS_DEFAULT)
        project_dir = Path.cwd()
        session_id = detect_session(sessions_root, project_dir, args.session_id)
        
        if not session_id:
            logger.error("No session detected to process")
            print("Error: No session detected to process", file=sys.stderr)
            return
        
        logger.info(f"Processing session: {session_id}")
        
        # Load messages
        session_dir = sessions_root / session_id
        messages = load_messages_from_history(session_dir)
        
        if not messages:
            logger.warning("No messages to process")
            print("Warning: No messages found in session", file=sys.stderr)
            return
        
        memories_extracted = 0
        transcript_exported = False
        transcript_path = None
        
        # Memory extraction
        if not args.no_memory and memory_enabled:
            try:
                async with asyncio.timeout(60):
                    logger.info("Starting memory extraction")
                    
                    # Get context from first user message
                    context = None
                    for msg in messages:
                        if msg.get("role") == "user":
                            context = msg.get("content", "")[:200]
                            break
                    
                    extractor = MemoryExtractor()
                    store = MemoryStore()
                    
                    extracted = await extractor.extract_from_messages(messages, context)
                    
                    if extracted and "memories" in extracted:
                        memories_list = extracted.get("memories", [])
                        store.add_memories_batch(extracted)
                        memories_extracted = len(memories_list)
                        logger.info(f"Extracted and stored {memories_extracted} memories")
            except TimeoutError:
                logger.error("Memory extraction timed out after 60 seconds")
            except Exception as e:
                logger.exception("Error during memory extraction", e)
        
        # Transcript export
        if not args.no_transcript:
            try:
                exporter = CodexTranscriptExporter(verbose=args.verbose)
                result = exporter.export_codex_transcript(
                    session_id=session_id,
                    output_dir=args.output_dir,
                    format_type=args.format
                )
                if result:
                    transcript_exported = True
                    transcript_path = str(result)
                    logger.info(f"Saved transcript to: {transcript_path}")
            except Exception as e:
                logger.exception("Error during transcript export", e)
        
        # Generate summary
        summary = {
            "sessionId": session_id,
            "memoriesExtracted": memories_extracted,
            "messagesProcessed": len(messages),
            "transcriptExported": transcript_exported,
            "transcriptPath": transcript_path,
            "timestamp": datetime.now().isoformat(),
            "source": "amplifier_cleanup"
        }
        
        # Write metadata
        metadata_file = Path(".codex/session_cleanup_metadata.json")
        metadata_file.parent.mkdir(exist_ok=True)
        with open(metadata_file, "w") as f:
            json.dump(summary, f, indent=2)
        
        # Print user-friendly summary
        print("✓ Session cleanup complete")
        if memories_extracted > 0:
            print(f"✓ Extracted {memories_extracted} memories")
        if transcript_exported and transcript_path:
            print(f"✓ Saved transcript to {transcript_path}")
        
    except Exception as e:
        logger.exception("Unexpected error during cleanup", e)
        print("Error during session cleanup", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())