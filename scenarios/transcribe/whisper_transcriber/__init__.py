"""
Whisper Transcriber Module

Transcribes audio using OpenAI Whisper API.
"""

from .core import Transcript
from .core import WhisperTranscriber

__all__ = ["Transcript", "WhisperTranscriber"]
