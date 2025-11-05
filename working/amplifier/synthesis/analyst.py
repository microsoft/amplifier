"""
The Analyst Brick

This script is responsible for performing a detailed analysis of a single document
based on a high-level research query. It reads a document, invokes an LLM to
create a structured "Analyst Brief," and saves the result to a cache.

It is a simple, single-purpose tool designed to be called from an orchestrator
like a Makefile.
"""

import json
import os
import sys

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from amplifier.synthesis.config import ANALYST_MODEL
from amplifier.synthesis.config import CACHE_DIR

# --- Prompt ---
ANALYST_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a meticulous research analyst. Your goal is to read the following document and produce a structured 'Analyst Brief' based on a high-level research query. The brief should not be a simple summary. It should deconstruct the document into its core components. "
            "Provide your output as a JSON object with the following keys: 'core_thesis', 'key_concepts', 'arguments_and_evidence', 'proposed_solutions', 'connections_and_implications'.",
        ),
        ("human", "High-Level Query: {query}\n\nDocument Content:\n---\n{document}\n---"),
    ]
)

# --- Core Functions ---


def get_file_content(path: str) -> str:
    """Reads and returns the content of a specified file."""
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {path}: {e}", file=sys.stderr)
        sys.exit(1)


def run_analysis(doc_path: str, query: str, clear_cache: bool):
    """
    Runs the analysis for a single document, handling caching.
    This function is designed to be called in parallel by an orchestrator.
    """
    filename = os.path.basename(doc_path)
    cache_path = os.path.join(CACHE_DIR, f"{filename}.json")

    if not clear_cache and os.path.exists(cache_path):
        # The orchestrator's progress bar won't see this, which is fine.
        # It means the task is "done" instantly.
        return

    content = get_file_content(doc_path)
    if not content:
        return

    try:
        llm = ChatOpenAI(model=ANALYST_MODEL, temperature=0)
        parser = JsonOutputParser()
        chain = ANALYST_PROMPT | llm | parser
        brief = chain.invoke({"query": query, "document": content})
        brief["source_document"] = filename

        with open(cache_path, "w") as f:
            json.dump(brief, f, indent=2)
    except Exception as e:
        # Log the error but don't crash the whole pipeline.
        print(f"Warning: Error processing {filename}: {e}", file=sys.stderr)
