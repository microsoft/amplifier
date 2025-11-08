#!/usr/bin/env python3
"""
Transcript Saver MCP Server - Codex-specific transcript management server.

This server provides tools to export, list, and convert Codex session transcripts,
mirroring the functionality of Claude Code's PreCompact hook but with explicit tool invocation.
"""

import json
import sys
from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("Error: MCP SDK not installed. Run 'uv add mcp' to install.", file=sys.stderr)
    exit(1)

# Add parent directory to path for absolute imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import base utilities
try:
    from base import AmplifierMCPServer
    from base import error_response
    from base import success_response
except ImportError:
    print("Error: Base utilities not found. Ensure base.py is available.", file=sys.stderr)
    exit(1)

# Add .codex to path for tool imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import transcript exporter
try:
    from tools.transcript_exporter import CodexTranscriptExporter
except ImportError:
    CodexTranscriptExporter = None

# Import codex transcripts builder
try:
    from tools.codex_transcripts_builder import HISTORY_DEFAULT
    from tools.codex_transcripts_builder import SESSIONS_DEFAULT
    from tools.codex_transcripts_builder import load_history
    from tools.codex_transcripts_builder import process_session
except ImportError:
    load_history = None
    process_session = None

# Import transcript manager
try:
    from tools.transcript_manager import TranscriptManager
except ImportError:
    TranscriptManager = None


class TranscriptSaverServer(AmplifierMCPServer):
    """MCP server for managing Codex session transcripts"""

    def __init__(self):
        # Initialize FastMCP
        mcp = FastMCP("amplifier-transcripts")

        # Call parent constructor
        super().__init__("transcript_saver", mcp)

        # Initialize transcript exporter if available
        self.exporter = CodexTranscriptExporter() if CodexTranscriptExporter else None

        # Initialize transcript manager if available
        self.manager = TranscriptManager() if TranscriptManager else None

        # Register tools
        self._register_tools()

    def _register_tools(self):
        """Register all MCP tools"""

        @self.mcp.tool()
        async def save_current_transcript(
            session_id: str | None = None, format: str = "both", output_dir: str | None = None
        ) -> dict[str, Any]:
            """Export current Codex session transcript (replaces PreCompact hook)

            Args:
                session_id: Optional session ID to export (detects current if not provided)
                format: Export format - "standard", "extended", "both", or "compact"
                output_dir: Optional output directory (defaults to .codex/transcripts/)

            Returns:
                Export result with path and metadata
            """
            try:
                if not self.exporter:
                    return error_response("Transcript exporter not available")

                # Determine session ID
                if not session_id:
                    session_id = self.get_current_codex_session()
                    if not session_id:
                        return error_response("No current session found")

                # Determine output directory
                if output_dir:
                    output_path = Path(output_dir)
                else:
                    output_path = Path(".codex/transcripts")

                # Export transcript
                result = self.exporter.export_codex_transcript(
                    session_id=session_id, output_dir=output_path, format_type=format, project_dir=self.project_root
                )

                if result:
                    # Get metadata
                    metadata = self.extract_session_metadata(Path("~/.codex/sessions") / session_id)
                    metadata.update(
                        {"export_path": str(result), "format": format, "exported_at": datetime.now().isoformat()}
                    )

                    self.logger.info(f"Exported transcript for session {session_id} to {result}")
                    return success_response({"session_id": session_id, "path": str(result)}, metadata)
                return error_response(f"Failed to export transcript for session {session_id}")

            except Exception as e:
                self.logger.exception("save_current_transcript failed", e)
                return error_response(f"Export failed: {str(e)}")

        @self.mcp.tool()
        async def save_project_transcripts(
            project_dir: str, format: str = "standard", incremental: bool = True
        ) -> dict[str, Any]:
            """Export all transcripts for current project

            Args:
                project_dir: Project directory to filter sessions
                format: Export format - "standard" or "compact"
                incremental: Skip already-exported sessions

            Returns:
                List of exported sessions with metadata
            """
            try:
                if not load_history or not process_session:
                    return error_response("Codex transcripts builder not available")

                project_path = Path(project_dir)
                if not project_path.exists():
                    return error_response(f"Project directory not found: {project_dir}")

                # Load sessions and filter by project
                sessions_map = load_history(HISTORY_DEFAULT, skip_errors=True, verbose=False)
                project_sessions = self.get_project_sessions(project_path)

                exported = []
                for session_id in project_sessions:
                    if session_id not in sessions_map:
                        continue

                    # Check if already exported (incremental mode)
                    if incremental:
                        output_dir = Path("~/.codex/transcripts").expanduser()
                        session_dir = output_dir / f"{session_id}_transcript.md"
                        if session_dir.exists():
                            continue

                    # Export session
                    try:
                        process_session(
                            session_id=session_id,
                            history_entries=sessions_map[session_id],
                            sessions_root=SESSIONS_DEFAULT,
                            output_base=output_dir,
                            tz_name="America/Los_Angeles",
                            cwd_separator="~",
                        )
                        metadata = self.extract_session_metadata(Path("~/.codex/sessions") / session_id)
                        exported.append({"session_id": session_id, "path": str(session_dir), "metadata": metadata})
                    except Exception as e:
                        self.logger.warning(f"Failed to export session {session_id}: {e}")

                self.logger.info(f"Exported {len(exported)} project transcripts")
                return success_response({"exported": exported}, {"total_exported": len(exported)})

            except Exception as e:
                self.logger.exception("save_project_transcripts failed", e)
                return error_response(f"Batch export failed: {str(e)}")

        @self.mcp.tool()
        async def list_available_sessions(project_only: bool = False, limit: int = 10) -> dict[str, Any]:
            """List Codex sessions available for export

            Args:
                project_only: Filter to current project directory only
                limit: Maximum number of sessions to return

            Returns:
                List of sessions with metadata
            """
            try:
                sessions_root = Path("~/.codex/sessions").expanduser()
                if not sessions_root.exists():
                    return success_response([], {"message": "No sessions directory found"})

                sessions = []
                current_project = self.project_root if project_only else None

                for session_dir in sorted(sessions_root.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
                    if session_dir.is_dir():
                        metadata = self.extract_session_metadata(session_dir)

                        # Filter by project if requested
                        if project_only and current_project:
                            session_cwd = metadata.get("cwd")
                            if session_cwd and Path(session_cwd).resolve() != current_project.resolve():
                                continue

                        sessions.append(metadata)

                        if len(sessions) >= limit:
                            break

                self.logger.info(f"Listed {len(sessions)} available sessions")
                return success_response(sessions, {"total": len(sessions), "limit": limit})

            except Exception as e:
                self.logger.exception("list_available_sessions failed", e)
                return error_response(f"Session listing failed: {str(e)}")

        @self.mcp.tool()
        async def convert_transcript_format(
            session_id: str, from_format: str, to_format: str, output_path: str | None = None
        ) -> dict[str, Any]:
            """Convert between Claude Code and Codex transcript formats

            Args:
                session_id: Session ID to convert
                from_format: Source format ("claude" or "codex")
                to_format: Target format ("claude" or "codex")
                output_path: Optional output path

            Returns:
                Conversion result with output path
            """
            try:
                if not self.manager:
                    return error_response("Transcript manager not available")

                # Perform conversion
                success = self.manager.convert_format(
                    session_id=session_id,
                    from_backend=from_format,
                    to_backend=to_format,
                    output_path=Path(output_path) if output_path else None,
                )

                if success:
                    output_file = output_path or f"converted_{session_id}.{'txt' if to_format == 'claude' else 'md'}"
                    self.logger.info(f"Converted session {session_id} from {from_format} to {to_format}")
                    return success_response(
                        {
                            "session_id": session_id,
                            "from_format": from_format,
                            "to_format": to_format,
                            "output_path": output_file,
                        }
                    )
                return error_response(f"Conversion failed for session {session_id}")

            except Exception as e:
                self.logger.exception("convert_transcript_format failed", e)
                return error_response(f"Conversion failed: {str(e)}")

    def get_current_codex_session(self) -> str | None:
        """Detect the most recent/active Codex session"""
        try:
            if self.exporter:
                return self.exporter.get_current_codex_session()
            return None
        except Exception as e:
            self.logger.warning(f"Failed to get current session: {e}")
            return None

    def get_project_sessions(self, project_dir: Path) -> list[str]:
        """Filter Codex sessions by project directory"""
        try:
            if self.exporter:
                return self.exporter.get_project_sessions(project_dir)
            return []
        except Exception as e:
            self.logger.warning(f"Failed to get project sessions: {e}")
            return []

    def extract_session_metadata(self, session_dir: Path) -> dict[str, Any]:
        """Parse session metadata from directory structure"""
        metadata = {"session_id": session_dir.name, "path": str(session_dir)}

        try:
            # Try to load meta.json
            meta_file = session_dir / "meta.json"
            if meta_file.exists():
                with open(meta_file) as f:
                    meta = json.load(f)
                    metadata.update({"started_at": meta.get("started_at"), "cwd": meta.get("cwd")})

            # Count messages from history.jsonl if available
            history_file = session_dir / "history.jsonl"
            if history_file.exists():
                message_count = 0
                with open(history_file) as f:
                    for line in f:
                        if line.strip():
                            message_count += 1
                metadata["message_count"] = str(message_count)

            # Get directory modification time as fallback start time
            if not metadata.get("started_at"):
                mtime = datetime.fromtimestamp(session_dir.stat().st_mtime, tz=UTC)
                metadata["started_at"] = mtime.isoformat()

        except Exception as e:
            self.logger.warning(f"Failed to extract metadata for {session_dir}: {e}")

        return metadata


def main():
    """Main entry point for the transcript saver MCP server"""
    try:
        server = TranscriptSaverServer()
        server.run()
    except Exception as e:
        print(f"Failed to start transcript saver server: {e}", file=sys.stderr)
        exit(1)


if __name__ == "__main__":
    main()
