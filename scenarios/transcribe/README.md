# Transcribe: Never Miss What Was Said

**Turn YouTube videos and audio files into searchable, quotable transcripts.**

## The Problem

You consume valuable content through videos and audio, but:
- **Can't search what was said** - Information is locked in audio format
- **Can't reference specific moments** - No way to quote or cite exact timestamps
- **Takes hours to review** - Re-watching entire videos to find that one insight
- **Miss key points** - No written record means details get forgotten
- **Can't share highlights** - No easy way to extract and share the best parts

## The Solution

Transcribe is a multi-stage pipeline that:

1. **Downloads audio** - From YouTube or uses your local files
2. **Creates accurate transcripts** - Using OpenAI's Whisper API
3. **Formats for readability** - Smart paragraphs with clickable timestamps
4. **Extracts insights** - AI-powered summaries and key quotes (optional)
5. **Preserves everything** - Keeps audio files for offline listening

**The result**: Searchable, readable transcripts with insights you can reference forever.

## Quick Start

**Prerequisites**: Complete the [Amplifier setup instructions](../../README.md#-step-by-step-setup) first.

### Basic Usage

```bash
# Transcribe a YouTube video
python -m scenarios.transcribe "https://youtube.com/watch?v=..."

# Transcribe a local audio file
python -m scenarios.transcribe podcast.mp3
```

The tool will:
1. Download/extract the audio
2. Send it to Whisper API for transcription
3. Format into readable paragraphs
4. Generate AI insights (summary + quotes)
5. Save everything in organized folders

## Your First Transcript

### 1. Find a video to transcribe

Choose a YouTube video or prepare an audio file:
- YouTube: Copy the video URL
- Local file: Note the path to your .mp3, .mp4, .wav, etc.

### 2. Run the transcription

```bash
python -m scenarios.transcribe "https://youtube.com/watch?v=dQw4w9WgXcQ"
```

### 3. Watch the progress

The tool will show:
```
Downloading audio from YouTube...
Extracting audio (this may take a moment)...
Transcribing with Whisper API...
Formatting transcript into readable paragraphs...
Generating AI insights...
✓ Transcript saved to: ~/amplifier/transcripts/dQw4w9WgXcQ/
```

### 4. Explore the output

Navigate to your transcripts folder:
```
~/amplifier/transcripts/dQw4w9WgXcQ/
├── audio.mp3          # The audio file (for offline listening)
├── transcript.md      # Readable transcript with timestamps
└── insights.md        # AI summary and key quotes
```

### 5. Use your transcript

- **Read** the formatted transcript with clickable timestamps
- **Search** for specific topics or quotes
- **Listen** to the preserved audio file
- **Share** insights and quotes with proper citations
- **Reference** exact moments with timestamp links

## Usage Examples

### Basic: Single YouTube Video

```bash
python -m scenarios.transcribe "https://youtube.com/watch?v=..."
```

**What happens**:
- Downloads audio from YouTube
- Creates accurate transcript
- Formats into readable paragraphs
- Generates summary and quotes
- Saves everything for future reference

### Advanced: Multiple Sources

```bash
python -m scenarios.transcribe video1.mp4 "https://youtube.com/..." podcast.mp3
```

**What happens**:
- Processes each source sequentially
- Saves state between each item
- Creates separate folders for each
- Updates the transcript index
- Can resume if interrupted

### Resume Interrupted Session

```bash
# If interrupted, just add --resume
python -m scenarios.transcribe --resume video1.mp4 video2.mp4
```

**What happens**:
- Finds where you left off
- Skips already completed items
- Continues from interruption point
- Preserves all previous work

## How It Works

### The Pipeline

```
YouTube URL or Audio File
         ↓
    [Download/Extract Audio]
         ↓
    [Whisper Transcription]
         ↓
    [Format Paragraphs] ────→ transcript.md
         ↓
    [Generate Summary] ─────→ insights.md
         ↓
    [Update Index] ─────────→ index.md
```

### Key Components

- **Video Loader**: Downloads from YouTube using yt-dlp
- **Audio Extractor**: Compresses audio for API limits (25MB max)
- **Whisper Transcriber**: Calls OpenAI's speech-to-text API
- **Transcript Formatter**: Creates readable paragraphs with timestamps
- **Insights Generator**: AI summaries and quote extraction
- **State Manager**: Enables interrupt/resume capability

### Why It Works

**Code handles the structure**:
- Audio download and extraction
- API calls and retry logic
- File organization and caching
- State management for resume
- Error handling and recovery

**AI handles the intelligence**:
- Accurate speech transcription
- Summary generation
- Key quote identification
- Content understanding

This separation means reliable processing (code) with intelligent output (AI).

## Configuration

### Output Locations

**User Content** (`~/amplifier/transcripts/`):
- `index.md` - Auto-generated index of all transcripts
- `[video-id]/audio.mp3` - Preserved audio file
- `[video-id]/transcript.md` - Readable transcript
- `[video-id]/insights.md` - Summary and quotes

**Technical Artifacts** (`.data/transcripts/`):
- `[video-id]/transcript.json` - Structured data
- `[video-id]/transcript.vtt` - WebVTT subtitles
- `[video-id]/transcript.srt` - SRT subtitles

### Audio Caching

Audio files are automatically cached to save bandwidth:
- First run downloads and saves audio
- Subsequent runs use cached version
- Force re-download with `--force-download`

### Cost Estimation

OpenAI Whisper API pricing (as of 2024):
- $0.006 per minute of audio
- Example: 60-minute video = $0.36
- Cost shown before processing

## Troubleshooting

### "yt-dlp is not installed"

**Problem**: Missing YouTube download dependency.

**Solution**:
```bash
make install  # or: uv add yt-dlp
```

### "ffmpeg not found"

**Problem**: Audio processing tool not installed.

**Solution**:
- macOS: `brew install ffmpeg`
- Ubuntu: `sudo apt-get install ffmpeg`
- Windows: Download from ffmpeg.org

### "Audio file too large"

**Problem**: File exceeds 25MB API limit.

**Solution**: The tool auto-compresses. If it still fails, manually compress:
```bash
ffmpeg -i input.wav -b:a 64k -ar 16000 output.mp3
```

### "API key not found"

**Problem**: OpenAI/Anthropic API keys not configured.

**Solution**: Set in `.env` file:
```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

## Learn More

- **[HOW_TO_CREATE_YOUR_OWN.md](./HOW_TO_CREATE_YOUR_OWN.md)** - Create your own tool like this
- **[Amplifier](https://github.com/microsoft/amplifier)** - The framework that powers these tools
- **[Scenario Tools](../)** - More tools like this one

## What's Next?

This tool demonstrates what's possible when you describe a process to Amplifier:

1. **Use it** - Transcribe videos and build your knowledge library
2. **Learn from it** - See [HOW_TO_CREATE_YOUR_OWN.md](./HOW_TO_CREATE_YOUR_OWN.md) for how it was made
3. **Build your own** - Describe your goal to Amplifier
4. **Share back** - Let others learn from what you create!

---

**Built through conversation using Amplifier** - The entire tool came from describing the goal in natural language. See [HOW_TO_CREATE_YOUR_OWN.md](./HOW_TO_CREATE_YOUR_OWN.md) for the actual conversation.