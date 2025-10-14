#!/usr/bin/env python3
"""
Test script to verify audio caching functionality.
"""

import tempfile
from pathlib import Path

from amplifier.utils.logger import get_logger

# Import the components we need to test
from scenarios.transcribe.storage import TranscriptStorage
from scenarios.transcribe.video_loader import VideoLoader

logger = get_logger(__name__)


def test_cache_functionality():
    """Test that caching works as expected."""

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Test 1: Test save_audio method
        logger.info("Test 1: Testing save_audio method...")
        storage = TranscriptStorage(output_dir=temp_path)

        # Create a dummy audio file
        source_audio = temp_path / "source.mp3"
        source_audio.write_text("dummy audio content")

        # Save it to an output directory
        output_dir = temp_path / "test_video"
        output_dir.mkdir()

        saved_path = storage.save_audio(source_audio, output_dir)

        assert saved_path.exists(), "Audio file should be saved"
        assert saved_path.name == "audio.mp3", "Should be named audio.mp3"
        assert saved_path.read_text() == "dummy audio content", "Content should match"
        logger.info("✓ save_audio works correctly")

        # Test 2: Test that save_audio doesn't copy if already in place
        logger.info("Test 2: Testing save_audio with file already in place...")
        existing_audio = output_dir / "audio.mp3"
        saved_again = storage.save_audio(existing_audio, output_dir)
        assert saved_again == existing_audio, "Should return same path if already in place"
        logger.info("✓ save_audio handles existing files correctly")

        # Test 3: Test video loader cache detection (mock test)
        logger.info("Test 3: Testing VideoLoader cache detection...")
        loader = VideoLoader()

        # Create a mock cached audio file
        cache_dir = temp_path / "cache_test"
        cache_dir.mkdir()
        cached_audio = cache_dir / "audio.mp3"
        cached_audio.write_text("cached audio")

        # Verify that the loader has the new signature with cache support
        # (We can't actually test downloading without a real URL)
        import inspect

        sig = inspect.signature(loader.download_audio)
        assert "use_cache" in sig.parameters, "download_audio should have use_cache parameter"
        assert sig.parameters["use_cache"].default is True, "use_cache should default to True"
        logger.info("✓ VideoLoader has cache detection implemented")

        # Test 4: Verify JSON metadata includes audio info
        logger.info("Test 4: Testing JSON metadata with audio info...")

        # Create mock objects for testing
        from scenarios.transcribe.video_loader.core import VideoInfo
        from scenarios.transcribe.whisper_transcriber.core import Transcript
        from scenarios.transcribe.whisper_transcriber.core import TranscriptSegment

        transcript = Transcript(
            text="Test transcript",
            language="en",
            duration=60.0,
            segments=[TranscriptSegment(id=0, start=0.0, end=5.0, text="Test segment")],
        )

        video_info = VideoInfo(source="test_source", type="file", title="Test Video", id="test_id", duration=60.0)

        # Save with audio path
        json_output_dir = temp_path / "json_test"
        json_output_dir.mkdir()

        # Update storage to use our test directory
        storage.output_dir = json_output_dir

        # Create a test audio file
        test_audio = json_output_dir / "test_audio.mp3"
        test_audio.write_bytes(b"x" * 1024 * 100)  # 100KB file

        # Save transcript with audio
        output_dir = storage.save(transcript, video_info, test_audio)

        # Read the JSON file from the actual output directory
        import json

        json_file = output_dir / "transcript.json"
        assert json_file.exists(), "JSON file should be created"

        with open(json_file) as f:
            data = json.load(f)

        assert "audio" in data, "JSON should have audio field"
        assert data["audio"] is not None, "Audio metadata should be present"
        assert data["audio"]["filename"] == "audio.mp3", "Should have correct filename"
        assert "size_mb" in data["audio"], "Should have size info"
        assert data["audio"]["format"] == "mp3", "Should have format info"

        logger.info("✓ JSON metadata includes audio info correctly")

        logger.info("\n✅ All cache functionality tests passed!")


if __name__ == "__main__":
    test_cache_functionality()
