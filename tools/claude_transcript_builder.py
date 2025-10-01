#!/usr/bin/env python3
"""
Claude Code Session Transcript Builder

This tool builds comprehensive transcripts from Claude Code session JSONL files.
It reconstructs the conversation DAG, handles branches and sidechains, and
produces readable markdown transcripts.
"""

import argparse
import json
import logging
import shutil
import sys
from datetime import UTC
from datetime import datetime
from pathlib import Path

from compact_tracer import trace_lineage
from dag_loader import DAGLoader
from dag_navigator import DAGNavigator
from subagent_mapper import SubagentMapper
from transcript_formatter import TranscriptFormatter

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def find_claude_projects_dir():
    """Find the Claude Code projects directory."""
    claude_dir = Path.home() / ".claude" / "projects"
    if not claude_dir.exists():
        return None
    return claude_dir


def list_projects(projects_dir: Path):
    """List all available projects."""
    projects = []
    for project_dir in projects_dir.iterdir():
        if project_dir.is_dir() and project_dir.name.startswith("-"):
            # Extract readable project name
            project_name = project_dir.name[1:].replace("-", "/")
            projects.append((project_dir.name, project_name))
    return sorted(projects, key=lambda x: x[1])


def list_sessions(project_dir: Path):
    """List all sessions in a project with their modification times."""
    sessions = []
    for session_file in project_dir.glob("*.jsonl"):
        mtime = session_file.stat().st_mtime
        sessions.append((session_file, mtime))
    return sorted(sessions, key=lambda x: x[1], reverse=True)


def find_default_session(projects_dir: Path):
    """Find the default session using context-aware selection.

    First tries to find a session from the current working directory's project.
    Falls back to the most recent session across all projects if no match.
    """
    import os

    # Get current working directory
    cwd = os.getcwd()

    # Convert CWD to Claude Code project directory format
    cwd_encoded = cwd.replace("/", "-").replace(".", "-")
    if not cwd_encoded.startswith("-"):
        cwd_encoded = "-" + cwd_encoded

    # Try to find the best matching project
    best_match = None
    best_match_score = 0

    for project_dir in projects_dir.iterdir():
        if project_dir.is_dir() and project_dir.name.startswith("-") and cwd_encoded.startswith(project_dir.name):
            # Score based on the length of the match (longer = more specific)
            score = len(project_dir.name)
            if score > best_match_score:
                best_match = project_dir
                best_match_score = score

    # If we found a matching project, use its most recent session
    if best_match:
        sessions = list_sessions(best_match)
        if sessions:
            session_file = sessions[0][0]  # Most recent session
            display_path = best_match.name[1:].replace("-", "/")
            if not display_path.startswith("/"):
                display_path = "/" + display_path
            logger.info(f"📍 Using session from current project: {display_path}")
            return session_file

    # Fallback: find most recent session across all projects
    most_recent = None
    most_recent_time = 0

    for project_dir in projects_dir.iterdir():
        if project_dir.is_dir():
            for session_file in project_dir.glob("*.jsonl"):
                mtime = session_file.stat().st_mtime
                if mtime > most_recent_time:
                    most_recent = session_file
                    most_recent_time = mtime

    return most_recent


def process_session(
    session_file: Path, output_dir: Path, include_system: bool = False, subagent_mapper: SubagentMapper | None = None
):
    """Process a single session file (with compact lineage) and generate transcripts.

    Args:
        session_file: Path to the JSONL session file
        output_dir: Directory to write output files
        include_system: Whether to include system messages
        subagent_mapper: Optional SubagentMapper for legacy session detection
    """
    logger.info(f"📄 Processing: {session_file}")

    # Extract project info
    project_dir_name = session_file.parent.name
    project_name = project_dir_name[1:].replace("-", "/") if project_dir_name.startswith("-") else project_dir_name
    logger.info(f"📂 Project: {project_name}")

    # Trace compact lineage
    project_dir = session_file.parent
    session_chain = trace_lineage(session_file, project_dir)

    if len(session_chain) > 1:
        logger.info(f"🔗 Found compact lineage: {len(session_chain)} sessions")
        for i, path in enumerate(session_chain):
            logger.info(f"   {i + 1}. {path.name}")

    # Calculate total size
    total_size = sum(p.stat().st_size for p in session_chain)
    logger.info(f"📏 Total size: {total_size:,} bytes")

    # Load the session data (with lineage if applicable)
    logger.info("")
    logger.info("Loading session data...")
    loader = DAGLoader(subagent_mapper=subagent_mapper)

    if len(session_chain) > 1:
        session_data = loader.load_session_chain(session_chain)
    else:
        session_data = loader.load_file(session_file)

    # Navigate the DAG to build conversation tree
    logger.info("Building conversation tree...")
    navigator = DAGNavigator(session_data)
    tree = navigator.build_conversation_tree()

    # Create formatter
    formatter = TranscriptFormatter(session_data, tree)

    # Prepare output directory
    session_id = session_file.stem
    session_output_dir = output_dir / project_dir_name / session_id
    session_output_dir.mkdir(parents=True, exist_ok=True)

    # Generate simple transcript
    logger.info("")
    logger.info("Generating transcripts...")
    simple_transcript = formatter.format_simple_transcript(include_system=include_system)
    simple_file = session_output_dir / "transcript.md"
    simple_file.write_text(simple_transcript, encoding="utf-8")
    logger.info(f"✅ Simple transcript: {simple_file}")

    # Generate extended transcript
    extended_transcript = formatter.format_extended_transcript(include_system=True)
    extended_file = session_output_dir / "transcript_extended.md"
    extended_file.write_text(extended_transcript, encoding="utf-8")
    logger.info(f"✅ Extended transcript: {extended_file}")

    # Export sidechains if present
    if tree.count_sidechains() > 0:
        formatter.export_sidechains(session_output_dir)
        logger.info(f"✅ Exported {tree.count_sidechains()} sidechains")

    # Export v1.x legacy subagent sessions if present
    if subagent_mapper:
        session_id = session_file.stem
        v1_subagents = [
            (sid, info)
            for sid, info in subagent_mapper.get_subagent_sessions(session_id)
            if not sid.startswith(session_id + "_sidechain_")  # Exclude v2.x synthetic sidechains
        ]

        if v1_subagents:
            subagents_dir = session_output_dir / "subagents"
            subagents_dir.mkdir(parents=True, exist_ok=True)

            for subagent_id, subagent_info in v1_subagents:
                # Find the subagent session file
                subagent_file = project_dir / f"{subagent_id}.jsonl"
                if not subagent_file.exists():
                    logger.warning(f"Subagent session file not found: {subagent_file.name}")
                    continue

                # Load and process the subagent session
                subagent_loader = DAGLoader()
                subagent_data = subagent_loader.load_file(subagent_file)

                # Create navigator and tree
                subagent_navigator = DAGNavigator(subagent_data)
                subagent_tree = subagent_navigator.build_conversation_tree()

                # Create output directory
                agent_type = subagent_info.subagent_type
                subagent_output_dir = subagents_dir / f"{agent_type}_{subagent_id[:8]}"
                subagent_output_dir.mkdir(parents=True, exist_ok=True)

                # Generate transcript
                subagent_formatter = TranscriptFormatter(subagent_data, subagent_tree)
                subagent_transcript = subagent_formatter.format_simple_transcript(include_system=False)

                # Write transcript
                transcript_file = subagent_output_dir / "transcript.md"
                transcript_file.write_text(subagent_transcript, encoding="utf-8")

            logger.info(f"✅ Exported {len(v1_subagents)} v1.x subagent sessions")

    # Copy original session file(s)
    if len(session_chain) > 1:
        # Create a subdirectory for the session chain
        chain_dir = session_output_dir / "session_chain"
        chain_dir.mkdir(exist_ok=True)
        for i, chain_file in enumerate(session_chain):
            dest = chain_dir / f"{i + 1:02d}_{chain_file.name}"
            shutil.copy2(chain_file, dest)
        logger.info(f"✅ Session chain: {len(session_chain)} files copied to {chain_dir}")
    else:
        session_copy = session_output_dir / "session.jsonl"
        shutil.copy2(session_file, session_copy)
        logger.info(f"✅ Session copy: {session_copy}")

    # Generate summary
    logger.info("")
    logger.info("📊 Summary:")
    logger.info(f"  - Messages: {session_data.count_messages()}")
    logger.info(f"  - Branches: {tree.count_branches()}")
    if tree.count_sidechains() > 0:
        logger.info(f"  - Sidechains: {tree.count_sidechains()}")
    if len(session_chain) > 1:
        logger.info(f"  - Chain length: {len(session_chain)} sessions")

    return session_output_dir


def _should_process_at_root(session_file: Path, subagent_mapper: SubagentMapper | None = None) -> bool:
    """Determine if a session should be processed at root level.

    Legacy subagent sessions are skipped as they appear within parent transcripts.
    Only human-initiated sessions are processed at root.

    Args:
        session_file: Path to session JSONL file
        subagent_mapper: Optional SubagentMapper for legacy session detection

    Returns:
        True if session should be processed, False if it should be skipped
    """
    # Check if session is a legacy subagent using mapper
    if subagent_mapper:
        session_id = session_file.stem
        if subagent_mapper.is_subagent_session(session_id):
            return False

    # Still check for modern sidechain markers
    try:
        with open(session_file, encoding="utf-8") as f:
            # Find first user message (may not be on first line)
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Check if this is a user message
                if data.get("type") == "user":
                    # Skip sidechain messages - we only check the main conversation
                    if data.get("isSidechain", False):
                        continue

                    # Check for subagent delegation patterns in user-generated text only
                    # (NOT in tool results, which might contain other session transcripts)
                    content = data.get("message", {})
                    if isinstance(content, dict):
                        content_items = content.get("content", "")
                    else:
                        content_items = content

                    # Extract only text content, skip tool_result blocks
                    text_parts = []
                    if isinstance(content_items, list):
                        for item in content_items:
                            if isinstance(item, dict) and item.get("type") == "text":
                                text_parts.append(item.get("text", ""))
                    elif isinstance(content_items, str):
                        text_parts.append(content_items)

                    # Check patterns only in user text
                    content_text = " ".join(text_parts).lower()

                    patterns = [
                        "you are evaluating",
                        "you are analyzing",
                        "you are reviewing",
                        "your task is to",
                        "please evaluate",
                        "please analyze",
                        "please review",
                    ]

                    # Found first non-sidechain user message - check for delegation pattern
                    # Return True (process) if no patterns found, False (skip) if patterns found
                    return not any(pattern in content_text for pattern in patterns)

            # No user message found - process anyway
            return True

    except (OSError, json.JSONDecodeError) as e:
        logger.warning(f"Error checking session {session_file.name}: {e}")
        return True  # Process anyway, will handle error later


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Build transcripts from Claude Code session files",
        epilog="Examples:\n"
        "  %(prog)s                     # Process most recent session\n"
        "  %(prog)s --list              # List all projects and sessions\n"
        "  %(prog)s --project amplifier # Process most recent from project\n"
        "  %(prog)s --session UUID      # Process specific session\n"
        "  %(prog)s session.jsonl       # Process specific file\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("session_file", nargs="?", help="Path to specific session file (optional)")

    parser.add_argument("--project", "-p", help="Project name or directory (fuzzy match supported)")

    parser.add_argument("--list", "-l", action="store_true", help="List available projects and sessions")

    parser.add_argument("--session", "-s", help="Session UUID or filename within project")

    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("./output"),
        help="Output directory for transcripts (default: ./output)",
    )

    parser.add_argument("--include-system", action="store_true", help="Include system messages in simple transcript")

    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Configure debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Find Claude projects directory
    projects_dir = find_claude_projects_dir()
    if not projects_dir:
        logger.error("Error: Claude Code projects directory not found at ~/.claude/projects")
        sys.exit(1)

    # Handle --list flag
    if args.list:
        logger.info("📁 Available Claude Code Projects:\n")
        projects = list_projects(projects_dir)

        if not projects:
            logger.info("No projects found")
            return

        for dir_name, readable_name in projects:
            project_path = projects_dir / dir_name
            sessions = list_sessions(project_path)
            logger.info(f"  📂 {readable_name}")
            logger.info(f"     Directory: {dir_name}")

            if sessions:
                logger.info(f"     Sessions: {len(sessions)}")
                # Show most recent 3 sessions
                for session_file, mtime in sessions[:3]:
                    dt = datetime.fromtimestamp(mtime, tz=UTC)
                    size_kb = session_file.stat().st_size / 1024
                    logger.info(f"       - {session_file.name} ({dt.strftime('%Y-%m-%d %H:%M')}, {size_kb:.1f}KB)")
                if len(sessions) > 3:
                    logger.info(f"       ... and {len(sessions) - 3} more")
            else:
                logger.info("     No sessions")
            logger.info("")
        return

    # Determine which session file to process
    session_file = None

    if args.session_file:
        # Explicit file provided
        session_file = Path(args.session_file)
        if not session_file.exists():
            logger.error(f"Error: File not found: {session_file}")
            sys.exit(1)

    elif args.project or args.session:
        # Handle project and/or session specification
        matched_project = None

        if args.project:
            # Find project by name (fuzzy match)
            project_query = args.project.lower()

            for project_dir in projects_dir.iterdir():
                if project_dir.is_dir():
                    project_name = project_dir.name.lower()
                    if project_query in project_name:
                        matched_project = project_dir
                        break

            if not matched_project:
                logger.error(f"Error: No project found matching '{args.project}'")
                logger.info("\nAvailable projects:")
                for _, readable in list_projects(projects_dir)[:10]:
                    logger.info(f"  - {readable}")
                sys.exit(1)
        else:
            # No project specified but session requested - use current directory project
            import os

            cwd = os.getcwd()
            cwd_encoded = cwd.replace("/", "-").replace(".", "-")
            if not cwd_encoded.startswith("-"):
                cwd_encoded = "-" + cwd_encoded

            # Find best matching project
            best_match_score = 0
            for project_dir in projects_dir.iterdir():
                if (
                    project_dir.is_dir()
                    and project_dir.name.startswith("-")
                    and cwd_encoded.startswith(project_dir.name)
                ):
                    score = len(project_dir.name)
                    if score > best_match_score:
                        matched_project = project_dir
                        best_match_score = score

            if not matched_project:
                logger.error("Error: Could not find project for current directory to search for session")
                logger.info("Hint: Use --project to specify the project")
                sys.exit(1)

        # Find session within project
        if args.session:
            # Specific session requested
            for sf in matched_project.glob("*.jsonl"):
                if args.session in sf.name:
                    session_file = sf
                    break

            if not session_file:
                logger.error(f"Error: No session matching '{args.session}' in project")
                sessions = list_sessions(matched_project)
                if sessions:
                    logger.info("\nAvailable sessions:")
                    for sf, _ in sessions[:5]:
                        logger.info(f"  - {sf.name}")
                sys.exit(1)
        else:
            # Use most recent session from project
            sessions = list_sessions(matched_project)
            if not sessions:
                logger.error(f"Error: No sessions found in project {matched_project.name}")
                sys.exit(1)
            session_file = sessions[0][0]

    else:
        # Default: process ALL sessions from current project
        # Use context-aware project detection
        import os

        cwd = os.getcwd()
        cwd_encoded = cwd.replace("/", "-").replace(".", "-")
        if not cwd_encoded.startswith("-"):
            cwd_encoded = "-" + cwd_encoded

        # Find best matching project
        best_match = None
        best_match_score = 0
        for project_dir in projects_dir.iterdir():
            if project_dir.is_dir() and project_dir.name.startswith("-") and cwd_encoded.startswith(project_dir.name):
                score = len(project_dir.name)
                if score > best_match_score:
                    best_match = project_dir
                    best_match_score = score

        if not best_match:
            logger.error("Error: Could not find project matching current directory")
            logger.info("Hint: Use --list to see available projects or --project to specify one")
            sys.exit(1)

        # Get all sessions from matched project
        sessions = list_sessions(best_match)
        if not sessions:
            logger.error(f"Error: No sessions found in project {best_match.name}")
            sys.exit(1)

        display_path = best_match.name[1:].replace("-", "/")
        if not display_path.startswith("/"):
            display_path = "/" + display_path

        # Create SubagentMapper for all sessions in project
        from subagent_mapper import SubagentMapper

        session_paths = [session_file for session_file, _ in sessions]
        subagent_mapper = SubagentMapper(session_paths)
        subagent_mapper.build_mapping()

        # Filter sessions to only human-initiated ones
        human_sessions = []
        skipped_subagents = []

        for session_file, mtime in sessions:
            if _should_process_at_root(session_file, subagent_mapper):
                human_sessions.append((session_file, mtime))
            else:
                skipped_subagents.append(session_file.stem)

        if skipped_subagents:
            logger.info(f"📍 Processing human-initiated sessions from: {display_path}")
            logger.info(
                f"⏭️  Skipping {len(skipped_subagents)} legacy subagent sessions (they appear in parent transcripts)"
            )
            if args.debug:
                for session_id in skipped_subagents:
                    logger.debug(f"  Skipped: {session_id}")
        else:
            logger.info(f"📍 Processing ALL sessions from current project: {display_path}")

        logger.info(f"📊 Processing {len(human_sessions)} human-initiated sessions")
        logger.info("")

        # Process filtered sessions
        for i, (session_file, _) in enumerate(human_sessions, 1):
            logger.info(f"{'=' * 60}")
            logger.info(f"Session {i} of {len(human_sessions)}")
            logger.info(f"{'=' * 60}")

            try:
                output_dir = process_session(
                    session_file, args.output, include_system=args.include_system, subagent_mapper=subagent_mapper
                )
                logger.info(f"✨ Transcripts saved to: {output_dir}")
                logger.info("")
            except Exception as e:
                logger.error(f"❌ Error processing {session_file.name}: {e}")
                if args.debug:
                    import traceback

                    traceback.print_exc()
                logger.info("")

        logger.info(f"✅ Completed processing {len(human_sessions)} sessions")
        return

    # Process a single session (when explicitly specified via args)
    try:
        logger.info(f"{'=' * 60}")

        # Create SubagentMapper for the project
        from subagent_mapper import SubagentMapper

        project_dir = session_file.parent
        session_paths = list(project_dir.glob("*.jsonl"))
        subagent_mapper = SubagentMapper(session_paths) if session_paths else None
        if subagent_mapper:
            subagent_mapper.build_mapping()

        # Check if this is a legacy subagent
        if not _should_process_at_root(session_file, subagent_mapper):
            logger.warning("Note: This appears to be a legacy subagent session")
            logger.warning("It would normally be skipped and appear within its parent transcript")
            logger.warning("Processing anyway since explicitly requested...")

        logger.info("Processing single session")
        logger.info(f"{'=' * 60}")

        output_dir = process_session(
            session_file, args.output, include_system=args.include_system, subagent_mapper=subagent_mapper
        )
        logger.info("")
        logger.info(f"✨ All transcripts saved to: {output_dir}")

    except Exception as e:
        logger.error(f"\n❌ Error processing session: {e}")
        if args.debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
