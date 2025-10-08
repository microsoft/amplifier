#!/usr/bin/env python3
"""
Test complete website generation: analyze → configure → generate content → create templates → render HTML + CSS
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from analyzer.repo_analyzer import RepositoryAnalyzer
from config_loader import ConfigLoader
from content.content_generator import ContentGenerator
from content.template_engine import TemplateEngine
from style.css_generator import CSSGenerator


def test_complete_website_generation():
    """Test the complete website generation pipeline"""

    print("🌐 Testing Complete Website Generation Pipeline")
    print("=" * 60)

    output_dir = Path(__file__).parent / "output" / "amplifier_website"
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: Analyze Amplifier repository
        print("1. 📊 Analyzing Amplifier repository...")
        repo_path = "/mnt/c/Users/samschillace/amplifier"
        analyzer = RepositoryAnalyzer(repo_path)
        analysis = analyzer.analyze_repository()

        print(f"   ✓ Detected paradigm: {analysis.paradigm_type.value}")
        print(f"   ✓ Found {len(analysis.agents)} agents")
        print(f"   ✓ Found {len(analysis.commands)} commands")
        print(f"   ✓ Complexity score: {analysis.complexity_score}")

        # Step 2: Load configuration
        print("\n2. ⚙️ Loading configuration...")
        loader = ConfigLoader()
        amplifier_config_path = Path(__file__).parent / "examples" / "amplifier_config.yaml"
        config = loader.load_full_config(str(amplifier_config_path))

        print(f"   ✓ Site name: {config.site['name']}")
        print(f"   ✓ Theme: {config.site['theme']}")
        print(f"   ✓ Pages to generate: {len(config.pages)}")

        # Step 3: Generate content
        print("\n3. 📝 Generating website content...")
        content_generator = ContentGenerator(config)
        content = content_generator.generate_content(analysis)

        print(f"   ✓ Revolution section: {content.revolution_section.title}")
        print(f"   ✓ Setup tiers: {len(content.progressive_setup.tiers)}")
        print(f"   ✓ Agent showcase: {content.agent_showcase.total_count} agents")
        print(f"   ✓ Hero section: {content.hero_section['title']}")

        # Step 4: Initialize template engine
        print("\n4. 🎨 Setting up template engine...")
        templates_dir = output_dir / "templates"
        css_filename = "amplifier-styles.css"
        template_engine = TemplateEngine(config, str(templates_dir), css_filename)
        template_engine.create_base_templates()

        print(f"   ✓ Templates created in: {templates_dir}")

        # Step 5: Generate CSS
        print("\n5. 🎨 Generating CSS stylesheet...")
        css_generator = CSSGenerator(config)
        css_path = output_dir / "amplifier-styles.css"
        css_generator.save_css(str(css_path))

        # Step 6: Generate HTML pages
        print("\n6. 📄 Generating HTML pages...")

        for page_config in config.pages:
            page_name = page_config["name"]
            print(f"   Generating {page_name}.html...")

            # Generate HTML for this page
            html_content = template_engine.generate_full_page(page_config, content)

            # Save HTML file
            html_path = output_dir / f"{page_name}.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            print(f"   ✓ {page_name}.html ({len(html_content):,} characters)")

        # Step 7: Create additional assets
        print("\n7. 📁 Creating additional assets...")

        # Create basic JavaScript file
        js_content = """// Basic website JavaScript
document.addEventListener('DOMContentLoaded', function() {
    console.log('Amplifier website loaded');

    // Tab functionality
    window.showTab = function(tabId, buttonElement) {
        // Hide all tab contents
        const tabContents = document.querySelectorAll('.tab-content');
        tabContents.forEach(content => content.classList.remove('active'));

        // Remove active class from all buttons
        const tabBtns = document.querySelectorAll('.tab-btn');
        tabBtns.forEach(btn => btn.classList.remove('active'));

        // Show selected tab and mark button as active
        const targetTab = document.getElementById(tabId);
        if (targetTab) {
            targetTab.classList.add('active');
        }

        if (buttonElement) {
            buttonElement.classList.add('active');
        }
    };

    // Counter animation
    const animateCounters = () => {
        const counters = document.querySelectorAll('[data-counter]');
        counters.forEach(counter => {
            const target = parseInt(counter.getAttribute('data-counter'));
            const duration = 2000;
            const start = performance.now();

            const updateCounter = (currentTime) => {
                const elapsed = currentTime - start;
                const progress = Math.min(elapsed / duration, 1);
                const easeOut = 1 - Math.pow(1 - progress, 3);
                const current = Math.floor(target * easeOut);

                counter.textContent = current.toLocaleString();

                if (progress < 1) {
                    requestAnimationFrame(updateCounter);
                }
            };

            requestAnimationFrame(updateCounter);
        });
    };

    // Trigger counter animation when revolution section is visible
    const revolutionSection = document.getElementById('revolution');
    if (revolutionSection) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateCounters();
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });

        observer.observe(revolutionSection);
    }

    // Smooth scrolling for navigation links
    const navLinks = document.querySelectorAll('a[href^="#"]');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);

            if (targetElement) {
                const headerHeight = 80; // Approximate header height
                const targetPosition = targetElement.offsetTop - headerHeight;

                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
});"""

        js_path = output_dir / "script.js"
        with open(js_path, "w", encoding="utf-8") as f:
            f.write(js_content)
        print(f"   ✓ script.js ({len(js_content):,} characters)")

        # Create a simple README for the generated website
        readme_content = f"""# Generated Amplifier Website

This website was automatically generated using the Website Generator tool.

## Generated Files

- `index.html` - Main homepage
- `setup.html` - Setup and installation guide
- `agents.html` - Agent showcase
- `amplifier-styles.css` - Complete stylesheet
- `script.js` - Interactive JavaScript

## Site Information

- **Project**: {config.site["name"]}
- **Theme**: {config.site["theme"]}
- **Paradigm Type**: {analysis.paradigm_type.value}
- **Agents**: {len(analysis.agents)}
- **Commands**: {len(analysis.commands)}
- **Complexity Score**: {analysis.complexity_score}

## Generation Summary

- **Revolution Section**: ✓ Generated with capability multipliers
- **Progressive Setup**: ✓ {len(content.progressive_setup.tiers)} tiers
- **Agent Showcase**: ✓ {content.agent_showcase.total_count} agents in {len(content.agent_showcase.agent_categories)} categories
- **Responsive Design**: ✓ Mobile, tablet, desktop breakpoints
- **Animations**: ✓ {config.design_system["animation_level"]} level animations

## View the Website

1. Open `index.html` in a web browser
2. Or serve with a local server:
   ```bash
   python -m http.server 8000
   ```

Generated on {content.hero_section.get("title", "Unknown Date")}
"""

        readme_path = output_dir / "README.md"
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)
        print("   ✓ README.md")

        # Step 8: Generate summary report
        print("\n8. 📋 Generating summary report...")

        summary_report = {
            "generation_info": {
                "timestamp": "2025-01-24",
                "repository_analyzed": repo_path,
                "config_used": str(amplifier_config_path),
            },
            "analysis_results": {
                "paradigm_type": analysis.paradigm_type.value,
                "agents_found": len(analysis.agents),
                "commands_found": len(analysis.commands),
                "complexity_score": analysis.complexity_score,
                "paradigm_indicators": analysis.paradigm_indicators,
            },
            "content_generated": {
                "has_revolution_section": content.revolution_section is not None,
                "setup_tiers": len(content.progressive_setup.tiers),
                "featured_agents": len(content.agent_showcase.featured_agents),
                "agent_categories": list(content.agent_showcase.agent_categories.keys()),
                "total_agents": content.agent_showcase.total_count,
            },
            "files_generated": {
                "html_pages": len(config.pages),
                "css_file": "amplifier-styles.css",
                "js_file": "script.js",
                "templates_created": True,
                "readme_included": True,
            },
        }

        report_path = output_dir / "generation_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(summary_report, f, indent=2, ensure_ascii=False)

        print("   ✓ generation_report.json")

        # Final summary
        print("\n✅ Complete website generation successful!")
        print("=" * 60)
        print(f"📁 Output directory: {output_dir}")
        print("🌐 Website files generated:")

        for file_path in output_dir.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(output_dir)
                size = file_path.stat().st_size
                print(f"   • {rel_path} ({size:,} bytes)")

        print("\n🚀 To view the website:")
        print(f"   1. cd {output_dir}")
        print("   2. python -m http.server 8000")
        print("   3. Open http://localhost:8000")

        print("\n🎯 Key Features Generated:")
        if content.revolution_section:
            print(
                f"   • Revolution section with {len(content.revolution_section.multiplier_effect['metrics'])} capability multipliers"
            )
            print(
                f"   • Role transformation: {content.revolution_section.role_transformation['old_role']['title']} → {content.revolution_section.role_transformation['new_role']['title']}"
            )
        print(f"   • Progressive setup with {len(content.progressive_setup.tiers)} tiers")
        print(
            f"   • {content.agent_showcase.total_count} agents organized into {len(content.agent_showcase.agent_categories)} categories"
        )
        print(f"   • Responsive design with {len(config.responsive.get('breakpoints', {}))} breakpoints")
        print(f"   • {config.design_system['animation_level']} level animations")

        return True

    except Exception as e:
        print(f"❌ Website generation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_complete_website_generation()
