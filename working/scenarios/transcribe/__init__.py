"""
Transcribe Scenario - Video/Audio Transcription Pipeline

Transcribes YouTube videos and local audio/video files using OpenAI Whisper API.
Saves transcripts in multiple formats with state persistence for resume capability.
"""

from .main import TranscriptionPipeline

__all__ = ["TranscriptionPipeline"]
