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
from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import Any


class TranscriptManager:
    def __init__(self, backend: str = "auto"):
        self.backend = backend if backend in ["claude", "codex", "auto"] else "auto"
        self.data_dir = Path(".data")
        self.transcripts_dir = self.data_dir / "transcripts"
        self.sessions_file = self.data_dir / "sessions.json"
        self.codex_global_dir = Path("~/.codex/transcripts").expanduser()
        self.codex_local_dir = Path(".codex/transcripts")
        self.codex_sessions_root = Path("~/.codex/sessions").expanduser()
        self.codex_history_path = Path("~/.codex/history.jsonl").expanduser()

        # Detect backend if auto
        if self.backend == "auto":
            self.backend = self._detect_backend()

        self.current_session = self._get_current_session()

    def _detect_backend(self) -> str:
        """Detect backend based on available directories and files."""
        has_claude = Path(".claude").exists() or self.transcripts_dir.exists()
        has_codex = Path(".codex").exists() or self.codex_global_dir.exists() or self.codex_local_dir.exists()

        if has_claude and has_codex:
            return "auto"  # Use both
        if has_codex:
            return "codex"
        return "claude"  # Default to claude

    def _get_transcript_dirs(self) -> list[Path]:
        """Get list of transcript directories based on backend."""
        dirs = []
        if self.backend in ["claude", "auto"]:
            if self.transcripts_dir.exists():
                dirs.append(self.transcripts_dir)
        if self.backend in ["codex", "auto"]:
            if self.codex_global_dir.exists():
                dirs.append(self.codex_global_dir)
            if self.codex_local_dir.exists():
                dirs.append(self.codex_local_dir)
        return dirs

    @property
    def codex_transcripts_dir(self) -> Path:
        """Primary Codex transcripts directory (global ~/.codex/transcripts/)."""
        return self.codex_global_dir

    def _get_current_session(self) -> str | None:
        """Get current session ID from environment or recent activity"""
        # Check Claude Code current_session file
        if self.backend in ["claude", "auto"]:
            current_session_file = Path(".claude/current_session")
            if current_session_file.exists():
                with open(current_session_file) as f:
                    return f.read().strip()

        # For Codex, try to get most recent session
        # Note: Codex doesn't maintain a current_session file like Claude Code
        transcripts = self.list_transcripts(last_n=1)
        if transcripts:
            if self.backend == "claude" or transcripts[0].suffix == ".txt":
                # Extract session ID from Claude Code filename
                match = re.search(r"compact_\d+_\d+_([a-f0-9-]+)\.txt", transcripts[0].name)
                if match:
                    return match.group(1)
            else:
                # Extract session ID from Codex directory name
                return self._extract_codex_session_id(transcripts[0])

        return None

    def _extract_codex_session_id(self, session_path: Path) -> str | None:
        """Extract session ID from Codex session directory name."""
        if session_path.is_dir():
            # Format: YYYY-MM-DD-HH-MM-PM__cwd__sessionid
            parts = session_path.name.split("__")
            if len(parts) >= 3:
                return parts[-1]  # Last part is session ID
        return None

    def _session_id_from_transcript_path(self, transcript_file: Path) -> str | None:
        if transcript_file.suffix == ".txt":
            match = re.search(r"compact_\d+_\d+_([A-Za-z0-9-]+)\.txt", transcript_file.name)
            return match.group(1) if match else None
        if transcript_file.suffix == ".md":
            metadata = self._load_codex_transcript_metadata(transcript_file)
            return metadata.get("session_id") or self._extract_codex_session_id(transcript_file.parent)
        return None

    def _determine_backend_for_path(self, transcript_file: Path) -> str:
        if transcript_file.suffix == ".md":
            return "codex"
        if transcript_file.suffix == ".txt":
            return "claude"
        return "unknown"

    def _normalize_session_id(self, session_id: str) -> str:
        """Normalize session ID to handle both full and short forms."""
        # Remove any hyphens and convert to lowercase for comparison
        return session_id.replace("-", "").lower()

    def list_transcripts(self, last_n: int | None = None, backend_filter: str | None = None) -> list[Path]:
        """List available transcripts from all backends, optionally limited to last N"""
        transcripts = []

        if self.backend in ["claude", "auto"]:
            transcripts.extend(self._list_claude_transcripts())

        if self.backend in ["codex", "auto"]:
            transcripts.extend(self._list_codex_transcripts())

        if backend_filter:
            transcripts = [t for t in transcripts if self._determine_backend_for_path(t) == backend_filter]

        # Sort by modification time (most recent first)
        transcripts = sorted(transcripts, key=lambda p: p.stat().st_mtime, reverse=True)

        if last_n:
            return transcripts[:last_n]
        return transcripts

    def _list_claude_transcripts(self) -> list[Path]:
        """List Claude Code transcript files."""
        if not self.transcripts_dir.exists():
            return []
        return list(self.transcripts_dir.glob("compact_*.txt"))

    def _list_codex_transcripts(self) -> list[Path]:
        """List Codex transcript directories and files."""
        transcripts = []

        # Check global Codex transcripts
        if self.codex_global_dir.exists():
            for session_dir in self.codex_global_dir.iterdir():
                if session_dir.is_dir():
                    # Look for transcript files in session directory
                    transcript_md = session_dir / "transcript.md"
                    transcript_ext = session_dir / "transcript_extended.md"
                    if transcript_md.exists():
                        transcripts.append(transcript_md)
                    elif transcript_ext.exists():
                        transcripts.append(transcript_ext)

        # Check local Codex transcripts
        if self.codex_local_dir.exists():
            for session_dir in self.codex_local_dir.iterdir():
                if session_dir.is_dir():
                    transcript_md = session_dir / "transcript.md"
                    transcript_ext = session_dir / "transcript_extended.md"
                    if transcript_md.exists():
                        transcripts.append(transcript_md)
                    elif transcript_ext.exists():
                        transcripts.append(transcript_ext)

        return transcripts

    def _codex_variants(self, session_dir: Path) -> list[str]:
        variants: list[str] = []
        mapping = {
            "standard": session_dir / "transcript.md",
            "extended": session_dir / "transcript_extended.md",
            "compact": session_dir / "transcript_compact.md",
        }
        for name, path in mapping.items():
            if path.exists():
                variants.append(name)
        return variants

    def _extract_metadata_field(self, content: str, patterns: list[str]) -> str | None:
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _load_codex_transcript_metadata(self, transcript_file: Path) -> dict[str, Any]:
        session_dir = transcript_file.parent
        metadata: dict[str, Any] = {}
        meta_file = session_dir / "meta.json"
        if meta_file.exists():
            try:
                metadata = json.loads(meta_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                metadata = {}

        content: str | None = None
        if not metadata:
            try:
                content = transcript_file.read_text(encoding="utf-8")
            except OSError:
                content = None

        if content:
            metadata.setdefault(
                "session_id",
                self._extract_metadata_field(
                    content,
                    [
                        r"\*\*Session ID:\*\*\s*([A-Za-z0-9-]+)",
                        r"- Session ID:\s*([A-Za-z0-9-]+)",
                    ],
                )
                or self._extract_codex_session_id(session_dir),
            )
            metadata.setdefault(
                "started_at",
                self._extract_metadata_field(
                    content,
                    [
                        r"\*\*Started:\*\*\s*([^\n]+)",
                        r"- Start:\s*([^\n]+)",
                    ],
                ),
            )
            metadata.setdefault(
                "cwd",
                self._extract_metadata_field(
                    content,
                    [
                        r"\*\*Working Directory:\*\*\s*([^\n]+)",
                        r"- CWD:\s*([^\n]+)",
                    ],
                ),
            )

        metadata.setdefault("session_id", self._extract_codex_session_id(session_dir) or "unknown")
        metadata["session_dir"] = str(session_dir)
        metadata["variants_available"] = self._codex_variants(session_dir)
        return metadata

    def _extract_claude_metadata(self, content: str) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        metadata["session_id"] = self._extract_metadata_field(
            content,
            [
                r"Session ID:\s*([A-Za-z0-9-]+)",
                r"# Session ID:\s*([A-Za-z0-9-]+)",
            ],
        )
        metadata["started_at"] = self._extract_metadata_field(
            content,
            [
                r"Exported:\s*([^\n]+)",
                r"Session Start:\s*([^\n]+)",
            ],
        )
        return metadata

    def _parse_timestamp_string(self, value: str | None) -> datetime | None:
        if not value:
            return None
        value = value.strip()
        iso_candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
        try:
            dt = datetime.fromisoformat(iso_candidate)
            return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
        except ValueError:
            pass
        for fmt in [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%b %d, %Y %I:%M %p",
        ]:
            try:
                dt = datetime.strptime(value, fmt)
                return dt.replace(tzinfo=UTC)
            except ValueError:
                continue
        try:
            timestamp = float(value)
            return datetime.fromtimestamp(timestamp, tz=UTC)
        except (ValueError, OSError):
            return None

    def _segment_start_time(self, transcript_file: Path, backend: str, content: str) -> datetime:
        fallback = datetime.fromtimestamp(transcript_file.stat().st_mtime, tz=UTC)
        if backend == "codex":
            metadata = self._load_codex_transcript_metadata(transcript_file)
            started_at = self._parse_timestamp_string(metadata.get("started_at"))
            if started_at:
                return started_at
        elif backend == "claude":
            metadata = self._extract_claude_metadata(content)
            started_at = self._parse_timestamp_string(metadata.get("started_at"))
            if started_at:
                return started_at
        return fallback

    def load_transcript_content(self, identifier: str, format_preference: str = "standard") -> str | None:
        """Load a transcript by session ID or filename and return its content"""
        # Try as direct filename first (Claude Code .txt files)
        if identifier.endswith(".txt"):
            transcript_path = self.transcripts_dir / identifier
            if transcript_path.exists():
                with open(transcript_path, encoding="utf-8") as f:
                    return f.read()

        # Normalize session ID for comparison
        normalized_id = self._normalize_session_id(identifier)

        # Search through all available transcripts
        for transcript_file in self.list_transcripts():
            # Check Claude Code format
            if transcript_file.suffix == ".txt":
                if identifier in transcript_file.name or normalized_id in self._normalize_session_id(
                    transcript_file.name
                ):
                    with open(transcript_file, encoding="utf-8") as f:
                        return f.read()

            # Check Codex format (session directories)
            elif transcript_file.suffix == ".md":
                # Extract session ID from directory path
                session_id = self._extract_codex_session_id(transcript_file.parent)
                if session_id and (identifier == session_id or normalized_id == self._normalize_session_id(session_id)):
                    # For Codex, prefer format based on preference
                    session_dir = transcript_file.parent
                    preferred_files = {
                        "standard": session_dir / "transcript.md",
                        "extended": session_dir / "transcript_extended.md",
                    }

                    # Try preferred format first, then fallback
                    for fmt in [format_preference, "extended" if format_preference == "standard" else "standard"]:
                        if fmt in preferred_files and preferred_files[fmt].exists():
                            with open(preferred_files[fmt], encoding="utf-8") as f:
                                return f.read()

        return None

    def restore_conversation_lineage(
        self, session_id: str | None = None, backend_filter: str | None = None
    ) -> str | None:
        """Restore entire conversation lineage by outputting all transcript content"""
        transcripts = self.list_transcripts(backend_filter=backend_filter)
        if not transcripts:
            return None

        transcript_details: list[tuple[datetime, Path, str, str, str]] = []
        for transcript_file in transcripts:
            if not transcript_file.exists():
                continue
            try:
                content = transcript_file.read_text(encoding="utf-8")
            except OSError:
                continue

            backend = self._determine_backend_for_path(transcript_file)
            start_ts = self._segment_start_time(transcript_file, backend, content)

            if backend == "claude":
                metadata = self._extract_claude_metadata(content)
                claude_match = re.search(r"compact_\d+_\d+_([A-Za-z0-9-]+)\.txt", transcript_file.name)
                session_from_content = metadata.get("session_id") or (
                    claude_match.group(1) if claude_match else "unknown"
                )
                backend_tag = "[Claude Code]"
            else:
                metadata = self._load_codex_transcript_metadata(transcript_file)
                session_from_content = (
                    metadata.get("session_id") or self._extract_codex_session_id(transcript_file.parent) or "unknown"
                )
                backend_tag = "[Codex]"

            transcript_details.append(
                (start_ts, transcript_file, backend_tag, content, session_from_content or "unknown")
            )

        if not transcript_details:
            return None

        transcript_details.sort(key=lambda item: item[0])

        combined_content: list[str] = []
        for index, (start_ts, transcript_file, backend_tag, content, session_from_content) in enumerate(
            transcript_details, start=1
        ):
            combined_content.append(f"\n{'=' * 80}\n")
            combined_content.append(f"CONVERSATION SEGMENT {index} {backend_tag}\n")
            combined_content.append(f"File: {transcript_file.name}\n")
            combined_content.append(f"Start: {start_ts.isoformat()}\n")
            if session_from_content and session_from_content != "unknown":
                combined_content.append(f"Session ID: {session_from_content}\n")
            combined_content.append(f"{'=' * 80}\n\n")
            combined_content.append(content)

        if not combined_content:
            return None

        return "".join(combined_content)

    def search_transcripts(self, term: str, max_results: int = 10, backend_filter: str | None = None) -> str | None:
        """Search transcripts and output matching content with context"""
        results = []
        search_backend = backend_filter or self.backend

        for transcript_file in self.list_transcripts():
            # Skip if backend filtering is requested
            if backend_filter:
                backend = self._determine_backend_for_path(transcript_file)
                if backend_filter != backend:
                    continue

            try:
                with open(transcript_file, encoding="utf-8") as f:
                    content = f.read()
                    if term.lower() in content.lower():
                        # Determine session ID and backend
                        if transcript_file.suffix == ".txt":
                            # Claude Code format
                            match = re.search(r"compact_\d+_\d+_([a-f0-9-]+)\.txt", transcript_file.name)
                            session_id = match.group(1) if match else "unknown"
                            backend_tag = "[Claude Code]"
                        else:
                            # Codex format
                            session_id = self._extract_codex_session_id(transcript_file.parent) or "unknown"
                            backend_tag = "[Codex]"

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
                                    f"Match in {transcript_file.name} (line {i + 1}) {backend_tag}\n"
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

    def list_transcripts_json(self, last_n: int | None = None, backend_filter: str | None = None) -> str:
        """List transcripts metadata in JSON format"""
        transcripts = self.list_transcripts(last_n=last_n, backend_filter=backend_filter)
        results = []

        for t in transcripts:
            backend = self._determine_backend_for_path(t)
            mtime = datetime.fromtimestamp(t.stat().st_mtime)  # noqa: DTZ006
            size_kb = t.stat().st_size / 1024
            item: dict[str, Any] = {
                "backend": backend,
                "filename": t.name,
                "timestamp": mtime.isoformat(),
                "size_kb": round(size_kb, 1),
            }

            if backend == "claude":
                match = re.search(r"compact_\d+_\d+_([A-Za-z0-9-]+)\.txt", t.name)
                session_id = match.group(1) if match else "unknown"
                item["session_id"] = session_id
                item["summary"] = ""
                try:
                    with open(t, encoding="utf-8") as f:
                        content = f.read(5000)
                        user_msg = re.search(r"Human:\s+(.+?)\n", content)
                        if user_msg:
                            item["summary"] = user_msg.group(1)[:200]
                except Exception:
                    pass
            elif backend == "codex":
                metadata = self._load_codex_transcript_metadata(t)
                item.update(metadata)
            else:
                item["session_id"] = "unknown"

            results.append(item)

        return json.dumps(results, indent=2)

    def export_transcript(
        self,
        session_id: str | None = None,
        output_format: str = "text",
        backend_override: str | None = None,
    ) -> Path | None:
        """Export a transcript to a file"""
        if not session_id:
            session_id = self.current_session

        if not session_id:
            return None

        normalized_target = self._normalize_session_id(session_id)

        transcripts = self.list_transcripts()
        matches: list[tuple[str, Path, str]] = []
        for transcript_path in transcripts:
            backend = self._determine_backend_for_path(transcript_path)
            if backend_override and backend != backend_override:
                continue
            candidate_session = self._session_id_from_transcript_path(transcript_path)
            if not candidate_session:
                continue
            if self._normalize_session_id(candidate_session).startswith(normalized_target):
                matches.append((backend, transcript_path, candidate_session))

        if not matches:
            return None

        backend, transcript_file, matched_session = matches[0]

        export_dir = Path("exported_transcripts")
        export_dir.mkdir(exist_ok=True)

        if backend == "codex":
            codex_tools_path = Path(".codex/tools").resolve()
            sys.path.append(str(codex_tools_path))
            try:
                from transcript_exporter import CodexTranscriptExporter  # type: ignore
            finally:
                if sys.path and sys.path[-1] == str(codex_tools_path):
                    sys.path.pop()

            exporter = CodexTranscriptExporter(
                sessions_root=self.codex_sessions_root,
                verbose=self.backend == "codex",
            )
            exporter.history_path = self.codex_history_path
            codex_format = self._map_codex_export_format(output_format)
            exported_path = exporter.export_codex_transcript(
                matched_session,
                export_dir,
                format_type=codex_format,
            )
            return exported_path

        # Claude export path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if output_format in {"markdown", "standard", "extended", "both"}:
            output_file = export_dir / f"conversation_{timestamp}.md"
            try:
                content = transcript_file.read_text(encoding="utf-8")
            except OSError:
                return None
            converted = self._convert_claude_to_codex(content, matched_session)
            output_file.write_text(converted, encoding="utf-8")
        else:
            output_file = export_dir / f"conversation_{timestamp}.txt"
            shutil.copy2(transcript_file, output_file)

        return output_file

    def _map_codex_export_format(self, output_format: str) -> str:
        mapping = {
            "markdown": "standard",
            "text": "compact",
            "standard": "standard",
            "extended": "extended",
            "both": "both",
            "compact": "compact",
        }
        return mapping.get(output_format, "standard")

    def convert_format(
        self, session_id: str, from_backend: str, to_backend: str, output_path: Path | None = None
    ) -> bool:
        """Convert a transcript from one backend format to another."""
        # Load source transcript
        original_backend = self.backend
        self.backend = from_backend
        content = self.load_transcript_content(session_id)
        self.backend = original_backend

        if not content:
            print(f"Could not find transcript for session {session_id} in {from_backend} backend", file=sys.stderr)
            return False

        # Simple format conversion (basic implementation)
        if from_backend == "claude" and to_backend == "codex":
            converted_content = self._convert_claude_to_codex(content, session_id)
        elif from_backend == "codex" and to_backend == "claude":
            converted_content = self._convert_codex_to_claude(content, session_id)
        else:
            print(f"Conversion from {from_backend} to {to_backend} not supported", file=sys.stderr)
            return False

        # Write converted content
        if output_path is None:
            if to_backend == "claude":
                output_path = self.transcripts_dir / f"converted_{session_id}.txt"
            else:
                output_dir = self.codex_local_dir / f"converted_{session_id}"
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / "transcript.md"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(converted_content)

        print(f"Converted transcript saved to {output_path}")
        return True

    def _convert_claude_to_codex(self, content: str, session_id: str) -> str:
        """Convert Claude Code format to Codex markdown format."""
        lines = content.split("\n")
        result = []

        # Add Codex header
        result.append("# Codex Session Transcript (Converted from Claude Code)")
        result.append("")
        result.append(f"**Session ID:** {session_id}")
        result.append(f"**Converted:** {datetime.now().isoformat()}")
        result.append("")
        result.append("---")
        result.append("")
        result.append("## Conversation")
        result.append("")

        # Simple conversion of message formats
        for line in lines:
            if line.startswith("[USER]:"):
                message = line[7:].strip()
                result.append("- **User**")
                result.append(f"  {message}")
                result.append("")
            elif line.startswith("[ASSISTANT]:"):
                message = line[13:].strip()
                result.append("- **Assistant**")
                result.append(f"  {message}")
                result.append("")
            elif line.startswith("[THINKING]:"):
                message = line[11:].strip()
                result.append("- **Assistant [thinking]**")
                result.append(f"  {message}")
                result.append("")
            elif line.startswith("[TOOL USE:"):
                tool_match = re.search(r"\[TOOL USE: ([^\]]+)\]", line)
                if tool_match:
                    tool_name = tool_match.group(1)
                    result.append(f"- **Tool Call ({tool_name})**")
            elif line.startswith("[TOOL RESULT]"):
                result.append("- **Tool Result**")

        return "\n".join(result)

    def _convert_codex_to_claude(self, content: str, session_id: str) -> str:
        """Convert Codex markdown format to Claude Code format."""
        lines = content.split("\n")
        result = []

        # Add Claude Code header
        result.append("# Amplifier Claude Code Transcript Export (Converted from Codex)")
        result.append(f"# Converted: {datetime.now()}")
        result.append(f"# Session ID: {session_id}")
        result.append("")
        result.append("=" * 80)
        result.append("")

        # Simple conversion of message formats
        for line in lines:
            if "- **User**" in line:
                # Next line typically contains the message
                result.append("[USER]: ")
            elif "- **Assistant**" in line and "[thinking]" not in line:
                result.append("[ASSISTANT]: ")
            elif "- **Assistant [thinking]**" in line:
                result.append("[THINKING]: ")
            elif "- **Tool Call" in line:
                tool_match = re.search(r"Tool Call \(([^)]+)\)", line)
                if tool_match:
                    tool_name = tool_match.group(1)
                    result.append(f"[TOOL USE: {tool_name}]")
            elif "- **Tool Result**" in line:
                result.append("[TOOL RESULT]")
            elif line.strip() and not line.startswith("#") and not line.startswith("**") and not line.startswith("-"):
                # Regular content line
                result.append(line)

        return "\n".join(result)


def main():
    parser = argparse.ArgumentParser(description="Transcript Manager - Pure CLI for Claude Code transcripts")
    parser.add_argument(
        "--backend",
        choices=["claude", "codex", "auto"],
        default="auto",
        help="Select backend preference (default: auto)",
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Restore command - outputs full conversation lineage content
    restore_parser = subparsers.add_parser("restore", help="Output entire conversation lineage content")
    restore_parser.add_argument("--session-id", help="Session ID to restore (default: current/latest)")
    restore_parser.add_argument("--backend", choices=["claude", "codex"], help="Filter transcripts by backend")

    # Load command - outputs specific transcript content
    load_parser = subparsers.add_parser("load", help="Output transcript content")
    load_parser.add_argument("session_id", help="Session ID or filename")
    load_parser.add_argument(
        "--format",
        choices=["standard", "extended", "markdown", "text"],
        default="standard",
        help="Preferred transcript format when multiple variants exist",
    )

    # List command - outputs metadata only
    list_parser = subparsers.add_parser("list", help="List transcript metadata")
    list_parser.add_argument("--last", type=int, help="Show last N transcripts")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")
    list_parser.add_argument("--backend", choices=["claude", "codex"], help="Filter transcripts by backend")

    # Search command - outputs matching content
    search_parser = subparsers.add_parser("search", help="Search and output matching content")
    search_parser.add_argument("term", help="Search term")
    search_parser.add_argument("--max", type=int, default=10, help="Maximum results")
    search_parser.add_argument("--backend", choices=["claude", "codex"], help="Filter transcripts by backend")

    # Export command - exports to file
    export_parser = subparsers.add_parser("export", help="Export transcript to file")
    export_parser.add_argument("--session-id", help="Session ID to export (default: current)")
    export_parser.add_argument(
        "--format",
        choices=["text", "markdown", "standard", "extended", "both", "compact"],
        default="markdown",
        help="Export format (text/markdown for Claude, standard/extended/both/compact for Codex)",
    )
    export_parser.add_argument("--backend", choices=["claude", "codex"], help="Force backend for export lookup")
    export_parser.add_argument("--current", action="store_true", help="Export the current session when no ID provided")

    args = parser.parse_args()

    manager = TranscriptManager(backend=args.backend)

    if args.command == "restore":
        content = manager.restore_conversation_lineage(
            session_id=args.session_id, backend_filter=getattr(args, "backend", None)
        )
        if content:
            print(content)
        else:
            print("Error: No transcripts found to restore", file=sys.stderr)
            sys.exit(1)

    elif args.command == "load":
        content = manager.load_transcript_content(args.session_id, format_preference=args.format)
        if content:
            print(content)
        else:
            print(f"Error: Transcript not found for '{args.session_id}'", file=sys.stderr)
            sys.exit(1)

    elif args.command == "list":
        if args.json:
            print(manager.list_transcripts_json(last_n=args.last, backend_filter=getattr(args, "backend", None)))
        else:
            transcripts = manager.list_transcripts(last_n=args.last, backend_filter=getattr(args, "backend", None))
            if not transcripts:
                print("No transcripts found")
            else:
                for t in transcripts:
                    backend_label = manager._determine_backend_for_path(t)
                    backend_tag = "[CLAUDE]" if backend_label == "claude" else "[CODEX]"
                    session_id = manager._session_id_from_transcript_path(t) or "unknown"
                    mtime = datetime.fromtimestamp(t.stat().st_mtime)  # noqa: DTZ006
                    size_kb = t.stat().st_size / 1024
                    if backend_label == "codex":
                        variants = ",".join(manager._codex_variants(t.parent))
                        print(
                            f"{backend_tag} {session_id[:8]}... | {mtime.strftime('%Y-%m-%d %H:%M')} | "
                            f"{size_kb:.1f}KB | variants={variants or 'standard'} | {t.name}"
                        )
                    else:
                        print(
                            f"{backend_tag} {session_id[:8]}... | {mtime.strftime('%Y-%m-%d %H:%M')} | "
                            f"{size_kb:.1f}KB | {t.name}"
                        )

    elif args.command == "search":
        results = manager.search_transcripts(
            args.term, max_results=args.max, backend_filter=getattr(args, "backend", None)
        )
        if results:
            print(results)
        else:
            print(f"No matches found for '{args.term}'")

    elif args.command == "export":
        target_session = args.session_id
        if not target_session and getattr(args, "current", False):
            target_session = manager.current_session

        output_file = manager.export_transcript(
            session_id=target_session,
            output_format=args.format,
            backend_override=getattr(args, "backend", None),
        )
        if output_file:
            print(f"Exported to: {output_file}")
        else:
            print("Error: Failed to export transcript", file=sys.stderr)
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
