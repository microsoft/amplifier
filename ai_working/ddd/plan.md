# DDD Plan: Recipe Extractor Tool

## Problem Statement

**What we're solving:**
Recipe enthusiasts have URLs scattered across bookmarks and notes, making it hard to:
- Access recipes quickly without navigating through ads and stories
- Scale recipes for different serving sizes
- Work with measurements they understand (metric vs imperial)
- Search their personal recipe collection

**User value:**
- Extract clean, portable recipes from 200+ recipe websites
- Store in searchable markdown format with rich metadata
- Auto-generate 1x, 2x, 3x scaled ingredient lists
- Convert volume measurements to weight (cups → grams/ml)
- Build personal recipe library for future search/organization

## Proposed Solution

**High-level approach:**
Create a command-line tool following the proven scenario tools pattern that:

1. **Fetches** recipe data from URL using `recipe-scrapers` library (supports 200+ sites)
2. **Converts** units using `pint` library (ingredient-aware conversions)
3. **Scales** ingredient lists to 1x, 2x, 3x quantities
4. **Formats** as clean markdown with structured YAML frontmatter
5. **Saves** to content directory with searchable metadata

**Tool signature:**
```bash
make recipe-extract URL=https://example.com/recipe
make recipe-extract URL=https://site1.com/r1 URL2=https://site2.com/r2
```

**Example output location:**
```
<first_content_dir>/recipes/
└── chocolate-chip-cookies.md  # Title-based slug
```

## Alternatives Considered

### Alternative 1: Custom HTML Parser
**Rejected because:**
- Violates ruthless simplicity (reinventing solved problem)
- Recipe sites change layouts frequently
- Would need to maintain parsers for 100+ sites
- `recipe-scrapers` library already solves this excellently

### Alternative 2: Simple conversion tables vs Pint library
**Chose Pint because:**
- Ingredient-aware (1 cup flour ≠ 1 cup sugar in grams)
- Handles complex unit conversions
- Extensible ingredient database
- Worth the dependency for accuracy

### Alternative 3: Multiple files per scale vs single file
**Chose single file because:**
- Everything in one place (better UX)
- Fewer files to manage
- Search returns one result per recipe
- Still organized with clear section headers

## Architecture & Design

### Key Interfaces ("Studs")

**1. Recipe Data Model (Pydantic):**
```python
class RecipeData:
    title: str
    source_url: str
    ingredients: list[Ingredient]
    instructions: list[str]
    prep_time: str | None
    cook_time: str | None
    servings: str | None
    tags: list[str]
    image_url: str | None
```

**2. Fetcher Interface:**
```python
def fetch_recipe(url: str) -> RecipeData:
    """Fetch structured recipe data from URL."""
```

**3. Converter Interface:**
```python
def convert_to_metric(ingredient: Ingredient) -> Ingredient:
    """Convert volume to weight where possible."""

def scale_ingredients(ingredients: list[Ingredient], multiplier: float) -> list[Ingredient]:
    """Scale all ingredients by multiplier."""
```

**4. Markdown Writer Interface:**
```python
def write_recipe_markdown(recipe: RecipeData, scales: list[float]) -> str:
    """Generate markdown with frontmatter and scaled sections."""
```

### Module Boundaries

**Fetcher Module** (`fetcher.py`):
- Responsibility: Get recipe data from URL
- Dependencies: `recipe-scrapers`, `httpx` (for retry)
- Output: RecipeData object

**Converter Module** (`converter.py`):
- Responsibility: Unit conversions and scaling math
- Dependencies: `pint` library
- Input: RecipeData
- Output: Scaled RecipeData variants

**Markdown Writer Module** (`markdown_writer.py`):
- Responsibility: Format to markdown
- Dependencies: None (pure Python)
- Input: RecipeData + scales
- Output: Markdown string with frontmatter

**State Module** (`state.py`):
- Responsibility: Track processed URLs for resume
- Dependencies: Amplifier state patterns
- Persist: `.data/recipe_extractor/state.json`

**Main Orchestrator** (`main.py`):
- Responsibility: CLI + pipeline coordination
- Dependencies: All modules above
- Pattern: Same as blog_writer/web_to_md

### Data Models

```python
# Core recipe data
class Ingredient:
    raw_text: str                    # "2 cups all-purpose flour"
    quantity: float | None           # 2.0
    unit: str | None                 # "cups"
    item: str                        # "all-purpose flour"
    metric_quantity: float | None    # 280 (grams)
    metric_unit: str | None          # "g"

class RecipeData:
    title: str
    source_url: str
    fetched_date: str
    ingredients: list[Ingredient]
    instructions: list[str]
    prep_time: str | None
    cook_time: str | None
    total_time: str | None
    servings: str | None
    description: str | None
    tags: list[str]
    image_url: str | None

# State tracking
class RecipeExtractorState:
    processed_urls: dict[str, bool]  # url -> success
    failed_urls: dict[str, str]      # url -> error message
    session_timestamp: str
```

## Files to Change

### Non-Code Files (Phase 2)

- [ ] `scenarios/recipe_extractor/README.md` - Create main documentation
- [ ] `scenarios/recipe_extractor/HOW_TO_CREATE_YOUR_OWN.md` - Create guide
- [ ] `scenarios/recipe_extractor/pyproject.toml` - Create with dependencies
- [ ] `scenarios/README.md` - Add recipe-extractor to featured tools list
- [ ] `Makefile` - Add recipe-extract command and help text
- [ ] `.gitignore` - Ensure `.data/recipe_extractor/` is ignored (already should be)

### Code Files (Phase 4)

- [ ] `scenarios/recipe_extractor/__init__.py` - Create package marker
- [ ] `scenarios/recipe_extractor/__main__.py` - Create CLI entry point
- [ ] `scenarios/recipe_extractor/main.py` - Create orchestrator with CLI
- [ ] `scenarios/recipe_extractor/fetcher.py` - Create recipe fetcher
- [ ] `scenarios/recipe_extractor/converter.py` - Create unit converter
- [ ] `scenarios/recipe_extractor/markdown_writer.py` - Create markdown formatter
- [ ] `scenarios/recipe_extractor/state.py` - Create state manager
- [ ] `scenarios/recipe_extractor/models.py` - Create Pydantic models

## Philosophy Alignment

### Ruthless Simplicity

**Start minimal:**
- Use proven libraries (`recipe-scrapers`, `pint`) instead of custom parsing
- Follow existing scenario tool patterns (no new patterns needed)
- Single command interface: `make recipe-extract URL=...`
- Flat file storage (no complex database)

**Avoid future-proofing:**
- NOT building search yet (future phase, separate tool)
- NOT downloading images initially (can add later if needed)
- NOT building recipe editing (markdown is editable anyway)
- NOT building meal planning features
- Start with common ingredients for conversions, expand as needed

**Clear over clever:**
- Straightforward pipeline: fetch → convert → scale → format → save
- Explicit ingredient sections (1x, 2x, 3x) over dynamic scaling
- YAML frontmatter for metadata (standard, greppable)
- Human-readable markdown output

### Modular Design

**Bricks (self-contained modules):**
- `fetcher.py` - Can work standalone, just returns RecipeData
- `converter.py` - Pure functions, no side effects, unit testable
- `markdown_writer.py` - String formatting, no external dependencies
- `state.py` - Isolated state management following Amplifier patterns

**Studs (clear interfaces):**
- RecipeData model (Pydantic) - Contract between modules
- Each module has single public function
- Type hints throughout for clarity
- No hidden dependencies between modules

**Regeneratable:**
- This spec defines complete behavior
- Each module can be rebuilt independently
- Contracts (Pydantic models) are source of truth
- Tests verify contracts, not implementation

## Test Strategy

### Unit Tests

**Converter module:**
```python
def test_scale_ingredients():
    # Test multiplying quantities correctly
    # Test handling missing units gracefully
    # Test metric conversion accuracy

def test_convert_to_metric():
    # Test cups to grams for common ingredients
    # Test handling unknown ingredients
    # Test preserving original when conversion unavailable
```

**Markdown writer:**
```python
def test_format_recipe():
    # Test YAML frontmatter generation
    # Test ingredient section formatting
    # Test instruction formatting
    # Test handling missing/optional fields
```

**Fetcher:**
```python
def test_fetch_recipe():
    # Test with mock recipe-scrapers response
    # Test error handling for unsupported sites
    # Test retry logic for network failures
```

### Integration Tests

**End-to-end:**
```python
def test_recipe_extraction_pipeline():
    # Test with real recipe URL (cached response)
    # Verify markdown output structure
    # Verify all sections present
    # Verify file saved to correct location
```

**State management:**
```python
def test_resume_capability():
    # Test state save after success
    # Test resume skips already processed
    # Test failed URL tracking
```

### User Testing (Phase 5)

**As actual user, test:**
1. Extract recipe from AllRecipes.com (most common)
2. Extract recipe from NYT Cooking (paywall detection)
3. Extract recipe from personal blog (less structured)
4. Verify 1x/2x/3x sections are correct
5. Verify metric conversions are accurate
6. Test resume after interruption
7. Test multiple URLs in one command
8. Verify markdown is readable and searchable

## Implementation Approach

### Phase 2 (Docs)

**Documentation to create:**
1. `scenarios/recipe_extractor/README.md`:
   - Problem it solves
   - Quick start examples
   - Command options
   - Output structure
   - Troubleshooting

2. `scenarios/recipe_extractor/HOW_TO_CREATE_YOUR_OWN.md`:
   - What problem you described
   - What thinking process you shared
   - How Amplifier implemented it
   - Pattern you can reuse

3. Update `scenarios/README.md`:
   - Add recipe-extractor to featured tools
   - Show it in the philosophy examples

4. Update `Makefile`:
   - Add recipe-extract command
   - Add help text
   - Follow pattern from blog-write and web-to-md

5. Create `pyproject.toml`:
   - Dependencies: recipe-scrapers, pint, httpx, click
   - Package metadata
   - Entry points

### Phase 4 (Code)

**Implementation order:**

**Chunk 1: Models + State (foundation):**
- `models.py` - Pydantic models (Ingredient, RecipeData)
- `state.py` - State management (following existing patterns)
- Tests for models

**Chunk 2: Fetcher (data acquisition):**
- `fetcher.py` - Recipe fetching with retry logic
- Integration with recipe-scrapers library
- Error handling for unsupported sites
- Tests with mocked responses

**Chunk 3: Converter (unit math):**
- `converter.py` - Pint-based conversions
- Ingredient database (start with 10-20 common ones)
- Scaling logic
- Unit tests for accuracy

**Chunk 4: Markdown Writer (formatting):**
- `markdown_writer.py` - Format to markdown
- YAML frontmatter generation
- Scaled ingredient sections (1x, 2x, 3x)
- Instruction formatting
- Unit tests for output structure

**Chunk 5: Orchestrator (CLI + pipeline):**
- `main.py` - CLI using Click
- Pipeline coordination
- State integration
- Progress logging
- Error reporting

**Chunk 6: Entry points:**
- `__init__.py` - Package marker
- `__main__.py` - CLI entry point
- Makefile integration

**Dependencies between chunks:**
- 1 → all (models used everywhere)
- 2, 3, 4 → independent (can build in parallel after 1)
- 5 → 1, 2, 3, 4 (orchestrates everything)
- 6 → 5 (final integration)

## Success Criteria

**Feature complete when:**
- [ ] Can extract recipe from 200+ supported sites via URL
- [ ] Generates clean markdown with YAML frontmatter
- [ ] Shows 1x, 2x, 3x ingredient sections
- [ ] Converts common measurements to metric (cups → grams)
- [ ] Saves to content directory with slug-based filename
- [ ] Handles multiple URLs in one command
- [ ] Can resume after interruption
- [ ] Shows clear progress and error messages

**Quality verified when:**
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Actual recipe extraction works end-to-end
- [ ] Scaled ingredients are mathematically correct
- [ ] Metric conversions are accurate for common ingredients
- [ ] Output markdown is readable and properly formatted
- [ ] Follows philosophy: ruthless simplicity + modular design
- [ ] Documented with examples and troubleshooting

**User testing complete when:**
- [ ] Extracted 5+ recipes from different sites successfully
- [ ] Verified 1x/2x/3x sections are accurate
- [ ] Verified metric conversions make sense
- [ ] Confirmed resume works after interruption
- [ ] Tested with both common and edge-case sites

## Next Steps

✅ **Phase 1 Complete: Planning Approved**

**Ready for Phase 2: Documentation Retcon**

The plan provides complete guidance for:
- What non-code files to create/update
- What documentation structure to follow
- What examples to include
- What philosophy principles to emphasize

Run: `/ddd:2-docs` to begin updating all documentation.

---

**Plan Version:** 1.0
**Created:** 2025-01-09
**Last Updated:** 2025-01-09
**Status:** Awaiting user approval
