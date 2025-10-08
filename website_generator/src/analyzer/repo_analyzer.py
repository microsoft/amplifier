"""
Repository analyzer for extracting project structure, capabilities, and paradigm indicators.
"""

import json
from dataclasses import asdict
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ParadigmType(Enum):
    """Classification of paradigm shift significance"""

    REVOLUTIONARY = "revolutionary"  # Fundamental paradigm shift (3+ indicators)
    EVOLUTIONARY = "evolutionary"  # Significant improvements (2 indicators)
    INCREMENTAL = "incremental"  # Standard feature additions (0-1 indicators)


@dataclass
class ProjectInfo:
    """Basic project metadata"""

    name: str
    description: str = ""
    version: str = ""
    language: str = ""
    framework: str = ""


@dataclass
class AgentInfo:
    """Information about a specialized agent"""

    name: str
    description: str
    capabilities: list[str]
    file_path: str


@dataclass
class CommandInfo:
    """Information about a command or workflow"""

    name: str
    description: str
    usage: str
    file_path: str


@dataclass
class RepoAnalysis:
    """Complete repository analysis results"""

    project_info: ProjectInfo
    paradigm_type: ParadigmType
    agents: list[AgentInfo]
    commands: list[CommandInfo]
    workflows: list[str]
    complexity_score: int
    paradigm_indicators: dict[str, int]


class RepositoryAnalyzer:
    """Analyzes repository structure and capabilities"""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")

    def analyze_repository(self) -> RepoAnalysis:
        """Perform complete repository analysis"""
        print(f"Analyzing repository: {self.repo_path}")

        # Extract project metadata
        print("Extracting project info...")
        project_info = self._extract_project_info()
        print(f"Project: {project_info.name} ({project_info.language})")

        # Extract capabilities
        print("Extracting agents...")
        agents = self._extract_agents()
        print(f"Found {len(agents)} agents")

        print("Extracting commands...")
        commands = self._extract_commands()
        print(f"Found {len(commands)} commands")

        print("Extracting workflows...")
        workflows = self._extract_workflows()
        print(f"Found workflows: {workflows}")

        # Analyze complexity
        print("Calculating complexity...")
        complexity_score = self._calculate_complexity(agents, commands, workflows)
        print(f"Complexity score: {complexity_score}")

        # Detect paradigm indicators
        print("Detecting paradigm indicators...")
        paradigm_indicators = self._detect_paradigm_indicators(agents, commands, workflows)
        print(f"Paradigm indicators: {paradigm_indicators}")

        # Determine paradigm type
        paradigm_type = self._classify_paradigm_shift(paradigm_indicators)
        print(f"Paradigm type: {paradigm_type.value}")

        return RepoAnalysis(
            project_info=project_info,
            paradigm_type=paradigm_type,
            agents=agents,
            commands=commands,
            workflows=workflows,
            complexity_score=complexity_score,
            paradigm_indicators=paradigm_indicators,
        )

    def _extract_project_info(self) -> ProjectInfo:
        """Extract basic project information"""
        name = self.repo_path.name
        description = ""
        version = ""
        language = ""
        framework = ""

        # Try to extract from README
        readme_files = ["README.md", "readme.md", "README.rst", "README.txt"]
        for readme_file in readme_files:
            readme_path = self.repo_path / readme_file
            if readme_path.exists():
                with open(readme_path, encoding="utf-8") as f:
                    content = f.read()
                    # Extract description from first paragraph after title
                    lines = content.split("\n")
                    for line in lines:
                        if line.strip() and not line.startswith("#") and not line.startswith("="):
                            description = line.strip()
                            break
                break

        # Try to extract from pyproject.toml
        pyproject_path = self.repo_path / "pyproject.toml"
        if pyproject_path.exists():
            language = "Python"
            try:
                import tomllib

                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                    if "project" in data:
                        proj = data["project"]
                        if "description" in proj and not description:
                            description = proj["description"]
                        if "version" in proj:
                            version = proj["version"]
            except Exception:
                pass

        # Try to extract from package.json
        package_json_path = self.repo_path / "package.json"
        if package_json_path.exists():
            language = "JavaScript/Node.js"
            try:
                with open(package_json_path) as f:
                    data = json.load(f)
                    if "description" in data and not description:
                        description = data["description"]
                    if "version" in data:
                        version = data["version"]
            except Exception:
                pass

        return ProjectInfo(name=name, description=description, version=version, language=language, framework=framework)

    def _extract_agents(self) -> list[AgentInfo]:
        """Extract specialized agents from the repository"""
        agents = []

        # Check common agent locations
        agent_patterns = [".claude/agents", "agents", "subagents", ".ai/agents"]

        for pattern in agent_patterns:
            agent_dir = self.repo_path / pattern
            if agent_dir.exists() and agent_dir.is_dir():
                print(f"Checking agent directory: {agent_dir}")
                for agent_file in agent_dir.glob("*.md"):
                    print(f"Processing agent file: {agent_file.name}")
                    agent_info = self._parse_agent_file(agent_file)
                    if agent_info:
                        agents.append(agent_info)
                    else:
                        print(f"Failed to parse agent file: {agent_file.name}")

        return agents

    def _parse_agent_file(self, agent_file: Path) -> AgentInfo | None:
        """Parse an individual agent file"""
        try:
            with open(agent_file, encoding="utf-8") as f:
                content = f.read()

            name = agent_file.stem
            description = ""
            capabilities = []

            lines = content.split("\n")
            current_section = None
            in_frontmatter = False
            frontmatter_done = False

            for i, line in enumerate(lines):
                line_stripped = line.strip()

                # Handle YAML frontmatter
                if i == 0 and line_stripped == "---":
                    in_frontmatter = True
                    continue
                if in_frontmatter and line_stripped == "---":
                    in_frontmatter = False
                    frontmatter_done = True
                    continue
                if in_frontmatter:
                    # Parse frontmatter for description
                    if line_stripped.startswith("description:"):
                        description = line_stripped[12:].strip()
                        # Remove quotes if present
                        if (
                            description.startswith('"')
                            and description.endswith('"')
                            or description.startswith("'")
                            and description.endswith("'")
                        ):
                            description = description[1:-1]
                    continue

                # Skip empty lines and process content after frontmatter
                if not frontmatter_done:
                    continue

                if line_stripped.startswith("# "):
                    current_section = line_stripped[2:].lower()
                elif line_stripped.startswith("## "):
                    current_section = line_stripped[3:].lower()
                elif line_stripped.startswith("### "):
                    current_section = line_stripped[4:].lower()
                elif line_stripped and not description and not line_stripped.startswith("#"):
                    # If no description from frontmatter, use first content line
                    if not description:
                        description = line_stripped[:200]  # Limit description length
                elif current_section and (
                    "capabilit" in current_section or "skill" in current_section or "method" in current_section
                ):
                    if line_stripped.startswith("- "):
                        capabilities.append(line_stripped[2:])
                elif line_stripped.startswith("- ") and not current_section:
                    # General bullet points as capabilities
                    capabilities.append(line_stripped[2:])

            # Ensure we have a description
            if not description and capabilities:
                description = f"Specialized agent with {len(capabilities)} capabilities"
            elif not description:
                description = f"Specialized agent: {name.replace('-', ' ').title()}"

            return AgentInfo(
                name=name,
                description=description,
                capabilities=capabilities,
                file_path=str(agent_file.relative_to(self.repo_path)),
            )

        except Exception as e:
            print(f"Error parsing agent file {agent_file}: {e}")
            return None

    def _extract_commands(self) -> list[CommandInfo]:
        """Extract commands and workflows from the repository"""
        commands = []

        # Check common command locations
        command_patterns = [".claude/commands/*.md", "commands/*.md", "scripts/*.md", ".ai/commands/*.md"]

        for pattern in command_patterns:
            command_dir = self.repo_path / pattern.split("/")[0]
            if command_dir.exists() and command_dir.is_dir():
                for command_file in command_dir.glob("*.md"):
                    command_info = self._parse_command_file(command_file)
                    if command_info:
                        commands.append(command_info)

        # Also check Makefile for common commands
        makefile_path = self.repo_path / "Makefile"
        if makefile_path.exists():
            makefile_commands = self._parse_makefile(makefile_path)
            commands.extend(makefile_commands)

        return commands

    def _parse_command_file(self, command_file: Path) -> CommandInfo | None:
        """Parse an individual command file"""
        try:
            with open(command_file, encoding="utf-8") as f:
                content = f.read()

            name = command_file.stem
            description = ""
            usage = ""

            lines = content.split("\n")
            for line in lines:
                line = line.strip()
                if line and not description and not line.startswith("#"):
                    description = line
                    break

            # Extract usage patterns (look for code blocks or command examples)
            in_code_block = False
            for line in lines:
                if line.strip().startswith("```"):
                    in_code_block = not in_code_block
                elif in_code_block and line.strip().startswith("make "):
                    usage = line.strip()
                    break
                elif line.strip().startswith("$ ") or line.strip().startswith("> "):
                    usage = line.strip()[2:]
                    break

            return CommandInfo(
                name=name, description=description, usage=usage, file_path=str(command_file.relative_to(self.repo_path))
            )

        except Exception as e:
            print(f"Error parsing command file {command_file}: {e}")
            return None

    def _parse_makefile(self, makefile_path: Path) -> list[CommandInfo]:
        """Extract commands from Makefile"""
        commands = []
        try:
            with open(makefile_path, encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")
            for line in lines:
                line = line.strip()
                if ":" in line and not line.startswith("#") and not line.startswith("\t"):
                    target = line.split(":")[0].strip()
                    if target and not target.startswith("."):
                        commands.append(
                            CommandInfo(
                                name=f"make {target}",
                                description=f"Makefile target: {target}",
                                usage=f"make {target}",
                                file_path="Makefile",
                            )
                        )

        except Exception as e:
            print(f"Error parsing Makefile: {e}")

        return commands

    def _extract_workflows(self) -> list[str]:
        """Extract workflow patterns from the repository"""
        workflows = []

        # Check for GitHub Actions
        gh_actions_path = self.repo_path / ".github" / "workflows"
        if gh_actions_path.exists():
            workflows.append("GitHub Actions")

        # Check for other CI/CD indicators
        ci_files = [".travis.yml", ".circleci/config.yml", "azure-pipelines.yml", "Jenkinsfile"]

        for ci_file in ci_files:
            if (self.repo_path / ci_file).exists():
                workflows.append(ci_file.split(".")[0].replace("/", "_"))

        return workflows

    def _calculate_complexity(self, agents: list[AgentInfo], commands: list[CommandInfo], workflows: list[str]) -> int:
        """Calculate overall project complexity score"""
        complexity = 0

        # Agent complexity
        complexity += len(agents)
        for agent in agents:
            complexity += len(agent.capabilities)

        # Command complexity
        complexity += len(commands)

        # Workflow complexity
        complexity += len(workflows) * 2

        # File structure complexity (optimized to avoid deep recursion)
        try:
            # Only count files in key directories to avoid performance issues
            key_dirs = ["src", "lib", "amplifier", ".claude", "docs"]
            total_files = 0
            for key_dir in key_dirs:
                dir_path = self.repo_path / key_dir
                if dir_path.exists():
                    total_files += sum(1 for _ in dir_path.rglob("*.py") if _.is_file())
                    total_files += sum(1 for _ in dir_path.rglob("*.md") if _.is_file())
            complexity += total_files // 10  # Rough file count contribution
        except Exception as e:
            print(f"Warning: Could not calculate file complexity: {e}")

        return min(complexity, 100)  # Cap at 100

    def _detect_paradigm_indicators(
        self, agents: list[AgentInfo], commands: list[CommandInfo], workflows: list[str]
    ) -> dict[str, int]:
        """Detect paradigm shift indicators"""
        indicators = {
            "ai_amplification": 0,
            "specialized_agents": 0,
            "parallel_workflows": 0,
            "knowledge_synthesis": 0,
            "modular_architecture": 0,
        }

        # Get all text for analysis
        all_text = " ".join([agent.description for agent in agents] + [cmd.description for cmd in commands])

        # Also check project description and README
        try:
            readme_content = ""
            readme_files = ["README.md", "readme.md", "AMPLIFIER_VISION.md"]
            for readme_file in readme_files:
                readme_path = self.repo_path / readme_file
                if readme_path.exists():
                    with open(readme_path, encoding="utf-8") as f:
                        readme_content += f.read() + " "
            all_text += readme_content.lower()
        except Exception:
            pass

        # AI amplification indicators - enhanced detection
        ai_keywords = ["claude", "ai", "llm", "gpt", "assistant", "agent", "amplifier", "subagent", "claude code"]
        ai_score = 0
        for keyword in ai_keywords:
            if keyword in all_text.lower():
                ai_score += 1

        # Bonus for project name containing AI-related terms
        if any(keyword in self.repo_path.name.lower() for keyword in ai_keywords):
            ai_score += 2

        indicators["ai_amplification"] = min(ai_score, 3)

        # Specialized agents - enhanced scoring
        agent_count = len(agents)
        if agent_count >= 20 or agent_count >= 10:  # Amplifier has 25+ agents
            indicators["specialized_agents"] = 3
        elif agent_count >= 5:
            indicators["specialized_agents"] = 2
        elif agent_count >= 1:
            indicators["specialized_agents"] = 1

        # Parallel workflows - enhanced detection
        parallel_keywords = ["parallel", "concurrent", "async", "multi", "batch", "pipeline"]
        parallel_score = 0
        for keyword in parallel_keywords:
            if keyword in all_text.lower():
                parallel_score += 1
        indicators["parallel_workflows"] = min(parallel_score, 3)

        # Knowledge synthesis - enhanced detection
        knowledge_keywords = [
            "synthesis",
            "knowledge",
            "extraction",
            "mining",
            "analysis",
            "insight",
            "understanding",
            "learning",
            "memory",
            "context",
            "reasoning",
            "thinking",
            "cognitive",
        ]
        knowledge_score = 0
        for keyword in knowledge_keywords:
            if keyword in all_text.lower():
                knowledge_score += 1
        indicators["knowledge_synthesis"] = min(knowledge_score // 2, 3)  # Scale down slightly

        # Modular architecture - enhanced detection
        modular_keywords = [
            "modular",
            "module",
            "component",
            "brick",
            "plugin",
            "microservice",
            "service",
            "toolkit",
            "framework",
            "architecture",
            "system",
            "platform",
        ]
        modular_score = 0
        for keyword in modular_keywords:
            if keyword in all_text.lower():
                modular_score += 1
        if modular_score >= 3:
            indicators["modular_architecture"] = 3
        elif modular_score >= 1:
            indicators["modular_architecture"] = 2

        # Revolutionary project bonus - check for paradigm shift language
        revolutionary_keywords = [
            "revolution",
            "paradigm",
            "transformation",
            "breakthrough",
            "game-chang",
            "disruptive",
            "fundamental",
            "reimagin",
            "multiplier",
            "supercharg",
            "amplif",
        ]
        revolutionary_score = 0
        for keyword in revolutionary_keywords:
            if keyword in all_text.lower():
                revolutionary_score += 1

        # Boost all scores if revolutionary language is detected
        if revolutionary_score >= 3:
            for key in indicators:
                indicators[key] = min(indicators[key] + 1, 3)

        return indicators

    def _classify_paradigm_shift(self, indicators: dict[str, int]) -> ParadigmType:
        """Classify the paradigm shift significance"""
        total_score = sum(indicators.values())

        # Check for specific revolutionary patterns
        has_many_agents = indicators["specialized_agents"] >= 3
        has_ai_focus = indicators["ai_amplification"] >= 3
        has_knowledge_work = indicators["knowledge_synthesis"] >= 2

        # Revolutionary: High total score OR strong AI+agents combination
        if total_score >= 10 or (has_many_agents and has_ai_focus and has_knowledge_work):
            return ParadigmType.REVOLUTIONARY
        if total_score >= 6 or (has_ai_focus and has_many_agents):
            return ParadigmType.EVOLUTIONARY
        return ParadigmType.INCREMENTAL

    def save_analysis(self, analysis: RepoAnalysis, output_path: str) -> None:
        """Save analysis results to JSON file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict for JSON serialization
        analysis_dict = asdict(analysis)
        analysis_dict["paradigm_type"] = analysis.paradigm_type.value

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(analysis_dict, f, indent=2, ensure_ascii=False)

        print(f"Analysis saved to: {output_file}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python repo_analyzer.py <repo_path>")
        sys.exit(1)

    repo_path = sys.argv[1]
    analyzer = RepositoryAnalyzer(repo_path)
    analysis = analyzer.analyze_repository()

    print("\nRepository Analysis Results:")
    print(f"Project: {analysis.project_info.name}")
    print(f"Description: {analysis.project_info.description}")
    print(f"Paradigm Type: {analysis.paradigm_type.value}")
    print(f"Complexity Score: {analysis.complexity_score}")
    print(f"Agents Found: {len(analysis.agents)}")
    print(f"Commands Found: {len(analysis.commands)}")
    print(f"Workflows: {', '.join(analysis.workflows) if analysis.workflows else 'None'}")
    print(f"Paradigm Indicators: {analysis.paradigm_indicators}")

    # Save analysis
    analyzer.save_analysis(analysis, f"{repo_path}_analysis.json")
