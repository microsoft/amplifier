# Web To MD - Web to Markdown Converter

A modular tool that converts web pages to clean, organized markdown files with AI enhancement.

## Features

- **Fetch & Convert**: Downloads web pages and converts HTML to clean markdown
- **Paywall Detection**: Automatically detects and rejects content behind paywalls or authentication walls
- **Image Handling**: Downloads and saves images locally with updated references
- **AI Enhancement**: Uses Claude to improve markdown formatting and structure
- **Domain Organization**: Automatically organizes pages by domain
- **Resume Support**: Can resume interrupted sessions
- **Index Generation**: Creates an index of all converted pages

## Installation

```bash
# Navigate to the web_to_md directory
cd scenarios/web_to_md

# Install dependencies using uv
uv add markdownify httpx beautifulsoup4 pyyaml click

# Or install as a package
pip install -e .
```

## Usage

### Using the Makefile (Recommended)

When working in the Amplifier workspace, the easiest way to use the tool is via make:

```bash
# Convert a single page
make web-to-md URL=https://example.com/article

# Convert multiple pages
make web-to-md URL=https://example.com/page1 URL2=https://example.com/page2

# Custom output directory
make web-to-md URL=https://example.com OUTPUT=./my-sites
```

The makefile command automatically uses your Amplifier configuration for content and data directories.

### Direct Python Usage

Convert a single web page:

```bash
python -m web_to_md --url https://example.com/article
```

### Multiple URLs

Convert multiple pages at once:

```bash
python -m web_to_md --url https://example.com/page1 --url https://example.com/page2
```

### Custom Output Directory

Specify where to save the converted files:

```bash
python -m web_to_md --url https://example.com --output ./my-sites
```

### Resume Interrupted Session

Continue from where you left off:

```bash
python -m web_to_md --url https://example.com/page1 --resume
```

### Verbose Output

See detailed processing information:

```bash
python -m web_to_md --url https://example.com --verbose
```

## Output Structure

The tool organizes converted pages by domain in a `sites/` subdirectory:

**When Amplifier is available:**
- Content: `<first_content_dir>/sites/` (from `AMPLIFIER_CONTENT_DIRS`)
- State: `.data/web_to_md/state.json` (from `AMPLIFIER_DATA_DIR`)

**Standalone mode:**
- Content: `./sites/` (current directory)
- State: `./sites/.web_to_md_state.json`

```
sites/
├── example.com/
│   ├── article.md
│   ├── about.md
│   └── images/
│       ├── img_a1b2c3d4.jpg
│       └── img_e5f6g7h8.png
├── another-site.org/
│   ├── post.md
│   └── images/
│       └── img_i9j0k1l2.gif
└── index.md
```

## Module Architecture

The tool is built with a modular architecture where each module has a single responsibility:

- **`fetcher/`**: Downloads web pages with retry logic
- **`converter/`**: Converts HTML to markdown using markdownify
- **`validator/`**: Detects paywalls and authentication walls
- **`image_handler/`**: Downloads and manages images
- **`enhancer/`**: Enhances markdown with AI (when available)
- **`organizer/`**: Manages file organization by domain
- **`indexer/`**: Generates index of all saved pages
- **`state.py`**: Tracks processing state for resume capability

## Markdown Enhancement

When the Claude Code SDK is available, the tool will:

1. Add YAML frontmatter with metadata
2. Improve heading hierarchy
3. Clean up formatting issues
4. Enhance link and list formatting

If the SDK is not available, basic formatting improvements are still applied.

## State Management

The tool saves its state for resumable processing:

**Amplifier mode:** `.data/web_to_md/state.json` (centralized data directory)
**Standalone mode:** `<output_dir>/.web_to_md_state.json` (alongside content)

The state file tracks:
- Successfully processed URLs
- Failed URLs with error messages
- Session timestamps

This allows you to resume processing if interrupted with the `--resume` flag.

## Error Handling

- **Paywall Detection**: Automatically detects and rejects content behind paywalls or authentication walls
  - Detects "member-only" content (Medium, Substack, etc.)
  - Identifies pages with excessive authentication prompts
  - Validates minimum content length to catch incomplete pages
  - Prevents saving partial/teaser content
- **Retry Logic**: Automatic retries with exponential backoff for network errors
- **Partial Failure**: Continues processing other URLs even if one fails
- **Cloud Sync Support**: Handles file I/O errors from OneDrive/Dropbox with retries
- **Graceful Degradation**: Falls back to basic processing if AI enhancement fails

## Examples

### Convert a blog and organize by domain

```bash
python -m web_to_md \
  --url https://blog.example.com/post1 \
  --url https://blog.example.com/post2 \
  --url https://news.example.com/article \
  --verbose
```

Output structure:
```
sites/
├── blog.example.com/
│   ├── post1.md
│   ├── post2.md
│   └── images/
├── news.example.com/
│   ├── article.md
│   └── images/
└── index.md
```

### Resume after interruption

```bash
# First run (gets interrupted)
python -m web_to_md --url https://example.com/page1 --url https://example.com/page2

# Resume where it left off
python -m web_to_md --url https://example.com/page1 --url https://example.com/page2 --resume
```

## Amplifier Integration

When running in the Amplifier workspace, the tool automatically integrates with:

**Path Configuration:**
- Reads content directories from `amplifier.config.paths`
- Stores state in centralized data directory
- Organizes output consistently with other Amplifier tools

**Standalone Mode:**
- Falls back to current directory if Amplifier is not available
- Stores state alongside content
- Fully functional without Amplifier dependencies

## Requirements

- Python 3.11+
- Dependencies listed in `pyproject.toml`

## License

Part of the Amplifier toolkit.