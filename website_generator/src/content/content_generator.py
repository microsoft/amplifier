"""
Content generator for website creation.
Generates content based on repository analysis and configuration.
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

# Import our components
import sys
sys.path.append(str(Path(__file__).parent.parent))
from analyzer.repo_analyzer import RepoAnalysis, ParadigmType, AgentInfo, CommandInfo
from config_loader import SiteConfig


@dataclass
class RevolutionContent:
    """Content for revolutionary paradigm section"""
    title: str
    subtitle: str
    problem_statement: str
    paradigm_comparison: Dict[str, Any]
    multiplier_effect: Dict[str, Any]
    role_transformation: Dict[str, Any]


@dataclass
class ProgressiveSetup:
    """Progressive setup tier content"""
    tiers: List[Dict[str, Any]]


@dataclass
class AgentShowcase:
    """Agent showcase content"""
    featured_agents: List[Dict[str, Any]]
    agent_categories: Dict[str, List[Dict[str, Any]]]
    total_count: int


@dataclass
class GeneratedContent:
    """Complete generated content for a website"""
    revolution_section: Optional[RevolutionContent]
    progressive_setup: ProgressiveSetup
    agent_showcase: AgentShowcase
    hero_section: Dict[str, Any]
    overview_section: Dict[str, Any]
    examples_section: Dict[str, Any]


class ContentGenerator:
    """Generates website content based on repository analysis"""

    def __init__(self, config: SiteConfig):
        self.config = config

    def generate_content(self, analysis: RepoAnalysis) -> GeneratedContent:
        """Generate complete website content"""
        print(f"Generating content for {analysis.paradigm_type.value} paradigm...")

        # Generate revolution section (only for revolutionary paradigm)
        revolution_section = None
        if analysis.paradigm_type == ParadigmType.REVOLUTIONARY:
            revolution_section = self._generate_revolution_section(analysis)

        # Generate other sections
        progressive_setup = self._generate_progressive_setup(analysis)
        agent_showcase = self._generate_agent_showcase(analysis)
        hero_section = self._generate_hero_section(analysis)
        overview_section = self._generate_overview_section(analysis)
        examples_section = self._generate_examples_section(analysis)

        return GeneratedContent(
            revolution_section=revolution_section,
            progressive_setup=progressive_setup,
            agent_showcase=agent_showcase,
            hero_section=hero_section,
            overview_section=overview_section,
            examples_section=examples_section
        )

    def _generate_revolution_section(self, analysis: RepoAnalysis) -> RevolutionContent:
        """Generate revolutionary paradigm content"""
        project_name = analysis.project_info.name.title()

        # Generate problem statement
        problem_statement = self._generate_problem_statement(analysis)

        # Generate paradigm comparison
        paradigm_comparison = self._generate_paradigm_comparison(analysis)

        # Generate multiplier effect
        multiplier_effect = self._generate_multiplier_effect(analysis)

        # Generate role transformation
        role_transformation = self._generate_role_transformation(analysis)

        return RevolutionContent(
            title="The Development Revolution",
            subtitle=f"Why {project_name} Changes Everything",
            problem_statement=problem_statement,
            paradigm_comparison=paradigm_comparison,
            multiplier_effect=multiplier_effect,
            role_transformation=role_transformation
        )

    def _generate_problem_statement(self, analysis: RepoAnalysis) -> str:
        """Generate problem statement for revolutionary tools"""
        agent_count = len(analysis.agents)

        if agent_count >= 20:
            scale_desc = "massive complexity"
            solution_desc = "specialized AI agents"
        elif agent_count >= 10:
            scale_desc = "growing complexity"
            solution_desc = "intelligent automation"
        else:
            scale_desc = "increasing demands"
            solution_desc = "AI-powered assistance"

        return f"""Traditional development approaches struggle with {scale_desc} of modern software projects.
        Developers spend countless hours on repetitive tasks, debugging obscure issues, and managing intricate architectures.
        {analysis.project_info.name.title()} revolutionizes this process through {solution_desc}, transforming
        how we approach software development entirely."""

    def _generate_paradigm_comparison(self, analysis: RepoAnalysis) -> Dict[str, Any]:
        """Generate before/after paradigm comparison"""
        agent_count = len(analysis.agents)

        comparison = {
            "categories": [
                {
                    "name": "Development Speed",
                    "before": "Hours per feature",
                    "after": "Minutes per feature",
                    "improvement": "10-50x faster"
                },
                {
                    "name": "Code Quality",
                    "before": "Manual reviews",
                    "after": "AI-powered analysis",
                    "improvement": "Consistent excellence"
                },
                {
                    "name": "Architecture",
                    "before": "Ad-hoc decisions",
                    "after": "Specialized expertise",
                    "improvement": "Professional patterns"
                },
                {
                    "name": "Debugging",
                    "before": "Manual investigation",
                    "after": "Systematic analysis",
                    "improvement": "Root cause focus"
                }
            ]
        }

        if agent_count >= 20:
            comparison["categories"].append({
                "name": "Specialization",
                "before": "Generalist approach",
                "after": f"{agent_count}+ expert agents",
                "improvement": "Domain expertise"
            })

        return comparison

    def _generate_multiplier_effect(self, analysis: RepoAnalysis) -> Dict[str, Any]:
        """Generate capability multiplication metrics"""
        agent_count = len(analysis.agents)
        complexity = analysis.complexity_score

        # Calculate multipliers based on project characteristics
        if agent_count >= 20 and complexity >= 80:
            # High complexity, many agents (like Amplifier)
            ideas_multiplier = 25  # 50 → 1250
            time_reduction = 12    # 12 hours → 1 hour
        elif agent_count >= 10:
            ideas_multiplier = 10  # 50 → 500
            time_reduction = 6     # 6 hours → 1 hour
        else:
            ideas_multiplier = 5   # 50 → 250
            time_reduction = 3     # 3 hours → 1 hour

        return {
            "metrics": [
                {
                    "name": "Ideas Generated",
                    "old_value": 50,
                    "new_value": 50 * ideas_multiplier,
                    "unit": "per month",
                    "multiplier": ideas_multiplier
                },
                {
                    "name": "Implementation Time",
                    "old_value": time_reduction,
                    "new_value": 1,
                    "unit": "hours",
                    "multiplier": time_reduction,
                    "inverse": True
                },
                {
                    "name": "Code Quality",
                    "old_value": 70,
                    "new_value": 95,
                    "unit": "% excellent",
                    "multiplier": 1.36
                }
            ]
        }

    def _generate_role_transformation(self, analysis: RepoAnalysis) -> Dict[str, Any]:
        """Generate role transformation narrative"""
        agent_count = len(analysis.agents)

        if agent_count >= 20:
            # High-agent environments like Amplifier
            return {
                "transformation_type": "elevation",
                "old_role": {
                    "title": "Traditional Developer",
                    "characteristics": [
                        "Code line by line manually",
                        "Debug through trial and error",
                        "Work on single tasks sequentially",
                        "Rely on personal knowledge only",
                        "Spend hours on repetitive work"
                    ]
                },
                "new_role": {
                    "title": "AI-Amplified Architect",
                    "characteristics": [
                        "Design and orchestrate systems",
                        "Deploy specialized expert agents",
                        "Coordinate parallel development streams",
                        "Access distributed expertise instantly",
                        "Focus on creative problem-solving"
                    ]
                },
                "transformation_message": "You don't become obsolete—you become orchestrator of an expert team."
            }
        elif agent_count >= 5:
            return {
                "transformation_type": "enhancement",
                "old_role": {
                    "title": "Solo Developer",
                    "characteristics": [
                        "Handle all aspects personally",
                        "Limited by individual expertise",
                        "Sequential task completion"
                    ]
                },
                "new_role": {
                    "title": "Augmented Developer",
                    "characteristics": [
                        "Leverage AI specialists for complex tasks",
                        "Access expert knowledge on demand",
                        "Parallel task execution"
                    ]
                }
            }
        else:
            return {
                "transformation_type": "assistance",
                "old_role": {
                    "title": "Manual Developer",
                    "characteristics": [
                        "All work done manually",
                        "Time-consuming processes"
                    ]
                },
                "new_role": {
                    "title": "AI-Assisted Developer",
                    "characteristics": [
                        "AI handles routine tasks",
                        "Accelerated development cycle"
                    ]
                }
            }

    def _generate_progressive_setup(self, analysis: RepoAnalysis) -> ProgressiveSetup:
        """Generate progressive setup tiers"""
        project_name = analysis.project_info.name
        agent_count = len(analysis.agents)

        tiers = []

        # Quick Taste (1 minute)
        quick_taste = {
            "name": "Quick Taste",
            "duration": "1 minute",
            "description": "Experience the power immediately",
            "focus": f"Your first {project_name} agent",
            "steps": [
                f"Install {project_name}",
                "Run your first agent command",
                "See immediate results"
            ]
        }

        if agent_count >= 5:
            quick_taste["demo_command"] = f"Use zen-architect to design my authentication system"
            quick_taste["expected_result"] = "Complete system architecture generated in seconds"
        else:
            quick_taste["demo_command"] = f"Run {project_name} --help"
            quick_taste["expected_result"] = "See available capabilities"

        tiers.append(quick_taste)

        # Essential Setup (5 minutes)
        essential = {
            "name": "Essential Setup",
            "duration": "5 minutes",
            "description": "Core features and workflows",
            "focus": f"Essential {project_name} workflow",
            "steps": [
                "Configure core settings",
                "Learn key commands",
                "Complete first real task"
            ]
        }

        if agent_count >= 10:
            essential["workflow"] = "Multi-agent workflow with 3-5 essential agents"
        else:
            essential["workflow"] = "Core feature demonstration"

        tiers.append(essential)

        # Power User (15+ minutes) - only for complex systems
        if analysis.complexity_score >= 50 or agent_count >= 5:
            power_user = {
                "name": "Power User",
                "duration": "15+ minutes",
                "description": "Full ecosystem mastery",
                "focus": f"Complete {project_name} mastery",
                "steps": [
                    "Advanced configuration",
                    "Custom integrations",
                    "Expert workflows"
                ]
            }

            if agent_count >= 20:
                power_user["mastery_features"] = [
                    f"All {agent_count}+ specialized agents",
                    "Parallel workflow orchestration",
                    "Custom agent creation",
                    "Advanced automation patterns"
                ]
            elif agent_count >= 10:
                power_user["mastery_features"] = [
                    "Advanced agent combinations",
                    "Complex workflow patterns",
                    "Integration customization"
                ]
            else:
                power_user["mastery_features"] = [
                    "Advanced features",
                    "Customization options",
                    "Expert patterns"
                ]

            tiers.append(power_user)

        return ProgressiveSetup(tiers=tiers)

    def _generate_agent_showcase(self, analysis: RepoAnalysis) -> AgentShowcase:
        """Generate agent showcase content"""
        agents = analysis.agents
        total_count = len(agents)

        # Select featured agents (first 6 or most important)
        featured_agents = []
        for i, agent in enumerate(agents[:6]):
            featured_agents.append(self._create_rich_agent_content(agent))

        # Categorize all agents with rich content
        categories = {
            "Architecture": [],
            "Development": [],
            "Quality": [],
            "Analysis": [],
            "Automation": [],
            "Other": []
        }

        for agent in agents:
            category = self._categorize_agent(agent.name)
            rich_agent = self._create_rich_agent_content(agent)
            categories[category].append(rich_agent)

        # Remove empty categories
        categories = {k: v for k, v in categories.items() if v}

        return AgentShowcase(
            featured_agents=featured_agents,
            agent_categories=categories,
            total_count=total_count
        )

    def _create_rich_agent_content(self, agent: AgentInfo) -> Dict[str, Any]:
        """Create rich, detailed content for an agent like the instructor site"""
        agent_name = agent.name
        category = self._categorize_agent(agent_name)

        # Generate detailed description based on agent name and existing description
        detailed_description = self._generate_detailed_agent_description(agent)

        # Generate example usage and output
        example_usage = self._generate_agent_usage_example(agent)
        example_output = self._generate_agent_output_example(agent)

        # Generate key capabilities
        key_capabilities = self._generate_agent_key_capabilities(agent)

        # Generate use cases
        use_cases = self._generate_agent_use_cases(agent)

        return {
            "name": agent_name,
            "category": category,
            "description": detailed_description,
            "capabilities": key_capabilities,
            "capabilities_count": len(agent.capabilities),
            "example_usage": example_usage,
            "example_output": example_output,
            "use_cases": use_cases,
            "file_path": agent.file_path
        }

    def _generate_detailed_agent_description(self, agent: AgentInfo) -> str:
        """Generate detailed agent description based on name and role"""
        name = agent.name
        existing_desc = agent.description

        # Agent-specific detailed descriptions
        if name == "zen-architect":
            return """The master architect who embodies ruthless simplicity and Wabi-sabi philosophy. Operates in three powerful modes:
            ANALYZE for problem decomposition, ARCHITECT for system design, and REVIEW for code quality assessment.
            Creates clear specifications that guide implementation, focusing on essential patterns over unnecessary abstractions."""

        elif name == "bug-hunter":
            return """Specialized debugging expert focused on systematically finding and fixing bugs. Uses hypothesis-driven debugging
            to efficiently locate root causes and implement minimal fixes. Follows a methodical approach that prevents future issues
            while maintaining code simplicity and reliability."""

        elif name == "security-guardian":
            return """Comprehensive security analysis expert that performs vulnerability assessments and security audits.
            Checks for common vulnerabilities (OWASP Top 10), detects hardcoded secrets, validates input/output security,
            and ensures data protection measures are in place before production deployments."""

        elif name == "test-coverage":
            return """Expert at analyzing test coverage and identifying gaps to suggest comprehensive test cases.
            Ensures thorough testing without over-testing, following the testing pyramid principle.
            Identifies edge cases and creates strategic test suites that maximize quality assurance."""

        elif name == "performance-optimizer":
            return """Analyzes and improves code and system performance through data-driven optimization.
            Profiles applications to identify bottlenecks, optimizes algorithms, improves database queries,
            and addresses performance concerns with a measure-first approach."""

        elif name == "modular-builder":
            return """Primary implementation agent that builds code from zen-architect specifications.
            Creates self-contained, regeneratable modules following the 'bricks and studs' philosophy.
            Transforms architectural designs into working code with proper separation of concerns."""

        elif "analysis" in name or "synthesis" in name:
            return f"""Advanced analysis agent specialized in {name.replace('-', ' ').replace('_', ' ')}.
            Processes complex information to extract insights and patterns. Uses multi-mode analysis
            to provide deep understanding and actionable recommendations for development decisions."""

        else:
            # Fallback to enhanced version of existing description
            if existing_desc and len(existing_desc) > 50:
                return existing_desc
            else:
                return f"""Specialized agent focused on {name.replace('-', ' ').replace('_', ' ')} tasks.
                Provides expert-level capabilities and follows best practices to ensure high-quality outcomes.
                Integrates seamlessly with other agents in the development ecosystem."""

    def _generate_agent_usage_example(self, agent: AgentInfo) -> str:
        """Generate usage example for an agent"""
        name = agent.name

        examples = {
            "zen-architect": "Use zen-architect to design a user notification system",
            "bug-hunter": "Use bug-hunter to investigate why the authentication system is throwing intermittent errors",
            "security-guardian": "Use security-guardian to review this API endpoint before production deployment",
            "test-coverage": "Use test-coverage to analyze gaps in our payment processing test suite",
            "performance-optimizer": "Use performance-optimizer to speed up our database queries in the user dashboard",
            "modular-builder": "Use modular-builder to implement the notification system from zen-architect's specification",
            "integration-specialist": "Use integration-specialist to connect our system with the new payment API",
            "content-researcher": "Use content-researcher to find relevant patterns for implementing OAuth authentication"
        }

        return examples.get(name, f"Use {name} to handle {name.replace('-', ' ')} tasks efficiently")

    def _generate_agent_output_example(self, agent: AgentInfo) -> str:
        """Generate example output for an agent"""
        name = agent.name

        outputs = {
            "zen-architect": "→ Returns: Problem analysis, 3 solution approaches with trade-offs, modular specification",
            "bug-hunter": "→ Returns: Root cause analysis, step-by-step debugging plan, fix implementation with tests",
            "security-guardian": "→ Returns: Security assessment report, vulnerability findings, remediation recommendations",
            "test-coverage": "→ Returns: Coverage analysis, identified gaps, comprehensive test case suggestions",
            "performance-optimizer": "→ Returns: Performance bottleneck analysis, optimization recommendations, implementation plan",
            "modular-builder": "→ Returns: Working implementation with tests, documentation, and integration instructions"
        }

        return outputs.get(name, f"→ Returns: Comprehensive {name.replace('-', ' ')} analysis and recommendations")

    def _generate_agent_key_capabilities(self, agent: AgentInfo) -> List[str]:
        """Generate key capabilities for an agent"""
        name = agent.name

        # Use existing capabilities if available and detailed
        if agent.capabilities and len(agent.capabilities) >= 3:
            return agent.capabilities[:6]  # Top 6 capabilities

        # Generate capabilities based on agent type
        capabilities_map = {
            "zen-architect": [
                "Analysis-first development approach",
                "Modular 'bricks & studs' architecture",
                "Clean contract specifications",
                "Complexity elimination strategies",
                "80/20 principle application",
                "Philosophy compliance review"
            ],
            "bug-hunter": [
                "Hypothesis-driven debugging methodology",
                "Root cause analysis techniques",
                "Systematic error reproduction",
                "Minimal fix implementation",
                "Prevention strategy development",
                "Code quality improvement"
            ],
            "security-guardian": [
                "OWASP Top 10 vulnerability scanning",
                "Hardcoded secrets detection",
                "Input/output validation checks",
                "Authentication system review",
                "Data protection compliance",
                "Production security audits"
            ],
            "test-coverage": [
                "Coverage gap identification",
                "Test strategy development",
                "Edge case discovery",
                "Testing pyramid optimization",
                "Quality assurance planning",
                "Test maintenance guidelines"
            ]
        }

        return capabilities_map.get(name, [
            f"Expert {name.replace('-', ' ')} analysis",
            "Best practice implementation",
            "Quality assurance focus",
            "Integration with development workflow",
            "Comprehensive documentation",
            "Scalable solution design"
        ])

    def _generate_agent_use_cases(self, agent: AgentInfo) -> List[str]:
        """Generate use cases for an agent"""
        name = agent.name

        use_cases_map = {
            "zen-architect": [
                "Designing new feature architectures",
                "Refactoring complex legacy systems",
                "Creating modular component specifications",
                "Establishing coding standards and patterns"
            ],
            "bug-hunter": [
                "Investigating production issues",
                "Debugging intermittent failures",
                "Analyzing test failures",
                "Resolving performance problems"
            ],
            "security-guardian": [
                "Pre-deployment security reviews",
                "API security assessments",
                "Authentication system audits",
                "Data privacy compliance checks"
            ]
        }

        return use_cases_map.get(name, [
            f"Complex {name.replace('-', ' ')} challenges",
            "Quality improvement initiatives",
            "Best practice implementation",
            "Team knowledge enhancement"
        ])

    def _categorize_agent(self, agent_name: str) -> str:
        """Categorize agent based on name patterns"""
        name_lower = agent_name.lower()

        if any(keyword in name_lower for keyword in ['architect', 'design', 'modular', 'builder']):
            return "Architecture"
        elif any(keyword in name_lower for keyword in ['bug', 'debug', 'test', 'security', 'performance']):
            return "Quality"
        elif any(keyword in name_lower for keyword in ['analysis', 'synthesis', 'extract', 'insight']):
            return "Analysis"
        elif any(keyword in name_lower for keyword in ['automation', 'cleanup', 'integration']):
            return "Automation"
        elif any(keyword in name_lower for keyword in ['contract', 'api', 'database']):
            return "Development"
        else:
            return "Other"

    def _generate_hero_section(self, analysis: RepoAnalysis) -> Dict[str, Any]:
        """Generate hero section content"""
        project_name = analysis.project_info.name.title()
        description = analysis.project_info.description or f"Supercharge your development with {project_name}"

        return {
            "title": project_name,
            "tagline": self.config.site.get('tagline', f"Next-Generation Development Tool"),
            "description": description,
            "cta_primary": "Get Started",
            "cta_secondary": "View Examples",
            "features_preview": [
                f"{len(analysis.agents)} Specialized Agents",
                f"Complexity Score: {analysis.complexity_score}",
                f"{analysis.paradigm_type.value.title()} Impact"
            ]
        }

    def _generate_overview_section(self, analysis: RepoAnalysis) -> Dict[str, Any]:
        """Generate overview section content"""
        return {
            "title": "Overview",
            "description": f"Understand how {analysis.project_info.name} transforms your development workflow",
            "key_points": [
                {
                    "title": "Specialized Agents",
                    "description": f"{len(analysis.agents)} expert agents handle different aspects of development",
                    "icon": "agents"
                },
                {
                    "title": "Parallel Processing",
                    "description": "Execute multiple development tasks simultaneously",
                    "icon": "parallel"
                },
                {
                    "title": "Quality Assurance",
                    "description": "Built-in quality checks and best practices enforcement",
                    "icon": "quality"
                }
            ]
        }

    def _generate_examples_section(self, analysis: RepoAnalysis) -> Dict[str, Any]:
        """Generate examples section content"""
        # Extract example commands from the analysis
        example_commands = []
        for cmd in analysis.commands[:5]:  # Top 5 commands
            if cmd.usage:
                example_commands.append({
                    "name": cmd.name,
                    "command": cmd.usage,
                    "description": cmd.description
                })

        return {
            "title": "Examples",
            "description": "Real workflows and commands you can use immediately",
            "examples": example_commands,
            "workflows": [
                {
                    "name": "Full Development Cycle",
                    "steps": [
                        "Design with zen-architect",
                        "Build with modular-builder",
                        "Test with test-coverage",
                        "Review with security-guardian"
                    ]
                }
            ]
        }


def test_content_generation():
    """Test content generation with Amplifier analysis"""
    # This would normally load from the actual analysis
    # For testing, we'll create a mock analysis
    from analyzer.repo_analyzer import ProjectInfo, RepoAnalysis, ParadigmType, AgentInfo

    # Mock analysis for testing
    project_info = ProjectInfo(
        name="amplifier",
        description="A complete development environment that supercharges AI coding assistants",
        language="Python"
    )

    mock_agents = [
        AgentInfo("zen-architect", "Designs systems with ruthless simplicity", ["architecture", "design"], ".claude/agents/zen-architect.md"),
        AgentInfo("bug-hunter", "Systematic debugging expert", ["debugging", "analysis"], ".claude/agents/bug-hunter.md"),
        AgentInfo("security-guardian", "Security analysis and best practices", ["security", "audit"], ".claude/agents/security-guardian.md"),
    ]

    mock_commands = [
        CommandInfo("zen-architect", "Design system architecture", "make design", ".claude/commands/design.md"),
        CommandInfo("test-suite", "Run comprehensive tests", "make test", "Makefile"),
    ]

    mock_analysis = RepoAnalysis(
        project_info=project_info,
        paradigm_type=ParadigmType.REVOLUTIONARY,
        agents=mock_agents,
        commands=mock_commands,
        workflows=[],
        complexity_score=100,
        paradigm_indicators={'ai_amplification': 3, 'specialized_agents': 3}
    )

    # Load config
    from config_loader import ConfigLoader
    loader = ConfigLoader()
    config = loader.load_full_config()

    # Generate content
    generator = ContentGenerator(config)
    content = generator.generate_content(mock_analysis)

    print("🎯 Content Generation Test Results:")
    print(f"Revolution Section: {content.revolution_section.title if content.revolution_section else 'None'}")
    print(f"Setup Tiers: {len(content.progressive_setup.tiers)}")
    print(f"Featured Agents: {len(content.agent_showcase.featured_agents)}")
    print(f"Agent Categories: {list(content.agent_showcase.agent_categories.keys())}")
    print(f"Hero Title: {content.hero_section['title']}")

    return True


if __name__ == "__main__":
    test_content_generation()