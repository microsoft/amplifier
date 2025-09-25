#!/usr/bin/env python3
"""
Integration script to convert knowledge store data to visualization format.
Reads from .data/knowledge/store.json and creates data/substack_knowledge_graph.json
"""

import json
from pathlib import Path


def load_knowledge_store(store_path: Path) -> dict:
    """Load the knowledge store JSON file"""
    with open(store_path, encoding="utf-8") as f:
        return json.load(f)


def extract_substack_articles(nodes: dict) -> list[str]:
    """Extract unique Substack article sources from all nodes"""
    sources = set()
    for node in nodes.values():
        for source in node.get("sources", []):
            # Identify Substack articles by the michaeljjabbour prefix
            if source.startswith("michaeljjabbour_"):
                sources.add(source)
    return sorted(sources)


def build_concepts(nodes: dict, articles: list[str]) -> list[dict]:
    """Build concept list from nodes, focusing on Substack-sourced concepts"""
    concepts = {}

    for _node_id, node in nodes.items():
        if node.get("type") != "concept":
            continue

        # Check if this concept appears in any Substack article
        node_sources = set(node.get("sources", []))
        article_sources = [s for s in node_sources if s in articles]

        if not article_sources:
            continue

        content = node.get("content", {})
        name = content.get("name", "")

        if name:
            if name not in concepts:
                concepts[name] = {
                    "name": name,
                    "articles": [],
                    "count": 0,
                    "description": content.get("description", ""),
                    "category": content.get("category", "general"),
                    "importance": content.get("importance", 0.5),
                }

            # Add articles for this concept
            for article in article_sources:
                if article not in concepts[name]["articles"]:
                    concepts[name]["articles"].append(article)

            concepts[name]["count"] += len(article_sources)

    # Convert to list and sort by count
    concept_list = list(concepts.values())
    concept_list.sort(key=lambda x: x["count"], reverse=True)

    return concept_list


def build_insights(nodes: dict, articles: list[str]) -> list[dict]:
    """Build insight list from nodes"""
    insights = []

    for _node_id, node in nodes.items():
        if node.get("type") != "insight":
            continue

        # Check if this insight comes from a Substack article
        node_sources = node.get("sources", [])
        article_sources = [s for s in node_sources if s in articles]

        if not article_sources:
            continue

        content = node.get("content", {})
        text = content.get("text", "")

        if text:
            # Find related concepts by checking connections
            related_concepts = []
            for conn_id in node.get("connections", []):
                if conn_id in nodes and nodes[conn_id].get("type") == "concept":
                    concept_name = nodes[conn_id].get("content", {}).get("name", "")
                    if concept_name and concept_name not in related_concepts:
                        related_concepts.append(concept_name)

            for article in article_sources:
                insights.append(
                    {
                        "text": text,
                        "article": article,
                        "concepts": related_concepts[:5],  # Limit to 5 concepts per insight
                        "importance": content.get("importance", 0.5),
                    }
                )

    # Sort by importance
    insights.sort(key=lambda x: x.get("importance", 0.5), reverse=True)

    return insights


def build_relationships(edges: dict, nodes: dict, articles: list[str]) -> list[dict]:
    """Build relationship list from edges"""
    relationships = []
    seen_pairs = set()

    for _edge_id, edge in edges.items():
        source_id = edge.get("source")
        target_id = edge.get("target")

        if not source_id or not target_id:
            continue

        # Check if both nodes exist and at least one is from a Substack article
        if source_id not in nodes or target_id not in nodes:
            continue

        source_node = nodes[source_id]
        target_node = nodes[target_id]

        # Check if either node is from a Substack article
        source_sources = set(source_node.get("sources", []))
        target_sources = set(target_node.get("sources", []))

        has_substack = any(s in articles for s in source_sources | target_sources)
        if not has_substack:
            continue

        # Get concept names
        source_name = source_node.get("content", {}).get("name", "")
        target_name = target_node.get("content", {}).get("name", "")

        if not source_name or not target_name:
            continue

        # Avoid duplicate relationships
        pair = tuple(sorted([source_name, target_name]))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)

        # Determine relationship type and strength
        edge_type = edge.get("type", "related")
        metadata = edge.get("metadata", {})
        strength = metadata.get("strength", 0.5)

        relationships.append({"source": source_name, "target": target_name, "type": edge_type, "strength": strength})

    # Sort by strength
    relationships.sort(key=lambda x: x["strength"], reverse=True)

    return relationships


def format_article_title(filename: str) -> str:
    """Convert filename to readable title"""
    # Remove prefix and extension
    title = filename.replace("michaeljjabbour_", "").replace(".md", "")
    # Replace hyphens with spaces
    title = title.replace("-", " ")
    return title


def main():
    """Main integration function"""
    # Paths
    store_path = Path(".data/knowledge/store.json")
    output_path = Path("data/substack_knowledge_graph.json")

    # Create output directory if needed
    output_path.parent.mkdir(exist_ok=True)

    print(f"Loading knowledge store from {store_path}...")
    store_data = load_knowledge_store(store_path)

    nodes = store_data.get("nodes", {})
    edges = store_data.get("edges", {})

    print(f"Found {len(nodes)} nodes and {len(edges)} edges")

    # Extract Substack articles
    articles = extract_substack_articles(nodes)
    print(f"Found {len(articles)} Substack articles")

    # Build formatted article list
    formatted_articles = []
    for article in articles:
        formatted_articles.append({"id": article, "title": format_article_title(article), "filename": article})

    # Build visualization data
    concepts = build_concepts(nodes, articles)
    print(f"Extracted {len(concepts)} concepts from Substack articles")

    insights = build_insights(nodes, articles)
    print(f"Extracted {len(insights)} insights from Substack articles")

    relationships = build_relationships(edges, nodes, articles)
    print(f"Extracted {len(relationships)} relationships")

    # Create final structure
    knowledge_graph = {
        "articles": formatted_articles,
        "concepts": concepts[:50],  # Top 50 concepts for visualization
        "insights": insights[:100],  # Top 100 insights
        "relationships": relationships[:200],  # Top 200 relationships
    }

    # Save to file
    print(f"\nSaving to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(knowledge_graph, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\nIntegration complete!")
    print(f"  Articles: {len(formatted_articles)}")
    print(f"  Concepts: {len(concepts)} (saved top 50)")
    print(f"  Insights: {len(insights)} (saved top 100)")
    print(f"  Relationships: {len(relationships)} (saved top 200)")

    # Show sample data
    if concepts:
        print("\nTop 5 concepts by frequency:")
        for concept in concepts[:5]:
            print(f"  - {concept['name']}: {concept['count']} occurrences")

    if insights:
        print("\nSample insights:")
        for insight in insights[:3]:
            text = insight["text"][:100] + "..." if len(insight["text"]) > 100 else insight["text"]
            print(f"  - {text}")


if __name__ == "__main__":
    main()
