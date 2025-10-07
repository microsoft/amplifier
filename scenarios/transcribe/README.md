# Transcribe Scenario

Transcribes YouTube videos and local audio/video files using OpenAI's Whisper API.

## Features

- ✅ YouTube video transcription (via yt-dlp)
- ✅ Local audio/video file transcription
- ✅ Multiple output formats (JSON, Markdown, WebVTT, SRT)
- ✅ Readable paragraphs with clickable timestamps (YouTube)
- ✅ AI-powered insights: summaries + key quotes (optional)
- ✅ Audio file preservation and caching (avoid re-downloads)
- ✅ Automatic audio compression for API limits
- ✅ State persistence for resume capability
- ✅ Cost estimation before processing
- ✅ Batch processing with incremental saves

## Prerequisites

1. **OpenAI API Key**: Set `OPENAI_API_KEY` environment variable in `.env`
2. **Anthropic API Key**: Set `ANTHROPIC_API_KEY` environment variable in `.env` (for AI enhancements)
3. **FFmpeg**: Required for audio extraction and compression

## Installation

```bash
# Install all dependencies (including yt-dlp, openai, anthropic)
make install

# Or manually with uv:
uv sync

# Ensure FFmpeg is installed (system dependency)
# macOS: brew install ffmpeg
# Ubuntu: sudo apt-get install ffmpeg
```

## Usage

### Basic Usage

```bash
# Transcribe a YouTube video
python -m scenarios.transcribe "https://youtube.com/watch?v=..."

# Transcribe a local video file
python -m scenarios.transcribe video.mp4

# Transcribe multiple sources
python -m scenarios.transcribe video1.mp4 "https://youtube.com/..." audio.mp3
```

### Resume Interrupted Session

```bash
# Resume last session
python -m scenarios.transcribe --resume video.mp4

# Resume specific session
python -m scenarios.transcribe --session-dir .data/transcribe/20241201_143022 --resume video.mp4
```

### Custom Output Directory

```bash
python -m scenarios.transcribe --output-dir ~/my-transcripts video.mp4
```

### Audio Caching

Audio files are automatically cached to avoid re-downloading. If you transcribe the same video twice, the second run uses the cached audio:

```bash
# First run: downloads audio
make transcribe SOURCE="https://youtube.com/watch?v=..."

# Second run: uses cached audio (instant)
make transcribe SOURCE="https://youtube.com/watch?v=..."

# Force re-download (ignore cache)
make transcribe SOURCE="https://youtube.com/watch?v=..." --force-download
```

**Benefits:**
- Saves bandwidth and time
- Audio preserved for offline listening
- All files self-contained in one directory

## Output Structure

Transcripts are saved in organized directories:

```
AMPLIFIER_CONTENT_DIRS/transcripts/
├── [video-id]/
│   ├── audio.mp3            # Downloaded/extracted audio (cached)
│   ├── transcript.json      # Full structured data with segments
│   ├── transcript.md        # Readable paragraphs with timestamps
│   ├── insights.md          # AI summary + key quotes (if enhanced)
│   ├── transcript.vtt       # WebVTT subtitles
│   └── transcript.srt       # SRT subtitles
```

**audio.mp3**: Preserved audio file (192kbps MP3). Re-used on subsequent runs - saves bandwidth and time.

**transcript.md**: Formatted in readable paragraphs grouped by natural pauses, with clickable YouTube timestamps at each section break.

**insights.md**: Combined summary (overview, key points, themes) and notable quotes with timestamps - only created when AI enhancement is enabled.

## State Management

The pipeline saves state after each video, enabling:
- Resume from interruption
- Skip already processed videos
- Track failed videos for retry

State files are saved in:
```
.data/transcribe/[session-timestamp]/
├── state.json              # Pipeline state
└── audio/                  # Temporary audio files
```

## Cost Estimation

OpenAI Whisper API pricing (as of 2024):
- $0.006 per minute of audio
- Estimated costs shown before processing

## Architecture

The pipeline follows a modular design:

1. **video_loader**: Load video info and download from YouTube
2. **audio_extractor**: Extract and compress audio for API
3. **whisper_transcriber**: Call OpenAI Whisper API
4. **transcript_formatter**: Format segments into readable paragraphs
5. **summary_generator**: Generate AI summaries (optional)
6. **quote_extractor**: Extract key quotes (optional)
7. **insights_generator**: Combine summaries and quotes
8. **storage**: Save transcripts in multiple formats
9. **state**: Track progress for resume capability

## Error Handling

- Automatic retry with exponential backoff for API failures
- Audio compression if file exceeds 25MB limit
- Failed videos tracked in state for manual retry
- Graceful handling of interrupted sessions

## Examples

### Transcribe YouTube Playlist (one at a time)
```bash
for url in url1 url2 url3; do
    python -m scenarios.transcribe "$url"
done
```

### Process Local Directory
```bash
python -m scenarios.transcribe ~/videos/*.mp4
```

### Resume After Failure
```bash
# First run (interrupted)
python -m scenarios.transcribe video1.mp4 video2.mp4 video3.mp4
# Ctrl+C after video1

# Resume (will skip video1, continue with video2)
python -m scenarios.transcribe --resume video1.mp4 video2.mp4 video3.mp4
```

## Troubleshooting

### "yt-dlp is not installed"
```bash
# Ensure all dependencies are installed
make install

# Or manually add yt-dlp:
uv add yt-dlp
```

### "ffmpeg not found"
Install FFmpeg for your platform:
- macOS: `brew install ffmpeg`
- Ubuntu/Debian: `sudo apt-get install ffmpeg`
- Windows: Download from ffmpeg.org

### "Audio file too large"
The pipeline automatically compresses audio files over 25MB. If compression fails, manually convert to a smaller format:
```bash
ffmpeg -i input.wav -b:a 64k -ar 16000 output.mp3
```

### API Rate Limits
The pipeline includes automatic retry with exponential backoff. For persistent issues, wait and resume later.

## Phase 2 Enhancements (Coming Soon)

- AI-powered summaries and key quotes extraction
- Batch processing with parallel downloads
- Screenshot extraction at key moments
- Custom prompt templates for domain-specific transcription