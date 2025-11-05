"""The Triage Brick

This script is responsible for the initial filtering of a large corpus of
documents. It reads a single document and uses a fast, inexpensive LLM to
determine if the document is relevant to a high-level research query.

If the document is deemed relevant, its path is printed to standard output.
This allows the script to be used in a pipeline with other tools.
"""

import argparse
import os
import sys

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from amplifier.synthesis.config import TRIAGE_MODEL

# --- Prompt ---
TRIAGE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a research assistant performing an initial triage of documents. Your task is to determine if a document is relevant to a user's research query. "
            "The document's content will be provided. Respond with the word 'true' if the document contains information that could help answer the query, and 'false' otherwise. Do not provide any explanation.",
        ),
        ("human", "Research Query: {query}\n\nDocument Content:\n---\n{document}\n---"),
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


def run_triage(doc_path: str, query: str) -> bool:
    """
    Runs the triage process for a single document.
    Returns True if the document is relevant, False otherwise.
    """
    content = get_file_content(doc_path)
    if not content:
        return False

    try:
        llm = ChatOpenAI(model=TRIAGE_MODEL, temperature=0)
        parser = StrOutputParser()
        chain = TRIAGE_PROMPT | llm | parser
        response = chain.invoke({"query": query, "document": content})
        return response.strip().lower() == "true"
    except Exception as e:
        # In case of an error, we can choose to be conservative and consider it not relevant.
        print(f"Warning: Error processing {doc_path} during triage: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point for the triage script."""
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Determines if a document is relevant to a query.")
    parser.add_argument("-d", "--document", type=str, required=True, help="The path to the document to analyze.")
    parser.add_argument("-q", "--query", type=str, required=True, help="The high-level research query.")
    args = parser.parse_args()

    run_triage(args.document, args.query)


if __name__ == "__main__":
    main()
