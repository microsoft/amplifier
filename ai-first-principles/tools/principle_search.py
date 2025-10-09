#!/usr/bin/env python3
"""
Search tool for finding relevant AI-first principles based on keywords and concepts.

This tool enables users to quickly find principles related to their current task
or problem domain, supporting both simple keyword search and concept-based search.
"""

import argparse
import re
import sys
from pathlib import Path


class PrincipleSearcher:
    """Search engine for AI-first principles."""

    def __init__(self):
        """Initialize the searcher."""
        self.root = Path(__file__).parent.parent / "principles"
        self.principles = self._load_principles()
        self.categories = {
            "people": range(1, 7),
            "process": range(7, 20),
            "technology": range(20, 38),
            "governance": range(38, 45),
        }

    def _load_principles(self) -> dict[int, dict]:
        """Load all principle files and extract metadata."""
        principles = {}

        for file_path in sorted(self.root.glob("**/*.md")):
            if file_path.name == "README.md":
                continue

            # Extract principle number from filename
            match = re.match(r"(\d+)-", file_path.name)
            if not match:
                continue

            num = int(match.group(1))
            content = file_path.read_text(encoding="utf-8").lower()

            # Extract title
            title_match = re.search(r"#\s+principle\s+#\d+[:\s-]+(.+)", content, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else ""

            # Extract category
            category = file_path.parent.name

            principles[num] = {
                "number": num,
                "title": title,
                "category": category,
                "path": file_path,
                "content": content,
                "filename": file_path.name,
            }

        return principles

    def search_keyword(self, keyword: str, context_lines: int = 2) -> list[dict]:
        """Search for principles containing a keyword."""
        keyword_lower = keyword.lower()
        results = []

        for num, principle in self.principles.items():
            if keyword_lower in principle["content"]:
                # Count occurrences
                count = principle["content"].count(keyword_lower)

                # Extract context snippets
                snippets = self._extract_snippets(principle["content"], keyword_lower, context_lines)

                results.append(
                    {
                        "number": num,
                        "title": principle["title"],
                        "category": principle["category"],
                        "path": principle["path"],
                        "occurrences": count,
                        "snippets": snippets[:3],  # Limit to 3 snippets
                    }
                )

        # Sort by occurrence count
        results.sort(key=lambda x: x["occurrences"], reverse=True)
        return results

    def search_concepts(self, concepts: list[str]) -> list[dict]:
        """Search for principles related to multiple concepts."""
        concept_scores = {}

        for concept in concepts:
            concept_lower = concept.lower()
            for num, principle in self.principles.items():
                if concept_lower in principle["content"]:
                    if num not in concept_scores:
                        concept_scores[num] = {"score": 0, "concepts": []}
                    concept_scores[num]["score"] += principle["content"].count(concept_lower)
                    concept_scores[num]["concepts"].append(concept)

        # Build results
        results = []
        for num, score_data in concept_scores.items():
            principle = self.principles[num]
            results.append(
                {
                    "number": num,
                    "title": principle["title"],
                    "category": principle["category"],
                    "path": principle["path"],
                    "score": score_data["score"],
                    "matched_concepts": score_data["concepts"],
                }
            )

        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def search_related(self, principle_num: int) -> list[dict]:
        """Find principles related to a specific principle."""
        if principle_num not in self.principles:
            return []

        principle = self.principles[principle_num]
        content = principle["content"]

        # Extract related principles section
        related_match = re.search(r"##\s+related\s+principles.*?(?=##|\Z)", content, re.IGNORECASE | re.DOTALL)

        if not related_match:
            return []

        related_text = related_match.group(0)
        results = []

        # Find all principle references
        refs = re.findall(r"principle\s+#(\d+)", related_text, re.IGNORECASE)
        for ref in refs:
            ref_num = int(ref)
            if ref_num in self.principles:
                ref_principle = self.principles[ref_num]
                results.append(
                    {
                        "number": ref_num,
                        "title": ref_principle["title"],
                        "category": ref_principle["category"],
                        "path": ref_principle["path"],
                    }
                )

        return results

    def search_by_category(self, category: str) -> list[dict]:
        """List all principles in a category."""
        category_lower = category.lower()
        results = []

        for num, principle in self.principles.items():
            if principle["category"] == category_lower:
                results.append(
                    {
                        "number": num,
                        "title": principle["title"],
                        "path": principle["path"],
                    }
                )

        results.sort(key=lambda x: x["number"])
        return results

    def search_examples(self, pattern: str) -> list[dict]:
        """Search for principles with specific example patterns."""
        pattern_lower = pattern.lower()
        results = []

        for num, principle in self.principles.items():
            # Look in good/bad examples sections
            examples_match = re.search(
                r"##\s+good\s+examples.*?(?=##|\Z)", principle["content"], re.IGNORECASE | re.DOTALL
            )

            if examples_match and pattern_lower in examples_match.group(0).lower():
                results.append(
                    {
                        "number": num,
                        "title": principle["title"],
                        "category": principle["category"],
                        "path": principle["path"],
                    }
                )

        return results

    def _extract_snippets(self, content: str, keyword: str, context_lines: int) -> list[str]:
        """Extract text snippets around keyword occurrences."""
        lines = content.split("\n")
        keyword_lower = keyword.lower()
        snippets = []

        for i, line in enumerate(lines):
            if keyword_lower in line.lower():
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                snippet_lines = lines[start:end]

                # Highlight the keyword
                snippet = "\n".join(snippet_lines)
                snippet = re.sub(
                    f"({re.escape(keyword)})",
                    r"**\1**",
                    snippet,
                    flags=re.IGNORECASE,
                )
                snippets.append(snippet.strip())

        return snippets


def format_results(results: list[dict], mode: str) -> str:
    """Format search results for display."""
    if not results:
        return "No principles found matching your search criteria."

    output = [f"Found {len(results)} matching principle(s):\n"]

    for result in results:
        output.append(f"📌 Principle #{result['number']}: {result['title']}")
        output.append(f"   Category: {result['category']}")
        output.append(f"   Path: {result['path']}")

        if mode == "keyword" and "occurrences" in result:
            output.append(f"   Occurrences: {result['occurrences']}")
            if result.get("snippets"):
                output.append("   Context:")
                for snippet in result["snippets"]:
                    # Indent snippet lines
                    indented = "\n".join(f"     {line}" for line in snippet.split("\n"))
                    output.append(indented)

        elif mode == "concepts" and "matched_concepts" in result:
            output.append(f"   Relevance score: {result['score']}")
            output.append(f"   Matched concepts: {', '.join(result['matched_concepts'])}")

        output.append("")

    return "\n".join(output)


def main():
    """Main entry point for the search tool."""
    parser = argparse.ArgumentParser(
        description="Search for relevant AI-first principles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search for principles mentioning "test"
  python3 tools/principle_search.py keyword test

  # Search for principles related to multiple concepts
  python3 tools/principle_search.py concepts "error handling" "recovery" "resilience"

  # Find principles related to principle #31
  python3 tools/principle_search.py related 31

  # List all technology principles
  python3 tools/principle_search.py category technology

  # Search for principles with specific code examples
  python3 tools/principle_search.py examples "async def"
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Search commands")

    # Keyword search
    keyword_parser = subparsers.add_parser("keyword", help="Search by keyword")
    keyword_parser.add_argument("term", help="Keyword to search for")
    keyword_parser.add_argument("--context", type=int, default=2, help="Number of context lines to show (default: 2)")

    # Concept search
    concept_parser = subparsers.add_parser("concepts", help="Search by multiple concepts")
    concept_parser.add_argument("concepts", nargs="+", help="Concepts to search for")

    # Related principles
    related_parser = subparsers.add_parser("related", help="Find related principles")
    related_parser.add_argument("number", type=int, help="Principle number")

    # Category listing
    category_parser = subparsers.add_parser("category", help="List principles by category")
    category_parser.add_argument(
        "category", choices=["people", "process", "technology", "governance"], help="Category name"
    )

    # Example search
    examples_parser = subparsers.add_parser("examples", help="Search in code examples")
    examples_parser.add_argument("pattern", help="Pattern to search for in examples")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    searcher = PrincipleSearcher()

    try:
        if args.command == "keyword":
            results = searcher.search_keyword(args.term, args.context)
            print(format_results(results, "keyword"))

        elif args.command == "concepts":
            results = searcher.search_concepts(args.concepts)
            print(format_results(results, "concepts"))

        elif args.command == "related":
            results = searcher.search_related(args.number)
            if results:
                print(f"Principles related to #{args.number}:\n")
                print(format_results(results, "related"))
            else:
                print(f"❌ Principle #{args.number} not found or has no related principles")

        elif args.command == "category":
            results = searcher.search_by_category(args.category)
            print(f"Principles in {args.category} category:\n")
            print(format_results(results, "category"))

        elif args.command == "examples":
            results = searcher.search_examples(args.pattern)
            print(format_results(results, "examples"))

    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
