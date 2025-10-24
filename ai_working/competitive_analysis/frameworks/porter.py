"""Porter's Five Forces analysis prompt generation.

Generates prompts for analyzing competitive dynamics using Michael Porter's
Five Forces framework (Competitive Strategy, 1980).
"""

import json


def get_porter_prompt(entity1: str, entity2: str, research_data: dict) -> str:
    """Generate Porter's Five Forces analysis prompt.

    Args:
        entity1: First company/product name
        entity2: Second company/product name
        research_data: Dictionary from research.json containing findings

    Returns:
        Formatted prompt string for LLM to generate Five Forces analysis
    """
    research_json = json.dumps(research_data, indent=2)

    return f"""Analyze {entity1} vs {entity2} using Porter's Five Forces framework.

Porter's Five Forces analyzes industry structure and competitive dynamics across 5 dimensions:

1. **Competitive Rivalry**: How intense is competition among existing players?
   - Number of competitors, market concentration
   - Rate of industry growth
   - Product differentiation
   - Switching costs
   - Exit barriers

2. **Threat of New Entrants**: How easy is it for new competitors to enter?
   - Capital requirements
   - Economies of scale
   - Brand loyalty and switching costs
   - Access to distribution channels
   - Regulatory barriers

3. **Bargaining Power of Suppliers**: How much leverage do suppliers have?
   - Number and concentration of suppliers
   - Uniqueness of supplier products
   - Cost of switching suppliers
   - Supplier integration potential

4. **Bargaining Power of Buyers**: How much leverage do customers have?
   - Number and concentration of buyers
   - Availability of substitutes
   - Price sensitivity
   - Buyer information and switching costs

5. **Threat of Substitutes**: What alternative solutions exist?
   - Availability of substitute products/services
   - Relative price-performance of substitutes
   - Switching costs to substitutes
   - Buyer propensity to substitute

## Research Data

{research_json}

## Task

For EACH entity ({entity1} and {entity2}), analyze ALL FIVE FORCES with specific examples and evidence from the research data.

Provide your analysis as structured JSON:

{{
  "{entity1}": {{
    "competitive_rivalry": {{
      "intensity": "LOW|MEDIUM|HIGH|VERY HIGH",
      "analysis": "Detailed analysis with specific examples..."
    }},
    "threat_of_new_entrants": {{
      "level": "LOW|MEDIUM|HIGH|VERY HIGH",
      "analysis": "Detailed analysis with specific examples..."
    }},
    "supplier_power": {{
      "level": "LOW|MEDIUM|HIGH|VERY HIGH",
      "analysis": "Detailed analysis with specific examples..."
    }},
    "buyer_power": {{
      "level": "LOW|MEDIUM|HIGH|VERY HIGH",
      "analysis": "Detailed analysis with specific examples..."
    }},
    "threat_of_substitutes": {{
      "level": "LOW|MEDIUM|HIGH|VERY HIGH",
      "analysis": "Detailed analysis with specific examples..."
    }}
  }},
  "{entity2}": {{
    ... same structure ...
  }}
}}

Be specific, use evidence from research data, and explain your reasoning for each force."""
