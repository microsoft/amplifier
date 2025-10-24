"""Research stage: Web research and data gathering.

Stage 1 of the competitive analysis pipeline. Conducts web research on both
entities and structures findings with sources.
"""

import json
from pathlib import Path

from claude_code_sdk import query

from ..models import CompanyResearch
from ..models import ResearchResult


async def run_research_async(entity1: str, entity2: str, output_dir: Path) -> ResearchResult:
    """Conduct web research on both entities.

    Args:
        entity1: First company/product name
        entity2: Second company/product name
        output_dir: Directory to save research.json

    Returns:
        ResearchResult with findings and sources

    Side effects:
        Writes research.json to output_dir
    """
    prompt = f"""Research and gather current information about {entity1} and {entity2}.

For EACH entity, find:
- Market position (market size, share, growth trajectory)
- Core offerings (main products/services)
- Target audience (primary customers and users)
- Key strengths (what they do well, competitive advantages)
- Key weaknesses (limitations, gaps, challenges)
- Pricing model (how they charge customers)
- Recent news and strategic initiatives (last 6-12 months)

Provide comprehensive, specific information with sources. Include URLs for all claims.

Return your findings as structured JSON:

{{
  "companies": [
    {{
      "name": "{entity1}",
      "findings": [
        "Finding 1 with specific details...",
        "Finding 2 with specific details...",
        ...
      ],
      "sources": [
        "https://source1.com/page",
        "https://source2.com/article",
        ...
      ]
    }},
    {{
      "name": "{entity2}",
      "findings": [
        ...
      ],
      "sources": [
        ...
      ]
    }}
  ]
}}

Be thorough and include at least 10-15 specific findings per entity."""

    # Call Claude SDK with web search enabled
    # Note: Using synchronous wrapper since CLI orchestration is sync
    response_text = ""
    async for message in query(prompt=prompt):
        # Collect assistant response text
        if hasattr(message, "content"):
            for block in message.content:
                if hasattr(block, "text"):
                    response_text += block.text

    # Parse response as JSON
    # Note: LLM might wrap JSON in markdown code blocks, extract it
    response_text = response_text.strip()
    if response_text.startswith("```"):
        # Remove markdown code blocks
        lines = response_text.split("\n")
        # Find start and end of JSON
        start_idx = 0
        end_idx = len(lines)
        for i, line in enumerate(lines):
            if line.strip().startswith("{"):
                start_idx = i
                break
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip().endswith("}"):
                end_idx = i + 1
                break
        response_text = "\n".join(lines[start_idx:end_idx])

    research_data = json.loads(response_text)

    # Build CompanyResearch objects
    companies = []
    for company_data in research_data["companies"]:
        company = CompanyResearch(
            name=company_data["name"],
            findings=company_data["findings"],
            sources=company_data["sources"],
        )
        companies.append(company)

    # Create ResearchResult with timestamp
    result = ResearchResult.create(companies=companies)

    # Save to research.json
    output_path = output_dir / "research.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")

    return result
