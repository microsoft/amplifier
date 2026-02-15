#!/usr/bin/env python3
"""
Claude Code PreCompact hook - exports full conversation transcript before compaction.
Saves transcript to .data/transcripts/ for later retrieval via @mention.
Includes duplicate detection to avoid re-embedding already-loaded transcripts.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory for logger import
sys.path.insert(0, str(Path(__file__).parent))
from hook_logger import HookLogger

logger = HookLogger("precompact_export")


class GoldPrefixCompactor:
    """Implements Gemini-optimized caching strategy by isolating the Frozen Zone."""

    def __init__(self, hook_logger):
        self.logger = hook_logger
        self.frozen_token_limit = 150000  # tokens (approx 600k chars)

    def identify_frozen_zone(self, entries: list) -> list:
        """Identify original entries that should stay in the Frozen Zone."""
        frozen = []
        total_chars = 0

        for i, entry in enumerate(entries):
            # Extract content for token counting
            content = ""
            entry_type = entry.get("type")
            if entry_type == "system":
                content = str(entry.get("content", ""))
            elif "message" in entry:
                msg = entry["message"]
                if isinstance(msg.get("content"), list):
                    for item in msg["content"]:
                        if isinstance(item, dict) and item.get("type") == "text":
                            content += item.get("text", "")
                else:
                    content = str(msg.get("content", ""))

            total_chars += len(content)

            # Core Mandates, Identity, and Agent manifests are usually in the first 3-5 turns
            is_core = any(
                x in content
                for x in ["Core Mandates", "Identity", "AMPLIFIER-AGENTS", "CLAUDE.md"]
            )

            if i < 5 or (entry_type == "system" and (i < 8 or is_core)):
                frozen.append(entry)
            else:
                # If we've already found some entries and hit a non-system/non-core entry, stop
                break

            if total_chars > self.frozen_token_limit * 4:
                break

        return frozen

    def get_middle_history(self, entries: list, frozen_count: int) -> list:
        """Extract 'Middle History' for summarization (everything between Frozen and last 5 turns)."""
        if len(entries) <= frozen_count + 5:
            return []
        return entries[frozen_count:-5]

    def summarize_stable(self, entries: list) -> str:
        """Generate a stable summary block for the middle history."""
        if not entries:
            return ""

        # Extract tool usage for stability markers
        tool_counts = {}
        for entry in entries:
            msg = entry.get("message", {})
            content = msg.get("content", "")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_use":
                        name = item.get("name", "unknown")
                        tool_counts[name] = tool_counts.get(name, 0) + 1

        summary = [
            "### [GOLD PREFIX: STABLE PROGRESS SNAPSHOT]",
            f"Compacted History Range: {len(entries)} turns",
            f"Stability Key: {len(entries)}-{sum(tool_counts.values())}",  # Stable key for caching
            "",
            "#### Summary of Operations:",
        ]

        if tool_counts:
            summary.append("- **Tools Executed:**")
            for name, count in sorted(tool_counts.items()):
                summary.append(f"  - {name}: {count} times")

        summary.append("\n--- [END OF STABLE SNAPSHOT] ---")
        return "\n".join(summary)


def format_message(msg: dict) -> str:
    """Format a single message for text output, including all content types"""
    role = msg.get("role", "unknown").upper()
    content = msg.get("content", "")

    output_lines = [f"[{role}]:"]

    # Handle content that's a list (from structured messages)
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict):
                item_type = item.get("type", "unknown")

                if item_type == "text":
                    text = item.get("text", "")
                    if text:
                        output_lines.append(text)

                elif item_type == "thinking":
                    thinking_text = item.get("text", "")
                    if thinking_text:
                        output_lines.append("")
                        output_lines.append("[THINKING]:")
                        output_lines.append(thinking_text)
                        output_lines.append("[/THINKING]")
                        output_lines.append("")

                elif item_type == "tool_use":
                    tool_name = item.get("name", "unknown")
                    tool_id = item.get("id", "unknown")
                    tool_input = item.get("input", {})
                    output_lines.append("")
                    output_lines.append(
                        f"[TOOL USE: {tool_name}] (ID: {tool_id[:20]}...)"
                    )
                    # Format tool input as indented JSON
                    try:
                        input_str = json.dumps(tool_input, indent=2)
                        for line in input_str.split("\n"):
                            output_lines.append(f"  {line}")
                    except (TypeError, ValueError):
                        output_lines.append(f"  {tool_input}")
                    output_lines.append("")

                elif item_type == "tool_result":
                    tool_id = item.get("tool_use_id", "unknown")
                    is_error = item.get("is_error", False)
                    result_content = item.get("content", "")

                    output_lines.append("")
                    error_marker = " [ERROR]" if is_error else ""
                    output_lines.append(
                        f"[TOOL RESULT{error_marker}] (ID: {tool_id[:20]}...)"
                    )

                    # Limit tool result output to prevent massive dumps
                    if isinstance(result_content, str):
                        lines = result_content.split("\n")
                        if len(lines) > 100:
                            # Show first 50 and last 20 lines
                            for line in lines[:50]:
                                output_lines.append(f"  {line}")
                            output_lines.append(
                                f"  ... ({len(lines) - 70} lines omitted) ..."
                            )
                            for line in lines[-20:]:
                                output_lines.append(f"  {line}")
                        else:
                            for line in lines:
                                output_lines.append(f"  {line}")
                    else:
                        output_lines.append(f"  {result_content}")
                    output_lines.append("")

                else:
                    # Handle any other content types we might encounter
                    output_lines.append(f"[{item_type.upper()}]: {item}")

    elif isinstance(content, str):
        # Simple string content
        output_lines.append(content)
    else:
        # Fallback for unexpected content format
        output_lines.append(str(content))

    return "\n".join(output_lines) + "\n"


def extract_loaded_session_ids(entries: list) -> set[str]:
    """
    Extract session IDs of transcripts that were already loaded into this conversation.
    This prevents duplicate embedding of the same transcripts.

    Args:
        entries: List of (entry_type, message) tuples from the conversation

    Returns:
        Set of session IDs that have been loaded
    """
    loaded_sessions = set()

    for entry_type, msg in entries:
        if entry_type == "assistant" and isinstance(msg.get("content"), str | list):
            content = msg.get("content", "")

            # Convert list content to string for searching
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                content = "\n".join(text_parts)

            # Look for patterns indicating a transcript was loaded
            # Pattern 1: "CONVERSATION SEGMENT" headers with session IDs
            session_pattern = r"Session ID:\s*([a-f0-9-]+)"
            for match in re.finditer(session_pattern, content):
                session_id = match.group(1)
                if len(session_id) > 20:  # Valid session IDs are UUID-like
                    loaded_sessions.add(session_id)
                    logger.info(f"Found previously loaded session: {session_id[:8]}...")

            # Pattern 2: File references to transcript files
            file_pattern = r"compact_\d+_\d+_([a-f0-9-]+)\.txt"
            for match in re.finditer(file_pattern, content):
                session_id = match.group(1)
                if len(session_id) > 20:
                    loaded_sessions.add(session_id)
                    logger.info(
                        f"Found referenced transcript file for session: {session_id[:8]}..."
                    )

    return loaded_sessions


def export_transcript(
    transcript_path: str,
    trigger: str,
    session_id: str,
    custom_instructions: str = "",
    full_entries: list | None = None,
) -> str:
    """
    Export the conversation transcript to a text file.
    Includes duplicate detection to avoid re-embedding already-loaded transcripts.

    Args:
        transcript_path: Path to the JSONL transcript file
        trigger: "manual" or "auto" - how compact was triggered
        session_id: The session ID for the conversation
        custom_instructions: Any custom instructions provided with compact
        full_entries: Optional list of full transcript entries already parsed

    Returns:
        Path to the exported transcript file
    """
    try:
        # Create storage directory
        storage_dir = Path(__file__).parent.parent.parent / ".data" / "transcripts"
        storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Storage directory: {storage_dir}")

        # Generate filename with timestamp and session ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"compact_{timestamp}_{session_id}.txt"
        output_path = storage_dir / output_filename

        # Read the JSONL transcript if not provided
        if full_entries is None:
            transcript_file = Path(transcript_path)
            if not transcript_file.exists():
                logger.error(f"Transcript file not found: {transcript_file}")
                return ""

            full_entries = []
            with open(transcript_file, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            full_entries.append(json.loads(line))
                        except:
                            continue

        logger.info(f"Processing {len(full_entries)} entries")

        # Parse JSONL and extract all conversation entries for formatting
        entries = []
        for entry in full_entries:
            entry_type = entry.get("type")

            # Include all entry types for complete transcript
            if entry_type == "system":
                # System entries provide important context
                subtype = entry.get("subtype", "")
                content = entry.get("content", "")
                timestamp = entry.get("timestamp", "")

                # Create a pseudo-message for system entries
                system_msg = {
                    "role": "system",
                    "content": f"[{subtype}] {content}",
                    "timestamp": timestamp,
                }
                entries.append(("system", system_msg))

            elif entry_type in ["user", "assistant"]:
                # Extract the actual message
                if "message" in entry and isinstance(entry["message"], dict):
                    msg = entry["message"]
                    entries.append((entry_type, msg))

            elif entry_type in ["summary", "meta"]:
                # Include summary/meta for context
                content = entry.get("content", "")
                if content:
                    meta_msg = {"role": entry_type, "content": content}
                    entries.append((entry_type, meta_msg))

        logger.info(f"Extracted {len(entries)} total entries from conversation")

        # Check for already-loaded transcripts to avoid duplication
        loaded_sessions = extract_loaded_session_ids(entries)
        if loaded_sessions:
            logger.info(
                f"Detected {len(loaded_sessions)} previously loaded transcript(s)"
            )
            logger.info("These will be marked in the export to avoid re-embedding")

        # Write formatted transcript to text file
        with open(output_path, "w", encoding="utf-8") as f:
            # Write header
            f.write("=" * 80 + "\n")
            f.write("CLAUDE CODE CONVERSATION TRANSCRIPT\n")
            f.write(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Session ID: {session_id}\n")
            f.write(f"Compact Trigger: {trigger}\n")
            if custom_instructions:
                f.write(f"Custom Instructions: {custom_instructions}\n")
            f.write(f"Total Entries: {len(entries)}\n")

            # Note if there are already-loaded transcripts
            if loaded_sessions:
                f.write(f"Previously Loaded Sessions: {len(loaded_sessions)}\n")
                for loaded_id in sorted(loaded_sessions):
                    f.write(f"  - {loaded_id}\n")
                f.write(
                    "Note: Content from these sessions may appear embedded in the conversation.\n"
                )

            # Gold Prefix Optimization Info
            compactor = GoldPrefixCompactor(logger)
            frozen = compactor.identify_frozen_zone(full_entries)
            middle = compactor.get_middle_history(full_entries, len(frozen))
            if middle:
                f.write(f"Gold Prefix Status: OPTIMIZED\n")
                f.write(f"Frozen Zone: {len(frozen)} turns preserved\n")
                f.write(f"Middle History: {len(middle)} turns summarized\n")
                f.write(
                    f"Recent turns: {len(full_entries) - len(frozen) - len(middle)} turns active\n"
                )

            f.write("=" * 80 + "\n\n")

            # Write all entries with proper formatting
            message_num = 0
            in_loaded_transcript = False

            for entry_type, msg in entries:
                content_str = ""
                if isinstance(msg.get("content"), str):
                    content_str = msg.get("content", "")
                elif isinstance(msg.get("content"), list):
                    # Extract text from structured content
                    for item in msg.get("content", []):
                        if isinstance(item, dict) and item.get("type") == "text":
                            content_str += item.get("text", "")

                # Check if we're entering or leaving a loaded transcript section
                if (
                    "CONVERSATION SEGMENT" in content_str
                    or "CLAUDE CODE CONVERSATION TRANSCRIPT" in content_str
                ):
                    in_loaded_transcript = True
                    f.write("\n--- [BEGIN EMBEDDED TRANSCRIPT] ---\n")
                elif in_loaded_transcript and "END OF TRANSCRIPT" in content_str:
                    in_loaded_transcript = False
                    f.write("--- [END EMBEDDED TRANSCRIPT] ---\n\n")

                # Write the message with appropriate formatting
                if entry_type in ["user", "assistant"]:
                    message_num += 1
                    marker = (
                        " [FROM EMBEDDED TRANSCRIPT]" if in_loaded_transcript else ""
                    )
                    f.write(f"\n--- Message {message_num} ({entry_type}){marker} ---\n")
                    f.write(format_message(msg))
                elif entry_type == "system":
                    f.write("\n--- System Event ---\n")
                    f.write(f"[SYSTEM]: {msg.get('content', '')}\n")
                    if msg.get("timestamp"):
                        f.write(f"Timestamp: {msg['timestamp']}\n")
                else:
                    # Handle meta/summary entries
                    f.write(f"\n--- {entry_type.title()} ---\n")
                    f.write(f"[{entry_type.upper()}]: {msg.get('content', '')}\n")
                f.write("\n")

            # Write footer
            f.write("=" * 80 + "\n")
            f.write("END OF TRANSCRIPT\n")
            f.write(f"File: {output_path.name}\n")
            f.write("=" * 80 + "\n")

        logger.info(f"Transcript exported to: {output_path}")
        return str(output_path)

    except Exception as e:
        logger.exception("Error exporting transcript", e)
        return ""


def push_memory_notes():
    """Push git notes to origin before compaction."""
    import os

    superpowers_dir = os.path.expanduser(
        "~/.claude/plugins/cache/superpowers-marketplace/superpowers"
    )
    if not os.path.isdir(superpowers_dir):
        # Fallback to local Przemek installation
        superpowers_dir = "C:/Przemek/superpowers"

    if not os.path.isdir(superpowers_dir):
        logger.info("Superpowers directory not found, skipping memory push")
        return

    git_dir = os.path.join(superpowers_dir, ".git")
    if not os.path.isdir(git_dir):
        logger.info("Not a git repo, skipping memory push")
        return

    try:
        import subprocess

        result = subprocess.run(
            ["git", "push", "origin", "refs/notes/superpowers"],
            cwd=superpowers_dir,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            logger.info(f"Git notes pushed to origin: {result.stderr.strip() or 'ok'}")
        else:
            logger.warning(
                f"Git notes push failed (non-critical): {result.stderr.strip()}"
            )
    except Exception as e:
        logger.warning(f"Git notes push error (non-critical): {e}")


def main():
    """Main hook entry point"""
    try:
        logger.info("PreCompact export hook started")

        # Read input from stdin
        raw_input = sys.stdin.read()
        input_data = json.loads(raw_input)

        # Extract relevant fields
        hook_event = input_data.get("hook_event_name", "")
        if hook_event != "PreCompact":
            logger.warning(f"Unexpected hook event: {hook_event}")

        transcript_path = input_data.get("transcript_path", "")
        trigger = input_data.get("trigger", "unknown")
        session_id = input_data.get("session_id", "unknown")
        custom_instructions = input_data.get("custom_instructions", "")

        logger.info(f"Compact trigger: {trigger}")
        logger.info(f"Session ID: {session_id}")
        if custom_instructions:
            logger.info(f"Custom instructions: {custom_instructions[:100]}...")

        # Push git-notes memory to origin before compaction
        try:
            push_memory_notes()
        except Exception as e:
            logger.warning(f"Memory push failed (non-critical): {e}")

        # Export the transcript
        exported_path = ""
        metadata = {
            "transcript_exported": False,
            "gold_prefix_optimized": False,
            "trigger": trigger,
        }
        full_entries = None

        if transcript_path:
            # First, perform Gold Prefix optimization analysis

            try:
                # Read transcript entries for analysis
                full_entries = []
                with open(transcript_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            try:
                                full_entries.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue

                compactor = GoldPrefixCompactor(logger)
                frozen = compactor.identify_frozen_zone(full_entries)
                middle = compactor.get_middle_history(full_entries, len(frozen))

                if middle:
                    summary = compactor.summarize_stable(middle)
                    logger.info(
                        f"Gold Prefix Analysis: {len(frozen)} frozen turns, {len(middle)} turns to summarize"
                    )
                    metadata["gold_prefix_optimized"] = True
                    metadata["frozen_turns"] = len(frozen)
                    metadata["summarized_turns"] = len(middle)
                    metadata["stable_summary"] = summary
            except Exception as e:
                logger.error(f"Gold Prefix optimization error: {e}")

            # Continue with existing export logic
            exported_path = export_transcript(
                transcript_path, trigger, session_id, custom_instructions, full_entries
            )

            if exported_path:
                logger.info(f"Successfully exported transcript to: {exported_path}")
                metadata["transcript_exported"] = True
                metadata["export_path"] = exported_path
            else:
                logger.error("Failed to export transcript")
        else:
            logger.error("No transcript_path provided in hook input")

        # Return success (non-blocking) with metadata
        output = {
            "continue": True,
            "suppressOutput": True,
            "metadata": metadata,
        }

        # Add a system message to notify about the export
        if exported_path:
            # Extract just the filename for the message
            filename = Path(exported_path).name
            output["systemMessage"] = (
                f"Transcript exported to .data/transcripts/{filename}"
            )

        json.dump(output, sys.stdout)
        logger.info("PreCompact export hook completed")

    except Exception as e:
        logger.exception("Error in PreCompact export hook", e)
        # Return non-blocking error - we don't want to prevent compaction
        json.dump(
            {"continue": True, "suppressOutput": True, "metadata": {"error": str(e)}},
            sys.stdout,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
