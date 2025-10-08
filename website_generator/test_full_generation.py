#!/usr/bin/env python3
"""
Test full content generation pipeline with real Amplifier data.
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from analyzer.repo_analyzer import RepositoryAnalyzer
from config_loader import ConfigLoader
from content.content_generator import ContentGenerator


def test_full_pipeline():
    """Test the complete pipeline: analyze → configure → generate content"""

    print("🚀 Testing Full Website Generation Pipeline")
    print("=" * 50)

    # Step 1: Analyze Amplifier repository
    print("1. Analyzing Amplifier repository...")
    repo_path = "/mnt/c/Users/samschillace/amplifier"
    analyzer = RepositoryAnalyzer(repo_path)
    analysis = analyzer.analyze_repository()

    print(f"   ✓ Found {len(analysis.agents)} agents")
    print(f"   ✓ Found {len(analysis.commands)} commands")
    print(f"   ✓ Paradigm type: {analysis.paradigm_type.value}")
    print(f"   ✓ Complexity score: {analysis.complexity_score}")

    # Step 2: Load configuration
    print("\n2. Loading configuration...")
    loader = ConfigLoader()
    amplifier_config_path = Path(__file__).parent / "examples" / "amplifier_config.yaml"
    config = loader.load_full_config(str(amplifier_config_path))

    print(f"   ✓ Loaded config for: {config.site['name']}")
    print(f"   ✓ Theme: {config.site['theme']}")
    print(f"   ✓ Pages: {len(config.pages)}")

    # Step 3: Generate content
    print("\n3. Generating website content...")
    generator = ContentGenerator(config)
    content = generator.generate_content(analysis)

    print(f"   ✓ Generated revolution section: {content.revolution_section.title}")
    print(f"   ✓ Created {len(content.progressive_setup.tiers)} setup tiers")
    print(f"   ✓ Showcased {content.agent_showcase.total_count} agents")
    print(f"   ✓ Agent categories: {list(content.agent_showcase.agent_categories.keys())}")

    # Step 4: Display sample generated content
    print("\n4. Sample Generated Content:")
    print("-" * 30)

    if content.revolution_section:
        print("🎯 Revolution Section:")
        print(f"   Title: {content.revolution_section.title}")
        print(f"   Subtitle: {content.revolution_section.subtitle}")
        print(f"   Problem: {content.revolution_section.problem_statement[:100]}...")

        # Show multiplier effects
        print("\n📊 Capability Multipliers:")
        for metric in content.revolution_section.multiplier_effect["metrics"]:
            if metric.get("inverse"):
                print(
                    f"   • {metric['name']}: {metric['old_value']} → {metric['new_value']} {metric['unit']} ({metric['multiplier']}x faster)"
                )
            else:
                print(
                    f"   • {metric['name']}: {metric['old_value']} → {metric['new_value']} {metric['unit']} ({metric['multiplier']}x)"
                )

    print("\n🏗️ Progressive Setup:")
    for i, tier in enumerate(content.progressive_setup.tiers, 1):
        print(f"   {i}. {tier['name']} ({tier['duration']})")
        print(f"      Focus: {tier['focus']}")
        if "demo_command" in tier:
            print(f"      Demo: {tier['demo_command']}")

    print("\n🤖 Agent Showcase:")
    print(f"   Total agents: {content.agent_showcase.total_count}")
    for category, agents in content.agent_showcase.agent_categories.items():
        print(f"   {category}: {len(agents)} agents")

    print("\n🎨 Hero Section:")
    hero = content.hero_section
    print(f"   Title: {hero['title']}")
    print(f"   Tagline: {hero['tagline']}")
    print(f"   Features: {', '.join(hero['features_preview'])}")

    # Step 5: Export analysis and content for inspection
    print("\n5. Exporting results...")

    # Save analysis
    analysis_output = Path(__file__).parent / "output" / "amplifier_analysis.json"
    analysis_output.parent.mkdir(exist_ok=True)
    analyzer.save_analysis(analysis, str(analysis_output))

    # Save generated content as JSON for inspection
    content_output = Path(__file__).parent / "output" / "generated_content.json"
    content_dict = {
        "revolution_section": {
            "title": content.revolution_section.title,
            "subtitle": content.revolution_section.subtitle,
            "problem_statement": content.revolution_section.problem_statement,
            "paradigm_comparison": content.revolution_section.paradigm_comparison,
            "multiplier_effect": content.revolution_section.multiplier_effect,
            "role_transformation": content.revolution_section.role_transformation,
        }
        if content.revolution_section
        else None,
        "progressive_setup": {"tiers": content.progressive_setup.tiers},
        "agent_showcase": {
            "featured_agents": content.agent_showcase.featured_agents,
            "agent_categories": content.agent_showcase.agent_categories,
            "total_count": content.agent_showcase.total_count,
        },
        "hero_section": content.hero_section,
        "overview_section": content.overview_section,
        "examples_section": content.examples_section,
    }

    with open(content_output, "w", encoding="utf-8") as f:
        json.dump(content_dict, f, indent=2, ensure_ascii=False)

    print(f"   ✓ Analysis saved to: {analysis_output}")
    print(f"   ✓ Content saved to: {content_output}")

    print("\n✅ Full pipeline test completed successfully!")
    print("📁 Check the output/ directory for detailed results")

    return True


if __name__ == "__main__":
    try:
        test_full_pipeline()
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback

        traceback.print_exc()
