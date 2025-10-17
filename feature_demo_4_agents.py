#!/usr/bin/env python3
"""
Feature Demo #4: Specialized AI Agents
Shows Amplifier's 23 specialized agents and how they work together
"""

from pathlib import Path


def main():
    print("\n" + "=" * 70)
    print("🤖 FEATURE #4: SPECIALIZED AI AGENTS")
    print("=" * 70)

    print("\n📋 What are Specialized Agents?")
    print("   Instead of one general AI assistant, Amplifier provides 23")
    print("   specialized agents, each expert in specific tasks:")
    print()
    print("   🏗️  Architecture & Design")
    print("   🐛 Debugging & Testing")
    print("   🔒 Security & Performance")
    print("   📚 Knowledge & Analysis")
    print("   🎨 Specialized Domains")

    # List all agents
    print("\n" + "-" * 70)
    print("📊 AVAILABLE AGENTS (23 Total)")
    print("-" * 70)

    agents_dir = Path(".claude/agents")
    agents = sorted([f.stem for f in agents_dir.glob("*.md")])

    # Categorize agents
    categories = {
        "🏗️ Architecture & Design": [
            "zen-architect",
            "modular-builder",
            "module-intent-architect",
            "api-contract-designer",
            "database-architect",
            "amplifier-cli-architect",
        ],
        "🐛 Debugging & Quality": [
            "bug-hunter",
            "test-coverage",
            "post-task-cleanup",
            "ambiguity-guardian",
        ],
        "🔒 Security & Performance": ["security-guardian", "performance-optimizer"],
        "📚 Knowledge & Analysis": [
            "concept-extractor",
            "insight-synthesizer",
            "pattern-emergence",
            "analysis-engine",
            "content-researcher",
        ],
        "🎨 Specialized Domains": [
            "graph-builder",
            "visualization-architect",
            "integration-specialist",
            "contract-spec-author",
            "subagent-architect",
        ],
    }

    for category, agent_list in categories.items():
        print(f"\n{category}:")
        for agent in agent_list:
            if agent in agents:
                # Read first line of description
                agent_file = agents_dir / f"{agent}.md"
                try:
                    with open(agent_file) as f:
                        # Skip frontmatter
                        lines = f.readlines()
                        desc = ""
                        in_frontmatter = False
                        for line in lines:
                            if line.strip() == "---":
                                in_frontmatter = not in_frontmatter
                                continue
                            if not in_frontmatter and line.strip():
                                desc = line.strip()[:60]
                                break
                except Exception:
                    desc = "Specialized agent"

                print(f"   • {agent:30} - {desc}...")

    # Showcase key agents
    print("\n" + "=" * 70)
    print("⭐ SPOTLIGHT: Key Agents")
    print("=" * 70)

    showcases = [
        {
            "name": "zen-architect",
            "icon": "🏗️",
            "purpose": "Architecture design and planning",
            "when": "Designing new features, system architecture",
            "example": '"Use zen-architect to design a caching layer"',
        },
        {
            "name": "bug-hunter",
            "icon": "🐛",
            "purpose": "Systematic bug investigation",
            "when": "Tracking down elusive bugs, debugging",
            "example": '"Deploy bug-hunter to find why login fails"',
        },
        {
            "name": "security-guardian",
            "icon": "🔒",
            "purpose": "Security review and hardening",
            "when": "Code security audits, vulnerability checks",
            "example": '"Have security-guardian review my API endpoints"',
        },
        {
            "name": "test-coverage",
            "icon": "✅",
            "purpose": "Comprehensive testing strategies",
            "when": "Adding tests, improving coverage",
            "example": '"Use test-coverage to add tests for auth module"',
        },
        {
            "name": "modular-builder",
            "icon": "🧱",
            "purpose": "Implements zen-architect's designs",
            "when": "Building new modules from specs",
            "example": '"Use modular-builder to implement the cache design"',
        },
        {
            "name": "performance-optimizer",
            "icon": "⚡",
            "purpose": "Performance analysis and optimization",
            "when": "Speed issues, resource optimization",
            "example": '"Have performance-optimizer analyze slow queries"',
        },
    ]

    for agent in showcases:
        print(f"\n{agent['icon']} {agent['name'].upper()}")
        print(f"   Purpose: {agent['purpose']}")
        print(f"   Use when: {agent['when']}")
        print(f"   Example: {agent['example']}")

    # Show how to use agents
    print("\n" + "=" * 70)
    print("💡 HOW TO USE AGENTS")
    print("=" * 70)

    print("\n1️⃣  In Claude Code:")
    print('   claude> "Use the zen-architect agent to design my auth system"')
    print()
    print("   Claude will:")
    print("   • Launch the specialized agent")
    print("   • Agent analyzes with its expertise")
    print("   • Returns detailed recommendations")
    print("   • You get expert-level guidance")

    print("\n2️⃣  Agent Chaining (Multiple Experts):")
    print('   claude> "Use zen-architect to design, then modular-builder to implement"')
    print()
    print("   Benefits:")
    print("   • Design phase: Architecture expert")
    print("   • Build phase: Implementation expert")
    print("   • Each agent focuses on what it does best")

    print("\n3️⃣  Parallel Analysis:")
    print('   claude> "Use bug-hunter and security-guardian to review this code"')
    print()
    print("   Benefits:")
    print("   • Multiple perspectives simultaneously")
    print("   • Comprehensive coverage")
    print("   • Faster than sequential review")

    # Show agent philosophy
    print("\n" + "=" * 70)
    print("🎯 AGENT DESIGN PHILOSOPHY")
    print("=" * 70)

    print("\n✨ Each agent is:")
    print("   • Specialized - Focused expertise")
    print("   • Autonomous - Makes decisions independently")
    print("   • Opinionated - Strong, consistent viewpoints")
    print("   • Collaborative - Works with other agents")

    print("\n🧠 Why This Works:")
    print("   • Specialist > Generalist for complex tasks")
    print("   • Consistent philosophy per domain")
    print("   • Parallel processing via multiple agents")
    print("   • Clear separation of concerns")

    # Real examples
    print("\n" + "=" * 70)
    print("📖 REAL-WORLD SCENARIOS")
    print("=" * 70)

    scenarios = [
        {
            "task": "Build a new API endpoint",
            "workflow": [
                "1. zen-architect: Designs the endpoint architecture",
                "2. api-contract-designer: Specifies the API contract",
                "3. modular-builder: Implements the code",
                "4. test-coverage: Adds comprehensive tests",
                "5. security-guardian: Security review",
            ],
        },
        {
            "task": "Fix a performance issue",
            "workflow": [
                "1. performance-optimizer: Identifies bottlenecks",
                "2. bug-hunter: Investigates root cause",
                "3. zen-architect: Designs optimization strategy",
                "4. modular-builder: Implements improvements",
                "5. test-coverage: Validates performance gains",
            ],
        },
        {
            "task": "Extract and organize concepts",
            "workflow": [
                "1. content-researcher: Scans documentation",
                "2. concept-extractor: Pulls key concepts",
                "3. insight-synthesizer: Finds patterns",
                "4. visualization-architect: Creates concept map",
            ],
        },
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📌 Scenario {i}: {scenario['task']}")
        for step in scenario["workflow"]:
            print(f"   {step}")

    print("\n" + "=" * 70)
    print("✅ Specialized Agents Demo Complete!")
    print("=" * 70)

    print("\n💡 Key Takeaways:")
    print("   1. 23 specialized agents, each expert in their domain")
    print("   2. Use agents for better results than general AI")
    print("   3. Chain agents for complex multi-step tasks")
    print("   4. Parallel agents for comprehensive analysis")
    print("   5. Consistent philosophy within each domain")

    print("\n🚀 Try it yourself:")
    print("   1. Start Claude: claude")
    print('   2. Use an agent: "Use zen-architect to design X"')
    print("   3. Chain agents: Design → Build → Test")
    print("   4. Explore: ls .claude/agents/")
    print()


if __name__ == "__main__":
    main()
