"""SWOT analysis prompt generation.

Generates prompts for analyzing competitive position using SWOT analysis
(Strengths, Weaknesses, Opportunities, Threats).
"""

import json


def get_swot_prompt(entity1: str, entity2: str, research_data: dict) -> str:
    """Generate SWOT analysis prompt.

    Args:
        entity1: First company/product name
        entity2: Second company/product name
        research_data: Dictionary from research.json containing findings

    Returns:
        Formatted prompt string for LLM to generate SWOT analysis
    """
    research_json = json.dumps(research_data, indent=2)

    return f"""Analyze {entity1} vs {entity2} using SWOT analysis framework.

SWOT analyzes competitive position across 4 dimensions:

1. **Strengths** (Internal Advantages):
   - What does the entity do well?
   - What unique capabilities or resources?
   - What competitive advantages?
   - Examples: technology, brand, talent, efficiency, market position

2. **Weaknesses** (Internal Limitations):
   - What are the gaps or limitations?
   - Where do competitors have advantages?
   - What resources are lacking?
   - Examples: technical debt, cost structure, limited scale, talent gaps

3. **Opportunities** (External Favorable Conditions):
   - What favorable market trends exist?
   - What unmet customer needs?
   - What new markets or segments?
   - Examples: market growth, technology shifts, regulatory changes, partnerships

4. **Threats** (External Challenges):
   - What competitive pressures exist?
   - What market headwinds?
   - What regulatory or technology risks?
   - Examples: new entrants, substitutes, economic conditions, changing preferences

## Research Data

{research_json}

## Task

For EACH entity ({entity1} and {entity2}), analyze ALL FOUR SWOT elements with specific examples and evidence from the research data.

Provide your analysis as structured JSON:

{{
  "{entity1}": {{
    "strengths": [
      "Strength 1 with specific evidence and examples",
      "Strength 2 with specific evidence and examples",
      ...
    ],
    "weaknesses": [
      "Weakness 1 with specific evidence and examples",
      "Weakness 2 with specific evidence and examples",
      ...
    ],
    "opportunities": [
      "Opportunity 1 with specific evidence and examples",
      "Opportunity 2 with specific evidence and examples",
      ...
    ],
    "threats": [
      "Threat 1 with specific evidence and examples",
      "Threat 2 with specific evidence and examples",
      ...
    ]
  }},
  "{entity2}": {{
    ... same structure ...
  }}
}}

Be specific, use evidence from research data, and provide 3-5 items for each SWOT element."""
