# Review Prompts

This directory contains customizable prompts for the review modules.

Advanced users can modify these to adjust how the tool analyzes repositories.

## Available Prompts

- `grounding_review.txt` - Template for grounding review
- `philosophy_review.txt` - Template for philosophy alignment review
- `completeness_review.txt` - Template for completeness assessment

## How to Customize

1. Copy the prompt file you want to modify
2. Edit the template, keeping the JSON structure requirements
3. The tool will automatically use custom prompts if present

## Variables Available

All prompts have access to:
- `{source_content}` - Source repository content
- `{target_content}` - Target repository content
- `{opportunities}` - Generated opportunities
- `{analysis_request}` - User's original request

Note: These are advanced customization options. The default prompts
are optimized for most use cases.
