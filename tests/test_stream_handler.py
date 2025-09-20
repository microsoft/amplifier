"""Tests for the stream handler module."""

import asyncio

import pytest

from amplifier.tools.module_generator.stream_handler import handle_streaming_response


class MockMessage:
    """Mock message object matching Claude SDK structure."""

    def __init__(self, text: str):
        self.content = [MockBlock(text)]


class MockBlock:
    """Mock content block with text attribute."""

    def __init__(self, text: str):
        self.text = text


async def create_mock_iterator(chunks: list[str], delay: float = 0.01):
    """Create a mock async iterator for testing."""
    for chunk in chunks:
        await asyncio.sleep(delay)
        yield MockMessage(chunk)


@pytest.mark.asyncio
async def test_basic_streaming():
    """Test basic streaming functionality."""
    chunks = ["Hello ", "world!"]
    response = await handle_streaming_response(create_mock_iterator(chunks), timeout_seconds=5, idle_timeout=1)
    assert response == "Hello world!"


@pytest.mark.asyncio
async def test_empty_response():
    """Test handling of empty response."""
    response = await handle_streaming_response(create_mock_iterator([]), timeout_seconds=1, idle_timeout=1)
    assert response == ""


@pytest.mark.asyncio
async def test_idle_timeout():
    """Test idle timeout detection."""

    async def slow_iterator():
        yield MockMessage("Start")
        await asyncio.sleep(2)  # Exceed idle timeout
        yield MockMessage("End")

    with pytest.raises(TimeoutError) as exc_info:
        await handle_streaming_response(slow_iterator(), timeout_seconds=10, idle_timeout=1)

    assert "no chunks for 1 seconds" in str(exc_info.value)
    assert "Partial response saved" in str(exc_info.value)


@pytest.mark.asyncio
async def test_total_timeout():
    """Test total timeout detection."""

    async def infinite_iterator():
        count = 0
        while True:
            await asyncio.sleep(0.1)
            yield MockMessage(f"Chunk {count}")
            count += 1

    with pytest.raises(TimeoutError) as exc_info:
        await handle_streaming_response(infinite_iterator(), timeout_seconds=1, idle_timeout=10)

    assert "Response timed out after 1 seconds" in str(exc_info.value)


@pytest.mark.asyncio
async def test_progress_callback():
    """Test progress callback functionality."""
    chunks_reported = []
    chars_reported = []

    def track_progress(chunks: int, chars: int):
        chunks_reported.append(chunks)
        chars_reported.append(chars)

    chunks = ["A", "B", "C"]
    response = await handle_streaming_response(
        create_mock_iterator(chunks), timeout_seconds=5, progress_callback=track_progress
    )

    assert response == "ABC"
    assert len(chunks_reported) > 0
    assert chunks_reported[-1] == 3  # Final chunk count
    assert chars_reported[-1] == 3  # Final char count
