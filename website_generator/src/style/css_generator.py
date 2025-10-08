"""
CSS generator for website styling.
Generates CSS based on design system configuration.
"""

import sys
from pathlib import Path

# Import our components
sys.path.append(str(Path(__file__).parent.parent))
from config_loader import SiteConfig


class CSSGenerator:
    """Generates CSS from design system configuration"""

    def __init__(self, config: SiteConfig):
        self.config = config
        self.design_system = config.design_system
        self.colors = self.design_system.get("colors", {})
        self.responsive = config.responsive

    def generate_full_css(self) -> str:
        """Generate complete CSS stylesheet"""
        css_parts = [
            self._generate_css_reset(),
            self._generate_css_variables(),
            self._generate_base_styles(),
            self._generate_layout_styles(),
            self._generate_component_styles(),
            self._generate_section_styles(),
            self._generate_responsive_styles(),
            self._generate_animation_styles(),
        ]

        return "\n\n".join(css_parts)

    def _generate_css_reset(self) -> str:
        """Generate CSS reset and base styles"""
        return """/* CSS Reset and Base Styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

html {
    scroll-behavior: smooth;
    font-size: 16px;
    line-height: 1.6;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
    background-color: var(--background-color);
    color: var(--text-primary);
    overflow-x: hidden;
}

img {
    max-width: 100%;
    height: auto;
}

a {
    text-decoration: none;
    color: inherit;
}

button {
    border: none;
    background: none;
    cursor: pointer;
    font: inherit;
}

ul, ol {
    list-style: none;
}"""

    def _generate_css_variables(self) -> str:
        """Generate CSS custom properties from design system"""
        vars_css = "/* CSS Custom Properties */\n:root {\n"

        # Colors
        for color_name, color_value in self.colors.items():
            css_name = color_name.replace("_", "-")
            vars_css += f"    --{css_name}: {color_value};\n"

        # Typography
        if self.design_system.get("typography") == "inter_modern":
            vars_css += """    --font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-size-xs: 0.75rem;
    --font-size-sm: 0.875rem;
    --font-size-base: 1rem;
    --font-size-lg: 1.125rem;
    --font-size-xl: 1.25rem;
    --font-size-2xl: 1.5rem;
    --font-size-3xl: 1.875rem;
    --font-size-4xl: 2.25rem;
    --font-size-5xl: 3rem;
"""

        # Spacing
        vars_css += """    --spacing-xs: 0.25rem;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    --spacing-xl: 2rem;
    --spacing-2xl: 3rem;
    --spacing-3xl: 4rem;
    --spacing-4xl: 6rem;
"""

        # Shadows
        vars_css += """    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
"""

        # Border radius
        vars_css += """    --radius-sm: 0.25rem;
    --radius: 0.5rem;
    --radius-md: 0.75rem;
    --radius-lg: 1rem;
    --radius-xl: 1.5rem;
"""

        # Responsive breakpoints
        if self.responsive:
            breakpoints = self.responsive.get("breakpoints", {})
            for bp_name, bp_value in breakpoints.items():
                vars_css += f"    --breakpoint-{bp_name}: {bp_value};\n"

        vars_css += "}"
        return vars_css

    def _generate_base_styles(self) -> str:
        """Generate base typography and element styles"""
        return """/* Base Typography and Elements */
body {
    font-family: var(--font-family, -apple-system, BlinkMacSystemFont, sans-serif);
    font-size: var(--font-size-base);
    line-height: 1.6;
}

h1, h2, h3, h4, h5, h6 {
    font-weight: 600;
    line-height: 1.2;
    margin-bottom: var(--spacing-md);
    color: var(--text-primary);
}

h1 { font-size: var(--font-size-4xl); }
h2 { font-size: var(--font-size-3xl); }
h3 { font-size: var(--font-size-2xl); }
h4 { font-size: var(--font-size-xl); }
h5 { font-size: var(--font-size-lg); }
h6 { font-size: var(--font-size-base); }

p {
    margin-bottom: var(--spacing-md);
    color: var(--text-secondary);
}

strong {
    font-weight: 600;
    color: var(--text-primary);
}

code {
    font-family: 'SF Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace;
    font-size: 0.875em;
    background: var(--surface, #f8fafc);
    padding: 0.125rem 0.25rem;
    border-radius: var(--radius-sm);
    border: 1px solid var(--border, #e5e7eb);
}

pre {
    background: var(--surface, #f8fafc);
    padding: var(--spacing-lg);
    border-radius: var(--radius);
    border: 1px solid var(--border, #e5e7eb);
    overflow-x: auto;
    margin-bottom: var(--spacing-lg);
}

pre code {
    background: none;
    padding: 0;
    border: none;
}"""

    def _generate_layout_styles(self) -> str:
        """Generate layout and grid styles"""
        return """/* Layout Styles */
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 var(--spacing-lg);
}

.section {
    padding: var(--spacing-4xl) 0;
}

.section-title {
    font-size: var(--font-size-3xl);
    font-weight: 700;
    text-align: center;
    margin-bottom: var(--spacing-lg);
    color: var(--text-primary);
}

.section-description {
    font-size: var(--font-size-lg);
    text-align: center;
    margin-bottom: var(--spacing-3xl);
    color: var(--text-secondary);
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
}

/* Grid Systems */
.grid {
    display: grid;
    gap: var(--spacing-lg);
}

.grid-2 { grid-template-columns: repeat(2, 1fr); }
.grid-3 { grid-template-columns: repeat(3, 1fr); }
.grid-4 { grid-template-columns: repeat(4, 1fr); }

.flex {
    display: flex;
    gap: var(--spacing-md);
}

.flex-center {
    justify-content: center;
    align-items: center;
}

.flex-between {
    justify-content: space-between;
    align-items: center;
}

.flex-col {
    flex-direction: column;
}"""

    def _generate_component_styles(self) -> str:
        """Generate component styles"""
        # Animation level for future component styling
        # animation_level = self.design_system.get("animation_level", "engaging")

        # Button styles
        btn_styles = """/* Button Components */
.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: var(--spacing-sm) var(--spacing-lg);
    font-size: var(--font-size-base);
    font-weight: 500;
    border-radius: var(--radius);
    cursor: pointer;
    text-decoration: none;
    border: none;
    transition: all 0.2s ease;
    gap: var(--spacing-xs);
}

.btn-primary {
    background: var(--primary-color);
    color: white;
}

.btn-primary:hover {
    background: var(--secondary-color);
    transform: translateY(-1px);
}

.btn-secondary {
    background: transparent;
    color: var(--primary-color);
    border: 2px solid var(--primary-color);
}

.btn-secondary:hover {
    background: var(--primary-color);
    color: white;
}

.btn-outline {
    background: transparent;
    color: var(--text-primary);
    border: 1px solid var(--border, #e5e7eb);
}

.btn-outline:hover {
    background: var(--surface, #f8fafc);
    border-color: var(--primary-color);
}"""

        # Card styles
        card_styles = """
/* Card Components */
.card {
    background: white;
    border-radius: var(--radius-lg);
    padding: var(--spacing-xl);
    box-shadow: var(--shadow);
    border: 1px solid var(--border, #e5e7eb);
    transition: all 0.3s ease;
}

.card:hover {
    box-shadow: var(--shadow-lg);
    transform: translateY(-2px);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: var(--spacing-md);
}

.card-title {
    font-size: var(--font-size-lg);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
}

.card-description {
    color: var(--text-secondary);
    margin-bottom: var(--spacing-md);
}"""

        # Badge styles
        badge_styles = """
/* Badge Components */
.badge {
    display: inline-flex;
    align-items: center;
    padding: 0.25rem 0.75rem;
    font-size: var(--font-size-sm);
    font-weight: 500;
    border-radius: var(--radius-xl);
    text-transform: uppercase;
    letter-spacing: 0.025em;
}

.badge-architecture {
    background: rgba(59, 130, 246, 0.1);
    color: var(--primary-color);
}

.badge-quality {
    background: rgba(16, 185, 129, 0.1);
    color: var(--success, #10b981);
}

.badge-analysis {
    background: rgba(139, 92, 246, 0.1);
    color: #8b5cf6;
}

.badge-automation {
    background: rgba(245, 158, 11, 0.1);
    color: var(--warning, #f59e0b);
}

.badge-development {
    background: rgba(107, 114, 128, 0.1);
    color: var(--text-secondary);
}"""

        return btn_styles + card_styles + badge_styles

    def _generate_section_styles(self) -> str:
        """Generate styles for specific sections"""
        return """/* Section-Specific Styles */

/* Header and Navigation */
.header {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid var(--border, #e5e7eb);
    position: sticky;
    top: 0;
    z-index: 100;
}

.nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-md) var(--spacing-lg);
}

.nav-brand h1 {
    font-size: var(--font-size-xl);
    font-weight: 700;
    color: var(--primary-color);
    margin: 0;
}

.nav-links {
    display: flex;
    gap: var(--spacing-xl);
}

.nav-links a {
    color: var(--text-secondary);
    font-weight: 500;
    transition: color 0.2s ease;
}

.nav-links a:hover {
    color: var(--primary-color);
}

/* Hero Section */
.hero-section {
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
    color: white;
    text-align: center;
    padding: var(--spacing-4xl) 0;
}

.hero-title {
    font-size: var(--font-size-5xl);
    font-weight: 800;
    margin-bottom: var(--spacing-md);
}

.hero-tagline {
    font-size: var(--font-size-xl);
    margin-bottom: var(--spacing-lg);
    opacity: 0.9;
}

.hero-description {
    font-size: var(--font-size-lg);
    margin-bottom: var(--spacing-2xl);
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
    opacity: 0.8;
}

.features-preview {
    display: flex;
    justify-content: center;
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-2xl);
    flex-wrap: wrap;
}

.feature-badge {
    background: rgba(255, 255, 255, 0.2);
    padding: var(--spacing-xs) var(--spacing-md);
    border-radius: var(--radius-xl);
    font-size: var(--font-size-sm);
    font-weight: 500;
}

.hero-actions {
    display: flex;
    justify-content: center;
    gap: var(--spacing-lg);
}

/* Revolution Section */
.revolution-section {
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    padding: var(--spacing-4xl) 0;
}

.revolution-title {
    font-size: var(--font-size-4xl);
    font-weight: 800;
    text-align: center;
    margin-bottom: var(--spacing-sm);
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.revolution-subtitle {
    font-size: var(--font-size-xl);
    text-align: center;
    color: var(--text-secondary);
    margin-bottom: var(--spacing-3xl);
}

.problem-statement {
    max-width: 800px;
    margin: 0 auto var(--spacing-3xl);
    font-size: var(--font-size-lg);
    text-align: center;
    color: var(--text-primary);
}

.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: var(--spacing-lg);
    margin-bottom: var(--spacing-3xl);
}

.metric-card {
    background: white;
    padding: var(--spacing-xl);
    border-radius: var(--radius-lg);
    text-align: center;
    box-shadow: var(--shadow);
}

.metric-name {
    font-size: var(--font-size-sm);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-secondary);
    margin-bottom: var(--spacing-sm);
}

.metric-comparison {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-xs);
}

.old-value {
    font-size: var(--font-size-lg);
    color: var(--text-secondary);
    text-decoration: line-through;
}

.new-value {
    font-size: var(--font-size-2xl);
    font-weight: 700;
    color: var(--primary-color);
}

.arrow {
    color: var(--primary-color);
    font-size: var(--font-size-xl);
}

.metric-unit {
    font-size: var(--font-size-sm);
    color: var(--text-secondary);
    margin-bottom: var(--spacing-xs);
}

.metric-multiplier {
    font-weight: 600;
    color: var(--success, #10b981);
}

/* Agent Showcase */
.agents-section {
    padding: var(--spacing-4xl) 0;
}

.agent-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: var(--spacing-lg);
    margin-bottom: var(--spacing-3xl);
}

.agent-card {
    background: white;
    padding: var(--spacing-xl);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow);
    border: 1px solid var(--border, #e5e7eb);
    transition: all 0.3s ease;
}

.agent-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-lg);
}

.agent-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: var(--spacing-md);
}

.agent-name {
    font-size: var(--font-size-lg);
    font-weight: 600;
    color: var(--text-primary);
}

.agent-description {
    color: var(--text-secondary);
    margin-bottom: var(--spacing-md);
    line-height: 1.6;
}

.agent-capabilities {
    list-style: none;
    padding: 0;
}

.agent-capabilities li {
    padding: var(--spacing-xs) 0;
    color: var(--text-secondary);
    font-size: var(--font-size-sm);
}

.agent-capabilities li:before {
    content: "✓";
    color: var(--success, #10b981);
    font-weight: bold;
    margin-right: var(--spacing-xs);
}

/* Rich Agent Card Styles */
.rich-agent-card {
    margin-bottom: var(--spacing-xl);
    padding: var(--spacing-2xl);
}

.rich-agent-card .agent-name {
    font-size: var(--font-size-xl);
    font-weight: 600;
    color: var(--text-primary);
}

.rich-agent-card .agent-category {
    background: var(--primary-color);
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: var(--radius-xl);
    font-size: var(--font-size-sm);
    font-weight: 500;
}

.agent-body {
    margin-top: var(--spacing-lg);
}

.agent-features,
.agent-use-cases,
.agent-example {
    margin-top: var(--spacing-lg);
}

.agent-features h4,
.agent-use-cases h4,
.agent-example h4 {
    font-size: var(--font-size-lg);
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: var(--spacing-sm);
}

.agent-features ul,
.agent-use-cases ul {
    list-style: none;
    padding-left: 0;
}

.agent-features li,
.agent-use-cases li {
    padding: var(--spacing-xs) 0;
    color: var(--text-secondary);
    position: relative;
    padding-left: 1.5rem;
}

.agent-features li:before,
.agent-use-cases li:before {
    content: "•";
    color: var(--primary-color);
    position: absolute;
    left: 0;
    font-weight: bold;
}

.example-command {
    background: #1e1e1e;
    color: #d4d4d4;
    padding: var(--spacing-md);
    border-radius: var(--radius);
    margin-bottom: var(--spacing-sm);
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 0.9rem;
}

.example-command pre {
    margin: 0;
    padding: 0;
    background: none;
    border: none;
    color: #d4d4d4;
}

.example-output {
    color: var(--success, #10b981);
    font-weight: 500;
    font-style: italic;
}

.advanced-section {
    margin-top: var(--spacing-lg);
    border-top: 1px solid var(--border, #e5e7eb);
    padding-top: var(--spacing-lg);
}

.advanced-section summary {
    cursor: pointer;
    color: var(--primary-color);
    font-size: 0.95rem;
    margin-bottom: var(--spacing-md);
    font-weight: 500;
}

.advanced-section summary:hover {
    color: var(--secondary-color);
}

.examples-container {
    margin-top: var(--spacing-md);
}

.example-card {
    background: var(--surface, #f8fafc);
    padding: var(--spacing-lg);
    border-radius: var(--radius);
    margin-bottom: var(--spacing-md);
    border: 1px solid var(--border, #e5e7eb);
}

.example-card h5 {
    color: var(--text-primary);
    margin-bottom: var(--spacing-sm);
    font-size: var(--font-size-base);
    font-weight: 600;
}

.example-card p {
    color: var(--text-secondary);
    margin: 0;
    font-size: var(--font-size-sm);
}

.example-card code {
    background: var(--text-primary);
    color: white;
    padding: 0.125rem 0.25rem;
    border-radius: 0.125rem;
    font-size: 0.85em;
}

/* Progressive Setup */
.setup-section {
    background: var(--surface, #f8fafc);
    padding: var(--spacing-4xl) 0;
}

.setup-tiers {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: var(--spacing-xl);
}

.tier-card {
    background: white;
    padding: var(--spacing-2xl);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow);
    border: 1px solid var(--border, #e5e7eb);
    text-align: center;
    transition: all 0.3s ease;
}

.tier-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-lg);
}

.tier-header {
    margin-bottom: var(--spacing-lg);
}

.tier-name {
    font-size: var(--font-size-xl);
    font-weight: 700;
    margin-bottom: var(--spacing-xs);
}

.tier-duration {
    background: var(--primary-color);
    color: white;
    padding: var(--spacing-xs) var(--spacing-md);
    border-radius: var(--radius-xl);
    font-size: var(--font-size-sm);
    font-weight: 600;
}

.tier-focus {
    font-weight: 600;
    margin-bottom: var(--spacing-lg);
}

.tier-steps {
    text-align: left;
    margin-bottom: var(--spacing-lg);
}

.tier-demo {
    background: var(--surface, #f8fafc);
    padding: var(--spacing-md);
    border-radius: var(--radius);
    margin-bottom: var(--spacing-lg);
    text-align: left;
}

.tier-demo code {
    background: var(--text-primary);
    color: white;
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--radius-sm);
}

/* Tab System */
.category-tabs {
    display: flex;
    justify-content: center;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-xl);
    flex-wrap: wrap;
}

.tab-btn {
    padding: var(--spacing-md) var(--spacing-lg);
    background: transparent;
    border: 2px solid var(--border, #e5e7eb);
    border-radius: var(--radius);
    cursor: pointer;
    transition: all 0.2s ease;
}

.tab-btn.active,
.tab-btn:hover {
    background: var(--primary-color);
    color: white;
    border-color: var(--primary-color);
}

.tab-content {
    display: none;
}

.tab-content.active {
    display: block;
}"""

    def _generate_responsive_styles(self) -> str:
        """Generate responsive breakpoint styles"""
        mobile_bp = self.responsive.get("breakpoints", {}).get("mobile", "768px")
        tablet_bp = self.responsive.get("breakpoints", {}).get("tablet", "1024px")

        return f"""/* Responsive Styles */

@media (max-width: {mobile_bp}) {{
    .container {{
        padding: 0 var(--spacing-md);
    }}

    .section {{
        padding: var(--spacing-2xl) 0;
    }}

    .hero-title {{
        font-size: var(--font-size-3xl);
    }}

    .hero-actions {{
        flex-direction: column;
        align-items: center;
    }}

    .grid-2,
    .grid-3,
    .grid-4 {{
        grid-template-columns: 1fr;
    }}

    .metrics-grid {{
        grid-template-columns: 1fr;
    }}

    .agent-grid {{
        grid-template-columns: 1fr;
    }}

    .setup-tiers {{
        grid-template-columns: 1fr;
    }}

    .category-tabs {{
        flex-direction: column;
        align-items: center;
    }}

    .nav-links {{
        display: none;
    }}
}}

@media (max-width: {tablet_bp}) and (min-width: {mobile_bp}) {{
    .grid-3,
    .grid-4 {{
        grid-template-columns: repeat(2, 1fr);
    }}

    .metrics-grid {{
        grid-template-columns: repeat(2, 1fr);
    }}

    .agent-grid {{
        grid-template-columns: repeat(2, 1fr);
    }}
}}"""

    def _generate_animation_styles(self) -> str:
        """Generate animation styles based on animation level"""
        animation_level = self.design_system.get("animation_level", "engaging")

        if animation_level == "minimal":
            return """/* Minimal Animations */
.btn, .card, .agent-card, .tier-card {
    transition: opacity 0.2s ease;
}"""

        if animation_level == "subtle":
            return """/* Subtle Animations */
.btn, .card, .agent-card, .tier-card {
    transition: all 0.2s ease;
}

.card:hover, .agent-card:hover, .tier-card:hover {
    transform: translateY(-2px);
}"""

        if animation_level == "engaging":
            return """/* Engaging Animations */
.btn, .card, .agent-card, .tier-card {
    transition: all 0.3s ease;
}

.card:hover, .agent-card:hover, .tier-card:hover {
    transform: translateY(-4px);
}

/* Counter Animation */
@keyframes counter-up {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.metric-card .new-value {
    animation: counter-up 0.6s ease-out;
}

/* Fade In Animation */
@keyframes fade-in {
    from { opacity: 0; transform: translateY(30px); }
    to { opacity: 1; transform: translateY(0); }
}

.card, .agent-card, .tier-card {
    animation: fade-in 0.6s ease-out;
}

/* Hover Effects */
.btn:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
}

.agent-card:hover .agent-name {
    color: var(--primary-color);
}"""

        # bold
        return """/* Bold Animations */
.btn, .card, .agent-card, .tier-card {
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.card:hover, .agent-card:hover, .tier-card:hover {
    transform: translateY(-8px) scale(1.02);
}

.btn:hover {
    transform: translateY(-3px) scale(1.05);
}

/* More dramatic animations */
@keyframes bounce-in {
    0% { opacity: 0; transform: scale(0.3); }
    50% { opacity: 1; transform: scale(1.05); }
    70% { transform: scale(0.9); }
    100% { opacity: 1; transform: scale(1); }
}

.metric-card {
    animation: bounce-in 0.6s ease-out;
}"""

    def save_css(self, output_path: str) -> None:
        """Save generated CSS to file"""
        css_content = self.generate_full_css()

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(css_content)

        print(f"✓ CSS saved to: {output_file} ({len(css_content):,} characters)")


def test_css_generator():
    """Test CSS generation"""
    print("🎨 Testing CSS Generator")
    print("=" * 25)

    # Load configuration
    from config_loader import ConfigLoader

    loader = ConfigLoader()
    amplifier_config_path = Path(__file__).parent.parent.parent / "examples" / "amplifier_config.yaml"
    config = loader.load_full_config(str(amplifier_config_path))

    # Generate CSS
    generator = CSSGenerator(config)

    # Test individual components
    print("Generating CSS components...")
    reset_css = generator._generate_css_reset()
    print(f"✓ CSS Reset: {len(reset_css)} characters")

    variables_css = generator._generate_css_variables()
    print(f"✓ CSS Variables: {len(variables_css)} characters")

    components_css = generator._generate_component_styles()
    print(f"✓ Component Styles: {len(components_css)} characters")

    sections_css = generator._generate_section_styles()
    print(f"✓ Section Styles: {len(sections_css)} characters")

    responsive_css = generator._generate_responsive_styles()
    print(f"✓ Responsive Styles: {len(responsive_css)} characters")

    animations_css = generator._generate_animation_styles()
    print(f"✓ Animation Styles: {len(animations_css)} characters")

    # Generate full CSS
    print("\nGenerating complete stylesheet...")
    full_css = generator.generate_full_css()
    print(f"✓ Complete CSS: {len(full_css):,} characters")

    # Save CSS
    output_dir = Path(__file__).parent.parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    generator.save_css(str(output_dir / "amplifier-styles.css"))

    print("\n📊 CSS Generation Summary:")
    print(f"  Theme: {config.design_system['color_palette']}")
    print(f"  Animation Level: {config.design_system['animation_level']}")
    print(f"  Responsive Breakpoints: {len(config.responsive.get('breakpoints', {}))}")
    print(f"  Color Variables: {len(config.design_system.get('colors', {}))}")

    print("\n✅ CSS generation test completed successfully!")
    return True


if __name__ == "__main__":
    test_css_generator()
