# AI Working Directory

**Purpose:** Workspace for AI tools specific to the Amplified Design project (Studio).

This follows the pattern established in `amplifier/ai_working/` but contains tools specific to Studio features rather than general-purpose amplifier tools.

## Philosophy

This directory is **NOT dot-prefixed** to allow easy reference by AI tools like Claude Code. See `amplifier/ai_working/README.md` for the pattern origin.

**From amplifier/ai_working/README.md:**
> The purpose of this directory is to provide a working space for AI-tools to create, modify, and execute plans for implementing changes in a project. It serves as a collaborative space where AI can generate plans, execute them, and document the process for future reference.

## Structure

```
ai_working/
├── discovery_processor/   # Processes content for Studio Discovery canvas
│   ├── core/              # Core processing logic
│   ├── processors/        # Content type processors
│   ├── session/           # Session management
│   ├── models.py          # Data models
│   ├── cli.py             # Command-line interface
│   └── README.md          # Tool documentation
└── tmp/                   # Temporary files (gitignored)
```

## Tools

### discovery_processor

**Purpose:** AI-powered content understanding for the Studio Discovery canvas.

**Processes:**
- Napkin sketches → Extract design intent, layouts, visual elements
- Documents → Analyze PDFs, Word docs, Excel sheets, presentations
- URLs → Fetch and analyze web content for design inspiration
- Canvas drawings → Understand user sketches drawn directly on canvas

**Usage:**
```bash
# From amplified-design/ root directory
python -m ai_working.discovery_processor.cli <file>

# With session management
python -m ai_working.discovery_processor.cli image.png \
  --session-file ./session.json \
  --session-id abc123 \
  --output ./output/

# Get help
python -m ai_working.discovery_processor.cli --help
```

**Used By:**
- `studio-interface/app/api/discovery/process/route.ts` - API endpoint for canvas content processing

**See:** [discovery_processor/README.md](./discovery_processor/README.md) for complete documentation.

---

## Usage Patterns

### From Studio Interface API Routes

```typescript
// studio-interface/app/api/discovery/process/route.ts
import { spawn } from 'child_process';
import { join } from 'path';

const projectRoot = join(process.cwd(), '..');  // Points to amplified-design/

const python = spawn('python3', [
  '-m',
  'ai_working.discovery_processor.cli',
  filePath,
  '--session-file', sessionFile,
  '--session-id', sessionId,
], {
  cwd: projectRoot,  // Run from amplified-design/ root
  env: { ...process.env, PYTHONPATH: projectRoot },
});
```

### From Command Line

```bash
# Navigate to project root
cd /path/to/amplified-design

# Run tool
python3 -m ai_working.discovery_processor.cli ./sketch.png
```

### From Python Scripts

```python
# Import from amplified-design/ root
from ai_working.discovery_processor import models, cli
from amplifier.ccsdk_toolkit import parse_llm_json  # Amplifier still accessible

# Use the tools
result = cli.process_file('sketch.png')
```

---

## Adding New Tools

When adding new Studio-specific AI tools:

1. **Create tool directory** in `ai_working/`
2. **Follow Python package structure:**
   ```
   new_tool/
   ├── __init__.py
   ├── cli.py          # Command-line interface
   ├── models.py       # Data models
   ├── core/           # Core logic
   └── README.md       # Documentation
   ```
3. **Use amplifier patterns:**
   - Session management (file-based state)
   - Progress tracking (resume capability)
   - Error handling (graceful failures)
   - Logging (structured, informative)
4. **Import from amplifier when useful:**
   ```python
   from amplifier.ccsdk_toolkit import parse_llm_json, AnthropicSession
   ```
5. **Document in this README**
6. **Add tests** in `tests/ai_working/new_tool/`

---

## Temporary Files

The `tmp/` directory is for temporary files that should NOT be version-controlled:

**Use for:**
- Intermediate processing files
- Cache files
- Test output
- Scratch work

**Gitignored:** Yes (see `.gitignore`)

**For version-controlled working files**, place them in tool-specific directories or create task-specific subdirectories.

---

## Separation from Amplifier

### What Goes in amplified-design/ai_working/?
- **Studio-specific tools** (Discovery canvas, design generation, etc.)
- **Project-specific workflows** (Hawks Nest design flow, etc.)
- **Integration tools** (connecting Studio to external services)

### What Stays in amplifier/ai_working/?
- **General-purpose tools** (dot_to_mermaid graph conversion)
- **Amplifier analysis** (adaptive evolution, ccsdk-toolkit docs)
- **Infrastructure documentation** (decision records, analysis)

**Rule of Thumb:** If it mentions "Studio", "Discovery canvas", "Hawks Nest", or specific amplified-design features → it goes here. If it's reusable across any ccsdk project → it goes in amplifier.

---

## Migration Notes

### Discovery Processor Migration (2025-10-23)

The `discovery_processor` tool was migrated from `amplifier/ai_working/` to `amplified-design/ai_working/` because:

1. It's Studio-specific (processes content for Discovery canvas)
2. It references Studio features and UI elements
3. It's tightly coupled with `studio-interface/` API routes
4. Amplifier should remain general-purpose (design principle)

**Old Location:** `amplifier/ai_working/discovery_processor/` (copy remains for reference)
**New Location:** `ai_working/discovery_processor/` (active version)

**Code Updated:**
- `studio-interface/app/api/discovery/process/route.ts` - Module path updated to reference new location

**Note:** The copy in `amplifier/ai_working/` cannot be deleted (read-only submodule) but is deprecated.

---

## Dependencies

Tools in this directory may use:

**From amplifier:**
- `amplifier.ccsdk_toolkit` - Claude Code SDK utilities (parse_llm_json, AnthropicSession, etc.)
- General-purpose amplifier tools

**External packages:**
- `claude-code-sdk` (ccsdk) - Claude Code development kit
- `httpx` - HTTP client
- `beautifulsoup4` - HTML parsing
- `click` - CLI framework
- Others as needed per tool

**Installation:**
```bash
# From amplified-design/ root
pip install claude-code-sdk httpx beautifulsoup4 click

# Or use requirements.txt if created
pip install -r requirements.txt
```

---

## Questions?

- **For amplifier AI working pattern:** See `amplifier/ai_working/README.md`
- **For discovery_processor:** See `ai_working/discovery_processor/README.md`
- **For Studio integration:** See `studio-interface/README.md` and `CLAUDE.md`
- **For design philosophy:** See `FRAMEWORK.md`, `PHILOSOPHY.md`, `PRINCIPLES.md`

---

**The artifact is the container. The tool is the means. The experience is the product.**

Design tools that serve humans, not screens.
