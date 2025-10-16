#!/usr/bin/env python3
"""
Feature Demo #6: Knowledge Graph & Synthesis
Shows how Amplifier builds a connected knowledge network
"""


def main():
    print("\n" + "=" * 70)
    print("🕸️  FEATURE #6: KNOWLEDGE GRAPH & SYNTHESIS")
    print("=" * 70)

    print("\n📋 What is the Knowledge Graph?")
    print("   Beyond storing individual pieces of knowledge,")
    print("   Amplifier connects them into a semantic network:")
    print()
    print("   • Concepts linked by relationships")
    print("   • Patterns emerge from connections")
    print("   • Navigate between related ideas")
    print("   • Find unexpected insights")
    print("   • Visualize your knowledge landscape")

    # Architecture
    print("\n" + "-" * 70)
    print("🏗️  KNOWLEDGE SYNTHESIS ARCHITECTURE")
    print("-" * 70)

    print("\n1️⃣  Extraction Layer")
    print("   • Scan documents in content directories")
    print("   • Extract concepts, claims, patterns")
    print("   • Store in structured format")

    print("\n2️⃣  Graph Building Layer")
    print("   • Identify concepts and entities")
    print("   • Discover relationships between them")
    print("   • Build knowledge graph (nodes + edges)")

    print("\n3️⃣  Synthesis Layer")
    print("   • Find patterns across knowledge")
    print("   • Identify tensions and contradictions")
    print("   • Discover emergent insights")
    print("   • Surface uncertainties")

    print("\n4️⃣  Query Layer")
    print("   • Semantic search across graph")
    print("   • Path finding between concepts")
    print("   • Neighbor exploration")
    print("   • Contradiction detection")

    # Example graph structure
    print("\n" + "=" * 70)
    print("📊 EXAMPLE: Knowledge Graph Structure")
    print("=" * 70)

    print("\n```")
    print("    [Microservices]")
    print("         |")
    print("         |--requires--> [Service Discovery]")
    print("         |--enables--> [Independent Scaling]")
    print("         |--challenges--> [Distributed Debugging]")
    print("         |")
    print("    [JWT Auth]")
    print("         |")
    print("         |--fits-well-with--> [Microservices]")
    print("         |--requires--> [Token Validation]")
    print("         |--security-concern--> [Token Expiration]")
    print("         |")
    print("    [Session Auth]")
    print("         |")
    print("         |--alternative-to--> [JWT Auth]")
    print("         |--requires--> [Centralized State]")
    print("         |--conflicts-with--> [Microservices]")
    print("```")

    print("\n💡 Notice:")
    print("   • Concepts connected by typed relationships")
    print("   • Conflicts become visible (Session Auth ⚡ Microservices)")
    print("   • Design implications emerge naturally")

    # Commands
    print("\n" + "=" * 70)
    print("🔧 KNOWLEDGE GRAPH COMMANDS")
    print("=" * 70)

    commands = [
        {
            "command": "make knowledge-graph-build",
            "purpose": "Build complete graph from extractions",
            "when": "Initial graph creation or full rebuild"
        },
        {
            "command": "make knowledge-graph-update",
            "purpose": "Incremental update with new content",
            "when": "After adding new documents"
        },
        {
            "command": "make knowledge-graph-stats",
            "purpose": "Show graph statistics",
            "output": "Nodes, edges, top concepts, density"
        },
        {
            "command": "make knowledge-graph-viz NODES=50",
            "purpose": "Create interactive HTML visualization",
            "output": "Browse graph in web browser"
        },
        {
            "command": "make knowledge-graph-search Q='authentication'",
            "purpose": "Semantic search within graph",
            "output": "Related concepts and paths"
        },
        {
            "command": "make knowledge-graph-path FROM='JWT' TO='Security'",
            "purpose": "Find paths between concepts",
            "output": "Connection chains"
        },
        {
            "command": "make knowledge-graph-neighbors CONCEPT='API' HOPS=2",
            "purpose": "Explore concept neighborhood",
            "output": "Related concepts within N hops"
        },
        {
            "command": "make knowledge-graph-tensions TOP=10",
            "purpose": "Find contradictions and tensions",
            "output": "Conflicting knowledge"
        }
    ]

    for cmd in commands:
        print(f"\n📌 {cmd['command']}")
        print(f"   Purpose: {cmd['purpose']}")
        if 'when' in cmd:
            print(f"   Use when: {cmd['when']}")
        if 'output' in cmd:
            print(f"   Output: {cmd['output']}")

    # Workflow
    print("\n" + "=" * 70)
    print("🔄 COMPLETE WORKFLOW")
    print("=" * 70)

    print("\n1️⃣  Setup Content Sources")
    print("   • Add docs to AMPLIFIER_CONTENT_DIRS in .env")
    print("   • Include: project docs, notes, articles, wikis")

    print("\n2️⃣  Scan and Extract")
    print("   make content-scan           # Find all documents")
    print("   make knowledge-sync         # Extract knowledge")

    print("\n3️⃣  Build Knowledge Graph")
    print("   make knowledge-graph-build  # Create graph")
    print("   make knowledge-graph-stats  # Verify creation")

    print("\n4️⃣  Visualize")
    print("   make knowledge-graph-viz    # Interactive HTML")
    print("   Open in browser to explore")

    print("\n5️⃣  Query and Explore")
    print("   make knowledge-query Q='your question'")
    print("   make knowledge-graph-search Q='topic'")
    print("   make knowledge-graph-tensions")

    print("\n6️⃣  Incremental Updates")
    print("   Add new docs → make knowledge-sync")
    print("   Update graph → make knowledge-graph-update")

    # Use cases
    print("\n" + "=" * 70)
    print("📖 REAL-WORLD USE CASES")
    print("=" * 70)

    use_cases = [
        {
            "scenario": "Learning New Domain",
            "how": [
                "Add domain documentation to content dirs",
                "Extract concepts: make knowledge-sync",
                "Visualize: make knowledge-graph-viz",
                "Explore connections visually",
                "Query for specific topics",
                "Discover related concepts you didn't know about"
            ]
        },
        {
            "scenario": "Architecture Decisions",
            "how": [
                "Extract from design docs and discussions",
                "Build graph of technologies and approaches",
                "Find tensions: make knowledge-graph-tensions",
                "Identify conflicts between choices",
                "Make informed trade-off decisions"
            ]
        },
        {
            "scenario": "Team Knowledge Base",
            "how": [
                "Extract from all team documentation",
                "Find knowledge gaps",
                "Identify contradictory guidance",
                "Surface tribal knowledge",
                "Navigate expertise landscape"
            ]
        },
        {
            "scenario": "Research Synthesis",
            "how": [
                "Process multiple research papers",
                "Extract key concepts and findings",
                "Find connections between papers",
                "Identify gaps in literature",
                "Generate new research questions"
            ]
        }
    ]

    for i, use_case in enumerate(use_cases, 1):
        print(f"\n🎯 Use Case {i}: {use_case['scenario']}")
        for step in use_case['how']:
            print(f"   • {step}")

    # Advanced features
    print("\n" + "=" * 70)
    print("🚀 ADVANCED FEATURES")
    print("=" * 70)

    print("\n🔍 Tension Detection")
    print("   Automatically finds contradictory knowledge:")
    print("   • 'Use sessions' vs 'Use JWT tokens'")
    print("   • 'Microservices scale better' vs 'Monoliths are simpler'")
    print("   • Helps identify design trade-offs")

    print("\n🌐 Path Finding")
    print("   Discover how concepts connect:")
    print("   • JWT → requires → Validation → needs → Crypto")
    print("   • Performance → improved-by → Caching → enables → Scale")
    print("   • Reveals implicit dependencies")

    print("\n📊 Pattern Emergence")
    print("   Statistical analysis reveals:")
    print("   • Most central concepts (high degree)")
    print("   • Knowledge clusters (communities)")
    print("   • Isolated concepts (potential gaps)")
    print("   • Frequent patterns")

    print("\n🎨 Interactive Visualization")
    print("   HTML graph you can:")
    print("   • Click to explore")
    print("   • Search and highlight")
    print("   • Zoom and pan")
    print("   • Filter by relationship type")
    print("   • Export for presentations")

    print("\n" + "=" * 70)
    print("✅ Knowledge Graph Demo Complete!")
    print("=" * 70)

    print("\n💡 Key Takeaways:")
    print("   1. Knowledge becomes a connected graph, not isolated notes")
    print("   2. Relationships reveal implicit connections")
    print("   3. Patterns emerge from the network structure")
    print("   4. Contradictions become visible and addressable")
    print("   5. Visual exploration beats linear search")

    print("\n🎓 Why This Matters:")
    print("   • Traditional notes are isolated - graphs show connections")
    print("   • Discover insights you didn't explicitly write down")
    print("   • Navigate knowledge by meaning, not file structure")
    print("   • Surface conflicts in understanding")
    print("   • External brain that grows with you")

    print("\n🚀 Try it yourself:")
    print("   1. Add docs: echo 'AMPLIFIER_CONTENT_DIRS=docs/' >> .env")
    print("   2. Extract: make knowledge-sync")
    print("   3. Build graph: make knowledge-graph-build")
    print("   4. Visualize: make knowledge-graph-viz")
    print("   5. Explore in browser!")
    print()


if __name__ == "__main__":
    main()
