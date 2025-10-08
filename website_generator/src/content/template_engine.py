"""
Template engine for converting generated content into HTML.
Uses Jinja2 for template processing with custom filters and functions.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from jinja2 import Environment
    from jinja2 import FileSystemLoader
    from jinja2 import select_autoescape
except ImportError:
    print("Installing Jinja2...")
    import subprocess

    subprocess.run(["pip", "install", "jinja2"], check=True)
    from jinja2 import Environment
    from jinja2 import FileSystemLoader
    from jinja2 import select_autoescape

# Import our components
import sys

sys.path.append(str(Path(__file__).parent.parent))
from config_loader import SiteConfig
from content.content_generator import GeneratedContent


class TemplateEngine:
    """Converts generated content into HTML using Jinja2 templates"""

    def __init__(self, config: SiteConfig, templates_dir: str | None = None, css_filename: str = "styles.css"):
        self.config = config
        self.css_filename = css_filename

        if templates_dir is None:
            self.templates_dir = Path(__file__).parent.parent.parent / "templates"
        else:
            self.templates_dir = Path(templates_dir)

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters and functions
        self._setup_template_functions()

    def _setup_template_functions(self):
        """Add custom Jinja2 filters and functions"""

        # Custom filters
        self.env.filters["format_number"] = self._format_number
        self.env.filters["truncate_words"] = self._truncate_words
        self.env.filters["slug"] = self._slugify
        self.env.filters["agent_badge"] = self._agent_badge

        # Global functions
        self.env.globals["now"] = datetime.now
        self.env.globals["config"] = self.config
        self.env.globals["get_color"] = self._get_color
        self.env.globals["get_icon"] = self._get_icon

    def _format_number(self, value: int) -> str:
        """Format numbers with commas"""
        if isinstance(value, int | float):
            return f"{value:,}"
        return str(value)

    def _truncate_words(self, text: str, words: int = 20) -> str:
        """Truncate text to specified number of words"""
        if not text:
            return ""
        word_list = text.split()
        if len(word_list) <= words:
            return text
        return " ".join(word_list[:words]) + "..."

    def _slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug"""
        import re

        slug = re.sub(r"[^\w\s-]", "", text.lower())
        slug = re.sub(r"[-\s]+", "-", slug)
        return slug.strip("-")

    def _agent_badge(self, agent_name: str) -> str:
        """Get CSS class for agent badge based on category"""
        name_lower = agent_name.lower()

        if any(keyword in name_lower for keyword in ["architect", "design", "modular"]):
            return "badge-architecture"
        if any(keyword in name_lower for keyword in ["bug", "debug", "test", "security"]):
            return "badge-quality"
        if any(keyword in name_lower for keyword in ["analysis", "synthesis", "extract"]):
            return "badge-analysis"
        if any(keyword in name_lower for keyword in ["automation", "cleanup"]):
            return "badge-automation"
        return "badge-development"

    def _get_color(self, color_name: str) -> str:
        """Get color value from design system"""
        colors = self.config.design_system.get("colors", {})
        return colors.get(color_name, "#2563eb")  # Default blue

    def _get_icon(self, icon_name: str) -> str:
        """Get icon class/SVG for given icon name"""
        # Simple icon mapping - could be enhanced with actual icon library
        icon_map = {
            "agents": "🤖",
            "parallel": "⚡",
            "quality": "✅",
            "architecture": "🏗️",
            "security": "🔒",
            "testing": "🧪",
            "analysis": "📊",
            "automation": "⚙️",
            "development": "💻",
        }
        return icon_map.get(icon_name, "📄")

    def render_page(self, page_name: str, content: GeneratedContent, **kwargs) -> str:
        """Render a complete page"""
        template_name = f"{page_name}.html"

        try:
            template = self.env.get_template(template_name)
        except Exception:
            # Fall back to base template
            template = self.env.get_template("base_template.html")

        # Prepare template context
        context = {
            "content": content,
            "page_name": page_name,
            "css_filename": self.css_filename,
            "site": self.config.site,
            "design_system": self.config.design_system,
            "interactions": self.config.interactions,
            "navigation": self.config.navigation,
            "seo": self.config.seo,
            **kwargs,
        }

        return template.render(**context)

    def render_section(self, section_name: str, section_content: Any, **kwargs) -> str:
        """Render an individual section"""
        template_name = f"sections/{section_name}.html"

        try:
            template = self.env.get_template(template_name)
        except Exception as e:
            print(f"Warning: Section template {template_name} not found: {e}")
            return self._render_fallback_section(section_name, section_content)

        context = {
            "section": section_content,
            "config": self.config,
            "site": self.config.site,
            "design_system": self.config.design_system,
            "interactions": self.config.interactions,
            "navigation": self.config.navigation,
            **kwargs,
        }

        return template.render(**context)

    def _render_fallback_section(self, section_name: str, content: Any) -> str:
        """Render fallback HTML for section when template is missing"""
        if isinstance(content, dict) and "title" in content:
            return f"""
            <section class="section {section_name}-section">
                <div class="container">
                    <h2 class="section-title">{content["title"]}</h2>
                    <p>Content for {section_name} section would go here.</p>
                </div>
            </section>
            """
        return f'<div class="section-placeholder">Section: {section_name}</div>'

    def generate_full_page(self, page_config: dict[str, Any], content: GeneratedContent) -> str:
        """Generate a complete HTML page with all sections"""
        page_name = page_config["name"]
        page_title = page_config.get("title", page_name.title())
        sections = page_config.get("sections", [])

        # Render all sections
        rendered_sections = []
        for section_name in sections:
            section_content = self._get_section_content(section_name, content)
            if section_content:
                rendered_section = self.render_section(section_name, section_content)
                rendered_sections.append(rendered_section)

        # Create page context
        page_context = {
            "page_title": page_title,
            "current_page": page_name,  # Renamed to avoid collision
            "sections_html": "\n".join(rendered_sections),
            "meta_description": self._generate_meta_description(content),
        }

        # Render complete page
        return self.render_page("index", content, **page_context)

    def _get_section_content(self, section_name: str, content: GeneratedContent) -> Any | None:
        """Get content for a specific section"""
        section_map = {
            "revolution": content.revolution_section,
            "hero": content.hero_section,
            "overview": content.overview_section,
            "features": content.overview_section,
            "agent_showcase": content.agent_showcase,
            "agents": content.agent_showcase,
            "agent_gallery": content.agent_showcase,
            "agent_categories": content.agent_showcase,
            "workflow_examples": content.agent_showcase,
            "custom_agents": content.agent_showcase,
            "progressive_setup": content.progressive_setup,
            "progressive_tiers": content.progressive_setup,
            "quick_setup": content.progressive_setup,
            "installation": content.progressive_setup,
            "first_agent": content.progressive_setup,
            "troubleshooting": content.progressive_setup,
            "examples": content.examples_section,
            "cta": {"title": "Get Started", "description": "Ready to transform your development?"},
        }

        return section_map.get(section_name)

    def _generate_meta_description(self, content: GeneratedContent) -> str:
        """Generate meta description from content"""
        if content.hero_section:
            return content.hero_section.get("description", "")
        if content.revolution_section:
            return content.revolution_section.problem_statement[:160] + "..."
        return f"{self.config.site['name']} - {self.config.site.get('tagline', '')}"

    def create_base_templates(self):
        """Create basic HTML templates if they don't exist"""
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        sections_dir = self.templates_dir / "sections"
        sections_dir.mkdir(exist_ok=True)

        # Base template
        base_template = self.templates_dir / "base_template.html"
        if not base_template.exists():
            base_html = self._get_base_template_html()
            with open(base_template, "w", encoding="utf-8") as f:
                f.write(base_html)

        # Page templates - create for all configured pages
        page_template_html = self._get_index_template_html()
        for page_config in self.config.pages:
            page_name = page_config["name"]
            page_template = self.templates_dir / f"{page_name}.html"
            if not page_template.exists():
                with open(page_template, "w", encoding="utf-8") as f:
                    f.write(page_template_html)

        # Section templates
        section_templates = {
            "revolution.html": self._get_revolution_section_html(),
            "hero.html": self._get_hero_section_html(),
            "agent_showcase.html": self._get_agent_showcase_html(),
            "agents.html": self._get_agent_showcase_html(),  # Alias
            "agent_gallery.html": self._get_agent_showcase_html(),  # Agents page sections
            "agent_categories.html": self._get_agent_showcase_html(),
            "workflow_examples.html": self._get_agent_showcase_html(),
            "custom_agents.html": self._get_agent_showcase_html(),
            "progressive_setup.html": self._get_progressive_setup_html(),
            "setup.html": self._get_progressive_setup_html(),  # Alias
            "progressive_tiers.html": self._get_progressive_setup_html(),  # Setup page sections
            "installation.html": self._get_progressive_setup_html(),
            "first_agent.html": self._get_progressive_setup_html(),
            "troubleshooting.html": self._get_progressive_setup_html(),
            "overview.html": self._get_overview_section_html(),  # Missing sections
            "quick_setup.html": self._get_progressive_setup_html(),
            "examples.html": self._get_examples_section_html(),
            "cta.html": self._get_cta_section_html(),
        }

        for template_name, template_html in section_templates.items():
            template_file = sections_dir / template_name
            if not template_file.exists():
                with open(template_file, "w", encoding="utf-8") as f:
                    f.write(template_html)

        print(f"✓ Created base templates in {self.templates_dir}")

    def _get_base_template_html(self) -> str:
        """Get base HTML template"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ page_title }} - {{ site.name }}</title>
    <meta name="description" content="{{ meta_description }}">

    <!-- SEO -->
    <meta property="og:title" content="{{ page_title }} - {{ site.name }}">
    <meta property="og:description" content="{{ meta_description }}">
    <meta property="og:type" content="website">

    <!-- Styles -->
    <link rel="stylesheet" href="{{ css_filename }}">

    <!-- Custom colors from design system -->
    <style>
        :root {
            --primary-color: {{ get_color('primary') }};
            --secondary-color: {{ get_color('secondary') }};
            --accent-color: {{ get_color('accent') }};
            --background-color: {{ get_color('background') }};
            --text-primary: {{ get_color('text_primary') }};
            --text-secondary: {{ get_color('text_secondary') }};
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <header class="header">
        <nav class="nav">
            <div class="nav-brand">
                <h1>{{ site.name }}</h1>
            </div>
            <ul class="nav-links">
                <li><a href="#hero">Home</a></li>
                {% if content.agent_showcase %}
                <li><a href="#agents">Agents</a></li>
                {% endif %}
                <li><a href="#examples">Examples</a></li>
                <li><a href="#setup">Setup</a></li>
            </ul>
        </nav>
    </header>

    <!-- Main Content -->
    <main>
        {{ sections_html | safe }}
    </main>

    <!-- Footer -->
    <footer class="footer">
        <div class="container">
            <p>&copy; {{ now().year }} {{ site.name }}. Built with Website Generator.</p>
        </div>
    </footer>

    <!-- JavaScript -->
    <script src="script.js"></script>
</body>
</html>"""

    def _get_index_template_html(self) -> str:
        """Get index page template (extends base)"""
        return """{% extends "base_template.html" %}

{% block content %}
{{ sections_html | safe }}
{% endblock %}"""

    def _get_revolution_section_html(self) -> str:
        """Get revolution section template"""
        return """<section class="revolution-section" id="revolution">
    <div class="container">
        <div class="revolution-content">
            <h2 class="revolution-title">{{ section.title }}</h2>
            <h3 class="revolution-subtitle">{{ section.subtitle }}</h3>

            <div class="problem-statement">
                <p>{{ section.problem_statement }}</p>
            </div>

            {% if section.multiplier_effect %}
            <div class="multiplier-showcase">
                <h4>Capability Multiplication</h4>
                <div class="metrics-grid">
                    {% for metric in section.multiplier_effect.metrics %}
                    <div class="metric-card">
                        <div class="metric-name">{{ metric.name }}</div>
                        <div class="metric-comparison">
                            <span class="old-value">{{ metric.old_value | format_number }}</span>
                            <span class="arrow">→</span>
                            <span class="new-value"
                                  {% if interactions.animated_counters %}
                                  data-counter="{{ metric.new_value }}"
                                  {% endif %}>
                                {{ metric.new_value | format_number }}
                            </span>
                        </div>
                        <div class="metric-unit">{{ metric.unit }}</div>
                        <div class="metric-multiplier">{{ metric.multiplier }}x {% if metric.inverse %}faster{% else %}more{% endif %}</div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}

            {% if section.paradigm_comparison %}
            <div class="paradigm-comparison">
                <h4>The Paradigm Shift</h4>
                <div class="comparison-grid">
                    {% for category in section.paradigm_comparison.categories %}
                    <div class="comparison-row">
                        <div class="category-name">{{ category.name }}</div>
                        <div class="before">{{ category.before }}</div>
                        <div class="after">{{ category.after }}</div>
                        <div class="improvement">{{ category.improvement }}</div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}

            {% if section.role_transformation %}
            <div class="role-transformation">
                <h4>Your Role Evolution</h4>
                <div class="transformation-grid">
                    <div class="old-role">
                        <h5>{{ section.role_transformation.old_role.title }}</h5>
                        <ul>
                            {% for char in section.role_transformation.old_role.characteristics %}
                            <li>{{ char }}</li>
                            {% endfor %}
                        </ul>
                    </div>
                    <div class="transformation-arrow">→</div>
                    <div class="new-role">
                        <h5>{{ section.role_transformation.new_role.title }}</h5>
                        <ul>
                            {% for char in section.role_transformation.new_role.characteristics %}
                            <li>{{ char }}</li>
                            {% endfor %}
                        </ul>
                    </div>
                </div>
                {% if section.role_transformation.transformation_message %}
                <p class="transformation-message">{{ section.role_transformation.transformation_message }}</p>
                {% endif %}
            </div>
            {% endif %}
        </div>
    </div>
</section>"""

    def _get_hero_section_html(self) -> str:
        """Get hero section template"""
        return """<section class="hero-section" id="hero">
    <div class="container">
        <div class="hero-content">
            <h1 class="hero-title">{{ section.title }}</h1>
            <p class="hero-tagline">{{ section.tagline }}</p>
            <p class="hero-description">{{ section.description }}</p>

            {% if section.features_preview %}
            <div class="features-preview">
                {% for feature in section.features_preview %}
                <span class="feature-badge">{{ feature }}</span>
                {% endfor %}
            </div>
            {% endif %}

            <div class="hero-actions">
                <a href="#setup" class="btn btn-primary">{{ section.cta_primary }}</a>
                <a href="#examples" class="btn btn-secondary">{{ section.cta_secondary }}</a>
            </div>
        </div>
    </div>
</section>"""

    def _get_agent_showcase_html(self) -> str:
        """Get agent showcase section template"""
        return """<section class="agents-section" id="agents">
    <div class="container">
        <h2 class="section-title">
            {% if section.total_count > 20 %}
            {{ section.total_count }}+ Specialized Agents
            {% else %}
            Specialized Agents
            {% endif %}
        </h2>
        <p class="section-description">Expert AI agents handle every aspect of development</p>

        {% if section.agent_categories %}
        <div class="agent-categories">
            <div class="category-tabs">
                {% for category, agents in section.agent_categories.items() %}
                <button class="tab-btn {% if loop.first %}active{% endif %}"
                        onclick="showTab('{{ category | slug }}', this)">
                    {{ get_icon(category | lower) }} {{ category }} ({{ agents | length }})
                </button>
                {% endfor %}
            </div>

            {% for category, agents in section.agent_categories.items() %}
            <div class="tab-content {% if loop.first %}active{% endif %}" id="{{ category | slug }}">
                <div class="agents-list">
                    {% for agent in agents %}
                    <div class="agent-card rich-agent-card">
                        <div class="agent-header">
                            <div class="agent-name">{{ agent.name }}</div>
                            <span class="agent-category {{ agent.name | agent_badge }}">{{ agent.category }}</span>
                        </div>
                        <div class="agent-body">
                            <p class="agent-description">{{ agent.description }}</p>

                            {% if agent.capabilities %}
                            <div class="agent-features">
                                <h4>Key Capabilities</h4>
                                <ul>
                                    {% for capability in agent.capabilities %}
                                    <li>{{ capability }}</li>
                                    {% endfor %}
                                </ul>
                            </div>
                            {% endif %}

                            {% if agent.use_cases %}
                            <div class="agent-use-cases">
                                <h4>Common Use Cases</h4>
                                <ul>
                                    {% for use_case in agent.use_cases %}
                                    <li>{{ use_case }}</li>
                                    {% endfor %}
                                </ul>
                            </div>
                            {% endif %}

                            {% if agent.example_usage %}
                            <div class="agent-example">
                                <h4>Example Usage</h4>
                                <div class="example-command">
                                    <pre>{{ agent.example_usage }}</pre>
                                </div>
                                {% if agent.example_output %}
                                <p class="example-output">{{ agent.example_output }}</p>
                                {% endif %}
                            </div>
                            {% endif %}

                            <details class="advanced-section">
                                <summary>Advanced Details & Examples</summary>
                                <div class="examples-container">
                                    <div class="example-card">
                                        <h5>Integration Pattern</h5>
                                        <p>This agent integrates seamlessly with other Amplifier agents and can be used in multi-agent workflows for complex development tasks.</p>
                                    </div>
                                    {% if agent.file_path %}
                                    <div class="example-card">
                                        <h5>Configuration</h5>
                                        <p>Agent definition: <code>{{ agent.file_path }}</code></p>
                                    </div>
                                    {% endif %}
                                </div>
                            </details>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
</section>"""

    def _get_progressive_setup_html(self) -> str:
        """Get progressive setup section template"""
        return """<section class="setup-section" id="setup">
    <div class="container">
        <h2 class="section-title">Progressive Setup</h2>
        <p class="section-description">Choose your learning path based on available time</p>

        <div class="setup-tiers">
            {% for tier in section.tiers %}
            <div class="tier-card" data-tier="{{ loop.index }}">
                <div class="tier-header">
                    <h3 class="tier-name">{{ tier.name }}</h3>
                    <span class="tier-duration">{{ tier.duration }}</span>
                </div>
                <p class="tier-description">{{ tier.description }}</p>
                <p class="tier-focus"><strong>Focus:</strong> {{ tier.focus }}</p>

                {% if tier.steps %}
                <ol class="tier-steps">
                    {% for step in tier.steps %}
                    <li>{{ step }}</li>
                    {% endfor %}
                </ol>
                {% endif %}

                {% if tier.demo_command %}
                <div class="tier-demo">
                    <strong>Try this:</strong>
                    <code>{{ tier.demo_command }}</code>
                    {% if tier.expected_result %}
                    <p><em>Expected: {{ tier.expected_result }}</em></p>
                    {% endif %}
                </div>
                {% endif %}

                {% if tier.mastery_features %}
                <div class="mastery-features">
                    <strong>What you'll master:</strong>
                    <ul>
                        {% for feature in tier.mastery_features %}
                        <li>{{ feature }}</li>
                        {% endfor %}
                    </ul>
                </div>
                {% endif %}

                <button class="btn btn-outline tier-btn">Start {{ tier.name }}</button>
            </div>
            {% endfor %}
        </div>
    </div>
</section>"""

    def _get_overview_section_html(self) -> str:
        """Get overview section template"""
        return """<section class="overview-section" id="overview">
    <div class="container">
        <h2 class="section-title">System Overview</h2>
        <p class="section-description">{{ section.description | default("Understanding how Amplifier transforms development") }}</p>

        <div class="overview-grid">
            <div class="overview-card">
                <div class="overview-icon">🎯</div>
                <h3>Smart Agents</h3>
                <p>23+ specialized agents handle different aspects of development</p>
            </div>
            <div class="overview-card">
                <div class="overview-icon">⚡</div>
                <h3>Parallel Processing</h3>
                <p>Run multiple workflows simultaneously for maximum efficiency</p>
            </div>
            <div class="overview-card">
                <div class="overview-icon">🔗</div>
                <h3>Modular Architecture</h3>
                <p>Clean, maintainable components that work together seamlessly</p>
            </div>
        </div>
    </div>
</section>"""

    def _get_examples_section_html(self) -> str:
        """Get examples section template"""
        return """<section class="examples-section" id="examples">
    <div class="container">
        <h2 class="section-title">Real-World Examples</h2>
        <p class="section-description">See Amplifier in action with practical workflows</p>

        <div class="examples-grid">
            <div class="example-card">
                <h4>Bug Investigation</h4>
                <div class="example-command">
                    <pre>Use bug-hunter to investigate database timeout errors</pre>
                </div>
                <p class="example-result">→ Complete root cause analysis with fix recommendations</p>
            </div>

            <div class="example-card">
                <h4>Security Review</h4>
                <div class="example-command">
                    <pre>Use security-guardian to review API endpoints before deployment</pre>
                </div>
                <p class="example-result">→ Comprehensive security report with vulnerability fixes</p>
            </div>

            <div class="example-card">
                <h4>Architecture Design</h4>
                <div class="example-command">
                    <pre>Use zen-architect to design a notification system</pre>
                </div>
                <p class="example-result">→ Complete modular specification ready for implementation</p>
            </div>
        </div>
    </div>
</section>"""

    def _get_cta_section_html(self) -> str:
        """Get call-to-action section template"""
        return """<section class="cta-section" id="get-started">
    <div class="container">
        <div class="cta-content">
            <h2 class="cta-title">{{ section.title | default("Ready to Transform Your Development?") }}</h2>
            <p class="cta-description">{{ section.description | default("Join developers who've already experienced the paradigm shift") }}</p>

            <div class="cta-buttons">
                <a href="#setup" class="btn btn-primary btn-lg">Get Started</a>
                <a href="{{ config.site.repo_url | default('#') }}" class="btn btn-outline btn-lg">View on GitHub</a>
            </div>

            <p class="cta-note">Free and open source • No signup required • 5 minute setup</p>
        </div>
    </div>
</section>"""


def test_template_engine():
    """Test the template engine with generated content"""
    print("🎨 Testing Template Engine")
    print("=" * 30)

    # Load configuration
    from config_loader import ConfigLoader

    loader = ConfigLoader()
    config = loader.load_full_config()

    # Create template engine
    engine = TemplateEngine(config)

    # Create base templates
    print("Creating base templates...")
    engine.create_base_templates()

    # Create mock content for testing
    from content.content_generator import AgentShowcase
    from content.content_generator import GeneratedContent
    from content.content_generator import ProgressiveSetup
    from content.content_generator import RevolutionContent

    mock_revolution = RevolutionContent(
        title="The Development Revolution",
        subtitle="Why Amplifier Changes Everything",
        problem_statement="Traditional development is slow and complex.",
        paradigm_comparison={
            "categories": [{"name": "Speed", "before": "Hours", "after": "Minutes", "improvement": "10x faster"}]
        },
        multiplier_effect={
            "metrics": [{"name": "Ideas", "old_value": 50, "new_value": 1250, "unit": "per month", "multiplier": 25}]
        },
        role_transformation={
            "old_role": {"title": "Traditional Developer", "characteristics": ["Code manually"]},
            "new_role": {"title": "AI Architect", "characteristics": ["Orchestrate agents"]},
        },
    )

    mock_setup = ProgressiveSetup(
        tiers=[{"name": "Quick Taste", "duration": "1 minute", "description": "Try it now", "focus": "First agent"}]
    )

    mock_showcase = AgentShowcase(
        featured_agents=[
            {
                "name": "zen-architect",
                "description": "System design",
                "capabilities": ["architecture"],
                "category": "Architecture",
            }
        ],
        agent_categories={
            "Architecture": [{"name": "zen-architect", "description": "System design", "capabilities_count": 5}]
        },
        total_count=23,
    )

    mock_content = GeneratedContent(
        revolution_section=mock_revolution,
        progressive_setup=mock_setup,
        agent_showcase=mock_showcase,
        hero_section={
            "title": "Amplifier",
            "tagline": "Supercharged Development",
            "description": "Transform your workflow",
        },
        overview_section={"title": "Overview", "key_points": []},
        examples_section={"title": "Examples", "examples": []},
    )

    # Test section rendering
    print("Testing section rendering...")
    revolution_html = engine.render_section("revolution", mock_revolution)
    print(f"✓ Revolution section: {len(revolution_html)} characters")

    hero_html = engine.render_section("hero", mock_content.hero_section)
    print(f"✓ Hero section: {len(hero_html)} characters")

    # Test full page generation
    print("Testing full page generation...")
    page_config = {"name": "index", "title": "Home", "sections": ["hero", "revolution", "agents", "setup"]}
    full_html = engine.generate_full_page(page_config, mock_content)
    print(f"✓ Full page: {len(full_html)} characters")

    # Save test output
    output_dir = Path(__file__).parent.parent.parent / "output"
    output_dir.mkdir(exist_ok=True)

    with open(output_dir / "test_page.html", "w", encoding="utf-8") as f:
        f.write(full_html)

    print(f"✓ Test page saved to: {output_dir / 'test_page.html'}")
    print("✅ Template engine test completed successfully!")

    return True


if __name__ == "__main__":
    test_template_engine()
