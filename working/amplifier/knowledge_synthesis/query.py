#!/usr/bin/env python3
"""
Knowledge Query CLI - Query extracted knowledge

Simple command-line tool for querying extracted knowledge.
"""

import json
import sys

import click

from amplifier.config.paths import paths


@click.command()
@click.argument("query", required=True)
@click.option("--limit", "-n", default=10, type=int, help="Maximum number of results (default: 10)")
@click.option(
    "--type",
    "-t",
    type=click.Choice(["all", "concept", "relationship", "insight", "pattern"], case_sensitive=False),
    default="all",
    help="Type of knowledge to search",
)
@click.option("--format", "-f", type=click.Choice(["text", "json"]), default="text", help="Output format")
def main(query: str, limit: int, type: str, format: str):
    """Query extracted knowledge base.

    Search through concepts, relationships, insights, and patterns extracted
    from content files.

    Examples:
        knowledge-query "machine learning"
        knowledge-query "Claude" --type concept
        knowledge-query "uses" --type relationship --limit 20
    """
    # Use paths.data_dir for the extractions file
    extractions_file = paths.data_dir / "knowledge" / "extractions.jsonl"

    if not extractions_file.exists():
        click.echo(f"No extractions found at {extractions_file}")
        click.echo("Run 'knowledge-synthesis sync' first to extract knowledge.")
        sys.exit(1)

    # Load all extractions
    extractions = []
    with open(extractions_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    extractions.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    if not extractions:
        click.echo("No extractions found in file.")
        sys.exit(1)

    # Search for matches
    query_lower = query.lower()
    matches = []

    for extraction in extractions:
        source_info = {
            "source_id": extraction.get("source_id", ""),
            "title": extraction.get("title", "Unknown"),
            "url": extraction.get("url", ""),
        }

        # Search concepts
        if type in ("all", "concept"):
            for concept in extraction.get("concepts", []):
                name = concept.get("name", "")
                description = concept.get("description", "")
                if query_lower in name.lower() or query_lower in description.lower():
                    matches.append(
                        {
                            "type": "concept",
                            "name": name,
                            "description": description,
                            "importance": concept.get("importance", 0),
                            **source_info,
                        }
                    )

        # Search relationships
        if type in ("all", "relationship"):
            for rel in extraction.get("relationships", []):
                subject = rel.get("subject", "")
                predicate = rel.get("predicate", "")
                obj = rel.get("object", "")
                if query_lower in subject.lower() or query_lower in predicate.lower() or query_lower in obj.lower():
                    matches.append(
                        {
                            "type": "relationship",
                            "subject": subject,
                            "predicate": predicate,
                            "object": obj,
                            "confidence": rel.get("confidence", 0),
                            **source_info,
                        }
                    )

        # Search insights
        if type in ("all", "insight"):
            for insight in extraction.get("insights", []):
                if isinstance(insight, str):
                    insight_text = insight
                else:
                    insight_text = insight.get("description", "")

                if query_lower in insight_text.lower():
                    matches.append({"type": "insight", "text": insight_text, **source_info})

        # Search patterns
        if type in ("all", "pattern"):
            for pattern in extraction.get("patterns", []):
                name = pattern.get("name", "")
                description = pattern.get("description", "")
                if query_lower in name.lower() or query_lower in description.lower():
                    matches.append(
                        {
                            "type": "pattern",
                            "name": name,
                            "description": description,
                            **source_info,
                        }
                    )

    # Sort by importance/confidence if available
    matches.sort(key=lambda x: x.get("importance", x.get("confidence", 0)), reverse=True)

    # Limit results
    matches = matches[:limit]

    # Output results
    if format == "json":
        output = {"query": query, "type": type, "count": len(matches), "results": matches}
        click.echo(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        # Text format
        if not matches:
            click.echo(f"No matches found for '{query}'")
        else:
            click.echo(f"\nFound {len(matches)} matches for '{query}':\n")

            for match in matches:
                if match["type"] == "concept":
                    click.echo(f"📌 CONCEPT: {match['name']}")
                    if match["description"]:
                        desc = match["description"][:150]
                        if len(match["description"]) > 150:
                            desc += "..."
                        click.echo(f"   {desc}")
                    click.echo(f"   Source: {match['title']}")
                    if match.get("importance"):
                        click.echo(f"   Importance: {match['importance']:.2f}")

                elif match["type"] == "relationship":
                    click.echo(f"🔗 RELATIONSHIP: {match['subject']} --{match['predicate']}--> {match['object']}")
                    click.echo(f"   Source: {match['title']}")
                    if match.get("confidence"):
                        click.echo(f"   Confidence: {match['confidence']:.2f}")

                elif match["type"] == "insight":
                    text = match["text"][:200]
                    if len(match["text"]) > 200:
                        text += "..."
                    click.echo(f"💡 INSIGHT: {text}")
                    click.echo(f"   Source: {match['title']}")

                elif match["type"] == "pattern":
                    click.echo(f"🔄 PATTERN: {match['name']}")
                    if match["description"]:
                        desc = match["description"][:150]
                        if len(match["description"]) > 150:
                            desc += "..."
                        click.echo(f"   {desc}")
                    click.echo(f"   Source: {match['title']}")

                click.echo()  # Blank line between results


if __name__ == "__main__":
    main()
