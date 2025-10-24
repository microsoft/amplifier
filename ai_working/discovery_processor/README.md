# Discovery Content Processor

AI-powered content understanding for the Discovery canvas. Processes images, documents, URLs, and canvas drawings to extract insights and design elements.

## Purpose

Enable the Discovery canvas to understand dropped content:
- **Napkin sketches** → Extract design intent, layouts, and visual elements
- **Documents** → Analyze PDFs, Word docs, Excel sheets, presentations
- **URLs** → Fetch and analyze web content for design inspiration
- **Canvas drawings** → Understand user sketches drawn directly on canvas

## Features

- ✅ **Claude Vision API Integration** - Analyze images and sketches with AI
- ✅ **Multi-Format Support** - Images, PDFs, Office docs, URLs
- ✅ **Progress Tracking** - Resume interrupted processing sessions
- ✅ **Batch Processing** - Handle multiple files efficiently
- ✅ **Design Element Extraction** - Colors, typography, layouts, interactions
- ✅ **Session Management** - File-based storage for reliability

## Installation

Ensure dependencies are installed:
```bash
# Install required Python packages
pip install claude-code-sdk httpx beautifulsoup4 click

# The module uses these from the amplifier project:
# - amplifier.ccsdk_toolkit
```

## Usage

### Basic Usage

```bash
# Process a single image
python -m ai_working.discovery_processor.cli image.png

# Process a single URL
python -m ai_working.discovery_processor.cli https://dribbble.com/shots/...

# Process all files in a directory
python -m ai_working.discovery_processor.cli ./uploads/

# Process with custom output directory
python -m ai_working.discovery_processor.cli ./uploads/ --output ./results/
```

### Options

```bash
# Specify output directory
python -m ai_working.discovery_processor.cli input_path --output discovery_output

# Specify session file location (for progress tracking)
python -m ai_working.discovery_processor.cli input_path --session-file session.json

# Resume existing session by ID
python -m ai_working.discovery_processor.cli input_path --session-id abc-123

# Clear previous session and start fresh
python -m ai_working.discovery_processor.cli input_path --clear-session

# Disable Vision API (faster but less insightful)
python -m ai_working.discovery_processor.cli input_path --no-vision-api

# Set timeout for processing
python -m ai_working.discovery_processor.cli input_path --timeout 600

# Verbose output for debugging
python -m ai_working.discovery_processor.cli input_path --verbose
```

### Python API

```python
from ai_working.discovery_processor import (
    ImageProcessor,
    ContentItem,
    ContentType,
    ProcessorConfig,
    SessionManager
)

# Create a content item
item = ContentItem(
    id="unique-id",
    type=ContentType.IMAGE,
    source_path="/path/to/sketch.png",
    file_name="sketch.png",
    mime_type="image/png",
    size_bytes=123456
)

# Configure processor
config = ProcessorConfig(
    use_vision_api=True,
    extract_colors=True,
    extract_typography=True,
    max_file_size_mb=50
)

# Process the item
processor = ImageProcessor(config)
if await processor.can_process(item):
    result = await processor.process(item, config)
    print(result.analysis)
    print(result.insights)
    print(result.design_elements)
```

## Module Architecture

```
discovery_processor/
├── core/                    # Core protocol and base classes
│   ├── __init__.py         # Public exports
│   └── processor.py        # BaseProcessor, ContentProcessor protocol
├── processors/             # Content processors
│   ├── __init__.py         # Public exports
│   ├── image.py           # Vision API for images/sketches
│   ├── url.py             # Web content fetching
│   ├── document.py        # PDF/Office parsing (placeholder)
│   └── canvas.py          # Drawing interpretation (placeholder)
├── session/                # Progress tracking
│   ├── __init__.py         # Public exports
│   └── manager.py          # SessionManager for file storage
├── models.py               # Shared data structures
├── cli.py                  # Command-line interface
├── __init__.py            # Module exports
└── README.md              # This file
```

## Data Models

### ContentItem

Represents a piece of content dropped into Discovery canvas:

```python
@dataclass
class ContentItem:
    id: str                          # Unique identifier
    type: ContentType                # IMAGE, DOCUMENT, URL, CANVAS_DRAWING
    source_path: str                 # File path or URL
    file_name: str                   # Display name
    mime_type: str | None            # MIME type
    size_bytes: int | None           # File size
    created_at: datetime             # When added
    metadata: dict[str, Any]         # Additional metadata
```

### ProcessingResult

Result of processing a content item:

```python
@dataclass
class ProcessingResult:
    content_id: str                  # ID of content processed
    status: ProcessingStatus         # COMPLETED, FAILED, etc.
    analysis: str                    # AI analysis text
    extracted_text: str              # Text extracted from content
    insights: list[str]              # Key insights
    design_elements: dict            # Colors, layouts, etc.
    warnings: list[str]              # Any warnings
    error_message: str | None        # Error if failed
    processing_time_ms: int          # Processing duration
    processed_at: datetime           # When completed
```

## Content Processors

### ImageProcessor

Analyzes images using Claude Vision API:
- ✅ Napkin sketches and hand-drawn diagrams
- ✅ Design mockups and screenshots
- ✅ Photos of whiteboards
- ✅ Digital diagrams and wireframes

**Supported formats**: JPG, PNG, GIF, WebP

**Example analysis output**:
```
Design Intent: Mobile app onboarding flow with 3 steps
Visual Elements:
  - Layout: Vertical card stack with centered content
  - Colors: Primary blue (#4A90E2), neutral grays
  - Typography: San-serif headings, 24px body text
Key Insights:
  - Progressive disclosure pattern
  - Thumb-friendly button placement
  - Clear visual hierarchy
```

### URLProcessor

Fetches and analyzes web content:
- ✅ Design inspiration sites
- ✅ Documentation and references
- ✅ Design system examples
- ✅ Product websites

**Example analysis output**:
```
Purpose: Portfolio showcasing minimalist product design
Design Patterns:
  - Grid-based layout with 3-column structure
  - Generous whitespace (Swedish minimalism)
  - Subtle hover animations (scale 1.02x)
Key Takeaways:
  - Use of negative space to direct attention
  - Consistent 8px spacing system
  - Mobile-first responsive approach
```

### DocumentProcessor (Placeholder)

Will handle:
- PDF documents and specifications
- Word documents with requirements
- Excel spreadsheets with data
- PowerPoint presentations

**Status**: Placeholder implementation. Future phases will add:
- PyPDF2 or pdfplumber for PDFs
- python-docx for Word documents
- openpyxl for Excel spreadsheets
- python-pptx for PowerPoint

### CanvasDrawingProcessor (Placeholder)

Will handle drawings created directly on canvas:
- User sketches with canvas tools
- Annotations and markup
- Quick diagrams and flows

**Status**: Placeholder implementation. Future phases will:
1. Convert canvas state to image format
2. Use Vision API to analyze the drawing
3. Identify shapes, annotations, flows
4. Extract text from labels

## Session Management

The tool tracks progress in a session file, enabling:
- **Resume capability**: Restart interrupted processing
- **Skip processed files**: Automatically skip completed items
- **Batch reliability**: Continue even if individual items fail

**Default behavior**:
- Session file: `discovery_session.json` in current directory
- Custom location: Use `--session-file` option
- Clear session: Use `--clear-session` flag

**Session data includes**:
```json
{
  "session_id": "abc-123-def",
  "processed_items": ["item-1", "item-2"],
  "results": [...],
  "failed_items": [],
  "total_items": 10,
  "started_at": "2024-10-20T12:00:00",
  "updated_at": "2024-10-20T12:05:00"
}
```

## Performance

- **Image processing**: ~2-5 seconds per image (Vision API)
- **URL fetching**: ~1-3 seconds per URL
- **Memory usage**: Minimal, processes one item at a time
- **Disk I/O**: Incremental saves after each item

## Error Handling

The processor handles several scenarios:
1. **Parse failures** - Logs error and continues
2. **Processing failures** - Marks item as failed, continues
3. **Network timeouts** - Configurable timeout with retry
4. **File I/O errors** - Retry with exponential backoff

## Vision API Integration

The image processor uses Claude's Vision API to analyze visual content:

**Analysis focuses on**:
1. **Design Intent** - What is this trying to solve?
2. **Visual Elements** - Layout, colors, typography, spacing
3. **Interactions** - User flows, states, interactions
4. **Key Insights** - What makes this design interesting?
5. **Design Patterns** - Recognizable UI conventions

**For low-fidelity sketches**:
- Focus on structure and intent over polish
- Identify key functional areas
- Note annotations and labels

**For high-fidelity mockups**:
- Extract specific design choices
- Identify component types
- Note unique design decisions

## Integration with Studio Interface

The Discovery canvas will use this processor via Next.js API routes:

```typescript
// studio-interface/app/api/discovery/process/route.ts
import { ImageProcessor, ContentItem } from '@/lib/discovery-processor'

export async function POST(request: Request) {
  const { contentItem } = await request.json()

  const processor = new ImageProcessor()
  const result = await processor.process(contentItem)

  return Response.json(result)
}
```

See "Next Steps" section for frontend integration details.

## Limitations

**Current Phase**:
- ✅ Image processing with Vision API - **Fully implemented**
- ✅ URL fetching and analysis - **Fully implemented**
- ⚠️  Document processing - **Placeholder** (needs PDF/Office parsers)
- ⚠️  Canvas drawing analysis - **Placeholder** (needs canvas-to-image conversion)

**Vision API**:
- Requires `claude` CLI installed and configured
- Network connectivity required
- May have rate limits or costs

**File Size**:
- Default max: 50MB per file
- Configurable via `max_file_size_mb`

## Testing

Test the processor with sample content:

```bash
# Test with a sample image
python -m ai_working.discovery_processor.cli test-sketch.png --verbose

# Test with a URL
python -m ai_working.discovery_processor.cli https://dribbble.com/shots/123456 --verbose

# Test batch processing
python -m ai_working.discovery_processor.cli ./test-uploads/ --verbose
```

## Next Steps

1. **Frontend Integration**:
   - Create Next.js API routes in `studio-interface/app/api/discovery/`
   - Add drop zone handling in Discovery canvas
   - Display processing results in UI
   - Integrate with Supabase for project storage

2. **Document Processing**:
   - Add PyPDF2/pdfplumber for PDF parsing
   - Add python-docx for Word documents
   - Add openpyxl for Excel spreadsheets
   - Add python-pptx for PowerPoint

3. **Canvas Drawing Analysis**:
   - Implement canvas state to image conversion
   - Use Vision API for drawing analysis
   - Extract shapes and annotations
   - Identify user intent from sketches

4. **Enhanced Analysis**:
   - Color palette extraction
   - Typography identification
   - Layout grid detection
   - Component recognition

## Regeneration Specification

This module can be fully regenerated from this specification:

**Core Protocol**:
- `BaseProcessor` - Abstract base with common functionality
- `ContentProcessor` - Protocol for processor implementations
- Each processor handles specific content types

**Processor Bricks**:
- `ImageProcessor` - Vision API integration
- `URLProcessor` - Web content fetching
- `DocumentProcessor` - Document parsing
- `CanvasDrawingProcessor` - Drawing analysis

**Session Brick**:
- `SessionManager` - Progress tracking and resume capability
- File-based storage with JSON serialization
- Incremental saves after each item

**CLI**:
- Orchestrates processors
- Handles batch processing
- Provides progress feedback

The module follows "bricks and studs" philosophy - each component is self-contained with clear interfaces.

## License

Part of the Amplified Design project.
