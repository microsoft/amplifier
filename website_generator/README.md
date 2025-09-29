# Automated Website Generator Tool

This tool automatically generates high-quality, paradigm-aware websites for repositories, inspired by the successful Amplifier instructor website transformation.

## Overview

The website generator analyzes repositories to detect paradigm shifts and generates appropriate content:
- **Revolutionary Change** (like Amplifier) → Full paradigm transformation content
- **Evolutionary Change** → Focus on improvements and enhancements
- **Incremental Change** → Standard feature documentation

## Key Features

- Repository structure and capability analysis
- Paradigm shift detection algorithm
- Automated content generation with progressive disclosure
- Consistent design system and CSS generation
- Nightly automation with change detection
- Configuration-driven consistency preservation

## Usage

```bash
# Generate website for any repository
website_generator generate --repo /path/to/project --output ./website

# Set up nightly automation
website_generator watch --repo /path/to/project --schedule nightly

# Regenerate with consistency validation
website_generator regenerate --repo /path/to/project --validate-consistency
```

## Architecture

- `src/analyzer/` - Repository analysis and paradigm detection
- `src/content/` - Content generation and template processing
- `src/style/` - CSS generation and component building
- `src/website/` - Site orchestration and asset management
- `src/automation/` - Change detection and scheduling
- `config/` - YAML configuration templates
- `templates/` - HTML templates and sections
- `assets/` - CSS, JavaScript, and other assets

## Implementation Status

- [x] Project structure created
- [ ] Repository analyzer implementation
- [ ] Paradigm shift detection
- [ ] Configuration system
- [ ] Template engine
- [ ] Content generation
- [ ] Automation and scheduling