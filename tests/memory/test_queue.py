"""Tests for JSONL-based extraction queue."""

import json

import pytest

from amplifier.memory.queue import QUEUE_FILE
from amplifier.memory.queue import QueuedExtraction
from amplifier.memory.queue import clear_queue
from amplifier.memory.queue import get_queued_items
from amplifier.memory.queue import queue_extraction
from amplifier.memory.queue import remove_from_queue


@pytest.fixture(autouse=True)
def clean_queue():
    """Clean queue before and after each test."""
    clear_queue()
    yield
    clear_queue()


def test_queue_extraction_appends():
    """Test that queue_extraction appends items to JSONL file."""
    item1 = QueuedExtraction(
        session_id="abc123",
        transcript_path="/path/to/transcript1.jsonl",
        timestamp="2025-11-11T14:30:00",
        hook_event="Stop",
    )
    item2 = QueuedExtraction(
        session_id="def456",
        transcript_path="/path/to/transcript2.jsonl",
        timestamp="2025-11-11T14:35:00",
        hook_event="SubagentStop",
    )

    queue_extraction(item1)
    queue_extraction(item2)

    assert QUEUE_FILE.exists()

    with QUEUE_FILE.open() as f:
        lines = f.readlines()

    assert len(lines) == 2
    assert json.loads(lines[0])["session_id"] == "abc123"
    assert json.loads(lines[1])["session_id"] == "def456"


def test_get_queued_items_returns_all():
    """Test that get_queued_items returns all items in queue."""
    item1 = QueuedExtraction(
        session_id="abc123",
        transcript_path="/path/to/transcript1.jsonl",
        timestamp="2025-11-11T14:30:00",
        hook_event="Stop",
    )
    item2 = QueuedExtraction(
        session_id="def456",
        transcript_path="/path/to/transcript2.jsonl",
        timestamp="2025-11-11T14:35:00",
        hook_event="SubagentStop",
        retries=2,
        last_error="Connection timeout",
    )

    queue_extraction(item1)
    queue_extraction(item2)

    items = get_queued_items()

    assert len(items) == 2
    assert items[0].session_id == "abc123"
    assert items[0].hook_event == "Stop"
    assert items[0].retries == 0
    assert items[1].session_id == "def456"
    assert items[1].retries == 2
    assert items[1].last_error == "Connection timeout"


def test_get_queued_items_empty_when_no_file():
    """Test that get_queued_items returns empty list when queue file doesn't exist."""
    assert not QUEUE_FILE.exists()
    items = get_queued_items()
    assert items == []


def test_remove_from_queue_deletes():
    """Test that remove_from_queue removes matching item."""
    item1 = QueuedExtraction(
        session_id="abc123",
        transcript_path="/path/to/transcript1.jsonl",
        timestamp="2025-11-11T14:30:00",
        hook_event="Stop",
    )
    item2 = QueuedExtraction(
        session_id="def456",
        transcript_path="/path/to/transcript2.jsonl",
        timestamp="2025-11-11T14:35:00",
        hook_event="SubagentStop",
    )
    item3 = QueuedExtraction(
        session_id="ghi789",
        transcript_path="/path/to/transcript3.jsonl",
        timestamp="2025-11-11T14:40:00",
        hook_event="Stop",
    )

    queue_extraction(item1)
    queue_extraction(item2)
    queue_extraction(item3)

    remove_from_queue("def456")

    items = get_queued_items()
    assert len(items) == 2
    assert items[0].session_id == "abc123"
    assert items[1].session_id == "ghi789"


def test_remove_from_queue_no_error_when_empty():
    """Test that remove_from_queue doesn't error when queue is empty."""
    assert not QUEUE_FILE.exists()
    remove_from_queue("nonexistent")


def test_clear_queue_works():
    """Test that clear_queue deletes the queue file."""
    item = QueuedExtraction(
        session_id="abc123",
        transcript_path="/path/to/transcript.jsonl",
        timestamp="2025-11-11T14:30:00",
        hook_event="Stop",
    )

    queue_extraction(item)
    assert QUEUE_FILE.exists()

    clear_queue()
    assert not QUEUE_FILE.exists()


def test_clear_queue_no_error_when_empty():
    """Test that clear_queue doesn't error when file doesn't exist."""
    assert not QUEUE_FILE.exists()
    clear_queue()
