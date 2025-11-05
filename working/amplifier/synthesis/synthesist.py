"""
The Synthesist Brick

This script is responsible for the final synthesis stage. It reads all the
pre-computed "Analyst Briefs" from the cache directory, combines them, and
invokes a powerful LLM to generate a cohesive report based on the original
high-level research query.

It is a simple, single-purpose tool designed to be called from an orchestrator
like a Makefile after the analysis stage is complete.
"""

import json
import os
import sys
from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from amplifier.synthesis.config import CACHE_DIR
from amplifier.synthesis.config import SYNTHESIST_MODEL

# --- Prompt ---
SYNTHESIST_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a world-class strategist and synthesizer. You have been provided with a user's high-level research objective and a series of Analyst Briefs, each deconstructing a different source document. "
            "Your task is to synthesize these disparate briefs into a single, cohesive, and insightful report that addresses the user's objective. "
            "Your report should have the following sections:\n"
            "1. **Executive Summary:** A high-level overview of the key findings and recommendations.\n"
            "2. **Convergent Themes:** Common ideas, concepts, or problems that appear across multiple documents.\n"
            "3. **Divergent Perspectives:** Where the documents disagree or offer conflicting solutions.\n"
            "4. **Synthesized Framework/Solution:** A new, unified framework or solution that addresses the user's objective, drawing upon the strengths of the various proposals.\n"
            "5. **Actionable Recommendations:** Concrete next steps or design principles for implementing the new framework.\n\n"
            "For every point you make, you MUST cite the source document(s) using the format [Source: filename.md]. Do not make up any information. If the evidence is insufficient, state that clearly.",
        ),
        ("human", "Research Objective: {query}\n\nAnalyst Briefs:\n---\n{briefs}\n---"),
    ]
)

# --- Core Functions ---


def get_analyst_briefs() -> list[dict[str, Any]]:
    """Reads all analyst briefs from the cache directory."""
    briefs = []
    if not os.path.exists(CACHE_DIR):
        return briefs

    for filename in os.listdir(CACHE_DIR):
        if filename.endswith(".json"):
            try:
                with open(os.path.join(CACHE_DIR, filename)) as f:
                    briefs.append(json.load(f))
            except Exception as e:
                print(f"Warning: Could not load or parse {filename}: {e}", file=sys.stderr)
    return briefs


def run_synthesis(query: str) -> str:
    """
    Runs the final synthesis stage by reading all cached analyst briefs
    and generating a cohesive report.
    """
    briefs = get_analyst_briefs()
    if not briefs:
        return (
            "Error: No analyst briefs were found in the cache. Cannot synthesize. Please run the analysis step first."
        )

    formatted_briefs = []
    for brief in briefs:
        source = brief.get("source_document", "Unknown")
        # Format the brief nicely for the prompt
        formatted_briefs.append(f"Source: {source}\n{json.dumps(brief, indent=2)}")

    llm = ChatOpenAI(model=SYNTHESIST_MODEL, temperature=0.2)
    parser = StrOutputParser()
    chain = SYNTHESIST_PROMPT | llm | parser

    final_report = chain.invoke({"query": query, "briefs": "\n\n---\n\n".join(formatted_briefs)})
    return final_report
