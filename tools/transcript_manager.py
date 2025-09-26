#!/usr/bin/env python3
"""
Transcript Manager - CLI tool for managing Claude Code conversation transcripts
A pure CLI that outputs transcript content directly for consumption by agents
"""

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path


class TranscriptManager:
    def __init__(self):
        self.data_dir = Path(".data")
        self.transcripts_dir = self.data_dir / "transcripts"
        self.sessions_file = self.data_dir / "sessions.json"
        self.current_session = self._get_current_session()

    def _get_current_session(self) -> str | None:
        """Get current session ID from environment or recent activity"""
        # Check if there's a current_session file
        current_session_file = Path(".claude/current_session")
        if current_session_file.exists():
            with open(current_session_file) as f:
                return f.read().strip()

        # Otherwise, find the most recent session from transcripts
        transcripts = self.list_transcripts(last_n=1)
        if transcripts:
            # Extract session ID from filename
            match = re.search(r"compact_\d+_\d+_([a-f0-9-]+)\.txt", transcripts[0].name)
            if match:
                return match.group(1)

        return None

    def list_transcripts(self, last_n: int | None = None) -> list[Path]:
        """List available transcripts, optionally limited to last N"""
        if not self.transcripts_dir.exists():
            return []

        transcripts = sorted(self.transcripts_dir.glob("compact_*.txt"), key=lambda p: p.stat().st_mtime, reverse=True)

        if last_n:
            return transcripts[:last_n]
        return transcripts

    def load_transcript_content(self, identifier: str) -> str | None:
        """Load a transcript by session ID or filename and return its content"""
        # Try as direct filename first
        if identifier.endswith(".txt"):
            transcript_path = self.transcripts_dir / identifier
            if transcript_path.exists():
                with open(transcript_path, encoding="utf-8") as f:
                    return f.read()

        # Try to find by session ID
        for transcript_file in self.list_transcripts():
            if identifier in transcript_file.name:
                with open(transcript_file, encoding="utf-8") as f:
                    return f.read()

        return None

    def restore_conversation_lineage(self, session_id: str | None = None) -> str | None:
        """Restore entire conversation lineage by outputting all transcript content"""
        # Get all available transcripts
        transcripts = self.list_transcripts()
        if not transcripts:
            return None

        # Sort transcripts by modification time (oldest first) to maintain chronological order
        transcripts_to_process = sorted(transcripts, key=lambda p: p.stat().st_mtime)

        combined_content = []
        sessions_restored = 0

        # Process each transcript file
        for transcript_file in transcripts_to_process:
            if transcript_file.exists():
                with open(transcript_file, encoding="utf-8") as f:
                    content = f.read()

                    # Extract session info from the transcript content if available
                    session_id_match = re.search(r"Session ID:\s*([a-f0-9-]+)", content)
                    session_id_from_content = session_id_match.group(1) if session_id_match else "unknown"

                    # Add separator and content
                    combined_content.append(f"\n{'=' * 80}\n")
                    combined_content.append(f"CONVERSATION SEGMENT {sessions_restored + 1}\n")
                    combined_content.append(f"File: {transcript_file.name}\n")
                    if session_id_from_content != "unknown":
                        combined_content.append(f"Session ID: {session_id_from_content}\n")
                    combined_content.append(f"{'=' * 80}\n\n")
                    combined_content.append(content)
                    sessions_restored += 1

        if not combined_content:
            return None

        return "".join(combined_content)

    def search_transcripts(self, term: str, max_results: int = 10) -> str | None:
        """Search transcripts and output matching content with context"""
        results = []
        for transcript_file in self.list_transcripts():
            try:
                with open(transcript_file, encoding="utf-8") as f:
                    content = f.read()
                    if term.lower() in content.lower():
                        # Extract session ID from filename
                        match = re.search(r"compact_\d+_\d+_([a-f0-9-]+)\.txt", transcript_file.name)
                        session_id = match.group(1) if match else "unknown"

                        # Find all occurrences with context
                        lines = content.split("\n")
                        for i, line in enumerate(lines):
                            if term.lower() in line.lower() and len(results) < max_results:
                                # Get context (5 lines before and after)
                                context_start = max(0, i - 5)
                                context_end = min(len(lines), i + 6)
                                context = "\n".join(lines[context_start:context_end])

                                results.append(
                                    f"\n{'=' * 60}\n"
                                    f"Match in {transcript_file.name} (line {i + 1})\n"
                                    f"Session ID: {session_id}\n"
                                    f"{'=' * 60}\n"
                                    f"{context}\n"
                                )

                                if len(results) >= max_results:
                                    break
            except Exception as e:
                print(f"Error searching {transcript_file.name}: {e}", file=sys.stderr)

        if results:
            return "".join(results)
        return None

    def list_transcripts_json(self, last_n: int | None = None) -> str:
        """List transcripts metadata in JSON format"""
        transcripts = self.list_transcripts(last_n=last_n)
        results = []

        for t in transcripts:
            # Extract session ID
            match = re.search(r"compact_\d+_\d+_([a-f0-9-]+)\.txt", t.name)
            session_id = match.group(1) if match else "unknown"

            # Get metadata
            mtime = datetime.fromtimestamp(t.stat().st_mtime)  # noqa: DTZ006
            size_kb = t.stat().st_size / 1024

            # Try to get first user message as summary
            summary = ""
            try:
                with open(t, encoding="utf-8") as f:
                    content = f.read(5000)  # Read first 5KB
                    # Look for first user message
                    user_msg = re.search(r"Human: (.+?)\n", content)
                    if user_msg:
                        summary = user_msg.group(1)[:200]
            except Exception:
                pass

            results.append(
                {
                    "session_id": session_id,
                    "filename": t.name,
                    "timestamp": mtime.isoformat(),
                    "size_kb": round(size_kb, 1),
                    "summary": summary,
                }
            )

        return json.dumps(results, indent=2)

    def export_transcript(self, session_id: str | None = None, output_format: str = "text") -> Path | None:
        """Export a transcript to a file"""
        if not session_id:
            session_id = self.current_session

        if not session_id:
            return None

        # Find the transcript file
        transcript_file = None
        for t in self.list_transcripts():
            if session_id in t.name:
                transcript_file = t
                break

        if not transcript_file:
            return None

        # Create export directory
        export_dir = Path("exported_transcripts")
        export_dir.mkdir(exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if output_format == "markdown":
            output_file = export_dir / f"conversation_{timestamp}.md"
        else:
            output_file = export_dir / f"conversation_{timestamp}.txt"

        # Copy the transcript
        shutil.copy2(transcript_file, output_file)

        return output_file


def main():
    parser = argparse.ArgumentParser(description="Transcript Manager - Pure CLI for Claude Code transcripts")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Restore command - outputs full conversation lineage content
    restore_parser = subparsers.add_parser("restore", help="Output entire conversation lineage content")
    restore_parser.add_argument("--session-id", help="Session ID to restore (default: current/latest)")

    # Load command - outputs specific transcript content
    load_parser = subparsers.add_parser("load", help="Output transcript content")
    load_parser.add_argument("session_id", help="Session ID or filename")

    # List command - outputs metadata only
    list_parser = subparsers.add_parser("list", help="List transcript metadata")
    list_parser.add_argument("--last", type=int, help="Show last N transcripts")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Search command - outputs matching content
    search_parser = subparsers.add_parser("search", help="Search and output matching content")
    search_parser.add_argument("term", help="Search term")
    search_parser.add_argument("--max", type=int, default=10, help="Maximum results")

    # Export command - exports to file
    export_parser = subparsers.add_parser("export", help="Export transcript to file")
    export_parser.add_argument("--session-id", help="Session ID to export (default: current)")
    export_parser.add_argument("--format", choices=["text", "markdown"], default="text", help="Export format")

    args = parser.parse_args()

    manager = TranscriptManager()

    if args.command == "restore":
        content = manager.restore_conversation_lineage(session_id=args.session_id)
        if content:
            print(content)
        else:
            print("Error: No transcripts found to restore", file=sys.stderr)
            sys.exit(1)

    elif args.command == "load":
        content = manager.load_transcript_content(args.session_id)
        if content:
            print(content)
        else:
            print(f"Error: Transcript not found for '{args.session_id}'", file=sys.stderr)
            sys.exit(1)

    elif args.command == "list":
        if args.json:
            print(manager.list_transcripts_json(last_n=args.last))
        else:
            transcripts = manager.list_transcripts(last_n=args.last)
            if not transcripts:
                print("No transcripts found")
            else:
                for t in transcripts:
                    # Extract session ID
                    match = re.search(r"compact_\d+_\d+_([a-f0-9-]+)\.txt", t.name)
                    session_id = match.group(1) if match else "unknown"
                    mtime = datetime.fromtimestamp(t.stat().st_mtime)  # noqa: DTZ006
                    size_kb = t.stat().st_size / 1024
                    print(f"{session_id[:8]}... | {mtime.strftime('%Y-%m-%d %H:%M')} | {size_kb:.1f}KB | {t.name}")

    elif args.command == "search":
        results = manager.search_transcripts(args.term, max_results=args.max)
        if results:
            print(results)
        else:
            print(f"No matches found for '{args.term}'")

    elif args.command == "export":
        output_file = manager.export_transcript(session_id=args.session_id, output_format=args.format)
        if output_file:
            print(f"Exported to: {output_file}")
        else:
            print("Error: Failed to export transcript", file=sys.stderr)
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
