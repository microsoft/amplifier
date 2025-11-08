#!/usr/bin/env python3
"""
Codex transcripts generator.

Reads ~/.codex/history.jsonl and corresponding rollout session files to produce
per-session transcripts under an output directory. The output directory will
contain one subdirectory per session, named with the session start timestamp,
the session's cwd (if available), and a short form of the session ID. Each
session directory will contain:
- history.jsonl: The history entries for the session
- transcript.md: A markdown transcript of the conversation
- transcript_extended.md: A more detailed markdown transcript with all events

NOTE: This processes ALL sessions found in the history file, not just ones created from this project directory.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import Any

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

HISTORY_DEFAULT = Path("~/.codex/history.jsonl").expanduser()
SESSIONS_DEFAULT = Path("~/.codex/sessions").expanduser()
OUTPUT_DEFAULT = Path("~/.codex/transcripts").expanduser()
TIMEZONE_DEFAULT = "America/Los_Angeles"


@dataclass(frozen=True)
class HistoryEntry:
    session_id: str
    ts: int
    text: str

    @classmethod
    def from_json(cls, payload: dict[str, Any]) -> HistoryEntry:
        # Validate required fields
        if "session_id" not in payload:
            raise ValueError("Missing required field: session_id")
        if "ts" not in payload:
            raise ValueError("Missing required field: ts")

        try:
            session_id = str(payload["session_id"])
            ts = int(payload["ts"])
            text = str(payload.get("text", ""))

            # Basic validation
            if not session_id:
                raise ValueError("session_id cannot be empty")
            if ts <= 0:
                raise ValueError(f"Invalid timestamp: {ts}")

            return cls(session_id=session_id, ts=ts, text=text)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Failed to parse HistoryEntry: {e}") from e


@dataclass
class SessionMeta:
    session_id: str
    started_at: datetime
    cwd: str | None


@dataclass
class TimelineEvent:
    timestamp: datetime
    order: int
    source: str
    kind: str
    role: str | None
    text: str
    content: Any | None
    raw: Any
    tool_name: str | None = None
    tool_args: Any | None = None
    tool_result: Any | None = None


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Codex session transcripts")
    parser.add_argument(
        "--history",
        type=Path,
        default=HISTORY_DEFAULT,
        help="Path to history.jsonl file",
    )
    parser.add_argument(
        "--sessions-root",
        type=Path,
        default=SESSIONS_DEFAULT,
        help="Path to sessions directory",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DEFAULT,
        help="Directory where transcripts will be written",
    )
    parser.add_argument(
        "--timezone",
        default=TIMEZONE_DEFAULT,
        help="Timezone identifier for local timestamps (default: America/Los_Angeles)",
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        help="Filter sessions by project directory (matches session cwd)",
    )
    parser.add_argument(
        "--session-id",
        help="Process only a specific session ID (full or short form)",
    )
    parser.add_argument(
        "--skip-errors",
        action="store_true",
        help="Continue processing when individual sessions fail",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Skip sessions that already have output directories",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reprocessing even in incremental mode",
    )
    parser.add_argument(
        "--output-format",
        choices=["standard", "compact", "both"],
        default="standard",
        help="Output format: standard (conversation + extended), compact (single file), or both.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose progress reporting",
    )
    parser.add_argument(
        "--cwd-separator",
        default="~",
        help="Character to join path components for cwd metadata (ASCII only).",
    )
    return parser.parse_args(argv)


def filter_sessions_by_project(
    sessions: dict[str, list[HistoryEntry]],
    project_dir: Path,
    sessions_root: Path,
    output_dir: Path | None = None,
) -> dict[str, list[HistoryEntry]]:
    """Filter sessions by project directory, matching session cwd against project_dir."""
    filtered_sessions = {}
    project_str = str(project_dir.resolve())

    for session_id, entries in sessions.items():
        session_dir = sessions_root / session_id
        meta: SessionMeta | None = None
        if session_dir.exists():
            try:
                meta = load_session_meta(session_dir)
            except Exception:
                # Skip sessions with invalid metadata
                continue
        if (meta is None or not meta.cwd) and output_dir and output_dir.exists():
            meta = _load_meta_from_output(session_id, output_dir) or meta

        if meta and meta.cwd:
            try:
                if Path(meta.cwd).resolve() == Path(project_str):
                    filtered_sessions[session_id] = entries
            except OSError:
                # Ignore invalid paths in metadata
                continue

    return filtered_sessions


def _normalize_session_id(value: str) -> str:
    return value.replace("-", "").lower()


def _filter_sessions_by_id(sessions: dict[str, list[HistoryEntry]], query: str) -> dict[str, list[HistoryEntry]]:
    normalized_query = _normalize_session_id(query)
    if not normalized_query:
        return sessions
    filtered = {
        session_id: entries
        for session_id, entries in sessions.items()
        if _normalize_session_id(session_id).startswith(normalized_query)
    }
    return filtered


def _load_meta_from_output(session_id: str, output_dir: Path) -> SessionMeta | None:
    if not output_dir.exists():
        return None

    normalized = _normalize_session_id(session_id)
    for candidate in output_dir.iterdir():
        if not candidate.is_dir():
            continue
        meta_file = candidate / "meta.json"
        if not meta_file.exists():
            continue
        try:
            with meta_file.open("r", encoding="utf-8") as handle:
                meta = json.load(handle)
        except (OSError, json.JSONDecodeError):
            continue
        stored_id = str(meta.get("session_id") or "")
        if stored_id and _normalize_session_id(stored_id) != normalized:
            continue
        started = _parse_timestamp_with_fallbacks(meta.get("started_at")) or datetime.fromtimestamp(0, tz=UTC)
        return SessionMeta(session_id=stored_id or session_id, started_at=started, cwd=meta.get("cwd"))

    return None


def load_session_meta(session_dir: Path) -> SessionMeta | None:
    """Load session metadata from session directory."""
    meta_file = session_dir / "meta.json"
    session_id = session_dir.name
    cwd: str | None = None
    started_at = datetime.fromtimestamp(0, tz=UTC)

    if meta_file.exists():
        try:
            with meta_file.open("r", encoding="utf-8") as handle:
                meta = json.load(handle)
        except (OSError, json.JSONDecodeError):
            pass
        else:
            session_id = str(meta.get("session_id") or session_id)
            cwd = meta.get("cwd")
            parsed = _parse_timestamp_with_fallbacks(meta.get("started_at"))
            if parsed is not None:
                started_at = parsed
            return SessionMeta(session_id=session_id, started_at=started_at, cwd=cwd)

    return SessionMeta(session_id=session_id, started_at=started_at, cwd=cwd)


def validate_session_entry(entry: HistoryEntry) -> bool:
    """Validate that a HistoryEntry has required fields and reasonable values."""
    if not entry.session_id or not isinstance(entry.session_id, str):
        return False
    # Allow empty text as some entries may have no text content
    return isinstance(entry.ts, int) and entry.ts > 0


def _parse_timestamp_with_fallbacks(value: Any) -> datetime | None:
    """Enhanced timestamp parsing with multiple format fallbacks."""
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    if isinstance(value, int | float):
        try:
            return datetime.fromtimestamp(float(value), tz=UTC)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return None
        iso_candidate = candidate[:-1] + "+00:00" if candidate.endswith("Z") else candidate
        try:
            dt = datetime.fromisoformat(iso_candidate)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            return dt.astimezone(UTC)
        except ValueError:
            pass

        fallback_formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y/%m/%d %H:%M:%S",
        ]

        for fmt in fallback_formats:
            try:
                dt = datetime.strptime(candidate, fmt)  # noqa: DTZ007
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                return dt.astimezone(UTC)
            except ValueError:
                continue

        try:
            numeric = float(candidate)
            return datetime.fromtimestamp(numeric, tz=UTC)
        except (ValueError, OverflowError, OSError):
            return None
    return None


def load_history(history_path: Path, skip_errors: bool = False, verbose: bool = False) -> dict[str, list[HistoryEntry]]:
    sessions: dict[str, list[HistoryEntry]] = {}
    if not history_path.exists():
        raise FileNotFoundError(f"History file not found: {history_path}")

    error_count = 0
    total_lines = 0
    with history_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            total_lines += 1
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                if skip_errors:
                    error_count += 1
                    if verbose:
                        print(
                            f"Skipping malformed JSON on line {line_number} of {history_path}: {exc}",
                            file=sys.stderr,
                        )
                    continue
                raise ValueError(f"Invalid JSON on line {line_number} of {history_path}") from exc

            try:
                entry = HistoryEntry.from_json(payload)
            except ValueError as exc:
                if skip_errors:
                    error_count += 1
                    if verbose:
                        print(
                            f"Skipping invalid history entry on line {line_number} of {history_path}: {exc}",
                            file=sys.stderr,
                        )
                    continue
                raise

            session_id = entry.session_id
            if not session_id:
                continue
            entries = sessions.setdefault(session_id, [])
            entries.append(entry)

    if verbose and error_count > 0:
        print(
            (
                f"Processed {total_lines} lines from {history_path}; "
                f"skipped {error_count} errors; loaded {len(sessions)} sessions."
            ),
            file=sys.stderr,
        )
    return sessions


def find_session_files(session_id: str, sessions_root: Path) -> list[Path]:
    if not sessions_root.exists():
        return []
    pattern = f"*{session_id}*.json*"
    return sorted(sessions_root.rglob(pattern))


def load_rollout_items(session_id: str, sessions_root: Path) -> tuple[SessionMeta, list[dict[str, Any]]]:
    files = find_session_files(session_id, sessions_root)
    meta: SessionMeta | None = None
    items: list[dict[str, Any]] = []

    for file_path in files:
        if file_path.suffix == ".jsonl":
            with file_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    event = json.loads(line)
                    if event.get("type") == "session_meta":
                        meta = meta or _meta_from_payload(session_id, event)
                    else:
                        items.append(event)
        else:
            with file_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
                session_info = data.get("session", {})
                if session_info:
                    candidate_meta = SessionMeta(
                        session_id=session_id,
                        started_at=_parse_timestamp(session_info.get("timestamp")),
                        cwd=session_info.get("cwd") or data.get("cwd"),
                    )
                    meta = meta or candidate_meta
                for item in data.get("items", []):
                    items.append(item)

    if meta is None:
        meta = SessionMeta(
            session_id=session_id,
            started_at=datetime.fromtimestamp(0, tz=UTC),
            cwd=None,
        )

    return meta, items


def _meta_from_payload(session_id: str, event: dict[str, Any]) -> SessionMeta:
    payload = event.get("payload", {})
    timestamp = payload.get("timestamp") or event.get("timestamp")
    started_at = _parse_timestamp(timestamp)
    cwd = payload.get("cwd")
    return SessionMeta(session_id=session_id, started_at=started_at, cwd=cwd)


def _parse_timestamp(value: Any | None) -> datetime:
    parsed = _parse_timestamp_with_fallbacks(value)
    if parsed is None:
        return datetime.fromtimestamp(0, tz=UTC)
    return parsed


def select_start(meta: SessionMeta, history_entries: list[HistoryEntry]) -> datetime:
    candidates: list[datetime] = []
    if meta.started_at.timestamp() > 0:
        candidates.append(meta.started_at)
    if history_entries:
        earliest_history = min(history_entries, key=lambda entry: entry.ts)
        candidates.append(datetime.fromtimestamp(earliest_history.ts, tz=UTC))
    return min(candidates) if candidates else datetime.fromtimestamp(0, tz=UTC)


def build_session_dir_name(meta: SessionMeta, history: list[HistoryEntry], tz_name: str, cwd_separator: str) -> str:
    tz = ZoneInfo(tz_name)
    start = select_start(meta, history).astimezone(tz)
    date_str = start.strftime("%Y-%m-%d-%I-%M-%p").lower()
    cwd_component = format_cwd(meta.cwd, cwd_separator)
    short_id = meta.session_id.split("-")[0]
    parts = [date_str]
    if cwd_component:
        parts.append(cwd_component)
    parts.append(short_id)
    return "__".join(parts)


def format_cwd(cwd: str | None, separator: str) -> str:
    if not cwd:
        return "cwd-unknown"
    home = Path.home()
    try:
        cwd_path = Path(cwd).resolve()
    except OSError:
        cwd_path = Path(cwd)
    try:
        relative = cwd_path.relative_to(home)
    except ValueError:
        relative = cwd_path
    parts = [part for part in relative.parts if part not in ("", ".")]
    if not parts:
        return "cwd-home"
    safe_parts = [sanitize_component(part) for part in parts]
    return separator.join(safe_parts)


def sanitize_component(component: str) -> str:
    allowed: list[str] = []
    for ch in component:
        if ch.isalnum() or ch in ("-", "_"):
            allowed.append(ch)
        else:
            allowed.append("-")
    sanitized = "".join(allowed).strip("-")
    return sanitized or "segment"


def ensure_session_dir(base: Path, name: str) -> Path:
    session_dir = base / name
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def write_history_jsonl(session_dir: Path, entries: list[HistoryEntry]) -> None:
    target = session_dir / "history.jsonl"
    existing_entries: list[HistoryEntry] = []
    seen: set[tuple[int, str]] = set()

    if target.exists():
        with target.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                payload = json.loads(line)
                entry = HistoryEntry.from_json(payload)
                existing_entries.append(entry)
                seen.add((entry.ts, entry.text))

    merged = existing_entries[:]
    for entry in sorted(entries, key=lambda e: e.ts):
        key = (entry.ts, entry.text)
        if key not in seen:
            merged.append(entry)
            seen.add(key)

    merged.sort(key=lambda e: e.ts)
    with target.open("w", encoding="utf-8") as handle:
        for entry in merged:
            handle.write(json.dumps(entry.__dict__, ensure_ascii=False) + "\n")


def collect_events(
    meta: SessionMeta,
    history_entries: list[HistoryEntry],
    rollout_items: list[dict[str, Any]],
) -> list[TimelineEvent]:
    base_start = select_start(meta, history_entries)
    events: list[TimelineEvent] = []
    seen_user_keys: set[tuple[str, int]] = set()
    call_registry: dict[str, dict[str, Any]] = {}

    def add_event(event: TimelineEvent) -> None:
        if event.role == "user" and event.text:
            key = (_normalize_text(event.text), int(event.timestamp.timestamp()))
            if key in seen_user_keys:
                return
            seen_user_keys.add(key)
        events.append(event)

    for index, item in enumerate(rollout_items):
        timestamp = _extract_event_timestamp(item, base_start, index)
        item_type = str(item.get("type") or "unknown")

        if item_type == "response_item":
            payload = item.get("payload", {})
            payload_type = str(payload.get("type") or "unknown")

            if payload_type == "message":
                role = payload.get("role")
                content = payload.get("content")
                text = _content_to_text(content)
                if not text.strip():
                    continue
                add_event(
                    TimelineEvent(
                        timestamp=timestamp,
                        order=index,
                        source="rollout",
                        kind="message",
                        role=str(role) if role else None,
                        text=text.strip(),
                        content=content,
                        raw=item,
                    )
                )
            elif payload_type == "reasoning":
                text = _reasoning_text(payload)
                add_event(
                    TimelineEvent(
                        timestamp=timestamp,
                        order=index,
                        source="rollout",
                        kind="reasoning",
                        role="assistant",
                        text=text.strip(),
                        content=payload.get("content"),
                        raw=item,
                    )
                )
            elif payload_type == "function_call":
                args_raw = payload.get("arguments")
                parsed_args = _maybe_parse_json(args_raw)
                call_id = str(payload.get("call_id")) if payload.get("call_id") else None
                add_event(
                    TimelineEvent(
                        timestamp=timestamp,
                        order=index,
                        source="rollout",
                        kind="tool_call",
                        role="assistant",
                        text="",
                        content=None,
                        raw=item,
                        tool_name=payload.get("name"),
                        tool_args=parsed_args if parsed_args is not None else args_raw,
                    )
                )
                if call_id:
                    call_registry[call_id] = {
                        "tool_name": payload.get("name"),
                        "arguments": parsed_args if parsed_args is not None else args_raw,
                    }
            elif payload_type == "function_call_output":
                call_id = str(payload.get("call_id")) if payload.get("call_id") else None
                call_meta = call_registry.get(call_id, {}) if call_id else {}
                output_raw = payload.get("output")
                parsed_output = _maybe_parse_json(output_raw)
                text = (
                    _content_to_text(parsed_output)
                    if parsed_output not in (None, "", [])
                    else (str(output_raw) if output_raw else "")
                )
                add_event(
                    TimelineEvent(
                        timestamp=timestamp,
                        order=index,
                        source="rollout",
                        kind="tool_result",
                        role="tool",
                        text=(text or "").strip(),
                        content=None,
                        raw=item,
                        tool_name=call_meta.get("tool_name"),
                        tool_args=call_meta.get("arguments"),
                        tool_result=parsed_output if parsed_output is not None else output_raw,
                    )
                )
            else:
                text = _content_to_text(payload.get("content")) or str(payload.get("text") or payload_type)
                add_event(
                    TimelineEvent(
                        timestamp=timestamp,
                        order=index,
                        source="rollout",
                        kind=payload_type,
                        role=None,
                        text=text.strip(),
                        content=payload,
                        raw=item,
                    )
                )

        elif item_type == "event_msg":
            payload = item.get("payload", {})
            role = _role_from_event_msg(payload.get("type"))
            text = payload.get("message") or _content_to_text(payload.get("content"))
            if not (text and text.strip()):
                continue
            add_event(
                TimelineEvent(
                    timestamp=timestamp,
                    order=index,
                    source="rollout",
                    kind="message",
                    role=role,
                    text=(text or "").strip(),
                    content=payload.get("content"),
                    raw=item,
                )
            )

        elif item_type == "turn_context":
            events.append(
                TimelineEvent(
                    timestamp=timestamp,
                    order=index,
                    source="rollout",
                    kind="context",
                    role=None,
                    text=json.dumps(item.get("payload"), ensure_ascii=False),
                    content=item.get("payload"),
                    raw=item,
                )
            )

        elif item_type == "message":
            role = item.get("role")
            text = _content_to_text(item.get("content")) or str(item.get("text", ""))
            if not text.strip():
                continue
            add_event(
                TimelineEvent(
                    timestamp=timestamp,
                    order=index,
                    source="rollout",
                    kind="message",
                    role=str(role) if role else None,
                    text=text.strip(),
                    content=item.get("content"),
                    raw=item,
                )
            )

        elif item_type == "reasoning":
            text = str(item.get("text") or item.get("content") or "")
            add_event(
                TimelineEvent(
                    timestamp=timestamp,
                    order=index,
                    source="rollout",
                    kind="reasoning",
                    role=item.get("role") or "assistant",
                    text=text.strip(),
                    content=item.get("content"),
                    raw=item,
                )
            )

        elif item_type == "tool_call":
            args = item.get("args") or item.get("arguments")
            add_event(
                TimelineEvent(
                    timestamp=timestamp,
                    order=index,
                    source="rollout",
                    kind="tool_call",
                    role=item.get("role") or "assistant",
                    text="",
                    content=None,
                    raw=item,
                    tool_name=item.get("name") or item.get("tool"),
                    tool_args=args,
                )
            )

        elif item_type == "tool_result":
            result = item.get("content") or item.get("result") or item.get("output")
            text = _content_to_text(result)
            add_event(
                TimelineEvent(
                    timestamp=timestamp,
                    order=index,
                    source="rollout",
                    kind="tool_result",
                    role="tool",
                    text=(text or "").strip(),
                    content=None,
                    raw=item,
                    tool_name=item.get("name") or item.get("tool"),
                    tool_result=result,
                )
            )

        else:
            text = _content_to_text(item.get("content")) or str(item.get("text", ""))
            events.append(
                TimelineEvent(
                    timestamp=timestamp,
                    order=index,
                    source="rollout",
                    kind=item_type,
                    role=item.get("role"),
                    text=text.strip(),
                    content=item.get("content"),
                    raw=item,
                )
            )

    base_order = len(events)
    for offset, entry in enumerate(history_entries):
        dt = datetime.fromtimestamp(entry.ts, tz=UTC)
        text = entry.text.strip()
        history_event = TimelineEvent(
            timestamp=dt,
            order=base_order + offset,
            source="history",
            kind="history_user",
            role="user",
            text=text,
            content=None,
            raw=entry,
        )
        add_event(history_event)

    events.sort(key=lambda ev: (ev.timestamp, ev.order))
    return events


def _extract_event_timestamp(item: dict[str, Any], fallback_start: datetime, index: int) -> datetime:
    timestamp = item.get("timestamp") or item.get("created_at") or item.get("ts")
    if isinstance(timestamp, int | float):
        return datetime.fromtimestamp(float(timestamp), tz=UTC)
    if isinstance(timestamp, str):
        parsed = _parse_timestamp_with_fallbacks(timestamp)
        if parsed and parsed.timestamp() > 0:
            return parsed
    return fallback_start + timedelta(seconds=index)


def _normalize_text(value: str) -> str:
    return " ".join(value.split()).lower()


def _content_to_text(content: Any | None) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for chunk in content:
            if isinstance(chunk, dict):
                chunk_type = chunk.get("type")
                if chunk_type in {
                    "input_text",
                    "text",
                    "summary_text",
                    "markdown_text",
                }:
                    parts.append(str(chunk.get("text", "")))
                elif chunk_type in {"tool_result", "output_text"}:
                    parts.append(str(chunk.get("text") or chunk.get("content") or ""))
                else:
                    parts.append(json.dumps(chunk, ensure_ascii=False))
            else:
                parts.append(str(chunk))
        return "\n".join(part for part in parts if part)
    if isinstance(content, dict):
        return json.dumps(content, ensure_ascii=False)
    return str(content)


def _reasoning_text(payload: dict[str, Any]) -> str:
    parts: list[str] = []
    summary = payload.get("summary")
    if summary:
        summary_text = _content_to_text(summary)
        if summary_text:
            parts.append(summary_text)
    content = payload.get("content")
    if content:
        content_text = _content_to_text(content)
        if content_text:
            parts.append(content_text)
    if parts:
        return "\n".join(parts)
    if payload.get("encrypted_content"):
        return ""
    return ""


def _role_from_event_msg(payload_type: str | None) -> str | None:
    if not payload_type:
        return None
    lowered = payload_type.lower()
    if "user" in lowered:
        return "user"
    if "assistant" in lowered:
        return "assistant"
    if "tool" in lowered:
        return "tool"
    return None


def _maybe_parse_json(value: Any) -> Any | None:
    if value is None:
        return None
    if isinstance(value, dict | list):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            try:
                return json.loads(stripped)
            except json.JSONDecodeError:
                return value
    return value


def write_conversation_transcript(
    session_dir: Path, meta: SessionMeta, events: list[TimelineEvent], tz_name: str
) -> None:
    target = session_dir / "transcript.md"
    tz = ZoneInfo(tz_name)
    lines: list[str] = ["# Session Transcript", ""]

    start_dt = events[0].timestamp if events else meta.started_at
    if start_dt.timestamp() <= 0 and meta.started_at.timestamp() > 0:
        start_dt = meta.started_at
    start_local = _format_local(start_dt, tz) if start_dt.timestamp() > 0 else "unknown"

    lines.append("## Metadata")
    lines.append(f"- Session ID: {meta.session_id}")
    lines.append(f"- Start: {start_local}")
    lines.append(f"- CWD: {meta.cwd or 'unknown'}")
    lines.append("")

    lines.append("## Conversation")
    if not events:
        lines.append("- (no events found)")
    else:
        for event in events:
            if event.kind not in {
                "message",
                "reasoning",
                "tool_call",
                "tool_result",
                "history_user",
            }:
                continue
            time_str = _format_local(event.timestamp, tz)
            if event.kind == "message":
                role_label = "User" if event.role == "user" else "Assistant" if event.role == "assistant" else "Message"
                body = event.text or ""
                normalized = body.lstrip()
                if role_label == "User" and normalized.startswith("<user_instructions"):
                    continue
                if role_label == "User" and normalized.startswith("<environment_context"):
                    continue
                lines.append(f"- **{role_label}** · {time_str}")
                if body:
                    for fragment in body.splitlines():
                        lines.append(f"  {fragment}")
                lines.append("")
            elif event.kind == "reasoning":
                cleaned = (event.text or "").strip()
                if cleaned and cleaned != "[encrypted reasoning omitted]":
                    lines.append(f"- **Assistant [thinking]** · {time_str}")
                    for fragment in cleaned.splitlines():
                        lines.append(f"  {fragment}")
                    lines.append("")
            elif event.kind == "tool_call":
                summary = _summarize_tool_args(event.tool_args)
                tool_label = event.tool_name or "unknown"
                lines.append(f"- **Tool Call** · {time_str}")
                detail = f"`{tool_label}` {summary}".rstrip()
                if detail:
                    lines.append(f"  {detail}")
                lines.append("")
            elif event.kind == "tool_result":
                summary_text = event.text or _content_to_text(event.tool_result)
                summary = _shorten(summary_text) if summary_text else ""
                tool_label = event.tool_name or "unknown"
                lines.append(f"- **Tool Result** · {time_str}")
                detail = f"`{tool_label}` {summary}".rstrip()
                if detail:
                    lines.append(f"  {detail}")
                lines.append("")
            elif event.kind == "history_user":
                lines.append(f"- **User [history]** · {time_str}")
                if event.text:
                    for fragment in event.text.splitlines():
                        lines.append(f"  {fragment}")
                lines.append("")

    target.write_text("\n".join(lines), encoding="utf-8")


def write_extended_transcript(session_dir: Path, meta: SessionMeta, events: list[TimelineEvent], tz_name: str) -> None:
    target = session_dir / "transcript_extended.md"
    tz = ZoneInfo(tz_name)
    lines: list[str] = [f"# Session {meta.session_id}", ""]

    start_dt = events[0].timestamp if events else meta.started_at
    if start_dt.timestamp() <= 0 and meta.started_at.timestamp() > 0:
        start_dt = meta.started_at
    start_local = _format_local(start_dt, tz) if start_dt.timestamp() > 0 else "unknown"

    lines.append("## Metadata")
    lines.append(f"- Start: {start_local}")
    lines.append(f"- CWD: {meta.cwd or 'unknown'}")
    lines.append(f"- Events: {len(events)}")
    lines.append("")

    lines.append("## Timeline")
    if not events:
        lines.append("- (no events found)")
    else:
        for event in events:
            time_str = _format_local(event.timestamp, tz)
            header = f"### {time_str} · {event.kind.upper()}"
            lines.append(header)
            lines.append("")
            lines.append(f"- Source: {event.source}")
            if event.role:
                lines.append(f"- Role: {event.role}")
            if event.tool_name:
                lines.append(f"- Tool: {event.tool_name}")
            lines.append(f"- Order: {event.order}")
            if event.text:
                lines.append("")
                lines.append("```text")
                lines.extend(event.text.splitlines() or [""])
                lines.append("```")
            if event.tool_args is not None:
                lines.append("")
                lines.append("```json")
                lines.append(pretty_json(event.tool_args))
                lines.append("```")
            if event.tool_result is not None:
                lines.append("")
                lines.append("```json")
                lines.append(pretty_json(event.tool_result))
                lines.append("```")
            lines.append("")
            lines.append("```json")
            lines.append(pretty_json(_raw_event_data(event.raw)))
            lines.append("```")
            lines.append("")

    target.write_text("\n".join(lines), encoding="utf-8")


def write_compact_transcript(session_dir: Path, meta: SessionMeta, events: list[TimelineEvent], tz_name: str) -> None:
    """Write a compact transcript that blends summary and timeline details."""
    target = session_dir / "transcript_compact.md"
    tz = ZoneInfo(tz_name)
    lines: list[str] = ["# Session Transcript (Compact)", ""]

    start_dt = events[0].timestamp if events else meta.started_at
    if start_dt.timestamp() <= 0 and meta.started_at.timestamp() > 0:
        start_dt = meta.started_at
    start_local = _format_local(start_dt, tz) if start_dt.timestamp() > 0 else "unknown"

    lines.append("## Metadata")
    lines.append(f"- Session ID: {meta.session_id}")
    lines.append(f"- Start: {start_local}")
    lines.append(f"- CWD: {meta.cwd or 'unknown'}")
    lines.append(f"- Events: {len(events)}")
    lines.append("")

    lines.append("## Timeline")
    if not events:
        lines.append("- (no events found)")
    else:
        for event in events:
            time_str = _format_local(event.timestamp, tz)
            role = event.role or event.kind
            summary: str = ""
            if event.kind in {"message", "history_user"}:
                summary = (event.text or "").strip()
            elif event.kind == "reasoning":
                summary = _shorten(event.text or "")
            elif event.kind == "tool_call":
                summary = f"tool call `{event.tool_name or 'unknown'}` {_summarize_tool_args(event.tool_args)}".strip()
            elif event.kind == "tool_result":
                summary_text = event.text or _content_to_text(event.tool_result)
                summary = f"tool result {_shorten(summary_text)}".strip()
            else:
                summary = _shorten(event.text or "")

            if not summary:
                summary = "(no content)"

            lines.append(f"- **{role or 'event'}** · {time_str} · {summary}")
    target.write_text("\n".join(lines), encoding="utf-8")


def write_session_metadata(session_dir: Path, meta: SessionMeta, events: list[TimelineEvent]) -> None:
    """Persist lightweight metadata for downstream tooling."""
    metadata = {
        "session_id": meta.session_id,
        "started_at": meta.started_at.astimezone(UTC).isoformat(),
        "cwd": meta.cwd,
        "event_count": len(events),
    }
    target = session_dir / "meta.json"
    target.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_block(lines: list[str], header: str, body: str) -> None:
    lines.append(header)
    if body:
        for fragment in body.splitlines():
            lines.append(f"  {fragment}")
    else:
        lines.append("  (no content)")
    lines.append("")


def _summarize_tool_args(args: Any | None, max_length: int = 120) -> str:
    if args is None:
        return ""
    if isinstance(args, dict):
        parts = [f"{key}={_shorten(value)}" for key, value in args.items()]
        summary = ", ".join(parts)
    elif isinstance(args, list):
        summary = ", ".join(_shorten(item) for item in args)
    else:
        summary = _shorten(args)
    summary = summary.replace("\n", " ")
    if len(summary) > max_length:
        summary = summary[: max_length - 3] + "..."
    return f"({summary})" if summary else ""


def _shorten(value: Any, max_length: int = 60) -> str:
    if isinstance(value, str):
        text = value
    else:
        try:
            text = json.dumps(value, ensure_ascii=False)
        except TypeError:
            text = str(value)
    text = " ".join(text.split())
    if len(text) > max_length:
        return text[: max_length - 3] + "..."
    return text


def _format_local(ts: datetime, tz: ZoneInfo) -> str:
    return ts.astimezone(tz).strftime("%Y-%m-%d %I:%M %p %Z")


def _raw_event_data(raw: Any) -> Any:
    if isinstance(raw, HistoryEntry):
        return {
            "session_id": raw.session_id,
            "ts": raw.ts,
            "text": raw.text,
            "source": "history.jsonl",
        }
    return raw


def pretty_json(value: Any) -> str:
    try:
        return json.dumps(value, indent=2, ensure_ascii=False)
    except TypeError:
        return json.dumps(str(value), indent=2, ensure_ascii=False)


def process_session(
    session_id: str,
    history_entries: list[HistoryEntry],
    sessions_root: Path,
    output_base: Path,
    tz_name: str,
    cwd_separator: str,
    output_format: str = "standard",
    incremental: bool = False,
    force: bool = False,
    verbose: bool = False,
) -> Path | None:
    meta, rollout_items = load_rollout_items(session_id, sessions_root)
    if (meta.started_at.timestamp() == 0) and history_entries:
        earliest_ts = min(entry.ts for entry in history_entries)
        meta.started_at = datetime.fromtimestamp(earliest_ts, tz=UTC)

    events = collect_events(meta, history_entries, rollout_items)
    if events:
        earliest_event = min(events, key=lambda ev: ev.timestamp).timestamp
        if meta.started_at.timestamp() == 0 or earliest_event < meta.started_at:
            meta.started_at = earliest_event

    session_dir_name = build_session_dir_name(meta, history_entries, tz_name, cwd_separator)
    session_dir = output_base / session_dir_name

    if incremental and session_dir.exists() and not force:
        if verbose:
            print(f"Skipping session {session_id} (already exists at {session_dir})", file=sys.stderr)
        return None

    session_dir = ensure_session_dir(output_base, session_dir_name)
    write_history_jsonl(session_dir, history_entries)

    if output_format in {"standard", "both"}:
        write_conversation_transcript(session_dir, meta, events, tz_name)
        write_extended_transcript(session_dir, meta, events, tz_name)
    if output_format in {"compact", "both"}:
        write_compact_transcript(session_dir, meta, events, tz_name)

    write_session_metadata(session_dir, meta, events)
    return session_dir


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    sessions_map = load_history(args.history, skip_errors=args.skip_errors, verbose=args.verbose)

    if args.session_id:
        sessions_map = _filter_sessions_by_id(sessions_map, args.session_id)
        if args.verbose and not sessions_map:
            print(f"No sessions matched session ID '{args.session_id}'", file=sys.stderr)

    if args.project_dir:
        sessions_map = filter_sessions_by_project(sessions_map, args.project_dir, args.sessions_root, args.output_dir)
        if args.verbose and not sessions_map:
            print(
                f"No sessions matched project directory '{args.project_dir}'",
                file=sys.stderr,
            )

    if not sessions_map:
        if args.verbose:
            print("No sessions to process.", file=sys.stderr)
        return

    args.output_dir.mkdir(parents=True, exist_ok=True)

    total_sessions = len(sessions_map)
    processed = 0
    skipped = 0
    started = datetime.now(tz=UTC)

    for index, (session_id, entries) in enumerate(sorted(sessions_map.items()), start=1):
        if args.verbose:
            print(f"[{index}/{total_sessions}] Processing session {session_id}", file=sys.stderr)
        try:
            result = process_session(
                session_id,
                entries,
                args.sessions_root,
                args.output_dir,
                args.timezone,
                args.cwd_separator,
                output_format=args.output_format,
                incremental=args.incremental,
                force=args.force,
                verbose=args.verbose,
            )
        except Exception as exc:
            skipped += 1
            if args.skip_errors:
                if args.verbose:
                    print(f"Failed session {session_id}: {exc}", file=sys.stderr)
                continue
            raise

        if result is None:
            skipped += 1
        else:
            processed += 1

    if args.verbose:
        duration = datetime.now(tz=UTC) - started
        print(
            (
                f"Completed processing in {duration.total_seconds():.1f}s: "
                f"{processed} processed, {skipped} skipped, {total_sessions} total."
            ),
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
