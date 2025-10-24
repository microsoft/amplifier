#!/usr/bin/env python3
"""
Codex Transcript Exporter - Codex-specific transcript exporter mirroring Claude Code's PreCompact hook.

This tool provides equivalent functionality to .claude/tools/hook_precompact.py but for Codex sessions.
It exports Codex session transcripts to a specified directory with duplicate detection and formatting.
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Import functions from the main codex transcripts builder
sys.path.append(str(Path(__file__).parent.parent.parent / "tools"))

try:
    from codex_transcripts_builder import HISTORY_DEFAULT
    from codex_transcripts_builder import SESSIONS_DEFAULT
    from codex_transcripts_builder import SessionMeta
    from codex_transcripts_builder import collect_events
    from codex_transcripts_builder import load_history
    from codex_transcripts_builder import load_rollout_items
    from codex_transcripts_builder import load_session_meta
    from codex_transcripts_builder import write_conversation_transcript
    from codex_transcripts_builder import write_extended_transcript
    from codex_transcripts_builder import write_session_metadata
except ImportError as e:
    print(f"Error importing codex_transcripts_builder: {e}", file=sys.stderr)
    print("Make sure tools/codex_transcripts_builder.py is available", file=sys.stderr)
    sys.exit(1)


class CodexTranscriptExporter:
    def __init__(
        self,
        sessions_root: Path = SESSIONS_DEFAULT,
        verbose: bool = False,
        tz_name: str = "America/Los_Angeles",
    ):
        self.sessions_root = sessions_root
        self.verbose = verbose
        self.history_path = HISTORY_DEFAULT
        self.tz_name = tz_name

    def get_current_codex_session(self) -> str | None:
        """Detect the most recent/active Codex session."""
        try:
            # Load history to find most recent session
            sessions = load_history(self.history_path, skip_errors=True, verbose=self.verbose)
            if not sessions:
                return None

            # Find the most recent session by timestamp
            latest_session = None
            latest_timestamp = 0

            for session_id, entries in sessions.items():
                if entries:
                    max_ts = max(entry.ts for entry in entries)
                    if max_ts > latest_timestamp:
                        latest_timestamp = max_ts
                        latest_session = session_id

            return latest_session
        except Exception as e:
            if self.verbose:
                print(f"Error detecting current session: {e}", file=sys.stderr)
            return None

    def get_project_sessions(self, project_dir: Path) -> list[str]:
        """Get all Codex sessions that match the project directory."""
        try:
            sessions = load_history(self.history_path, skip_errors=True, verbose=self.verbose)
            project_sessions = []
            project_str = str(project_dir.resolve())

            for session_id in sessions:
                session_dir = self.sessions_root / session_id
                if session_dir.exists():
                    try:
                        # Load session metadata to check cwd
                        meta = load_session_meta(session_dir)
                        if meta and meta.cwd and Path(meta.cwd).resolve() == Path(project_str):
                            project_sessions.append(session_id)
                    except Exception:
                        continue

            return project_sessions
        except Exception as e:
            if self.verbose:
                print(f"Error filtering project sessions: {e}", file=sys.stderr)
            return []

    def export_codex_transcript(
        self,
        session_id: str,
        output_dir: Path,
        format_type: str = "standard",
        project_dir: Path | None = None,
    ) -> Path | None:
        """Export a Codex transcript to the specified directory.

        Args:
            session_id: Session to export
            output_dir: Directory to write transcript
            format_type: 'standard', 'extended', 'both', 'compact'
            project_dir: Optional project directory for filtering

        Returns:
            Path to exported transcript or None if failed
        """
        try:
            # Validate session exists
            session_dir = self.sessions_root / session_id
            if not session_dir.exists():
                if self.verbose:
                    print(f"Session directory not found: {session_dir}", file=sys.stderr)
                return None

            output_dir.mkdir(parents=True, exist_ok=True)
            existing_ids = self._extract_loaded_session_ids(output_dir)

            # Load history once to gather entries
            sessions = load_history(self.history_path, skip_errors=True, verbose=self.verbose)
            history_entries = sessions.get(session_id, [])

            # Load rollout items via builder contract
            meta, rollout_items = load_rollout_items(session_id, self.sessions_root)
            events = collect_events(meta, history_entries, rollout_items)

            session_output_dir = output_dir / session_id
            already_exported = session_id in existing_ids

            if already_exported and format_type != "compact":
                existing_path = self._locate_existing_export(session_id, session_output_dir, output_dir, format_type)
                if self.verbose:
                    print(f"Session {session_id} already exported; reusing {existing_path}", file=sys.stderr)
                return existing_path

            session_output_dir.mkdir(parents=True, exist_ok=True)

            exported_path: Path | None = None
            if format_type in ["standard", "both"]:
                write_conversation_transcript(session_output_dir, meta, events, self.tz_name)
                exported_path = session_output_dir / "transcript.md"

            if format_type in ["extended", "both"]:
                write_extended_transcript(session_output_dir, meta, events, self.tz_name)
                if exported_path is None:
                    exported_path = session_output_dir / "transcript_extended.md"

            if format_type == "compact":
                compact_path = output_dir / f"{session_id}_compact.md"
                self._write_compact_transcript(
                    events,
                    compact_path,
                    meta,
                    already_embedded=already_exported,
                )
                exported_path = compact_path

            write_session_metadata(session_output_dir, meta, events)

            if self.verbose and exported_path:
                print(f"Exported session {session_id} to {exported_path}")

            return exported_path

        except Exception as e:
            if self.verbose:
                print(f"Error exporting session {session_id}: {e}", file=sys.stderr)
            return None

    def _extract_loaded_session_ids(self, output_dir: Path) -> set[str]:
        """Extract session IDs from previously exported transcripts."""
        session_ids = set()

        if not output_dir.exists():
            return session_ids

        for candidate in output_dir.iterdir():
            if candidate.is_dir():
                meta_file = candidate / "meta.json"
                if meta_file.exists():
                    try:
                        metadata = json.loads(meta_file.read_text(encoding="utf-8"))
                        stored_id = metadata.get("session_id")
                        if stored_id:
                            session_ids.add(str(stored_id))
                            continue
                    except (OSError, json.JSONDecodeError):
                        pass
                for transcript_file in candidate.glob("transcript*.md"):
                    session_ids.update(self._session_ids_from_text(transcript_file))
            elif candidate.suffix == ".md":
                session_ids.update(self._session_ids_from_text(candidate))

        return session_ids

    def _session_ids_from_text(self, transcript_file: Path) -> set[str]:
        ids: set[str] = set()
        try:
            content = transcript_file.read_text(encoding="utf-8")
        except OSError:
            return ids

        ids.update(re.findall(r"Session ID:\s*([A-Za-z0-9-]+)", content))
        ids.update(re.findall(r"\*\*Session ID:\*\*\s*([A-Za-z0-9-]+)", content))
        ids.update(re.findall(r"# Embedded Transcript: ([a-f0-9-]+)", content))
        return ids

    def _locate_existing_export(
        self,
        session_id: str,
        session_output_dir: Path,
        output_dir: Path,
        format_type: str,
    ) -> Path | None:
        candidates: list[Path] = []

        if session_output_dir.exists():
            candidates.extend(
                [
                    session_output_dir / "transcript.md",
                    session_output_dir / "transcript_extended.md",
                    session_output_dir / "transcript_compact.md",
                ]
            )

        # Legacy flat-file exports
        candidates.extend(
            [
                output_dir / f"{session_id}_transcript.md",
                output_dir / f"{session_id}_transcript_extended.md",
                output_dir / f"{session_id}_compact.md",
            ]
        )

        if format_type == "standard":
            preferred = [candidates[0], candidates[1]]
        elif format_type == "extended":
            preferred = [candidates[1], candidates[0]]
        elif format_type == "compact":
            preferred = [candidates[2]]
        else:
            preferred = candidates[:2]

        for candidate in preferred:
            if candidate and candidate.exists():
                return candidate
        return None

    def _write_compact_transcript(
        self,
        events: list[Any],
        output_path: Path,
        session_meta: SessionMeta | None,
        already_embedded: bool = False,
    ):
        """Write a compact single-file transcript combining standard and extended formats."""
        with open(output_path, "w", encoding="utf-8") as f:
            if already_embedded and session_meta:
                f.write(f"# Embedded Transcript: {session_meta.session_id}\n\n")
            else:
                f.write("# Codex Session Transcript (Compact Format)\n\n")

            if session_meta:
                f.write(f"**Session ID:** {session_meta.session_id}\n")
                f.write(f"**Started:** {session_meta.started_at}\n")
                if session_meta.cwd:
                    f.write(f"**Working Directory:** {session_meta.cwd}\n")
                f.write(f"**Exported:** {datetime.now()}\n\n")

            f.write("---\n\n")

            # Write conversation flow
            f.write("## Conversation\n\n")
            for event in events:
                timestamp = getattr(event, "timestamp", None)
                if isinstance(timestamp, datetime):
                    timestamp_str = timestamp.isoformat()
                else:
                    timestamp_str = "unknown"

                role = getattr(event, "role", None) or getattr(event, "kind", "event")
                role_label = role.title() if isinstance(role, str) else "Event"

                text = getattr(event, "text", "") or ""
                if text:
                    f.write(f"**{role_label} @ {timestamp_str}:** {text}\n\n")
                elif getattr(event, "tool_name", None):
                    f.write(f"**Tool Call {event.tool_name} @ {timestamp_str}:** {event.tool_args}\n\n")
                    if getattr(event, "tool_result", None):
                        f.write(f"**Tool Result:** {event.tool_result}\n\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Codex session transcripts")
    parser.add_argument("--session-id", help="Export specific session ID (full or short form)")
    parser.add_argument("--current", action="store_true", help="Export current/latest session")
    parser.add_argument("--project-only", action="store_true", help="Filter sessions by current project directory")
    parser.add_argument(
        "--format", choices=["standard", "extended", "both", "compact"], default="standard", help="Output format"
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path(".codex/transcripts"), help="Output directory for transcripts"
    )
    parser.add_argument("--sessions-root", type=Path, default=SESSIONS_DEFAULT, help="Codex sessions directory")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    exporter = CodexTranscriptExporter(sessions_root=args.sessions_root, verbose=args.verbose)

    # Determine which session(s) to export
    sessions_to_export = []

    if args.session_id:
        sessions_to_export.append(args.session_id)
    elif args.current:
        current_session = exporter.get_current_codex_session()
        if current_session:
            sessions_to_export.append(current_session)
        else:
            print("No current session found", file=sys.stderr)
            sys.exit(1)
    elif args.project_only:
        project_sessions = exporter.get_project_sessions(Path.cwd())
        sessions_to_export.extend(project_sessions)
        if not sessions_to_export:
            print("No project sessions found", file=sys.stderr)
            sys.exit(1)
    else:
        print("Must specify --session-id, --current, or --project-only", file=sys.stderr)
        sys.exit(1)

    # Export sessions
    success_count = 0
    for session_id in sessions_to_export:
        result = exporter.export_codex_transcript(
            session_id=session_id,
            output_dir=args.output_dir,
            format_type=args.format,
            project_dir=Path.cwd() if args.project_only else None,
        )
        if result:
            success_count += 1
            print(f"Exported: {result}")
        else:
            print(f"Failed to export session: {session_id}", file=sys.stderr)

    if args.verbose:
        print(f"Successfully exported {success_count}/{len(sessions_to_export)} sessions")

    sys.exit(0 if success_count > 0 else 1)


if __name__ == "__main__":
    main()
