# Recipe Extractor

**Transform recipe URLs into clean, searchable markdown files with automatic scaling and unit conversions.**

---

## What It Does

The Recipe Extractor fetches recipes from 200+ recipe websites, extracts the essential information, and saves them as clean markdown files with:

- **Automatic scaling**: 1x, 2x, and 3x ingredient sections for easy recipe scaling
- **Unit conversions**: Volume measurements (cups, tablespoons) converted to weight (grams, ml)
- **Rich metadata**: YAML frontmatter with tags, timing, and source information for future search
- **Resumable processing**: Checkpoint system saves progress and skips already-processed URLs

Perfect for building a personal recipe library from scattered bookmarks and recipe sites.

---

## Quick Start

Extract a single recipe:

```bash
make recipe-extract URL=https://www.allrecipes.com/recipe/10813/best-chocolate-chip-cookies/
```

Extract multiple recipes:

```bash
make recipe-extract URL=https://example.com/recipe1 URL2=https://example.com/recipe2
```

Recipes are saved to your first content directory under `recipes/`:

```
<content_dir>/recipes/
├── best-chocolate-chip-cookies.md
├── classic-banana-bread.md
└── homemade-pizza-dough.md
```

---

## How It Works

The Recipe Extractor follows a simple pipeline:

```
URL
 ↓
[Fetch Recipe] → Uses recipe-scrapers library (200+ sites supported)
 ↓
[Parse & Structure] → Extracts title, ingredients, instructions, metadata
 ↓
[Convert Units] → Cups/tbsp → grams/ml (ingredient-aware)
 ↓
[Scale Ingredients] → Generates 1x, 2x, 3x sections
 ↓
[Format Markdown] → YAML frontmatter + scaled sections + instructions
 ↓
[Save to Content Directory] → recipes/recipe-name.md
```

### Supported Sites

The tool uses the `recipe-scrapers` library which supports 200+ recipe websites including:

- AllRecipes
- Food Network
- Bon Appétit
- Serious Eats
- NYT Cooking
- Budget Bytes
- And many more...

### Unit Conversion

Conversions are ingredient-aware using the `pint` library:

- 1 cup all-purpose flour = 120g
- 1 cup granulated sugar = 200g
- 1 cup butter = 227g
- 1 tablespoon = 15ml

Volume measurements are converted to weight where possible for precision baking.

---

## Output Structure

Each recipe is saved as a markdown file with:

### YAML Frontmatter

```yaml
---
title: Classic Chocolate Chip Cookies
source_url: https://www.allrecipes.com/recipe/10813/
fetched_date: 2025-01-09
tags: [dessert, cookies, baking]
prep_time: 15 minutes
cook_time: 12 minutes
total_time: 27 minutes
servings: 24 cookies
description: The best chocolate chip cookie recipe with a crispy edge...
---
```

### Content Structure

```markdown
# Classic Chocolate Chip Cookies

The best chocolate chip cookie recipe with a crispy edge...

## Ingredients

### 1x (24 cookies)
- 2¼ cups (280g) all-purpose flour
- 1 cup (227g) butter, softened
- ¾ cup (150g) granulated sugar
- ...

### 2x (48 cookies)
- 4½ cups (560g) all-purpose flour
- 2 cups (454g) butter, softened
- 1½ cups (300g) granulated sugar
- ...

### 3x (72 cookies)
- 6¾ cups (840g) all-purpose flour
- 3 cups (681g) butter, softened
- 2¼ cups (450g) granulated sugar
- ...

## Instructions

1. Preheat oven to 375°F (190°C).
2. In a large bowl, cream together the butter and both sugars...
3. ...
```

---

## Command Reference

### Basic Usage

```bash
# Single URL
make recipe-extract URL=<recipe-url>

# Multiple URLs (up to 5)
make recipe-extract URL=<url1> URL2=<url2> URL3=<url3>
```

### State Management

The tool maintains state in `.data/recipe_extractor/state.json` to:

- Track successfully processed URLs
- Skip already-extracted recipes on re-run
- Record failed URLs with error messages
- Enable resumable batch processing

To see what's been processed:

```bash
cat .data/recipe_extractor/state.json
```

---

## Troubleshooting

### "URL not supported"

The recipe-scrapers library supports 200+ sites, but some recipe sites may not be supported. Check the [recipe-scrapers documentation](https://github.com/hhursev/recipe-scrapers) for the full list of supported sites.

### "Unit conversion failed"

Some ingredients may not have known conversions (e.g., "1 can of tomatoes"). The tool preserves the original measurement in these cases.

### "Missing ingredients or instructions"

Some recipe websites have non-standard formatting. The tool extracts what it can and logs warnings for missing data.

### Resume After Interruption

If processing is interrupted:

```bash
# Simply re-run the same command
make recipe-extract URL=<url1> URL2=<url2> ...
```

The tool automatically skips already-processed URLs.

---

## Philosophy Alignment

### Ruthless Simplicity

- **Uses proven libraries**: `recipe-scrapers` (200+ sites) instead of custom parsing
- **Flat storage**: Simple directory structure with rich tagging instead of complex hierarchy
- **Single command**: One `make recipe-extract` command for all use cases
- **No over-engineering**: Focuses on fetch, parse, save - search comes later when needed

### Modular Design

- **Clear module boundaries**: Fetcher, converter, markdown writer, state manager
- **Regeneratable**: Each module follows the plan's spec and can be rebuilt independently
- **Testable**: Unit tests for conversion logic, integration tests for full pipeline

### Honest Documentation

- **Real limitations**: Documents known conversion limitations upfront
- **Actual examples**: All examples shown are tested and work
- **No future-proofing**: Describes what exists now, not what might be added

---

## Implementation Notes

Built following Document-Driven Development (DDD) methodology:

- **Documentation first**: This README was written before code
- **Code matches docs**: Implementation follows this specification exactly
- **Retcon approach**: Docs describe present state, not evolution

See `HOW_TO_CREATE_YOUR_OWN.md` for the creation process.

---

## Related Tools

- [web-to-md](../web_to_md/) - General web page to markdown converter
- [blog-writer](../blog_writer/) - Transform ideas into polished blog posts

---

**Return to**: [Scenarios Overview](../README.md)
