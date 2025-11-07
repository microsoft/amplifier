"""Token usage tracking and estimation for Claude Code sessions."""

import json
import logging
from pathlib import Path
from typing import Any

from .models import TokenUsageSnapshot

logger = logging.getLogger(__name__)


class TokenTracker:
    """Tracks and estimates token usage for Claude Code sessions.

    Provides conservative token estimation using word counts and multipliers
    to avoid false positives when monitoring token limits.
    """

    TOKEN_MULTIPLIER = 1.3  # Conservative multiplier for word-to-token conversion

    def estimate_from_session_log(self, session_log_path: Path) -> TokenUsageSnapshot:
        """Estimate token usage from a session log file.

        Args:
            session_log_path: Path to the session log file

        Returns:
            TokenUsageSnapshot with estimated usage

        Raises:
            FileNotFoundError: If log file doesn't exist
            json.JSONDecodeError: If log file is corrupted
        """
        try:
            with open(session_log_path, encoding="utf-8") as f:
                content = f.read()

            # Simple word-based estimation
            word_count = len(content.split())
            estimated_tokens = int(word_count * self.TOKEN_MULTIPLIER)

            # Assume 100k token limit for calculation
            usage_pct = min((estimated_tokens / 100000) * 100, 100.0)

            return TokenUsageSnapshot(estimated_tokens=estimated_tokens, usage_pct=usage_pct, source="session_log")

        except FileNotFoundError:
            logger.warning(f"Session log file not found: {session_log_path}")
            return TokenUsageSnapshot(estimated_tokens=0, usage_pct=0.0, source="session_log_missing")
        except Exception as e:
            logger.error(f"Error reading session log {session_log_path}: {e}")
            return TokenUsageSnapshot(estimated_tokens=0, usage_pct=0.0, source="session_log_error")

    def estimate_from_transcript(self, transcript_path: Path) -> TokenUsageSnapshot:
        """Estimate token usage from a Claude Code JSONL transcript.

        Args:
            transcript_path: Path to the JSONL transcript file

        Returns:
            TokenUsageSnapshot with estimated usage
        """
        total_tokens = 0

        try:
            with open(transcript_path, encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        entry = json.loads(line)
                        tokens = self._count_tokens_in_entry(entry)
                        total_tokens += tokens
                    except json.JSONDecodeError as e:
                        logger.warning(f"Skipping corrupted line {line_num} in {transcript_path}: {e}")
                        continue

            # Assume 100k token limit for calculation
            usage_pct = min((total_tokens / 100000) * 100, 100.0)

            return TokenUsageSnapshot(estimated_tokens=total_tokens, usage_pct=usage_pct, source="transcript")

        except FileNotFoundError:
            logger.warning(f"Transcript file not found: {transcript_path}")
            return TokenUsageSnapshot(estimated_tokens=0, usage_pct=0.0, source="transcript_missing")
        except Exception as e:
            logger.error(f"Error reading transcript {transcript_path}: {e}")
            return TokenUsageSnapshot(estimated_tokens=0, usage_pct=0.0, source="transcript_error")

    def _count_tokens_in_entry(self, entry: dict[str, Any]) -> int:
        """Count tokens in a single transcript entry.

        Args:
            entry: JSON entry from transcript

        Returns:
            Estimated token count for this entry
        """
        token_count = 0

        # Count tokens in message content
        if "message" in entry:
            message = entry["message"]
            if isinstance(message, dict) and "content" in message:
                content = message["content"]
                if isinstance(content, str):
                    # Simple word-based counting
                    word_count = len(content.split())
                    token_count += int(word_count * self.TOKEN_MULTIPLIER)
                elif isinstance(content, list):
                    # Handle list of content blocks (common in Claude responses)
                    for block in content:
                        if isinstance(block, dict) and "text" in block:
                            word_count = len(block["text"].split())
                            token_count += int(word_count * self.TOKEN_MULTIPLIER)

        return token_count

    def get_current_usage(self, workspace_id: str) -> TokenUsageSnapshot:
        """Get current token usage for a workspace.

        Determines workspace type and calls appropriate estimation method.

        Args:
            workspace_id: Identifier for the workspace

        Returns:
            Current token usage snapshot
        """
        # Try Claude Code transcript first (preferred)
        transcript_path = Path.home() / ".config/claude/projects" / workspace_id / f"{workspace_id}.jsonl"
        if transcript_path.exists():
            return self.estimate_from_transcript(transcript_path)

        # Fall back to session log
        session_log_path = Path(".codex/workspaces") / workspace_id / "session.log"
        if session_log_path.exists():
            return self.estimate_from_session_log(session_log_path)

        # No session files found
        logger.warning(f"No session files found for workspace {workspace_id}")
        return TokenUsageSnapshot(estimated_tokens=0, usage_pct=0.0, source="no_files")

    def should_terminate(self, usage: TokenUsageSnapshot, config: "MonitorConfig") -> tuple[bool, str]:
        """Check if session should terminate based on token usage.

        Args:
            usage: Current token usage snapshot
            config: Monitor configuration

        Returns:
            Tuple of (should_terminate, reason)
        """
        if usage.usage_pct >= config.token_critical_threshold:
            return (
                True,
                f"Token usage {usage.usage_pct:.1f}% exceeds critical threshold {config.token_critical_threshold}%",
            )
        if usage.usage_pct >= config.token_warning_threshold:
            return (
                False,
                f"Token usage {usage.usage_pct:.1f}% exceeds warning threshold {config.token_warning_threshold}%",
            )
        return False, f"Token usage {usage.usage_pct:.1f}% is within safe limits"
