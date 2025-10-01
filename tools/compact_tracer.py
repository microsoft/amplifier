#!/usr/bin/env python3
"""
Compact Tracer Module - Trace session lineage through compact boundaries.

This module reconstructs the full conversation history by following compact
operations backwards to the original session.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def trace_lineage(session_path: Path, project_dir: Path) -> list[Path]:
    """Trace compact lineage back to the original session.

    Returns list of session paths ordered from oldest to newest.
    Handles circular references and missing sessions gracefully.

    Args:
        session_path: Starting session file path
        project_dir: Directory containing all session files

    Returns:
        List of session paths from oldest to newest
    """
    chain = []
    visited = set()
    current = session_path

    logger.info(f"Starting lineage trace from {session_path.name}")

    while current:
        # Check for circular references
        if current.stem in visited:
            logger.warning(f"Circular reference detected at {current.stem}")
            break

        # Add to chain (prepend for chronological order)
        chain.insert(0, current)
        visited.add(current.stem)
        logger.debug(f"Added {current.name} to chain (position {len(chain)})")

        # Find compact boundary in current session
        prev_session_id = find_compact_boundary(current)

        if prev_session_id:
            prev_path = project_dir / f"{prev_session_id}.jsonl"
            if prev_path.exists():
                logger.debug(f"Following compact boundary to {prev_session_id}")
                current = prev_path
            else:
                logger.warning(f"Previous session not found: {prev_session_id}")
                break
        else:
            logger.debug(f"No compact boundary found in {current.name} - reached origin")
            current = None  # No more compacts, reached origin

    logger.info(f"Trace complete: found {len(chain)} sessions in chain")
    return chain


def find_compact_boundary(session_path: Path) -> str | None:
    """Find compact boundary in session and return previous session ID.

    Compact boundaries have:
    - type: "system"
    - subtype: "compact_boundary"
    - sessionId: <previous-session-id>

    Args:
        session_path: Path to session JSONL file

    Returns:
        Previous session ID if compact boundary found, None otherwise
    """
    try:
        with open(session_path, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line)

                    # Check for compact boundary
                    if data.get("type") == "system" and data.get("subtype") == "compact_boundary":
                        # Previous session ID is in sessionId field
                        prev_session_id = data.get("sessionId")
                        if prev_session_id:
                            logger.debug(f"Found compact boundary at line {line_num} pointing to {prev_session_id}")
                            return prev_session_id

                except json.JSONDecodeError:
                    # Skip unparseable lines gracefully
                    logger.debug(f"Skipping malformed JSON at line {line_num}")
                    continue

    except FileNotFoundError:
        logger.error(f"Session file not found: {session_path}")
    except Exception as e:
        logger.error(f"Error reading session file {session_path}: {e}")

    return None  # No compact boundary found


def get_session_metadata(session_path: Path) -> dict:
    """Extract useful metadata from a session file.

    Args:
        session_path: Path to session JSONL file

    Returns:
        Dictionary with session metadata:
        - session_id: UUID from filename
        - message_count: Total number of messages
        - file_size: Size in bytes
        - has_compact: Whether session contains a compact boundary
    """
    metadata = {"session_id": session_path.stem, "message_count": 0, "file_size": 0, "has_compact": False}

    try:
        # Get file size
        metadata["file_size"] = session_path.stat().st_size

        # Count messages and check for compact
        with open(session_path, encoding="utf-8") as f:
            for line in f:
                metadata["message_count"] += 1

                # Check if this is a compact boundary
                if not metadata["has_compact"]:
                    try:
                        data = json.loads(line)
                        if data.get("type") == "system" and data.get("subtype") == "compact_boundary":
                            metadata["has_compact"] = True
                    except json.JSONDecodeError:
                        pass

    except FileNotFoundError:
        logger.error(f"Session file not found: {session_path}")
    except Exception as e:
        logger.error(f"Error getting metadata for {session_path}: {e}")

    return metadata


# Example usage and testing
if __name__ == "__main__":
    # Set up logging for testing
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Test with a sample session
    import sys
    from pathlib import Path

    if len(sys.argv) > 1:
        session_file = Path(sys.argv[1])
        project_dir = session_file.parent
    else:
        # Default test case
        project_dir = Path.home() / ".claude/projects/-home-brkrabac-repos-amplifier"
        session_file = project_dir / "856e3139-2a1b-4eb2-927a-5181a0bbfa88.jsonl"

    if not session_file.exists():
        print(f"Session file not found: {session_file}")
        sys.exit(1)

    print(f"\nTracing lineage for: {session_file.name}")
    print("-" * 60)

    # Trace the lineage
    chain = trace_lineage(session_file, project_dir)

    print(f"\nFound {len(chain)} sessions in chain:")
    for i, session in enumerate(chain):
        metadata = get_session_metadata(session)
        print(f"  {i + 1}. {session.name}")
        print(f"     Messages: {metadata['message_count']}")
        print(f"     Size: {metadata['file_size']:,} bytes")
        print(f"     Has compact: {metadata['has_compact']}")
