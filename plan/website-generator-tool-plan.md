# Automated Website Generator Tool Plan

## Analysis of Instructor Website Transformation Work

Based on the extensive instructor website transformation completed, I've identified the key patterns, components, and requirements for building an automated website generator tool.

## Core Transformation Patterns Identified

### 1. **Content Analysis & Gap Detection**
The transformation process involved:
- **Repository Analysis**: Deep examination of project structure, documentation, and capabilities
- **Gap Identification**: Mental model gaps, complexity gaps, trust gaps, workflow transformation gaps
- **Paradigm Mapping**: Understanding fundamental shifts the tool/framework represents

### 2. **Progressive Disclosure Architecture**
- **Tier-based Setup**: Quick Taste (1 min) → Essential (5 min) → Power User (15 min)
- **Capability Discovery**: Starter pack → Intermediate → Expert level features
- **Entry Path Customization**: Different paths for skeptical developers, early adopters, managers

### 3. **Content Generation Patterns**
- **Revolution Sections**: Problem statement → Paradigm comparison → Multiplier effects → Role transformation
- **Interactive Elements**: Animated counters, terminal demos, progressive reveals
- **Trust Building**: Safety demonstrations, gradual confidence building, failure recovery examples

### 4. **Consistent Design System**
- **CSS Variables**: Consistent color scheme, typography, spacing
- **Component Library**: Reusable cards, buttons, sections, animations
- **Responsive Design**: Mobile-first approach with progressive enhancement

## Automated Website Generator Tool Architecture

### Tool Structure: `website_generator/`

```
website_generator/
├── README.md
├── config/
│   ├── site_template.yaml          # Master template configuration
│   ├── content_patterns.yaml       # Content generation patterns
│   └── style_system.yaml          # Design system definitions
├── src/
│   ├── analyzer/
│   │   ├── repo_analyzer.py        # Repository structure analysis
│   │   ├── capability_extractor.py # Extract features, agents, commands
│   │   └── paradigm_detector.py    # Detect fundamental paradigm shifts
│   ├── content/
│   │   ├── content_generator.py    # Generate content sections
│   │   ├── template_engine.py      # Template processing system
│   │   └── interactive_builder.py  # Build interactive elements
│   ├── style/
│   │   ├── css_generator.py        # Generate CSS from design system
│   │   └── component_builder.py    # Build reusable components
│   ├── website/
│   │   ├── site_builder.py         # Orchestrate full site build
│   │   ├── page_generator.py       # Generate individual pages
│   │   └── asset_manager.py        # Handle CSS, JS, images
│   └── automation/
│       ├── change_detector.py      # Detect repo changes
│       ├── scheduler.py            # Nightly automation
│       └── consistency_validator.py # Ensure regeneration consistency
├── templates/
│   ├── base_template.html          # Base HTML structure
│   ├── sections/                   # Reusable section templates
│   │   ├── revolution.html
│   │   ├── progressive_setup.html
│   │   ├── capability_showcase.html
│   │   └── trust_building.html
│   └── pages/                      # Full page templates
├── assets/
│   ├── css/
│   │   ├── variables.css           # CSS custom properties
│   │   ├── components.css          # Reusable components
│   │   └── sections.css           # Section-specific styles
│   └── js/
│       ├── animations.js           # Counter animations, transitions
│       ├── progressive.js          # Progressive disclosure logic
│       └── interactions.js         # Interactive elements
└── examples/
    └── amplifier_config.yaml      # Example configuration for Amplifier
```

## Configuration System Design

### 1. **Master Site Template (`site_template.yaml`)**

```yaml
# Site Identity & Branding
site:
  name: "Amplifier"
  tagline: "Supercharged AI Development"
  description: "A complete development environment that supercharges AI coding assistants"
  theme: "revolution"  # revolution, professional, minimal, etc.

# Content Generation Strategy
content_strategy:
  paradigm_shift_detection: true
  progressive_disclosure: true
  trust_building_focus: true
  role_transformation_emphasis: true

# Design System
design_system:
  color_palette: "amplifier_blue_gradient"
  typography: "inter_modern"
  component_style: "card_based_progressive"
  animation_level: "engaging"  # minimal, subtle, engaging, bold

# Page Structure
pages:
  - name: "index"
    sections: ["revolution", "hero", "overview", "features", "quick_setup", "examples"]
  - name: "setup"
    sections: ["progressive_tiers", "detailed_instructions", "troubleshooting"]
  - name: "agents"
    sections: ["agent_showcase", "capability_matrix", "integration_patterns"]

# Interactive Elements
interactions:
  animated_counters: true
  progressive_setup_tiers: true
  terminal_demos: true
  copy_paste_commands: true
```

### 2. **Content Patterns (`content_patterns.yaml`)**

```yaml
# Repository Analysis Patterns
analysis_patterns:
  agent_detection:
    file_patterns: [".claude/agents/*.md", "agents/", "subagents/"]
    capability_extraction: "markdown_headers_and_descriptions"

  command_detection:
    file_patterns: [".claude/commands/*.md", "commands/", "scripts/"]
    usage_pattern_extraction: true

  paradigm_indicators:
    - "specialized_agents"
    - "modular_architecture"
    - "ai_code_generation"
    - "parallel_development"
    - "knowledge_synthesis"

# Content Generation Templates
content_templates:
  revolution_section:
    problem_statement: "constraint_based"  # Extract core limitation being solved
    paradigm_comparison: "before_after_table"
    multiplier_calculation: "capability_multiplication"
    role_transformation: "old_role_vs_new_role"

  progressive_setup:
    tier_structure:
      quick_taste: "1_minute_demo"
      essential: "5_minute_core_features"
      power_user: "15_minute_full_ecosystem"

  capability_showcase:
    organization: "beginner_intermediate_expert"
    presentation: "card_grid_with_examples"
    progressive_reveal: true

# Trust Building Patterns
trust_building:
  safety_demonstrations: true
  gradual_confidence_building: true
  human_role_elevation: true
  ai_quality_assurance_showcase: true
```

### 3. **Dynamic Content Generation Logic**

#### Repository Analyzer (`repo_analyzer.py`)

```python
class RepositoryAnalyzer:
    """Analyzes repository structure and capabilities"""

    def analyze_repository(self, repo_path: str) -> RepoAnalysis:
        analysis = RepoAnalysis()

        # Extract project metadata
        analysis.project_info = self._extract_project_info(repo_path)

        # Detect paradigm indicators
        analysis.paradigm_type = self._detect_paradigm_shift(repo_path)

        # Extract capabilities
        analysis.agents = self._extract_agents(repo_path)
        analysis.commands = self._extract_commands(repo_path)
        analysis.workflows = self._extract_workflows(repo_path)

        # Analyze complexity level
        analysis.complexity_score = self._calculate_complexity(repo_path)

        return analysis

    def _detect_paradigm_shift(self, repo_path: str) -> ParadigmType:
        """Detect if this represents a fundamental paradigm shift"""
        indicators = {
            'ai_amplification': self._check_ai_features(repo_path),
            'specialized_agents': self._count_agents(repo_path),
            'parallel_workflows': self._detect_parallel_patterns(repo_path),
            'knowledge_synthesis': self._check_knowledge_systems(repo_path)
        }

        # Score paradigm shift significance
        shift_score = sum(indicators.values())

        if shift_score >= 3:
            return ParadigmType.REVOLUTIONARY
        elif shift_score >= 2:
            return ParadigmType.EVOLUTIONARY
        else:
            return ParadigmType.INCREMENTAL
```

#### Content Generator (`content_generator.py`)

```python
class ContentGenerator:
    """Generates website content based on repository analysis"""

    def generate_revolution_section(self, analysis: RepoAnalysis) -> RevolutionContent:
        """Generate paradigm shift explanation content"""

        if analysis.paradigm_type == ParadigmType.REVOLUTIONARY:
            return self._generate_revolutionary_content(analysis)
        elif analysis.paradigm_type == ParadigmType.EVOLUTIONARY:
            return self._generate_evolutionary_content(analysis)
        else:
            return self._generate_incremental_content(analysis)

    def _generate_revolutionary_content(self, analysis: RepoAnalysis) -> RevolutionContent:
        """Generate content for paradigm-shifting tools like Amplifier"""

        # Extract core constraint being solved
        problem_statement = self._extract_core_problem(analysis)

        # Generate before/after comparison
        paradigm_comparison = self._generate_paradigm_comparison(analysis)

        # Calculate capability multiplication
        multiplier_effect = self._calculate_multiplier_effect(analysis)

        # Generate role transformation content
        role_transformation = self._generate_role_transformation(analysis)

        return RevolutionContent(
            problem_statement=problem_statement,
            paradigm_comparison=paradigm_comparison,
            multiplier_effect=multiplier_effect,
            role_transformation=role_transformation
        )

    def generate_progressive_setup(self, analysis: RepoAnalysis) -> ProgressiveSetup:
        """Generate tiered setup experience"""

        # Analyze complexity to determine tier structure
        complexity = analysis.complexity_score

        tiers = []

        # Quick Taste (1 minute)
        quick_taste = self._generate_quick_taste_tier(analysis)
        tiers.append(quick_taste)

        # Essential Setup (5 minutes)
        essential = self._generate_essential_tier(analysis)
        tiers.append(essential)

        # Power User (15+ minutes)
        if complexity >= 3:  # Only for complex systems
            power_user = self._generate_power_user_tier(analysis)
            tiers.append(power_user)

        return ProgressiveSetup(tiers=tiers)
```

## Automation & Consistency System

### 1. **Change Detection (`change_detector.py`)**

```python
class ChangeDetector:
    """Detects meaningful changes that should trigger regeneration"""

    def detect_changes(self, repo_path: str, last_build_hash: str) -> ChangeReport:
        current_hash = self._get_repo_hash(repo_path)

        if current_hash == last_build_hash:
            return ChangeReport(has_changes=False)

        # Analyze specific changes
        changes = self._analyze_git_diff(last_build_hash, current_hash)

        # Determine if changes warrant regeneration
        significant_changes = self._filter_significant_changes(changes)

        return ChangeReport(
            has_changes=len(significant_changes) > 0,
            changes=significant_changes,
            current_hash=current_hash
        )

    def _filter_significant_changes(self, changes: List[Change]) -> List[Change]:
        """Filter for changes that should trigger regeneration"""
        significant = []

        for change in changes:
            if any([
                change.affects_agents,
                change.affects_commands,
                change.affects_documentation,
                change.affects_core_features,
                change.is_major_version_bump
            ]):
                significant.append(change)

        return significant
```

### 2. **Consistency Validator (`consistency_validator.py`)**

```python
class ConsistencyValidator:
    """Ensures regenerated sites maintain visual and structural consistency"""

    def validate_consistency(self, old_site: SiteStructure, new_site: SiteStructure) -> ValidationReport:
        """Validate that regeneration preserves key consistency elements"""

        issues = []

        # Check CSS variable consistency
        css_issues = self._validate_css_consistency(old_site.css, new_site.css)
        issues.extend(css_issues)

        # Check component structure consistency
        component_issues = self._validate_component_consistency(old_site, new_site)
        issues.extend(component_issues)

        # Check navigation consistency
        nav_issues = self._validate_navigation_consistency(old_site.nav, new_site.nav)
        issues.extend(nav_issues)

        # Check responsive design consistency
        responsive_issues = self._validate_responsive_consistency(old_site, new_site)
        issues.extend(responsive_issues)

        return ValidationReport(
            is_consistent=len(issues) == 0,
            issues=issues
        )
```

## Implementation Strategy

### Phase 1: Core Infrastructure (Week 1-2)
1. **Repository Analysis System**
   - Build repo analyzer to extract agents, commands, workflows
   - Implement paradigm shift detection algorithm
   - Create capability complexity scoring system

2. **Configuration System**
   - Design YAML-based configuration schema
   - Implement template loading and validation
   - Create design system configuration management

### Phase 2: Content Generation (Week 3-4)
1. **Template Engine**
   - Build Jinja2-based template processing
   - Implement dynamic content generation logic
   - Create component and section builders

2. **Interactive Element Builder**
   - Generate JavaScript for animations and interactions
   - Build progressive disclosure logic
   - Create terminal demo simulations

### Phase 3: Automation & Consistency (Week 5-6)
1. **Change Detection System**
   - Implement git-based change monitoring
   - Create significance filtering algorithms
   - Build automated triggering system

2. **Consistency Validation**
   - Create CSS and component consistency checkers
   - Implement visual regression detection
   - Build regeneration validation pipeline

### Phase 4: Testing & Polish (Week 7-8)
1. **Tool Testing**
   - Test with Amplifier repository as primary use case
   - Validate consistent regeneration across multiple runs
   - Performance optimization for nightly automation

2. **Documentation & Examples**
   - Complete tool documentation
   - Create configuration examples for different project types
   - Build troubleshooting and customization guides

## Usage Pattern

```bash
# Initial generation
website_generator generate --repo /path/to/amplifier --config amplifier_config.yaml --output ./website

# Nightly automation
website_generator watch --repo /path/to/amplifier --config amplifier_config.yaml --output ./website --schedule nightly

# Manual regeneration with change detection
website_generator regenerate --repo /path/to/amplifier --config amplifier_config.yaml --output ./website --validate-consistency
```

## Expected Benefits

1. **Consistency**: Same visual design and structure across regenerations
2. **Freshness**: Automatically incorporates new features, agents, and documentation
3. **Scalability**: Can be applied to other repositories with similar patterns
4. **Maintainability**: Centralized design system and content patterns
5. **Quality**: Built-in validation ensures regenerated sites meet standards

This tool will automate the intensive manual work of transforming technical repositories into engaging, educational websites that help users understand and adopt paradigm-shifting development tools.